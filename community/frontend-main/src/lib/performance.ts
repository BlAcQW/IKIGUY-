// Performance monitoring and optimization utilities

export interface PerformanceMetrics {
  pageLoadTime: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  cumulativeLayoutShift: number;
  firstInputDelay: number;
  timeToInteractive: number;
}

export interface MemoryInfo {
  usedJSHeapSize: number;
  totalJSHeapSize: number;
  jsHeapSizeLimit: number;
}

class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: PerformanceMetrics = {
    pageLoadTime: 0,
    firstContentfulPaint: 0,
    largestContentfulPaint: 0,
    cumulativeLayoutShift: 0,
    firstInputDelay: 0,
    timeToInteractive: 0,
  };

  public static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  public init(): void {
    this.measurePageLoad();
    this.measureWebVitals();
    this.monitorMemoryUsage();
    this.observeResourceLoading();
  }

  private measurePageLoad(): void {
    if (typeof window !== 'undefined' && 'performance' in window) {
      window.addEventListener('load', () => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        if (navigation) {
          this.metrics.pageLoadTime = navigation.loadEventEnd - navigation.fetchStart;
        }
      });
    }
  }

  private measureWebVitals(): void {
    if (typeof window !== 'undefined') {
      // First Contentful Paint
      this.observePerformanceEntries('paint', (entries) => {
        const fcp = entries.find(entry => entry.name === 'first-contentful-paint');
        if (fcp) {
          this.metrics.firstContentfulPaint = fcp.startTime;
        }
      });

      // Largest Contentful Paint
      this.observePerformanceEntries('largest-contentful-paint', (entries) => {
        const lcp = entries[entries.length - 1];
        if (lcp) {
          this.metrics.largestContentfulPaint = lcp.startTime;
        }
      });

      // Cumulative Layout Shift
      this.observePerformanceEntries('layout-shift', (entries) => {
        let cls = 0;
        entries.forEach(entry => {
          if (!(entry as any).hadRecentInput) {
            cls += (entry as any).value;
          }
        });
        this.metrics.cumulativeLayoutShift = cls;
      });

      // First Input Delay
      this.observePerformanceEntries('first-input', (entries) => {
        const fid = entries[0];
        if (fid) {
          this.metrics.firstInputDelay = fid.processingStart - fid.startTime;
        }
      });
    }
  }

  private observePerformanceEntries(
    entryType: string,
    callback: (entries: PerformanceEntry[]) => void
  ): void {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          callback(list.getEntries());
        });
        observer.observe({ entryTypes: [entryType] });
      } catch (error) {
        console.warn(`Failed to observe ${entryType}:`, error);
      }
    }
  }

  private monitorMemoryUsage(): void {
    if ('memory' in performance) {
      setInterval(() => {
        const memory = (performance as any).memory;
        if (memory) {
          this.logMemoryUsage({
            usedJSHeapSize: memory.usedJSHeapSize,
            totalJSHeapSize: memory.totalJSHeapSize,
            jsHeapSizeLimit: memory.jsHeapSizeLimit,
          });
        }
      }, 30000); // Check every 30 seconds
    }
  }

  private observeResourceLoading(): void {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          list.getEntries().forEach((entry) => {
            const resource = entry as PerformanceResourceTiming;
            // Log slow resources (> 1 second)
            if (resource.duration > 1000) {
              console.warn(`Slow resource: ${resource.name} took ${Math.round(resource.duration)}ms`);
            }
          });
        });
        observer.observe({ entryTypes: ['resource'] });
      } catch (error) {
        console.warn('Failed to observe resource loading:', error);
      }
    }
  }

  public getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  public logMetrics(): void {
    if (process.env.NODE_ENV === 'development') {
      console.group('Performance Metrics');
      console.log('Page Load Time:', Math.round(this.metrics.pageLoadTime), 'ms');
      console.log('First Contentful Paint:', Math.round(this.metrics.firstContentfulPaint), 'ms');
      console.log('Largest Contentful Paint:', Math.round(this.metrics.largestContentfulPaint), 'ms');
      console.log('Cumulative Layout Shift:', this.metrics.cumulativeLayoutShift.toFixed(3));
      console.log('First Input Delay:', Math.round(this.metrics.firstInputDelay), 'ms');
      console.groupEnd();
    }
  }

  private logMemoryUsage(memory: MemoryInfo): void {
    const usedMB = Math.round(memory.usedJSHeapSize / 1024 / 1024);
    const totalMB = Math.round(memory.totalJSHeapSize / 1024 / 1024);
    const limitMB = Math.round(memory.jsHeapSizeLimit / 1024 / 1024);

    // Log warning if memory usage is high
    if (usedMB > limitMB * 0.8) {
      console.warn(`High memory usage: ${usedMB}MB / ${limitMB}MB (${Math.round(usedMB / limitMB * 100)}%)`);
    }

    if (process.env.NODE_ENV === 'development') {
      console.log(`Memory: ${usedMB}MB used, ${totalMB}MB total, ${limitMB}MB limit`);
    }
  }
}

// Utility functions for performance optimization

export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

// Lazy loading utility for images
export const lazyLoadImage = (src: string): Promise<HTMLImageElement> => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
};

// Virtual scrolling hook for large lists
export const useVirtualScrolling = (
  itemHeight: number,
  containerHeight: number,
  itemCount: number,
  scrollTop: number
) => {
  const startIndex = Math.floor(scrollTop / itemHeight);
  const endIndex = Math.min(
    startIndex + Math.ceil(containerHeight / itemHeight) + 1,
    itemCount - 1
  );

  return {
    startIndex,
    endIndex,
    visibleItems: endIndex - startIndex + 1,
    offsetY: startIndex * itemHeight,
  };
};

// Bundle analyzer helper (for development)
export const analyzeBundleSize = (): void => {
  if (process.env.NODE_ENV === 'development') {
    console.group('Bundle Analysis');
    console.log('To analyze bundle size, run: npm run build && npx vite-bundle-analyzer');
    console.log('Consider using webpack-bundle-analyzer for detailed analysis');
    console.groupEnd();
  }
};

// Memory leak detector
export const detectMemoryLeaks = (): void => {
  if (process.env.NODE_ENV === 'development' && 'performance' in window && (performance as any).memory) {
    let previousMemory = (performance as any).memory.usedJSHeapSize;

    setInterval(() => {
      const currentMemory = (performance as any).memory.usedJSHeapSize;
      const memoryIncrease = currentMemory - previousMemory;

      if (memoryIncrease > 10 * 1024 * 1024) { // 10MB increase
        console.warn(`Potential memory leak detected: ${Math.round(memoryIncrease / 1024 / 1024)}MB increase`);
      }

      previousMemory = currentMemory;
    }, 60000); // Check every minute
  }
};

// Create and export singleton instance
export const performanceMonitor = PerformanceMonitor.getInstance();

// Auto-initialize performance monitoring
if (typeof window !== 'undefined') {
  performanceMonitor.init();

  // Log metrics after page load
  window.addEventListener('load', () => {
    setTimeout(() => {
      performanceMonitor.logMetrics();
    }, 2000);
  });

  // Start memory leak detection in development
  if (process.env.NODE_ENV === 'development') {
    detectMemoryLeaks();
  }
}