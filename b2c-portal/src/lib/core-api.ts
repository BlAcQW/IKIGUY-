/**
 * Core Backend API Client for B2C Portal
 * 
 * This service layer connects the B2C Portal frontend to the Core Backend's
 * internal APIs. The Core Backend is the private control plane that orchestrates
 * all KasaAI functionality.
 */

import { mongoAuth } from '@/lib/mongo-auth';
import { transformResponse, transformResponseArray, transformRequest } from '@/lib/type-conversions.ts';
import { createRetryWrapper, RETRY_CONFIGS } from '@/lib/retry-logic.ts';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


// Core Backend API configuration
const CORE_API_BASE_URL = CORE_API_URL;
const CORE_API_TIMEOUT = 30000; // 30 seconds

// Types for Core Backend API responses
export interface CoreApiResponse<T = any> {
	status: 'success' | 'error';
	data?: T;
	error?: {
		code: string;
		message: string;
		request_id?: string;
	};
}

export interface Assistant {
	id: string;
	name: string;
	template: string;
	channel: string;
	language: string;
	voice: string;
	prompt: string;
	organization_id: string;
	created_at: string;
	updated_at: string;
}

export interface AssistantCreate {
	name: string;
	template: string;
	channel: string;
	language: string;
	voice: string;
	prompt: string;
	organization_id: string;
}

export interface Campaign {
        id: string;
        name: string;
        assistant_id: string;
        audience_id: string;
        status:
                | 'draft'
                | 'scheduled'
                | 'running'
                | 'paused'
                | 'stopped'
                | 'completed';
        organization_id: string;
        created_at: string;
        updated_at: string;
}

export interface CampaignCreate {
	name: string;
	assistant_id: string;
	audience_id: string;
	organization_id: string;
	cron?: string;
	pacing_per_minute?: number;
	max_attempts?: number;
	backoff_minutes?: number;
}

export interface KnowledgeBaseSource {
	id: string;
	organization_id: string;
	uri: string;
	source_type: string;
	created_at: string;
}

export interface KnowledgeBaseSearchRequest {
	organization_id: string;
	query: string;
	top_k?: number;
}

export interface KnowledgeBaseSearchResult {
	source_id: string;
	text: string;
	score: number;
}

export interface LicenseInfo {
	organization_id: string;
	is_active: boolean;
	features: Record<string, any>;
	limits: Record<string, any>;
	expires_at?: string;
}

export interface UsageData {
	organization_id: string;
	minutes: number;
	messages: number;
	stt_calls: number;
	tts_calls: number;
	telephony_cost: number;
	stt_cost: number;
	tts_cost: number;
	period: string;
	generated_at: string;
}

export interface PaymentMethod {
	id: string;
	type: string;
	name: string;
	currency: string;
	is_default: boolean;
}

export interface WalletBalance {
	wallet_id: string;
	balance: number;
	pending_balance: number;
	reserved_balance: number;
	available_balance: number;
	total_balance: number;
	currency: string;
	last_transaction_at?: string;
	auto_reload_enabled: boolean;
	low_balance_alert_enabled: boolean;
}

export interface WalletPaymentMethod {
	id: string;
	provider: string;
	method_type: string;
	display_name: string;
	nickname?: string;
	is_default: boolean;
	is_verified: boolean;
	is_active: boolean;
	created_at: string;
	last_used_at?: string;
	card_last4?: string;
	card_brand?: string;
	phone_number_masked?: string;
	bank_name?: string;
}

export interface WalletTransaction {
	id: string;
	transaction_type: string;
	status: string;
	amount: number;
	currency: string;
	processing_fee: number;
	total_amount: number;
	description: string;
	payment_method_display?: string;
	created_at: string;
	completed_at?: string;
}

export interface WalletDepositRequest {
	amount: number;
	currency: string;
	payment_method_id: string;
	description?: string;
}

export interface WalletSettings {
	wallet_id: string;
	auto_reload_enabled: boolean;
	auto_reload_threshold: number;
	auto_reload_amount: number;
	auto_reload_payment_method_id?: string;
	low_balance_alert_enabled: boolean;
	low_balance_threshold: number;
}

export interface UpdateWalletSettingsRequest {
	auto_reload_enabled?: boolean;
	auto_reload_threshold?: number;
	auto_reload_amount?: number;
	auto_reload_payment_method_id?: string;
	low_balance_alert_enabled?: boolean;
	low_balance_threshold?: number;
}

export interface AddPaymentMethodRequest {
	provider: string;
	method_type: string;
	display_name: string;
	stripe_payment_method_id?: string;
	flutterwave_token?: string;
	phone_number?: string;
	phone_network?: string;
	account_number?: string;
	bank_name?: string;
	bank_code?: string;
	nickname?: string;
}

// Affiliate Program Types
export interface AffiliateProfile {
	id: string;
	user_id: string;
	organization_id: string;
	referral_code: string;
	upline_id?: string;
	tier_level: number;
	tier1_commission_rate: number;
	tier2_commission_rate: number;
	tier3_commission_rate: number;
	total_referrals: number;
	direct_referrals: number;
	total_sales: number;
	total_commissions_earned: number;
	total_commissions_paid: number;
	pending_commissions: number;
	is_active: boolean;
	is_verified: boolean;
	joined_program_at: string;
	last_referral_at?: string;
	payout_method: 'wallet_credit' | 'mobile_money' | 'bank_transfer' | 'paypal';
	payout_threshold: number;
	payment_method_id?: string;
	created_at: string;
	updated_at: string;
}

export interface AffiliateStats {
	total_earned: number;
	total_paid: number;
	pending_commissions: number;
	this_month_earnings: number;
	last_month_earnings: number;
	total_referrals: number;
	direct_referrals: number;
	tier2_referrals: number;
	tier3_referrals: number;
	total_sales: number;
	conversion_rate: number;
	average_commission_per_referral: number;
	last_referral_at?: string;
	last_commission_at?: string;
}

export interface ReferralLink {
	id: string;
	referral_code: string;
	url: string;
	utm_source?: string;
	utm_campaign?: string;
	utm_medium?: string;
	click_count: number;
	conversion_count: number;
	conversion_rate: number;
	created_at: string;
}

export interface Referral {
	user_id: string;
	name?: string;
	email: string;
	joined_at: string;
	tier_level: number;
	total_purchases: number;
	commissions_earned_from_user: number;
	first_purchase_at?: string;
	is_active: boolean;
}

export interface ReferralAttribution {
	id: string;
	affiliate_id: string;
	referral_code: string;
	referred_user_id: string;
	organization_id: string;
	attribution_date: string;
	attribution_source: string;
	ip_address?: string;
	user_agent?: string;
	utm_source?: string;
	utm_campaign?: string;
	utm_medium?: string;
	created_at: string;
}

export interface CommissionRecord {
	id: string;
	referred_user_name?: string;
	referred_user_email: string;
	sale_amount: number;
	commission_rate: number;
	commission_amount: number;
	tier_level: number;
	status: 'pending' | 'approved' | 'paid' | 'cancelled';
	created_at: string;
	approved_at?: string;
	paid_at?: string;
}

export interface PayoutRequest {
	id: string;
	amount: number;
	payout_method: 'wallet_credit' | 'mobile_money' | 'bank_transfer' | 'paypal';
	processing_fee: number;
	net_amount: number;
	status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
	created_at: string;
	processed_at?: string;
	notes?: string;
	failure_reason?: string;
}

export interface NetworkStats {
	tier1_count: number;
	tier2_count: number;
	tier3_count: number;
	total_network_size: number;
	total_network_sales: number;
	total_network_commissions: number;
}

export interface JoinProgramRequest {
	upline_referral_code?: string;
}

export interface UpdateAffiliateProfileRequest {
	payout_method?: 'wallet_credit' | 'mobile_money' | 'bank_transfer' | 'paypal';
	payout_threshold?: number;
	payment_method_id?: string;
}

export interface CreateReferralLinkRequest {
	utm_source?: string;
	utm_campaign?: string;
	utm_medium?: string;
}

export interface PayoutRequestCreate {
	amount: number;
	payout_method: 'wallet_credit' | 'mobile_money' | 'bank_transfer' | 'paypal';
	payment_method_id?: string;
}

export interface PaginatedResponse<T> {
	items: T[];
	total: number;
	limit: number;
	offset: number;
}

// Industry Module Types
export interface IndustryModuleCapability {
	id: string;
	name: string;
	description: string;
	category: string;
	parameters: Record<string, any>;
	estimated_duration: number;
	required_integrations: string[];
}

export interface IndustryModuleWorkflow {
	id: string;
	name: string;
	description: string;
	steps: Array<{
		step_id: string;
		capability_id: string;
		parameters: Record<string, any>;
		condition?: string;
	}>;
	estimated_duration: number;
	required_integrations: string[];
}

export interface IndustryModuleAnalytics {
	module_name: string;
	metrics: Record<string, number>;
	time_series: Array<{
		timestamp: string;
		values: Record<string, number>;
	}>;
	insights: string[];
	recommendations: string[];
}

export interface IndustryModuleCompliance {
	module_name: string;
	compliance_frameworks: string[];
	status: 'compliant' | 'non_compliant' | 'pending_review';
	last_audit: string;
	next_audit: string;
	requirements: Array<{
		requirement_id: string;
		description: string;
		status: 'met' | 'not_met' | 'in_progress';
		evidence: string[];
	}>;
}

export interface IndustryModuleHealth {
	module_name: string;
	status: 'healthy' | 'degraded' | 'unhealthy';
	uptime_percentage: number;
	last_check: string;
	integrations: Array<{
		name: string;
		status: 'connected' | 'disconnected' | 'error';
		last_sync: string;
		error_message?: string;
	}>;
	performance_metrics: {
		avg_response_time: number;
		error_rate: number;
		throughput: number;
	};
}

/**
 * Get service token for Core Backend API calls
 */
async function getServiceToken(): Promise<string> {
	const accessToken = mongoAuth.getAccessToken();
	if (!accessToken) {
		throw new Error('No active MongoDB session');
	}

	return accessToken;
}

/**
 * Make authenticated request to Core Backend API
 */
async function coreApiRequest<T>(
	endpoint: string,
	options: RequestInit = {}
): Promise<T> {
	const serviceToken = await getServiceToken();

	// Get current organization from localStorage
	const currentOrgId = localStorage.getItem('kasaai_current_organization_id');

	const headers: HeadersInit = {
		'Content-Type': 'application/json',
		'Authorization': `Bearer ${serviceToken}`,
		...options.headers,
	};

	// Add organization context if available
	if (currentOrgId) {
		headers['X-Organization-ID'] = currentOrgId;
	}

	const response = await fetch(`${CORE_API_BASE_URL}${endpoint}`, {
		...options,
		headers,
		signal: AbortSignal.timeout(CORE_API_TIMEOUT),
	});

	if (!response.ok) {
		const errorData = await response.json().catch(() => ({}));
		const error: any = new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
		// Attach response object for status code checking
		error.response = { status: response.status, data: errorData };
		throw error;
	}

	return response.json();
}

// Create retry wrapper for API requests
const retryableApiRequest = createRetryWrapper(coreApiRequest, RETRY_CONFIGS.standard);

/**
 * Assistant Management API
 */
export const assistantApi = {
	/**
	 * Create a new assistant
	 */
	async create(assistant: AssistantCreate): Promise<Assistant> {
		const transformedAssistant = transformRequest(assistant);
		const response = await retryableApiRequest<Assistant>('/internal/assistants', {
			method: 'POST',
			body: JSON.stringify(transformedAssistant),
		});
		return transformResponse(response);
	},

	/**
	 * Get assistant by ID
	 */
	async get(id: string): Promise<Assistant> {
		const response = await retryableApiRequest<Assistant>(`/internal/assistants/${id}`);
		return transformResponse(response);
	},

	/**
	 * List assistants for organization (uses X-Organization-ID header)
	 */
	async list(): Promise<Assistant[]> {
		const response = await retryableApiRequest<Assistant[]>(`/internal/assistants`);
		return transformResponseArray(response);
	},
};

/**
 * Campaign Management API
 */
export const campaignApi = {
	/**
	 * Create a new campaign
	 */
	async create(campaign: CampaignCreate): Promise<Campaign> {
		const transformedCampaign = transformRequest(campaign);
		const response = await retryableApiRequest<Campaign>('/internal/campaigns', {
			method: 'POST',
			body: JSON.stringify(transformedCampaign),
		});
		return transformResponse(response);
	},

	/**
	 * Get campaign by ID
	 */
	async get(id: string): Promise<Campaign> {
		const response = await retryableApiRequest<Campaign>(`/internal/campaigns/${id}`);
		return transformResponse(response);
	},

	/**
	 * List campaigns for organization (uses X-Organization-ID header)
	 */
        async list(): Promise<Campaign[]> {
                const response = await retryableApiRequest<Campaign[]>(`/internal/campaigns`);
                return transformResponseArray(response);
        },

        /**
         * Start a campaign
         */
        async start(id: string): Promise<Campaign> {
                const response = await retryableApiRequest<Campaign>(`/internal/campaigns/${id}/start`, {
                        method: 'POST',
                });
                return transformResponse(response);
        },

        /**
         * Pause a campaign
         */
        async pause(id: string): Promise<Campaign> {
                const response = await retryableApiRequest<Campaign>(`/internal/campaigns/${id}/pause`, {
                        method: 'POST',
                });
                return transformResponse(response);
        },

        /**
         * Resume a paused campaign
         */
        async resume(id: string): Promise<Campaign> {
                const response = await retryableApiRequest<Campaign>(`/internal/campaigns/${id}/resume`, {
                        method: 'POST',
                });
                return transformResponse(response);
        },

        /**
         * Stop a campaign
         */
        async stop(id: string): Promise<Campaign> {
                const response = await retryableApiRequest<Campaign>(`/internal/campaigns/${id}/stop`, {
                        method: 'POST',
                });
                return transformResponse(response);
        },
};

/**
 * Knowledge Base API
 */
export const knowledgeBaseApi = {
	/**
	 * Ingest content into knowledge base (uses X-Organization-ID header)
	 */
	async ingest(content?: string, url?: string): Promise<{ source_id: string; chunks: number }> {
		const request = transformRequest({ content, url });
		const response = await retryableApiRequest<{ source_id: string; chunks: number }>('/internal/kb', {
			method: 'POST',
			body: JSON.stringify(request),
		});
		return transformResponse(response);
	},

	/**
	 * Search knowledge base
	 */
	async search(request: KnowledgeBaseSearchRequest): Promise<KnowledgeBaseSearchResult[]> {
		const transformedRequest = transformRequest(request);
		const response = await retryableApiRequest<KnowledgeBaseSearchResult[]>('/internal/kb/search', {
			method: 'POST',
			body: JSON.stringify(transformedRequest),
		});
		return transformResponseArray(response);
	},
};

/**
 * License Management API
 */
export const licenseApi = {
	/**
	 * Get license status (uses X-Organization-ID header)
	 */
	async getStatus(): Promise<LicenseInfo> {
		const response = await retryableApiRequest<LicenseInfo>(`/internal/licenses/status`);
		return transformResponse(response);
	},

	/**
	 * Verify license for specific features (uses X-Organization-ID header)
	 */
	async verify(
		agents: number = 0,
		channels: number = 0,
		minutes: number = 0
	): Promise<{ allowed: boolean; detail?: string }> {
		const request = transformRequest({ agents, channels, minutes });
		const response = await retryableApiRequest<{ allowed: boolean; detail?: string }>('/internal/licenses/verify', {
			method: 'POST',
			body: JSON.stringify(request),
		});
		return transformResponse(response);
	},

	/**
	 * Activate license (uses X-Organization-ID header)
	 */
	async activate(
		licenseKey: string,
		features?: Record<string, any>,
		limits?: Record<string, any>
	): Promise<{ status: string; license_id: string }> {
		const request = transformRequest({
			license_key: licenseKey,
			features: features || {},
			limits: limits || {},
		});
		const response = await retryableApiRequest<{ status: string; license_id: string }>('/internal/licenses/activate', {
			method: 'POST',
			body: JSON.stringify(request),
		});
		return transformResponse(response);
	},
};

/**
 * Usage Analytics API
 */
export const usageApi = {
	/**
	 * Get usage analytics (uses X-Organization-ID header)
	 */
	async getUsageData(
		startDate?: string,
		endDate?: string
	): Promise<UsageData> {
		const params = new URLSearchParams();
		if (startDate) params.append('start_date', startDate);
		if (endDate) params.append('end_date', endDate);

		const queryString = params.toString();
		const endpoint = queryString ? `/internal/usage?${queryString}` : '/internal/usage';
		const response = await retryableApiRequest<UsageData>(endpoint);
		return transformResponse(response);
	},

	/**
	 * Get usage summary (uses X-Organization-ID header)
	 */
	async getUsageSummary(): Promise<UsageData> {
		const response = await retryableApiRequest<UsageData>(`/internal/usage`);
		return transformResponse(response);
	},
};

/**
 * Payment API
 */
export const paymentApi = {
	/**
	 * Get wallet balance
	 */
	async getWalletBalance(): Promise<WalletBalance> {
		const response = await retryableApiRequest<WalletBalance>('/api/wallet/balance');
		return transformResponse(response);
	},

	/**
	 * Get payment methods
	 */
	async getPaymentMethods(): Promise<WalletPaymentMethod[]> {
		const response = await retryableApiRequest<WalletPaymentMethod[]>('/api/wallet/payment-methods');
		return transformResponseArray(response);
	},

	/**
	 * Add payment method
	 */
	async addPaymentMethod(methodData: AddPaymentMethodRequest): Promise<WalletPaymentMethod> {
		const transformedData = transformRequest(methodData);
		const response = await retryableApiRequest<WalletPaymentMethod>('/api/wallet/payment-methods', {
			method: 'POST',
			body: JSON.stringify(transformedData),
		});
		return transformResponse(response);
	},

	/**
	 * Update payment method
	 */
	async updatePaymentMethod(methodId: string, updates: { nickname?: string; is_default?: boolean }): Promise<WalletPaymentMethod> {
		const transformedData = transformRequest(updates);
		const response = await retryableApiRequest<WalletPaymentMethod>(`/api/wallet/payment-methods/${methodId}`, {
			method: 'PATCH',
			body: JSON.stringify(transformedData),
		});
		return transformResponse(response);
	},

	/**
	 * Delete payment method
	 */
	async deletePaymentMethod(methodId: string): Promise<void> {
		await retryableApiRequest(`/api/wallet/payment-methods/${methodId}`, {
			method: 'DELETE',
		});
	},

	/**
	 * Create deposit
	 */
	async createDeposit(depositData: WalletDepositRequest): Promise<WalletTransaction> {
		const transformedData = transformRequest(depositData);
		const response = await retryableApiRequest<WalletTransaction>('/api/wallet/deposit', {
			method: 'POST',
			body: JSON.stringify(transformedData),
		});
		return transformResponse(response);
	},

	/**
	 * Get transaction history
	 */
	async getTransactions(limit?: number, offset?: number): Promise<WalletTransaction[]> {
		const params = new URLSearchParams();
		if (limit) params.append('limit', limit.toString());
		if (offset) params.append('offset', offset.toString());
		const url = `/api/wallet/transactions${params.toString() ? '?' + params.toString() : ''}`;
		const response = await retryableApiRequest<WalletTransaction[]>(url);
		return transformResponseArray(response);
	},

	/**
	 * Get specific transaction
	 */
	async getTransaction(transactionId: string): Promise<WalletTransaction> {
		const response = await retryableApiRequest<WalletTransaction>(`/api/wallet/transactions/${transactionId}`);
		return transformResponse(response);
	},

	/**
	 * Get available payment providers
	 */
	async getPaymentProviders(): Promise<{ providers: any[] }> {
		const response = await retryableApiRequest<{ providers: any[] }>('/api/wallet/providers');
		// Ensure response has the correct structure
		if (!response || typeof response !== 'object') {
			console.error('Invalid response from providers endpoint:', response);
			return { providers: [] };
		}
		// If response already has providers array, return it
		if (Array.isArray(response.providers)) {
			return transformResponse(response);
		}
		// If response IS the providers array (shouldn't happen but handle it)
		if (Array.isArray(response)) {
			return { providers: transformResponseArray(response) };
		}
		console.error('Unexpected response structure from providers endpoint:', response);
		return { providers: [] };
	},

	/**
	 * Get wallet settings
	 */
	async getWalletSettings(): Promise<WalletSettings> {
		const response = await retryableApiRequest<WalletSettings>('/api/wallet/settings');
		return transformResponse(response);
	},

	/**
	 * Update wallet settings
	 */
	async updateWalletSettings(settings: UpdateWalletSettingsRequest): Promise<WalletSettings> {
		const transformedData = transformRequest(settings);
		const response = await retryableApiRequest<WalletSettings>('/api/wallet/settings', {
			method: 'PATCH',
			body: JSON.stringify(transformedData),
		});
		return transformResponse(response);
	},
};

/**
 * Affiliate Program API
 */
export const affiliateApi = {
	/**
	 * Join the affiliate program
	 */
	async joinProgram(request?: JoinProgramRequest): Promise<AffiliateProfile> {
		const response = await retryableApiRequest<AffiliateProfile>('/api/affiliates/join', {
			method: 'POST',
			body: JSON.stringify(request || {}),
		});
		return transformResponse(response);
	},

	/**
	 * Get affiliate profile for current user
	 */
	async getProfile(): Promise<AffiliateProfile> {
		const response = await retryableApiRequest<AffiliateProfile>('/api/affiliates/profile');
		return transformResponse(response);
	},

	/**
	 * Update affiliate profile settings
	 */
	async updateProfile(updates: UpdateAffiliateProfileRequest): Promise<AffiliateProfile> {
		const transformedData = transformRequest(updates);
		const response = await retryableApiRequest<AffiliateProfile>('/api/affiliates/profile', {
			method: 'PATCH',
			body: JSON.stringify(transformedData),
		});
		return transformResponse(response);
	},

	/**
	 * Get affiliate dashboard statistics
	 */
	async getStats(): Promise<AffiliateStats> {
		const response = await retryableApiRequest<AffiliateStats>('/api/affiliates/stats');
		return transformResponse(response);
	},

	/**
	 * Get all referral links
	 */
	async getReferralLinks(): Promise<ReferralLink[]> {
		const response = await retryableApiRequest<ReferralLink[]>('/api/affiliates/referral-links');
		return transformResponseArray(response);
	},

	/**
	 * Create custom referral link with UTM parameters
	 */
	async createReferralLink(request: CreateReferralLinkRequest): Promise<ReferralLink> {
		const transformedData = transformRequest(request);
		const response = await retryableApiRequest<ReferralLink>('/api/affiliates/referral-links', {
			method: 'POST',
			body: JSON.stringify(transformedData),
		});
		return transformResponse(response);
	},

	/**
	 * Get primary referral code and URL
	 */
	async getReferralCode(): Promise<{ referral_code: string; base_url: string; full_url: string }> {
		const response = await retryableApiRequest<{ referral_code: string; base_url: string; full_url: string }>('/api/affiliates/referral-code');
		return transformResponse(response);
	},

	/**
	 * Get list of referrals (paginated)
	 */
	async getReferrals(tier?: number, limit: number = 50, offset: number = 0): Promise<PaginatedResponse<Referral>> {
		const params = new URLSearchParams();
		if (tier) params.append('tier', tier.toString());
		params.append('limit', limit.toString());
		params.append('offset', offset.toString());

		const response = await retryableApiRequest<PaginatedResponse<Referral>>(`/api/affiliates/referrals?${params.toString()}`);
		return transformResponse(response);
	},

	/**
	 * Get network statistics
	 */
	async getNetworkStats(): Promise<NetworkStats> {
		const response = await retryableApiRequest<NetworkStats>('/api/affiliates/network/stats');
		return transformResponse(response);
	},

	/**
	 * Get network tree visualization
	 */
	async getNetworkTree(): Promise<any[]> {
		const response = await retryableApiRequest<any[]>('/api/affiliates/network/tree');
		return transformResponseArray(response);
	},

	/**
	 * Get commission records (paginated)
	 */
	async getCommissions(
		status?: 'pending' | 'approved' | 'paid' | 'cancelled',
		limit: number = 50,
		offset: number = 0
	): Promise<PaginatedResponse<CommissionRecord>> {
		const params = new URLSearchParams();
		if (status) params.append('status', status);
		params.append('limit', limit.toString());
		params.append('offset', offset.toString());

		const response = await retryableApiRequest<PaginatedResponse<CommissionRecord>>(`/api/affiliates/commissions?${params.toString()}`);
		return transformResponse(response);
	},

	/**
	 * Get pending commissions
	 */
	async getPendingCommissions(): Promise<{ pending_amount: number; pending_count: number; records: CommissionRecord[] }> {
		const response = await retryableApiRequest<{ pending_amount: number; pending_count: number; records: CommissionRecord[] }>('/api/affiliates/commissions/pending');
		return transformResponse(response);
	},

	/**
	 * Get payout history (paginated)
	 */
	async getPayouts(limit: number = 50, offset: number = 0): Promise<PaginatedResponse<PayoutRequest>> {
		const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() });
		const response = await retryableApiRequest<PaginatedResponse<PayoutRequest>>(`/api/affiliates/payouts?${params.toString()}`);
		return transformResponse(response);
	},

	/**
	 * Request payout
	 */
	async requestPayout(request: PayoutRequestCreate): Promise<PayoutRequest> {
		const transformedData = transformRequest(request);
		const response = await retryableApiRequest<PayoutRequest>('/api/affiliates/payouts/request', {
			method: 'POST',
			body: JSON.stringify(transformedData),
		});
		return transformResponse(response);
	},

	/**
	 * Track referral click (public endpoint)
	 */
	async trackReferral(referralCode: string): Promise<{ success: boolean; referral_code: string; message: string }> {
		const response = await retryableApiRequest<{ success: boolean; referral_code: string; message: string }>(
			`/api/public/track-referral?ref=${encodeURIComponent(referralCode)}`
		);
		return transformResponse(response);
	},

	/**
	 * Attribute signup to referral (internal use after user registration)
	 */
	async attributeSignup(
		userId: string,
		organizationId: string,
		referralCode: string
	): Promise<ReferralAttribution | null> {
		try {
			const response = await retryableApiRequest<ReferralAttribution>(
				'/api/affiliates/internal/attribute-signup',
				{
					method: 'POST',
					body: JSON.stringify({
						user_id: userId,
						organization_id: organizationId,
						referral_code: referralCode
					}),
				}
			);
			return transformResponse(response);
		} catch (error) {
			console.error('Failed to attribute signup:', error);
			return null;
		}
	},

	/**
	 * Get affiliate leaderboard
	 */
	async getLeaderboard(
		period: string = 'all_time',
		metric: string = 'earnings',
		limit: number = 100
	): Promise<any> {
		const params = new URLSearchParams({
			period,
			metric,
			limit: limit.toString()
		});
		const response = await retryableApiRequest<any>(`/api/affiliates/leaderboard?${params.toString()}`);
		return transformResponse(response);
	},

	/**
	 * Get current user's rank
	 */
	async getMyRank(metric: string = 'earnings'): Promise<any> {
		const params = new URLSearchParams({ metric });
		const response = await retryableApiRequest<any>(`/api/affiliates/my-rank?${params.toString()}`);
		return transformResponse(response);
	},

	/**
	 * Get conversion analytics
	 */
	async getConversionAnalytics(days: number = 30): Promise<any> {
		const params = new URLSearchParams({ days: days.toString() });
		const response = await retryableApiRequest<any>(
			`/api/affiliates/analytics/conversion-rates?${params.toString()}`
		);
		return transformResponse(response);
	},

	/**
	 * Get traffic source breakdown
	 */
	async getTrafficSources(days: number = 30): Promise<any> {
		const params = new URLSearchParams({ days: days.toString() });
		const response = await retryableApiRequest<any>(
			`/api/affiliates/analytics/traffic-sources?${params.toString()}`
		);
		return transformResponse(response);
	},

	/**
	 * Get link performance metrics
	 */
	async getLinkPerformance(days: number = 30): Promise<any> {
		const params = new URLSearchParams({ days: days.toString() });
		const response = await retryableApiRequest<any>(
			`/api/affiliates/analytics/link-performance?${params.toString()}`
		);
		return transformResponse(response);
	},

	/**
	 * Get all campaigns for current affiliate
	 */
	async getCampaigns(status?: string): Promise<any> {
		const params = status ? new URLSearchParams({ status }) : '';
		const response = await retryableApiRequest<any>(
			`/api/affiliates/campaigns${params ? '?' + params.toString() : ''}`
		);
		return transformResponse(response);
	},

	/**
	 * Get specific campaign
	 */
	async getCampaign(campaignId: string): Promise<any> {
		const response = await retryableApiRequest<any>(
			`/api/affiliates/campaigns/${campaignId}`
		);
		return transformResponse(response);
	},

	/**
	 * Create new campaign
	 */
	async createCampaign(campaignData: any): Promise<any> {
		const request = transformRequest(campaignData);
		const response = await retryableApiRequest<any>(
			'/api/affiliates/campaigns',
			{
				method: 'POST',
				body: JSON.stringify(request)
			}
		);
		return transformResponse(response);
	},

	/**
	 * Update campaign
	 */
	async updateCampaign(campaignId: string, updates: any): Promise<any> {
		const request = transformRequest(updates);
		const response = await retryableApiRequest<any>(
			`/api/affiliates/campaigns/${campaignId}`,
			{
				method: 'PATCH',
				body: JSON.stringify(request)
			}
		);
		return transformResponse(response);
	},

	/**
	 * Delete campaign
	 */
	async deleteCampaign(campaignId: string): Promise<any> {
		const response = await retryableApiRequest<any>(
			`/api/affiliates/campaigns/${campaignId}`,
			{
				method: 'DELETE'
			}
		);
		return transformResponse(response);
	},
};

/**
 * MCP Integration API
 */
export const mcpApi = {
	/**
	 * Create CRM lead
	 */
	async createCrmLead(tenantId: string, leadData: Record<string, any>): Promise<any> {
		const request = transformRequest({
			tenant_id: tenantId,
			lead_data: leadData,
		});
		const response = await coreApiRequest('/internal/mcp/crm/leads', {
			method: 'POST',
			body: JSON.stringify(request),
		});
		return transformResponse(response);
	},

	/**
	 * Update CRM contact
	 */
	async updateCrmContact(tenantId: string, contactId: string, contactData: Record<string, any>): Promise<any> {
		const request = transformRequest({
			tenant_id: tenantId,
			contact_data: contactData,
		});
		const response = await coreApiRequest(`/internal/mcp/crm/contacts/${contactId}`, {
			method: 'PUT',
			body: JSON.stringify(request),
		});
		return transformResponse(response);
	},

	/**
	 * Create helpdesk ticket
	 */
	async createHelpdeskTicket(tenantId: string, ticketData: Record<string, any>): Promise<any> {
		const request = transformRequest({
			tenant_id: tenantId,
			ticket_data: ticketData,
		});
		const response = await coreApiRequest('/internal/mcp/helpdesk/tickets', {
			method: 'POST',
			body: JSON.stringify(request),
		});
		return transformResponse(response);
	},

	/**
	 * Process payment
	 */
	async processPayment(tenantId: string, paymentData: Record<string, any>): Promise<any> {
		const request = transformRequest({
			tenant_id: tenantId,
			payment_data: paymentData,
		});
		const response = await coreApiRequest('/internal/mcp/payments/process', {
			method: 'POST',
			body: JSON.stringify(request),
		});
		return transformResponse(response);
	},

	/**
	 * Send email
	 */
	async sendEmail(tenantId: string, emailData: Record<string, any>): Promise<any> {
		const request = transformRequest({
			tenant_id: tenantId,
			email_data: emailData,
		});
		const response = await coreApiRequest('/internal/mcp/email/send', {
			method: 'POST',
			body: JSON.stringify(request),
		});
		return transformResponse(response);
	},

	/**
	 * Send SMS
	 */
	async sendSms(tenantId: string, smsData: Record<string, any>): Promise<any> {
		const request = transformRequest({
			tenant_id: tenantId,
			sms_data: smsData,
		});
		const response = await coreApiRequest('/internal/mcp/sms/send', {
			method: 'POST',
			body: JSON.stringify(request),
		});
		return transformResponse(response);
	},

	/**
	 * Create calendar event
	 */
	async createCalendarEvent(tenantId: string, eventData: Record<string, any>): Promise<any> {
		const request = transformRequest({
			tenant_id: tenantId,
			event_data: eventData,
		});
		const response = await coreApiRequest('/internal/mcp/calendar/create-event', {
			method: 'POST',
			body: JSON.stringify(request),
		});
		return transformResponse(response);
	},

	/**
	 * List calendar events
	 */
	async listCalendarEvents(tenantId: string, startDate?: string, endDate?: string): Promise<any> {
		const params = new URLSearchParams({ tenant_id: tenantId });
		if (startDate) params.append('start_date', startDate);
		if (endDate) params.append('end_date', endDate);

		const response = await coreApiRequest(`/internal/mcp/calendar/events?${params.toString()}`);
		return transformResponse(response);
	},

	/**
	 * Upload document
	 */
	async uploadDocument(tenantId: string, documentData: Record<string, any>): Promise<any> {
		const request = transformRequest({
			tenant_id: tenantId,
			document_data: documentData,
		});
		const response = await coreApiRequest('/internal/mcp/documents/upload', {
			method: 'POST',
			body: JSON.stringify(request),
		});
		return transformResponse(response);
	},

	/**
	 * List documents
	 */
	async listDocuments(tenantId: string, folderId?: string): Promise<any> {
		const params = new URLSearchParams({ tenant_id: tenantId });
		if (folderId) params.append('folder_id', folderId);

		const response = await coreApiRequest(`/internal/mcp/documents/list?${params.toString()}`);
		return transformResponse(response);
	},

	/**
	 * Track analytics event
	 */
	async trackAnalytics(tenantId: string, analyticsData: Record<string, any>): Promise<any> {
		const request = transformRequest({
			tenant_id: tenantId,
			analytics_data: analyticsData,
		});
		const response = await coreApiRequest('/internal/mcp/analytics/track', {
			method: 'POST',
			body: JSON.stringify(request),
		});
		return transformResponse(response);
	},

	/**
	 * Get analytics report
	 */
	async getAnalyticsReport(tenantId: string, reportType: string, startDate?: string, endDate?: string): Promise<any> {
		const params = new URLSearchParams({
			tenant_id: tenantId,
			report_type: reportType
		});
		if (startDate) params.append('start_date', startDate);
		if (endDate) params.append('end_date', endDate);

		const response = await coreApiRequest(`/internal/mcp/analytics/report?${params.toString()}`);
		return transformResponse(response);
	},

	/**
	 * Generate AI content
	 */
	async generateAiContent(tenantId: string, generationData: Record<string, any>): Promise<any> {
		return coreApiRequest('/internal/mcp/ai/generate', {
			method: 'POST',
			body: JSON.stringify({
				tenant_id: tenantId,
				generation_data: generationData,
			}),
		});
	},

	/**
	 * Analyze with AI
	 */
	async analyzeWithAi(tenantId: string, analysisData: Record<string, any>): Promise<any> {
		return coreApiRequest('/internal/mcp/ai/analyze', {
			method: 'POST',
			body: JSON.stringify({
				tenant_id: tenantId,
				analysis_data: analysisData,
			}),
		});
	},
};

/**
 * Industry Module API
 */
export const industryModuleApi = {
	/**
	 * Initialize an industry module for a tenant
	 */
	async initializeModule(
		tenantId: string,
		industry: string,
		settings: Record<string, any>
	): Promise<{ status: string; module_id: string; capabilities: IndustryModuleCapability[] }> {
		const response = await retryableApiRequest(`/internal/modules/${industry}/initialize`, {
			method: 'POST',
			body: JSON.stringify({
				tenant_id: tenantId,
				settings: settings,
			}),
		});
		return transformResponse(response);
	},

	/**
	 * Execute a module capability
	 */
	async executeModuleCapability(
		tenantId: string,
		industry: string,
		capability: string,
		params: Record<string, any>
	): Promise<any> {
		const response = await retryableApiRequest(`/internal/modules/${industry}/capabilities/${capability}/execute`, {
			method: 'POST',
			body: JSON.stringify({
				tenant_id: tenantId,
				parameters: params,
			}),
		});
		return transformResponse(response);
	},

	/**
	 * Execute a module workflow
	 */
	async executeModuleWorkflow(
		tenantId: string,
		industry: string,
		workflow: string,
		params: Record<string, any>
	): Promise<any> {
		const response = await retryableApiRequest(`/internal/modules/${industry}/workflows/${workflow}/execute`, {
			method: 'POST',
			body: JSON.stringify({
				tenant_id: tenantId,
				parameters: params,
			}),
		});
		return transformResponse(response);
	},

	/**
	 * Get industry analytics
	 */
	async getIndustryAnalytics(
		tenantId: string,
		industry: string,
		metrics: string[],
		timeRange: string = '7d',
		filters?: Record<string, any>
	): Promise<IndustryModuleAnalytics> {
		const params = new URLSearchParams({
			tenant_id: tenantId,
			metrics: metrics.join(','),
			time_range: timeRange,
		});
		if (filters) {
			params.append('filters', JSON.stringify(filters));
		}

		const response = await retryableApiRequest<IndustryModuleAnalytics>(`/internal/modules/${industry}/analytics?${params.toString()}`);
		return transformResponse(response);
	},

	/**
	 * Get module capabilities
	 */
	async getModuleCapabilities(tenantId: string, industry: string): Promise<IndustryModuleCapability[]> {
		const params = new URLSearchParams({ tenant_id: tenantId });
		const response = await retryableApiRequest<IndustryModuleCapability[]>(`/internal/modules/${industry}/capabilities?${params.toString()}`);
		return transformResponseArray(response);
	},

	/**
	 * Get module workflows
	 */
	async getModuleWorkflows(tenantId: string, industry: string): Promise<IndustryModuleWorkflow[]> {
		const params = new URLSearchParams({ tenant_id: tenantId });
		const response = await retryableApiRequest<IndustryModuleWorkflow[]>(`/internal/modules/${industry}/workflows?${params.toString()}`);
		return transformResponseArray(response);
	},

	/**
	 * Get module compliance information
	 */
	async getModuleCompliance(tenantId: string, industry: string): Promise<IndustryModuleCompliance> {
		const params = new URLSearchParams({ tenant_id: tenantId });
		const response = await retryableApiRequest<IndustryModuleCompliance>(`/internal/modules/${industry}/compliance?${params.toString()}`);
		return transformResponse(response);
	},

	/**
	 * Get module health status
	 */
	async getModuleHealth(tenantId: string, industry: string): Promise<IndustryModuleHealth> {
		const params = new URLSearchParams({ tenant_id: tenantId });
		const response = await retryableApiRequest<IndustryModuleHealth>(`/internal/modules/${industry}/health?${params.toString()}`);
		return transformResponse(response);
	},

	/**
	 * Get available industries
	 */
	async getAvailableIndustries(): Promise<Array<{ id: string; name: string; description: string; capabilities: string[] }>> {
		const response = await retryableApiRequest<Array<{ id: string; name: string; description: string; capabilities: string[] }>>('/internal/modules/available');
		return transformResponseArray(response);
	},
};

/**
 * Health check
 */
export const healthApi = {
	/**
	 * Check Core Backend health
	 */
	async check(): Promise<{ status: string }> {
		return coreApiRequest<{ status: string }>('/health');
	},
};

// Export all APIs
export const coreApi = {
	assistant: assistantApi,
	campaign: campaignApi,
	knowledgeBase: knowledgeBaseApi,
	license: licenseApi,
	usage: usageApi,
	payment: paymentApi,
	affiliate: affiliateApi,
	mcp: mcpApi,
	industryModule: industryModuleApi,
	health: healthApi,
};

// Convenience exports for commonly used functions
export const {
	createAssistant,
	getAssistants,
	getAssistant,
	updateAssistant,
	deleteAssistant,
} = assistantApi;

export const {
        createCampaign,
        getCampaigns,
        getCampaign,
        start: startCampaign,
        pause: pauseCampaign,
        resume: resumeCampaign,
        stop: stopCampaign,
} = campaignApi;

export const {
	searchKnowledgeBase,
	addKnowledgeSource,
	getKnowledgeSources,
} = knowledgeBaseApi;

export const {
	getLicenseInfo,
	checkFeatureAccess,
} = licenseApi;

export const {
	getUsageData,
	getUsageSummary,
} = usageApi;

export const {
	createStripeCheckout,
	verifyMobileMoneyPayment,
	getWalletBalance,
} = paymentApi;
