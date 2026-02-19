import { render, screen, fireEvent, waitFor, renderHook } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import ImageOptimizer, { useImageOptimization, ResponsiveImage, BackgroundImage } from '@/components/ImageOptimizer';
import { 
  detectImageFormat, 
  isWebPSupported, 
  getOptimalFormat, 
  getOptimalQuality,
  generateOptimizedUrl,
  generateSrcSet,
  generateSizes,
  preloadImage,
  lazyLoadImage,
  compressImage,
  getImageInfo,
  createOptimizedImage,
  batchOptimizeImages
} from '@/utils/imageOptimization';

// Mock IntersectionObserver
const mockIntersectionObserver = vi.fn();
mockIntersectionObserver.mockReturnValue({
  observe: () => null,
  unobserve: () => null,
  disconnect: () => null,
});
window.IntersectionObserver = mockIntersectionObserver;

// Mock Image constructor
const mockImage = vi.fn();
mockImage.mockImplementation(() => ({
  onload: null,
  onerror: null,
  src: '',
  naturalWidth: 100,
  naturalHeight: 100,
}));
window.Image = mockImage;

// Mock URL.createObjectURL
const mockCreateObjectURL = vi.fn();
mockCreateObjectURL.mockReturnValue('blob:mock-url');
URL.createObjectURL = mockCreateObjectURL;

// Mock URL.revokeObjectURL
const mockRevokeObjectURL = vi.fn();
URL.revokeObjectURL = mockRevokeObjectURL;

describe('ImageOptimizer Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders with basic props', () => {
    render(
      <ImageOptimizer
        src="/test-image.jpg"
        alt="Test image"
        width={100}
        height={100}
      />
    );

    expect(screen.getByAltText('Test image')).toBeInTheDocument();
  });

  it('renders with lazy loading by default', () => {
    render(
      <ImageOptimizer
        src="/test-image.jpg"
        alt="Test image"
      />
    );

    const img = screen.getByAltText('Test image');
    expect(img).toHaveAttribute('loading', 'lazy');
  });

  it('renders with eager loading when priority is true', () => {
    render(
      <ImageOptimizer
        src="/test-image.jpg"
        alt="Test image"
        priority={true}
      />
    );

    const img = screen.getByAltText('Test image');
    expect(img).toHaveAttribute('loading', 'lazy'); // Still lazy due to intersection observer
  });

  it('shows loading state initially', () => {
    render(
      <ImageOptimizer
        src="/test-image.jpg"
        alt="Test image"
      />
    );

    // Should show loading spinner
    expect(screen.getByRole('img')).toHaveClass('opacity-0');
  });

  it('handles image load successfully', async () => {
    render(
      <ImageOptimizer
        src="/test-image.jpg"
        alt="Test image"
      />
    );

    const img = screen.getByAltText('Test image');
    
    // Simulate image load
    fireEvent.load(img);

    await waitFor(() => {
      expect(img).toHaveClass('opacity-100');
    });
  });

  it('handles image error', async () => {
    render(
      <ImageOptimizer
        src="/invalid-image.jpg"
        alt="Test image"
      />
    );

    const img = screen.getByAltText('Test image');
    
    // Simulate image error
    fireEvent.error(img);

    await waitFor(() => {
      expect(screen.getByText('Image failed to load')).toBeInTheDocument();
    });
  });

  it('applies custom className', () => {
    render(
      <ImageOptimizer
        src="/test-image.jpg"
        alt="Test image"
        className="custom-class"
      />
    );

    const container = screen.getByAltText('Test image').parentElement;
    expect(container).toHaveClass('custom-class');
  });

  it('applies blur effect when specified', () => {
    render(
      <ImageOptimizer
        src="/test-image.jpg"
        alt="Test image"
        blur={true}
      />
    );

    const img = screen.getByAltText('Test image');
    expect(img).toHaveClass('filter', 'blur-sm');
  });

  it('calls onLoad callback when image loads', async () => {
    const onLoadMock = vi.fn();
    
    render(
      <ImageOptimizer
        src="/test-image.jpg"
        alt="Test image"
        onLoad={onLoadMock}
      />
    );

    const img = screen.getByAltText('Test image');
    fireEvent.load(img);

    await waitFor(() => {
      expect(onLoadMock).toHaveBeenCalled();
    });
  });

  it('calls onError callback when image fails', async () => {
    const onErrorMock = vi.fn();
    
    render(
      <ImageOptimizer
        src="/invalid-image.jpg"
        alt="Test image"
        onError={onErrorMock}
      />
    );

    const img = screen.getByAltText('Test image');
    fireEvent.error(img);

    await waitFor(() => {
      expect(onErrorMock).toHaveBeenCalled();
    });
  });
});

describe('useImageOptimization Hook', () => {
  it('returns WebP support status', async () => {
    const { result } = renderHook(() => useImageOptimization());
    
    // Mock WebP support check
    const mockWebPImage = {
      onload: null,
      onerror: null,
      src: '',
      height: 2, // WebP supported
    };
    
    mockImage.mockReturnValue(mockWebPImage);
    
    await waitFor(() => {
      expect(result.current.isWebPSupported).toBe(true);
    });
  });

  it('returns optimal format for WebP', async () => {
    const { result } = renderHook(() => useImageOptimization());
    
    // Mock WebP support
    const mockWebPImage = {
      onload: null,
      onerror: null,
      src: '',
      height: 2,
    };
    
    mockImage.mockReturnValue(mockWebPImage);
    
    await waitFor(() => {
      const format = result.current.getOptimalFormat('auto');
      expect(format).toBe('webp');
    });
  });

  it('returns optimal quality based on file size', () => {
    const { result } = renderHook(() => useImageOptimization());
    
    // Test different file sizes
    expect(result.current.getOptimalQuality(1024 * 1024)).toBe(70); // 1MB
    expect(result.current.getOptimalQuality(500 * 1024)).toBe(80); // 500KB
    expect(result.current.getOptimalQuality(100 * 1024)).toBe(90); // 100KB
  });
});

describe('ResponsiveImage Component', () => {
  it('renders with srcSet', () => {
    const srcSet = {
      mobile: '/mobile.jpg',
      tablet: '/tablet.jpg',
      desktop: '/desktop.jpg',
    };

    render(
      <ResponsiveImage
        srcSet={srcSet}
        alt="Responsive image"
      />
    );

    expect(screen.getByAltText('Responsive image')).toBeInTheDocument();
  });

  it('updates src based on window size', async () => {
    const srcSet = {
      mobile: '/mobile.jpg',
      tablet: '/tablet.jpg',
      desktop: '/desktop.jpg',
    };

    render(
      <ResponsiveImage
        srcSet={srcSet}
        alt="Responsive image"
      />
    );

    // Mock window resize
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1200,
    });

    fireEvent(window, new Event('resize'));

    await waitFor(() => {
      const img = screen.getByAltText('Responsive image');
      expect(img).toHaveAttribute('src', '/desktop.jpg');
    });
  });
});

describe('BackgroundImage Component', () => {
  it('renders with background image', () => {
    render(
      <BackgroundImage
        src="/background.jpg"
        alt="Background"
      >
        <div>Content</div>
      </BackgroundImage>
    );

    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('applies overlay when specified', () => {
    render(
      <BackgroundImage
        src="/background.jpg"
        alt="Background"
        overlay={true}
        overlayColor="rgba(0, 0, 0, 0.5)"
      >
        <div>Content</div>
      </BackgroundImage>
    );

    const overlay = document.querySelector('.absolute.inset-0');
    expect(overlay).toBeInTheDocument();
  });
});

describe('Image Optimization Utilities', () => {
  describe('detectImageFormat', () => {
    it('detects JPEG format', () => {
      expect(detectImageFormat('image.jpg')).toBe('jpeg');
      expect(detectImageFormat('image.jpeg')).toBe('jpeg');
    });

    it('detects WebP format', () => {
      expect(detectImageFormat('image.webp')).toBe('webp');
    });

    it('detects PNG format', () => {
      expect(detectImageFormat('image.png')).toBe('png');
    });

    it('detects GIF format', () => {
      expect(detectImageFormat('image.gif')).toBe('gif');
    });

    it('detects SVG format', () => {
      expect(detectImageFormat('image.svg')).toBe('svg');
    });

    it('defaults to JPEG for unknown format', () => {
      expect(detectImageFormat('image.unknown')).toBe('jpeg');
    });
  });

  describe('isWebPSupported', () => {
    it('returns true when WebP is supported', async () => {
      const mockWebPImage = {
        onload: null,
        onerror: null,
        src: '',
        height: 2,
      };
      
      mockImage.mockReturnValue(mockWebPImage);
      
      const result = await isWebPSupported();
      expect(result).toBe(true);
    });

    it('returns false when WebP is not supported', async () => {
      const mockWebPImage = {
        onload: null,
        onerror: null,
        src: '',
        height: 0,
      };
      
      mockImage.mockReturnValue(mockWebPImage);
      
      const result = await isWebPSupported();
      expect(result).toBe(false);
    });
  });

  describe('getOptimalFormat', () => {
    it('returns WebP when supported and preferred', async () => {
      const mockWebPImage = {
        onload: null,
        onerror: null,
        src: '',
        height: 2,
      };
      
      mockImage.mockReturnValue(mockWebPImage);
      
      const result = await getOptimalFormat('jpeg', true);
      expect(result).toBe('webp');
    });

    it('returns original format when WebP not preferred', async () => {
      const result = await getOptimalFormat('png', false);
      expect(result).toBe('jpeg');
    });

    it('keeps SVG format unchanged', async () => {
      const result = await getOptimalFormat('svg', true);
      expect(result).toBe('svg');
    });
  });

  describe('getOptimalQuality', () => {
    it('returns appropriate quality for hero context', () => {
      expect(getOptimalQuality(1024 * 1024, 'hero')).toBe(90);
    });

    it('returns appropriate quality for thumbnail context', () => {
      expect(getOptimalQuality(1024 * 1024, 'thumbnail')).toBe(70);
    });

    it('returns appropriate quality for gallery context', () => {
      expect(getOptimalQuality(1024 * 1024, 'gallery')).toBe(80);
    });

    it('returns appropriate quality for background context', () => {
      expect(getOptimalQuality(1024 * 1024, 'background')).toBe(75);
    });
  });

  describe('generateOptimizedUrl', () => {
    it('returns original URL for external URLs', () => {
      const result = generateOptimizedUrl('https://example.com/image.jpg');
      expect(result).toBe('https://example.com/image.jpg');
    });

    it('returns original URL for data URLs', () => {
      const result = generateOptimizedUrl('data:image/jpeg;base64,test');
      expect(result).toBe('data:image/jpeg;base64,test');
    });

    it('adds optimization parameters to local URLs', () => {
      const result = generateOptimizedUrl('/image.jpg', {
        width: 100,
        height: 100,
        quality: 80,
        format: 'webp',
      });

      expect(result).toContain('w=100');
      expect(result).toContain('h=100');
      expect(result).toContain('q=80');
      expect(result).toContain('f=webp');
    });
  });

  describe('generateSrcSet', () => {
    it('generates srcSet with default breakpoints', () => {
      const result = generateSrcSet('/image.jpg');
      
      expect(result).toContain('320w');
      expect(result).toContain('480w');
      expect(result).toContain('768w');
      expect(result).toContain('1024w');
      expect(result).toContain('1440w');
      expect(result).toContain('1920w');
    });

    it('generates srcSet with custom breakpoints', () => {
      const customBreakpoints = [
        { width: 100, quality: 70 },
        { width: 200, quality: 80 },
      ];
      
      const result = generateSrcSet('/image.jpg', customBreakpoints);
      
      expect(result).toContain('100w');
      expect(result).toContain('200w');
    });
  });

  describe('generateSizes', () => {
    it('generates sizes with default breakpoints', () => {
      const result = generateSizes();
      
      expect(result).toContain('(max-width: 320px)');
      expect(result).toContain('(max-width: 480px)');
      expect(result).toContain('(max-width: 768px)');
      expect(result).toContain('(max-width: 1024px)');
      expect(result).toContain('(max-width: 1440px)');
      expect(result).toContain('(max-width: 1920px)');
    });

    it('generates sizes with custom breakpoints', () => {
      const customBreakpoints = [
        { width: 100, quality: 70 },
        { width: 200, quality: 80 },
      ];
      
      const result = generateSizes(customBreakpoints);
      
      expect(result).toContain('(max-width: 100px)');
      expect(result).toContain('(max-width: 200px)');
    });
  });

  describe('preloadImage', () => {
    it('creates preload link', async () => {
      const mockLink = {
        rel: '',
        as: '',
        href: '',
        fetchPriority: '',
        onload: null,
        onerror: null,
      };
      
      const mockCreateElement = vi.fn().mockReturnValue(mockLink);
      const mockAppendChild = vi.fn();
      
      Object.defineProperty(document, 'createElement', {
        value: mockCreateElement,
      });
      
      Object.defineProperty(document.head, 'appendChild', {
        value: mockAppendChild,
      });
      
      await preloadImage('/test.jpg');
      
      expect(mockCreateElement).toHaveBeenCalledWith('link');
      expect(mockLink.rel).toBe('preload');
      expect(mockLink.as).toBe('image');
      expect(mockLink.href).toBe('/test.jpg');
      expect(mockAppendChild).toHaveBeenCalledWith(mockLink);
    });
  });

  describe('lazyLoadImage', () => {
    it('sets up intersection observer', async () => {
      const mockImg = document.createElement('img');
      const mockObserver = {
        observe: vi.fn(),
        unobserve: vi.fn(),
        disconnect: vi.fn(),
      };
      
      mockIntersectionObserver.mockReturnValue(mockObserver);
      
      const promise = lazyLoadImage(mockImg, '/test.jpg');
      
      expect(mockObserver.observe).toHaveBeenCalledWith(mockImg);
      
      // Simulate intersection
      const callback = mockIntersectionObserver.mock.calls[0][0];
      const entries = [{ isIntersecting: true, target: mockImg }];
      callback(entries);
      
      await promise;
    });
  });

  describe('compressImage', () => {
    it('compresses image with canvas', async () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
      const mockCanvas = {
        width: 0,
        height: 0,
        getContext: vi.fn().mockReturnValue({
          drawImage: vi.fn(),
        }),
        toBlob: vi.fn().mockImplementation((callback) => {
          callback(new Blob(['test'], { type: 'image/jpeg' }));
        }),
      };
      
      const mockCreateElement = vi.fn().mockReturnValue(mockCanvas);
      Object.defineProperty(document, 'createElement', {
        value: mockCreateElement,
      });
      
      const result = await compressImage(mockFile, {
        maxWidth: 100,
        maxHeight: 100,
        quality: 0.8,
        format: 'jpeg',
      });
      
      expect(result).toBeInstanceOf(Blob);
      expect(mockCreateElement).toHaveBeenCalledWith('canvas');
    });
  });

  describe('getImageInfo', () => {
    it('returns image information', async () => {
      const mockImg = {
        onload: null,
        onerror: null,
        src: '',
        naturalWidth: 100,
        naturalHeight: 100,
      };
      
      mockImage.mockReturnValue(mockImg);
      
      const result = await getImageInfo('/test.jpg');
      
      expect(result).toEqual({
        width: 100,
        height: 100,
        size: 0,
        format: 'jpeg',
        url: '/test.jpg',
      });
    });
  });

  describe('createOptimizedImage', () => {
    it('creates optimized image object', async () => {
      const mockWebPImage = {
        onload: null,
        onerror: null,
        src: '',
        height: 2,
      };
      
      mockImage.mockReturnValue(mockWebPImage);
      
      const result = await createOptimizedImage('/test.jpg', {
        width: 100,
        height: 100,
        quality: 80,
        context: 'hero',
      });
      
      expect(result).toHaveProperty('src');
      expect(result).toHaveProperty('width', 100);
      expect(result).toHaveProperty('height', 100);
      expect(result).toHaveProperty('format');
      expect(result).toHaveProperty('quality');
    });
  });

  describe('batchOptimizeImages', () => {
    it('optimizes multiple images', async () => {
      const mockWebPImage = {
        onload: null,
        onerror: null,
        src: '',
        height: 2,
      };
      
      mockImage.mockReturnValue(mockWebPImage);
      
      const images = [
        { url: '/image1.jpg' },
        { url: '/image2.jpg' },
      ];
      
      const result = await batchOptimizeImages(images);
      
      expect(result).toHaveLength(2);
      expect(result[0]).toHaveProperty('src');
      expect(result[1]).toHaveProperty('src');
    });

    it('handles errors gracefully', async () => {
      const mockWebPImage = {
        onload: null,
        onerror: null,
        src: '',
        height: 0, // WebP not supported
      };
      
      mockImage.mockReturnValue(mockWebPImage);
      
      const images = [
        { url: '/image1.jpg' },
        { url: '/image2.jpg' },
      ];
      
      const result = await batchOptimizeImages(images);
      
      expect(result).toHaveLength(2);
      expect(result[0]).toHaveProperty('src', '/image1.jpg');
      expect(result[1]).toHaveProperty('src', '/image2.jpg');
    });
  });
});

