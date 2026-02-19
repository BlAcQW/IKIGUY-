/**
 * Image Optimization Utilities
 * 
 * This module provides utilities for optimizing images, including:
 * - Format detection and conversion
 * - Compression and quality optimization
 * - Responsive image generation
 * - Lazy loading utilities
 */

export interface ImageInfo {
	width: number;
	height: number;
	size: number;
	format: string;
	url: string;
}

export interface OptimizedImage {
	src: string;
	srcSet?: string;
	sizes?: string;
	width: number;
	height: number;
	format: string;
	quality: number;
}

export interface ResponsiveBreakpoint {
	width: number;
	quality: number;
	format?: string;
}

// Default responsive breakpoints
export const DEFAULT_BREAKPOINTS: ResponsiveBreakpoint[] = [
	{ width: 320, quality: 70 },   // Mobile small
	{ width: 480, quality: 75 },   // Mobile large
	{ width: 768, quality: 80 },   // Tablet
	{ width: 1024, quality: 85 },  // Desktop small
	{ width: 1440, quality: 90 },  // Desktop large
	{ width: 1920, quality: 95 },  // Desktop extra large
];

// Supported image formats
export const SUPPORTED_FORMATS = ['webp', 'jpeg', 'jpg', 'png', 'gif', 'svg'] as const;
export type SupportedFormat = typeof SUPPORTED_FORMATS[number];

/**
 * Detect image format from URL or file extension
 */
export function detectImageFormat(url: string): SupportedFormat {
	const extension = url.split('.').pop()?.toLowerCase();

	if (extension === 'jpg' || extension === 'jpeg') return 'jpeg';
	if (extension === 'webp') return 'webp';
	if (extension === 'png') return 'png';
	if (extension === 'gif') return 'gif';
	if (extension === 'svg') return 'svg';

	// Default to jpeg if format cannot be detected
	return 'jpeg';
}

/**
 * Check if browser supports WebP format
 */
export function isWebPSupported(): Promise<boolean> {
	return new Promise((resolve) => {
		const webP = new Image();
		webP.onload = webP.onerror = () => {
			resolve(webP.height === 2);
		};
		webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
	});
}

/**
 * Get optimal image format based on browser support and original format
 */
export async function getOptimalFormat(
	originalFormat: SupportedFormat,
	preferWebP: boolean = true
): Promise<SupportedFormat> {
	// Always prefer WebP if supported and requested
	if (preferWebP && originalFormat !== 'svg' && await isWebPSupported()) {
		return 'webp';
	}

	// For vector graphics, keep original format
	if (originalFormat === 'svg') {
		return 'svg';
	}

	// For other formats, return original or fallback to jpeg
	return originalFormat === 'gif' ? 'gif' : 'jpeg';
}

/**
 * Calculate optimal quality based on file size and usage context
 */
export function getOptimalQuality(
	fileSize: number,
	context: 'hero' | 'thumbnail' | 'gallery' | 'background' = 'gallery'
): number {
	const sizeMB = fileSize / (1024 * 1024);

	// Base quality by context
	const contextQuality = {
		hero: 90,
		thumbnail: 70,
		gallery: 80,
		background: 75,
	}[context];

	// Adjust based on file size
	if (sizeMB > 5) return Math.max(60, contextQuality - 20);
	if (sizeMB > 2) return Math.max(70, contextQuality - 10);
	if (sizeMB > 1) return contextQuality;

	return Math.min(95, contextQuality + 5);
}

/**
 * Generate optimized image URL with parameters
 */
export function generateOptimizedUrl(
	originalUrl: string,
	options: {
		width?: number;
		height?: number;
		quality?: number;
		format?: SupportedFormat;
		fit?: 'cover' | 'contain' | 'fill' | 'inside' | 'outside';
	} = {}
): string {
	// If it's an external URL or data URL, return as is
	if (originalUrl.startsWith('data:') || originalUrl.startsWith('http')) {
		return originalUrl;
	}

	// For local images, add optimization parameters
	const url = new URL(originalUrl, window.location.origin);

	if (options.width) url.searchParams.set('w', options.width.toString());
	if (options.height) url.searchParams.set('h', options.height.toString());
	if (options.quality) url.searchParams.set('q', options.quality.toString());
	if (options.format) url.searchParams.set('f', options.format);
	if (options.fit) url.searchParams.set('fit', options.fit);

	return url.toString();
}

/**
 * Generate responsive image srcSet
 */
export function generateSrcSet(
	originalUrl: string,
	breakpoints: ResponsiveBreakpoint[] = DEFAULT_BREAKPOINTS,
	format?: SupportedFormat
): string {
	return breakpoints
		.map(({ width, quality, format: bpFormat }) => {
			const optimizedUrl = generateOptimizedUrl(originalUrl, {
				width,
				quality,
				format: bpFormat || format,
			});
			return `${optimizedUrl} ${width}w`;
		})
		.join(', ');
}

/**
 * Generate responsive sizes attribute
 */
export function generateSizes(
	breakpoints: ResponsiveBreakpoint[] = DEFAULT_BREAKPOINTS,
	containerWidth: number = 100
): string {
	return breakpoints
		.map(({ width }) => {
			const percentage = (width / containerWidth) * 100;
			return `(max-width: ${width}px) ${percentage}vw`;
		})
		.join(', ') + `, ${containerWidth}vw`;
}

/**
 * Preload critical images
 */
export function preloadImage(src: string, priority: 'high' | 'low' = 'low'): Promise<void> {
	return new Promise((resolve, reject) => {
		const link = document.createElement('link');
		link.rel = 'preload';
		link.as = 'image';
		link.href = src;
		link.fetchPriority = priority;

		link.onload = () => resolve();
		link.onerror = () => reject(new Error(`Failed to preload image: ${src}`));

		document.head.appendChild(link);
	});
}

/**
 * Lazy load image with intersection observer
 */
export function lazyLoadImage(
	imgElement: HTMLImageElement,
	src: string,
	options: {
		rootMargin?: string;
		threshold?: number;
	} = {}
): Promise<void> {
	return new Promise((resolve, reject) => {
		const observer = new IntersectionObserver(
			(entries) => {
				entries.forEach((entry) => {
					if (entry.isIntersecting) {
						const img = entry.target as HTMLImageElement;
						img.src = src;

						img.onload = () => {
							observer.unobserve(img);
							resolve();
						};

						img.onerror = () => {
							observer.unobserve(img);
							reject(new Error(`Failed to load image: ${src}`));
						};
					}
				});
			},
			{
				rootMargin: options.rootMargin || '50px 0px',
				threshold: options.threshold || 0.01,
			}
		);

		observer.observe(imgElement);
	});
}

/**
 * Compress image data using Canvas API
 */
export function compressImage(
	file: File,
	options: {
		maxWidth?: number;
		maxHeight?: number;
		quality?: number;
		format?: 'jpeg' | 'png' | 'webp';
	} = {}
): Promise<Blob> {
	return new Promise((resolve, reject) => {
		const canvas = document.createElement('canvas');
		const ctx = canvas.getContext('2d');

		if (!ctx) {
			reject(new Error('Canvas context not supported'));
			return;
		}

		const img = new Image();
		img.onload = () => {
			// Calculate new dimensions
			let { width, height } = img;
			const { maxWidth, maxHeight } = options;

			if (maxWidth && width > maxWidth) {
				height = (height * maxWidth) / width;
				width = maxWidth;
			}

			if (maxHeight && height > maxHeight) {
				width = (width * maxHeight) / height;
				height = maxHeight;
			}

			// Set canvas dimensions
			canvas.width = width;
			canvas.height = height;

			// Draw and compress image
			ctx.drawImage(img, 0, 0, width, height);

			const format = options.format || 'jpeg';
			const quality = options.quality || 0.8;

			canvas.toBlob(
				(blob) => {
					if (blob) {
						resolve(blob);
					} else {
						reject(new Error('Failed to compress image'));
					}
				},
				`image/${format}`,
				quality
			);
		};

		img.onerror = () => reject(new Error('Failed to load image for compression'));
		img.src = URL.createObjectURL(file);
	});
}

/**
 * Get image information
 */
export function getImageInfo(url: string): Promise<ImageInfo> {
	return new Promise((resolve, reject) => {
		const img = new Image();
		img.onload = () => {
			resolve({
				width: img.naturalWidth,
				height: img.naturalHeight,
				size: 0, // Size not available from Image object
				format: detectImageFormat(url),
				url,
			});
		};
		img.onerror = () => reject(new Error(`Failed to load image: ${url}`));
		img.src = url;
	});
}

/**
 * Create optimized image object
 */
export async function createOptimizedImage(
	originalUrl: string,
	options: {
		width?: number;
		height?: number;
		quality?: number;
		format?: SupportedFormat;
		breakpoints?: ResponsiveBreakpoint[];
		context?: 'hero' | 'thumbnail' | 'gallery' | 'background';
	} = {}
): Promise<OptimizedImage> {
	const format = options.format || detectImageFormat(originalUrl);
	const optimalFormat = await getOptimalFormat(format);
	const quality = options.quality || getOptimalQuality(0, options.context);

	const optimizedImage: OptimizedImage = {
		src: generateOptimizedUrl(originalUrl, {
			width: options.width,
			height: options.height,
			quality,
			format: optimalFormat,
		}),
		width: options.width || 0,
		height: options.height || 0,
		format: optimalFormat,
		quality,
	};

	// Add responsive srcSet if breakpoints provided
	if (options.breakpoints) {
		optimizedImage.srcSet = generateSrcSet(originalUrl, options.breakpoints, optimalFormat);
		optimizedImage.sizes = generateSizes(options.breakpoints);
	}

	return optimizedImage;
}

/**
 * Batch optimize multiple images
 */
export async function batchOptimizeImages(
	images: Array<{ url: string; options?: Parameters<typeof createOptimizedImage>[1] }>
): Promise<OptimizedImage[]> {
	const optimizedImages: OptimizedImage[] = [];

	for (const { url, options } of images) {
		try {
			const optimized = await createOptimizedImage(url, options);
			optimizedImages.push(optimized);
		} catch (error) {
			console.error(`Failed to optimize image: ${url}`, error);
			// Add fallback
			optimizedImages.push({
				src: url,
				width: 0,
				height: 0,
				format: detectImageFormat(url),
				quality: 80,
			});
		}
	}

	return optimizedImages;
}

