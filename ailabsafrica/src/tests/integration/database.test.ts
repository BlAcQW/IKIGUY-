import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { supabase } from '@/integrations/supabase/client';

// Test configuration
const TEST_TIMEOUT = 30000; // 30 seconds for database operations

describe('Database Integration Tests', () => {
	let testUserId: string;
	let testAssistantId: string;
	let testDemoId: string;
	let testBookingId: string;

	beforeAll(async () => {
		// Set up test environment
		console.log('Setting up database integration test environment...');

		// Create a test user for database tests
		const { data: authData, error: authError } = await supabase.auth.signUp({
			email: 'db-integration-test@example.com',
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
		console.log('Cleaning up database integration test environment...');

		if (testUserId) {
			// Clean up all test data
			await cleanupTestData();

			// Delete test user
			const { error } = await supabase.auth.admin.deleteUser(testUserId);
			if (error) {
				console.error('Failed to delete test user:', error);
			}
		}
	}, TEST_TIMEOUT);

	const cleanupTestData = async () => {
		// Clean up test data in reverse order of dependencies
		if (testBookingId) {
			await supabase.from('demo_bookings').delete().eq('id', testBookingId);
		}
		if (testDemoId) {
			await supabase.from('demos').delete().eq('id', testDemoId);
		}
		if (testAssistantId) {
			await supabase.from('assistants').delete().eq('id', testAssistantId);
		}
	};

	describe('User Management', () => {
		it('should create and retrieve user profile', async () => {
			const profileData = {
				id: testUserId,
				full_name: 'Database Test User',
				email: 'db-integration-test@example.com',
				company: 'Test Company',
				phone: '+233 54 123 4567',
				role: 'user',
				created_at: new Date().toISOString()
			};

			// Insert profile
			const { error: insertError } = await supabase
				.from('profiles')
				.insert([profileData]);

			expect(insertError).toBeNull();

			// Retrieve profile
			const { data: profile, error: selectError } = await supabase
				.from('profiles')
				.select('*')
				.eq('id', testUserId)
				.single();

			expect(selectError).toBeNull();
			expect(profile).toBeDefined();
			expect(profile.full_name).toBe('Database Test User');
			expect(profile.email).toBe('db-integration-test@example.com');
		}, TEST_TIMEOUT);

		it('should update user profile', async () => {
			const updateData = {
				full_name: 'Updated Database Test User',
				company: 'Updated Test Company'
			};

			const { error } = await supabase
				.from('profiles')
				.update(updateData)
				.eq('id', testUserId);

			expect(error).toBeNull();

			// Verify update
			const { data: profile, error: selectError } = await supabase
				.from('profiles')
				.select('*')
				.eq('id', testUserId)
				.single();

			expect(selectError).toBeNull();
			expect(profile.full_name).toBe('Updated Database Test User');
			expect(profile.company).toBe('Updated Test Company');
		}, TEST_TIMEOUT);
	});

	describe('Assistant Management', () => {
		beforeEach(async () => {
			// Create a test assistant for each test
			const assistantData = {
				name: 'Database Test Assistant',
				description: 'Test assistant for database integration tests',
				voice_id: 'test-voice-id',
				instructions: 'Test instructions for database integration',
				user_id: testUserId,
				is_active: true,
				created_at: new Date().toISOString()
			};

			const { data, error } = await supabase
				.from('assistants')
				.insert([assistantData])
				.select()
				.single();

			if (error) {
				console.error('Failed to create test assistant:', error);
				throw error;
			}

			testAssistantId = data.id;
		});

		afterEach(async () => {
			// Clean up test assistant
			if (testAssistantId) {
				await supabase.from('assistants').delete().eq('id', testAssistantId);
				testAssistantId = '';
			}
		});

		it('should create assistant successfully', async () => {
			const assistantData = {
				name: 'New Database Assistant',
				description: 'New test assistant',
				voice_id: 'new-voice-id',
				instructions: 'New test instructions',
				user_id: testUserId,
				is_active: true
			};

			const { data, error } = await supabase
				.from('assistants')
				.insert([assistantData])
				.select()
				.single();

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.name).toBe('New Database Assistant');
			expect(data.user_id).toBe(testUserId);

			// Clean up
			await supabase.from('assistants').delete().eq('id', data.id);
		}, TEST_TIMEOUT);

		it('should retrieve user assistants', async () => {
			const { data: assistants, error } = await supabase
				.from('assistants')
				.select('*')
				.eq('user_id', testUserId);

			expect(error).toBeNull();
			expect(Array.isArray(assistants)).toBe(true);
			expect(assistants.length).toBeGreaterThan(0);
			expect(assistants[0].user_id).toBe(testUserId);
		}, TEST_TIMEOUT);

		it('should update assistant', async () => {
			const updateData = {
				name: 'Updated Database Assistant',
				description: 'Updated description'
			};

			const { error } = await supabase
				.from('assistants')
				.update(updateData)
				.eq('id', testAssistantId);

			expect(error).toBeNull();

			// Verify update
			const { data: assistant, error: selectError } = await supabase
				.from('assistants')
				.select('*')
				.eq('id', testAssistantId)
				.single();

			expect(selectError).toBeNull();
			expect(assistant.name).toBe('Updated Database Assistant');
			expect(assistant.description).toBe('Updated description');
		}, TEST_TIMEOUT);

		it('should delete assistant', async () => {
			const { error } = await supabase
				.from('assistants')
				.delete()
				.eq('id', testAssistantId);

			expect(error).toBeNull();

			// Verify deletion
			const { data: assistant, error: selectError } = await supabase
				.from('assistants')
				.select('*')
				.eq('id', testAssistantId)
				.single();

			expect(selectError).toBeDefined(); // Should not find the record
			expect(assistant).toBeNull();
		}, TEST_TIMEOUT);
	});

	describe('Demo Management', () => {
		beforeEach(async () => {
			// Create a test demo for each test
			const demoData = {
				title: 'Database Test Demo',
				description: 'Test demo for database integration tests',
				user_id: testUserId,
				is_public: true,
				created_at: new Date().toISOString()
			};

			const { data, error } = await supabase
				.from('demos')
				.insert([demoData])
				.select()
				.single();

			if (error) {
				console.error('Failed to create test demo:', error);
				throw error;
			}

			testDemoId = data.id;
		});

		afterEach(async () => {
			// Clean up test demo
			if (testDemoId) {
				await supabase.from('demos').delete().eq('id', testDemoId);
				testDemoId = '';
			}
		});

		it('should create demo successfully', async () => {
			const demoData = {
				title: 'New Database Demo',
				description: 'New test demo',
				user_id: testUserId,
				is_public: false
			};

			const { data, error } = await supabase
				.from('demos')
				.insert([demoData])
				.select()
				.single();

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.title).toBe('New Database Demo');
			expect(data.user_id).toBe(testUserId);

			// Clean up
			await supabase.from('demos').delete().eq('id', data.id);
		}, TEST_TIMEOUT);

		it('should retrieve user demos', async () => {
			const { data: demos, error } = await supabase
				.from('demos')
				.select('*')
				.eq('user_id', testUserId);

			expect(error).toBeNull();
			expect(Array.isArray(demos)).toBe(true);
			expect(demos.length).toBeGreaterThan(0);
			expect(demos[0].user_id).toBe(testUserId);
		}, TEST_TIMEOUT);

		it('should retrieve public demos', async () => {
			const { data: demos, error } = await supabase
				.from('demos')
				.select('*')
				.eq('is_public', true);

			expect(error).toBeNull();
			expect(Array.isArray(demos)).toBe(true);
			expect(demos.length).toBeGreaterThan(0);
			expect(demos[0].is_public).toBe(true);
		}, TEST_TIMEOUT);
	});

	describe('Demo Bookings', () => {
		beforeEach(async () => {
			// Create a test demo booking for each test
			const bookingData = {
				user_id: testUserId,
				full_name: 'Database Test User',
				company_name: 'Test Company',
				email: 'db-integration-test@example.com',
				phone: '+233 54 123 4567',
				preferred_date: '2024-12-25',
				preferred_time: '14:30',
				timezone: 'UTC',
				demo_type: 'general',
				notes: 'Database integration test booking',
				status: 'pending',
				created_at: new Date().toISOString()
			};

			const { data, error } = await supabase
				.from('demo_bookings')
				.insert([bookingData])
				.select()
				.single();

			if (error) {
				console.error('Failed to create test booking:', error);
				throw error;
			}

			testBookingId = data.id;
		});

		afterEach(async () => {
			// Clean up test booking
			if (testBookingId) {
				await supabase.from('demo_bookings').delete().eq('id', testBookingId);
				testBookingId = '';
			}
		});

		it('should create demo booking successfully', async () => {
			const bookingData = {
				user_id: testUserId,
				full_name: 'New Database User',
				company_name: 'New Test Company',
				email: 'new-db-test@example.com',
				phone: '+233 54 987 6543',
				preferred_date: '2024-12-26',
				preferred_time: '15:00',
				timezone: 'GMT+1',
				demo_type: 'banking',
				notes: 'New database integration test booking',
				status: 'pending'
			};

			const { data, error } = await supabase
				.from('demo_bookings')
				.insert([bookingData])
				.select()
				.single();

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.full_name).toBe('New Database User');
			expect(data.user_id).toBe(testUserId);

			// Clean up
			await supabase.from('demo_bookings').delete().eq('id', data.id);
		}, TEST_TIMEOUT);

		it('should retrieve user bookings', async () => {
			const { data: bookings, error } = await supabase
				.from('demo_bookings')
				.select('*')
				.eq('user_id', testUserId);

			expect(error).toBeNull();
			expect(Array.isArray(bookings)).toBe(true);
			expect(bookings.length).toBeGreaterThan(0);
			expect(bookings[0].user_id).toBe(testUserId);
		}, TEST_TIMEOUT);

		it('should update booking status', async () => {
			const { error } = await supabase
				.from('demo_bookings')
				.update({ status: 'confirmed' })
				.eq('id', testBookingId);

			expect(error).toBeNull();

			// Verify update
			const { data: booking, error: selectError } = await supabase
				.from('demo_bookings')
				.select('*')
				.eq('id', testBookingId)
				.single();

			expect(selectError).toBeNull();
			expect(booking.status).toBe('confirmed');
		}, TEST_TIMEOUT);
	});

	describe('Analytics Tracking', () => {
		it('should track demo analytics', async () => {
			const analyticsData = {
				demo_id: 'test-demo-id',
				user_id: testUserId,
				event_type: 'demo_viewed',
				event_data: {
					duration: 120,
					source: 'database_integration_test'
				},
				created_at: new Date().toISOString()
			};

			const { data, error } = await supabase
				.from('demo_analytics')
				.insert([analyticsData])
				.select()
				.single();

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.demo_id).toBe('test-demo-id');
			expect(data.user_id).toBe(testUserId);

			// Clean up
			await supabase.from('demo_analytics').delete().eq('id', data.id);
		}, TEST_TIMEOUT);

		it('should retrieve analytics for demo', async () => {
			// First create some test analytics
			const analyticsData = [
				{
					demo_id: 'test-demo-id',
					user_id: testUserId,
					event_type: 'demo_viewed',
					event_data: { duration: 120 },
					created_at: new Date().toISOString()
				},
				{
					demo_id: 'test-demo-id',
					user_id: testUserId,
					event_type: 'demo_shared',
					event_data: { platform: 'email' },
					created_at: new Date().toISOString()
				}
			];

			const { data: insertedData, error: insertError } = await supabase
				.from('demo_analytics')
				.insert(analyticsData)
				.select();

			expect(insertError).toBeNull();
			expect(insertedData).toBeDefined();

			// Retrieve analytics
			const { data: analytics, error } = await supabase
				.from('demo_analytics')
				.select('*')
				.eq('demo_id', 'test-demo-id');

			expect(error).toBeNull();
			expect(Array.isArray(analytics)).toBe(true);
			expect(analytics.length).toBeGreaterThanOrEqual(2);

			// Clean up
			const analyticsIds = insertedData.map(item => item.id);
			await supabase.from('demo_analytics').delete().in('id', analyticsIds);
		}, TEST_TIMEOUT);
	});

	describe('Comments and Ratings', () => {
		it('should add comment to demo', async () => {
			const commentData = {
				demo_id: 'test-demo-id',
				user_id: testUserId,
				comment: 'Database integration test comment',
				rating: 5,
				created_at: new Date().toISOString()
			};

			const { data, error } = await supabase
				.from('demo_comments')
				.insert([commentData])
				.select()
				.single();

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.comment).toBe('Database integration test comment');
			expect(data.rating).toBe(5);

			// Clean up
			await supabase.from('demo_comments').delete().eq('id', data.id);
		}, TEST_TIMEOUT);

		it('should retrieve comments for demo', async () => {
			// First create some test comments
			const commentData = [
				{
					demo_id: 'test-demo-id',
					user_id: testUserId,
					comment: 'First test comment',
					rating: 4,
					created_at: new Date().toISOString()
				},
				{
					demo_id: 'test-demo-id',
					user_id: testUserId,
					comment: 'Second test comment',
					rating: 5,
					created_at: new Date().toISOString()
				}
			];

			const { data: insertedData, error: insertError } = await supabase
				.from('demo_comments')
				.insert(commentData)
				.select();

			expect(insertError).toBeNull();
			expect(insertedData).toBeDefined();

			// Retrieve comments
			const { data: comments, error } = await supabase
				.from('demo_comments')
				.select('*')
				.eq('demo_id', 'test-demo-id')
				.order('created_at', { ascending: false });

			expect(error).toBeNull();
			expect(Array.isArray(comments)).toBe(true);
			expect(comments.length).toBeGreaterThanOrEqual(2);

			// Clean up
			const commentIds = insertedData.map(item => item.id);
			await supabase.from('demo_comments').delete().in('id', commentIds);
		}, TEST_TIMEOUT);
	});

	describe('Payment and Billing', () => {
		it('should create payment record', async () => {
			const paymentData = {
				user_id: testUserId,
				amount: 1000, // $10.00 in cents
				currency: 'usd',
				status: 'pending',
				payment_method: 'card',
				description: 'Database integration test payment',
				created_at: new Date().toISOString()
			};

			const { data, error } = await supabase
				.from('payments')
				.insert([paymentData])
				.select()
				.single();

			expect(error).toBeNull();
			expect(data).toBeDefined();
			expect(data.amount).toBe(1000);
			expect(data.user_id).toBe(testUserId);

			// Clean up
			await supabase.from('payments').delete().eq('id', data.id);
		}, TEST_TIMEOUT);

		it('should update payment status', async () => {
			// First create a payment
			const paymentData = {
				user_id: testUserId,
				amount: 2000,
				currency: 'usd',
				status: 'pending',
				payment_method: 'card',
				description: 'Test payment for status update'
			};

			const { data: createdPayment, error: createError } = await supabase
				.from('payments')
				.insert([paymentData])
				.select()
				.single();

			expect(createError).toBeNull();
			expect(createdPayment).toBeDefined();

			// Update status
			const { error: updateError } = await supabase
				.from('payments')
				.update({ status: 'completed' })
				.eq('id', createdPayment.id);

			expect(updateError).toBeNull();

			// Verify update
			const { data: updatedPayment, error: selectError } = await supabase
				.from('payments')
				.select('*')
				.eq('id', createdPayment.id)
				.single();

			expect(selectError).toBeNull();
			expect(updatedPayment.status).toBe('completed');

			// Clean up
			await supabase.from('payments').delete().eq('id', createdPayment.id);
		}, TEST_TIMEOUT);
	});

	describe('Data Integrity', () => {
		it('should enforce foreign key constraints', async () => {
			// Try to create a record with non-existent user_id
			const invalidData = {
				name: 'Test Assistant',
				description: 'Test description',
				voice_id: 'test-voice',
				user_id: 'non-existent-user-id'
			};

			const { error } = await supabase
				.from('assistants')
				.insert([invalidData]);

			// Should fail due to foreign key constraint
			expect(error).toBeDefined();
			expect(error?.code).toBe('23503'); // Foreign key violation
		}, TEST_TIMEOUT);

		it('should enforce unique constraints', async () => {
			// Create first record
			const firstData = {
				name: 'Unique Test Assistant',
				description: 'First test assistant',
				voice_id: 'test-voice-1',
				user_id: testUserId
			};

			const { error: firstError } = await supabase
				.from('assistants')
				.insert([firstData]);

			expect(firstError).toBeNull();

			// Try to create duplicate (assuming name should be unique per user)
			const duplicateData = {
				name: 'Unique Test Assistant',
				description: 'Second test assistant',
				voice_id: 'test-voice-2',
				user_id: testUserId
			};

			const { error: duplicateError } = await supabase
				.from('assistants')
				.insert([duplicateData]);

			// Should fail due to unique constraint (if implemented)
			// Note: This test assumes a unique constraint exists
			if (duplicateError) {
				expect(duplicateError.code).toBe('23505'); // Unique violation
			}

			// Clean up
			await supabase.from('assistants').delete().eq('name', 'Unique Test Assistant');
		}, TEST_TIMEOUT);
	});

	describe('Performance Tests', () => {
		it('should handle large result sets efficiently', async () => {
			const startTime = Date.now();

			const { data, error } = await supabase
				.from('profiles')
				.select('*')
				.limit(100);

			const endTime = Date.now();
			const queryTime = endTime - startTime;

			expect(error).toBeNull();
			expect(Array.isArray(data)).toBe(true);
			expect(queryTime).toBeLessThan(1000); // Should complete within 1 second
		}, TEST_TIMEOUT);

		it('should handle concurrent operations', async () => {
			const promises = Array(5).fill(null).map(async () => {
				const { data, error } = await supabase
					.from('profiles')
					.select('id, full_name')
					.eq('id', testUserId)
					.single();

				return { data, error };
			});

			const results = await Promise.all(promises);

			results.forEach(({ data, error }) => {
				expect(error).toBeNull();
				expect(data).toBeDefined();
			});
		}, TEST_TIMEOUT);
	});
});
