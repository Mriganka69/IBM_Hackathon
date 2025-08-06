import { useState, useEffect } from 'react';
import { Camera, Wifi, WifiOff, AlertTriangle } from 'lucide-react';
import { getStatusColor, formatCameraName, getCameraLocation } from '../utils';

const CameraCard = ({ camera, onClick, isSelected = false }) => {
  const [imageError, setImageError] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    // Update timestamp every 30 seconds
    const interval = setInterval(() => {
      setLastUpdate(new Date());
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'online':
        return <Wifi className="h-4 w-4 text-green-600" />;
      case 'offline':
        return <WifiOff className="h-4 w-4 text-red-600" />;
      case 'error':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      default:
        return <Camera className="h-4 w-4 text-gray-600" />;
    }
  };

  const handleImageError = () => {
    setImageError(true);
  };

  return (
    <div
      className={`card p-4 cursor-pointer transition-all duration-200 hover:shadow-md ${
        isSelected ? 'ring-2 ring-primary-500' : ''
      }`}
      onClick={() => onClick(camera)}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          {getStatusIcon(camera.status)}
          <h3 className="font-medium text-gray-900 dark:text-white">
            {formatCameraName(camera.id)}
          </h3>
        </div>
        <span
          className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
            camera.status
          )}`}
        >
          {camera.status || 'Unknown'}
        </span>
      </div>

      <div className="relative mb-3">
        {imageError ? (
          <div className="w-full h-32 bg-gray-200 dark:bg-gray-700 rounded-lg flex items-center justify-center">
            <Camera className="h-8 w-8 text-gray-400" />
          </div>
        ) : (
          <img
            src={camera.thumbnail || `/api/cameras/${camera.id}/thumbnail`}
            alt={`${formatCameraName(camera.id)} thumbnail`}
            className="w-full h-32 object-cover rounded-lg"
            onError={handleImageError}
          />
        )}
        
        {/* Overlay for person count */}
        {camera.personCount > 0 && (
          <div className="absolute top-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
            {camera.personCount} person{camera.personCount !== 1 ? 's' : ''}
          </div>
        )}
      </div>

      <div className="space-y-2">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {getCameraLocation(camera.id)}
        </p>
        
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>Last update: {lastUpdate.toLocaleTimeString()}</span>
          {camera.fps && (
            <span>{camera.fps} FPS</span>
          )}
        </div>

        {camera.error && (
          <div className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900 p-2 rounded">
            {camera.error}
          </div>
        )}
      </div>
    </div>
  );
};

export default CameraCard; 