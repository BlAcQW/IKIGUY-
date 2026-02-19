import { useEffect, useRef, useState } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';

interface PerformanceMetrics {
  pageLoadTime: number;
  apiResponseTime: number;
  memoryUsage: number;
  networkRequests: number;
  errors: number;
  timestamp: number;
}

interface PerformanceMonitorProps {
  children: React.ReactNode;
  enabled?: boolean;
}

export default function PerformanceMonitor({ children, enabled = true }: PerformanceMonitorProps) {
  const [metrics, setMetrics] = useState<PerformanceMetrics[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const { toast } = useToast();
  const startTime = useRef<number>(performance.now());
  const apiRequests = useRef<number>(0);
  const errors = useRef<number>(0);

  useEffect(() => {
    if (!enabled) return;

    // Start monitoring when component mounts
    startMonitoring();

    // Cleanup on unmount
    return () => {
      stopMonitoring();
    };
  }, [enabled]);

  const startMonitoring = () => {
    setIsMonitoring(true);
    startTime.current = performance.now();
    
    // Monitor page load performance
    if ('performance' in window) {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'navigation') {
            const navEntry = entry as PerformanceNavigationTiming;
            const loadTime = navEntry.loadEventEnd - navEntry.loadEventStart;
            
            addMetric({
              pageLoadTime: loadTime,
              apiResponseTime: 0,
              memoryUsage: getMemoryUsage(),
              networkRequests: apiRequests.current,
              errors: errors.current,
              timestamp: Date.now()
            });
          }
        }
      });
      
      observer.observe({ entryTypes: ['navigation'] });
    }

    // Monitor API requests
    monitorApiRequests();
    
    // Monitor errors
    monitorErrors();
    
    // Monitor memory usage
    const memoryInterval = setInterval(() => {
      const currentMetrics = {
        pageLoadTime: 0,
        apiResponseTime: 0,
        memoryUsage: getMemoryUsage(),
        networkRequests: apiRequests.current,
        errors: errors.current,
        timestamp: Date.now()
      };
      
      addMetric(currentMetrics);
    }, 30000); // Every 30 seconds

    return () => {
      clearInterval(memoryInterval);
    };
  };

  const stopMonitoring = () => {
    setIsMonitoring(false);
  };

  const monitorApiRequests = () => {
    // Intercept fetch requests
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const startTime = performance.now();
      apiRequests.current++;
      
      try {
        const response = await originalFetch(...args);
        const endTime = performance.now();
        const responseTime = endTime - startTime;
        
        addMetric({
          pageLoadTime: 0,
          apiResponseTime: responseTime,
          memoryUsage: getMemoryUsage(),
          networkRequests: apiRequests.current,
          errors: errors.current,
          timestamp: Date.now()
        });
        
        return response;
      } catch (error) {
        errors.current++;
        throw error;
      }
    };
  };

  const monitorErrors = () => {
    const originalErrorHandler = window.onerror;
    const originalUnhandledRejectionHandler = window.onunhandledrejection;
    
    window.onerror = (message, source, lineno, colno, error) => {
      errors.current++;
      addMetric({
        pageLoadTime: 0,
        apiResponseTime: 0,
        memoryUsage: getMemoryUsage(),
        networkRequests: apiRequests.current,
        errors: errors.current,
        timestamp: Date.now()
      });
      
      if (originalErrorHandler) {
        return originalErrorHandler(message, source, lineno, colno, error);
      }
    };
    
    window.onunhandledrejection = (event) => {
      errors.current++;
      addMetric({
        pageLoadTime: 0,
        apiResponseTime: 0,
        memoryUsage: getMemoryUsage(),
        networkRequests: apiRequests.current,
        errors: errors.current,
        timestamp: Date.now()
      });
      
      if (originalUnhandledRejectionHandler) {
        return originalUnhandledRejectionHandler(event);
      }
    };
  };

  const getMemoryUsage = (): number => {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return memory.usedJSHeapSize / 1024 / 1024; // Convert to MB
    }
    return 0;
  };

  const addMetric = async (metric: PerformanceMetrics) => {
    setMetrics(prev => [...prev, metric]);
    
    // Keep only last 100 metrics
    if (metrics.length > 100) {
      setMetrics(prev => prev.slice(-100));
    }
    
    // Send to Supabase for analytics (disabled to prevent CORS errors)
    // try {
    //   await supabase.functions.invoke('track-performance', {
    //     body: {
    //       action: 'track',
    //       data: metric
    //     }
    //   });
    // } catch (error) {
    //   console.error('Failed to track performance metric:', error);
    // }
    
    // Alert if performance is poor
    if (metric.pageLoadTime > 3000) { // 3 seconds
      toast({
        title: "Slow Page Load",
        description: `Page took ${(metric.pageLoadTime / 1000).toFixed(1)}s to load`,
        variant: "destructive"
      });
    }
    
    if (metric.apiResponseTime > 2000) { // 2 seconds
      toast({
        title: "Slow API Response",
        description: `API request took ${(metric.apiResponseTime / 1000).toFixed(1)}s`,
        variant: "destructive"
      });
    }
    
    if (metric.memoryUsage > 100) { // 100MB
      toast({
        title: "High Memory Usage",
        description: `Memory usage: ${metric.memoryUsage.toFixed(1)}MB`,
        variant: "destructive"
      });
    }
  };

  const getAverageMetrics = () => {
    if (metrics.length === 0) return null;
    
    const totals = metrics.reduce((acc, metric) => ({
      pageLoadTime: acc.pageLoadTime + metric.pageLoadTime,
      apiResponseTime: acc.apiResponseTime + metric.apiResponseTime,
      memoryUsage: acc.memoryUsage + metric.memoryUsage,
      networkRequests: acc.networkRequests + metric.networkRequests,
      errors: acc.errors + metric.errors
    }), {
      pageLoadTime: 0,
      apiResponseTime: 0,
      memoryUsage: 0,
      networkRequests: 0,
      errors: 0
    });
    
    return {
      avgPageLoadTime: totals.pageLoadTime / metrics.length,
      avgApiResponseTime: totals.apiResponseTime / metrics.length,
      avgMemoryUsage: totals.memoryUsage / metrics.length,
      totalNetworkRequests: totals.networkRequests,
      totalErrors: totals.errors
    };
  };

  const exportMetrics = () => {
    const dataStr = JSON.stringify(metrics, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `performance-metrics-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const averageMetrics = getAverageMetrics();

  return (
    <div>
      {children}
      
      {/* Performance Debug Panel (only in development) */}
      {import.meta.env.DEV && isMonitoring && (
        <div className="fixed bottom-4 right-4 bg-black/80 text-white p-4 rounded-lg text-xs max-w-xs">
          <h3 className="font-bold mb-2">Performance Monitor</h3>
          {averageMetrics && (
            <div className="space-y-1">
              <div>Avg Page Load: {(averageMetrics.avgPageLoadTime / 1000).toFixed(1)}s</div>
              <div>Avg API Response: {(averageMetrics.avgApiResponseTime / 1000).toFixed(1)}s</div>
              <div>Avg Memory: {averageMetrics.avgMemoryUsage.toFixed(1)}MB</div>
              <div>Total Requests: {averageMetrics.totalNetworkRequests}</div>
              <div>Total Errors: {averageMetrics.totalErrors}</div>
            </div>
          )}
          <div className="mt-2 space-x-2">
            <button
              onClick={exportMetrics}
              className="bg-blue-600 px-2 py-1 rounded text-xs"
            >
              Export
            </button>
            <button
              onClick={stopMonitoring}
              className="bg-red-600 px-2 py-1 rounded text-xs"
            >
              Stop
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Hook to use performance monitoring
export function usePerformanceMonitoring() {
  const [isMonitoring, setIsMonitoring] = useState(false);
  
  const startMonitoring = () => {
    setIsMonitoring(true);
  };
  
  const stopMonitoring = () => {
    setIsMonitoring(false);
  };
  
  return {
    isMonitoring,
    startMonitoring,
    stopMonitoring
  };
}

