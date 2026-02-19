import React from 'react';

/**
 * Retry Logic Utilities for B2C Portal
 * 
 * Provides utilities for retrying failed API requests with exponential backoff
 * and configurable retry strategies.
 */

export interface RetryConfig {
	maxAttempts: number;
	baseDelay: number;
	maxDelay: number;
	backoffMultiplier: number;
	retryableErrors: string[];
	onRetry?: (attempt: number, error: Error) => void;
	onMaxAttemptsReached?: (error: Error) => void;
}

export interface RetryResult<T> {
	success: boolean;
	data?: T;
	error?: Error;
	attempts: number;
	totalTime: number;
}

/**
 * Default retry configuration
 */
export const DEFAULT_RETRY_CONFIG: RetryConfig = {
	maxAttempts: 3,
	baseDelay: 1000, // 1 second
	maxDelay: 10000, // 10 seconds
	backoffMultiplier: 2,
	retryableErrors: [
		'network',
		'timeout',
		'ECONNRESET',
		'ECONNREFUSED',
		'ENOTFOUND',
		'ETIMEDOUT',
		'fetch',
		'Failed to fetch',
	],
};

/**
 * Check if an error is retryable based on the configuration
 */
export function isRetryableError(error: Error, config: RetryConfig): boolean {
	const errorMessage = error.message.toLowerCase();
	return config.retryableErrors.some(retryableError =>
		errorMessage.includes(retryableError.toLowerCase())
	);
}

/**
 * Calculate delay for retry attempt with exponential backoff
 */
export function calculateRetryDelay(attempt: number, config: RetryConfig): number {
	const delay = config.baseDelay * Math.pow(config.backoffMultiplier, attempt - 1);
	return Math.min(delay, config.maxDelay);
}

/**
 * Sleep utility for async/await
 */
export function sleep(ms: number): Promise<void> {
	return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry a function with exponential backoff
 */
export async function retry<T>(
	fn: () => Promise<T>,
	config: Partial<RetryConfig> = {}
): Promise<RetryResult<T>> {
	const finalConfig = { ...DEFAULT_RETRY_CONFIG, ...config };
	const startTime = Date.now();
	let lastError: Error;

	for (let attempt = 1; attempt <= finalConfig.maxAttempts; attempt++) {
		try {
			const data = await fn();
			return {
				success: true,
				data,
				attempts: attempt,
				totalTime: Date.now() - startTime,
			};
		} catch (error) {
			lastError = error as Error;

			// Check if this is the last attempt
			if (attempt === finalConfig.maxAttempts) {
				if (finalConfig.onMaxAttemptsReached) {
					finalConfig.onMaxAttemptsReached(lastError);
				}
				return {
					success: false,
					error: lastError,
					attempts: attempt,
					totalTime: Date.now() - startTime,
				};
			}

			// Check if error is retryable
			if (!isRetryableError(lastError, finalConfig)) {
				return {
					success: false,
					error: lastError,
					attempts: attempt,
					totalTime: Date.now() - startTime,
				};
			}

			// Call onRetry callback
			if (finalConfig.onRetry) {
				finalConfig.onRetry(attempt, lastError);
			}

			// Wait before retrying
			const delay = calculateRetryDelay(attempt, finalConfig);
			await sleep(delay);
		}
	}

	// This should never be reached, but TypeScript requires it
	return {
		success: false,
		error: lastError!,
		attempts: finalConfig.maxAttempts,
		totalTime: Date.now() - startTime,
	};
}

/**
 * Retry configuration for different types of operations
 */
export const RETRY_CONFIGS = {
	// Quick retries for user interactions
	quick: {
		maxAttempts: 2,
		baseDelay: 500,
		maxDelay: 2000,
		backoffMultiplier: 1.5,
	},

	// Standard retries for most API calls
	standard: {
		maxAttempts: 3,
		baseDelay: 1000,
		maxDelay: 10000,
		backoffMultiplier: 2,
	},

	// Aggressive retries for critical operations
	aggressive: {
		maxAttempts: 5,
		baseDelay: 2000,
		maxDelay: 30000,
		backoffMultiplier: 2,
	},

	// Conservative retries for non-critical operations
	conservative: {
		maxAttempts: 2,
		baseDelay: 2000,
		maxDelay: 5000,
		backoffMultiplier: 1.5,
	},
} as const;

/**
 * Create a retry wrapper for API functions
 */
export function createRetryWrapper<T extends any[], R>(
	fn: (...args: T) => Promise<R>,
	config: Partial<RetryConfig> = {}
) {
	return async (...args: T): Promise<R> => {
		const result = await retry(() => fn(...args), config);

		if (!result.success) {
			throw result.error;
		}

		return result.data!;
	};
}

/**
 * Retry hook for React components
 */
export function useRetry() {
	const [isRetrying, setIsRetrying] = React.useState(false);
	const [retryCount, setRetryCount] = React.useState(0);

	const retryWithState = React.useCallback(async <T>(
		fn: () => Promise<T>,
		config: Partial<RetryConfig> = {}
	): Promise<T> => {
		setIsRetrying(true);
		setRetryCount(0);

		const result = await retry(fn, {
			...config,
			onRetry: (attempt, error) => {
				setRetryCount(attempt);
				config.onRetry?.(attempt, error);
			},
		});

		setIsRetrying(false);

		if (!result.success) {
			throw result.error;
		}

		return result.data!;
	}, []);

	return {
		retry: retryWithState,
		isRetrying,
		retryCount,
	};
}

/**
 * Retry configuration for specific error types
 */
export const ERROR_RETRY_CONFIGS = {
	network: {
		maxAttempts: 3,
		baseDelay: 1000,
		maxDelay: 10000,
		backoffMultiplier: 2,
		retryableErrors: ['network', 'fetch', 'Failed to fetch'],
	},

	timeout: {
		maxAttempts: 2,
		baseDelay: 2000,
		maxDelay: 8000,
		backoffMultiplier: 2,
		retryableErrors: ['timeout', 'ETIMEDOUT'],
	},

	server: {
		maxAttempts: 3,
		baseDelay: 1000,
		maxDelay: 15000,
		backoffMultiplier: 2,
		retryableErrors: ['500', '502', '503', '504'],
	},

	auth: {
		maxAttempts: 1, // Don't retry auth errors
		baseDelay: 0,
		maxDelay: 0,
		backoffMultiplier: 1,
		retryableErrors: [],
	},
} as const;

/**
 * Smart retry that chooses configuration based on error type
 */
export async function smartRetry<T>(
	fn: () => Promise<T>,
	baseConfig: Partial<RetryConfig> = {}
): Promise<RetryResult<T>> {
	try {
		return await retry(fn, baseConfig);
	} catch (error) {
		const errorMessage = (error as Error).message.toLowerCase();

		// Choose retry config based on error type
		let errorConfig: Partial<RetryConfig> = {};

		if (errorMessage.includes('network') || errorMessage.includes('fetch')) {
			errorConfig = ERROR_RETRY_CONFIGS.network;
		} else if (errorMessage.includes('timeout')) {
			errorConfig = ERROR_RETRY_CONFIGS.timeout;
		} else if (errorMessage.includes('500') || errorMessage.includes('502') || errorMessage.includes('503')) {
			errorConfig = ERROR_RETRY_CONFIGS.server;
		} else if (errorMessage.includes('401') || errorMessage.includes('403')) {
			errorConfig = ERROR_RETRY_CONFIGS.auth;
		}

		// Merge with base config
		const finalConfig = { ...baseConfig, ...errorConfig };

		return await retry(fn, finalConfig);
	}
}

/**
 * Retry with user notification
 */
export async function retryWithNotification<T>(
	fn: () => Promise<T>,
	config: Partial<RetryConfig> & {
		onRetryNotification?: (attempt: number, maxAttempts: number) => void;
		onErrorNotification?: (error: Error) => void;
	} = {}
): Promise<T> {
	const { onRetryNotification, onErrorNotification, ...retryConfig } = config;

	const result = await retry(fn, {
		...retryConfig,
		onRetry: (attempt, error) => {
			if (onRetryNotification) {
				onRetryNotification(attempt, retryConfig.maxAttempts || DEFAULT_RETRY_CONFIG.maxAttempts);
			}
			retryConfig.onRetry?.(attempt, error);
		},
		onMaxAttemptsReached: (error) => {
			if (onErrorNotification) {
				onErrorNotification(error);
			}
			retryConfig.onMaxAttemptsReached?.(error);
		},
	});

	if (!result.success) {
		throw result.error;
	}

	return result.data!;
}
