// Format timestamp to readable date
export const formatDate = (timestamp) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString();
  };
  
  // Format relative time (e.g., "2 minutes ago")
  export const formatRelativeTime = (timestamp) => {
    if (!timestamp) return 'N/A';
    
    const now = new Date();
    const date = new Date(timestamp);
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    return `${Math.floor(diffInSeconds / 86400)} days ago`;
  };
  
  // Get status color based on status string
  export const getStatusColor = (status) => {
    const statusColors = {
      online: 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-400',
      offline: 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-400',
      error: 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-400',
      granted: 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-400',
      denied: 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-400',
      tailgating: 'text-orange-600 bg-orange-100 dark:bg-orange-900 dark:text-orange-400',
      active: 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-400',
      inactive: 'text-gray-600 bg-gray-100 dark:bg-gray-900 dark:text-gray-400',
    };
    
    return statusColors[status?.toLowerCase()] || 'text-gray-600 bg-gray-100 dark:bg-gray-900 dark:text-gray-400';
  };
  
  // Format camera name
  export const formatCameraName = (cameraId) => {
    if (!cameraId) return 'Unknown Camera';
    
    // Convert camera_1 to "Camera 1"
    return cameraId.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  };
  
  // Format employee ID
  export const formatEmployeeId = (employeeId) => {
    if (!employeeId) return 'N/A';
    return employeeId.toUpperCase();
  };
  
  // Generate random ID for testing
  export const generateId = () => {
    return Math.random().toString(36).substr(2, 9);
  };
  
  // Debounce function for search inputs
  export const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  };
  
  // Format file size
  export const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  
  // Validate email format
  export const isValidEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };
  
  // Format access type
  export const formatAccessType = (accessType) => {
    const types = {
      card_swipe: 'Card Swipe',
      face_recognition: 'Face Recognition',
      body_recognition: 'Body Recognition',
    };
    return types[accessType] || accessType;
  };
  
  // Get camera location from camera ID
  export const getCameraLocation = (cameraId) => {
    const locations = {
      camera_1: 'Main Entrance',
      camera_2: 'Office Floor',
      camera_3: 'Parking Lot',
      camera_4: 'Server Room',
    };
    return locations[cameraId] || 'Unknown Location';
  }; 