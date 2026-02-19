import { z } from 'zod';

// Input validation schemas
export const emailSchema = z.string().email('Invalid email address');
export const passwordSchema = z.string().min(8, 'Password must be at least 8 characters')
	.regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'Password must contain at least one uppercase letter, one lowercase letter, and one number');

export const urlSchema = z.string().url('Invalid URL format');
export const phoneSchema = z.string().regex(/^\+?[\d\s\-()]+$/, 'Invalid phone number format');

// Rate limiting configuration
export interface RateLimitConfig {
	windowMs: number; // Time window in milliseconds
	maxRequests: number; // Maximum requests per window
	message: string;
}

export const defaultRateLimits: Record<string, RateLimitConfig> = {
	auth: { windowMs: 15 * 60 * 1000, maxRequests: 5, message: 'Too many authentication attempts' },
	api: { windowMs: 60 * 1000, maxRequests: 100, message: 'Too many API requests' },
	upload: { windowMs: 60 * 1000, maxRequests: 10, message: 'Too many upload attempts' },
};

// Rate limiting store (in production, use Redis or similar)
const rateLimitStore = new Map<string, { count: number; resetTime: number }>();

export class RateLimiter {
	static checkLimit(key: string, config: RateLimitConfig): { allowed: boolean; remaining: number; resetTime: number } {
		const now = Date.now();
		const record = rateLimitStore.get(key);

		if (!record || now > record.resetTime) {
			// Reset or create new record
			rateLimitStore.set(key, { count: 1, resetTime: now + config.windowMs });
			return { allowed: true, remaining: config.maxRequests - 1, resetTime: now + config.windowMs };
		}

		if (record.count >= config.maxRequests) {
			return { allowed: false, remaining: 0, resetTime: record.resetTime };
		}

		record.count++;
		return { allowed: true, remaining: config.maxRequests - record.count, resetTime: record.resetTime };
	}

	static resetLimit(key: string): void {
		rateLimitStore.delete(key);
	}
}

// Input sanitization
export class InputSanitizer {
	static sanitizeString(input: string): string {
		return input
			.trim()
			.replace(/[<>]/g, '') // Remove potential HTML tags
			.replace(/javascript:/gi, '') // Remove javascript: protocol
			.replace(/on\w+=/gi, '') // Remove event handlers
			.substring(0, 1000); // Limit length
	}

	static sanitizeHTML(input: string): string {
		return input
			.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '') // Remove script tags
			.replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '') // Remove iframe tags
			.replace(/javascript:/gi, '') // Remove javascript: protocol
			.replace(/on\w+=/gi, ''); // Remove event handlers
	}

	static sanitizeSQL(input: string): string {
		// Basic SQL injection prevention (use parameterized queries in production)
                const sqlKeywords = [
                        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
                        'UNION', 'EXEC', 'EXECUTE', 'SCRIPT', '--', '/\\*', '\\*/', ';'
                ];

                let sanitized = input;
                sqlKeywords.forEach(keyword => {
                        const regex = new RegExp(keyword, 'gi');
                        sanitized = sanitized.replace(regex, '');
                });

		return sanitized;
	}

	static sanitizeFilename(filename: string): string {
		return filename
			.replace(/[^a-zA-Z0-9._-]/g, '') // Remove special characters
			.replace(/\.\./g, '') // Remove path traversal
			.substring(0, 255); // Limit length
	}
}

// CSRF protection
export class CSRFProtection {
	private static tokens = new Map<string, { token: string; expires: number }>();

	static generateToken(sessionId: string): string {
		const token = this.generateRandomToken();
		const expires = Date.now() + (30 * 60 * 1000); // 30 minutes

		this.tokens.set(sessionId, { token, expires });
		return token;
	}

	static validateToken(sessionId: string, token: string): boolean {
		const record = this.tokens.get(sessionId);

		if (!record || Date.now() > record.expires) {
			this.tokens.delete(sessionId);
			return false;
		}

		return record.token === token;
	}

	static removeToken(sessionId: string): void {
		this.tokens.delete(sessionId);
	}

	private static generateRandomToken(): string {
		const array = new Uint8Array(32);
		crypto.getRandomValues(array);
		return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
	}
}

// XSS protection
export class XSSProtection {
	static encodeHTML(input: string): string {
		const div = document.createElement('div');
		div.textContent = input;
		return div.innerHTML;
	}

	static encodeAttribute(input: string): string {
		return input
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;')
			.replace(/'/g, '&#x27;');
	}

	static encodeURL(input: string): string {
		return encodeURIComponent(input);
	}

	static validateContentSecurityPolicy(script: string): boolean {
		// Basic CSP validation (in production, use a proper CSP parser)
		const dangerousPatterns = [
			/eval\s*\(/i,
			/Function\s*\(/i,
			/setTimeout\s*\(/i,
			/setInterval\s*\(/i,
			/new\s+Function/i,
		];

		return !dangerousPatterns.some(pattern => pattern.test(script));
	}
}

// Password security
export class PasswordSecurity {
	static hashPassword(password: string): Promise<string> {
		// In production, use bcrypt or similar
		return crypto.subtle.digest('SHA-256', new TextEncoder().encode(password))
			.then(hash => Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, '0')).join(''));
	}

	static validatePasswordStrength(password: string): {
		isValid: boolean;
		score: number;
		feedback: string[];
	} {
		const feedback: string[] = [];
		let score = 0;

		if (password.length >= 8) score += 1;
		else feedback.push('Password must be at least 8 characters long');

		if (/[a-z]/.test(password)) score += 1;
		else feedback.push('Password must contain at least one lowercase letter');

		if (/[A-Z]/.test(password)) score += 1;
		else feedback.push('Password must contain at least one uppercase letter');

		if (/\d/.test(password)) score += 1;
		else feedback.push('Password must contain at least one number');

		if (/[^A-Za-z0-9]/.test(password)) score += 1;
		else feedback.push('Password should contain at least one special character');

		if (password.length >= 12) score += 1;
		else feedback.push('Consider using a longer password for better security');

		return {
			isValid: score >= 4,
			score: Math.min(score, 5),
			feedback: feedback.length > 0 ? feedback : ['Password strength is good']
		};
	}

	static generateSecurePassword(length: number = 16): string {
		const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*';
		let password = '';

		// Ensure at least one character from each category
		password += 'abcdefghijklmnopqrstuvwxyz'[Math.floor(Math.random() * 26)];
		password += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[Math.floor(Math.random() * 26)];
		password += '0123456789'[Math.floor(Math.random() * 10)];
		password += '!@#$%^&*'[Math.floor(Math.random() * 8)];

		// Fill the rest randomly
		for (let i = 4; i < length; i++) {
			password += charset[Math.floor(Math.random() * charset.length)];
		}

		// Shuffle the password
		return password.split('').sort(() => Math.random() - 0.5).join('');
	}
}

// Session security
export class SessionSecurity {
	static generateSessionId(): string {
		const array = new Uint8Array(32);
		crypto.getRandomValues(array);
		return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
	}

	static validateSession(sessionId: string): boolean {
		// Basic session validation (in production, validate against database)
		return /^[a-f0-9]{64}$/.test(sessionId);
	}

	static isSessionExpired(createdAt: number, maxAge: number = 24 * 60 * 60 * 1000): boolean {
		return Date.now() - createdAt > maxAge;
	}
}

// API security
export class APISecurity {
	static validateAPIKey(apiKey: string): boolean {
		// Basic API key validation (in production, validate against database)
		return /^[a-zA-Z0-9]{32,64}$/.test(apiKey);
	}

	static generateAPIKey(): string {
		const array = new Uint8Array(32);
		crypto.getRandomValues(array);
		return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
	}

	static validateOrigin(origin: string, allowedOrigins: string[]): boolean {
		return allowedOrigins.includes(origin) || allowedOrigins.includes('*');
	}

	static validateContentType(contentType: string, allowedTypes: string[]): boolean {
		return allowedTypes.some(type => contentType.startsWith(type));
	}
}

// Security headers
export const securityHeaders = {
	'X-Content-Type-Options': 'nosniff',
	'X-Frame-Options': 'DENY',
	'X-XSS-Protection': '1; mode=block',
	'Referrer-Policy': 'strict-origin-when-cross-origin',
	'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
	'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; frame-ancestors 'none';",
};

// Security utilities
export const SecurityUtils = {
        // Validate and sanitize user input
        validateInput: (input: unknown, schema: z.ZodSchema): { isValid: boolean; data?: unknown; errors?: string[] } => {
		try {
			const data = schema.parse(input);
			return { isValid: true, data };
		} catch (error) {
			if (error instanceof z.ZodError) {
				return { isValid: false, errors: error.errors.map(e => e.message) };
			}
			return { isValid: false, errors: ['Validation failed'] };
		}
	},

	// Check if request is from a bot
	isBot: (userAgent: string): boolean => {
		const botPatterns = [
			/bot/i, /crawler/i, /spider/i, /scraper/i, /curl/i, /wget/i,
			/python/i, /java/i, /perl/i, /ruby/i, /php/i
		];
		return botPatterns.some(pattern => pattern.test(userAgent));
	},

	// Validate file upload
	validateFileUpload: (file: File, allowedTypes: string[], maxSize: number): { isValid: boolean; error?: string } => {
		if (!allowedTypes.includes(file.type)) {
			return { isValid: false, error: 'File type not allowed' };
		}

		if (file.size > maxSize) {
			return { isValid: false, error: 'File too large' };
		}

		return { isValid: true };
	},

	// Generate secure random string
	generateSecureRandom: (length: number = 32): string => {
		const array = new Uint8Array(length);
		crypto.getRandomValues(array);
		return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
	},

	// Check if string contains malicious content
	containsMaliciousContent: (input: string): boolean => {
		const maliciousPatterns = [
			/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
			/javascript:/gi,
			/on\w+=/gi,
			/data:text\/html/gi,
			/vbscript:/gi,
			/expression\s*\(/gi,
		];

		return maliciousPatterns.some(pattern => pattern.test(input));
	}
};

export default {
	RateLimiter,
	InputSanitizer,
	CSRFProtection,
	XSSProtection,
	PasswordSecurity,
	SessionSecurity,
	APISecurity,
	SecurityUtils,
	securityHeaders,
	emailSchema,
	passwordSchema,
	urlSchema,
	phoneSchema,
};
