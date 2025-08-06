import axios from 'axios';

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
export const getCameras = () => api.get('/cameras');
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