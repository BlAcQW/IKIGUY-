import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import PerformanceMonitor, { usePerformanceMonitoring } from '@/components/PerformanceMonitor';
import { supabase } from '@/integrations/supabase/client';

// Mock Supabase client
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    functions: {
      invoke: vi.fn(),
    },
  },
}));

// Mock toast
const mockToast = vi.fn();
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: mockToast }),
}));

// Mock environment variables
vi.mock('@/lib/env', () => ({
  env: {
    VITE_DEBUG_MODE: 'true',
  },
}));

const TestComponent = () => <div>Test Content</div>;

const renderPerformanceMonitor = (props: any = {}) => {
  return render(
    <PerformanceMonitor {...props}>
      <TestComponent />
    </PerformanceMonitor>
  );
};

describe('PerformanceMonitor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset performance.now to return consistent values
    vi.spyOn(performance, 'now').mockReturnValue(1000);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders children when enabled', () => {
      renderPerformanceMonitor({ enabled: true });
      
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('renders children when disabled', () => {
      renderPerformanceMonitor({ enabled: false });
      
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('starts monitoring when enabled', () => {
      renderPerformanceMonitor({ enabled: true });
      
      // Check that PerformanceObserver was called
      expect(window.PerformanceObserver).toHaveBeenCalled();
    });

    it('does not start monitoring when disabled', () => {
      renderPerformanceMonitor({ enabled: false });
      
      expect(window.PerformanceObserver).not.toHaveBeenCalled();
    });
  });

  describe('Performance Monitoring', () => {
    it('monitors page load performance', async () => {
      renderPerformanceMonitor({ enabled: true });
      
      // Simulate navigation timing entry
      const mockNavigationEntry = {
        entryType: 'navigation',
        loadEventEnd: 2000,
        loadEventStart: 500,
      };
      
      // Get the PerformanceObserver callback and simulate an entry
      const mockObserverCallback = (window.PerformanceObserver as any).mock.calls[0][0];
      mockObserverCallback({ getEntries: () => [mockNavigationEntry] });
      
      await waitFor(() => {
        expect(supabase.functions.invoke).toHaveBeenCalledWith('track-performance', {
          body: {
            action: 'track',
            data: expect.objectContaining({
              pageLoadTime: 1500,
              timestamp: expect.any(Number),
            }),
          },
        });
      });
    });

    it('monitors API request performance', async () => {
      renderPerformanceMonitor({ enabled: true });
      
      // Mock fetch to return a successful response
      global.fetch = vi.fn().mockResolvedValueOnce({ ok: true });
      
      await fetch('/api/test');
      
      await waitFor(() => {
        expect(supabase.functions.invoke).toHaveBeenCalledWith('track-performance', {
          body: {
            action: 'track',
            data: expect.objectContaining({
              apiResponseTime: expect.any(Number),
              networkRequests: 1,
              timestamp: expect.any(Number),
            }),
          },
        });
      });
    });

    it('monitors API request errors', async () => {
      renderPerformanceMonitor({ enabled: true });
      
      // Mock fetch to throw an error
      global.fetch = vi.fn().mockRejectedValueOnce(new Error('Network error'));
      
      try {
        await fetch('/api/test');
      } catch (error) {
        // Expected error
      }
      
      await waitFor(() => {
        expect(supabase.functions.invoke).toHaveBeenCalledWith('track-performance', {
          body: {
            action: 'track',
            data: expect.objectContaining({
              errors: 1,
              timestamp: expect.any(Number),
            }),
          },
        });
      });
    });

    it('monitors memory usage', async () => {
      renderPerformanceMonitor({ enabled: true });
      
      // Simulate memory monitoring interval
      await waitFor(() => {
        expect(supabase.functions.invoke).toHaveBeenCalledWith('track-performance', {
          body: {
            action: 'track',
            data: expect.objectContaining({
              memoryUsage: expect.any(Number),
              timestamp: expect.any(Number),
            }),
          },
        });
      });
    });
  });

  describe('Performance Alerts', () => {
    it('shows slow page load alert', async () => {
      renderPerformanceMonitor({ enabled: true });
      
      // Simulate slow page load
      const mockNavigationEntry = {
        entryType: 'navigation',
        loadEventEnd: 5000, // 5 seconds
        loadEventStart: 500,
      };
      
      const mockObserverCallback = (window.PerformanceObserver as any).mock.calls[0][0];
      mockObserverCallback({ getEntries: () => [mockNavigationEntry] });
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Slow Page Load",
          description: expect.stringContaining("Page took"),
          variant: "destructive"
        });
      });
    });

    it('shows slow API response alert', async () => {
      renderPerformanceMonitor({ enabled: true });
      
      // Mock slow API response
      global.fetch = vi.fn().mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ ok: true }), 3000))
      );
      
      await fetch('/api/test');
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Slow API Response",
          description: expect.stringContaining("API request took"),
          variant: "destructive"
        });
      });
    });

    it('shows high memory usage alert', async () => {
      renderPerformanceMonitor({ enabled: true });
      
      // Mock high memory usage
      Object.defineProperty(performance, 'memory', {
        value: { usedJSHeapSize: 200 * 1024 * 1024 }, // 200MB
        writable: true,
      });
      
      // Trigger memory monitoring
      const mockNavigationEntry = {
        entryType: 'navigation',
        loadEventEnd: 2000,
        loadEventStart: 500,
      };
      
      const mockObserverCallback = (window.PerformanceObserver as any).mock.calls[0][0];
      mockObserverCallback({ getEntries: () => [mockNavigationEntry] });
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "High Memory Usage",
          description: expect.stringContaining("Memory usage:"),
          variant: "destructive"
        });
      });
    });
  });

  describe('Debug Panel', () => {
    it('shows debug panel in development mode', () => {
      renderPerformanceMonitor({ enabled: true });
      
      expect(screen.getByText('Performance Monitor')).toBeInTheDocument();
    });

    it('does not show debug panel in production mode', () => {
      // Mock production environment
      vi.doMock('@/lib/env', () => ({
        env: {
          VITE_DEBUG_MODE: 'false',
        },
      }));
      
      renderPerformanceMonitor({ enabled: true });
      
      expect(screen.queryByText('Performance Monitor')).not.toBeInTheDocument();
    });

    it('shows average metrics in debug panel', () => {
      renderPerformanceMonitor({ enabled: true });
      
      expect(screen.getByText('Performance Monitor')).toBeInTheDocument();
      expect(screen.getByText('Avg Page Load:')).toBeInTheDocument();
      expect(screen.getByText('Avg API Response:')).toBeInTheDocument();
      expect(screen.getByText('Avg Memory:')).toBeInTheDocument();
    });

    it('exports metrics when export button is clicked', async () => {
      renderPerformanceMonitor({ enabled: true });
      
      const exportButton = screen.getByText('Export');
      fireEvent.click(exportButton);
      
      // Check that URL.createObjectURL was called
      expect(URL.createObjectURL).toHaveBeenCalled();
      expect(document.createElement).toHaveBeenCalledWith('a');
    });

    it('stops monitoring when stop button is clicked', () => {
      renderPerformanceMonitor({ enabled: true });
      
      const stopButton = screen.getByText('Stop');
      fireEvent.click(stopButton);
      
      // Check that the debug panel is no longer visible
      expect(screen.queryByText('Performance Monitor')).not.toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('handles Supabase tracking errors gracefully', async () => {
      // Mock Supabase error
      (supabase.functions.invoke as any).mockRejectedValueOnce(new Error('Supabase error'));
      
      renderPerformanceMonitor({ enabled: true });
      
      // Simulate performance entry
      const mockNavigationEntry = {
        entryType: 'navigation',
        loadEventEnd: 2000,
        loadEventStart: 500,
      };
      
      const mockObserverCallback = (window.PerformanceObserver as any).mock.calls[0][0];
      mockObserverCallback({ getEntries: () => [mockNavigationEntry] });
      
      // Should not throw error
      await waitFor(() => {
        expect(supabase.functions.invoke).toHaveBeenCalled();
      });
    });

    it('handles missing performance API gracefully', () => {
      // Mock missing performance API
      Object.defineProperty(window, 'performance', {
        value: undefined,
        writable: true,
      });
      
      expect(() => {
        renderPerformanceMonitor({ enabled: true });
      }).not.toThrow();
    });

    it('handles missing memory API gracefully', () => {
      // Mock missing memory API
      Object.defineProperty(performance, 'memory', {
        value: undefined,
        writable: true,
      });
      
      expect(() => {
        renderPerformanceMonitor({ enabled: true });
      }).not.toThrow();
    });
  });

  describe('Memory Management', () => {
    it('limits metrics array to 100 entries', async () => {
      renderPerformanceMonitor({ enabled: true });
      
      // Simulate many performance entries
      for (let i = 0; i < 150; i++) {
        const mockNavigationEntry = {
          entryType: 'navigation',
          loadEventEnd: 2000 + i,
          loadEventStart: 500,
        };
        
        const mockObserverCallback = (window.PerformanceObserver as any).mock.calls[0][0];
        mockObserverCallback({ getEntries: () => [mockNavigationEntry] });
      }
      
      await waitFor(() => {
        // Should not exceed 100 entries
        expect(supabase.functions.invoke).toHaveBeenCalledTimes(100);
      });
    });
  });

  describe('Cleanup', () => {
    it('cleans up monitoring on unmount', () => {
      const { unmount } = renderPerformanceMonitor({ enabled: true });
      
      unmount();
      
      // Check that PerformanceObserver disconnect was called
      expect(window.PerformanceObserver).toHaveBeenCalled();
    });

    it('restores original fetch on unmount', () => {
      const originalFetch = window.fetch;
      const { unmount } = renderPerformanceMonitor({ enabled: true });
      
      unmount();
      
      // Fetch should be restored
      expect(window.fetch).toBe(originalFetch);
    });
  });
});

describe('usePerformanceMonitoring', () => {
  it('provides monitoring state and controls', () => {
    const TestHookComponent = () => {
      const { isMonitoring, startMonitoring, stopMonitoring } = usePerformanceMonitoring();
      
      return (
        <div>
          <span data-testid="monitoring-status">{isMonitoring ? 'monitoring' : 'stopped'}</span>
          <button onClick={startMonitoring}>Start</button>
          <button onClick={stopMonitoring}>Stop</button>
        </div>
      );
    };
    
    render(<TestHookComponent />);
    
    expect(screen.getByTestId('monitoring-status')).toHaveTextContent('stopped');
    
    fireEvent.click(screen.getByText('Start'));
    expect(screen.getByTestId('monitoring-status')).toHaveTextContent('monitoring');
    
    fireEvent.click(screen.getByText('Stop'));
    expect(screen.getByTestId('monitoring-status')).toHaveTextContent('stopped');
  });
});
