import axios from 'axios';
import { formatCameraName, getCameraLocation } from '../utils';

const API_BASE_URL = 'http://localhost:5000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens if needed
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Health check
export const checkHealth = () => api.get('/health');

// System statistics
export const getSystemStats = () => api.get('/system/stats');

// Camera endpoints
export const getCameras = async () => {
  const response = await api.get('/cameras');
  // Convert cameras object to array and normalize field names
  if (response.cameras && typeof response.cameras === 'object') {
    const camerasArray = Object.values(response.cameras).map(camera => ({
      ...camera,
      personCount: camera.person_count || camera.personCount || 0,
      lastFrame: camera.last_frame_time || camera.lastFrame,
      // Ensure all required fields exist
      status: camera.status || 'unknown',
      fps: camera.fps || 0,
      name: camera.name || formatCameraName(camera.id),
      location: camera.location || getCameraLocation(camera.id)
    }));
    return {
      ...response,
      cameras: camerasArray
    };
  }
  return response;
};
export const getCameraStatus = (cameraId) => api.get(`/cameras/${cameraId}`);
export const getCameraHealth = (cameraId) => api.get(`/cameras/${cameraId}/health`);

// Access logs
export const getAccessLogs = async (params = {}) => {
  const queryParams = new URLSearchParams(params).toString();
  const response = await api.get(`/access/logs?${queryParams}`);
  // Ensure logs is always an array and normalize field names
  if (response.logs && Array.isArray(response.logs)) {
    return response.logs.map(log => ({
      ...log,
      log_id: log.id || log.log_id,
      access_result: log.access_type || log.access_result,
      confidence_score: log.confidence || log.confidence_score,
      // Ensure all required fields exist
      timestamp: log.timestamp || new Date().toISOString(),
      camera_id: log.camera_id || 'unknown',
      person_id: log.person_id || 'unknown',
      access_type: log.access_type || 'unknown'
    }));
  } else if (Array.isArray(response)) {
    return response;
  }
  return [];
};

// Employees
export const getEmployees = async () => {
  const response = await api.get('/employees');
  // Ensure employees is always an array and normalize field names
  if (response.employees && Array.isArray(response.employees)) {
    return response.employees.map(employee => ({
      ...employee,
      employee_id: employee.id || employee.employee_id,
      // Ensure all required fields exist
      name: employee.name || 'Unknown',
      email: employee.email || '',
      department: employee.department || '',
      position: employee.position || '',
      face_image: employee.face_snapshot || employee.face_image || '',
      registered_date: employee.registered_date || new Date().toISOString(),
      status: employee.status || 'active'
    }));
  } else if (Array.isArray(response)) {
    return response;
  }
  return [];
};
export const getEmployee = (employeeId) => api.get(`/employees/${employeeId}`);
export const createEmployee = (employeeData) => api.post('/employees', employeeData);
export const updateEmployee = (employeeId, employeeData) => 
  api.put(`/employees/${employeeId}`, employeeData);
export const deleteEmployee = (employeeId) => api.delete(`/employees/${employeeId}`);

// Real-time video stream URL
export const getVideoStreamUrl = (cameraId) => 
  `${API_BASE_URL}/cameras/${cameraId}/stream`;

// WebSocket connection for real-time updates
export const getWebSocketUrl = () => 'ws://localhost:5000/ws';

export default api; 