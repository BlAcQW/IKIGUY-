/**
 * CDN Integration Utilities
 * 
 * This module provides utilities for integrating with CDN services for static assets,
 * including automatic CDN URL generation, fallback handling, and performance optimization.
 */

export interface CDNConfig {
	baseUrl: string;
	version?: string;
	fallbackUrl?: string;
	enableCache?: boolean;
	cacheDuration?: number;
	enableCompression?: boolean;
	enableWebP?: boolean;
	enableAvif?: boolean;
}

export interface CDNResponse {
	url: string;
	cached: boolean;
	fallback: boolean;
	performance: {
		loadTime: number;
		size: number;
	};
}

// Default CDN configuration
export const DEFAULT_CDN_CONFIG: CDNConfig = {
	baseUrl: import.meta.env.VITE_CDN_URL || '',
	version: import.meta.env.VITE_APP_VERSION || '1.0.0',
	fallbackUrl: import.meta.env.VITE_FALLBACK_URL || '',
	enableCache: true,
	cacheDuration: 24 * 60 * 60 * 1000, // 24 hours
	enableCompression: true,
	enableWebP: true,
	enableAvif: true,
};

// CDN cache for performance optimization
const cdnCache = new Map<string, { url: string; timestamp: number; data: any }>();

/**
 * Generate CDN URL for static assets
 */
export function generateCDNUrl(
	path: string,
	config: Partial<CDNConfig> = {}
): string {
	const finalConfig = { ...DEFAULT_CDN_CONFIG, ...config };

	if (!finalConfig.baseUrl) {
		return path; // Fallback to original path if no CDN configured
	}

	// Remove leading slash if present
	const cleanPath = path.startsWith('/') ? path.slice(1) : path;

	// Build CDN URL
	let cdnUrl = `${finalConfig.baseUrl}/${cleanPath}`;

	// Add version for cache busting
	if (finalConfig.version) {
		cdnUrl += `?v=${finalConfig.version}`;
	}

	// Add compression parameters
	if (finalConfig.enableCompression) {
		cdnUrl += `${finalConfig.version ? '&' : '?'}compress=true`;
	}

	return cdnUrl;
}

/**
 * Generate responsive CDN URLs for images
 */
export function generateResponsiveCDNUrls(
	imagePath: string,
	sizes: number[],
	config: Partial<CDNConfig> = {}
): string[] {
	const finalConfig = { ...DEFAULT_CDN_CONFIG, ...config };

	if (!finalConfig.baseUrl) {
		return [imagePath]; // Fallback to original path
	}

	return sizes.map(size => {
		const baseUrl = generateCDNUrl(imagePath, finalConfig);
		return `${baseUrl}&w=${size}`;
	});
}

/**
 * Generate srcSet for responsive images
 */
export function generateCDNSrcSet(
	imagePath: string,
	breakpoints: { width: number; quality?: number }[],
	config: Partial<CDNConfig> = {}
): string {
	const finalConfig = { ...DEFAULT_CDN_CONFIG, ...config };

	if (!finalConfig.baseUrl) {
		return imagePath; // Fallback to original path
	}

	return breakpoints
		.map(({ width, quality = 80 }) => {
			const cdnUrl = generateCDNUrl(imagePath, finalConfig);
			const url = `${cdnUrl}&w=${width}&q=${quality}`;
			return `${url} ${width}w`;
		})
		.join(', ');
}

/**
 * Preload CDN assets for better performance
 */
export async function preloadCDNAsset(
	path: string,
	type: 'image' | 'script' | 'style' | 'font' = 'image',
	config: Partial<CDNConfig> = {}
): Promise<void> {
	const cdnUrl = generateCDNUrl(path, config);

	return new Promise((resolve, reject) => {
		const link = document.createElement('link');
		link.rel = 'preload';
		link.as = type;
		link.href = cdnUrl;
		link.fetchPriority = 'high';

		link.onload = () => resolve();
		link.onerror = () => reject(new Error(`Failed to preload: ${cdnUrl}`));

		document.head.appendChild(link);
	});
}

/**
 * Load asset from CDN with fallback
 */
export async function loadCDNAsset(
	path: string,
	config: Partial<CDNConfig> = {}
): Promise<CDNResponse> {
	const finalConfig = { ...DEFAULT_CDN_CONFIG, ...config };
	const startTime = performance.now();

	// Check cache first
	const cacheKey = `${path}-${finalConfig.version}`;
	if (finalConfig.enableCache && cdnCache.has(cacheKey)) {
		const cached = cdnCache.get(cacheKey)!;
		if (Date.now() - cached.timestamp < (finalConfig.cacheDuration || 0)) {
			return {
				url: cached.url,
				cached: true,
				fallback: false,
				performance: {
					loadTime: 0,
					size: 0,
				},
			};
		}
	}

	const cdnUrl = generateCDNUrl(path, finalConfig);

	try {
		// Try CDN first
		const response = await fetch(cdnUrl, { method: 'HEAD' });

		if (response.ok) {
			const loadTime = performance.now() - startTime;
			const size = parseInt(response.headers.get('content-length') || '0');

			const result: CDNResponse = {
				url: cdnUrl,
				cached: false,
				fallback: false,
				performance: { loadTime, size },
			};

			// Cache the result
			if (finalConfig.enableCache) {
				cdnCache.set(cacheKey, {
					url: cdnUrl,
					timestamp: Date.now(),
					data: result,
				});
			}

			return result;
		}
	} catch (error) {
		console.warn(`CDN failed for ${path}:`, error);
	}

	// Fallback to original URL
	if (finalConfig.fallbackUrl) {
		const fallbackUrl = `${finalConfig.fallbackUrl}/${path}`;
		const loadTime = performance.now() - startTime;

		return {
			url: fallbackUrl,
			cached: false,
			fallback: true,
			performance: { loadTime, size: 0 },
		};
	}

	// Final fallback to original path
	const loadTime = performance.now() - startTime;
	return {
		url: path,
		cached: false,
		fallback: true,
		performance: { loadTime, size: 0 },
	};
}

/**
 * Batch load multiple CDN assets
 */
export async function batchLoadCDNAssets(
	paths: string[],
	config: Partial<CDNConfig> = {}
): Promise<CDNResponse[]> {
	const promises = paths.map(path => loadCDNAsset(path, config));
	return Promise.allSettled(promises).then(results =>
		results.map(result =>
			result.status === 'fulfilled' ? result.value : {
				url: '',
				cached: false,
				fallback: true,
				performance: { loadTime: 0, size: 0 },
			}
		)
	);
}

/**
 * Optimize image for CDN with format detection
 */
export function optimizeImageForCDN(
	imagePath: string,
	options: {
		width?: number;
		height?: number;
		quality?: number;
		format?: 'auto' | 'webp' | 'avif' | 'jpeg' | 'png';
		fit?: 'cover' | 'contain' | 'fill' | 'inside' | 'outside';
	} = {},
	config: Partial<CDNConfig> = {}
): string {
	const finalConfig = { ...DEFAULT_CDN_CONFIG, ...config };

	if (!finalConfig.baseUrl) {
		return imagePath; // Fallback to original path
	}

	let cdnUrl = generateCDNUrl(imagePath, finalConfig);

	// Add image optimization parameters
	const params = new URLSearchParams();

	if (options.width) params.append('w', options.width.toString());
	if (options.height) params.append('h', options.height.toString());
	if (options.quality) params.append('q', options.quality.toString());
	if (options.fit) params.append('fit', options.fit);

	// Add format optimization
	if (options.format === 'auto') {
		if (finalConfig.enableAvif) {
			params.append('f', 'avif');
		} else if (finalConfig.enableWebP) {
			params.append('f', 'webp');
		}
	} else if (options.format) {
		params.append('f', options.format);
	}

	// Add parameters to URL
	if (params.toString()) {
		cdnUrl += `${cdnUrl.includes('?') ? '&' : '?'}${params.toString()}`;
	}

	return cdnUrl;
}

/**
 * Clear CDN cache
 */
export function clearCDNCache(): void {
	cdnCache.clear();
}

/**
 * Get CDN cache statistics
 */
export function getCDNCacheStats(): {
	size: number;
	entries: Array<{ key: string; timestamp: number; age: number }>;
} {
	const entries = Array.from(cdnCache.entries()).map(([key, value]) => ({
		key,
		timestamp: value.timestamp,
		age: Date.now() - value.timestamp,
	}));

	return {
		size: cdnCache.size,
		entries,
	};
}

/**
 * Monitor CDN performance
 */
export function monitorCDNPerformance(
	path: string,
	config: Partial<CDNConfig> = {}
): Promise<{
	cdnTime: number;
	fallbackTime: number;
	success: boolean;
}> {
	const finalConfig = { ...DEFAULT_CDN_CONFIG, ...config };

	return new Promise(async (resolve) => {
		const cdnUrl = generateCDNUrl(path, finalConfig);
		const fallbackUrl = finalConfig.fallbackUrl ? `${finalConfig.fallbackUrl}/${path}` : path;

		// Test CDN
		const cdnStart = performance.now();
		let cdnSuccess = false;

		try {
			const cdnResponse = await fetch(cdnUrl, { method: 'HEAD' });
			cdnSuccess = cdnResponse.ok;
		} catch (error) {
			console.warn('CDN test failed:', error);
		}

		const cdnTime = performance.now() - cdnStart;

		// Test fallback
		const fallbackStart = performance.now();
		let fallbackSuccess = false;

		try {
			const fallbackResponse = await fetch(fallbackUrl, { method: 'HEAD' });
			fallbackSuccess = fallbackResponse.ok;
		} catch (error) {
			console.warn('Fallback test failed:', error);
		}

		const fallbackTime = performance.now() - fallbackStart;

		resolve({
			cdnTime,
			fallbackTime,
			success: cdnSuccess || fallbackSuccess,
		});
	});
}

/**
 * Initialize CDN with configuration
 */
export function initializeCDN(config: Partial<CDNConfig> = {}): void {
	const finalConfig = { ...DEFAULT_CDN_CONFIG, ...config };

	// Set up global CDN configuration
	(window as any).__CDN_CONFIG__ = finalConfig;

	// Preload critical assets
	const criticalAssets = [
		// '/favicon.ico', // Removed - causing preload warning
		// '/logo.png', // Removed - file doesn't exist
		// '/hero-bg.jpg', // Removed - file is in assets, not public
	];

	criticalAssets.forEach(asset => {
		preloadCDNAsset(asset, 'image', finalConfig).catch(console.warn);
	});

	console.log('CDN initialized with config:', finalConfig);
}

/**
 * Get CDN configuration
 */
export function getCDNConfig(): CDNConfig {
	return { ...DEFAULT_CDN_CONFIG };
}

/**
 * Update CDN configuration
 */
export function updateCDNConfig(config: Partial<CDNConfig>): void {
	Object.assign(DEFAULT_CDN_CONFIG, config);
	(window as any).__CDN_CONFIG__ = DEFAULT_CDN_CONFIG;
}

/**
 * Check if CDN is available
 */
export async function isCDNAvailable(config: Partial<CDNConfig> = {}): Promise<boolean> {
	const finalConfig = { ...DEFAULT_CDN_CONFIG, ...config };

	if (!finalConfig.baseUrl) {
		return false;
	}

	try {
		const response = await fetch(`${finalConfig.baseUrl}/health`, { method: 'HEAD' });
		return response.ok;
	} catch (error) {
		return false;
	}
}

/**
 * Get CDN health status
 */
export async function getCDNHealth(config: Partial<CDNConfig> = {}): Promise<{
	available: boolean;
	responseTime: number;
	status: 'healthy' | 'degraded' | 'unavailable';
}> {
	const finalConfig = { ...DEFAULT_CDN_CONFIG, ...config };

	if (!finalConfig.baseUrl) {
		return {
			available: false,
			responseTime: 0,
			status: 'unavailable',
		};
	}

	const startTime = performance.now();

	try {
		const response = await fetch(`${finalConfig.baseUrl}/health`, { method: 'HEAD' });
		const responseTime = performance.now() - startTime;

		if (response.ok) {
			return {
				available: true,
				responseTime,
				status: responseTime < 1000 ? 'healthy' : 'degraded',
			};
		}
	} catch (error) {
		console.warn('CDN health check failed:', error);
	}

	return {
		available: false,
		responseTime: performance.now() - startTime,
		status: 'unavailable',
	};
}

