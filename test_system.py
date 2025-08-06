#!/usr/bin/env python3
"""
Test script for Intelligent Office Access Management System
This script tests all major components to ensure they're working correctly.
"""

import sys
import os
import time
import logging
from unittest.mock import Mock, patch
import numpy as np

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """Setup test logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_imports():
    """Test that all modules can be imported"""
    logger = logging.getLogger(__name__)
    logger.info("Testing module imports...")
    
    try:
        # Test core imports
        from app import create_app
        from app.detection.detector import PersonDetector
        from app.detection.tracker import Tracker
        from app.database.elasticsearch_client import ElasticsearchClient
        from app.utils.face_embedding import FaceEmbeddingGenerator
        from app.utils.tailgating_detector import TailgatingDetector
        from app.utils.access_control import AccessControl
        from app.utils.camera_monitor import CameraMonitor
        from app.utils.multi_camera_manager import MultiCameraManager
        
        logger.info("✅ All modules imported successfully")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False

def test_flask_app():
    """Test Flask app creation"""
    logger = logging.getLogger(__name__)
    logger.info("Testing Flask app creation...")
    
    try:
        from app import create_app
        
        # Create app with test config
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key',
            'ELASTICSEARCH_URL': 'http://localhost:9200',
            'ELASTICSEARCH_USERNAME': 'elastic',
            'ELASTICSEARCH_PASSWORD': 'changeme'
        }):
            app = create_app()
            
        # Test app configuration
        assert app.config['SECRET_KEY'] == 'test-secret-key'
        assert 'CAMERA_CONFIG' in app.config
        
        logger.info("✅ Flask app created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Flask app test failed: {e}")
        return False

def test_face_embedding():
    """Test face embedding functionality"""
    logger = logging.getLogger(__name__)
    logger.info("Testing face embedding...")
    
    try:
        from app.utils.face_embedding import FaceEmbeddingGenerator
        
        # Create a dummy image
        dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Initialize face embedding generator
        face_embedding = FaceEmbeddingGenerator()
        
        # Test face detection (should work even with random image)
        faces = face_embedding.detect_faces(dummy_image)
        
        # Test body feature extraction
        body_features = face_embedding.extract_body_features(dummy_image, [100, 100, 200, 300])
        
        logger.info(f"✅ Face embedding test completed - Detected faces: {len(faces)}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Face embedding test failed: {e}")
        return False

def test_tailgating_detector():
    """Test tailgating detection"""
    logger = logging.getLogger(__name__)
    logger.info("Testing tailgating detector...")
    
    try:
        from app.utils.tailgating_detector import TailgatingDetector
        
        # Initialize tailgating detector
        detector = TailgatingDetector()
        
        # Create mock tracks
        class MockTrack:
            def __init__(self, track_id):
                self.track_id = track_id
                self.confirmed = True
            
            def is_confirmed(self):
                return self.confirmed
            
            def to_ltrb(self):
                return [100, 50, 200, 300]  # Mock bounding box
        
        mock_tracks = [MockTrack(1), MockTrack(2)]
        
        # Test tailgating detection
        result = detector.update_tracks(mock_tracks, (480, 640))
        
        # Test card swipe registration
        detector.register_card_swipe("CARD001", "PERSON001", time.time())
        
        # Get statistics
        stats = detector.get_tailgating_statistics()
        
        logger.info(f"✅ Tailgating detector test completed - Active tracks: {stats['active_tracks']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Tailgating detector test failed: {e}")
        return False

def test_camera_monitor():
    """Test camera monitoring"""
    logger = logging.getLogger(__name__)
    logger.info("Testing camera monitor...")
    
    try:
        from app.utils.camera_monitor import CameraMonitor
        
        # Initialize camera monitor
        monitor = CameraMonitor()
        
        # Register a test camera
        monitor.register_camera("test_camera", "0")
        
        # Update frame received
        dummy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        monitor.update_frame_received("test_camera", dummy_frame)
        
        # Get camera status
        status = monitor.get_camera_status("test_camera")
        
        # Get statistics
        stats = monitor.get_camera_statistics()
        
        logger.info(f"✅ Camera monitor test completed - Status: {status['status']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Camera monitor test failed: {e}")
        return False

def test_access_control():
    """Test access control system"""
    logger = logging.getLogger(__name__)
    logger.info("Testing access control...")
    
    try:
        from app.utils.access_control import AccessControl
        
        # Initialize access control
        access_control = AccessControl()
        
        # Test person identification with dummy data
        identification_data = {
            'face_embedding': [0.1] * 512,
            'body_features': [0.1] * 256
        }
        
        result = access_control.identify_person(identification_data)
        
        # Test access verification
        access_result = access_control.verify_access("camera_1", "person_1", False)
        
        # Get statistics
        stats = access_control.get_access_statistics()
        
        logger.info(f"✅ Access control test completed - Identification: {result['identified']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Access control test failed: {e}")
        return False

def test_database_client():
    """Test database client (without actual connection)"""
    logger = logging.getLogger(__name__)
    logger.info("Testing database client...")
    
    try:
        from app.database.elasticsearch_client import ElasticsearchClient
        
        # Test with mock connection
        with patch('elasticsearch.Elasticsearch') as mock_es:
            # Mock successful connection
            mock_es.return_value.info.return_value = {
                'cluster_name': 'test-cluster',
                'version': {'number': '8.10.0'}
            }
            mock_es.return_value.indices.exists.return_value = False
            mock_es.return_value.index.return_value = {'_id': 'test-id'}
            
            # Initialize client
            client = ElasticsearchClient()
            
            # Test connection check
            connection_status = client.check_connection()
            
            logger.info(f"✅ Database client test completed - Status: {connection_status['status']}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Database client test failed: {e}")
        return False

def test_multi_camera_manager():
    """Test multi-camera manager"""
    logger = logging.getLogger(__name__)
    logger.info("Testing multi-camera manager...")
    
    try:
        from app.utils.multi_camera_manager import MultiCameraManager
        
        # Create test camera configuration
        camera_config = {
            'test_camera_1': {
                'name': 'Test Camera 1',
                'rtsp_url': '0',
                'width': 640,
                'height': 480,
                'fps': 30
            }
        }
        
        # Initialize manager
        manager = MultiCameraManager(camera_config, max_workers=2)
        
        # Test camera initialization (without actually opening cameras)
        with patch('cv2.VideoCapture') as mock_cap:
            mock_cap.return_value.isOpened.return_value = True
            mock_cap.return_value.set.return_value = True
            
            manager.initialize_cameras()
            
            # Get camera status
            status = manager.get_camera_status('test_camera_1')
            
            # Get system statistics
            stats = manager.get_system_statistics()
            
            logger.info(f"✅ Multi-camera manager test completed - Cameras: {stats['total_cameras']}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Multi-camera manager test failed: {e}")
        return False

def test_person_detector():
    """Test person detector (without actual model)"""
    logger = logging.getLogger(__name__)
    logger.info("Testing person detector...")
    
    try:
        from app.detection.detector import PersonDetector
        
        # Test with mock YOLO model
        with patch('ultralytics.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_model.fuse.return_value = None
            mock_model.return_value = [Mock()]  # Mock detection results
            mock_yolo.return_value = mock_model
            
            # Initialize detector
            detector = PersonDetector(camera_id="test_camera")
            
            # Create dummy frame
            dummy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            # Test detection (with mocked model)
            processed_frame, tracks = detector.detect_and_track(dummy_frame)
            
            # Get system status
            status = detector.get_system_status()
            
            logger.info(f"✅ Person detector test completed - Frame shape: {processed_frame.shape}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Person detector test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    logger = setup_logging()
    logger.info("🧪 Starting Intelligent Access System Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Flask App", test_flask_app),
        ("Face Embedding", test_face_embedding),
        ("Tailgating Detector", test_tailgating_detector),
        ("Camera Monitor", test_camera_monitor),
        ("Access Control", test_access_control),
        ("Database Client", test_database_client),
        ("Multi-Camera Manager", test_multi_camera_manager),
        ("Person Detector", test_person_detector),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running {test_name} test...")
        try:
            if test_func():
                logger.info(f"✅ {test_name} test PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} test FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} test FAILED with exception: {e}")
            failed += 1
    
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 Test Results: {passed} PASSED, {failed} FAILED")
    
    if failed == 0:
        logger.info("🎉 All tests passed! System is ready to run.")
        return True
    else:
        logger.warning(f"⚠️  {failed} test(s) failed. Please check the errors above.")
        return False

def test_yolo_model():
    """Test YOLO model availability"""
    logger = logging.getLogger(__name__)
    logger.info("Testing YOLO model availability...")
    
    try:
        model_path = "yolov8s.pt"
        if os.path.exists(model_path):
            logger.info(f"✅ YOLO model found: {model_path}")
            return True
        else:
            logger.warning(f"⚠️  YOLO model not found: {model_path}")
            logger.info("You can download it using: from ultralytics import YOLO; YOLO('yolov8s.pt')")
            return False
            
    except Exception as e:
        logger.error(f"❌ YOLO model test failed: {e}")
        return False

def test_camera_availability():
    """Test camera availability"""
    logger = logging.getLogger(__name__)
    logger.info("Testing camera availability...")
    
    try:
        import cv2
        
        # Test webcam
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            logger.info("✅ Webcam (index 0) is available")
            cap.release()
            return True
        else:
            logger.warning("⚠️  Webcam (index 0) is not available")
            return False
            
    except Exception as e:
        logger.error(f"❌ Camera test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Intelligent Office Access Management System - Test Suite")
    print("=" * 70)
    
    # Run component tests
    component_tests_passed = run_all_tests()
    
    print("\n" + "=" * 70)
    print("🔧 Hardware/Model Tests")
    print("=" * 70)
    
    # Run hardware/model tests
    yolo_test = test_yolo_model()
    camera_test = test_camera_availability()
    
    print(f"\n📊 Hardware Test Results:")
    print(f"   YOLO Model: {'✅ Available' if yolo_test else '❌ Not Found'}")
    print(f"   Camera: {'✅ Available' if camera_test else '❌ Not Available'}")
    
    print("\n" + "=" * 70)
    if component_tests_passed and yolo_test and camera_test:
        print("🎉 All tests passed! Your system is ready to run the Intelligent Access System.")
        print("\n🚀 To start the system, run:")
        print("   python run.py --demo-mode")
    else:
        print("⚠️  Some tests failed. Please address the issues before running the system.")
        if not yolo_test:
            print("   - Download YOLO model: from ultralytics import YOLO; YOLO('yolov8s.pt')")
        if not camera_test:
            print("   - Check camera connections and permissions")
    
    print("=" * 70) 