import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  Video, 
  VideoOff, 
  Maximize, 
  Minimize, 
  Settings,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Users,
  Activity
} from 'lucide-react';
import { getCameras, getVideoStreamUrl } from '../api';
import { formatRelativeTime, getCameraLocation } from '../utils';

const LiveFeed = () => {
  const [searchParams] = useSearchParams();
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [cameras, setCameras] = useState([]);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const cameraId = searchParams.get('camera') || 'camera_1';

  useEffect(() => {
    const fetchCameras = async () => {
      try {
        const camerasData = await getCameras();
        setCameras(camerasData);
        const camera = camerasData.find(c => c.id === cameraId) || camerasData[0];
        setSelectedCamera(camera);
        setError(null);
      } catch (err) {
        console.error('Error fetching cameras:', err);
        setError('Failed to load cameras');
        
        // Mock data
        const mockCameras = [
          {
            id: 'camera_1',
            name: 'Main Entrance',
            status: 'online',
            location: 'Main Entrance'
          },
          {
            id: 'camera_2',
            name: 'Office Floor',
            status: 'online',
            location: 'Office Floor'
          }
        ];
        setCameras(mockCameras);
        setSelectedCamera(mockCameras.find(c => c.id === cameraId) || mockCameras[0]);
      } finally {
        setLoading(false);
      }
    };

    fetchCameras();
  }, [cameraId]);

  useEffect(() => {
    // Mock real-time logs
    const mockLogs = [
      {
        id: 1,
        timestamp: new Date(Date.now() - 5000),
        message: 'Employee 123 Access Granted',
        type: 'success',
        personId: '123'
      },
      {
        id: 2,
        timestamp: new Date(Date.now() - 15000),
        message: 'Tailgating Detected - Multiple persons detected',
        type: 'warning',
        personId: '124'
      },
      {
        id: 3,
        timestamp: new Date(Date.now() - 30000),
        message: 'Unknown Person Detected',
        type: 'error',
        personId: 'unknown'
      }
    ];
    setLogs(mockLogs);

    // Simulate new logs
    const interval = setInterval(() => {
      const newLog = {
        id: Date.now(),
        timestamp: new Date(),
        message: `Person ${Math.floor(Math.random() * 1000)} detected`,
        type: ['success', 'warning', 'error'][Math.floor(Math.random() * 3)],
        personId: Math.floor(Math.random() * 1000).toString()
      };
      setLogs(prev => [newLog, ...prev.slice(0, 9)]);
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      videoRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const getLogIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Activity className="h-4 w-4 text-gray-600" />;
    }
  };

  const getLogColor = (type) => {
    switch (type) {
      case 'success':
        return 'border-l-green-500 bg-green-50 dark:bg-green-900';
      case 'warning':
        return 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-900';
      case 'error':
        return 'border-l-red-500 bg-red-50 dark:bg-red-900';
      default:
        return 'border-l-gray-500 bg-gray-50 dark:bg-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
          <div className="h-96 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Live Access Monitoring
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Real-time video feed with person detection and access control
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Camera Selection */}
        <div className="lg:col-span-1">
          <div className="card p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Camera Selection
            </h2>
            <div className="space-y-2">
              {cameras.map((camera) => (
                <button
                  key={camera.id}
                  onClick={() => setSelectedCamera(camera)}
                  className={`w-full p-3 text-left rounded-lg transition-colors duration-200 ${
                    selectedCamera?.id === camera.id
                      ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    {camera.status === 'online' ? (
                      <Video className="h-4 w-4 text-green-600" />
                    ) : (
                      <VideoOff className="h-4 w-4 text-red-600" />
                    )}
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {camera.name}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {getCameraLocation(camera.id)}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Video Feed */}
        <div className="lg:col-span-2">
          <div className="card p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {selectedCamera?.name || 'Camera Feed'}
              </h2>
              <div className="flex items-center space-x-2">
                <button
                  onClick={toggleFullscreen}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-200"
                  title="Toggle fullscreen"
                >
                  {isFullscreen ? (
                    <Minimize className="h-4 w-4" />
                  ) : (
                    <Maximize className="h-4 w-4" />
                  )}
                </button>
                <button
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-200"
                  title="Settings"
                >
                  <Settings className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="relative bg-black rounded-lg overflow-hidden">
              {selectedCamera?.status === 'online' ? (
                <>
                  <video
                    ref={videoRef}
                    className="w-full h-96 object-cover"
                    autoPlay
                    muted
                    loop
                    src={getVideoStreamUrl(selectedCamera.id)}
                    onError={() => setError('Failed to load video stream')}
                  />
                  <canvas
                    ref={canvasRef}
                    className="absolute top-0 left-0 w-full h-full pointer-events-none"
                  />
                  
                  {/* Mock bounding boxes */}
                  <div className="absolute top-4 left-4 bg-green-500 text-white px-2 py-1 rounded text-sm">
                    Person ID: 123
                  </div>
                  <div className="absolute top-4 right-4 bg-yellow-500 text-white px-2 py-1 rounded text-sm">
                    Person ID: 124
                  </div>
                </>
              ) : (
                <div className="w-full h-96 flex items-center justify-center bg-gray-900">
                  <div className="text-center">
                    <VideoOff className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400">Camera Offline</p>
                    <p className="text-sm text-gray-500 mt-2">
                      {selectedCamera?.error || 'No video feed available'}
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Video Stats */}
            <div className="mt-4 grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-sm text-gray-600 dark:text-gray-400">People Detected</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">2</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600 dark:text-gray-400">FPS</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">30</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600 dark:text-gray-400">Status</p>
                <p className="text-2xl font-bold text-green-600">Active</p>
              </div>
            </div>
          </div>
        </div>

        {/* Live Logs */}
        <div className="lg:col-span-1">
          <div className="card p-4 h-full">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Live Logs
            </h2>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className={`p-3 rounded-lg border-l-4 ${getLogColor(log.type)}`}
                >
                  <div className="flex items-start space-x-3">
                    {getLogIcon(log.type)}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {log.message}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {formatRelativeTime(log.timestamp)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mt-6 p-4 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400 mr-2" />
            <span className="text-red-800 dark:text-red-200">{error}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveFeed; 