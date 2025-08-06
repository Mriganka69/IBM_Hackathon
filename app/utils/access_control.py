import time
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
from app.database.elasticsearch_client import ElasticsearchClient
from app.utils.face_embedding import FaceEmbeddingGenerator
from app.utils.tailgating_detector import TailgatingDetector

class AccessControl:
    def __init__(self):
        """Initialize access control system"""
        self.es_client = ElasticsearchClient()
        self.face_embedding = FaceEmbeddingGenerator()
        self.tailgating_detector = TailgatingDetector()
        
        # Access control parameters
        self.face_similarity_threshold = 0.6
        self.body_similarity_threshold = 0.7
        self.access_timeout = 30  # seconds
        
        # Cache for employee data
        self.employee_cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.last_cache_update = 0
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Access control system initialized")
    
    def _update_employee_cache(self):
        """Update employee cache from database"""
        try:
            current_time = time.time()
            if current_time - self.last_cache_update > self.cache_timeout:
                employees = self.es_client.get_all_employees()
                
                # Update cache
                self.employee_cache = {}
                for employee in employees:
                    self.employee_cache[employee['employee_id']] = employee
                
                self.last_cache_update = current_time
                self.logger.info(f"Employee cache updated with {len(employees)} employees")
                
        except Exception as e:
            self.logger.error(f"Error updating employee cache: {e}")
    
    def identify_person(self, identification_data: Dict) -> Dict:
        """
        Identify person from face or body features
        
        Args:
            identification_data: Dictionary containing face_embedding or body_features
            
        Returns:
            Identification result with employee details and confidence
        """
        try:
            self._update_employee_cache()
            
            if not self.employee_cache:
                return {
                    'identified': False,
                    'confidence': 0.0,
                    'employee_id': None,
                    'employee_name': None,
                    'message': 'No employees registered in system'
                }
            
            best_match = None
            best_confidence = 0.0
            identification_method = None
            
            # Try face identification first
            if 'face_embedding' in identification_data:
                face_embedding = np.array(identification_data['face_embedding'])
                
                for employee_id, employee in self.employee_cache.items():
                    if 'face_embedding' in employee and employee['face_embedding'] is not None:
                        employee_embedding = np.array(employee['face_embedding'])
                        
                        is_similar, similarity = self.face_embedding.compare_embeddings(
                            face_embedding, employee_embedding, self.face_similarity_threshold
                        )
                        
                        if is_similar and similarity > best_confidence:
                            best_match = employee
                            best_confidence = similarity
                            identification_method = 'face'
            
            # Try body identification if face failed
            if best_match is None and 'body_features' in identification_data:
                body_features = np.array(identification_data['body_features'])
                
                for employee_id, employee in self.employee_cache.items():
                    if 'body_features' in employee and employee['body_features'] is not None:
                        employee_features = np.array(employee['body_features'])
                        
                        is_similar, similarity = self.face_embedding.compare_body_features(
                            body_features, employee_features, self.body_similarity_threshold
                        )
                        
                        if is_similar and similarity > best_confidence:
                            best_match = employee
                            best_confidence = similarity
                            identification_method = 'body'
            
            if best_match is not None:
                return {
                    'identified': True,
                    'confidence': best_confidence,
                    'employee_id': best_match['employee_id'],
                    'employee_name': best_match['name'],
                    'access_level': best_match['access_level'],
                    'department': best_match.get('department', 'Unknown'),
                    'identification_method': identification_method,
                    'message': f'Person identified as {best_match["name"]}'
                }
            else:
                return {
                    'identified': False,
                    'confidence': 0.0,
                    'employee_id': None,
                    'employee_name': None,
                    'message': 'Person not recognized'
                }
                
        except Exception as e:
            self.logger.error(f"Error identifying person: {e}")
            return {
                'identified': False,
                'confidence': 0.0,
                'employee_id': None,
                'employee_name': None,
                'message': f'Identification error: {str(e)}'
            }
    
    def verify_access(self, camera_id: str, person_id: str, card_swipe: bool) -> Dict:
        """
        Verify access for a person
        
        Args:
            camera_id: ID of the camera
            person_id: ID of the person
            card_swipe: Whether a card was swiped
            
        Returns:
            Access verification result
        """
        try:
            current_time = time.time()
            
            # Get person identification from recent logs
            recent_logs = self.es_client.get_access_logs(
                person_id=person_id,
                limit=1
            )
            
            if not recent_logs:
                return {
                    'access_granted': False,
                    'reason': 'No recent identification found',
                    'confidence': 0.0,
                    'employee_id': None
                }
            
            latest_log = recent_logs[0]
            
            # Check if identification is recent enough
            log_time = time.mktime(time.strptime(latest_log['timestamp'], '%Y-%m-%dT%H:%M:%S.%f'))
            if current_time - log_time > self.access_timeout:
                return {
                    'access_granted': False,
                    'reason': 'Identification expired',
                    'confidence': 0.0,
                    'employee_id': None
                }
            
            # Get employee details
            employee_id = latest_log.get('employee_id')
            if not employee_id:
                return {
                    'access_granted': False,
                    'reason': 'No employee ID found',
                    'confidence': 0.0,
                    'employee_id': None
                }
            
            employee = self.es_client.get_employee(employee_id)
            if not employee:
                return {
                    'access_granted': False,
                    'reason': 'Employee not found',
                    'confidence': 0.0,
                    'employee_id': None
                }
            
            # Check access level
            access_level = employee.get('access_level', 'basic')
            confidence = latest_log.get('confidence_score', 0.0)
            
            # Determine access result
            access_granted = False
            reason = ''
            
            if card_swipe:
                # Card swipe with visual verification
                if confidence >= self.face_similarity_threshold:
                    access_granted = True
                    reason = 'Card swipe with visual verification'
                else:
                    access_granted = False
                    reason = 'Card swipe but visual verification failed'
            else:
                # No card swipe - visual identification only
                if confidence >= self.face_similarity_threshold:
                    access_granted = True
                    reason = 'Visual identification only'
                else:
                    access_granted = False
                    reason = 'Visual identification failed'
            
            # Register card swipe for tailgating detection
            if card_swipe:
                card_id = employee.get('card_id', 'unknown')
                self.tailgating_detector.register_card_swipe(card_id, person_id, current_time)
            
            return {
                'access_granted': access_granted,
                'reason': reason,
                'confidence': confidence,
                'employee_id': employee_id,
                'employee_name': employee['name'],
                'access_level': access_level,
                'card_swipe': card_swipe
            }
            
        except Exception as e:
            self.logger.error(f"Error verifying access: {e}")
            return {
                'access_granted': False,
                'reason': f'Verification error: {str(e)}',
                'confidence': 0.0,
                'employee_id': None
            }
    
    def process_access_event(self, camera_id: str, person_id: str, 
                           face_embedding: Optional[np.ndarray] = None,
                           body_features: Optional[np.ndarray] = None,
                           card_swipe: bool = False) -> Dict:
        """
        Process a complete access event including identification and verification
        
        Args:
            camera_id: ID of the camera
            person_id: ID of the person
            face_embedding: Face embedding vector
            body_features: Body feature vector
            card_swipe: Whether a card was swiped
            
        Returns:
            Complete access event result
        """
        try:
            current_time = time.time()
            
            # Step 1: Identify person
            identification_data = {}
            if face_embedding is not None:
                identification_data['face_embedding'] = face_embedding.tolist()
            if body_features is not None:
                identification_data['body_features'] = body_features.tolist()
            
            identification_result = self.identify_person(identification_data)
            
            # Step 2: Verify access
            access_result = self.verify_access(camera_id, person_id, card_swipe)
            
            # Step 3: Create access log
            log_data = {
                'camera_id': camera_id,
                'person_id': person_id,
                'access_type': 'card_swipe' if card_swipe else 'visual_only',
                'access_result': 'granted' if access_result['access_granted'] else 'denied',
                'confidence_score': identification_result['confidence'],
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%f'),
                'location': 'entrance'  # This could be determined from camera_id
            }
            
            # Add employee ID if identified
            if identification_result['identified']:
                log_data['employee_id'] = identification_result['employee_id']
            
            # Add face/body features if available
            if face_embedding is not None:
                log_data['face_embedding'] = face_embedding.tolist()
            if body_features is not None:
                log_data['body_features'] = body_features.tolist()
            
            # Create log entry
            log_id = self.es_client.create_access_log(log_data)
            
            # Step 4: Check for tailgating
            tailgating_result = self.tailgating_detector.get_tailgating_statistics()
            
            # Create alert if access denied
            if not access_result['access_granted']:
                alert_data = {
                    'alert_type': 'unauthorized_access',
                    'severity': 'high',
                    'camera_id': camera_id,
                    'person_id': person_id,
                    'description': f"Unauthorized access attempt: {access_result['reason']}"
                }
                self.es_client.create_alert(alert_data)
            
            return {
                'log_id': log_id,
                'identification': identification_result,
                'access_verification': access_result,
                'tailgating_status': tailgating_result,
                'timestamp': current_time
            }
            
        except Exception as e:
            self.logger.error(f"Error processing access event: {e}")
            return {
                'error': str(e),
                'timestamp': time.time()
            }
    
    def get_access_statistics(self) -> Dict:
        """Get access control statistics"""
        try:
            # Get recent logs
            recent_logs = self.es_client.get_access_logs(limit=100)
            
            # Calculate statistics
            total_attempts = len(recent_logs)
            granted_attempts = len([log for log in recent_logs if log['access_result'] == 'granted'])
            denied_attempts = total_attempts - granted_attempts
            
            # Get employee count
            employee_count = self.es_client.get_employee_count()
            
            # Get tailgating statistics
            tailgating_stats = self.tailgating_detector.get_tailgating_statistics()
            
            return {
                'total_access_attempts': total_attempts,
                'granted_access': granted_attempts,
                'denied_access': denied_attempts,
                'success_rate': granted_attempts / total_attempts if total_attempts > 0 else 0,
                'registered_employees': employee_count,
                'tailgating_alerts': tailgating_stats['total_alerts'],
                'active_tracks': tailgating_stats['active_tracks']
            }
            
        except Exception as e:
            self.logger.error(f"Error getting access statistics: {e}")
            return {}
    
    def register_employee(self, employee_data: Dict) -> str:
        """
        Register a new employee
        
        Args:
            employee_data: Employee information including face/body features
            
        Returns:
            Employee ID
        """
        try:
            employee_id = self.es_client.register_employee(employee_data)
            
            # Update cache
            self.employee_cache[employee_id] = employee_data
            
            self.logger.info(f"Employee registered: {employee_id}")
            return employee_id
            
        except Exception as e:
            self.logger.error(f"Error registering employee: {e}")
            raise
    
    def update_employee(self, employee_id: str, update_data: Dict) -> bool:
        """
        Update employee information
        
        Args:
            employee_id: Employee ID
            update_data: Updated employee data
            
        Returns:
            Success status
        """
        try:
            success = self.es_client.update_employee(employee_id, update_data)
            
            if success:
                # Update cache
                if employee_id in self.employee_cache:
                    self.employee_cache[employee_id].update(update_data)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating employee: {e}")
            return False 