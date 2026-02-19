import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { CDNProvider, useCDN, CDNStatus, CDNPerformanceMonitor, CDNCacheManager } from '@/components/CDNProvider';
import { 
  generateCDNUrl, 
  generateResponsiveCDNUrls, 
  generateCDNSrcSet,
  preloadCDNAsset,
  loadCDNAsset,
  batchLoadCDNAssets,
  optimizeImageForCDN,
  clearCDNCache,
  getCDNCacheStats,
  monitorCDNPerformance,
  initializeCDN,
  getCDNConfig,
  updateCDNConfig,
  isCDNAvailable,
  getCDNHealth
} from '@/utils/cdnIntegration';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock performance API
const mockPerformance = {
  now: vi.fn(() => 1000),
};
global.performance = mockPerformance;

// Mock document methods
const mockCreateElement = vi.fn();
const mockAppendChild = vi.fn();
Object.defineProperty(document, 'createElement', { value: mockCreateElement });
Object.defineProperty(document.head, 'appendChild', { value: mockAppendChild });

// Mock window
const mockWindow = {
  __CDN_CONFIG__: {},
};
Object.defineProperty(window, '__CDN_CONFIG__', {
  value: mockWindow.__CDN_CONFIG__,
  writable: true,
});

describe('CDN Integration Utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('generateCDNUrl', () => {
    it('generates CDN URL with base configuration', () => {
      const result = generateCDNUrl('/images/logo.png', {
        baseUrl: 'https://cdn.example.com',
        version: '1.0.0',
      });

      expect(result).toContain('https://cdn.example.com/images/logo.png');
      expect(result).toContain('v=1.0.0');
    });

    it('returns original path when no CDN configured', () => {
      const result = generateCDNUrl('/images/logo.png', { baseUrl: '' });
      expect(result).toBe('/images/logo.png');
    });

    it('adds compression parameter when enabled', () => {
      const result = generateCDNUrl('/images/logo.png', {
        baseUrl: 'https://cdn.example.com',
        enableCompression: true,
      });

      expect(result).toContain('compress=true');
    });
  });

  describe('generateResponsiveCDNUrls', () => {
    it('generates responsive URLs for different sizes', () => {
      const result = generateResponsiveCDNUrls('/images/hero.jpg', [320, 768, 1024], {
        baseUrl: 'https://cdn.example.com',
      });

      expect(result).toHaveLength(3);
      expect(result[0]).toContain('w=320');
      expect(result[1]).toContain('w=768');
      expect(result[2]).toContain('w=1024');
    });

    it('returns original path when no CDN configured', () => {
      const result = generateResponsiveCDNUrls('/images/hero.jpg', [320, 768], { baseUrl: '' });
      expect(result).toEqual(['/images/hero.jpg']);
    });
  });

  describe('generateCDNSrcSet', () => {
    it('generates srcSet with breakpoints', () => {
      const breakpoints = [
        { width: 320, quality: 70 },
        { width: 768, quality: 80 },
      ];

      const result = generateCDNSrcSet('/images/hero.jpg', breakpoints, {
        baseUrl: 'https://cdn.example.com',
      });

      expect(result).toContain('320w');
      expect(result).toContain('768w');
      expect(result).toContain('q=70');
      expect(result).toContain('q=80');
    });

    it('returns original path when no CDN configured', () => {
      const result = generateCDNSrcSet('/images/hero.jpg', [{ width: 320 }], { baseUrl: '' });
      expect(result).toBe('/images/hero.jpg');
    });
  });

  describe('preloadCDNAsset', () => {
    it('creates preload link element', async () => {
      const mockLink = {
        rel: '',
        as: '',
        href: '',
        fetchPriority: '',
        onload: null,
        onerror: null,
      };

      mockCreateElement.mockReturnValue(mockLink);

      const promise = preloadCDNAsset('/images/logo.png', 'image', {
        baseUrl: 'https://cdn.example.com',
      });

      // Simulate successful load
      setTimeout(() => {
        mockLink.onload();
      }, 0);

      await promise;

      expect(mockCreateElement).toHaveBeenCalledWith('link');
      expect(mockLink.rel).toBe('preload');
      expect(mockLink.as).toBe('image');
      expect(mockAppendChild).toHaveBeenCalledWith(mockLink);
    });

    it('handles preload errors', async () => {
      const mockLink = {
        rel: '',
        as: '',
        href: '',
        fetchPriority: '',
        onload: null,
        onerror: null,
      };

      mockCreateElement.mockReturnValue(mockLink);

      const promise = preloadCDNAsset('/images/logo.png', 'image', {
        baseUrl: 'https://cdn.example.com',
      });

      // Simulate error
      setTimeout(() => {
        mockLink.onerror();
      }, 0);

      await expect(promise).rejects.toThrow('Failed to preload');
    });
  });

  describe('loadCDNAsset', () => {
    it('loads asset from CDN successfully', async () => {
      mockFetch.mockResolvedValueOnce({ 
        ok: true, 
        headers: new Map([['content-length', '1024']]) 
      });

      const result = await loadCDNAsset('/test.jpg', { baseUrl: 'https://cdn.example.com' });

      expect(result.url).toContain('https://cdn.example.com');
      expect(result.cached).toBe(false);
      expect(result.fallback).toBe(false);
      expect(result.performance.loadTime).toBeGreaterThan(0);
    });

    it('falls back to original URL when CDN fails', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await loadCDNAsset('/test.jpg', { 
        baseUrl: 'https://cdn.example.com',
        fallbackUrl: 'https://fallback.example.com'
      });

      expect(result.url).toContain('https://fallback.example.com');
      expect(result.fallback).toBe(true);
    });

    it('uses cache when available', async () => {
      // Mock the CDN cache by first loading an asset to populate it
      mockFetch.mockResolvedValueOnce({ 
        ok: true, 
        headers: new Map([['content-length', '1024']]) 
      });

      // First load to populate cache
      await loadCDNAsset('/test.jpg', { 
        baseUrl: 'https://cdn.example.com',
        enableCache: true 
      });

      // Second load should use cache (no fetch call)
      const result = await loadCDNAsset('/test.jpg', { 
        baseUrl: 'https://cdn.example.com',
        enableCache: true 
      });

      expect(result.url).toBe('https://cdn.example.com/test.jpg');
      expect(result.cached).toBe(true);
      // Should only have called fetch once (for the first load)
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('batchLoadCDNAssets', () => {
    it('loads multiple assets in parallel', async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true, headers: new Map([['content-length', '1024']]) })
        .mockResolvedValueOnce({ ok: true, headers: new Map([['content-length', '2048']]) });

      const results = await batchLoadCDNAssets(['/test1.jpg', '/test2.jpg'], { 
        baseUrl: 'https://cdn.example.com' 
      });

      expect(results).toHaveLength(2);
      expect(results[0].url).toContain('https://cdn.example.com');
      expect(results[1].url).toContain('https://cdn.example.com');
    });

    it('handles mixed success and failure', async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true, headers: new Map([['content-length', '1024']]) })
        .mockRejectedValueOnce(new Error('Network error'));

      const results = await batchLoadCDNAssets(['/test1.jpg', '/test2.jpg'], { 
        baseUrl: 'https://cdn.example.com' 
      });

      expect(results).toHaveLength(2);
      expect(results[0].url).toContain('https://cdn.example.com');
      expect(results[1].fallback).toBe(true);
    });
  });

  describe('optimizeImageForCDN', () => {
    it('optimizes image with parameters', () => {
      const result = optimizeImageForCDN('/images/hero.jpg', {
        width: 800,
        height: 600,
        quality: 85,
        format: 'webp',
        fit: 'cover',
      }, {
        baseUrl: 'https://cdn.example.com',
      });

      expect(result).toContain('w=800');
      expect(result).toContain('h=600');
      expect(result).toContain('q=85');
      expect(result).toContain('f=webp');
      expect(result).toContain('fit=cover');
    });

    it('adds format optimization when enabled', () => {
      const result = optimizeImageForCDN('/images/hero.jpg', {
        format: 'auto',
      }, {
        baseUrl: 'https://cdn.example.com',
        enableAvif: true,
      });

      expect(result).toContain('f=avif');
    });
  });

  describe('clearCDNCache', () => {
    it('clears the CDN cache', () => {
      // First, add something to cache
      loadCDNAsset('/test.jpg', { baseUrl: 'https://cdn.example.com', enableCache: true });
      
      const statsBefore = getCDNCacheStats();
      expect(statsBefore.size).toBeGreaterThan(0);

      clearCDNCache();

      const statsAfter = getCDNCacheStats();
      expect(statsAfter.size).toBe(0);
    });
  });

  describe('getCDNCacheStats', () => {
    it('returns cache statistics', () => {
      const stats = getCDNCacheStats();
      
      expect(stats).toHaveProperty('size');
      expect(stats).toHaveProperty('entries');
      expect(Array.isArray(stats.entries)).toBe(true);
    });
  });

  describe('monitorCDNPerformance', () => {
    it('monitors CDN performance', async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true }) // CDN health check
        .mockResolvedValueOnce({ ok: true }); // Fallback health check

      const result = await monitorCDNPerformance('/images/logo.png', {
        baseUrl: 'https://cdn.example.com',
        fallbackUrl: 'https://fallback.example.com',
      });

      expect(result).toHaveProperty('cdnTime');
      expect(result).toHaveProperty('fallbackTime');
      expect(result).toHaveProperty('success');
    });
  });

  describe('initializeCDN', () => {
    it('initializes CDN with configuration', () => {
      const config = {
        baseUrl: 'https://cdn.example.com',
        version: '1.0.0',
      };

      initializeCDN(config);

      expect(window.__CDN_CONFIG__).toEqual(expect.objectContaining(config));
    });
  });

  describe('getCDNConfig', () => {
    it('returns current CDN configuration', () => {
      const config = getCDNConfig();
      
      expect(config).toHaveProperty('baseUrl');
      expect(config).toHaveProperty('version');
      expect(config).toHaveProperty('enableCache');
    });
  });

  describe('updateCDNConfig', () => {
    it('updates CDN configuration', () => {
      const newConfig = {
        baseUrl: 'https://new-cdn.example.com',
        enableCache: false,
      };

      updateCDNConfig(newConfig);

      const updatedConfig = getCDNConfig();
      expect(updatedConfig.baseUrl).toBe('https://new-cdn.example.com');
      expect(updatedConfig.enableCache).toBe(false);
    });
  });

  describe('isCDNAvailable', () => {
    it('checks CDN availability', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true });

      const result = await isCDNAvailable({ baseUrl: 'https://cdn.example.com' });
      expect(result).toBe(true);
    });

    it('returns false when CDN is not available', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await isCDNAvailable({ baseUrl: 'https://cdn.example.com' });
      expect(result).toBe(false);
    });

    it('returns false when no base URL configured', async () => {
      const result = await isCDNAvailable({ baseUrl: '' });
      expect(result).toBe(false);
    });
  });

  describe('getCDNHealth', () => {
    it('returns CDN health status', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true });

      const result = await getCDNHealth({ baseUrl: 'https://cdn.example.com' });

      expect(result).toHaveProperty('available');
      expect(result).toHaveProperty('responseTime');
      expect(result).toHaveProperty('status');
      expect(result.available).toBe(true);
    });

    it('returns unavailable status when CDN fails', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await getCDNHealth({ baseUrl: 'https://cdn.example.com' });

      expect(result.available).toBe(false);
      expect(result.status).toBe('unavailable');
    });
  });
});

describe('CDNProvider Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('provides CDN context to children', () => {
    const TestComponent = () => {
      const cdn = useCDN();
      return <div data-testid="cdn-config">{cdn.config.baseUrl}</div>;
    };

    render(
      <CDNProvider config={{ baseUrl: 'https://cdn.example.com' }}>
        <TestComponent />
      </CDNProvider>
    );

    expect(screen.getByTestId('cdn-config')).toHaveTextContent('https://cdn.example.com');
  });

  it('throws error when used outside provider', () => {
    const TestComponent = () => {
      useCDN();
      return <div>Test</div>;
    };

    expect(() => render(<TestComponent />)).toThrow('useCDN must be used within a CDNProvider');
  });
});

describe('CDNStatus Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders basic status', () => {
    render(
      <CDNProvider>
        <CDNStatus />
      </CDNProvider>
    );

    expect(screen.getByText(/CDN/)).toBeInTheDocument();
  });

  it('renders detailed status when showDetails is true', () => {
    render(
      <CDNProvider>
        <CDNStatus showDetails={true} />
      </CDNProvider>
    );

    expect(screen.getByText('CDN Status')).toBeInTheDocument();
    expect(screen.getByText('Available:')).toBeInTheDocument();
    expect(screen.getByText('Response Time:')).toBeInTheDocument();
  });
});

describe('CDNPerformanceMonitor Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders performance monitor', () => {
    render(
      <CDNProvider>
        <CDNPerformanceMonitor paths={['/test1.jpg', '/test2.jpg']} />
      </CDNProvider>
    );

    expect(screen.getByText('CDN Performance')).toBeInTheDocument();
  });

  it('calls onPerformanceUpdate callback', async () => {
    const mockCallback = vi.fn();

    render(
      <CDNProvider>
        <CDNPerformanceMonitor 
          paths={['/test.jpg']} 
          onPerformanceUpdate={mockCallback}
        />
      </CDNProvider>
    );

    await waitFor(() => {
      expect(mockCallback).toHaveBeenCalled();
    });
  });
});

describe('CDNCacheManager Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders cache manager', () => {
    render(
      <CDNProvider>
        <CDNCacheManager />
      </CDNProvider>
    );

    expect(screen.getByText('CDN Cache')).toBeInTheDocument();
    expect(screen.getByText('Refresh')).toBeInTheDocument();
    expect(screen.getByText('Clear Cache')).toBeInTheDocument();
  });

  it('clears cache when clear button is clicked', () => {
    render(
      <CDNProvider>
        <CDNCacheManager />
      </CDNProvider>
    );

    const clearButton = screen.getByText('Clear Cache');
    fireEvent.click(clearButton);

    // Cache should be cleared
    const stats = getCDNCacheStats();
    expect(stats.size).toBe(0);
  });

  it('refreshes stats when refresh button is clicked', () => {
    render(
      <CDNProvider>
        <CDNCacheManager />
      </CDNProvider>
    );

    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);

    // Stats should be refreshed
    expect(screen.getByText('Cache Size:')).toBeInTheDocument();
  });
});

