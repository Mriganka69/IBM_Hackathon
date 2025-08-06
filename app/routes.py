from flask import Blueprint, request, jsonify, current_app
from app.database.elasticsearch_client import ElasticsearchClient
from app.utils.access_control import AccessControl
from app.utils.camera_monitor import CameraMonitor
import json
import datetime

api_bp = Blueprint('api', __name__)

# Initialize components
es_client = ElasticsearchClient()
access_control = AccessControl()
camera_monitor = CameraMonitor()

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_status = es_client.check_connection()
        
        # Check camera status
        camera_status = camera_monitor.get_all_camera_status()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.datetime.now().isoformat(),
            'database': db_status,
            'cameras': camera_status
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }), 500

@api_bp.route('/cameras', methods=['GET'])
def get_cameras():
    """Get all camera configurations"""
    try:
        cameras = current_app.config['CAMERA_CONFIG']
        return jsonify({
            'cameras': cameras,
            'count': len(cameras)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/cameras/<camera_id>/status', methods=['GET'])
def get_camera_status(camera_id):
    """Get specific camera status"""
    try:
        status = camera_monitor.get_camera_status(camera_id)
        return jsonify(status), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/access/logs', methods=['GET'])
def get_access_logs():
    """Get access logs with filtering"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        camera_id = request.args.get('camera_id')
        person_id = request.args.get('person_id')
        limit = int(request.args.get('limit', 100))
        
        logs = es_client.get_access_logs(
            start_date=start_date,
            end_date=end_date,
            camera_id=camera_id,
            person_id=person_id,
            limit=limit
        )
        
        return jsonify({
            'logs': logs,
            'count': len(logs)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/access/logs', methods=['POST'])
def create_access_log():
    """Create a new access log entry"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['camera_id', 'person_id', 'access_type', 'timestamp']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create log entry
        log_id = es_client.create_access_log(data)
        
        return jsonify({
            'message': 'Access log created successfully',
            'log_id': log_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/employees', methods=['GET'])
def get_employees():
    """Get all registered employees"""
    try:
        employees = es_client.get_all_employees()
        return jsonify({
            'employees': employees,
            'count': len(employees)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/employees', methods=['POST'])
def register_employee():
    """Register a new employee"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['employee_id', 'name', 'face_embedding', 'access_level']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Register employee
        employee_id = es_client.register_employee(data)
        
        return jsonify({
            'message': 'Employee registered successfully',
            'employee_id': employee_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/employees/<employee_id>', methods=['GET'])
def get_employee(employee_id):
    """Get specific employee details"""
    try:
        employee = es_client.get_employee(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        return jsonify(employee), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/employees/<employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """Update employee details"""
    try:
        data = request.get_json()
        
        # Update employee
        success = es_client.update_employee(employee_id, data)
        
        if not success:
            return jsonify({'error': 'Employee not found'}), 404
        
        return jsonify({
            'message': 'Employee updated successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/employees/<employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """Delete employee"""
    try:
        success = es_client.delete_employee(employee_id)
        
        if not success:
            return jsonify({'error': 'Employee not found'}), 404
        
        return jsonify({
            'message': 'Employee deleted successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get system alerts"""
    try:
        # Get query parameters
        alert_type = request.args.get('type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 50))
        
        alerts = es_client.get_alerts(
            alert_type=alert_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return jsonify({
            'alerts': alerts,
            'count': len(alerts)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/access/verify', methods=['POST'])
def verify_access():
    """Verify access for a person"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['camera_id', 'person_id', 'card_swipe']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Verify access
        access_result = access_control.verify_access(
            camera_id=data['camera_id'],
            person_id=data['person_id'],
            card_swipe=data['card_swipe']
        )
        
        return jsonify(access_result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/detection/identify', methods=['POST'])
def identify_person():
    """Identify person from face/body features"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'face_embedding' not in data and 'body_features' not in data:
            return jsonify({'error': 'Either face_embedding or body_features must be provided'}), 400
        
        # Identify person
        identification_result = access_control.identify_person(data)
        
        return jsonify(identification_result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/system/stats', methods=['GET'])
def get_system_stats():
    """Get system statistics"""
    try:
        stats = {
            'total_employees': es_client.get_employee_count(),
            'total_access_logs': es_client.get_access_log_count(),
            'active_cameras': camera_monitor.get_active_camera_count(),
            'system_uptime': camera_monitor.get_system_uptime(),
            'last_alert': es_client.get_last_alert(),
            'tailgating_incidents': es_client.get_tailgating_count()
        }
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
