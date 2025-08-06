import { useState, useEffect } from 'react';
import { 
  FileText, 
  Download, 
  Filter,
  Calendar,
  RefreshCw
} from 'lucide-react';
import LogTable from '../components/LogTable';
import { getAccessLogs } from '../api';

const AccessLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({});

  useEffect(() => {
    fetchLogs();
  }, [filters]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const data = await getAccessLogs(filters);
      // Ensure logs is always an array
      const logList = Array.isArray(data) ? data : [];
      setLogs(logList);
      setError(null);
    } catch (err) {
      console.error('Error fetching access logs:', err);
      setError('Failed to load access logs');
      
      // Mock data
      setLogs([
        {
          log_id: 1,
          timestamp: new Date(Date.now() - 5000).toISOString(),
          camera_id: 'camera_1',
          person_id: 'EMP001',
          access_type: 'face_recognition',
          access_result: 'granted',
          confidence_score: 0.95
        },
        {
          log_id: 2,
          timestamp: new Date(Date.now() - 15000).toISOString(),
          camera_id: 'camera_2',
          person_id: 'unknown',
          access_type: 'body_recognition',
          access_result: 'denied',
          confidence_score: 0.45
        },
        {
          log_id: 3,
          timestamp: new Date(Date.now() - 30000).toISOString(),
          camera_id: 'camera_1',
          person_id: 'EMP002',
          access_type: 'face_recognition',
          access_result: 'tailgating',
          confidence_score: 0.88
        },
        {
          log_id: 4,
          timestamp: new Date(Date.now() - 60000).toISOString(),
          camera_id: 'camera_3',
          person_id: 'EMP003',
          access_type: 'card_swipe',
          access_result: 'granted',
          confidence_score: 1.0
        },
        {
          log_id: 5,
          timestamp: new Date(Date.now() - 120000).toISOString(),
          camera_id: 'camera_1',
          person_id: 'EMP001',
          access_type: 'face_recognition',
          access_result: 'granted',
          confidence_score: 0.92
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
  };

  const handleExport = () => {
    // Create CSV content
    const headers = ['Timestamp', 'Camera', 'Person ID', 'Access Type', 'Status', 'Confidence'];
    const csvContent = [
      headers.join(','),
      ...(Array.isArray(logs) ? logs.map(log => [
        new Date(log.timestamp).toLocaleString(),
        log.camera_id,
        log.person_id,
        log.access_type,
        log.access_result,
        log.confidence_score ? `${(log.confidence_score * 100).toFixed(1)}%` : 'N/A'
      ].join(',')) : [])
    ].join('\n');

    // Download CSV file
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `access_logs_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const handleRefresh = () => {
    fetchLogs();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Access Logs
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          View and analyze access control events and security incidents
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-center">
            <FileText className="h-5 w-5 text-red-600 dark:text-red-400 mr-2" />
            <span className="text-red-800 dark:text-red-200">{error}</span>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div className="flex items-center space-x-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Recent Access Events
          </h2>
          <button
            onClick={handleRefresh}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors duration-200"
            title="Refresh logs"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={handleExport}
            className="btn-secondary flex items-center"
          >
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <LogTable
        logs={logs}
        loading={loading}
        onFilterChange={handleFilterChange}
      />

      {/* Statistics */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-green-100 dark:bg-green-900">
              <FileText className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Logs</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{Array.isArray(logs) ? logs.length : 0}</p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900">
              <Calendar className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Today</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {Array.isArray(logs) ? logs.filter(log => {
                  const today = new Date().toDateString();
                  const logDate = new Date(log.timestamp).toDateString();
                  return today === logDate;
                }).length : 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-yellow-100 dark:bg-yellow-900">
              <Filter className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Granted</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {Array.isArray(logs) ? logs.filter(log => log.access_result === 'granted').length : 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-red-100 dark:bg-red-900">
              <FileText className="h-6 w-6 text-red-600 dark:text-red-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Denied</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {Array.isArray(logs) ? logs.filter(log => log.access_result === 'denied' || log.access_result === 'tailgating').length : 0}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AccessLogs; 