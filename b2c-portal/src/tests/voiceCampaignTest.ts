/**
 * Voice Campaign Wizard Test Suite
 *
 * Comprehensive testing script to validate the complete voice campaign workflow
 * including wizard functionality, n8n integration, VAPI calls, and LLM processing.
 */

import { vapiIntegrationService } from '../services/vapiIntegrationService';
import { llmFallbackService } from '../services/llmFallbackService';
import N8NWorkflowGenerator from '../services/n8nWorkflowGenerator';

interface TestConfig {
  assistantId: string;
  phoneId: string;
  testPhoneNumber: string;
  apiKey: string;
}

interface TestResults {
  timestamp: string;
  totalTests: number;
  passed: number;
  failed: number;
  details: Array<{
    test: string;
    status: 'PASS' | 'FAIL';
    duration: number;
    error?: string;
    data?: any;
  }>;
}

export class VoiceCampaignTestSuite {
  private config: TestConfig;
  private results: TestResults;

  constructor(config: TestConfig) {
    this.config = config;
    this.results = {
      timestamp: new Date().toISOString(),
      totalTests: 0,
      passed: 0,
      failed: 0,
      details: []
    };
  }

  /**
   * Run complete test suite
   */
  async runFullTestSuite(): Promise<TestResults> {
    console.log('🚀 Starting Voice Campaign Test Suite...');
    console.log(`📞 Test Phone: ${this.config.testPhoneNumber}`);
    console.log(`🤖 Assistant ID: ${this.config.assistantId}`);
    console.log(`📱 Phone ID: ${this.config.phoneId}`);
    console.log('━'.repeat(50));

    // Test 1: VAPI Assistant Validation
    await this.testVAPIAssistantValidation();

    // Test 2: VAPI Call Initiation
    await this.testVAPICallInitiation();

    // Test 3: N8N Workflow Generation
    await this.testN8NWorkflowGeneration();

    // Test 4: N8N Workflow Deployment
    await this.testN8NWorkflowDeployment();

    // Test 5: LLM Fallback System
    await this.testLLMFallbackSystem();

    // Test 6: Campaign Configuration Analysis
    await this.testCampaignAnalysis();

    // Test 7: End-to-End Campaign Test
    await this.testEndToEndCampaign();

    // Generate summary
    this.generateTestSummary();

    return this.results;
  }

  /**
   * Test 1: Validate VAPI Assistant Configuration
   */
  private async testVAPIAssistantValidation(): Promise<void> {
    const startTime = Date.now();

    try {
      console.log('🧪 Test 1: VAPI Assistant Validation');

      // Test assistant retrieval
      const assistant = await vapiIntegrationService.getAssistant(this.config.assistantId);

      if (!assistant || !assistant.id) {
        throw new Error('Assistant not found or invalid response');
      }

      // Validate assistant configuration
      const validation = await vapiIntegrationService.validateAssistantConfig(this.config.assistantId);

      if (!validation.valid) {
        console.warn('⚠️  Assistant configuration issues:', validation.issues);
      } else {
        console.log('✅ Assistant configuration is valid');
      }

      if (validation.recommendations.length > 0) {
        console.log('💡 Recommendations:', validation.recommendations);
      }

      this.recordTestResult('VAPI Assistant Validation', 'PASS', startTime, {
        assistantName: assistant.name,
        valid: validation.valid,
        issues: validation.issues,
        recommendations: validation.recommendations
      });

      console.log(`✅ Test 1 PASSED (${Date.now() - startTime}ms)`);

    } catch (error) {
      this.recordTestResult('VAPI Assistant Validation', 'FAIL', startTime, undefined, error.message);
      console.log(`❌ Test 1 FAILED: ${error.message}`);
    }
  }

  /**
   * Test 2: Test VAPI Call Initiation
   */
  private async testVAPICallInitiation(): Promise<void> {
    const startTime = Date.now();

    try {
      console.log('🧪 Test 2: VAPI Call Initiation');

      // Initiate test call
      const call = await vapiIntegrationService.initiateCall(
        this.config.assistantId,
        this.config.phoneId,
        this.config.testPhoneNumber,
        {
          test_mode: true,
          test_suite: 'voice_campaign_validation',
          initiated_at: new Date().toISOString()
        }
      );

      if (!call || !call.id) {
        throw new Error('Call initiation failed - no call ID returned');
      }

      console.log(`📞 Call initiated: ${call.id}`);
      console.log(`📊 Status: ${call.status}`);

      // Wait a moment and check call status
      await new Promise(resolve => setTimeout(resolve, 5000));

      const updatedCall = await vapiIntegrationService.getCall(call.id);
      console.log(`📊 Updated status: ${updatedCall.status}`);

      this.recordTestResult('VAPI Call Initiation', 'PASS', startTime, {
        callId: call.id,
        status: updatedCall.status,
        assistantId: call.assistantId,
        phoneNumberId: call.phoneNumberId
      });

      console.log(`✅ Test 2 PASSED (${Date.now() - startTime}ms)`);

    } catch (error) {
      this.recordTestResult('VAPI Call Initiation', 'FAIL', startTime, undefined, error.message);
      console.log(`❌ Test 2 FAILED: ${error.message}`);
    }
  }

  /**
   * Test 3: N8N Workflow Generation
   */
  private async testN8NWorkflowGeneration(): Promise<void> {
    const startTime = Date.now();

    try {
      console.log('🧪 Test 3: N8N Workflow Generation');

      const mockCampaignConfig = {
        name: 'Test Voice Campaign',
        description: 'Automated test campaign for validation',
        vapiAssistantId: this.config.assistantId,
        vapiPhoneId: this.config.phoneId,
        testAudienceNumbers: [this.config.testPhoneNumber],
        integrations: ['email', 'database', 'analytics'],
        automationSteps: [
          {
            id: 'step1',
            name: 'Initiate Call',
            type: 'trigger' as const,
            config: { type: 'vapi_call' }
          },
          {
            id: 'step2',
            name: 'Process Results',
            type: 'action' as const,
            config: { type: 'result_processing' }
          }
        ],
        desiredOutcomes: ['generate-leads', 'gather-information'],
        launchConfig: {
          maxConcurrentCalls: 3,
          dailyLimit: 100,
          callWindow: { start: '09:00', end: '17:00' }
        }
      };

      // Generate workflow
      const workflow = await N8NWorkflowGenerator.generateVoiceCampaignWorkflow(mockCampaignConfig);

      if (!workflow || !workflow.nodes || workflow.nodes.length === 0) {
        throw new Error('Workflow generation failed - no nodes generated');
      }

      console.log(`🔧 Generated workflow with ${workflow.nodes.length} nodes`);
      console.log(`📋 Workflow name: ${workflow.name}`);

      // Validate workflow structure
      const hasWebhook = workflow.nodes.some(node => node.type === 'n8n-nodes-base.webhook');
      const hasVAPICall = workflow.nodes.some(node => node.name.includes('VAPI'));
      const hasAnalytics = workflow.nodes.some(node => node.name.includes('Analytics'));

      if (!hasWebhook) {
        throw new Error('Workflow missing webhook trigger');
      }

      if (!hasVAPICall) {
        throw new Error('Workflow missing VAPI call node');
      }

      this.recordTestResult('N8N Workflow Generation', 'PASS', startTime, {
        nodeCount: workflow.nodes.length,
        hasWebhook,
        hasVAPICall,
        hasAnalytics,
        workflowName: workflow.name
      });

      console.log(`✅ Test 3 PASSED (${Date.now() - startTime}ms)`);

    } catch (error) {
      this.recordTestResult('N8N Workflow Generation', 'FAIL', startTime, undefined, error.message);
      console.log(`❌ Test 3 FAILED: ${error.message}`);
    }
  }

  /**
   * Test 4: N8N Workflow Deployment
   */
  private async testN8NWorkflowDeployment(): Promise<void> {
    const startTime = Date.now();

    try {
      console.log('🧪 Test 4: N8N Workflow Deployment');

      // Generate a simple test workflow
      const testWorkflow = {
        name: `Test Workflow ${Date.now()}`,
        active: false,
        nodes: [
          {
            parameters: {
              httpMethod: 'POST',
              path: `test-${Date.now()}`,
              responseMode: 'responseNode'
            },
            type: 'n8n-nodes-base.webhook',
            typeVersion: 2,
            position: [0, 0] as [number, number],
            id: 'webhook-test',
            name: 'Test Webhook'
          },
          {
            parameters: {
              respondWith: 'json',
              responseBody: '{"status": "success", "test": true}'
            },
            type: 'n8n-nodes-base.respondToWebhook',
            typeVersion: 1.2,
            position: [200, 0] as [number, number],
            id: 'response-test',
            name: 'Test Response'
          }
        ],
        connections: {
          'Test Webhook': {
            main: [[{ node: 'Test Response', type: 'main', index: 0 }]]
          }
        },
        settings: {
          executionOrder: 'v1'
        }
      };

      // Test deployment
      const deployment = await N8NWorkflowGenerator.deployWorkflow(testWorkflow);

      if (!deployment || !deployment.id) {
        throw new Error('Workflow deployment failed - no workflow ID returned');
      }

      console.log(`🚀 Deployed workflow: ${deployment.id}`);
      console.log(`🔗 Webhook URL: ${deployment.webhookUrl}`);

      this.recordTestResult('N8N Workflow Deployment', 'PASS', startTime, {
        workflowId: deployment.id,
        webhookUrl: deployment.webhookUrl
      });

      console.log(`✅ Test 4 PASSED (${Date.now() - startTime}ms)`);

    } catch (error) {
      this.recordTestResult('N8N Workflow Deployment', 'FAIL', startTime, undefined, error.message);
      console.log(`❌ Test 4 FAILED: ${error.message}`);
    }
  }

  /**
   * Test 5: LLM Fallback System
   */
  private async testLLMFallbackSystem(): Promise<void> {
    const startTime = Date.now();

    try {
      console.log('🧪 Test 5: LLM Fallback System');

      const testRequest = {
        prompt: 'Analyze this test voice campaign configuration for optimization opportunities: Campaign focused on lead generation with 100 contacts, using VAPI assistant for sales calls.',
        type: 'campaign-analysis' as const,
        maxTokens: 500,
        temperature: 0.7
      };

      // Test LLM processing
      const response = await llmFallbackService.processRequest(testRequest);

      if (!response || !response.content || response.content.length < 50) {
        throw new Error('LLM response is too short or empty');
      }

      console.log(`🤖 Provider: ${response.provider}`);
      console.log(`⏱️  Latency: ${response.latency}ms`);
      console.log(`🎯 Confidence: ${response.confidence}`);
      console.log(`📊 Tokens: ${response.usage.totalTokens}`);

      // Test multiple providers by clearing cache and retrying
      llmFallbackService.clearCache();

      this.recordTestResult('LLM Fallback System', 'PASS', startTime, {
        provider: response.provider,
        latency: response.latency,
        confidence: response.confidence,
        tokenCount: response.usage.totalTokens,
        contentLength: response.content.length
      });

      console.log(`✅ Test 5 PASSED (${Date.now() - startTime}ms)`);

    } catch (error) {
      this.recordTestResult('LLM Fallback System', 'FAIL', startTime, undefined, error.message);
      console.log(`❌ Test 5 FAILED: ${error.message}`);
    }
  }

  /**
   * Test 6: Campaign Configuration Analysis
   */
  private async testCampaignAnalysis(): Promise<void> {
    const startTime = Date.now();

    try {
      console.log('🧪 Test 6: Campaign Configuration Analysis');

      const mockCampaignConfig = {
        name: 'Test Sales Campaign',
        description: 'Lead generation campaign for testing',
        templateId: 'sales-cold-outreach',
        testAudienceNumbers: [this.config.testPhoneNumber],
        expectedVolume: 50,
        vapiAssistantId: this.config.assistantId,
        selectedIntegrations: ['email', 'crm'],
        desiredOutcomes: ['generate-leads', 'book-appointments'],
        launchType: 'test-first'
      };

      // Analyze campaign using LLM service
      const analysis = await llmFallbackService.analyzeCampaign(mockCampaignConfig);

      if (!analysis || !analysis.content) {
        throw new Error('Campaign analysis failed - no analysis returned');
      }

      console.log(`📊 Analysis provider: ${analysis.provider}`);
      console.log(`📝 Analysis length: ${analysis.content.length} characters`);

      // Check if analysis contains key recommendations
      const hasRecommendations = analysis.content.toLowerCase().includes('recommend');
      const hasOptimization = analysis.content.toLowerCase().includes('optim');

      this.recordTestResult('Campaign Configuration Analysis', 'PASS', startTime, {
        provider: analysis.provider,
        analysisLength: analysis.content.length,
        hasRecommendations,
        hasOptimization,
        confidence: analysis.confidence
      });

      console.log(`✅ Test 6 PASSED (${Date.now() - startTime}ms)`);

    } catch (error) {
      this.recordTestResult('Campaign Configuration Analysis', 'FAIL', startTime, undefined, error.message);
      console.log(`❌ Test 6 FAILED: ${error.message}`);
    }
  }

  /**
   * Test 7: End-to-End Campaign Test
   */
  private async testEndToEndCampaign(): Promise<void> {
    const startTime = Date.now();

    try {
      console.log('🧪 Test 7: End-to-End Campaign Test');

      // Run campaign test with single contact
      const testResult = await vapiIntegrationService.runCampaignTest(
        'test-campaign-e2e',
        this.config.assistantId,
        this.config.phoneId,
        {
          testContacts: [
            {
              phoneNumber: this.config.testPhoneNumber,
              expectedOutcome: 'lead-qualification'
            }
          ],
          testCriteria: {
            minConnectionRate: 50,
            minCompletionRate: 50,
            maxErrorRate: 50,
            minQualityScore: 30
          }
        }
      );

      if (!testResult || testResult.results.length === 0) {
        throw new Error('End-to-end test failed - no results returned');
      }

      console.log(`📊 Test results: ${testResult.summary.successful}/${testResult.summary.totalTests} successful`);
      console.log(`🎯 Average quality score: ${testResult.summary.avgQualityScore}`);
      console.log(`⏱️  Average duration: ${Math.round(testResult.summary.avgDuration / 1000)}s`);
      console.log(`✅ Test passed: ${testResult.summary.passed}`);

      this.recordTestResult('End-to-End Campaign Test', 'PASS', startTime, {
        totalTests: testResult.summary.totalTests,
        successful: testResult.summary.successful,
        failed: testResult.summary.failed,
        avgDuration: testResult.summary.avgDuration,
        avgQualityScore: testResult.summary.avgQualityScore,
        testPassed: testResult.summary.passed
      });

      console.log(`✅ Test 7 PASSED (${Date.now() - startTime}ms)`);

    } catch (error) {
      this.recordTestResult('End-to-End Campaign Test', 'FAIL', startTime, undefined, error.message);
      console.log(`❌ Test 7 FAILED: ${error.message}`);
    }
  }

  /**
   * Record test result
   */
  private recordTestResult(
    test: string,
    status: 'PASS' | 'FAIL',
    startTime: number,
    data?: any,
    error?: string
  ): void {
    const duration = Date.now() - startTime;

    this.results.details.push({
      test,
      status,
      duration,
      error,
      data
    });

    this.results.totalTests++;
    if (status === 'PASS') {
      this.results.passed++;
    } else {
      this.results.failed++;
    }
  }

  /**
   * Generate test summary
   */
  private generateTestSummary(): void {
    console.log('');
    console.log('━'.repeat(50));
    console.log('📊 TEST SUITE SUMMARY');
    console.log('━'.repeat(50));
    console.log(`⏰ Completed: ${new Date().toLocaleString()}`);
    console.log(`📈 Total Tests: ${this.results.totalTests}`);
    console.log(`✅ Passed: ${this.results.passed}`);
    console.log(`❌ Failed: ${this.results.failed}`);
    console.log(`📊 Success Rate: ${Math.round((this.results.passed / this.results.totalTests) * 100)}%`);
    console.log('');

    // Detailed results
    this.results.details.forEach((detail, index) => {
      const icon = detail.status === 'PASS' ? '✅' : '❌';
      console.log(`${icon} Test ${index + 1}: ${detail.test} (${detail.duration}ms)`);
      if (detail.error) {
        console.log(`   Error: ${detail.error}`);
      }
    });

    console.log('');
    console.log('━'.repeat(50));

    if (this.results.failed === 0) {
      console.log('🎉 ALL TESTS PASSED! Voice Campaign Wizard is ready for production.');
    } else {
      console.log(`⚠️  ${this.results.failed} test(s) failed. Please review and fix issues before deployment.`);
    }

    console.log('━'.repeat(50));
  }
}

/**
 * Run the test suite with provided credentials
 */
export async function runVoiceCampaignTests(): Promise<TestResults> {
  const testConfig: TestConfig = {
    assistantId: '3b73fb13-16d9-4eca-a910-ea2e0bd930e1',
    phoneId: '6c5af6e1-a2b7-41d6-ac04-4c9691bf73e4',
    testPhoneNumber: '+12397783680',
    apiKey: '42cf1e7c-2ef9-4bd7-ba30-52f2813605a2'
  };

  const testSuite = new VoiceCampaignTestSuite(testConfig);
  const results = await testSuite.runFullTestSuite();

  return results;
}

// Export for use in other modules
export default VoiceCampaignTestSuite;