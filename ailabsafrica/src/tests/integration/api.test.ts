import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { createClient } from '@supabase/supabase-js';
import { vi } from 'vitest';

// Import the actual Supabase client configuration
import { supabase } from '@/integrations/supabase/client';

// Test configuration
const TEST_TIMEOUT = 30000; // 30 seconds for API calls

describe('API Integration Tests', () => {
	let testUserId: string;
	let testAssistantId: string;
	let testDemoId: string;

	beforeAll(async () => {
		// Set up test environment
		console.log('Setting up integration test environment...');

		// Create a test user for integration tests
		const { data: authData, error: authError } = await supabase.auth.signUp({
			email: 'integration-test@example.com',
			password: 'testpassword123',
		});

		if (authError) {
			console.error('Failed to create test user:', authError);
			throw authError;
		}

		testUserId = authData.user?.id || '';
		console.log('Test user created:', testUserId);
	}, TEST_TIMEOUT);

	afterAll(async () => {
		// Clean up test data
		console.log('Cleaning up integration test environment...');

		if (testUserId) {
			// Delete test user and associated data
			const { error } = await supabase.auth.admin.deleteUser(testUserId);
			if (error) {
				console.error('Failed to delete test user:', error);
			}
		}
	}, TEST_TIMEOUT);

	describe('Contact Form API', () => {
		it('should submit contact form successfully', async () => {
			const contactData = {
				name: 'Integration Test User',
				email: 'integration-test@example.com',
				company: 'Test Company',
				phone: '+233 54 123 4567',
				subject: 'Integration Test Subject',
				message: 'This is a test message from integration tests'
			};

			const { data, error } = await supabase.functions.invoke('contact-form', {
				body: contactData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.success).toBe(true);
		}, TEST_TIMEOUT);

		it('should handle invalid contact form data', async () => {
			const invalidData = {
				name: '', // Missing required field
				email: 'invalid-email',
				subject: '',
				message: ''
			};

			const { data, error } = await supabase.functions.invoke('contact-form', {
				body: invalidData
			});

			// Should return an error for invalid data
			expect(data?.success).toBe(false);
			expect(data?.error).toBeDefined();
		}, TEST_TIMEOUT);
	});

	describe('Demo Notification API', () => {
		it('should send demo notification successfully', async () => {
			const demoData = {
				fullName: 'Integration Test User',
				companyName: 'Test Company',
				email: 'integration-test@example.com',
				phone: '+233 54 123 4567',
				preferredDate: '2024-12-25',
				preferredTime: '14:30',
				timezone: 'UTC',
				demoType: 'general',
				notes: 'Integration test demo request'
			};

			const { data, error } = await supabase.functions.invoke('send-demo-notification', {
				body: demoData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
		}, TEST_TIMEOUT);
	});

	describe('Password Reset API', () => {
		it('should initiate password reset process', async () => {
			const resetData = {
				email: 'integration-test@example.com'
			};

			const { data, error } = await supabase.functions.invoke('password-reset', {
				body: resetData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
		}, TEST_TIMEOUT);

		it('should handle non-existent email for password reset', async () => {
			const resetData = {
				email: 'nonexistent@example.com'
			};

			const { data, error } = await supabase.functions.invoke('password-reset', {
				body: resetData
			});

			// Should handle gracefully even if email doesn't exist
			expect(error).toBeNull();
			expect(data).toBeDefined();
		}, TEST_TIMEOUT);
	});

	describe('Email Verification API', () => {
		it('should handle email verification request', async () => {
			const verificationData = {
				email: 'integration-test@example.com',
				token: 'test-verification-token'
			};

			const { data, error } = await supabase.functions.invoke('email-verification', {
				body: verificationData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
		}, TEST_TIMEOUT);
	});

	describe('VAPI Voices API', () => {
		it('should list available VAPI voices', async () => {
			const { data, error } = await supabase.functions.invoke('list-vapi-voices', {
				body: {}
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(Array.isArray(data.voices)).toBe(true);
			expect(data.voices.length).toBeGreaterThan(0);
		}, TEST_TIMEOUT);
	});

	describe('Custom Demos API', () => {
		it('should list custom demos', async () => {
			const { data, error } = await supabase.functions.invoke('list-custom-demos', {
				body: {
					userId: testUserId
				}
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(Array.isArray(data.demos)).toBe(true);
		}, TEST_TIMEOUT);
	});

	describe('Site Information Extraction API', () => {
		it('should extract site information from URL', async () => {
			const siteData = {
				url: 'https://example.com'
			};

			const { data, error } = await supabase.functions.invoke('extract-site-info', {
				body: siteData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.siteInfo).toBeDefined();
		}, TEST_TIMEOUT);

		it('should handle invalid URL', async () => {
			const siteData = {
				url: 'invalid-url'
			};

			const { data, error } = await supabase.functions.invoke('extract-site-info', {
				body: siteData
			});

			// Should handle invalid URL gracefully
			expect(data?.error).toBeDefined();
		}, TEST_TIMEOUT);
	});

	describe('Demo HTML Generation API', () => {
		it('should generate demo HTML', async () => {
			const demoData = {
				title: 'Integration Test Demo',
				description: 'Test demo description',
				features: ['Feature 1', 'Feature 2'],
				customizations: {
					theme: 'light',
					language: 'en'
				}
			};

			const { data, error } = await supabase.functions.invoke('generate-demo-html', {
				body: demoData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.html).toBeDefined();
			expect(typeof data.html).toBe('string');
		}, TEST_TIMEOUT);
	});

	describe('Assistant Management API', () => {
		beforeEach(async () => {
			// Create a test assistant for each test
			const assistantData = {
				name: 'Integration Test Assistant',
				description: 'Test assistant for integration tests',
				voiceId: 'test-voice-id',
				instructions: 'Test instructions',
				userId: testUserId
			};

			const { data, error } = await supabase.functions.invoke('create-assistant', {
				body: assistantData
			});

			if (error) {
				console.error('Failed to create test assistant:', error);
				throw error;
			}

			testAssistantId = data.assistantId;
		});

		afterEach(async () => {
			// Clean up test assistant
			if (testAssistantId) {
				await supabase.functions.invoke('manage-assistant', {
					body: {
						action: 'delete',
						assistantId: testAssistantId
					}
				});
			}
		});

		it('should create assistant successfully', async () => {
			const assistantData = {
				name: 'Test Assistant Creation',
				description: 'Test assistant description',
				voiceId: 'test-voice-id',
				instructions: 'Test instructions',
				userId: testUserId
			};

			const { data, error } = await supabase.functions.invoke('create-assistant', {
				body: assistantData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.assistantId).toBeDefined();
			expect(typeof data.assistantId).toBe('string');
		}, TEST_TIMEOUT);

		it('should manage assistant (update)', async () => {
			const updateData = {
				action: 'update',
				assistantId: testAssistantId,
				updates: {
					name: 'Updated Test Assistant',
					description: 'Updated description'
				}
			};

			const { data, error } = await supabase.functions.invoke('manage-assistant', {
				body: updateData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.success).toBe(true);
		}, TEST_TIMEOUT);

		it('should clone assistant', async () => {
			const cloneData = {
				assistantId: testAssistantId,
				newName: 'Cloned Test Assistant',
				userId: testUserId
			};

			const { data, error } = await supabase.functions.invoke('clone-assistant', {
				body: cloneData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.clonedAssistantId).toBeDefined();
		}, TEST_TIMEOUT);
	});

	describe('Analytics API', () => {
		it('should track demo analytics', async () => {
			const analyticsData = {
				demoId: 'test-demo-id',
				userId: testUserId,
				event: 'demo_viewed',
				metadata: {
					duration: 120,
					source: 'integration_test'
				}
			};

			const { data, error } = await supabase.functions.invoke('track-demo-analytics', {
				body: analyticsData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.success).toBe(true);
		}, TEST_TIMEOUT);

		it('should export analytics data', async () => {
			const exportData = {
				userId: testUserId,
				dateRange: {
					start: '2024-01-01',
					end: '2024-12-31'
				},
				format: 'csv'
			};

			const { data, error } = await supabase.functions.invoke('export-analytics', {
				body: exportData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.exportUrl).toBeDefined();
		}, TEST_TIMEOUT);
	});

	describe('Payment Processing API', () => {
		it('should process payment successfully', async () => {
			const paymentData = {
				amount: 1000, // $10.00 in cents
				currency: 'usd',
				paymentMethod: 'card',
				description: 'Integration test payment',
				userId: testUserId
			};

			const { data, error } = await supabase.functions.invoke('process-payment', {
				body: paymentData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.paymentId).toBeDefined();
		}, TEST_TIMEOUT);

		it('should verify payment', async () => {
			const paymentId = 'test-payment-id';

			const { data, error } = await supabase.functions.invoke('verify-payment', {
				body: { paymentId }
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
		}, TEST_TIMEOUT);

		it('should process refund', async () => {
			const refundData = {
				paymentId: 'test-payment-id',
				amount: 500, // $5.00 refund
				reason: 'Integration test refund'
			};

			const { data, error } = await supabase.functions.invoke('process-refund', {
				body: refundData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
		}, TEST_TIMEOUT);
	});

	describe('Invoice Generation API', () => {
		it('should generate invoice', async () => {
			const invoiceData = {
				userId: testUserId,
				items: [
					{
						description: 'Test Service',
						amount: 1000,
						quantity: 1
					}
				],
				customerInfo: {
					name: 'Test Customer',
					email: 'test@example.com'
				}
			};

			const { data, error } = await supabase.functions.invoke('generate-invoice', {
				body: invoiceData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.invoiceUrl).toBeDefined();
		}, TEST_TIMEOUT);
	});

	describe('Two-Factor Authentication API', () => {
		it('should setup two-factor authentication', async () => {
			const setupData = {
				userId: testUserId
			};

			const { data, error } = await supabase.functions.invoke('setup-two-factor', {
				body: setupData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.qrCode).toBeDefined();
			expect(data.secret).toBeDefined();
		}, TEST_TIMEOUT);

		it('should verify two-factor code', async () => {
			const verifyData = {
				userId: testUserId,
				code: '123456'
			};

			const { data, error } = await supabase.functions.invoke('verify-two-factor', {
				body: verifyData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
		}, TEST_TIMEOUT);

		it('should generate backup codes', async () => {
			const backupData = {
				userId: testUserId
			};

			const { data, error } = await supabase.functions.invoke('generate-backup-codes', {
				body: backupData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(Array.isArray(data.backupCodes)).toBe(true);
			expect(data.backupCodes.length).toBeGreaterThan(0);
		}, TEST_TIMEOUT);

		it('should disable two-factor authentication', async () => {
			const disableData = {
				userId: testUserId
			};

			const { data, error } = await supabase.functions.invoke('disable-two-factor', {
				body: disableData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.success).toBe(true);
		}, TEST_TIMEOUT);
	});

	describe('Demo Comments API', () => {
		beforeEach(async () => {
			// Create a test demo for comments
			testDemoId = 'test-demo-id';
		});

		it('should add comment to demo', async () => {
			const commentData = {
				demoId: testDemoId,
				userId: testUserId,
				comment: 'Integration test comment',
				rating: 5
			};

			const { data, error } = await supabase.functions.invoke('demo-comments', {
				body: {
					action: 'add',
					...commentData
				}
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.commentId).toBeDefined();
		}, TEST_TIMEOUT);

		it('should get comments for demo', async () => {
			const { data, error } = await supabase.functions.invoke('demo-comments', {
				body: {
					action: 'get',
					demoId: testDemoId
				}
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(Array.isArray(data.comments)).toBe(true);
		}, TEST_TIMEOUT);
	});

	describe('Demo Versioning API', () => {
		it('should create demo version', async () => {
			const versionData = {
				demoId: testDemoId,
				userId: testUserId,
				version: '1.1.0',
				changes: 'Integration test changes'
			};

			const { data, error } = await supabase.functions.invoke('demo-versioning', {
				body: {
					action: 'create',
					...versionData
				}
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.versionId).toBeDefined();
		}, TEST_TIMEOUT);

		it('should get demo versions', async () => {
			const { data, error } = await supabase.functions.invoke('demo-versioning', {
				body: {
					action: 'list',
					demoId: testDemoId
				}
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(Array.isArray(data.versions)).toBe(true);
		}, TEST_TIMEOUT);
	});

	describe('CDN Management API', () => {
		it('should manage CDN assets', async () => {
			const cdnData = {
				action: 'upload',
				fileName: 'test-asset.jpg',
				fileType: 'image/jpeg',
				userId: testUserId
			};

			const { data, error } = await supabase.functions.invoke('cdn-management', {
				body: cdnData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
		}, TEST_TIMEOUT);
	});

	describe('Image Optimization API', () => {
		it('should optimize image', async () => {
			const imageData = {
				imageUrl: 'https://example.com/test-image.jpg',
				options: {
					width: 800,
					quality: 80,
					format: 'webp'
				}
			};

			const { data, error } = await supabase.functions.invoke('optimize-image', {
				body: imageData
			});

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.optimizedUrl).toBeDefined();
		}, TEST_TIMEOUT);
	});

	describe('Error Handling', () => {
		it('should handle API errors gracefully', async () => {
			const invalidData = {
				// Missing required fields
			};

			const { data, error } = await supabase.functions.invoke('contact-form', {
				body: invalidData
			});

			// Should return error response instead of throwing
			expect(data?.success).toBe(false);
			expect(data?.error).toBeDefined();
		}, TEST_TIMEOUT);

		it('should handle network errors', async () => {
			// Test with invalid function name to simulate network error
			const { data, error } = await supabase.functions.invoke('non-existent-function', {
				body: {}
			});

			// Should handle gracefully
			expect(error).toBeDefined();
		}, TEST_TIMEOUT);
	});

	describe('Performance Tests', () => {
		it('should respond within acceptable time limits', async () => {
			const startTime = Date.now();

			const { data, error } = await supabase.functions.invoke('list-vapi-voices', {
				body: {}
			});

			const endTime = Date.now();
			const responseTime = endTime - startTime;

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(responseTime).toBeLessThan(5000); // Should respond within 5 seconds
		}, TEST_TIMEOUT);

		it('should handle concurrent requests', async () => {
			const promises = Array(5).fill(null).map(() =>
				supabase.functions.invoke('list-vapi-voices', { body: {} })
			);

			const results = await Promise.all(promises);

			results.forEach(({ data, error }) => {
				expect(error).toBeNull();
				expect(data).toBeDefined();
			});
		}, TEST_TIMEOUT);
	});
});
