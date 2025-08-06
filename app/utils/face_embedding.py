import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
import logging
from typing import List, Tuple, Optional, Dict
import os

class FaceEmbeddingGenerator:
    def __init__(self, model_name='buffalo_l'):
        """
        Initialize face embedding generator using InsightFace
        
        Args:
            model_name: InsightFace model name ('buffalo_l', 'buffalo_m', 'buffalo_s')
        """
        self.logger = logging.getLogger(__name__)
        
        try:
            # Initialize InsightFace app
            self.app = FaceAnalysis(name=model_name)
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            
            # Get face embedding model
            self.embedding_model = insightface.model_zoo.get_model('arcface_r100_v1')
            
            self.logger.info(f"Face embedding generator initialized with model: {model_name}")
            
        except Exception as e:
            self.logger.error(f"Error initializing face embedding generator: {e}")
            raise
    
    def detect_faces(self, image: np.ndarray) -> List[Dict]:
        """
        Detect faces in an image
        
        Args:
            image: Input image as numpy array (BGR format)
            
        Returns:
            List of face detection results
        """
        try:
            # Detect faces using InsightFace
            faces = self.app.get(image)
            
            results = []
            for face in faces:
                # Get bounding box
                bbox = face.bbox.astype(int)
                
                # Get keypoints
                kps = face.kps.astype(int) if face.kps is not None else None
                
                # Get embedding
                embedding = face.embedding
                
                # Get gender and age
                gender = face.gender
                age = face.age
                
                results.append({
                    'bbox': bbox,  # [x1, y1, x2, y2]
                    'kps': kps,    # 5 keypoints
                    'embedding': embedding,
                    'gender': gender,
                    'age': age,
                    'confidence': face.det_score
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error detecting faces: {e}")
            return []
    
    def extract_face_embedding(self, image: np.ndarray, face_bbox: List[int]) -> Optional[np.ndarray]:
        """
        Extract face embedding from a specific face region
        
        Args:
            image: Input image as numpy array
            face_bbox: Face bounding box [x1, y1, x2, y2]
            
        Returns:
            Face embedding vector or None if extraction fails
        """
        try:
            # Crop face region
            x1, y1, x2, y2 = face_bbox
            face_crop = image[y1:y2, x1:x2]
            
            if face_crop.size == 0:
                return None
            
            # Detect faces in cropped region
            faces = self.app.get(face_crop)
            
            if len(faces) > 0:
                # Return the first face embedding
                return faces[0].embedding
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting face embedding: {e}")
            return None
    
    def compare_embeddings(self, embedding1: np.ndarray, embedding2: np.ndarray, 
                          threshold: float = 0.6) -> Tuple[bool, float]:
        """
        Compare two face embeddings
        
        Args:
            embedding1: First face embedding
            embedding2: Second face embedding
            threshold: Similarity threshold (default: 0.6)
            
        Returns:
            Tuple of (is_similar, similarity_score)
        """
        try:
            # Normalize embeddings
            embedding1_norm = embedding1 / np.linalg.norm(embedding1)
            embedding2_norm = embedding2 / np.linalg.norm(embedding2)
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1_norm, embedding2_norm)
            
            # Determine if faces are similar
            is_similar = similarity >= threshold
            
            return is_similar, float(similarity)
            
        except Exception as e:
            self.logger.error(f"Error comparing embeddings: {e}")
            return False, 0.0
    
    def find_best_match(self, query_embedding: np.ndarray, 
                       reference_embeddings: List[np.ndarray],
                       threshold: float = 0.6) -> Tuple[Optional[int], float]:
        """
        Find the best matching face embedding from a list of reference embeddings
        
        Args:
            query_embedding: Query face embedding
            reference_embeddings: List of reference face embeddings
            threshold: Similarity threshold
            
        Returns:
            Tuple of (best_match_index, best_similarity_score)
        """
        try:
            best_match_idx = None
            best_similarity = 0.0
            
            for i, ref_embedding in enumerate(reference_embeddings):
                is_similar, similarity = self.compare_embeddings(
                    query_embedding, ref_embedding, threshold
                )
                
                if is_similar and similarity > best_similarity:
                    best_similarity = similarity
                    best_match_idx = i
            
            return best_match_idx, best_similarity
            
        except Exception as e:
            self.logger.error(f"Error finding best match: {e}")
            return None, 0.0
    
    def extract_body_features(self, image: np.ndarray, person_bbox: List[int]) -> Optional[np.ndarray]:
        """
        Extract body features from a person bounding box
        This is a simplified implementation - in production, you might use
        a dedicated person re-identification model
        
        Args:
            image: Input image as numpy array
            person_bbox: Person bounding box [x1, y1, x2, y2]
            
        Returns:
            Body feature vector or None if extraction fails
        """
        try:
            # Crop person region
            x1, y1, x2, y2 = person_bbox
            person_crop = image[y1:y2, x1:x2]
            
            if person_crop.size == 0:
                return None
            
            # Resize to standard size
            person_crop_resized = cv2.resize(person_crop, (128, 256))
            
            # Convert to grayscale
            gray = cv2.cvtColor(person_crop_resized, cv2.COLOR_BGR2GRAY)
            
            # Extract histogram features
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = hist.flatten() / hist.sum()  # Normalize
            
            # Extract HOG-like features (simplified)
            # In production, use a proper person re-id model
            features = []
            
            # Divide image into grid and extract features
            grid_size = 8
            h, w = gray.shape
            cell_h, cell_w = h // grid_size, w // grid_size
            
            for i in range(grid_size):
                for j in range(grid_size):
                    cell = gray[i*cell_h:(i+1)*cell_h, j*cell_w:(j+1)*cell_w]
                    cell_mean = np.mean(cell)
                    cell_std = np.std(cell)
                    features.extend([cell_mean, cell_std])
            
            # Combine histogram and grid features
            combined_features = np.concatenate([hist, np.array(features)])
            
            return combined_features
            
        except Exception as e:
            self.logger.error(f"Error extracting body features: {e}")
            return None
    
    def compare_body_features(self, features1: np.ndarray, features2: np.ndarray,
                             threshold: float = 0.7) -> Tuple[bool, float]:
        """
        Compare two body feature vectors
        
        Args:
            features1: First body feature vector
            features2: Second body feature vector
            threshold: Similarity threshold
            
        Returns:
            Tuple of (is_similar, similarity_score)
        """
        try:
            # Normalize features
            features1_norm = features1 / (np.linalg.norm(features1) + 1e-8)
            features2_norm = features2 / (np.linalg.norm(features2) + 1e-8)
            
            # Calculate cosine similarity
            similarity = np.dot(features1_norm, features2_norm)
            
            # Determine if bodies are similar
            is_similar = similarity >= threshold
            
            return is_similar, float(similarity)
            
        except Exception as e:
            self.logger.error(f"Error comparing body features: {e}")
            return False, 0.0
    
    def draw_face_detections(self, image: np.ndarray, faces: List[Dict]) -> np.ndarray:
        """
        Draw face detection results on image
        
        Args:
            image: Input image
            faces: List of face detection results
            
        Returns:
            Image with face detections drawn
        """
        try:
            result_image = image.copy()
            
            for face in faces:
                bbox = face['bbox']
                confidence = face['confidence']
                gender = face['gender']
                age = face['age']
                
                # Draw bounding box
                x1, y1, x2, y2 = bbox
                cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Draw keypoints if available
                if face['kps'] is not None:
                    for kp in face['kps']:
                        cv2.circle(result_image, tuple(kp), 2, (0, 0, 255), -1)
                
                # Draw text
                text = f"Conf: {confidence:.2f}, Age: {age}, Gender: {gender}"
                cv2.putText(result_image, text, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            return result_image
            
        except Exception as e:
            self.logger.error(f"Error drawing face detections: {e}")
            return image 