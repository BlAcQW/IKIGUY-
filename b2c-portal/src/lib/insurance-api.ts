/**
 * Insurance Module API Client for B2C Portal
 *
 * This service layer connects the B2C Portal frontend to the Core Backend's
 * insurance industry module APIs for comprehensive automation capabilities.
 */

import { getAuthHeaders as getMongoAuthHeaders } from '@/lib/auth-utils';
import { createRetryWrapper, RETRY_CONFIGS } from '@/lib/retry-logic.ts';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


// Core Backend API configuration
const CORE_API_BASE_URL = import.meta.env.VITE_CORE_API_URL || API_BASE_URL;
const CORE_API_TIMEOUT = 30000; // 30 seconds

// Types for Insurance Module API
export interface InsuranceApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    request_id?: string;
  };
}

export interface InsuranceCapability {
  name: string;
  description: string;
  enabled: boolean;
  settings: {
    category: string;
    requires_auth: boolean;
    parameters: string[];
  };
}

export interface InsuranceWorkflow {
  workflow_id: string;
  name: string;
  description: string;
  enabled: boolean;
  steps: WorkflowStep[];
}

export interface WorkflowStep {
  type: string;
  config: Record<string, any>;
  params?: Record<string, any>;
  duration?: number;
}

export interface InsuranceAnalytics {
  policy_analytics: {
    total_policies: number;
    active_policies: number;
    renewal_rate: number;
    average_premium: number;
  };
  claims_analytics: {
    total_claims: number;
    pending_claims: number;
    average_processing_time: number;
    approval_rate: number;
  };
  customer_analytics: {
    total_customers: number;
    average_policies_per_customer: number;
    customer_satisfaction_score: number;
  };
  risk_analytics: {
    average_risk_score: number;
    fraud_detection_rate: number;
    loss_ratio: number;
  };
}

export interface ComplianceInfo {
  insurance_compliance: {
    status: string;
    last_audit: string;
    next_audit: string;
    regulatory_requirements: string[];
  };
}

// Core API client class
class InsuranceApiClient {
  private baseUrl: string;
  private timeout: number;

  constructor() {
    this.baseUrl = CORE_API_BASE_URL;
    this.timeout = CORE_API_TIMEOUT;
  }

  /**
   * Get authorization headers with MongoDB auth token
   */
  private async getAuthHeaders(): Promise<Record<string, string>> {
    const authHeaders = await getMongoAuthHeaders();

    return {
      'Content-Type': 'application/json',
      ...authHeaders,
    };
  }

  /**
   * Make authenticated API request
   */
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<InsuranceApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = await this.getAuthHeaders();

    const response = await fetch(url, {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
      signal: AbortSignal.timeout(this.timeout),
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Initialize insurance module for current tenant
   */
  async initializeModule(settings: Record<string, any> = {}): Promise<InsuranceApiResponse> {
    return this.makeRequest('/internal/modules/insurance/initialize', {
      method: 'POST',
      body: JSON.stringify({
        settings,
        tenant_config: {}
      }),
    });
  }

  /**
   * Get available insurance capabilities
   */
  async getCapabilities(): Promise<InsuranceApiResponse<InsuranceCapability[]>> {
    return this.makeRequest('/internal/modules/insurance/capabilities');
  }

  /**
   * Execute specific insurance capability
   */
  async executeCapability(
    capability: string,
    params: Record<string, any>,
    context?: Record<string, any>
  ): Promise<InsuranceApiResponse> {
    return this.makeRequest(`/internal/modules/insurance/capabilities/${capability}/execute`, {
      method: 'POST',
      body: JSON.stringify({
        params,
        context: context || {}
      }),
    });
  }

  /**
   * Get available insurance workflows
   */
  async getWorkflows(): Promise<InsuranceApiResponse<InsuranceWorkflow[]>> {
    return this.makeRequest('/internal/modules/insurance/workflows');
  }

  /**
   * Execute specific insurance workflow
   */
  async executeWorkflow(
    workflow: string,
    params: Record<string, any>,
    context?: Record<string, any>
  ): Promise<InsuranceApiResponse> {
    return this.makeRequest(`/internal/modules/insurance/workflows/${workflow}/execute`, {
      method: 'POST',
      body: JSON.stringify({
        params,
        context: context || {}
      }),
    });
  }

  /**
   * Get insurance analytics
   */
  async getAnalytics(
    metrics: string[] = ['policy_analytics', 'claims_analytics', 'customer_analytics', 'risk_analytics'],
    timeRange: string = '7d',
    filters?: Record<string, any>
  ): Promise<InsuranceApiResponse<InsuranceAnalytics>> {
    const queryParams = new URLSearchParams();
    metrics.forEach(metric => queryParams.append('metrics', metric));
    queryParams.append('time_range', timeRange);
    if (filters) {
      queryParams.append('filters', JSON.stringify(filters));
    }

    return this.makeRequest(`/internal/modules/insurance/analytics?${queryParams.toString()}`);
  }

  /**
   * Get compliance information
   */
  async getCompliance(): Promise<InsuranceApiResponse<ComplianceInfo>> {
    return this.makeRequest('/internal/modules/insurance/compliance');
  }

  /**
   * Get integration points
   */
  async getIntegrations(): Promise<InsuranceApiResponse> {
    return this.makeRequest('/internal/modules/insurance/integrations');
  }

  /**
   * Get module health status
   */
  async getHealth(): Promise<InsuranceApiResponse> {
    return this.makeRequest('/internal/modules/insurance/health');
  }

  // Convenience methods for specific insurance operations

  /**
   * Process a new insurance claim
   */
  async processClaim(claimData: {
    policy_id: string;
    customer_id: string;
    claim_type: string;
    claim_amount: number;
    incident_date: string;
  }): Promise<InsuranceApiResponse> {
    return this.executeCapability('claims_processing', {
      action: 'process',
      claim_data: claimData
    });
  }

  /**
   * Assess customer risk
   */
  async assessRisk(customerData: {
    customer_id: string;
    age?: number;
    location?: string;
    history?: Record<string, any>;
  }): Promise<InsuranceApiResponse> {
    return this.executeCapability('risk_assessment', {
      action: 'assess',
      customer_data: customerData
    });
  }

  /**
   * Create new insurance policy
   */
  async createPolicy(policyData: {
    customer_id: string;
    policy_type: string;
    coverage_amount: number;
    premium_amount: number;
    start_date: string;
    end_date: string;
  }): Promise<InsuranceApiResponse> {
    return this.executeCapability('policy_management', {
      action: 'create',
      policy_data: policyData
    });
  }

  /**
   * Analyze claim for fraud
   */
  async analyzeFraud(claimId: string): Promise<InsuranceApiResponse> {
    return this.executeCapability('fraud_detection', {
      action: 'analyze',
      claim_id: claimId
    });
  }

  /**
   * Schedule medical exam
   */
  async scheduleMedicalExam(customerId: string, scheduleData: {
    exam_date: string;
    location: string;
    exam_type?: string;
  }): Promise<InsuranceApiResponse> {
    return this.executeCapability('medical_exam_scheduling', {
      action: 'schedule',
      customer_id: customerId,
      schedule_data: scheduleData
    });
  }

  /**
   * Generate rate quote
   */
  async generateQuote(customerId: string, quoteData: {
    coverage_type: string;
    coverage_amount: number;
    term?: string;
  }): Promise<InsuranceApiResponse> {
    return this.executeCapability('rate_quotes', {
      action: 'generate',
      customer_id: customerId,
      quote_data: quoteData
    });
  }

  /**
   * Process premium payment
   */
  async processPremiumPayment(policyId: string, paymentData: {
    amount: number;
    payment_method: string;
    payment_date?: string;
  }): Promise<InsuranceApiResponse> {
    return this.executeCapability('premium_collection', {
      action: 'collect',
      policy_id: policyId,
      payment_data: paymentData
    });
  }

  /**
   * Send customer communication
   */
  async sendCustomerCommunication(customerId: string, messageType: string, messageData?: Record<string, any>): Promise<InsuranceApiResponse> {
    return this.executeCapability('customer_communication', {
      customer_id: customerId,
      message_type: messageType,
      message_data: messageData || {}
    });
  }

  /**
   * Process and manage documents
   */
  async processDocument(documentId: string, documentData: {
    document_type: string;
    content?: string;
    metadata?: Record<string, any>;
  }): Promise<InsuranceApiResponse> {
    return this.executeCapability('document_management', {
      action: 'process',
      document_id: documentId,
      document_data: documentData
    });
  }

  /**
   * Verify document authenticity
   */
  async verifyDocument(documentId: string): Promise<InsuranceApiResponse> {
    return this.executeCapability('document_management', {
      action: 'verify',
      document_id: documentId
    });
  }

  /**
   * Generate comprehensive rate quote with market comparison
   */
  async generateComprehensiveQuote(customerId: string, quoteData: {
    coverage_type: string;
    coverage_amount: number;
    term?: string;
    additional_coverage?: string[];
    compare_market?: boolean;
  }): Promise<InsuranceApiResponse> {
    return this.executeCapability('rate_quotes', {
      action: 'generate',
      customer_id: customerId,
      quote_data: quoteData
    });
  }

  /**
   * Setup customer communication hub profile
   */
  async setupCommunicationProfile(customerId: string, preferences: {
    preferred_channels: string[];
    communication_frequency: string;
    opt_out_types?: string[];
    language?: string;
  }): Promise<InsuranceApiResponse> {
    return this.executeCapability('customer_communication', {
      action: 'setup_profile',
      customer_id: customerId,
      preferences: preferences
    });
  }

  /**
   * Orchestrate multi-channel communication
   */
  async orchestrateMultiChannelMessage(customerId: string, messageData: {
    message_type: string;
    content: string;
    channels: string[];
    priority?: string;
    schedule?: string;
  }): Promise<InsuranceApiResponse> {
    return this.executeCapability('customer_communication', {
      action: 'orchestrate_messaging',
      customer_id: customerId,
      message_data: messageData
    });
  }
}

// Create retry-wrapped version of the API client
const insuranceApiClient = new InsuranceApiClient();

// Export retry-wrapped methods
export const insuranceApi = {
  // Module management
  initializeModule: createRetryWrapper(
    insuranceApiClient.initializeModule.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  getCapabilities: createRetryWrapper(
    insuranceApiClient.getCapabilities.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  executeCapability: createRetryWrapper(
    insuranceApiClient.executeCapability.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  getWorkflows: createRetryWrapper(
    insuranceApiClient.getWorkflows.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  executeWorkflow: createRetryWrapper(
    insuranceApiClient.executeWorkflow.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  // Analytics and reporting
  getAnalytics: createRetryWrapper(
    insuranceApiClient.getAnalytics.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  getCompliance: createRetryWrapper(
    insuranceApiClient.getCompliance.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  getIntegrations: createRetryWrapper(
    insuranceApiClient.getIntegrations.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  getHealth: createRetryWrapper(
    insuranceApiClient.getHealth.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  // Convenience methods
  processClaim: createRetryWrapper(
    insuranceApiClient.processClaim.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  assessRisk: createRetryWrapper(
    insuranceApiClient.assessRisk.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  createPolicy: createRetryWrapper(
    insuranceApiClient.createPolicy.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  analyzeFraud: createRetryWrapper(
    insuranceApiClient.analyzeFraud.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  scheduleMedicalExam: createRetryWrapper(
    insuranceApiClient.scheduleMedicalExam.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  generateQuote: createRetryWrapper(
    insuranceApiClient.generateQuote.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  processPremiumPayment: createRetryWrapper(
    insuranceApiClient.processPremiumPayment.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  sendCustomerCommunication: createRetryWrapper(
    insuranceApiClient.sendCustomerCommunication.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  // New convenience methods
  processDocument: createRetryWrapper(
    insuranceApiClient.processDocument.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  verifyDocument: createRetryWrapper(
    insuranceApiClient.verifyDocument.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  generateComprehensiveQuote: createRetryWrapper(
    insuranceApiClient.generateComprehensiveQuote.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  setupCommunicationProfile: createRetryWrapper(
    insuranceApiClient.setupCommunicationProfile.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),

  orchestrateMultiChannelMessage: createRetryWrapper(
    insuranceApiClient.orchestrateMultiChannelMessage.bind(insuranceApiClient),
    RETRY_CONFIGS.api
  ),
};

export default insuranceApi;