from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    """Application factory for Flask app"""
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    app.config['ELASTICSEARCH_URL'] = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
    app.config['ELASTICSEARCH_USERNAME'] = os.getenv('ELASTICSEARCH_USERNAME', 'elastic')
    app.config['ELASTICSEARCH_PASSWORD'] = os.getenv('ELASTICSEARCH_PASSWORD', 'changeme')
    
    # Camera configuration
    app.config['CAMERA_CONFIG'] = {
        'camera_1': {
            'name': 'Main Entrance',
            'rtsp_url': os.getenv('CAMERA_1_RTSP', '0'),  # Default to webcam
            'location': 'Main Entrance',
            'access_zone': 'entrance'
        },
        'camera_2': {
            'name': 'Office Floor',
            'rtsp_url': os.getenv('CAMERA_2_RTSP', '1'),  # Second camera
            'location': 'Office Floor',
            'access_zone': 'office'
        }
    }
    
    # Register blueprints
    from app.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
