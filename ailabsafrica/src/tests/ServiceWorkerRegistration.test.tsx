import { render, screen, fireEvent, waitFor, renderHook } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import ServiceWorkerRegistration, { useOnlineStatus } from '@/components/ServiceWorkerRegistration';
import { useToast } from '@/components/ui/use-toast';

// Mock dependencies
vi.mock('@/components/ui/use-toast');
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    functions: {
      invoke: vi.fn()
    }
  }
}));

// Mock service worker
const mockServiceWorker = {
  register: vi.fn(),
  getRegistration: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  controller: null
};

// Mock navigator
Object.defineProperty(window, 'navigator', {
  value: {
    serviceWorker: mockServiceWorker,
    onLine: true
  },
  writable: true
});

describe('ServiceWorkerRegistration', () => {
  const mockToast = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue({ toast: mockToast });
    
    // Reset service worker mocks
    mockServiceWorker.register.mockResolvedValue({
      addEventListener: vi.fn(),
      waiting: null,
      installing: null
    });
    mockServiceWorker.getRegistration.mockResolvedValue({
      waiting: null
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders children without crashing', () => {
    render(
      <ServiceWorkerRegistration>
        <div data-testid="child">Test Child</div>
      </ServiceWorkerRegistration>
    );

    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('registers service worker on mount', async () => {
    render(
      <ServiceWorkerRegistration>
        <div>Test</div>
      </ServiceWorkerRegistration>
    );

    await waitFor(() => {
      expect(mockServiceWorker.register).toHaveBeenCalledWith('/sw.js', {
        scope: '/'
      });
    });
  });

  it('handles service worker registration success', async () => {
    const mockRegistration = {
      addEventListener: vi.fn(),
      waiting: null,
      installing: null
    };

    mockServiceWorker.register.mockResolvedValue(mockRegistration);

    render(
      <ServiceWorkerRegistration>
        <div>Test</div>
      </ServiceWorkerRegistration>
    );

    await waitFor(() => {
      expect(mockRegistration.addEventListener).toHaveBeenCalledWith('updatefound', expect.any(Function));
      expect(mockRegistration.addEventListener).toHaveBeenCalledWith('success', expect.any(Function));
      expect(mockRegistration.addEventListener).toHaveBeenCalledWith('error', expect.any(Function));
    });
  });

  it('shows toast on service worker registration success', async () => {
    const mockRegistration = {
      addEventListener: vi.fn((event, callback) => {
        if (event === 'success') {
          callback();
        }
      }),
      waiting: null,
      installing: null
    };

    mockServiceWorker.register.mockResolvedValue(mockRegistration);

    render(
      <ServiceWorkerRegistration>
        <div>Test</div>
      </ServiceWorkerRegistration>
    );

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: "App Ready",
        description: "The app is now available offline",
        icon: expect.any(Object)
      });
    });
  });

  it('handles service worker registration error', async () => {
    const mockRegistration = {
      addEventListener: vi.fn((event, callback) => {
        if (event === 'error') {
          callback(new Error('Registration failed'));
        }
      }),
      waiting: null,
      installing: null
    };

    mockServiceWorker.register.mockResolvedValue(mockRegistration);

    render(
      <ServiceWorkerRegistration>
        <div>Test</div>
      </ServiceWorkerRegistration>
    );

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: "Service Worker Error",
        description: "Failed to register service worker",
        variant: "destructive",
        icon: expect.any(Object)
      });
    });
  });

  it('handles service worker update found', async () => {
    const mockNewWorker = {
      addEventListener: vi.fn((event, callback) => {
        if (event === 'statechange') {
          callback();
        }
      }),
      state: 'installed'
    };

    const mockRegistration = {
      addEventListener: vi.fn((event, callback) => {
        if (event === 'updatefound') {
          callback();
        }
      }),
      waiting: null,
      installing: mockNewWorker
    };

    mockServiceWorker.register.mockResolvedValue(mockRegistration);
    mockServiceWorker.controller = {}; // Simulate existing controller

    render(
      <ServiceWorkerRegistration>
        <div>Test</div>
      </ServiceWorkerRegistration>
    );

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: "Update Available",
        description: "A new version of the app is available. Click to update.",
        action: expect.any(Object)
      });
    });
  });

  it('handles update service worker function', async () => {
    const mockWaitingWorker = {
      postMessage: vi.fn()
    };

    const mockRegistration = {
      waiting: mockWaitingWorker
    };

    mockServiceWorker.getRegistration.mockResolvedValue(mockRegistration);

    render(
      <ServiceWorkerRegistration>
        <div>Test</div>
      </ServiceWorkerRegistration>
    );

    // Simulate update button click
    const updateButton = screen.queryByText('Update Now');
    if (updateButton) {
      fireEvent.click(updateButton);
    }

    await waitFor(() => {
      expect(mockWaitingWorker.postMessage).toHaveBeenCalledWith({ type: 'SKIP_WAITING' });
    });
  });

  it('handles update service worker error', async () => {
    mockServiceWorker.getRegistration.mockRejectedValue(new Error('Update failed'));

    render(
      <ServiceWorkerRegistration>
        <div>Test</div>
      </ServiceWorkerRegistration>
    );

    // Simulate update button click
    const updateButton = screen.queryByText('Update Now');
    if (updateButton) {
      fireEvent.click(updateButton);
    }

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: "Update Failed",
        description: "Failed to update the app. Please refresh manually.",
        variant: "destructive"
      });
    });
  });

  it('does not register service worker when disabled', () => {
    render(
      <ServiceWorkerRegistration enabled={false}>
        <div>Test</div>
      </ServiceWorkerRegistration>
    );

    expect(mockServiceWorker.register).not.toHaveBeenCalled();
  });

  it('handles service worker not supported', () => {
    // Mock service worker not available
    Object.defineProperty(window, 'navigator', {
      value: {
        onLine: true
      },
      writable: true
    });

    render(
      <ServiceWorkerRegistration>
        <div>Test</div>
      </ServiceWorkerRegistration>
    );

    expect(mockServiceWorker.register).not.toHaveBeenCalled();
  });
});

describe('useOnlineStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns initial online status', () => {
    const { result } = renderHook(() => useOnlineStatus());
    expect(result.current).toBe(true);
  });

  it('updates status when going offline', () => {
    const { result } = renderHook(() => useOnlineStatus());
    
    // Simulate going offline
    Object.defineProperty(window.navigator, 'onLine', {
      value: false,
      writable: true
    });
    
    fireEvent(window, new Event('offline'));
    
    expect(result.current).toBe(false);
  });

  it('updates status when going online', () => {
    // Start offline
    Object.defineProperty(window.navigator, 'onLine', {
      value: false,
      writable: true
    });

    const { result } = renderHook(() => useOnlineStatus());
    
    // Simulate going online
    Object.defineProperty(window.navigator, 'onLine', {
      value: true,
      writable: true
    });
    
    fireEvent(window, new Event('online'));
    
    expect(result.current).toBe(true);
  });

  it('cleans up event listeners on unmount', () => {
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');
    
    const { unmount } = renderHook(() => useOnlineStatus());
    
    unmount();
    
    expect(removeEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function));
    expect(removeEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function));
  });
});

