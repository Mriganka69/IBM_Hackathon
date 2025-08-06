import cv2
import threading
import time
import logging
from typing import Dict, List, Optional, Callable
import numpy as np
from app.detection.detector import PersonDetector
from app.utils.camera_monitor import CameraMonitor
import queue

class MultiCameraManager:
    def __init__(self, camera_config: Dict, max_workers: int = 4):
        """
        Initialize multi-camera manager
        
        Args:
            camera_config: Dictionary mapping camera_id to camera configuration
            max_workers: Maximum number of worker threads
        """
        self.camera_config = camera_config
        self.max_workers = max_workers
        
        # Camera instances
        self.cameras = {}
        self.detectors = {}
        self.camera_threads = {}
        
        # Threading control
        self.stop_all = False
        self.worker_threads = []
        self.frame_queue = queue.Queue(maxsize=100)
        
        # Camera monitor
        self.camera_monitor = CameraMonitor()
        
        # Callbacks
        self.frame_callbacks = []
        self.alert_callbacks = []
        
        # Statistics
        self.stats = {
            'total_frames_processed': 0,
            'active_cameras': 0,
            'start_time': time.time()
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"MultiCameraManager initialized with {len(camera_config)} cameras")
    
    def add_frame_callback(self, callback: Callable):
        """Add callback for frame processing"""
        self.frame_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable):
        """Add callback for alerts"""
        self.alert_callbacks.append(callback)
    
    def initialize_cameras(self):
        """Initialize all cameras"""
        try:
            for camera_id, config in self.camera_config.items():
                self._initialize_camera(camera_id, config)
            
            self.logger.info(f"Initialized {len(self.cameras)} cameras")
            
        except Exception as e:
            self.logger.error(f"Error initializing cameras: {e}")
            raise
    
    def _initialize_camera(self, camera_id: str, config: Dict):
        """Initialize a single camera"""
        try:
            # Open camera
            rtsp_url = config.get('rtsp_url', '0')
            cap = cv2.VideoCapture(rtsp_url)
            
            if not cap.isOpened():
                raise ValueError(f"Could not open camera {camera_id} with URL: {rtsp_url}")
            
            # Set camera properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.get('width', 640))
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.get('height', 480))
            cap.set(cv2.CAP_PROP_FPS, config.get('fps', 30))
            
            # Store camera
            self.cameras[camera_id] = {
                'capture': cap,
                'config': config,
                'status': 'initialized'
            }
            
            # Initialize detector
            detector = PersonDetector(
                model_path=config.get('model_path', 'yolov8s.pt'),
                confidence_threshold=config.get('confidence_threshold', 0.5),
                camera_id=camera_id
            )
            self.detectors[camera_id] = detector
            
            # Register with camera monitor
            self.camera_monitor.register_camera(camera_id, rtsp_url)
            
            self.logger.info(f"Camera {camera_id} initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing camera {camera_id}: {e}")
            raise
    
    def start_all_cameras(self):
        """Start all camera processing threads"""
        try:
            # Start camera monitoring
            self.camera_monitor.start_monitoring()
            
            # Start worker threads
            for i in range(self.max_workers):
                worker = threading.Thread(target=self._worker_loop, args=(i,))
                worker.daemon = True
                worker.start()
                self.worker_threads.append(worker)
            
            # Start camera threads
            for camera_id in self.cameras.keys():
                self._start_camera_thread(camera_id)
            
            self.logger.info(f"Started {len(self.cameras)} camera threads and {self.max_workers} worker threads")
            
        except Exception as e:
            self.logger.error(f"Error starting cameras: {e}")
            raise
    
    def _start_camera_thread(self, camera_id: str):
        """Start processing thread for a specific camera"""
        try:
            if camera_id in self.camera_threads and self.camera_threads[camera_id].is_alive():
                return  # Already running
            
            thread = threading.Thread(target=self._camera_processing_loop, args=(camera_id,))
            thread.daemon = True
            thread.start()
            self.camera_threads[camera_id] = thread
            
            self.cameras[camera_id]['status'] = 'running'
            self.stats['active_cameras'] += 1
            
            self.logger.info(f"Started processing thread for camera {camera_id}")
            
        except Exception as e:
            self.logger.error(f"Error starting camera thread for {camera_id}: {e}")
    
    def _camera_processing_loop(self, camera_id: str):
        """Main processing loop for a camera"""
        try:
            camera = self.cameras[camera_id]
            cap = camera['capture']
            detector = self.detectors[camera_id]
            
            frame_count = 0
            
            while not self.stop_all and camera['status'] == 'running':
                try:
                    # Read frame
                    ret, frame = cap.read()
                    
                    if not ret or frame is None:
                        self.logger.warning(f"Failed to read frame from camera {camera_id}")
                        time.sleep(0.1)
                        continue
                    
                    # Update camera monitor
                    self.camera_monitor.update_frame_received(camera_id, frame)
                    
                    # Process frame with detector
                    processed_frame, tracks = detector.detect_and_track(frame)
                    
                    # Add to processing queue
                    try:
                        self.frame_queue.put_nowait({
                            'camera_id': camera_id,
                            'frame': processed_frame,
                            'tracks': tracks,
                            'timestamp': time.time(),
                            'frame_number': frame_count
                        })
                    except queue.Full:
                        self.logger.warning(f"Frame queue full, dropping frame from camera {camera_id}")
                    
                    frame_count += 1
                    
                    # Small delay to prevent overwhelming the system
                    time.sleep(0.01)
                    
                except Exception as e:
                    self.logger.error(f"Error processing frame from camera {camera_id}: {e}")
                    time.sleep(0.1)
            
            self.logger.info(f"Camera processing loop ended for {camera_id}")
            
        except Exception as e:
            self.logger.error(f"Error in camera processing loop for {camera_id}: {e}")
        finally:
            self.stats['active_cameras'] -= 1
    
    def _worker_loop(self, worker_id: int):
        """Worker thread loop for processing frames"""
        try:
            while not self.stop_all:
                try:
                    # Get frame from queue
                    frame_data = self.frame_queue.get(timeout=1.0)
                    
                    # Process frame
                    self._process_frame(frame_data)
                    
                    # Update statistics
                    self.stats['total_frames_processed'] += 1
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    self.logger.error(f"Error in worker {worker_id}: {e}")
            
            self.logger.info(f"Worker {worker_id} loop ended")
            
        except Exception as e:
            self.logger.error(f"Error in worker loop {worker_id}: {e}")
    
    def _process_frame(self, frame_data: Dict):
        """Process a frame with callbacks"""
        try:
            # Call frame callbacks
            for callback in self.frame_callbacks:
                try:
                    callback(frame_data)
                except Exception as e:
                    self.logger.error(f"Error in frame callback: {e}")
            
        except Exception as e:
            self.logger.error(f"Error processing frame: {e}")
    
    def stop_all_cameras(self):
        """Stop all camera processing"""
        try:
            self.logger.info("Stopping all cameras...")
            
            # Stop all processing
            self.stop_all = True
            
            # Stop camera threads
            for camera_id in self.camera_threads:
                self.cameras[camera_id]['status'] = 'stopped'
            
            # Wait for threads to finish
            for thread in self.camera_threads.values():
                thread.join(timeout=5.0)
            
            for thread in self.worker_threads:
                thread.join(timeout=5.0)
            
            # Stop camera monitoring
            self.camera_monitor.stop_monitoring()
            
            # Release camera resources
            self._cleanup_cameras()
            
            self.logger.info("All cameras stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping cameras: {e}")
    
    def _cleanup_cameras(self):
        """Cleanup camera resources"""
        try:
            for camera_id, camera in self.cameras.items():
                # Release capture
                if camera['capture'] is not None:
                    camera['capture'].release()
                
                # Cleanup detector
                if camera_id in self.detectors:
                    self.detectors[camera_id].cleanup()
            
            # Clear collections
            self.cameras.clear()
            self.detectors.clear()
            self.camera_threads.clear()
            
        except Exception as e:
            self.logger.error(f"Error cleaning up cameras: {e}")
    
    def get_camera_status(self, camera_id: str) -> Dict:
        """Get status of a specific camera"""
        try:
            if camera_id not in self.cameras:
                return {'status': 'not_found'}
            
            camera = self.cameras[camera_id]
            detector = self.detectors.get(camera_id)
            
            status = {
                'camera_id': camera_id,
                'status': camera['status'],
                'config': camera['config']
            }
            
            # Add detector status if available
            if detector:
                detector_status = detector.get_system_status()
                status['detector'] = detector_status
            
            # Add camera monitor status
            monitor_status = self.camera_monitor.get_camera_status(camera_id)
            status['monitor'] = monitor_status
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting camera status for {camera_id}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_all_camera_status(self) -> Dict:
        """Get status of all cameras"""
        try:
            all_status = {}
            for camera_id in self.cameras.keys():
                all_status[camera_id] = self.get_camera_status(camera_id)
            return all_status
            
        except Exception as e:
            self.logger.error(f"Error getting all camera status: {e}")
            return {}
    
    def get_system_statistics(self) -> Dict:
        """Get overall system statistics"""
        try:
            # Get camera monitor statistics
            camera_stats = self.camera_monitor.get_camera_statistics()
            
            # Calculate uptime
            uptime = time.time() - self.stats['start_time']
            
            # Calculate average FPS
            avg_fps = 0
            if uptime > 0:
                avg_fps = self.stats['total_frames_processed'] / uptime
            
            return {
                'total_cameras': len(self.cameras),
                'active_cameras': self.stats['active_cameras'],
                'total_frames_processed': self.stats['total_frames_processed'],
                'average_fps': avg_fps,
                'system_uptime': uptime,
                'camera_statistics': camera_stats,
                'queue_size': self.frame_queue.qsize()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system statistics: {e}")
            return {'error': str(e)}
    
    def restart_camera(self, camera_id: str) -> bool:
        """Restart a specific camera"""
        try:
            if camera_id not in self.cameras:
                return False
            
            self.logger.info(f"Restarting camera {camera_id}")
            
            # Stop camera
            self.cameras[camera_id]['status'] = 'stopped'
            if camera_id in self.camera_threads:
                self.camera_threads[camera_id].join(timeout=5.0)
            
            # Reinitialize camera
            config = self.camera_config[camera_id]
            self._initialize_camera(camera_id, config)
            
            # Restart camera thread
            self._start_camera_thread(camera_id)
            
            self.logger.info(f"Camera {camera_id} restarted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restarting camera {camera_id}: {e}")
            return False
    
    def add_camera(self, camera_id: str, config: Dict) -> bool:
        """Add a new camera dynamically"""
        try:
            if camera_id in self.cameras:
                self.logger.warning(f"Camera {camera_id} already exists")
                return False
            
            # Add to config
            self.camera_config[camera_id] = config
            
            # Initialize camera
            self._initialize_camera(camera_id, config)
            
            # Start camera if system is running
            if not self.stop_all:
                self._start_camera_thread(camera_id)
            
            self.logger.info(f"Camera {camera_id} added successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding camera {camera_id}: {e}")
            return False
    
    def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera dynamically"""
        try:
            if camera_id not in self.cameras:
                return False
            
            self.logger.info(f"Removing camera {camera_id}")
            
            # Stop camera
            self.cameras[camera_id]['status'] = 'stopped'
            if camera_id in self.camera_threads:
                self.camera_threads[camera_id].join(timeout=5.0)
            
            # Cleanup camera
            camera = self.cameras[camera_id]
            if camera['capture'] is not None:
                camera['capture'].release()
            
            if camera_id in self.detectors:
                self.detectors[camera_id].cleanup()
            
            # Remove from collections
            del self.cameras[camera_id]
            del self.detectors[camera_id]
            if camera_id in self.camera_threads:
                del self.camera_threads[camera_id]
            
            # Remove from config
            if camera_id in self.camera_config:
                del self.camera_config[camera_id]
            
            self.logger.info(f"Camera {camera_id} removed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing camera {camera_id}: {e}")
            return False 