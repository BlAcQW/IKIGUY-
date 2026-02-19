import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { 
  CDNConfig, 
  CDNResponse, 
  initializeCDN, 
  getCDNConfig, 
  updateCDNConfig,
  isCDNAvailable,
  getCDNHealth,
  generateCDNUrl,
  loadCDNAsset,
  batchLoadCDNAssets,
  clearCDNCache,
  getCDNCacheStats,
  monitorCDNPerformance
} from '@/utils/cdnIntegration';

interface CDNContextType {
  config: CDNConfig;
  isAvailable: boolean;
  health: {
    available: boolean;
    responseTime: number;
    status: 'healthy' | 'degraded' | 'unavailable';
  };
  updateConfig: (config: Partial<CDNConfig>) => void;
  loadAsset: (path: string) => Promise<CDNResponse>;
  loadAssets: (paths: string[]) => Promise<CDNResponse[]>;
  generateUrl: (path: string) => string;
  clearCache: () => void;
  getCacheStats: () => { size: number; entries: Array<{ key: string; timestamp: number; age: number }> };
  monitorPerformance: (path: string) => Promise<{ cdnTime: number; fallbackTime: number; success: boolean }>;
}

const CDNContext = createContext<CDNContextType | undefined>(undefined);

interface CDNProviderProps {
  children: ReactNode;
  config?: Partial<CDNConfig>;
  autoInitialize?: boolean;
  healthCheckInterval?: number;
}

export function CDNProvider({ 
  children, 
  config = {}, 
  autoInitialize = true,
  healthCheckInterval = 300000 // 5 minutes
}: CDNProviderProps) {
  const [cdnConfig, setCdnConfig] = useState<CDNConfig>(getCDNConfig());
  const [isAvailable, setIsAvailable] = useState(false);
  const [health, setHealth] = useState({
    available: false,
    responseTime: 0,
    status: 'unavailable' as const,
  });

  // Initialize CDN
  useEffect(() => {
    if (autoInitialize) {
      initializeCDN(config);
      setCdnConfig(getCDNConfig());
    }
  }, [autoInitialize, config]);

  // Check CDN availability on mount
  useEffect(() => {
    const checkAvailability = async () => {
      const available = await isCDNAvailable(config);
      setIsAvailable(available);
    };

    checkAvailability();
  }, [config]);

  // Health check
  useEffect(() => {
    const performHealthCheck = async () => {
      const healthStatus = await getCDNHealth(config);
      setHealth(healthStatus);
    };

    // Initial health check
    performHealthCheck();

    // Set up interval for health checks
    const interval = setInterval(performHealthCheck, healthCheckInterval);

    return () => clearInterval(interval);
  }, [config, healthCheckInterval]);

  // Update configuration
  const updateConfig = (newConfig: Partial<CDNConfig>) => {
    updateCDNConfig(newConfig);
    setCdnConfig(getCDNConfig());
  };

  // Load single asset
  const loadAsset = async (path: string): Promise<CDNResponse> => {
    return loadCDNAsset(path, cdnConfig);
  };

  // Load multiple assets
  const loadAssets = async (paths: string[]): Promise<CDNResponse[]> => {
    return batchLoadCDNAssets(paths, cdnConfig);
  };

  // Generate CDN URL
  const generateUrl = (path: string): string => {
    return generateCDNUrl(path, cdnConfig);
  };

  // Clear cache
  const clearCache = () => {
    clearCDNCache();
  };

  // Get cache stats
  const getCacheStats = () => {
    return getCDNCacheStats();
  };

  // Monitor performance
  const monitorPerformance = async (path: string) => {
    return monitorCDNPerformance(path, cdnConfig);
  };

  const contextValue: CDNContextType = {
    config: cdnConfig,
    isAvailable,
    health,
    updateConfig,
    loadAsset,
    loadAssets,
    generateUrl,
    clearCache,
    getCacheStats,
    monitorPerformance,
  };

  return (
    <CDNContext.Provider value={contextValue}>
      {children}
    </CDNContext.Provider>
  );
}

// Hook to use CDN context
export function useCDN() {
  const context = useContext(CDNContext);
  if (context === undefined) {
    throw new Error('useCDN must be used within a CDNProvider');
  }
  return context;
}

// CDN Status Component
interface CDNStatusProps {
  showDetails?: boolean;
  className?: string;
}

export function CDNStatus({ showDetails = false, className = '' }: CDNStatusProps) {
  const { health, isAvailable } = useCDN();

  const getStatusColor = () => {
    switch (health.status) {
      case 'healthy':
        return 'text-green-500';
      case 'degraded':
        return 'text-yellow-500';
      case 'unavailable':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusIcon = () => {
    switch (health.status) {
      case 'healthy':
        return '🟢';
      case 'degraded':
        return '🟡';
      case 'unavailable':
        return '🔴';
      default:
        return '⚪';
    }
  };

  if (!showDetails) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <span>{getStatusIcon()}</span>
        <span className={`text-sm font-medium ${getStatusColor()}`}>
          CDN {health.status}
        </span>
      </div>
    );
  }

  return (
    <div className={`p-4 border rounded-lg ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold">CDN Status</h3>
        <div className="flex items-center space-x-2">
          <span>{getStatusIcon()}</span>
          <span className={`font-medium ${getStatusColor()}`}>
            {health.status}
          </span>
        </div>
      </div>
      
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span>Available:</span>
          <span className={isAvailable ? 'text-green-500' : 'text-red-500'}>
            {isAvailable ? 'Yes' : 'No'}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span>Response Time:</span>
          <span>{health.responseTime.toFixed(2)}ms</span>
        </div>
        
        <div className="flex justify-between">
          <span>Status:</span>
          <span className={getStatusColor()}>
            {health.status}
          </span>
        </div>
      </div>
    </div>
  );
}

// CDN Performance Monitor Component
interface CDNPerformanceMonitorProps {
  paths: string[];
  onPerformanceUpdate?: (results: Array<{ path: string; cdnTime: number; fallbackTime: number; success: boolean }>) => void;
  interval?: number;
  className?: string;
}

export function CDNPerformanceMonitor({ 
  paths, 
  onPerformanceUpdate, 
  interval = 60000, // 1 minute
  className = '' 
}: CDNPerformanceMonitorProps) {
  const { monitorPerformance } = useCDN();
  const [results, setResults] = useState<Array<{ path: string; cdnTime: number; fallbackTime: number; success: boolean }>>([]);

  useEffect(() => {
    const performMonitoring = async () => {
      const monitoringResults = await Promise.all(
        paths.map(async (path) => {
          const result = await monitorPerformance(path);
          return { path, ...result };
        })
      );

      setResults(monitoringResults);
      onPerformanceUpdate?.(monitoringResults);
    };

    // Initial monitoring
    performMonitoring();

    // Set up interval
    const intervalId = setInterval(performMonitoring, interval);

    return () => clearInterval(intervalId);
  }, [paths, interval, monitorPerformance, onPerformanceUpdate]);

  const averageCDNTime = results.length > 0 
    ? results.reduce((sum, r) => sum + r.cdnTime, 0) / results.length 
    : 0;

  const averageFallbackTime = results.length > 0 
    ? results.reduce((sum, r) => sum + r.fallbackTime, 0) / results.length 
    : 0;

  const successRate = results.length > 0 
    ? (results.filter(r => r.success).length / results.length) * 100 
    : 0;

  return (
    <div className={`p-4 border rounded-lg ${className}`}>
      <h3 className="text-lg font-semibold mb-4">CDN Performance</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-500">
            {averageCDNTime.toFixed(2)}ms
          </div>
          <div className="text-sm text-gray-600">Avg CDN Time</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-green-500">
            {averageFallbackTime.toFixed(2)}ms
          </div>
          <div className="text-sm text-gray-600">Avg Fallback Time</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-500">
            {successRate.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">Success Rate</div>
        </div>
      </div>

      {showDetails && (
        <div className="space-y-2">
          <h4 className="font-medium">Individual Results:</h4>
          {results.map((result, index) => (
            <div key={index} className="flex justify-between text-sm">
              <span className="truncate">{result.path}</span>
              <div className="flex space-x-4">
                <span className={result.success ? 'text-green-500' : 'text-red-500'}>
                  {result.success ? '✓' : '✗'}
                </span>
                <span>{result.cdnTime.toFixed(2)}ms</span>
                <span>{result.fallbackTime.toFixed(2)}ms</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// CDN Cache Manager Component
interface CDNCacheManagerProps {
  className?: string;
}

export function CDNCacheManager({ className = '' }: CDNCacheManagerProps) {
  const { clearCache, getCacheStats } = useCDN();
  const [stats, setStats] = useState(getCacheStats());

  const handleClearCache = () => {
    clearCache();
    setStats(getCacheStats());
  };

  const handleRefreshStats = () => {
    setStats(getCacheStats());
  };

  return (
    <div className={`p-4 border rounded-lg ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">CDN Cache</h3>
        <div className="flex space-x-2">
          <button
            onClick={handleRefreshStats}
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Refresh
          </button>
          <button
            onClick={handleClearCache}
            className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600"
          >
            Clear Cache
          </button>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between">
          <span>Cache Size:</span>
          <span className="font-medium">{stats.size} entries</span>
        </div>

        {stats.entries.length > 0 && (
          <div>
            <h4 className="font-medium mb-2">Recent Entries:</h4>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {stats.entries.slice(0, 10).map((entry, index) => (
                <div key={index} className="flex justify-between text-sm">
                  <span className="truncate">{entry.key}</span>
                  <span className="text-gray-500">
                    {Math.round(entry.age / 1000)}s ago
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

