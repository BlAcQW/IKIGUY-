/**
 * PWA Cache Settings Component
 * Displays cache status and allows cache management
 */

import { useState, useEffect } from 'react';
import { Database, Trash2, RefreshCw, HardDrive } from 'lucide-react';
import { usePWA, formatBytes } from '../hooks/usePWA';
import toast from 'react-hot-toast';

export function PWACacheSettings() {
  const { cacheStatus, getCacheStatus, clearCache } = usePWA();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadCacheStatus();
  }, []);

  const loadCacheStatus = async () => {
    setLoading(true);
    try {
      await getCacheStatus();
    } catch (error) {
      console.error('Failed to load cache status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async () => {
    if (!confirm('Are you sure you want to clear all cached data? This will remove offline content.')) {
      return;
    }

    setLoading(true);
    try {
      await clearCache();
      toast.success('Cache cleared successfully');
      setTimeout(loadCacheStatus, 500); // Reload status after a short delay
    } catch (error) {
      console.error('Failed to clear cache:', error);
      toast.error('Failed to clear cache');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-800 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
          <Database className="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Offline Storage</h3>
          <p className="text-sm text-gray-400">Manage cached content for offline access</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-6 h-6 text-purple-500 animate-spin" />
        </div>
      ) : cacheStatus ? (
        <>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <HardDrive className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-400">Audio Files</span>
              </div>
              <p className="text-2xl font-bold text-white">{cacheStatus.audioFiles}</p>
              <p className="text-xs text-gray-400 mt-1">
                {formatBytes(cacheStatus.audioSize)}
              </p>
            </div>

            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Database className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-400">Static Assets</span>
              </div>
              <p className="text-2xl font-bold text-white">{cacheStatus.staticFiles}</p>
              <p className="text-xs text-gray-400 mt-1">
                {formatBytes(cacheStatus.staticSize)}
              </p>
            </div>
          </div>

          <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 mb-4">
            <p className="text-sm text-blue-300">
              <strong>Tip:</strong> Cached audio files allow you to listen offline. The app automatically manages storage up to 500MB.
            </p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={loadCacheStatus}
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2.5 rounded-lg font-medium transition disabled:opacity-50"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>

            <button
              onClick={handleClearCache}
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 text-white px-4 py-2.5 rounded-lg font-medium transition disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4" />
              Clear Cache
            </button>
          </div>
        </>
      ) : (
        <div className="text-center py-8">
          <p className="text-gray-400 mb-4">Cache status unavailable</p>
          <button
            onClick={loadCacheStatus}
            className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg font-medium transition"
          >
            Load Status
          </button>
        </div>
      )}
    </div>
  );
}
