import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://freshmanna-api.ailabsafrica.com';

/**
 * APIClient - Centralized HTTP client for FreshManna API
 * Handles authentication, token refresh, and all API endpoints
 */
class APIClient {
	private client: AxiosInstance;
	private accessToken: string | null = null;
	private refreshToken: string | null = null;

	constructor() {
		this.client = axios.create({
			baseURL: `${API_BASE_URL}/api/v1`,
			headers: {
				'Content-Type': 'application/json'
			},
			timeout: 30000 // 30 seconds
		});

		// Load tokens from localStorage
		this.accessToken = localStorage.getItem('access_token');
		this.refreshToken = localStorage.getItem('refresh_token');

		// Request interceptor - add auth token
		this.client.interceptors.request.use(
			(config) => {
				if (this.accessToken) {
					config.headers.Authorization = `Bearer ${this.accessToken}`;
				}
				return config;
			},
			(error) => Promise.reject(error)
		);

		// Response interceptor - handle token refresh
		this.client.interceptors.response.use(
			(response) => response,
			async (error: AxiosError) => {
				const originalRequest = error.config as any;

				// Token expired - attempt refresh
				if (error.response?.status === 401 && !originalRequest._retry && this.refreshToken) {
					originalRequest._retry = true;

					try {
						const response = await this.client.post('/auth/refresh', {
							refresh_token: this.refreshToken
						});

						const { access_token, refresh_token } = response.data;
						this.setTokens(access_token, refresh_token);

						// Retry original request with new token
						originalRequest.headers.Authorization = `Bearer ${access_token}`;
						return this.client(originalRequest);
					} catch (refreshError) {
						// Refresh failed - clear tokens
						this.clearTokens();

						// Only redirect to auth page if this was an authenticated endpoint
						// Don't redirect for public endpoints like /devotionals
						const url = originalRequest.url || '';
						const isAuthRequired = url.includes('/users/me') || url.includes('/bookmarks') || url.includes('/history');

						if (isAuthRequired && typeof window !== 'undefined') {
							// Only redirect on auth-required pages, not public browsing
							const currentPath = window.location.pathname;
							const isPublicPage = ['/', '/browse', '/about', '/devotional'].some(p => currentPath.startsWith(p));

							if (!isPublicPage) {
								window.location.href = '/auth';
							}
						}

						return Promise.reject(refreshError);
					}
				}

				// For 401 on public endpoints, clear any invalid tokens silently
				if (error.response?.status === 401 && this.accessToken) {
					const url = originalRequest.url || '';
					const isPublicEndpoint = url.includes('/devotionals') && !url.includes('bookmark') && !url.includes('like');

					if (isPublicEndpoint) {
						// Clear invalid token and retry without auth
						this.clearTokens();
						delete originalRequest.headers.Authorization;
						return this.client(originalRequest);
					}
				}

				return Promise.reject(error);
			}
		);
	}

	/**
	 * Store authentication tokens
	 */
	setTokens(accessToken: string, refreshToken: string): void {
		this.accessToken = accessToken;
		this.refreshToken = refreshToken;
		localStorage.setItem('access_token', accessToken);
		localStorage.setItem('refresh_token', refreshToken);
	}

	/**
	 * Clear authentication tokens
	 */
	clearTokens(): void {
		this.accessToken = null;
		this.refreshToken = null;
		localStorage.removeItem('access_token');
		localStorage.removeItem('refresh_token');
		// Dispatch custom event to notify components of logout
		if (typeof window !== 'undefined') {
			window.dispatchEvent(new Event('auth:logout'));
		}
	}

	// ============ Authentication ============

	/**
	 * Register a new user
	 */
	async signup(data: {
		email: string;
		password: string;
		name: string;
		role?: 'user' | 'admin';
	}) {
		const response = await this.client.post('/auth/signup', data);
		if (response.data.access_token) {
			this.setTokens(response.data.access_token, response.data.refresh_token);
		}
		return response.data;
	}

	/**
	 * Login user and get tokens
	 */
	async login(email: string, password: string) {
		const response = await this.client.post('/auth/login', { email, password });
		this.setTokens(response.data.access_token, response.data.refresh_token);
		return response.data;
	}

	/**
	 * Logout user (clear tokens)
	 */
	async logout() {
		try {
			await this.client.post('/auth/logout');
		} catch (error) {
			console.error('Logout error:', error);
		} finally {
			this.clearTokens();
		}
	}

	/**
	 * Request password reset email
	 */
	async forgotPassword(email: string) {
		const response = await this.client.post('/auth/forgot-password', { email });
		return response.data;
	}

	/**
	 * Reset password with token
	 */
	async resetPassword(token: string, new_password: string) {
		const response = await this.client.post('/auth/reset-password', { token, new_password });
		return response.data;
	}

	/**
	 * Get current authenticated user
	 */
	async getCurrentUser() {
		const response = await this.client.get('/auth/me');
		return response.data;
	}

	/**
	 * Change password for authenticated user
	 */
	async changePassword(currentPassword: string, newPassword: string): Promise<any> {
		const response = await this.client.post('/auth/change-password', {
			current_password: currentPassword,
			new_password: newPassword,
		});
		return response.data;
	}

	/**
	 * Refresh access token
	 */
	async refreshAccessToken() {
		const response = await this.client.post('/auth/refresh', {
			refresh_token: this.refreshToken
		});
		this.setTokens(response.data.access_token, response.data.refresh_token);
		return response.data;
	}

	// ============ Devotionals ============

	/**
	 * Get list of devotionals with filters
	 */
	async getDevotionals(params?: {
		category?: string;
		search?: string;
		author_id?: string;
		status?: 'draft' | 'scheduled' | 'published';
		page?: number;
		limit?: number;
		sort_by?: 'created_at' | 'published_at' | 'views_count' | 'likes_count';
		sort_order?: 'asc' | 'desc';
		start_date?: string; // YYYY-MM-DD format
		end_date?: string;   // YYYY-MM-DD format
		days?: number;        // Last N days from today
	}) {
		const response = await this.client.get('/devotionals/', { params });
		return response.data;
	}

	/**
	 * Get single devotional by ID
	 */
	async getDevotional(id: string) {
		const response = await this.client.get(`/devotionals/${id}`);
		return response.data;
	}

	/**
	 * Get devotional by slug
	 */
	async getDevotionalBySlug(slug: string) {
		const response = await this.client.get(`/devotionals/slug/${slug}`);
		return response.data;
	}

	/**
	 * Get today's devotional (public endpoint)
	 */
	async getTodaysDevotional() {
		const response = await this.client.get('/devotionals/today');
		return response.data;
	}

	/**
	 * Create new devotional (pastors only)
	 */
	async createDevotional(data: any) {
		const response = await this.client.post('/devotionals/', data);
		return response.data;
	}

	/**
	 * Update devotional (author only)
	 */
	async updateDevotional(id: string, data: any) {
		const response = await this.client.put(`/devotionals/${id}`, data);
		return response.data;
	}

	/**
	 * Delete devotional (author only)
	 */
	async deleteDevotional(id: string) {
		const response = await this.client.delete(`/devotionals/${id}`);
		return response.data;
	}

	/**
	 * Publish a draft devotional
	 */
	async publishDevotional(id: string) {
		const response = await this.client.post(`/devotionals/${id}/publish`);
		return response.data;
	}

	// ============ Engagement ============

	/**
	 * Like or unlike a devotional
	 */
	async likeDevotional(id: string) {
		const response = await this.client.post(`/devotionals/${id}/like`);
		return response.data;
	}

	/**
	 * Bookmark or unbookmark a devotional
	 */
	async bookmarkDevotional(id: string) {
		const response = await this.client.post(`/devotionals/${id}/bookmark`);
		return response.data;
	}

	/**
	 * Get user's bookmarked devotionals
	 */
	async getBookmarks() {
		const response = await this.client.get('/users/me/bookmarks');
		return response.data;
	}

	/**
	 * Get user's bookmarked devotionals (alias for consistency)
	 */
	async getBookmarkedDevotionals() {
		const response = await this.client.get('/users/me/bookmarks?type=devotional');
		return response.data;
	}

	/**
	 * Bookmark a scripture reference
	 */
	async bookmarkScripture(data: {
		reference: string;
		verse_text?: string;
		translation?: string;
		devotional_id?: string;
	}) {
		const response = await this.client.post('/scriptures/bookmark', data);
		return response.data;
	}

	/**
	 * Get user's bookmarked scriptures
	 */
	async getBookmarkedScriptures() {
		const response = await this.client.get('/users/me/bookmarks?type=scripture');
		return response.data;
	}

	/**
	 * Unbookmark a scripture
	 */
	async unbookmarkScripture(scriptureId: string) {
		const response = await this.client.delete(`/scriptures/${scriptureId}/bookmark`);
		return response.data;
	}

	/**
	 * Track a devotional share
	 */
	async shareDevotional(id: string, platform: 'whatsapp' | 'facebook' | 'twitter' | 'instagram' | 'copy_link') {
		const response = await this.client.post(`/devotionals/${id}/share`, { platform });
		return response.data;
	}

	/**
	 * Track reading progress
	 */
	async trackReading(id: string, data: {
		reading_progress: number;
		listening_progress?: number;
		time_spent_seconds: number;
	}) {
		const response = await this.client.post(`/devotionals/${id}/read`, data);
		return response.data;
	}

	/**
	 * Mark devotional as completely read (convenience method)
	 */
	async markAsRead(id: string) {
		return this.trackReading(id, {
			reading_progress: 100,
			time_spent_seconds: 0,
		});
	}

	/**
	 * Get reading history
	 */
	async getReadingHistory() {
		const response = await this.client.get('/users/me/history');
		return response.data;
	}

	// ============ Notifications ============

	/**
	 * Schedule a daily reminder notification
	 */
	async scheduleDailyReminder(reminderTime: string) {
		const response = await this.client.post('/notifications/reminders/schedule', null, {
			params: { reminder_time: reminderTime }
		});
		return response.data;
	}

	/**
	 * Get user notifications
	 */
	async getNotifications(params?: {
		page?: number;
		page_size?: number;
		unread_only?: boolean;
	}) {
		const response = await this.client.get('/notifications/', { params });
		return response.data;
	}

	/**
	 * Mark notification as read
	 */
	async markNotificationRead(notificationId: string) {
		const response = await this.client.post(`/notifications/${notificationId}/read`);
		return response.data;
	}

	// ============ Push Notifications ============

	/**
	 * Subscribe to push notifications
	 */
	async subscribeToPushNotifications(subscription: PushSubscription) {
		const response = await this.client.post('/push/subscribe', {
			endpoint: subscription.endpoint,
			keys: {
				p256dh: arrayBufferToBase64(subscription.getKey('p256dh')!),
				auth: arrayBufferToBase64(subscription.getKey('auth')!),
			},
			user_agent: navigator.userAgent,
		});
		return response.data;
	}

	/**
	 * Unsubscribe from push notifications
	 */
	async unsubscribeFromPushNotifications(endpoint?: string) {
		const params = endpoint ? { endpoint } : {};
		const response = await this.client.post('/push/unsubscribe', null, { params });
		return response.data;
	}

	/**
	 * Get user segments
	 */
	async getUserSegments() {
		const response = await this.client.get('/push/segments');
		return response.data;
	}

	/**
	 * Create announcement (admin only)
	 */
	async createAnnouncement(data: {
		title: string;
		message: string;
		segments?: string[];
		user_ids?: string[];
		scheduled_at?: string;
		data?: any;
	}) {
		const response = await this.client.post('/push/announcements', data);
		return response.data;
	}

	/**
	 * List announcements (admin only)
	 */
	async listAnnouncements(limit: number = 50) {
		const response = await this.client.get('/push/announcements', { params: { limit } });
		return response.data;
	}

	/**
	 * Update notification frequency settings
	 */
	async updateNotificationFrequency(settings: {
		daily_reminders?: number;
		new_devotionals?: number;
		announcements?: number;
		total_per_day?: number;
	}) {
		const response = await this.client.put('/push/frequency', settings);
		return response.data;
	}

	/**
	 * Get notification frequency settings
	 */
	async getNotificationFrequency() {
		const response = await this.client.get('/push/frequency');
		return response.data;
	}

	/**
	 * Subscribe to daily devotionals via email/WhatsApp
	 */
	async subscribeToDevotionals(data: {
		name: string;
		email?: string;
		whatsapp?: string;
		facebook_group?: boolean;
		preferences?: Record<string, any>;
	}) {
		const response = await this.client.post('/subscribe', data);
		return response.data;
	}

	/**
	 * Unsubscribe from daily devotionals
	 */
	async unsubscribeFromDevotionals(data: {
		email?: string;
		whatsapp?: string;
		token?: string;
	}) {
		const response = await this.client.post('/unsubscribe', data);
		return response.data;
	}

	/**
	 * Verify subscription
	 */
	async verifySubscription(subscriptionId: string, channel: string, token: string) {
		const response = await this.client.get(`/subscriptions/verify/${subscriptionId}`, {
			params: { channel, token }
		});
		return response.data;
	}

	/**
	 * Get VAPID public key for push subscription
	 */
	async getVapidPublicKey() {
		const response = await this.client.get('/push/vapid-public-key');
		return response.data;
	}

	// ============ Comments ============

	/**
	 * Get comments for a devotional
	 */
	async getComments(devotionalId: string, params?: { page?: number; limit?: number }) {
		const response = await this.client.get(`/devotionals/${devotionalId}/comments`, { params });
		return response.data;
	}

	/**
	 * Create a comment or reply
	 */
	async createComment(devotionalId: string, data: {
		text: string;
		parent_comment_id?: string;
	}) {
		const response = await this.client.post(`/devotionals/${devotionalId}/comments`, data);
		return response.data;
	}

	/**
	 * Update a comment
	 */
	async updateComment(commentId: string, data: { text: string }) {
		const response = await this.client.put(`/comments/${commentId}`, data);
		return response.data;
	}

	/**
	 * Delete a comment
	 */
	async deleteComment(commentId: string) {
		const response = await this.client.delete(`/comments/${commentId}`);
		return response.data;
	}

	/**
	 * Like or unlike a comment
	 */
	async likeComment(commentId: string) {
		const response = await this.client.post(`/comments/${commentId}/like`);
		return response.data;
	}

	// ============ AI Features ============

	/**
	 * Generate text-to-speech audio for devotional
	 */
	async generateTTS(devotionalId: string, data?: {
		provider_id?: string;
		voice_id?: string;
		speed?: number;
		language?: string;
		force_regenerate?: boolean;
	}) {
		const response = await this.client.post(`/ai/devotionals/${devotionalId}/tts`, data);
		return response.data;
	}

	// ============ User Profile ============

	/**
	 * Get user profile
	 */
	async getUserProfile(userId: string) {
		const response = await this.client.get(`/users/${userId}`);
		return response.data;
	}

	/**
	 * Update current user profile
	 */
	async updateProfile(data: {
		name?: string;
		bio?: string;
		avatar_url?: string;
		ministry_name?: string;
		ministry_website?: string;
		reading_preferences?: {
			font_size?: 'small' | 'medium' | 'large';
			theme?: 'light' | 'sepia' | 'dark';
			line_height?: 'compact' | 'normal' | 'relaxed';
			notification_time?: string;
			notifications_enabled?: boolean;
		};
		privacy_settings?: any;
	}) {
		const response = await this.client.put('/auth/me', data);
		return response.data;
	}

	/**
	 * Update reading preferences (convenience method)
	 */
	async updateReadingPreferences(preferences: {
		font_size?: 'small' | 'medium' | 'large';
		theme?: 'light' | 'sepia' | 'dark';
		line_height?: 'compact' | 'normal' | 'relaxed';
	}) {
		return this.updateProfile({ reading_preferences: preferences });
	}

	// ============ Analytics (Pastors) ============

	/**
	 * Get dashboard statistics for pastor
	 */
	async getDashboardStats() {
		const response = await this.client.get('/analytics/dashboard');
		return response.data;
	}

	/**
	 * Get analytics for specific devotional
	 */
	async getDevotionalAnalytics(devotionalId: string) {
		const response = await this.client.get(`/analytics/devotionals/${devotionalId}`);
		return response.data;
	}

	// ============ Admin Dashboard ============

	/**
	 * Get admin dashboard statistics
	 */
	async getAdminStats() {
		const response = await this.client.get('/admin/dashboard/stats');
		return response.data;
	}

	/**
	 * Get platform analytics
	 */
	async getAdminAnalytics(days: number = 30) {
		const response = await this.client.get('/analytics/dashboard', {
			params: { days }
		});
		return response.data;
	}

	/**
	 * Get top performing content
	 */
	async getTopContent(params?: {
		metric?: 'views' | 'likes' | 'comments' | 'shares';
		limit?: number;
	}) {
		const response = await this.client.get('/admin/dashboard/top-content', { params });
		return response.data;
	}

	/**
	 * Get recent activity
	 */
	async getRecentActivity(limit: number = 10) {
		const response = await this.client.get('/admin/dashboard/recent-activity', {
			params: { limit }
		});
		return response.data;
	}

	// ============ Author Dashboard ============

	/**
	 * Get author dashboard statistics
	 */
	async getAuthorStats() {
		const response = await this.client.get('/author/dashboard/stats');
		return response.data;
	}

	/**
	 * Get author performance metrics
	 */
	async getAuthorPerformance(days: number = 30) {
		const response = await this.client.get('/author/dashboard/performance', {
			params: { days }
		});
		return response.data;
	}

	/**
	 * Get author milestones
	 */
	async getAuthorMilestones() {
		const response = await this.client.get('/author/dashboard/milestones');
		return response.data;
	}

	// ============ Platform Settings ============

	/**
	 * Get platform settings (admin only)
	 */
	async getPlatformSettings() {
		const response = await this.client.get('/admin/settings');
		return response.data;
	}

	/**
	 * Update platform settings (admin only)
	 */
	async updatePlatformSettings(settings: any) {
		const response = await this.client.put('/admin/settings', settings);
		return response.data;
	}

	// ============ Content Moderation ============

	/**
	 * Get moderation statistics
	 */
	async getModerationStats() {
		const response = await this.client.get('/moderation/stats');
		return response.data;
	}

	/**
	 * Get list of flags (moderation queue)
	 */
	async getFlags(params?: {
		status?: 'pending' | 'reviewed' | 'dismissed' | 'action_taken';
		content_type?: 'devotional' | 'comment';
		reason_category?: 'spam' | 'inappropriate' | 'offensive' | 'plagiarism' | 'misleading' | 'other';
		page?: number;
		page_size?: number;
		sort_by?: 'created_at' | 'status';
		sort_order?: 'asc' | 'desc';
	}) {
		const response = await this.client.get('/moderation/queue', { params });
		return response.data;
	}

	/**
	 * Get flag details
	 */
	async getFlag(flagId: string) {
		const response = await this.client.get(`/moderation/flags/${flagId}`);
		return response.data;
	}

	/**
	 * Flag a devotional for review
	 */
	async flagDevotional(devotionalId: string, data: {
		reason: string;
		details?: string;
		severity: 'low' | 'medium' | 'high' | 'critical';
	}) {
		const response = await this.client.post(`/devotionals/${devotionalId}/flag`, data);
		return response.data;
	}

	/**
	 * Moderate flagged content (resolve a flag)
	 */
	async resolveFlag(flagId: string, data: {
		action: 'approve' | 'delete' | 'hide' | 'warn_author' | 'suspend_author' | 'dismiss_flag';
		reason?: string;
		notes?: string;
	}) {
		const response = await this.client.post(`/moderation/flags/${flagId}/moderate`, data);
		return response.data;
	}

	// ============ Analytics ============

	/**
	 * Get dashboard analytics
	 */
	async getDashboardAnalytics(days: number = 30) {
		const response = await this.client.get('/analytics/dashboard', {
			params: { days }
		});
		return response.data;
	}

	/**
	 * Get engagement trends
	 */
	async getEngagementTrends(days: number = 30, granularity: 'daily' | 'weekly' | 'monthly' = 'daily') {
		const response = await this.client.get('/analytics/engagement/trends', {
			params: { days, granularity }
		});
		return response.data;
	}

	/**
	 * Get top performing devotionals
	 */
	async getTopDevotionals(limit: number = 10, metric: 'views' | 'likes' | 'comments' | 'shares' | 'engagement' = 'views', days: number = 30) {
		const response = await this.client.get('/analytics/devotionals/top', {
			params: { limit, metric, days }
		});
		return response.data;
	}

	/**
	 * Get reader insights
	 */
	async getReaderInsights(days: number = 30) {
		const response = await this.client.get('/analytics/readers/insights', {
			params: { days }
		});
		return response.data;
	}

	/**
	 * Get audience growth metrics
	 */
	async getAudienceGrowth(days: number = 90) {
		const response = await this.client.get('/analytics/audience/growth', {
			params: { days }
		});
		return response.data;
	}

	/**
	 * Export analytics to CSV
	 */
	async exportAnalyticsCSV(days: number = 30) {
		const response = await this.client.get('/analytics/export/csv', {
			params: { days },
			responseType: 'blob'
		});
		return response.data;
	}

	// ============ Calendar View ============

	/**
	 * Get devotionals in calendar view
	 */
	async getCalendarDevotionals(params?: {
		start_date?: string;
		end_date?: string;
		year?: number;
		month?: number;
		week?: number;
		status?: 'published' | 'scheduled' | 'draft';
		category?: string;
	}) {
		const response = await this.client.get('/calendar/devotionals', { params });
		return response.data;
	}

	/**
	 * Find gaps in devotional schedule
	 */
	async getScheduleGaps(params?: {
		start_date?: string;
		end_date?: string;
	}) {
		const response = await this.client.get('/calendar/gaps', { params });
		return response.data;
	}

	/**
	 * Get upcoming devotionals
	 */
	async getUpcomingDevotionals(params?: {
		days?: number;
		limit?: number;
	}) {
		const response = await this.client.get('/calendar/upcoming', { params });
		return response.data;
	}

	/**
	 * Get calendar statistics
	 */
	async getCalendarStats() {
		const response = await this.client.get('/calendar/stats');
		return response.data;
	}

	// ============ File Upload ============

	/**
	 * Upload file (image, audio, etc.)
	 */
	async uploadFile(file: File, type: 'image' | 'audio' | 'video') {
		const formData = new FormData();
		formData.append('file', file);
		formData.append('type', type);

		const response = await this.client.post('/upload', formData, {
			headers: {
				'Content-Type': 'multipart/form-data'
			}
		});
		return response.data;
	}

	// ============ Gamification ============

	/**
	 * Get user's gamification profile
	 */
	async getGamificationProfile() {
		const response = await this.client.get('/gamification/profile');
		return response.data;
	}

	/**
	 * Get user's streak information
	 */
	async getStreak() {
		const response = await this.client.get('/gamification/streak');
		return response.data;
	}

	/**
	 * Use a streak freeze
	 */
	async useStreakFreeze() {
		const response = await this.client.post('/gamification/streak/freeze');
		return response.data;
	}

	/**
	 * Get all achievements with user progress
	 */
	async getAchievements(params?: { category?: string; unlocked_only?: boolean }) {
		const response = await this.client.get('/gamification/achievements', { params });
		return response.data;
	}

	/**
	 * Get specific achievement details
	 */
	async getAchievement(achievementId: string) {
		const response = await this.client.get(`/gamification/achievements/${achievementId}`);
		return response.data;
	}

	/**
	 * Get leaderboard rankings
	 */
	async getLeaderboard(type: 'global' | 'friends' | 'weekly' = 'global', limit: number = 100) {
		const response = await this.client.get('/gamification/leaderboard', {
			params: { type, limit }
		});
		return response.data;
	}

	/**
	 * Get gamification statistics
	 */
	async getGamificationStats() {
		const response = await this.client.get('/gamification/stats');
		return response.data;
	}

	// ============ Groups ============

	/**
	 * List groups with filters
	 */
	async listGroups(params?: {
		page?: number;
		page_size?: number;
		is_public?: boolean;
		search?: string;
	}) {
		const response = await this.client.get('/groups/', { params });
		return response.data;
	}

	/**
	 * Get single group by ID
	 */
	async getGroup(groupId: string) {
		const response = await this.client.get(`/groups/${groupId}`);
		return response.data;
	}

	/**
	 * Create a new group
	 */
	async createGroup(data: {
		name: string;
		description?: string;
		is_public?: boolean;
		devotional_id?: string;
		discussion_topic?: string;
	}) {
		const response = await this.client.post('/groups/', data);
		return response.data;
	}

	/**
	 * Update a group
	 */
	async updateGroup(groupId: string, data: {
		name?: string;
		description?: string;
		is_public?: boolean;
		discussion_topic?: string;
	}) {
		const response = await this.client.put(`/groups/${groupId}`, data);
		return response.data;
	}

	/**
	 * Delete a group
	 */
	async deleteGroup(groupId: string) {
		const response = await this.client.delete(`/groups/${groupId}`);
		return response.data;
	}

	/**
	 * Join a group
	 */
	async joinGroup(groupId: string) {
		const response = await this.client.post(`/groups/${groupId}/join`);
		return response.data;
	}

	/**
	 * Leave a group
	 */
	async leaveGroup(groupId: string) {
		const response = await this.client.post(`/groups/${groupId}/leave`);
		return response.data;
	}

	/**
	 * Get group messages
	 */
	async getGroupMessages(groupId: string, params?: {
		page?: number;
		page_size?: number;
	}) {
		const response = await this.client.get(`/groups/${groupId}/messages`, { params });
		return response.data;
	}

	/**
	 * Create a group message
	 */
	async createGroupMessage(groupId: string, data: {
		text: string;
		devotional_id?: string;
	}) {
		const response = await this.client.post(`/groups/${groupId}/messages`, data);
		return response.data;
	}

	// ============ Group Invites ============

	/**
	 * Create a group invite
	 */
	async createGroupInvite(groupId: string, data: {
		invitee_email?: string;
		invitee_id?: string;
	}) {
		const response = await this.client.post(`/groups/${groupId}/invites`, data);
		return response.data;
	}

	/**
	 * List group invites
	 */
	async listGroupInvites(groupId: string, params?: {
		page?: number;
		page_size?: number;
		status?: string;
	}) {
		const response = await this.client.get(`/groups/${groupId}/invites`, { params });
		return response.data;
	}

	/**
	 * Get invite by token
	 */
	async getInviteByToken(token: string) {
		const response = await this.client.get(`/invites/token/${token}`);
		return response.data;
	}

	/**
	 * Accept an invite
	 */
	async acceptInvite(token: string) {
		const response = await this.client.post(`/invites/token/${token}/accept`);
		return response.data;
	}

	/**
	 * Decline an invite
	 */
	async declineInvite(inviteId: string) {
		const response = await this.client.post(`/invites/${inviteId}/decline`);
		return response.data;
	}

	/**
	 * Revoke an invite
	 */
	async revokeInvite(inviteId: string) {
		const response = await this.client.delete(`/invites/${inviteId}`);
		return response.data;
	}

	// ============ Health Check ============

	/**
	 * Check API health
	 */
	async healthCheck() {
		const response = await this.client.get('/health');
		return response.data;
	}

	// ============ Series ============

	/**
	 * List all series
	 */
	async listSeries(authorId?: string): Promise<any[]> {
		const params = authorId ? { author_id: authorId } : {};
		const response = await this.client.get('/series', { params });
		return response.data;
	}

	/**
	 * Get series by ID
	 */
	async getSeries(seriesId: string): Promise<any> {
		const response = await this.client.get(`/series/${seriesId}`);
		return response.data;
	}

	/**
	 * Get devotionals in a series
	 */
	async getSeriesDevotionals(seriesId: string): Promise<any[]> {
		const response = await this.client.get(`/series/${seriesId}/devotionals`);
		return response.data;
	}

	/**
	 * Create a new series (author/admin only)
	 */
	async createSeries(data: {
		name: string;
		description?: string;
		cover_image_url?: string;
		start_date?: string; // ISO date string
	}): Promise<any> {
		const response = await this.client.post('/series/', data);
		return response.data;
	}

	/**
	 * Update series metadata (author/admin only)
	 */
	async updateSeries(seriesId: string, data: {
		name?: string;
		description?: string;
		cover_image_url?: string;
		start_date?: string; // ISO date string
	}): Promise<any> {
		const response = await this.client.patch(`/series/${seriesId}`, data);
		return response.data;
	}

	/**
	 * Move a series to a new start date (reschedules all devotionals)
	 */
	async moveSeries(seriesId: string, newStartDate: string): Promise<any> {
		const response = await this.client.post(`/series/${seriesId}/move`, null, {
			params: { new_start_date: newStartDate }
		});
		return response.data;
	}

	/**
	 * Delete a series (author/admin only)
	 * @param seriesId - Series ID to delete
	 * @param handleDevotionals - 'unlink' to orphan devotionals, 'delete' to fail if devotionals exist
	 */
	async deleteSeries(seriesId: string, handleDevotionals: 'unlink' | 'delete' = 'unlink'): Promise<any> {
		const orphan_devotionals = handleDevotionals === 'unlink';
		const response = await this.client.delete(`/series/${seriesId}`, {
			params: { orphan_devotionals }
		});
		return response.data;
	}

	/**
	 * Schedule all devotionals in a series (author/admin only)
	 * Calculates scheduled_at = series.start_date + (part_number - 1) days
	 */
	async scheduleSeries(seriesId: string): Promise<any> {
		const response = await this.client.post(`/series/${seriesId}/schedule`);
		return response.data;
	}

	/**
	 * Reorder devotionals in a series (author/admin only)
	 * @param seriesId - Series ID
	 * @param devotionalOrder - Array of devotional IDs in desired order
	 */
	async reorderSeriesDevotionals(seriesId: string, devotionalOrder: string[]): Promise<any> {
		const response = await this.client.post(`/series/${seriesId}/reorder`, devotionalOrder);
		return response.data;
	}

	/**
	 * Remove a devotional from a series (author/admin only)
	 * @param seriesId - Series ID
	 * @param devotionalId - Devotional ID to remove
	 * @param autoRenumber - If true, renumber remaining devotionals; if false, leave gaps
	 */
	async removeDevotionalFromSeries(
		seriesId: string,
		devotionalId: string,
		autoRenumber: boolean = true
	): Promise<any> {
		const response = await this.client.delete(`/series/${seriesId}/devotionals/${devotionalId}`, {
			params: { auto_renumber: autoRenumber }
		});
		return response.data;
	}
}

// Helper function to convert ArrayBuffer to base64
function arrayBufferToBase64(buffer: ArrayBuffer): string {
	const bytes = new Uint8Array(buffer);
	let binary = '';
	for (let i = 0; i < bytes.byteLength; i++) {
		binary += String.fromCharCode(bytes[i]);
	}
	return btoa(binary);
}

// Export singleton instance
export const apiClient = new APIClient();
