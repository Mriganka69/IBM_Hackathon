# app/detection/detector.py
import cv2
import time
import numpy as np
from ultralytics import YOLO
from app.detection.tracker import Tracker
from app.utils.face_embedding import FaceEmbeddingGenerator
from app.utils.tailgating_detector import TailgatingDetector
from app.utils.access_control import AccessControl
from app.utils.camera_monitor import CameraMonitor
import logging
from typing import Dict, List, Optional, Tuple

class PersonDetector:
    def __init__(self, model_path="yolov8s.pt", confidence_threshold=0.5, camera_id="camera_1"):
        """
        Initialize the enhanced person detector with all integrated systems
        
        Args:
            model_path: Path to YOLO model
            confidence_threshold: Detection confidence threshold
            camera_id: Camera identifier for this detector instance
        """
        # Set environment variable to handle PyTorch 2.6+ security requirements
        import os
        os.environ['TORCH_WEIGHTS_ONLY'] = 'False'
        
        print("Loading YOLO model...")
        try:
            # Try smaller model first if available
            if model_path == "yolov8s.pt" and os.path.exists("yolov8n.pt"):
                self.model = YOLO("yolov8n.pt")
            else:
                self.model = YOLO(model_path)
            self.model.fuse()
        except Exception as e:
            # Fallback to original model
            self.model = YOLO(model_path)
            self.model.fuse()
        
        self.tracker = Tracker()
        self.confidence_threshold = confidence_threshold
        self.target_classes = [0]  # Person class only
        self.camera_id = camera_id
        
        # Initialize integrated systems
        self.face_embedding = FaceEmbeddingGenerator()
        self.tailgating_detector = TailgatingDetector()
        self.access_control = AccessControl()
        self.camera_monitor = CameraMonitor()
        
        # Register camera for monitoring
        self.camera_monitor.register_camera(camera_id)
        self.camera_monitor.start_monitoring()
        
        # FPS tracking
        self.fps_counter = 0
        self.fps_time = time.time()
        self.current_fps = 0
        
        # Processing state
        self.frame_count = 0
        self.last_processing_time = time.time()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Enhanced PersonDetector initialized for camera: {camera_id}")
    
    def process_detections(self, results):
        """Extract bounding boxes and confidences from YOLO results"""
        bbox_xywh = []
        confidences = []
        
        for result in results:
            if result.boxes is not None:
                for det in result.boxes.data.tolist():
                    if len(det) >= 6:
                        x1, y1, x2, y2, conf, cls = det[:6]
                        
                        # Filter by confidence and class (person only)
                        if conf >= self.confidence_threshold and int(cls) in self.target_classes:
                            w = x2 - x1
                            h = y2 - y1
                            x = x1 + w / 2
                            y = y1 + h / 2
                            
                            bbox_xywh.append([x, y, w, h])
                            confidences.append(conf)
        
        return bbox_xywh, confidences
    
    def process_person_detection(self, frame: np.ndarray, person_bbox: List[float]) -> Dict:
        """
        Process a detected person for identification and access control
        
        Args:
            frame: Input frame
            person_bbox: Person bounding box [x, y, w, h] (center format)
            
        Returns:
            Processing result with identification and access information
        """
        try:
            # Convert center format to corner format
            x, y, w, h = person_bbox
            x1, y1, x2, y2 = int(x - w/2), int(y - h/2), int(x + w/2), int(y + h/2)
            
            # Ensure coordinates are within frame bounds
            h_frame, w_frame = frame.shape[:2]
            x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w_frame, x2), min(h_frame, y2)
            
            # Extract person region
            person_region = frame[y1:y2, x1:x2]
            
            if person_region.size == 0:
                return {'error': 'Invalid person region'}
            
            # Detect faces in person region
            faces = self.face_embedding.detect_faces(person_region)
            
            # Extract features
            face_embedding = None
            body_features = None
            
            if faces:
                # Use the first detected face
                face = faces[0]
                face_embedding = face['embedding']
            
            # Extract body features
            body_features = self.face_embedding.extract_body_features(frame, [x1, y1, x2, y2])
            
            return {
                'face_embedding': face_embedding,
                'body_features': body_features,
                'face_detected': len(faces) > 0,
                'person_bbox': [x1, y1, x2, y2]
            }
            
        except Exception as e:
            self.logger.error(f"Error processing person detection: {e}")
            return {'error': str(e)}
    
    def draw_tracks(self, frame, tracks, processing_results=None):
        """Draw bounding boxes, track IDs, and identification information"""
        for i, track in enumerate(tracks):
            if not track.is_confirmed():
                continue
                
            track_id = track.track_id
            ltrb = track.to_ltrb()
            l, t, r, b = map(int, ltrb)
            
            # Ensure coordinates are within frame
            h, w = frame.shape[:2]
            l, t, r, b = max(0, l), max(0, t), min(w, r), min(h, b)
            
            # Get processing result for this track
            processing_result = None
            if processing_results and i < len(processing_results):
                processing_result = processing_results[i]
            
            # Choose color based on identification status
            if processing_result and 'face_embedding' in processing_result and processing_result['face_embedding'] is not None:
                color = (0, 255, 0)  # Green for identified person
                label = f'Person ID: {track_id} (Identified)'
            else:
                color = (0, 255, 255)  # Yellow for unidentified person
                label = f'Person ID: {track_id} (Unknown)'
            
            # Draw bounding box
            cv2.rectangle(frame, (l, t), (r, b), color, 2)
            
            # Draw ID label
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame, (l, t - label_size[1] - 10), 
                         (l + label_size[0], t), color, -1)
            cv2.putText(frame, label, (l, t - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
            # Draw additional information if available
            if processing_result:
                if processing_result.get('face_detected'):
                    cv2.putText(frame, "Face Detected", (l, b + 20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    def calculate_fps(self):
        """Calculate FPS"""
        self.fps_counter += 1
        if time.time() - self.fps_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_time = time.time()
        return self.current_fps
    
    def draw_info(self, frame, tracks, tailgating_result=None):
        """Draw system information on frame"""
        fps = self.calculate_fps()
        active_tracks = len([t for t in tracks if t.is_confirmed()])
        
        # Basic info
        cv2.putText(frame, f'FPS: {fps}', (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f'Active Persons: {active_tracks}', (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f'Camera: {self.camera_id}', (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Tailgating information
        if tailgating_result:
            if tailgating_result['tailgating_detected']:
                cv2.putText(frame, f'TAILGATING DETECTED!', (10, 120), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                cv2.putText(frame, f'Confidence: {tailgating_result["tailgating_confidence"]:.2f}', (10, 150), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                cv2.putText(frame, f'Entry Zone: {tailgating_result["persons_in_entry_zone"]} persons', (10, 120), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    def detect_and_track(self, frame):
        """Enhanced detection and tracking with integrated systems"""
        try:
            # Update camera monitor
            self.camera_monitor.update_frame_received(self.camera_id, frame)
            
            # Run YOLO detection
            results = self.model(frame, stream=False, verbose=False)
            
            # Process detections
            bbox_xywh, confidences = self.process_detections(results)
            
            # Update tracker
            tracks = self.tracker.update(frame, bbox_xywh, confidences)
            
            # Process each detected person
            processing_results = []
            for i, track in enumerate(tracks):
                if track.is_confirmed():
                    # Get track bounding box in center format
                    ltrb = track.to_ltrb()
                    x1, y1, x2, y2 = ltrb
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    w = x2 - x1
                    h = y2 - y1
                    
                    person_bbox = [center_x, center_y, w, h]
                    
                    # Process person detection
                    result = self.process_person_detection(frame, person_bbox)
                    processing_results.append(result)
                    
                    # Process access event if face detected
                    if result.get('face_embedding') is not None:
                        # Simulate card swipe (in real system, this would come from card reader)
                        card_swipe = False  # This would be determined by actual card reader
                        
                        # Process access event
                        access_event = self.access_control.process_access_event(
                            camera_id=self.camera_id,
                            person_id=str(track.track_id),
                            face_embedding=result['face_embedding'],
                            body_features=result.get('body_features'),
                            card_swipe=card_swipe
                        )
                        
                        # Log access event
                        if 'error' not in access_event:
                            self.logger.info(f"Access event processed: {access_event.get('log_id')}")
            
            # Update tailgating detector
            tailgating_result = self.tailgating_detector.update_tracks(tracks, frame.shape)
            
            # Draw everything
            self.draw_tracks(frame, tracks, processing_results)
            self.draw_info(frame, tracks, tailgating_result)
            
            # Draw tailgating visualization
            frame = self.tailgating_detector.draw_tailgating_visualization(frame, tailgating_result)
            
            # Update frame counter
            self.frame_count += 1
            
            return frame, tracks
            
        except Exception as e:
            self.logger.error(f"Error in detect_and_track: {e}")
            return frame, []
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        try:
            camera_stats = self.camera_monitor.get_camera_statistics()
            access_stats = self.access_control.get_access_statistics()
            tailgating_stats = self.tailgating_detector.get_tailgating_statistics()
            
            return {
                'camera_id': self.camera_id,
                'frame_count': self.frame_count,
                'current_fps': self.current_fps,
                'camera_statistics': camera_stats,
                'access_statistics': access_stats,
                'tailgating_statistics': tailgating_stats,
                'system_uptime': self.camera_monitor.get_system_uptime()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.camera_monitor.cleanup()
            self.logger.info("PersonDetector cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")