import { useState, useEffect } from 'react';
import {
  Users,
  Shield,
  AlertTriangle,
  Activity,
  TrendingUp,
  Wifi,
  WifiOff
} from 'lucide-react';
import CameraCard from '../components/CameraCard';
import { getSystemStats, getCameras } from '../api';
import { formatRelativeTime } from '../utils';

const Dashboard = () => {
  const [systemStats, setSystemStats] = useState(null);
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [statsData, camerasData] = await Promise.all([
          getSystemStats(),
          getCameras()
        ]);

        setSystemStats(statsData);

        // Ensure cameras is always an array
        const cameraList = Array.isArray(camerasData?.cameras)
          ? camerasData.cameras
          : Array.isArray(camerasData)
            ? camerasData
            : [];

        setCameras(cameraList);
        setError(null);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data');

        // Set fallback mock data
        setSystemStats({
          total_people_detected: 42,
          total_access_granted: 156,
          total_access_denied: 8,
          total_tailgating_incidents: 3,
          active_cameras: 2,
          total_cameras: 4,
          system_uptime: '2 days, 14 hours',
          last_update: new Date().toISOString()
        });

        setCameras([
          {
            id: 'camera_1',
            name: 'Main Entrance',
            status: 'online',
            personCount: 2,
            fps: 30,
            lastFrame: new Date().toISOString()
          },
          {
            id: 'camera_2',
            name: 'Office Floor',
            status: 'online',
            personCount: 1,
            fps: 28,
            lastFrame: new Date().toISOString()
          },
          {
            id: 'camera_3',
            name: 'Parking Lot',
            status: 'offline',
            personCount: 0,
            fps: 0,
            error: 'Connection lost'
          },
          {
            id: 'camera_4',
            name: 'Server Room',
            status: 'error',
            personCount: 0,
            fps: 0,
            error: 'Hardware malfunction'
          }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Refresh data every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const StatCard = ({ title, value, icon: Icon, color = 'blue', subtitle = '' }) => (
    <div className="card p-6">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg bg-${color}-100 dark:bg-${color}-900`}>
          <Icon className={`h-6 w-6 text-${color}-600 dark:text-${color}-400`} />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 dark:text-gray-400">{subtitle}</p>
          )}
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[...Array(2)].map((_, i) => (
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
          Dashboard
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Real-time overview of the Intelligent Office Access Management System
        </p>
        {systemStats?.last_update && (
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Last updated: {formatRelativeTime(systemStats.last_update)}
          </p>
        )}
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

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="People Detected"
          value={systemStats?.total_people_detected || 0}
          icon={Users}
          color="blue"
          subtitle="Currently in view"
        />
        <StatCard
          title="Access Granted"
          value={systemStats?.total_access_granted || 0}
          icon={Shield}
          color="green"
          subtitle="Today"
        />
        <StatCard
          title="Access Denied"
          value={systemStats?.total_access_denied || 0}
          icon={AlertTriangle}
          color="red"
          subtitle="Today"
        />
        <StatCard
          title="Tailgating Incidents"
          value={systemStats?.total_tailgating_incidents || 0}
          icon={Activity}
          color="orange"
          subtitle="Today"
        />
      </div>

      {/* Camera Status Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Camera Status
            </h2>
            <div className="flex items-center space-x-2">
              <Wifi className="h-4 w-4 text-green-600" />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {systemStats?.active_cameras || 0} / {systemStats?.total_cameras || 0} Active
              </span>
            </div>
          </div>

          <div className="space-y-3">
            {Array.isArray(cameras) && cameras.map((camera) => (
              <div key={camera.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="flex items-center space-x-3">
                  {camera.status === 'online' ? (
                    <Wifi className="h-4 w-4 text-green-600" />
                  ) : (
                    <WifiOff className="h-4 w-4 text-red-600" />
                  )}
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {camera.name}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {camera.personCount} person{camera.personCount !== 1 ? 's' : ''} detected
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    camera.status === 'online'
                      ? 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-400'
                      : 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-400'
                  }`}>
                    {camera.status}
                  </span>
                  {camera.fps > 0 && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {camera.fps} FPS
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              System Health
            </h2>
            <TrendingUp className="h-5 w-5 text-green-600" />
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-gray-400">System Uptime</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {systemStats?.system_uptime || 'Unknown'}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-gray-400">Active Cameras</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {systemStats?.active_cameras || 0} / {systemStats?.total_cameras || 0}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-gray-400">Total Access Events</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {(systemStats?.total_access_granted || 0) + (systemStats?.total_access_denied || 0)}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-gray-400">Success Rate</span>
              <span className="font-medium text-green-600">
                {systemStats?.total_access_granted && systemStats?.total_access_denied
                  ? `${Math.round((systemStats.total_access_granted / (systemStats.total_access_granted + systemStats.total_access_denied)) * 100)}%`
                  : '100%'
                }
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Camera Grid */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Live Camera Feeds
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.isArray(cameras) && cameras.map((camera) => (
            <CameraCard
              key={camera.id}
              camera={camera}
              onClick={() => {
                window.location.href = `/live-feed?camera=${camera.id}`;
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
