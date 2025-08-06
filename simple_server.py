from flask import Flask, jsonify, request
from flask_cors import CORS
import datetime
import random
import time

app = Flask(__name__)
CORS(app)

# Mock data for the frontend
mock_cameras = {
    "camera_1": {
        "id": "camera_1",
        "name": "Main Entrance",
        "location": "Building A - Ground Floor",
        "status": "online",
        "fps": 25.5,
        "person_count": 3,
        "last_frame_time": datetime.datetime.now().isoformat(),
        "health": "healthy"
    },
    "camera_2": {
        "id": "camera_2", 
        "name": "Side Entrance",
        "location": "Building A - Side Door",
        "status": "online",
        "fps": 24.8,
        "person_count": 1,
        "last_frame_time": datetime.datetime.now().isoformat(),
        "health": "healthy"
    }
}

mock_employees = [
    {
        "id": "EMP001",
        "name": "John Smith",
        "email": "john.smith@company.com",
        "department": "Engineering",
        "position": "Senior Developer",
        "face_snapshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiM2QjcyOEQiLz4KPHN2ZyB4PSIxMCIgeT0iMTIiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIgdmlld0JveD0iMCAwIDIwIDIwIiBmaWxsPSJub25lIj4KPHBhdGggZD0iTTEwIDEyQzEyLjIwOTEgMTIgMTQgMTAuMjA5MSAxNCA4QzE0IDUuNzkwODYgMTIuMjA5MSA0IDEwIDRDNy43OTA4NiA0IDYgNS43OTA4NiA2IDhDNiAxMC4yMDkxIDcuNzkwODYgMTIgMTAgMTJaIiBmaWxsPSJ3aGl0ZSIvPgo8cGF0aCBkPSJNMTAgMTRDNy4zMzMzMyAxNCA1IDE2LjMzMzMgNSAxOVYyMEgxNVYxOUMxNSAxNi4zMzMzIDEyLjY2NjcgMTQgMTAgMTRaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4KPC9zdmc+",
        "registered_date": "2024-01-15T10:30:00Z",
        "last_access": "2024-08-07T14:30:00Z"
    },
    {
        "id": "EMP002", 
        "name": "Sarah Johnson",
        "email": "sarah.johnson@company.com",
        "department": "Marketing",
        "position": "Marketing Manager",
        "face_snapshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiM2QjcyOEQiLz4KPHN2ZyB4PSIxMCIgeT0iMTIiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIgdmlld0JveD0iMCAwIDIwIDIwIiBmaWxsPSJub25lIj4KPHBhdGggZD0iTTEwIDEyQzEyLjIwOTEgMTIgMTQgMTAuMjA5MSAxNCA4QzE0IDUuNzkwODYgMTIuMjA5MSA0IDEwIDRDNy43OTA4NiA0IDYgNS43OTA4NiA2IDhDNiAxMC4yMDkxIDcuNzkwODYgMTIgMTAgMTJaIiBmaWxsPSJ3aGl0ZSIvPgo8cGF0aCBkPSJNMTAgMTRDNy4zMzMzMyAxNCA1IDE2LjMzMzMgNSAxOVYyMEgxNVYxOUMxNSAxNi4zMzMzIDEyLjY2NjcgMTQgMTAgMTRaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4KPC9zdmc+",
        "registered_date": "2024-02-20T09:15:00Z",
        "last_access": "2024-08-07T13:45:00Z"
    },
    {
        "id": "EMP003",
        "name": "Mike Chen",
        "email": "mike.chen@company.com", 
        "department": "Sales",
        "position": "Sales Representative",
        "face_snapshot": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiM2QjcyOEQiLz4KPHN2ZyB4PSIxMCIgeT0iMTIiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIgdmlld0JveD0iMCAwIDIwIDIwIiBmaWxsPSJub25lIj4KPHBhdGggZD0iTTEwIDEyQzEyLjIwOTEgMTIgMTQgMTAuMjA5MSAxNCA4QzE0IDUuNzkwODYgMTIuMjA5MSA0IDEwIDRDNy43OTA4NiA0IDYgNS43OTA4NiA2IDhDNiAxMC4yMDkxIDcuNzkwODYgMTIgMTAgMTJaIiBmaWxsPSJ3aGl0ZSIvPgo8cGF0aCBkPSJNMTAgMTRDNy4zMzMzMyAxNCA1IDE2LjMzMzMgNSAxOVYyMEgxNVYxOUMxNSAxNi4zMzMzIDEyLjY2NjcgMTQgMTAgMTRaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4KPC9zdmc+",
        "registered_date": "2024-03-10T14:20:00Z",
        "last_access": "2024-08-07T12:15:00Z"
    }
]

mock_access_logs = [
    {
        "id": "log_001",
        "timestamp": "2024-08-07T14:30:00Z",
        "camera_id": "camera_1",
        "person_id": "EMP001",
        "access_type": "granted",
        "confidence": 0.95,
        "details": "Employee John Smith granted access"
    },
    {
        "id": "log_002", 
        "timestamp": "2024-08-07T14:25:00Z",
        "camera_id": "camera_2",
        "person_id": "EMP002",
        "access_type": "granted",
        "confidence": 0.92,
        "details": "Employee Sarah Johnson granted access"
    },
    {
        "id": "log_003",
        "timestamp": "2024-08-07T14:20:00Z", 
        "camera_id": "camera_1",
        "person_id": "unknown",
        "access_type": "denied",
        "confidence": 0.45,
        "details": "Unknown person denied access"
    },
    {
        "id": "log_004",
        "timestamp": "2024-08-07T14:15:00Z",
        "camera_id": "camera_1", 
        "person_id": "EMP003",
        "access_type": "tailgating",
        "confidence": 0.88,
        "details": "Tailgating detected - Employee Mike Chen"
    }
]

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'database': {'status': 'connected'},
        'cameras': {'active': 2, 'total': 2}
    }), 200

@app.route('/api/cameras', methods=['GET'])
def get_cameras():
    """Get all camera configurations"""
    return jsonify({
        'cameras': mock_cameras,
        'count': len(mock_cameras)
    }), 200

@app.route('/api/cameras/<camera_id>', methods=['GET'])
def get_camera_status(camera_id):
    """Get specific camera status"""
    if camera_id in mock_cameras:
        return jsonify(mock_cameras[camera_id]), 200
    else:
        return jsonify({'error': 'Camera not found'}), 404

@app.route('/api/cameras/<camera_id>/health', methods=['GET'])
def get_camera_health(camera_id):
    """Get camera health status"""
    if camera_id in mock_cameras:
        camera = mock_cameras[camera_id]
        return jsonify({
            'camera_id': camera_id,
            'status': camera['status'],
            'health': camera['health'],
            'last_frame_time': camera['last_frame_time'],
            'fps': camera['fps'],
            'person_count': camera['person_count'],
            'errors': []
        }), 200
    else:
        return jsonify({'error': 'Camera not found'}), 404

@app.route('/api/cameras/<camera_id>/stream', methods=['GET'])
def get_camera_stream(camera_id):
    """Mock video stream endpoint"""
    if camera_id in mock_cameras:
        # Return a simple HTML page with a mock video that can be embedded
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Camera Stream - {camera_id}</title></head>
        <body style="margin:0; background:black;">
            <div style="width:100%; height:100vh; display:flex; align-items:center; justify-content:center; color:white; font-family:Arial;">
                <div style="text-align:center;">
                    <h2>Mock Video Stream</h2>
                    <p>Camera: {camera_id}</p>
                    <p>Status: {mock_cameras[camera_id]['status']}</p>
                    <p>This is a mock stream for demonstration purposes.</p>
                    <div style="margin-top: 20px; padding: 20px; background: rgba(255,255,255,0.1); border-radius: 10px;">
                        <p>📹 Live Feed Simulation</p>
                        <p>People Detected: {mock_cameras[camera_id]['person_count']}</p>
                        <p>FPS: {mock_cameras[camera_id]['fps']}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html, 200, {'Content-Type': 'text/html'}
    else:
        return jsonify({'error': 'Camera not found'}), 404

@app.route('/api/access/logs', methods=['GET'])
def get_access_logs():
    """Get access logs with filtering"""
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    camera_id = request.args.get('camera_id')
    person_id = request.args.get('person_id')
    limit = int(request.args.get('limit', 100))
    
    # Filter logs based on parameters
    filtered_logs = mock_access_logs.copy()
    
    if camera_id:
        filtered_logs = [log for log in filtered_logs if log['camera_id'] == camera_id]
    
    if person_id:
        filtered_logs = [log for log in filtered_logs if log['person_id'] == person_id]
    
    # Apply limit
    filtered_logs = filtered_logs[:limit]
    
    return jsonify({
        'logs': filtered_logs,
        'count': len(filtered_logs),
        'total': len(mock_access_logs)
    }), 200

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """Get all employees"""
    return jsonify({
        'employees': mock_employees,
        'count': len(mock_employees)
    }), 200

@app.route('/api/employees/<employee_id>', methods=['GET'])
def get_employee(employee_id):
    """Get specific employee"""
    employee = next((emp for emp in mock_employees if emp['id'] == employee_id), None)
    if employee:
        return jsonify(employee), 200
    else:
        return jsonify({'error': 'Employee not found'}), 404

@app.route('/api/employees', methods=['POST'])
def create_employee():
    """Create a new employee"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'email', 'department', 'position']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Create new employee
    new_employee = {
        'id': f'EMP{str(len(mock_employees) + 1).zfill(3)}',
        'name': data['name'],
        'email': data['email'],
        'department': data['department'],
        'position': data['position'],
        'face_snapshot': data.get('face_snapshot', ''),
        'registered_date': datetime.datetime.now().isoformat(),
        'last_access': None
    }
    
    mock_employees.append(new_employee)
    
    return jsonify(new_employee), 201

@app.route('/api/employees/<employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """Update an employee"""
    employee = next((emp for emp in mock_employees if emp['id'] == employee_id), None)
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
    
    data = request.get_json()
    
    # Update fields
    for field in ['name', 'email', 'department', 'position']:
        if field in data:
            employee[field] = data[field]
    
    return jsonify(employee), 200

@app.route('/api/employees/<employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """Delete an employee"""
    global mock_employees
    employee = next((emp for emp in mock_employees if emp['id'] == employee_id), None)
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
    
    mock_employees = [emp for emp in mock_employees if emp['id'] != employee_id]
    
    return jsonify({'message': 'Employee deleted successfully'}), 200

@app.route('/api/system/stats', methods=['GET'])
def get_system_stats():
    """Get system statistics"""
    total_people = sum(camera['person_count'] for camera in mock_cameras.values())
    active_cameras = len([c for c in mock_cameras.values() if c['status'] == 'online'])
    
    # Count access types
    granted_access = len([log for log in mock_access_logs if log['access_type'] == 'granted'])
    denied_access = len([log for log in mock_access_logs if log['access_type'] == 'denied'])
    tailgating_incidents = len([log for log in mock_access_logs if log['access_type'] == 'tailgating'])
    
    return jsonify({
        'total_people_detected': total_people,
        'active_cameras': active_cameras,
        'total_cameras': len(mock_cameras),
        'granted_access': granted_access,
        'denied_access': denied_access,
        'tailgating_incidents': tailgating_incidents,
        'total_employees': len(mock_employees),
        'system_uptime': '2h 15m 30s',
        'average_fps': 25.2,
        'last_updated': datetime.datetime.now().isoformat()
    }), 200

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get system alerts"""
    alerts = [
        {
            'id': 'alert_001',
            'type': 'tailgating',
            'severity': 'high',
            'message': 'Tailgating detected at Main Entrance',
            'timestamp': datetime.datetime.now().isoformat(),
            'camera_id': 'camera_1',
            'resolved': False
        },
        {
            'id': 'alert_002',
            'type': 'camera_offline',
            'severity': 'medium', 
            'message': 'Camera 3 is offline',
            'timestamp': (datetime.datetime.now() - datetime.timedelta(minutes=5)).isoformat(),
            'camera_id': 'camera_3',
            'resolved': True
        }
    ]
    
    return jsonify({
        'alerts': alerts,
        'count': len(alerts),
        'unresolved': len([a for a in alerts if not a['resolved']])
    }), 200

if __name__ == '__main__':
    print("🚀 Starting Simple Flask Server for Frontend Testing")
    print("=" * 60)
    print("📋 Available endpoints:")
    print("   • Health Check: http://localhost:5000/api/health")
    print("   • Cameras: http://localhost:5000/api/cameras")
    print("   • Employees: http://localhost:5000/api/employees")
    print("   • Access Logs: http://localhost:5000/api/access/logs")
    print("   • System Stats: http://localhost:5000/api/system/stats")
    print("=" * 60)
    print("🎮 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
