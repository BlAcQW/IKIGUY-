/**
 * Environment variable validation utility
 * Checks for required environment variables and provides helpful error messages
 */

interface EnvironmentConfig {
	SUPABASE_URL: string;
	SUPABASE_ANON_KEY: string;
	VAPI_PUBLIC_KEY: string;
	APP_ENV: string;
	DEBUG_MODE: boolean;
}

/**
 * Validates required environment variables
 * @throws Error if required variables are missing
 */
export function validateEnvironment(): EnvironmentConfig {
	const requiredVars = {
		SUPABASE_URL: import.meta.env.VITE_SUPABASE_URL,
		SUPABASE_ANON_KEY: import.meta.env.VITE_SUPABASE_ANON_KEY,
		VAPI_PUBLIC_KEY: import.meta.env.VITE_VAPI_PUBLIC_KEY,
	};

	const missingVars: string[] = [];

	// Check for missing required variables
	Object.entries(requiredVars).forEach(([key, value]) => {
		if (!value || value === 'undefined' || value === 'your_supabase_url_here' || value === 'your_vapi_public_key_here') {
			missingVars.push(`VITE_${key}`);
		}
	});

	if (missingVars.length > 0) {
		throw new Error(
			`Missing required environment variables: ${missingVars.join(', ')}\n` +
			'Please check your .env file and ensure all required variables are set.'
		);
	}

	return {
		SUPABASE_URL: requiredVars.SUPABASE_URL,
		SUPABASE_ANON_KEY: requiredVars.SUPABASE_ANON_KEY,
		VAPI_PUBLIC_KEY: requiredVars.VAPI_PUBLIC_KEY,
		APP_ENV: import.meta.env.VITE_APP_ENV || 'development',
		DEBUG_MODE: import.meta.env.VITE_DEBUG_MODE === 'true',
	};
}

/**
 * Get environment configuration with validation
 * @returns EnvironmentConfig object
 */
export function getEnvironmentConfig(): EnvironmentConfig {
	try {
		return validateEnvironment();
	} catch (error) {
		console.error('Environment validation failed:', error);

		// In development, show helpful error message
		if (import.meta.env.DEV) {
			console.error(`
🚨 Environment Configuration Error 🚨

Please ensure you have a .env file with the following variables:

VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_VAPI_PUBLIC_KEY=your_vapi_public_key

Copy .env.example to .env and fill in your actual values.
      `);
		}

		throw error;
	}
}

/**
 * Check if we're in development mode
 */
export const isDevelopment = import.meta.env.DEV;

/**
 * Check if we're in production mode
 */
export const isProduction = import.meta.env.PROD;

/**
 * Get the current environment
 */
export const getEnvironment = (): string => {
	return import.meta.env.VITE_APP_ENV || (isProduction ? 'production' : 'development');
};
