import os
import json
import datetime
import uuid
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from cryptography.fernet import Fernet
import base64
import hashlib
import logging

class ElasticsearchClient:
    def __init__(self):
        """Initialize Elasticsearch client with security features"""
        self.es_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
        self.es_username = os.getenv('ELASTICSEARCH_USERNAME', 'elastic')
        self.es_password = os.getenv('ELASTICSEARCH_PASSWORD', 'changeme')
        
        # Initialize encryption key
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
        if not self.encryption_key:
            # Generate a new key if not provided
            self.encryption_key = Fernet.generate_key()
            print(f"Generated new encryption key: {self.encryption_key.decode()}")
        
        self.cipher = Fernet(self.encryption_key)
        
        # Initialize Elasticsearch client
        self.es = Elasticsearch(
            [self.es_url],
            basic_auth=(self.es_username, self.es_password),
            verify_certs=False,  # Set to True in production with proper certificates
            ssl_show_warn=False
        )
        
        # Initialize indices
        self._create_indices()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _create_indices(self):
        """Create necessary indices with proper mappings"""
        indices = {
            'employees': {
                'mappings': {
                    'properties': {
                        'employee_id': {'type': 'keyword'},
                        'name': {'type': 'text'},
                        'face_embedding': {'type': 'binary'},  # Encrypted
                        'body_features': {'type': 'binary'},   # Encrypted
                        'access_level': {'type': 'keyword'},
                        'card_id': {'type': 'keyword'},
                        'department': {'type': 'keyword'},
                        'created_at': {'type': 'date'},
                        'updated_at': {'type': 'date'},
                        'is_active': {'type': 'boolean'}
                    }
                }
            },
            'access_logs': {
                'mappings': {
                    'properties': {
                        'log_id': {'type': 'keyword'},
                        'camera_id': {'type': 'keyword'},
                        'person_id': {'type': 'keyword'},
                        'employee_id': {'type': 'keyword'},
                        'access_type': {'type': 'keyword'},  # card_swipe, face_recognition, body_recognition
                        'access_result': {'type': 'keyword'},  # granted, denied, tailgating
                        'confidence_score': {'type': 'float'},
                        'face_embedding': {'type': 'binary'},  # Encrypted
                        'body_features': {'type': 'binary'},   # Encrypted
                        'timestamp': {'type': 'date'},
                        'location': {'type': 'keyword'},
                        'tailgating_detected': {'type': 'boolean'},
                        'tailgating_count': {'type': 'integer'}
                    }
                }
            },
            'alerts': {
                'mappings': {
                    'properties': {
                        'alert_id': {'type': 'keyword'},
                        'alert_type': {'type': 'keyword'},  # camera_offline, tailgating, unauthorized_access
                        'severity': {'type': 'keyword'},  # low, medium, high, critical
                        'camera_id': {'type': 'keyword'},
                        'person_id': {'type': 'keyword'},
                        'description': {'type': 'text'},
                        'timestamp': {'type': 'date'},
                        'resolved': {'type': 'boolean'},
                        'resolved_at': {'type': 'date'}
                    }
                }
            },
            'camera_health': {
                'mappings': {
                    'properties': {
                        'camera_id': {'type': 'keyword'},
                        'status': {'type': 'keyword'},  # online, offline, error
                        'last_frame_time': {'type': 'date'},
                        'fps': {'type': 'float'},
                        'error_message': {'type': 'text'},
                        'timestamp': {'type': 'date'}
                    }
                }
            }
        }
        
        for index_name, index_config in indices.items():
            try:
                if not self.es.indices.exists(index=index_name):
                    self.es.indices.create(
                        index=index_name,
                        body=index_config,
                        ignore=400
                    )
                    self.logger.info(f"Created index: {index_name}")
            except Exception as e:
                self.logger.error(f"Error creating index {index_name}: {e}")
    
    def _encrypt_data(self, data):
        """Encrypt sensitive data"""
        if isinstance(data, str):
            data = data.encode()
        elif isinstance(data, list):
            data = json.dumps(data).encode()
        return self.cipher.encrypt(data)
    
    def _decrypt_data(self, encrypted_data):
        """Decrypt sensitive data"""
        try:
            decrypted = self.cipher.decrypt(encrypted_data)
            # Try to decode as JSON first, then as string
            try:
                return json.loads(decrypted.decode())
            except:
                return decrypted.decode()
        except Exception as e:
            self.logger.error(f"Error decrypting data: {e}")
            return None
    
    def check_connection(self):
        """Check Elasticsearch connection"""
        try:
            info = self.es.info()
            return {
                'status': 'connected',
                'cluster_name': info.get('cluster_name'),
                'version': info.get('version', {}).get('number')
            }
        except Exception as e:
            return {
                'status': 'disconnected',
                'error': str(e)
            }
    
    def register_employee(self, employee_data):
        """Register a new employee"""
        try:
            employee_id = employee_data['employee_id']
            
            # Check if employee already exists
            if self.es.exists(index='employees', id=employee_id):
                raise ValueError(f"Employee {employee_id} already exists")
            
            # Encrypt sensitive data
            doc = {
                'employee_id': employee_id,
                'name': employee_data['name'],
                'access_level': employee_data['access_level'],
                'department': employee_data.get('department', 'Unknown'),
                'card_id': employee_data.get('card_id'),
                'is_active': True,
                'created_at': datetime.datetime.now().isoformat(),
                'updated_at': datetime.datetime.now().isoformat()
            }
            
            # Encrypt face embedding if provided
            if 'face_embedding' in employee_data:
                doc['face_embedding'] = self._encrypt_data(employee_data['face_embedding'])
            
            # Encrypt body features if provided
            if 'body_features' in employee_data:
                doc['body_features'] = self._encrypt_data(employee_data['body_features'])
            
            # Index the document
            result = self.es.index(
                index='employees',
                id=employee_id,
                body=doc
            )
            
            self.logger.info(f"Registered employee: {employee_id}")
            return employee_id
            
        except Exception as e:
            self.logger.error(f"Error registering employee: {e}")
            raise
    
    def get_employee(self, employee_id):
        """Get employee details"""
        try:
            result = self.es.get(index='employees', id=employee_id)
            employee = result['_source']
            
            # Decrypt sensitive data
            if 'face_embedding' in employee:
                employee['face_embedding'] = self._decrypt_data(employee['face_embedding'])
            if 'body_features' in employee:
                employee['body_features'] = self._decrypt_data(employee['body_features'])
            
            return employee
            
        except Exception as e:
            self.logger.error(f"Error getting employee {employee_id}: {e}")
            return None
    
    def get_all_employees(self):
        """Get all employees"""
        try:
            search = Search(using=self.es, index='employees')
            search = search.filter('term', is_active=True)
            response = search.execute()
            
            employees = []
            for hit in response:
                employee = hit.to_dict()
                
                # Decrypt sensitive data
                if 'face_embedding' in employee:
                    employee['face_embedding'] = self._decrypt_data(employee['face_embedding'])
                if 'body_features' in employee:
                    employee['body_features'] = self._decrypt_data(employee['body_features'])
                
                employees.append(employee)
            
            return employees
            
        except Exception as e:
            self.logger.error(f"Error getting all employees: {e}")
            return []
    
    def update_employee(self, employee_id, update_data):
        """Update employee details"""
        try:
            # Check if employee exists
            if not self.es.exists(index='employees', id=employee_id):
                return False
            
            # Prepare update document
            doc = {
                'updated_at': datetime.datetime.now().isoformat()
            }
            
            # Add non-sensitive fields
            for field in ['name', 'access_level', 'department', 'card_id', 'is_active']:
                if field in update_data:
                    doc[field] = update_data[field]
            
            # Encrypt sensitive data
            if 'face_embedding' in update_data:
                doc['face_embedding'] = self._encrypt_data(update_data['face_embedding'])
            if 'body_features' in update_data:
                doc['body_features'] = self._encrypt_data(update_data['body_features'])
            
            # Update the document
            self.es.update(
                index='employees',
                id=employee_id,
                body={'doc': doc}
            )
            
            self.logger.info(f"Updated employee: {employee_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating employee {employee_id}: {e}")
            return False
    
    def delete_employee(self, employee_id):
        """Delete employee (soft delete)"""
        try:
            if not self.es.exists(index='employees', id=employee_id):
                return False
            
            # Soft delete by setting is_active to False
            self.es.update(
                index='employees',
                id=employee_id,
                body={
                    'doc': {
                        'is_active': False,
                        'updated_at': datetime.datetime.now().isoformat()
                    }
                }
            )
            
            self.logger.info(f"Deleted employee: {employee_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting employee {employee_id}: {e}")
            return False
    
    def create_access_log(self, log_data):
        """Create access log entry"""
        try:
            log_id = str(uuid.uuid4())
            
            doc = {
                'log_id': log_id,
                'camera_id': log_data['camera_id'],
                'person_id': log_data['person_id'],
                'access_type': log_data['access_type'],
                'access_result': log_data.get('access_result', 'unknown'),
                'confidence_score': log_data.get('confidence_score', 0.0),
                'timestamp': log_data['timestamp'],
                'location': log_data.get('location', 'unknown'),
                'tailgating_detected': log_data.get('tailgating_detected', False),
                'tailgating_count': log_data.get('tailgating_count', 0)
            }
            
            # Encrypt sensitive data
            if 'face_embedding' in log_data:
                doc['face_embedding'] = self._encrypt_data(log_data['face_embedding'])
            if 'body_features' in log_data:
                doc['body_features'] = self._encrypt_data(log_data['body_features'])
            
            # Index the document
            self.es.index(
                index='access_logs',
                id=log_id,
                body=doc
            )
            
            self.logger.info(f"Created access log: {log_id}")
            return log_id
            
        except Exception as e:
            self.logger.error(f"Error creating access log: {e}")
            raise
    
    def get_access_logs(self, start_date=None, end_date=None, camera_id=None, 
                       person_id=None, limit=100):
        """Get access logs with filtering"""
        try:
            search = Search(using=self.es, index='access_logs')
            
            # Add filters
            if start_date:
                search = search.filter('range', timestamp={'gte': start_date})
            if end_date:
                search = search.filter('range', timestamp={'lte': end_date})
            if camera_id:
                search = search.filter('term', camera_id=camera_id)
            if person_id:
                search = search.filter('term', person_id=person_id)
            
            # Sort by timestamp (newest first)
            search = search.sort('-timestamp')
            
            # Limit results
            search = search[:limit]
            
            response = search.execute()
            
            logs = []
            for hit in response:
                log = hit.to_dict()
                
                # Decrypt sensitive data
                if 'face_embedding' in log:
                    log['face_embedding'] = self._decrypt_data(log['face_embedding'])
                if 'body_features' in log:
                    log['body_features'] = self._decrypt_data(log['body_features'])
                
                logs.append(log)
            
            return logs
            
        except Exception as e:
            self.logger.error(f"Error getting access logs: {e}")
            return []
    
    def create_alert(self, alert_data):
        """Create system alert"""
        try:
            alert_id = str(uuid.uuid4())
            
            doc = {
                'alert_id': alert_id,
                'alert_type': alert_data['alert_type'],
                'severity': alert_data.get('severity', 'medium'),
                'description': alert_data['description'],
                'timestamp': datetime.datetime.now().isoformat(),
                'resolved': False
            }
            
            # Add optional fields
            for field in ['camera_id', 'person_id']:
                if field in alert_data:
                    doc[field] = alert_data[field]
            
            # Index the document
            self.es.index(
                index='alerts',
                id=alert_id,
                body=doc
            )
            
            self.logger.info(f"Created alert: {alert_id} - {alert_data['alert_type']}")
            return alert_id
            
        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")
            raise
    
    def get_alerts(self, alert_type=None, start_date=None, end_date=None, limit=50):
        """Get system alerts"""
        try:
            search = Search(using=self.es, index='alerts')
            
            # Add filters
            if alert_type:
                search = search.filter('term', alert_type=alert_type)
            if start_date:
                search = search.filter('range', timestamp={'gte': start_date})
            if end_date:
                search = search.filter('range', timestamp={'lte': end_date})
            
            # Sort by timestamp (newest first)
            search = search.sort('-timestamp')
            
            # Limit results
            search = search[:limit]
            
            response = search.execute()
            
            alerts = []
            for hit in response:
                alerts.append(hit.to_dict())
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error getting alerts: {e}")
            return []
    
    def update_camera_health(self, camera_id, health_data):
        """Update camera health status"""
        try:
            doc = {
                'camera_id': camera_id,
                'status': health_data['status'],
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            # Add optional fields
            for field in ['last_frame_time', 'fps', 'error_message']:
                if field in health_data:
                    doc[field] = health_data[field]
            
            # Index the document
            self.es.index(
                index='camera_health',
                body=doc
            )
            
        except Exception as e:
            self.logger.error(f"Error updating camera health for {camera_id}: {e}")
    
    def get_employee_count(self):
        """Get total number of active employees"""
        try:
            search = Search(using=self.es, index='employees')
            search = search.filter('term', is_active=True)
            response = search.execute()
            return response.hits.total.value
        except Exception as e:
            self.logger.error(f"Error getting employee count: {e}")
            return 0
    
    def get_access_log_count(self):
        """Get total number of access logs"""
        try:
            search = Search(using=self.es, index='access_logs')
            response = search.execute()
            return response.hits.total.value
        except Exception as e:
            self.logger.error(f"Error getting access log count: {e}")
            return 0
    
    def get_tailgating_count(self):
        """Get total number of tailgating incidents"""
        try:
            search = Search(using=self.es, index='access_logs')
            search = search.filter('term', tailgating_detected=True)
            response = search.execute()
            return response.hits.total.value
        except Exception as e:
            self.logger.error(f"Error getting tailgating count: {e}")
            return 0
    
    def get_last_alert(self):
        """Get the most recent alert"""
        try:
            search = Search(using=self.es, index='alerts')
            search = search.sort('-timestamp')
            search = search[:1]
            response = search.execute()
            
            if response.hits:
                return response.hits[0].to_dict()
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting last alert: {e}")
            return None 