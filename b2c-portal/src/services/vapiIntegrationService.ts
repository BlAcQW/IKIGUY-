/**
 * VAPI Integration Service
 *
 * Comprehensive service for managing VAPI voice assistant integration
 * including assistant management, call initiation, real-time monitoring,
 * and testing framework for voice campaigns.
 */

interface VAPIAssistant {
  id: string;
  name: string;
  firstMessage: string;
  model: {
    provider: string;
    model: string;
    temperature: number;
    systemPrompt: string;
  };
  voice: {
    provider: string;
    voiceId: string;
  };
  functions?: Array<{
    name: string;
    description: string;
    parameters: Record<string, any>;
  }>;
  serverUrl?: string;
  serverUrlSecret?: string;
}

interface VAPICall {
  id: string;
  assistantId: string;
  phoneNumberId: string;
  customer: {
    number: string;
    name?: string;
    company?: string;
  };
  status: 'queued' | 'ringing' | 'in-progress' | 'forwarding' | 'ended';
  startedAt?: string;
  endedAt?: string;
  endedReason?: string;
  cost?: number;
  transcript?: string;
  recordingUrl?: string;
  analysis?: {
    summary: string;
    sentiment: string;
    outcome: Record<string, any>;
    quality_score: number;
  };
  metadata?: Record<string, any>;
}

interface TestResult {
  success: boolean;
  callId?: string;
  duration?: number;
  transcript?: string;
  outcome?: Record<string, any>;
  error?: string;
  qualityScore?: number;
}

interface CampaignTestSuite {
  campaignId: string;
  testContacts: Array<{
    phoneNumber: string;
    expectedOutcome: string;
    metadata?: Record<string, any>;
  }>;
  testCriteria: {
    minConnectionRate: number;
    minCompletionRate: number;
    maxErrorRate: number;
    minQualityScore: number;
  };
  results: TestResult[];
  summary: {
    totalTests: number;
    successful: number;
    failed: number;
    avgDuration: number;
    avgQualityScore: number;
    passed: boolean;
  };
}

export class VAPIIntegrationService {
  private static readonly VAPI_API_BASE = 'https://api.vapi.ai';
  private static readonly API_KEY = import.meta.env.VITE_VAPI_API_KEY || '42cf1e7c-2ef9-4bd7-ba30-52f2813605a2';

  private activeCalls: Map<string, VAPICall> = new Map();
  private testSuites: Map<string, CampaignTestSuite> = new Map();

  /**
   * Get assistant details from VAPI
   */
  async getAssistant(assistantId: string): Promise<VAPIAssistant> {
    try {
      const response = await fetch(`${VAPIIntegrationService.VAPI_API_BASE}/assistant/${assistantId}`, {
        headers: {
          'Authorization': `Bearer ${VAPIIntegrationService.API_KEY}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch assistant: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get assistant:', error);
      throw error;
    }
  }

  /**
   * List all available assistants
   */
  async listAssistants(): Promise<VAPIAssistant[]> {
    try {
      const response = await fetch(`${VAPIIntegrationService.VAPI_API_BASE}/assistant`, {
        headers: {
          'Authorization': `Bearer ${VAPIIntegrationService.API_KEY}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to list assistants: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to list assistants:', error);
      throw error;
    }
  }

  /**
   * Create a new assistant
   */
  async createAssistant(config: Partial<VAPIAssistant>): Promise<VAPIAssistant> {
    try {
      const response = await fetch(`${VAPIIntegrationService.VAPI_API_BASE}/assistant`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${VAPIIntegrationService.API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });

      if (!response.ok) {
        throw new Error(`Failed to create assistant: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to create assistant:', error);
      throw error;
    }
  }

  /**
   * Update existing assistant
   */
  async updateAssistant(assistantId: string, updates: Partial<VAPIAssistant>): Promise<VAPIAssistant> {
    try {
      const response = await fetch(`${VAPIIntegrationService.VAPI_API_BASE}/assistant/${assistantId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${VAPIIntegrationService.API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      });

      if (!response.ok) {
        throw new Error(`Failed to update assistant: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to update assistant:', error);
      throw error;
    }
  }

  /**
   * Initiate a voice call
   */
  async initiateCall(
    assistantId: string,
    phoneNumberId: string,
    customerNumber: string,
    metadata?: Record<string, any>
  ): Promise<VAPICall> {
    try {
      const callPayload = {
        assistantId,
        phoneNumberId,
        customer: {
          number: customerNumber
        },
        metadata: {
          campaign_initiated: true,
          timestamp: new Date().toISOString(),
          ...metadata
        }
      };

      const response = await fetch(`${VAPIIntegrationService.VAPI_API_BASE}/call`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${VAPIIntegrationService.API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(callPayload)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`Failed to initiate call: ${response.status} ${response.statusText} - ${JSON.stringify(errorData)}`);
      }

      const call = await response.json();

      // Store call for tracking
      this.activeCalls.set(call.id, call);

      // Start monitoring call status
      this.monitorCall(call.id);

      return call;
    } catch (error) {
      console.error('Failed to initiate call:', error);
      throw error;
    }
  }

  /**
   * Get call details
   */
  async getCall(callId: string): Promise<VAPICall> {
    try {
      const response = await fetch(`${VAPIIntegrationService.VAPI_API_BASE}/call/${callId}`, {
        headers: {
          'Authorization': `Bearer ${VAPIIntegrationService.API_KEY}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to get call: ${response.status} ${response.statusText}`);
      }

      const call = await response.json();

      // Update stored call data
      if (this.activeCalls.has(callId)) {
        this.activeCalls.set(callId, call);
      }

      return call;
    } catch (error) {
      console.error('Failed to get call:', error);
      throw error;
    }
  }

  /**
   * List calls with optional filtering
   */
  async listCalls(filters?: {
    assistantId?: string;
    phoneNumberId?: string;
    status?: string;
    limit?: number;
  }): Promise<VAPICall[]> {
    try {
      const searchParams = new URLSearchParams();
      if (filters?.assistantId) searchParams.append('assistantId', filters.assistantId);
      if (filters?.phoneNumberId) searchParams.append('phoneNumberId', filters.phoneNumberId);
      if (filters?.status) searchParams.append('status', filters.status);
      if (filters?.limit) searchParams.append('limit', filters.limit.toString());

      const url = `${VAPIIntegrationService.VAPI_API_BASE}/call${searchParams.toString() ? '?' + searchParams.toString() : ''}`;

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${VAPIIntegrationService.API_KEY}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to list calls: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to list calls:', error);
      throw error;
    }
  }

  /**
   * Monitor call status in real-time
   */
  private async monitorCall(callId: string): Promise<void> {
    const checkInterval = 5000; // Check every 5 seconds
    const maxChecks = 60; // Maximum 5 minutes of monitoring
    let checks = 0;

    const monitor = setInterval(async () => {
      checks++;

      try {
        const call = await this.getCall(callId);

        if (call.status === 'ended' || checks >= maxChecks) {
          clearInterval(monitor);
          this.activeCalls.delete(callId);

          // Trigger completion handlers if any
          this.handleCallCompleted(call);
        }
      } catch (error) {
        console.error(`Failed to monitor call ${callId}:`, error);
        if (checks >= maxChecks) {
          clearInterval(monitor);
          this.activeCalls.delete(callId);
        }
      }
    }, checkInterval);
  }

  /**
   * Handle call completion
   */
  private handleCallCompleted(call: VAPICall): void {
    console.log(`Call ${call.id} completed with status: ${call.status}, reason: ${call.endedReason}`);

    // Emit custom event for call completion
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('vapiCallCompleted', {
        detail: { call }
      }));
    }
  }

  /**
   * Create and run test suite for campaign
   */
  async runCampaignTest(
    campaignId: string,
    assistantId: string,
    phoneNumberId: string,
    testConfig: {
      testContacts: Array<{
        phoneNumber: string;
        expectedOutcome: string;
        metadata?: Record<string, any>;
      }>;
      testCriteria: {
        minConnectionRate: number;
        minCompletionRate: number;
        maxErrorRate: number;
        minQualityScore: number;
      };
    }
  ): Promise<CampaignTestSuite> {
    const testSuite: CampaignTestSuite = {
      campaignId,
      testContacts: testConfig.testContacts,
      testCriteria: testConfig.testCriteria,
      results: [],
      summary: {
        totalTests: testConfig.testContacts.length,
        successful: 0,
        failed: 0,
        avgDuration: 0,
        avgQualityScore: 0,
        passed: false
      }
    };

    console.log(`Starting campaign test for ${campaignId} with ${testConfig.testContacts.length} contacts`);

    // Run tests sequentially to avoid rate limiting
    for (const testContact of testConfig.testContacts) {
      try {
        console.log(`Testing call to ${testContact.phoneNumber}`);

        const call = await this.initiateCall(
          assistantId,
          phoneNumberId,
          testContact.phoneNumber,
          {
            test_mode: true,
            expected_outcome: testContact.expectedOutcome,
            campaign_id: campaignId,
            ...testContact.metadata
          }
        );

        // Wait for call to complete
        const result = await this.waitForCallCompletion(call.id, 300000); // 5 minute timeout

        const testResult: TestResult = {
          success: result.status === 'ended' && result.endedReason !== 'assistant-error',
          callId: result.id,
          duration: result.endedAt && result.startedAt
            ? new Date(result.endedAt).getTime() - new Date(result.startedAt).getTime()
            : 0,
          transcript: result.transcript,
          outcome: result.analysis?.outcome || {},
          qualityScore: result.analysis?.quality_score || 0
        };

        testSuite.results.push(testResult);

        if (testResult.success) {
          testSuite.summary.successful++;
        } else {
          testSuite.summary.failed++;
        }

        // Wait between calls to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 2000));

      } catch (error) {
        console.error(`Test call failed for ${testContact.phoneNumber}:`, error);

        const testResult: TestResult = {
          success: false,
          error: error.message
        };

        testSuite.results.push(testResult);
        testSuite.summary.failed++;
      }
    }

    // Calculate summary metrics
    const successfulResults = testSuite.results.filter(r => r.success);
    testSuite.summary.avgDuration = successfulResults.length > 0
      ? successfulResults.reduce((sum, r) => sum + (r.duration || 0), 0) / successfulResults.length
      : 0;

    testSuite.summary.avgQualityScore = successfulResults.length > 0
      ? successfulResults.reduce((sum, r) => sum + (r.qualityScore || 0), 0) / successfulResults.length
      : 0;

    // Evaluate test criteria
    const connectionRate = (testSuite.summary.successful / testSuite.summary.totalTests) * 100;
    const errorRate = (testSuite.summary.failed / testSuite.summary.totalTests) * 100;

    testSuite.summary.passed =
      connectionRate >= testConfig.testCriteria.minConnectionRate &&
      errorRate <= testConfig.testCriteria.maxErrorRate &&
      testSuite.summary.avgQualityScore >= testConfig.testCriteria.minQualityScore;

    // Store test suite
    this.testSuites.set(campaignId, testSuite);

    console.log(`Campaign test completed. Passed: ${testSuite.summary.passed}`);

    return testSuite;
  }

  /**
   * Wait for call completion with timeout
   */
  private async waitForCallCompletion(callId: string, timeout: number = 300000): Promise<VAPICall> {
    const startTime = Date.now();
    const checkInterval = 5000;

    return new Promise((resolve, reject) => {
      const check = async () => {
        try {
          const call = await this.getCall(callId);

          if (call.status === 'ended') {
            resolve(call);
            return;
          }

          if (Date.now() - startTime >= timeout) {
            reject(new Error(`Call ${callId} timed out after ${timeout}ms`));
            return;
          }

          setTimeout(check, checkInterval);
        } catch (error) {
          reject(error);
        }
      };

      check();
    });
  }

  /**
   * Get test suite results
   */
  getTestSuite(campaignId: string): CampaignTestSuite | undefined {
    return this.testSuites.get(campaignId);
  }

  /**
   * List all active calls
   */
  getActiveCalls(): VAPICall[] {
    return Array.from(this.activeCalls.values());
  }

  /**
   * Get call analytics
   */
  getCallAnalytics(timeframe: '1h' | '24h' | '7d' | '30d' = '24h'): Promise<{
    totalCalls: number;
    successfulCalls: number;
    failedCalls: number;
    avgDuration: number;
    avgCost: number;
    outcomeBreakdown: Record<string, number>;
  }> {
    // In real implementation, this would query the analytics database
    // For now, return mock data based on stored calls
    const calls = Array.from(this.activeCalls.values());

    const analytics = {
      totalCalls: calls.length,
      successfulCalls: calls.filter(c => c.status === 'ended' && c.endedReason !== 'assistant-error').length,
      failedCalls: calls.filter(c => c.status === 'ended' && c.endedReason === 'assistant-error').length,
      avgDuration: calls.length > 0
        ? calls.reduce((sum, c) => {
            if (c.startedAt && c.endedAt) {
              return sum + (new Date(c.endedAt).getTime() - new Date(c.startedAt).getTime());
            }
            return sum;
          }, 0) / calls.length
        : 0,
      avgCost: calls.length > 0
        ? calls.reduce((sum, c) => sum + (c.cost || 0), 0) / calls.length
        : 0,
      outcomeBreakdown: {}
    };

    return Promise.resolve(analytics);
  }

  /**
   * Validate assistant configuration
   */
  async validateAssistantConfig(assistantId: string): Promise<{
    valid: boolean;
    issues: string[];
    recommendations: string[];
  }> {
    try {
      const assistant = await this.getAssistant(assistantId);
      const issues: string[] = [];
      const recommendations: string[] = [];

      // Check required fields
      if (!assistant.firstMessage || assistant.firstMessage.length < 10) {
        issues.push('First message is too short or missing');
      }

      if (!assistant.model?.systemPrompt || assistant.model.systemPrompt.length < 50) {
        issues.push('System prompt is too short or missing');
      }

      if (!assistant.voice?.voiceId) {
        issues.push('Voice configuration is missing');
      }

      // Check optimal settings
      if (assistant.model?.temperature > 0.8) {
        recommendations.push('Consider lowering temperature for more consistent responses');
      }

      if (assistant.firstMessage && assistant.firstMessage.length > 200) {
        recommendations.push('Consider shortening first message for better engagement');
      }

      if (!assistant.functions || assistant.functions.length === 0) {
        recommendations.push('Consider adding functions for enhanced interactivity');
      }

      return {
        valid: issues.length === 0,
        issues,
        recommendations
      };

    } catch (error) {
      return {
        valid: false,
        issues: [`Failed to validate assistant: ${error.message}`],
        recommendations: []
      };
    }
  }

  /**
   * Test assistant with a simple call
   */
  async testAssistant(
    assistantId: string,
    phoneNumberId: string,
    testPhoneNumber: string = import.meta.env.VITE_TEST_PHONE_NUMBER || '+12397783680'
  ): Promise<TestResult> {
    try {
      console.log(`Testing assistant ${assistantId} with call to ${testPhoneNumber}`);

      const call = await this.initiateCall(
        assistantId,
        phoneNumberId,
        testPhoneNumber,
        {
          test_mode: true,
          test_type: 'assistant_validation'
        }
      );

      // Wait for call to complete (shorter timeout for test)
      const result = await this.waitForCallCompletion(call.id, 120000); // 2 minute timeout

      return {
        success: result.status === 'ended' && result.endedReason !== 'assistant-error',
        callId: result.id,
        duration: result.endedAt && result.startedAt
          ? new Date(result.endedAt).getTime() - new Date(result.startedAt).getTime()
          : 0,
        transcript: result.transcript,
        outcome: result.analysis?.outcome || {},
        qualityScore: result.analysis?.quality_score || 0
      };

    } catch (error) {
      console.error('Assistant test failed:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }
}

// Export singleton instance
export const vapiIntegrationService = new VAPIIntegrationService();
export default vapiIntegrationService;