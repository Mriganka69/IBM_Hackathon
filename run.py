#!/usr/bin/env python3
"""
Intelligent Office Access Management System (Project Code: P-002)
Main entry point for the complete system with Flask backend and multi-camera support.

Features:
- YOLOv8 + DeepSort for real-time person detection and tracking
- InsightFace for face detection and embedding
- Tailgating detection using DeepSort tracking
- Multi-camera support with health monitoring
- Elasticsearch database with encryption
- Flask REST API backend
- Access control with card swipe simulation
- Employee identification and registration
"""

import cv2
import sys
import os
import time
import threading
import signal
import argparse
from flask import Flask
import logging

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import application components
from app import create_app
from app.utils.multi_camera_manager import MultiCameraManager
from app.database.elasticsearch_client import ElasticsearchClient
from app.utils.access_control import AccessControl
from app.utils.face_embedding import FaceEmbeddingGenerator

# Global variables for graceful shutdown
camera_manager = None
flask_app = None
shutdown_event = threading.Event()

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('access_system.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()

def create_camera_config():
    """Create camera configuration"""
    return {
        'camera_1': {
            'name': 'Main Entrance',
            'rtsp_url': os.getenv('CAMERA_1_RTSP', '0'),  # Default to webcam
            'location': 'Main Entrance',
            'access_zone': 'entrance',
            'width': 640,
            'height': 480,
            'fps': 30,
            'model_path': 'yolov8s.pt',
            'confidence_threshold': 0.5
        },
        'camera_2': {
            'name': 'Office Floor',
            'rtsp_url': os.getenv('CAMERA_2_RTSP', '1'),  # Second camera
            'location': 'Office Floor',
            'access_zone': 'office',
            'width': 640,
            'height': 480,
            'fps': 30,
            'model_path': 'yolov8s.pt',
            'confidence_threshold': 0.5
        }
    }

def initialize_database():
    """Initialize and test database connection"""
    logger = logging.getLogger(__name__)
    try:
        es_client = ElasticsearchClient()
        connection_status = es_client.check_connection()
        
        if connection_status['status'] == 'connected':
            logger.info(f"✅ Database connected: {connection_status['cluster_name']}")
            return es_client
        else:
            logger.warning(f"⚠️  Database connection failed: {connection_status.get('error', 'Unknown error')}")
            logger.info("System will run with limited functionality (no data persistence)")
            return None
            
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
        return None

def register_sample_employees(es_client):
    """Register sample employees for testing"""
    logger = logging.getLogger(__name__)
    
    if not es_client:
        logger.warning("No database connection, skipping employee registration")
        return
    
    try:
        # Initialize face embedding generator
        face_embedding = FaceEmbeddingGenerator()
        
        # Sample employee data (in production, this would come from a registration process)
        sample_employees = [
            {
                'employee_id': 'EMP001',
                'name': 'John Doe',
                'access_level': 'admin',
                'department': 'IT',
                'card_id': 'CARD001'
            },
            {
                'employee_id': 'EMP002',
                'name': 'Jane Smith',
                'access_level': 'user',
                'department': 'HR',
                'card_id': 'CARD002'
            }
        ]
        
        for employee in sample_employees:
            try:
                # Check if employee already exists
                existing = es_client.get_employee(employee['employee_id'])
                if not existing:
                    # In a real system, face embeddings would be captured during registration
                    # For demo purposes, we'll create dummy embeddings
                    dummy_face_embedding = [0.1] * 512  # 512-dimensional face embedding
                    dummy_body_features = [0.1] * 256   # 256-dimensional body features
                    
                    employee['face_embedding'] = dummy_face_embedding
                    employee['body_features'] = dummy_body_features
                    
                    es_client.register_employee(employee)
                    logger.info(f"✅ Registered sample employee: {employee['name']}")
                else:
                    logger.info(f"ℹ️  Employee already exists: {employee['name']}")
                    
            except Exception as e:
                logger.error(f"❌ Error registering employee {employee['name']}: {e}")
                
    except Exception as e:
        logger.error(f"❌ Error in sample employee registration: {e}")

def frame_callback(frame_data):
    """Callback for processed frames"""
    # This function can be used to save frames, send to external systems, etc.
    camera_id = frame_data['camera_id']
    frame_number = frame_data['frame_number']
    
    # Example: Save every 100th frame
    if frame_number % 100 == 0:
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f"frames/{camera_id}_{timestamp}_{frame_number}.jpg"
        os.makedirs('frames', exist_ok=True)
        cv2.imwrite(filename, frame_data['frame'])

def start_flask_server(host='0.0.0.0', port=5000):
    """Start Flask server in a separate thread"""
    global flask_app
    
    def run_flask():
        flask_app = create_app()
        flask_app.run(host=host, port=port, debug=False, use_reloader=False)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 Flask server started on http://{host}:{port}")
    
    return flask_thread

def main():
    """Main entry point for the Intelligent Office Access Management System"""
    parser = argparse.ArgumentParser(description="Intelligent Office Access Management System")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind Flask server to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind Flask server to")
    parser.add_argument("--cameras", type=int, default=2, help="Number of cameras to use")
    parser.add_argument("--no-flask", action="store_true", help="Disable Flask server")
    parser.add_argument("--demo-mode", action="store_true", help="Enable demo mode with sample data")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 Starting Intelligent Office Access Management System (P-002)")
    logger.info("=" * 70)
    
    camera_manager = None
    flask_thread = None
    
    try:
        # Check if YOLO model exists
        model_path = "yolov8s.pt"
        if not os.path.exists(model_path):
            logger.error(f"❌ Model file {model_path} not found!")
            logger.info("Please download it using: from ultralytics import YOLO; YOLO('yolov8s.pt')")
            return
        
        # Initialize database
        logger.info("📊 Initializing database...")
        try:
            es_client = initialize_database()
        except Exception as e:
            logger.warning(f"⚠️ Database initialization failed: {e}")
            logger.info("Continuing without database functionality...")
            es_client = None
        
        # Register sample employees if in demo mode
        if args.demo_mode and es_client:
            logger.info("👥 Registering sample employees...")
            register_sample_employees(es_client)
        
        # Create camera configuration
        logger.info("📹 Setting up camera configuration...")
        camera_config = create_camera_config()
        
        # Limit cameras based on argument
        if args.cameras < len(camera_config):
            camera_config = {k: v for k, v in list(camera_config.items())[:args.cameras]}
        
        # Initialize multi-camera manager
        logger.info("🎥 Initializing multi-camera manager...")
        camera_manager = MultiCameraManager(camera_config, max_workers=4)
        
        # Add frame callback
        camera_manager.add_frame_callback(frame_callback)
        
        # Initialize cameras (but don't fail if cameras are not available)
        logger.info("🔧 Initializing cameras...")
        try:
            camera_manager.initialize_cameras()
            cameras_available = True
        except Exception as e:
            logger.warning(f"⚠️ Camera initialization failed: {e}")
            logger.info("Continuing without camera functionality...")
            cameras_available = False
        
        # Start Flask server if not disabled
        if not args.no_flask:
            logger.info("🌐 Starting Flask server...")
            flask_thread = start_flask_server(args.host, args.port)
        
        # Start camera processing only if cameras are available
        if cameras_available:
            logger.info("▶️  Starting camera processing...")
            try:
                camera_manager.start_all_cameras()
            except Exception as e:
                logger.warning(f"⚠️ Camera processing failed: {e}")
        
        logger.info("✅ System started successfully!")
        logger.info("=" * 70)
        logger.info("📋 System Features:")
        logger.info("   • YOLOv8 + DeepSort person detection and tracking")
        logger.info("   • InsightFace face detection and embedding")
        logger.info("   • Tailgating detection")
        logger.info("   • Multi-camera support with health monitoring")
        logger.info("   • Elasticsearch database with encryption")
        logger.info("   • Flask REST API backend")
        logger.info("   • Access control with employee identification")
        logger.info("=" * 70)
        
        if not args.no_flask:
            logger.info("🌐 API Endpoints:")
            logger.info(f"   • Health Check: http://{args.host}:{args.port}/api/health")
            logger.info(f"   • System Stats: http://{args.host}:{args.port}/api/system/stats")
            logger.info(f"   • Camera Status: http://{args.host}:{args.port}/api/cameras")
            logger.info(f"   • Access Logs: http://{args.host}:{args.port}/api/access/logs")
            logger.info(f"   • Employees: http://{args.host}:{args.port}/api/employees")
            logger.info("=" * 70)
        
        logger.info("🎮 Controls:")
        logger.info("   • Press Ctrl+C to stop the system")
        logger.info("   • Check logs for detailed information")
        logger.info("=" * 70)
        
        # Main loop - wait for shutdown signal
        while not shutdown_event.is_set():
            try:
                # Get system statistics every 30 seconds (only if cameras are available)
                if camera_manager and cameras_available:
                    try:
                        stats = camera_manager.get_system_statistics()
                        logger.info(f"📊 System Stats - Cameras: {stats['active_cameras']}, "
                                  f"FPS: {stats['average_fps']:.1f}, "
                                  f"Frames: {stats['total_frames_processed']}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error getting system stats: {e}")
                else:
                    logger.info("📊 System running in API-only mode")
                
                time.sleep(30)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(5)
        
    except Exception as e:
        logger.error(f"❌ System startup error: {e}")
        return
    
    finally:
        # Graceful shutdown
        logger.info("🛑 Shutting down system...")
        
        try:
            # Stop camera manager
            if camera_manager:
                logger.info("🛑 Stopping camera manager...")
                try:
                    camera_manager.stop_all_cameras()
                except Exception as e:
                    logger.warning(f"⚠️ Error stopping camera manager: {e}")
            
            # Stop Flask server
            if flask_app:
                logger.info("🛑 Stopping Flask server...")
                # Flask server will stop when main thread ends
            
            logger.info("✅ System shutdown completed")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")

def run_basic_detection():
    """Fallback to basic detection if main system fails"""
    logger = logging.getLogger(__name__)
    logger.info("🔄 Falling back to basic detection mode...")
    
    try:
        # Set environment variable to handle PyTorch 2.6+ security requirements
        import os
        os.environ['TORCH_WEIGHTS_ONLY'] = 'False'
        
        from ultralytics import YOLO
        from app.detection.tracker import Tracker
        
        # Load model (try smaller model first)
        try:
            model = YOLO("yolov8n.pt")
            model.fuse()
        except:
            # Fallback to larger model
            model = YOLO("yolov8s.pt")
            model.fuse()
        
        # Initialize tracker
        tracker = Tracker()
        
        # Open camera
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            logger.error("❌ Error: Could not open camera")
            return
        
        logger.info("🎥 Camera opened successfully")
        logger.info("🚀 Starting basic detection...")
        logger.info("Press 'q' to quit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run detection
            results = model(frame, stream=False, verbose=False)
            
            bbox_xywh = []
            confidences = []
            
            for result in results:
                if result.boxes is not None:
                    for det in result.boxes.data.tolist():
                        if len(det) >= 6:
                            x1, y1, x2, y2, conf, cls = det[:6]
                            if conf >= 0.5 and int(cls) == 0:  # Person class with confidence > 0.5
                                w = x2 - x1
                                h = y2 - y1
                                x = x1 + w / 2
                                y = y1 + h / 2
                                bbox_xywh.append([x, y, w, h])
                                confidences.append(conf)
            
            # Update tracker
            tracks = tracker.update(frame, bbox_xywh, confidences)
            
            # Draw results
            for track in tracks:
                if track.is_confirmed():
                    track_id = track.track_id
                    l, t, r, b = map(int, track.to_ltrb())
                    cv2.rectangle(frame, (l, t), (r, b), (0, 255, 0), 2)
                    cv2.putText(frame, f'ID: {track_id}', (l, t - 10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Show frame
            cv2.imshow("Intelligent Access System - Basic Mode", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
    except Exception as e:
        logger.error(f"❌ Basic detection error: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        print("🔄 Attempting to run basic detection...")
        run_basic_detection()