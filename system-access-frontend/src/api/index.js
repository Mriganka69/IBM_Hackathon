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
export const getAccessLogs = (params = {}) => {
  const queryParams = new URLSearchParams(params).toString();
  return api.get(`/access/logs?${queryParams}`);
};

// Employees
export const getEmployees = () => api.get('/employees');
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