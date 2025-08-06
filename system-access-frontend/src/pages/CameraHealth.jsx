import { useState, useEffect } from 'react';
import { 
  Camera, 
  Wifi, 
  WifiOff, 
  AlertTriangle, 
  CheckCircle,
  XCircle,
  Activity,
  Clock,
  Settings,
  RefreshCw,
  TrendingUp,
  TrendingDown
} from 'lucide-react';
import { getCameras, getCameraHealth } from '../api';
import { formatRelativeTime, getCameraLocation } from '../utils';

const CameraHealth = () => {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCamera, setSelectedCamera] = useState(null);

  useEffect(() => {
    fetchCameras();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchCameras, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchCameras = async () => {
    try {
      setLoading(true);
      const camerasData = await getCameras();
      // Ensure cameras is always an array
      const cameraList = Array.isArray(camerasData?.cameras)
        ? camerasData.cameras
        : Array.isArray(camerasData)
          ? camerasData
          : [];
      setCameras(cameraList);
      setError(null);
    } catch (err) {
      console.error('Error fetching cameras:', err);
      setError('Failed to load camera data');
      
      // Mock data
      setCameras([
        {
          id: 'camera_1',
          name: 'Main Entrance',
          status: 'online',
          location: 'Main Entrance',
          fps: 30,
          resolution: '1920x1080',
          lastFrame: new Date(Date.now() - 5000).toISOString(),
          uptime: '2 days, 14 hours',
          error: null,
          alerts: []
        },
        {
          id: 'camera_2',
          name: 'Office Floor',
          status: 'online',
          location: 'Office Floor',
          fps: 28,
          resolution: '1920x1080',
          lastFrame: new Date(Date.now() - 3000).toISOString(),
          uptime: '1 day, 8 hours',
          error: null,
          alerts: []
        },
        {
          id: 'camera_3',
          name: 'Parking Lot',
          status: 'offline',
          location: 'Parking Lot',
          fps: 0,
          resolution: '1920x1080',
          lastFrame: new Date(Date.now() - 300000).toISOString(),
          uptime: '0 days, 0 hours',
          error: 'Connection lost - Network timeout',
          alerts: ['Network connectivity issue', 'Camera not responding']
        },
        {
          id: 'camera_4',
          name: 'Server Room',
          status: 'error',
          location: 'Server Room',
          fps: 0,
          resolution: '1920x1080',
          lastFrame: new Date(Date.now() - 600000).toISOString(),
          uptime: '0 days, 0 hours',
          error: 'Hardware malfunction - Sensor failure',
          alerts: ['Hardware error', 'Temperature warning', 'Low disk space']
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'online':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'offline':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'error':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      default:
        return <Camera className="h-5 w-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'online':
        return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-400';
      case 'offline':
        return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-400';
      case 'error':
        return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-400';
      default:
        return 'text-gray-600 bg-gray-100 dark:bg-gray-900 dark:text-gray-400';
    }
  };

  const getHealthScore = (camera) => {
    if (camera.status === 'online' && camera.fps > 25) return 100;
    if (camera.status === 'online' && camera.fps > 15) return 80;
    if (camera.status === 'online') return 60;
    if (camera.status === 'offline') return 20;
    return 0;
  };

  const getHealthColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Camera Health
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Monitor camera status, performance, and system health
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400 mr-2" />
            <span className="text-red-800 dark:text-red-200">{error}</span>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-green-100 dark:bg-green-900">
              <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Online</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {cameras.filter(c => c.status === 'online').length}
              </p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-red-100 dark:bg-red-900">
              <XCircle className="h-6 w-6 text-red-600 dark:text-red-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Offline</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {cameras.filter(c => c.status === 'offline').length}
              </p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-yellow-100 dark:bg-yellow-900">
              <AlertTriangle className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Errors</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {cameras.filter(c => c.status === 'error').length}
              </p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900">
              <Activity className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {cameras.length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Camera Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cameras.map((camera) => {
          const healthScore = getHealthScore(camera);
          return (
            <div key={camera.id} className="card p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(camera.status)}
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      {camera.name}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {getCameraLocation(camera.id)}
                    </p>
                  </div>
                </div>
                <span
                  className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                    camera.status
                  )}`}
                >
                  {camera.status}
                </span>
              </div>

              {/* Health Score */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Health Score
                  </span>
                  <span className={`text-lg font-bold ${getHealthColor(healthScore)}`}>
                    {healthScore}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      healthScore >= 80 ? 'bg-green-600' :
                      healthScore >= 60 ? 'bg-yellow-600' :
                      healthScore >= 40 ? 'bg-orange-600' : 'bg-red-600'
                    }`}
                    style={{ width: `${healthScore}%` }}
                  ></div>
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="space-y-3 mb-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">FPS</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {camera.fps || 0}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Resolution</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {camera.resolution || 'N/A'}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Uptime</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {camera.uptime || 'N/A'}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Last Frame</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatRelativeTime(camera.lastFrame)}
                  </span>
                </div>
              </div>

              {/* Error Messages */}
              {camera.error && (
                <div className="mb-4 p-3 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-800 rounded-lg">
                  <p className="text-sm text-red-800 dark:text-red-200">
                    {camera.error}
                  </p>
                </div>
              )}

              {/* Alerts */}
              {camera.alerts && camera.alerts.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Alerts
                  </h4>
                  {camera.alerts.map((alert, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <AlertTriangle className="h-3 w-3 text-yellow-600" />
                      <span className="text-xs text-gray-600 dark:text-gray-400">
                        {alert}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Actions */}
              <div className="mt-4 flex items-center justify-between">
                <button
                  onClick={() => setSelectedCamera(camera)}
                  className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                >
                  View Details
                </button>
                <div className="flex items-center space-x-2">
                  <button
                    className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors duration-200"
                    title="Settings"
                  >
                    <Settings className="h-4 w-4" />
                  </button>
                  <button
                    onClick={fetchCameras}
                    className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors duration-200"
                    title="Refresh"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Camera Details Modal */}
      {selectedCamera && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {selectedCamera.name} - Details
              </h2>
              <button
                onClick={() => setSelectedCamera(null)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <XCircle className="h-6 w-6" />
              </button>
            </div>

            <div className="space-y-6">
              {/* Status Overview */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Status</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {selectedCamera.status}
                  </p>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Health Score</p>
                  <p className={`text-lg font-semibold ${getHealthColor(getHealthScore(selectedCamera))}`}>
                    {getHealthScore(selectedCamera)}%
                  </p>
                </div>
              </div>

              {/* Performance Metrics */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                  Performance Metrics
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <p className="text-sm text-gray-600 dark:text-gray-400">FPS</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {selectedCamera.fps || 0}
                    </p>
                  </div>
                  <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Resolution</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {selectedCamera.resolution || 'N/A'}
                    </p>
                  </div>
                  <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Uptime</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {selectedCamera.uptime || 'N/A'}
                    </p>
                  </div>
                  <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Last Frame</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {formatRelativeTime(selectedCamera.lastFrame)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Error Details */}
              {selectedCamera.error && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                    Error Details
                  </h3>
                  <div className="p-4 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-800 rounded-lg">
                    <p className="text-red-800 dark:text-red-200">
                      {selectedCamera.error}
                    </p>
                  </div>
                </div>
              )}

              {/* Alerts */}
              {selectedCamera.alerts && selectedCamera.alerts.length > 0 && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                    Active Alerts
                  </h3>
                  <div className="space-y-2">
                    {selectedCamera.alerts.map((alert, index) => (
                      <div key={index} className="flex items-center space-x-3 p-3 bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                        <AlertTriangle className="h-4 w-4 text-yellow-600" />
                        <span className="text-yellow-800 dark:text-yellow-200">
                          {alert}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CameraHealth; 