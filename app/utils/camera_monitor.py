import cv2
import time
import threading
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict, deque
import psutil
import os

class CameraMonitor:
    def __init__(self, health_check_interval: float = 30.0, 
                 frame_timeout: float = 10.0,
                 max_consecutive_failures: int = 3):
        """
        Initialize camera health monitoring system
        
        Args:
            health_check_interval: Interval between health checks in seconds
            frame_timeout: Maximum time to wait for a frame before considering camera offline
            max_consecutive_failures: Maximum consecutive failures before marking camera as offline
        """
        self.health_check_interval = health_check_interval
        self.frame_timeout = frame_timeout
        self.max_consecutive_failures = max_consecutive_failures
        
        # Camera status tracking
        self.camera_status = defaultdict(lambda: {
            'status': 'unknown',
            'last_frame_time': None,
            'fps': 0.0,
            'consecutive_failures': 0,
            'total_frames': 0,
            'error_message': None,
            'last_health_check': None
        })
        
        # Frame rate calculation
        self.frame_times = defaultdict(lambda: deque(maxlen=30))
        
        # Monitoring thread
        self.monitoring_thread = None
        self.stop_monitoring = False
        
        # Camera connections
        self.camera_connections = {}
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Camera monitor initialized")
    
    def start_monitoring(self):
        """Start the camera monitoring thread"""
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            self.stop_monitoring = False
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            self.logger.info("Camera monitoring started")
    
    def stop_monitoring(self):
        """Stop the camera monitoring thread"""
        self.stop_monitoring = True
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        self.logger.info("Camera monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while not self.stop_monitoring:
            try:
                # Check all cameras
                for camera_id in list(self.camera_status.keys()):
                    self._check_camera_health(camera_id)
                
                # Wait for next check
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5.0)  # Wait before retrying
    
    def _check_camera_health(self, camera_id: str):
        """Check health of a specific camera"""
        try:
            current_time = time.time()
            status = self.camera_status[camera_id]
            
            # Check if camera has received frames recently
            if status['last_frame_time'] is not None:
                time_since_last_frame = current_time - status['last_frame_time']
                
                if time_since_last_frame > self.frame_timeout:
                    status['consecutive_failures'] += 1
                    status['error_message'] = f"No frames received for {time_since_last_frame:.1f} seconds"
                    
                    if status['consecutive_failures'] >= self.max_consecutive_failures:
                        if status['status'] != 'offline':
                            status['status'] = 'offline'
                            self._create_camera_alert(camera_id, 'offline', 
                                                    f"Camera {camera_id} went offline")
                            self.logger.warning(f"Camera {camera_id} marked as offline")
                else:
                    # Camera is receiving frames
                    if status['status'] == 'offline':
                        status['status'] = 'online'
                        self._create_camera_alert(camera_id, 'online', 
                                                f"Camera {camera_id} came back online")
                        self.logger.info(f"Camera {camera_id} came back online")
                    
                    status['consecutive_failures'] = 0
                    status['error_message'] = None
            
            # Update last health check time
            status['last_health_check'] = current_time
            
        except Exception as e:
            self.logger.error(f"Error checking camera {camera_id} health: {e}")
            self.camera_status[camera_id]['error_message'] = str(e)
    
    def _create_camera_alert(self, camera_id: str, alert_type: str, description: str):
        """Create camera alert (to be implemented with database integration)"""
        # This would typically create an alert in the database
        # For now, just log it
        self.logger.info(f"Camera alert: {camera_id} - {alert_type}: {description}")
    
    def register_camera(self, camera_id: str, rtsp_url: str = None):
        """
        Register a camera for monitoring
        
        Args:
            camera_id: Unique camera identifier
            rtsp_url: RTSP URL or camera index
        """
        try:
            self.camera_status[camera_id] = {
                'status': 'unknown',
                'last_frame_time': None,
                'fps': 0.0,
                'consecutive_failures': 0,
                'total_frames': 0,
                'error_message': None,
                'last_health_check': time.time(),
                'rtsp_url': rtsp_url
            }
            
            self.logger.info(f"Camera {camera_id} registered for monitoring")
            
        except Exception as e:
            self.logger.error(f"Error registering camera {camera_id}: {e}")
    
    def update_frame_received(self, camera_id: str, frame: np.ndarray = None):
        """
        Update camera status when a frame is received
        
        Args:
            camera_id: Camera identifier
            frame: Received frame (optional)
        """
        try:
            current_time = time.time()
            
            if camera_id not in self.camera_status:
                self.register_camera(camera_id)
            
            status = self.camera_status[camera_id]
            
            # Update frame time
            status['last_frame_time'] = current_time
            status['total_frames'] += 1
            
            # Calculate FPS
            self.frame_times[camera_id].append(current_time)
            if len(self.frame_times[camera_id]) >= 2:
                time_diff = self.frame_times[camera_id][-1] - self.frame_times[camera_id][0]
                if time_diff > 0:
                    status['fps'] = len(self.frame_times[camera_id]) / time_diff
            
            # Reset failure count if frame received
            if status['consecutive_failures'] > 0:
                status['consecutive_failures'] = 0
                status['error_message'] = None
            
            # Mark as online if was offline
            if status['status'] == 'offline':
                status['status'] = 'online'
                self._create_camera_alert(camera_id, 'online', f"Camera {camera_id} came back online")
            
        except Exception as e:
            self.logger.error(f"Error updating frame received for camera {camera_id}: {e}")
    
    def get_camera_status(self, camera_id: str) -> Dict:
        """
        Get status of a specific camera
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Camera status dictionary
        """
        try:
            if camera_id not in self.camera_status:
                return {
                    'status': 'not_registered',
                    'error_message': 'Camera not registered for monitoring'
                }
            
            status = self.camera_status[camera_id].copy()
            
            # Add additional information
            current_time = time.time()
            if status['last_frame_time']:
                status['time_since_last_frame'] = current_time - status['last_frame_time']
            else:
                status['time_since_last_frame'] = None
            
            if status['last_health_check']:
                status['time_since_health_check'] = current_time - status['last_health_check']
            else:
                status['time_since_health_check'] = None
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting camera status for {camera_id}: {e}")
            return {
                'status': 'error',
                'error_message': str(e)
            }
    
    def get_all_camera_status(self) -> Dict[str, Dict]:
        """
        Get status of all monitored cameras
        
        Returns:
            Dictionary mapping camera IDs to their status
        """
        try:
            all_status = {}
            for camera_id in self.camera_status.keys():
                all_status[camera_id] = self.get_camera_status(camera_id)
            return all_status
            
        except Exception as e:
            self.logger.error(f"Error getting all camera status: {e}")
            return {}
    
    def get_active_camera_count(self) -> int:
        """Get number of active (online) cameras"""
        try:
            active_count = 0
            for camera_id in self.camera_status.keys():
                status = self.get_camera_status(camera_id)
                if status['status'] == 'online':
                    active_count += 1
            return active_count
            
        except Exception as e:
            self.logger.error(f"Error getting active camera count: {e}")
            return 0
    
    def get_system_uptime(self) -> float:
        """Get system uptime in seconds"""
        try:
            # Get process start time
            process = psutil.Process(os.getpid())
            return time.time() - process.create_time()
        except Exception as e:
            self.logger.error(f"Error getting system uptime: {e}")
            return 0.0
    
    def get_camera_statistics(self) -> Dict:
        """Get overall camera statistics"""
        try:
            total_cameras = len(self.camera_status)
            active_cameras = self.get_active_camera_count()
            offline_cameras = total_cameras - active_cameras
            
            # Calculate average FPS
            total_fps = 0.0
            cameras_with_fps = 0
            for camera_id in self.camera_status.keys():
                status = self.get_camera_status(camera_id)
                if status['fps'] > 0:
                    total_fps += status['fps']
                    cameras_with_fps += 1
            
            avg_fps = total_fps / cameras_with_fps if cameras_with_fps > 0 else 0.0
            
            # Calculate total frames
            total_frames = sum(status['total_frames'] for status in self.camera_status.values())
            
            return {
                'total_cameras': total_cameras,
                'active_cameras': active_cameras,
                'offline_cameras': offline_cameras,
                'uptime_percentage': (active_cameras / total_cameras * 100) if total_cameras > 0 else 0,
                'average_fps': avg_fps,
                'total_frames_processed': total_frames,
                'system_uptime': self.get_system_uptime()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting camera statistics: {e}")
            return {}
    
    def test_camera_connection(self, camera_id: str, rtsp_url: str = None) -> Dict:
        """
        Test connection to a camera
        
        Args:
            camera_id: Camera identifier
            rtsp_url: RTSP URL or camera index to test
            
        Returns:
            Connection test result
        """
        try:
            if rtsp_url is None:
                rtsp_url = self.camera_status.get(camera_id, {}).get('rtsp_url', '0')
            
            # Try to open camera
            cap = cv2.VideoCapture(rtsp_url)
            
            if not cap.isOpened():
                return {
                    'success': False,
                    'error_message': f"Could not open camera: {rtsp_url}",
                    'camera_id': camera_id
                }
            
            # Try to read a frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                return {
                    'success': False,
                    'error_message': "Could not read frame from camera",
                    'camera_id': camera_id
                }
            
            return {
                'success': True,
                'frame_shape': frame.shape,
                'camera_id': camera_id,
                'message': "Camera connection test successful"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'camera_id': camera_id
            }
    
    def reset_camera_status(self, camera_id: str):
        """Reset status for a specific camera"""
        try:
            if camera_id in self.camera_status:
                self.camera_status[camera_id] = {
                    'status': 'unknown',
                    'last_frame_time': None,
                    'fps': 0.0,
                    'consecutive_failures': 0,
                    'total_frames': 0,
                    'error_message': None,
                    'last_health_check': time.time()
                }
                
                # Clear frame times
                if camera_id in self.frame_times:
                    self.frame_times[camera_id].clear()
                
                self.logger.info(f"Reset status for camera {camera_id}")
            
        except Exception as e:
            self.logger.error(f"Error resetting camera status for {camera_id}: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.stop_monitoring()
            
            # Close any open camera connections
            for cap in self.camera_connections.values():
                if cap is not None:
                    cap.release()
            
            self.camera_connections.clear()
            self.logger.info("Camera monitor cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during camera monitor cleanup: {e}") 