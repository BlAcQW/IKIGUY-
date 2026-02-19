import React, { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';

interface ImageOptimizerProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  placeholder?: string;
  loading?: 'lazy' | 'eager';
  sizes?: string;
  quality?: number;
  format?: 'webp' | 'jpeg' | 'png' | 'auto';
  blur?: boolean;
  priority?: boolean;
  onLoad?: () => void;
  onError?: (error: Error) => void;
}

interface ImageState {
  isLoaded: boolean;
  isError: boolean;
  isInView: boolean;
}

export function ImageOptimizer({
  src,
  alt,
  width,
  height,
  className,
  placeholder = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSIjOWNhM2FmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+TG9hZGluZy4uLjwvdGV4dD48L3N2Zz4=',
  loading = 'lazy',
  sizes = '100vw',
  quality = 80,
  format = 'auto',
  blur = false,
  priority = false,
  onLoad,
  onError,
}: ImageOptimizerProps) {
  const [state, setState] = useState<ImageState>({
    isLoaded: false,
    isError: false,
    isInView: false,
  });
  
  const imgRef = useRef<HTMLImageElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  // Generate optimized image URL
  const generateOptimizedUrl = (originalSrc: string): string => {
    // If it's already an optimized URL or external URL, return as is
    if (originalSrc.startsWith('data:') || originalSrc.startsWith('http')) {
      return originalSrc;
    }

    // For local images, we can add optimization parameters
    // In a real implementation, you might use a CDN or image optimization service
    const url = new URL(originalSrc, window.location.origin);
    
    if (width) url.searchParams.set('w', width.toString());
    if (height) url.searchParams.set('h', height.toString());
    if (quality !== 80) url.searchParams.set('q', quality.toString());
    if (format !== 'auto') url.searchParams.set('f', format);
    
    return url.toString();
  };

  // Intersection Observer for lazy loading
  useEffect(() => {
    if (loading === 'lazy' && !priority) {
      observerRef.current = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              setState(prev => ({ ...prev, isInView: true }));
              if (observerRef.current) {
                observerRef.current.unobserve(entry.target);
              }
            }
          });
        },
        {
          rootMargin: '50px 0px',
          threshold: 0.01,
        }
      );

      if (imgRef.current) {
        observerRef.current.observe(imgRef.current);
      }
    } else {
      // For eager loading or priority images, load immediately
      setState(prev => ({ ...prev, isInView: true }));
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [loading, priority]);

  // Handle image load
  const handleLoad = () => {
    setState(prev => ({ ...prev, isLoaded: true }));
    onLoad?.();
  };

  // Handle image error
  const handleError = () => {
    setState(prev => ({ ...prev, isError: true }));
    onError?.(new Error(`Failed to load image: ${src}`));
  };

  // Determine if we should show the actual image
  const shouldShowImage = state.isInView || priority;
  const optimizedSrc = shouldShowImage ? generateOptimizedUrl(src) : placeholder;

  return (
    <div 
      className={cn(
        'relative overflow-hidden',
        className
      )}
      style={{
        width: width ? `${width}px` : 'auto',
        height: height ? `${height}px` : 'auto',
      }}
    >
      {/* Placeholder/Blur effect */}
      {!state.isLoaded && !state.isError && (
        <div 
          className="absolute inset-0 bg-gray-200 animate-pulse"
          style={{
            backgroundImage: `url(${placeholder})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}
        />
      )}

      {/* Main image */}
      <img
        ref={imgRef}
        src={optimizedSrc}
        alt={alt}
        width={width}
        height={height}
        loading={loading}
        sizes={sizes}
        className={cn(
          'transition-opacity duration-300',
          state.isLoaded ? 'opacity-100' : 'opacity-0',
          blur && 'filter blur-sm',
          'w-full h-full object-cover'
        )}
        onLoad={handleLoad}
        onError={handleError}
        style={{
          minHeight: height ? `${height}px` : 'auto',
        }}
      />

      {/* Error state */}
      {state.isError && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 text-gray-500 text-sm">
          <div className="text-center">
            <div className="text-2xl mb-2">📷</div>
            <div>Image failed to load</div>
          </div>
        </div>
      )}

      {/* Loading indicator */}
      {!state.isLoaded && !state.isError && shouldShowImage && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      )}
    </div>
  );
}

// Hook for image optimization
export function useImageOptimization() {
  const [isWebPSupported, setIsWebPSupported] = useState(false);

  useEffect(() => {
    // Check WebP support
    const webP = new Image();
    webP.onload = webP.onerror = () => {
      setIsWebPSupported(webP.height === 2);
    };
    webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
  }, []);

  const getOptimalFormat = (preferredFormat: string = 'auto'): string => {
    if (preferredFormat === 'auto') {
      return isWebPSupported ? 'webp' : 'jpeg';
    }
    return preferredFormat;
  };

  const getOptimalQuality = (fileSize: number): number => {
    // Adjust quality based on file size
    if (fileSize > 1024 * 1024) return 70; // Large files
    if (fileSize > 500 * 1024) return 80; // Medium files
    return 90; // Small files
  };

  return {
    isWebPSupported,
    getOptimalFormat,
    getOptimalQuality,
  };
}

// Responsive image component
interface ResponsiveImageProps extends Omit<ImageOptimizerProps, 'src'> {
  srcSet: {
    mobile: string;
    tablet: string;
    desktop: string;
  };
  breakpoints?: {
    mobile: number;
    tablet: number;
    desktop: number;
  };
}

export function ResponsiveImage({
  srcSet,
  breakpoints = { mobile: 768, tablet: 1024, desktop: 1920 },
  ...props
}: ResponsiveImageProps) {
  const [currentSrc, setCurrentSrc] = useState(srcSet.mobile);

  useEffect(() => {
    const updateSrc = () => {
      const width = window.innerWidth;
      if (width >= breakpoints.desktop) {
        setCurrentSrc(srcSet.desktop);
      } else if (width >= breakpoints.tablet) {
        setCurrentSrc(srcSet.tablet);
      } else {
        setCurrentSrc(srcSet.mobile);
      }
    };

    updateSrc();
    window.addEventListener('resize', updateSrc);
    return () => window.removeEventListener('resize', updateSrc);
  }, [srcSet, breakpoints]);

  return <ImageOptimizer src={currentSrc} {...props} />;
}

// Background image component
interface BackgroundImageProps extends Omit<ImageOptimizerProps, 'src'> {
  src: string;
  children: React.ReactNode;
  overlay?: boolean;
  overlayColor?: string;
  overlayOpacity?: number;
}

export function BackgroundImage({
  src,
  children,
  overlay = false,
  overlayColor = 'rgba(0, 0, 0, 0.5)',
  overlayOpacity = 0.5,
  ...props
}: BackgroundImageProps) {
  const [isLoaded, setIsLoaded] = useState(false);

  return (
    <div className="relative">
      <ImageOptimizer
        src={src}
        {...props}
        className="absolute inset-0 w-full h-full object-cover"
        onLoad={() => setIsLoaded(true)}
      />
      {overlay && (
        <div
          className="absolute inset-0"
          style={{
            backgroundColor: overlayColor,
            opacity: overlayOpacity,
          }}
        />
      )}
      <div className={cn('relative z-10', !isLoaded && 'opacity-0')}>
        {children}
      </div>
    </div>
  );
}

// Default export for backward compatibility
export default ImageOptimizer;

