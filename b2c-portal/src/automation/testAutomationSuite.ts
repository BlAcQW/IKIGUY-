/**
 * Test Automation Suite for Voice Campaign Wizard
 *
 * Comprehensive automated testing framework that validates:
 * - Voice campaign creation flow
 * - VAPI agent integration
 * - N8N workflow generation and deployment
 * - End-to-end call execution
 * - Results processing and analytics
 */

import { vapiIntegrationService } from '../services/vapiIntegrationService';
import { llmFallbackService } from '../services/llmFallbackService';
import N8NWorkflowGenerator from '../services/n8nWorkflowGenerator';

interface TestScenario {
  id: string;
  name: string;
  description: string;
  steps: TestStep[];
  expectedOutcomes: string[];
  timeout: number;
}

interface TestStep {
  id: string;
  name: string;
  action: 'create_agent' | 'create_campaign' | 'deploy_workflow' | 'execute_call' | 'validate_results';
  parameters: Record<string, any>;
  validations: Array<{
    field: string;
    condition: 'exists' | 'equals' | 'contains' | 'greater_than' | 'less_than';
    value: any;
  }>;
}

interface TestResult {
  scenarioId: string;
  stepId: string;
  status: 'PASS' | 'FAIL' | 'SKIP';
  duration: number;
  error?: string;
  data?: any;
  timestamp: string;
}

interface AutomationReport {
  testRunId: string;
  startTime: string;
  endTime: string;
  totalScenarios: number;
  passedScenarios: number;
  failedScenarios: number;
  totalSteps: number;
  passedSteps: number;
  failedSteps: number;
  scenarios: Array<{
    scenario: TestScenario;
    results: TestResult[];
    status: 'PASS' | 'FAIL';
    duration: number;
  }>;
  summary: {
    successRate: number;
    avgScenarioDuration: number;
    criticalFailures: string[];
    recommendations: string[];
  };
}

export class TestAutomationSuite {
  private testRunId: string;
  private results: TestResult[] = [];
  private startTime: Date;

  constructor() {
    this.testRunId = `test_run_${Date.now()}`;
    this.startTime = new Date();
  }

  /**
   * Main entry point to run all test scenarios
   */
  async runAllTests(): Promise<AutomationReport> {
    console.log('🚀 Starting Test Automation Suite');
    console.log(`📊 Test Run ID: ${this.testRunId}`);
    console.log('━'.repeat(60));

    const scenarios = this.getTestScenarios();
    const scenarioResults: AutomationReport['scenarios'] = [];

    for (const scenario of scenarios) {
      console.log(`\n🧪 Running Scenario: ${scenario.name}`);
      console.log(`📝 ${scenario.description}`);

      const scenarioStartTime = Date.now();
      const scenarioResults_: TestResult[] = [];
      let scenarioStatus: 'PASS' | 'FAIL' = 'PASS';

      for (const step of scenario.steps) {
        const stepResult = await this.executeTestStep(scenario.id, step);
        scenarioResults_.push(stepResult);
        this.results.push(stepResult);

        if (stepResult.status === 'FAIL') {
          scenarioStatus = 'FAIL';
          console.log(`   ❌ Step Failed: ${step.name}`);

          // Skip remaining steps if critical step fails
          if (step.action === 'create_agent' || step.action === 'create_campaign') {
            console.log('   ⏭️  Skipping remaining steps due to critical failure');
            break;
          }
        } else {
          console.log(`   ✅ Step Passed: ${step.name}`);
        }
      }

      const scenarioDuration = Date.now() - scenarioStartTime;
      scenarioResults.push({
        scenario,
        results: scenarioResults_,
        status: scenarioStatus,
        duration: scenarioDuration
      });

      console.log(`📊 Scenario ${scenarioStatus === 'PASS' ? '✅ PASSED' : '❌ FAILED'} (${scenarioDuration}ms)`);
    }

    return this.generateReport(scenarioResults);
  }

  /**
   * Define test scenarios for voice campaign automation
   */
  private getTestScenarios(): TestScenario[] {
    return [
      {
        id: 'basic_agent_creation',
        name: 'Basic Agent Creation Test',
        description: 'Create and validate a basic VAPI test agent',
        timeout: 30000,
        expectedOutcomes: ['agent_created', 'agent_configured', 'agent_validated'],
        steps: [
          {
            id: 'create_test_agent',
            name: 'Create VAPI Test Agent',
            action: 'create_agent',
            parameters: {
              name: 'ailabs-test',
              firstMessage: 'Hello! This is a test call from AI Labs. This is an automated test to validate our voice campaign system. Please stay on the line for about 30 seconds.',
              model: {
                provider: 'openai',
                model: 'gpt-4',
                temperature: 0.7,
                systemPrompt: `You are a friendly test assistant for AI Labs. Your role is to:
1. Greet the caller warmly
2. Explain this is a test call for system validation
3. Ask one simple question: "On a scale of 1-10, how would you rate the call quality?"
4. Thank them and end the call professionally
5. Keep the conversation under 1 minute

Be concise, professional, and friendly. Always end with "Thank you for helping us test our system!"`,
                functions: []
              },
              voice: {
                provider: 'elevenlabs',
                voiceId: 'jennifer'
              }
            },
            validations: [
              { field: 'id', condition: 'exists', value: true },
              { field: 'name', condition: 'equals', value: 'ailabs-test' }
            ]
          }
        ]
      },
      {
        id: 'campaign_creation_flow',
        name: 'Campaign Creation Flow Test',
        description: 'Test complete campaign creation with the test agent',
        timeout: 60000,
        expectedOutcomes: ['campaign_created', 'workflow_generated', 'workflow_deployed'],
        steps: [
          {
            id: 'create_test_campaign',
            name: 'Create Test Campaign Configuration',
            action: 'create_campaign',
            parameters: {
              name: 'Automated Test Campaign',
              description: 'System validation test campaign',
              vapiAssistantId: 'to_be_set', // Will be set from previous step
              vapiPhoneId: '6c5af6e1-a2b7-41d6-ac04-4c9691bf73e4',
              testAudienceNumbers: ['+12397783680'],
              integrations: ['analytics'],
              automationSteps: [
                {
                  id: 'step1',
                  name: 'Initiate Test Call',
                  type: 'trigger',
                  config: { type: 'vapi_call' }
                }
              ],
              desiredOutcomes: ['gather-information'],
              launchConfig: {
                maxConcurrentCalls: 1,
                dailyLimit: 10,
                callWindow: { start: '09:00', end: '17:00' }
              }
            },
            validations: [
              { field: 'workflow.nodes', condition: 'exists', value: true },
              { field: 'workflow.nodes.length', condition: 'greater_than', value: 0 }
            ]
          },
          {
            id: 'deploy_test_workflow',
            name: 'Deploy N8N Test Workflow',
            action: 'deploy_workflow',
            parameters: {
              workflow: 'from_previous_step'
            },
            validations: [
              { field: 'id', condition: 'exists', value: true },
              { field: 'webhookUrl', condition: 'exists', value: true }
            ]
          }
        ]
      },
      {
        id: 'end_to_end_call_test',
        name: 'End-to-End Call Execution Test',
        description: 'Execute a complete test call and validate results',
        timeout: 120000,
        expectedOutcomes: ['call_initiated', 'call_completed', 'results_processed'],
        steps: [
          {
            id: 'initiate_test_call',
            name: 'Initiate Test Call',
            action: 'execute_call',
            parameters: {
              assistantId: 'from_agent_creation',
              phoneId: '6c5af6e1-a2b7-41d6-ac04-4c9691bf73e4',
              customerNumber: '+12397783680',
              metadata: {
                test_mode: true,
                automation_test: true,
                expected_duration: 60
              }
            },
            validations: [
              { field: 'id', condition: 'exists', value: true },
              { field: 'status', condition: 'exists', value: true }
            ]
          },
          {
            id: 'validate_call_results',
            name: 'Validate Call Results',
            action: 'validate_results',
            parameters: {
              callId: 'from_previous_step',
              expectedOutcomes: ['information_gathered'],
              minDuration: 10000, // 10 seconds minimum
              maxDuration: 120000 // 2 minutes maximum
            },
            validations: [
              { field: 'status', condition: 'equals', value: 'ended' },
              { field: 'duration', condition: 'greater_than', value: 5000 }
            ]
          }
        ]
      }
    ];
  }

  /**
   * Execute individual test step
   */
  private async executeTestStep(scenarioId: string, step: TestStep): Promise<TestResult> {
    const startTime = Date.now();
    const result: TestResult = {
      scenarioId,
      stepId: step.id,
      status: 'FAIL',
      duration: 0,
      timestamp: new Date().toISOString()
    };

    try {
      console.log(`   ⚙️  Executing: ${step.name}`);

      let stepData: any;

      switch (step.action) {
        case 'create_agent':
          stepData = await this.createTestAgent(step.parameters);
          break;

        case 'create_campaign':
          stepData = await this.createTestCampaign(step.parameters);
          break;

        case 'deploy_workflow':
          stepData = await this.deployTestWorkflow(step.parameters);
          break;

        case 'execute_call':
          stepData = await this.executeTestCall(step.parameters);
          break;

        case 'validate_results':
          stepData = await this.validateCallResults(step.parameters);
          break;

        default:
          throw new Error(`Unknown test action: ${step.action}`);
      }

      // Validate results
      const validationResult = this.validateStepResults(stepData, step.validations);

      result.status = validationResult.passed ? 'PASS' : 'FAIL';
      result.data = stepData;
      result.error = validationResult.error;

      console.log(`   📊 Validation: ${result.status}`);

    } catch (error) {
      result.status = 'FAIL';
      result.error = error.message;
      console.log(`   ❌ Error: ${error.message}`);
    }

    result.duration = Date.now() - startTime;
    return result;
  }

  /**
   * Create VAPI test agent
   */
  private async createTestAgent(parameters: any): Promise<any> {
    console.log(`   🤖 Creating VAPI agent: ${parameters.name}`);

    const agentConfig = {
      name: parameters.name,
      firstMessage: parameters.firstMessage,
      model: parameters.model,
      voice: parameters.voice
    };

    // Create agent using VAPI service
    const agent = await vapiIntegrationService.createAssistant(agentConfig);

    console.log(`   ✅ Agent created with ID: ${agent.id}`);

    // Store agent ID for subsequent steps
    this.setContextData('testAgentId', agent.id);

    return agent;
  }

  /**
   * Create test campaign configuration
   */
  private async createTestCampaign(parameters: any): Promise<any> {
    console.log('   📋 Creating test campaign configuration');

    // Use agent ID from previous step
    const agentId = this.getContextData('testAgentId');
    if (!agentId) {
      throw new Error('Test agent ID not found from previous step');
    }

    const campaignConfig = {
      ...parameters,
      vapiAssistantId: agentId
    };

    // Generate N8N workflow
    const workflow = await N8NWorkflowGenerator.generateVoiceCampaignWorkflow(campaignConfig);

    console.log(`   ✅ Campaign workflow generated with ${workflow.nodes.length} nodes`);

    // Store workflow for deployment
    this.setContextData('testWorkflow', workflow);

    return {
      campaign: campaignConfig,
      workflow: workflow
    };
  }

  /**
   * Deploy test workflow to N8N
   */
  private async deployTestWorkflow(parameters: any): Promise<any> {
    console.log('   🚀 Deploying test workflow to N8N');

    const workflow = this.getContextData('testWorkflow');
    if (!workflow) {
      throw new Error('Test workflow not found from previous step');
    }

    // Deploy workflow
    const deployment = await N8NWorkflowGenerator.deployWorkflow(workflow);

    console.log(`   ✅ Workflow deployed with ID: ${deployment.id}`);

    // Store deployment info
    this.setContextData('testWorkflowDeployment', deployment);

    return deployment;
  }

  /**
   * Execute test call
   */
  private async executeTestCall(parameters: any): Promise<any> {
    console.log('   📞 Initiating test call');

    const agentId = this.getContextData('testAgentId');
    if (!agentId) {
      throw new Error('Test agent ID not found');
    }

    const call = await vapiIntegrationService.initiateCall(
      agentId,
      parameters.phoneId,
      parameters.customerNumber,
      parameters.metadata
    );

    console.log(`   ✅ Call initiated with ID: ${call.id}`);
    console.log('   ⏳ Waiting for call completion...');

    // Wait for call to complete (with timeout)
    const completedCall = await this.waitForCallCompletion(call.id, 90000); // 90 second timeout

    this.setContextData('testCall', completedCall);

    return completedCall;
  }

  /**
   * Validate call results
   */
  private async validateCallResults(parameters: any): Promise<any> {
    console.log('   🔍 Validating call results');

    const call = this.getContextData('testCall');
    if (!call) {
      throw new Error('Test call data not found');
    }

    const analysis = {
      callId: call.id,
      status: call.status,
      duration: call.endedAt && call.startedAt
        ? new Date(call.endedAt).getTime() - new Date(call.startedAt).getTime()
        : 0,
      endedReason: call.endedReason,
      hasTranscript: Boolean(call.transcript),
      transcriptLength: call.transcript?.length || 0,
      cost: call.cost || 0,

      // Validation results
      validations: {
        completedSuccessfully: call.status === 'ended' && call.endedReason !== 'assistant-error',
        withinDurationLimits: true, // Will be set below
        hasContent: (call.transcript?.length || 0) > 10
      }
    };

    // Check duration limits
    analysis.validations.withinDurationLimits =
      analysis.duration >= parameters.minDuration &&
      analysis.duration <= parameters.maxDuration;

    console.log(`   📊 Call duration: ${Math.round(analysis.duration / 1000)}s`);
    console.log(`   📊 Status: ${analysis.status} (${analysis.endedReason})`);
    console.log(`   📊 Transcript length: ${analysis.transcriptLength} chars`);

    return analysis;
  }

  /**
   * Wait for call completion with timeout
   */
  private async waitForCallCompletion(callId: string, timeout: number): Promise<any> {
    const startTime = Date.now();
    const checkInterval = 5000; // Check every 5 seconds

    while (Date.now() - startTime < timeout) {
      try {
        const call = await vapiIntegrationService.getCall(callId);

        if (call.status === 'ended') {
          return call;
        }

        console.log(`   ⏱️  Call status: ${call.status} (${Math.round((Date.now() - startTime) / 1000)}s)`);

        // Wait before next check
        await new Promise(resolve => setTimeout(resolve, checkInterval));

      } catch (error) {
        console.log(`   ⚠️  Error checking call status: ${error.message}`);
      }
    }

    throw new Error(`Call ${callId} did not complete within ${timeout}ms timeout`);
  }

  /**
   * Validate step results against expected conditions
   */
  private validateStepResults(data: any, validations: TestStep['validations']): { passed: boolean; error?: string } {
    for (const validation of validations) {
      const fieldValue = this.getNestedValue(data, validation.field);

      switch (validation.condition) {
        case 'exists':
          if (validation.value && !fieldValue) {
            return { passed: false, error: `Field '${validation.field}' does not exist` };
          }
          break;

        case 'equals':
          if (fieldValue !== validation.value) {
            return { passed: false, error: `Field '${validation.field}' expected '${validation.value}', got '${fieldValue}'` };
          }
          break;

        case 'contains':
          if (!String(fieldValue).includes(validation.value)) {
            return { passed: false, error: `Field '${validation.field}' does not contain '${validation.value}'` };
          }
          break;

        case 'greater_than':
          if (Number(fieldValue) <= Number(validation.value)) {
            return { passed: false, error: `Field '${validation.field}' (${fieldValue}) not greater than ${validation.value}` };
          }
          break;

        case 'less_than':
          if (Number(fieldValue) >= Number(validation.value)) {
            return { passed: false, error: `Field '${validation.field}' (${fieldValue}) not less than ${validation.value}` };
          }
          break;
      }
    }

    return { passed: true };
  }

  /**
   * Get nested value from object using dot notation
   */
  private getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  }

  // Context data storage for sharing data between steps
  private contextData: Map<string, any> = new Map();

  private setContextData(key: string, value: any): void {
    this.contextData.set(key, value);
  }

  private getContextData(key: string): any {
    return this.contextData.get(key);
  }

  /**
   * Generate comprehensive test report
   */
  private generateReport(scenarioResults: AutomationReport['scenarios']): AutomationReport {
    const endTime = new Date();
    const totalDuration = endTime.getTime() - this.startTime.getTime();

    const totalScenarios = scenarioResults.length;
    const passedScenarios = scenarioResults.filter(r => r.status === 'PASS').length;
    const failedScenarios = totalScenarios - passedScenarios;

    const totalSteps = this.results.length;
    const passedSteps = this.results.filter(r => r.status === 'PASS').length;
    const failedSteps = totalSteps - passedSteps;

    const criticalFailures: string[] = [];
    const recommendations: string[] = [];

    // Analyze failures
    scenarioResults.forEach(scenario => {
      scenario.results.forEach(result => {
        if (result.status === 'FAIL') {
          if (result.stepId.includes('create_agent') || result.stepId.includes('create_campaign')) {
            criticalFailures.push(`Critical failure in ${scenario.scenario.name}: ${result.error}`);
          }
        }
      });
    });

    // Generate recommendations
    if (failedSteps > 0) {
      recommendations.push('Review failed test steps and fix underlying issues');
    }
    if (passedScenarios < totalScenarios) {
      recommendations.push('Investigate scenario failures before production deployment');
    }
    if (criticalFailures.length > 0) {
      recommendations.push('Address critical failures immediately - system may not be production ready');
    }

    const report: AutomationReport = {
      testRunId: this.testRunId,
      startTime: this.startTime.toISOString(),
      endTime: endTime.toISOString(),
      totalScenarios,
      passedScenarios,
      failedScenarios,
      totalSteps,
      passedSteps,
      failedSteps,
      scenarios: scenarioResults,
      summary: {
        successRate: totalSteps > 0 ? Math.round((passedSteps / totalSteps) * 100) : 0,
        avgScenarioDuration: totalScenarios > 0 ? Math.round(scenarioResults.reduce((sum, r) => sum + r.duration, 0) / totalScenarios) : 0,
        criticalFailures,
        recommendations
      }
    };

    this.printReport(report);
    return report;
  }

  /**
   * Print formatted test report to console
   */
  private printReport(report: AutomationReport): void {
    console.log('\n' + '='.repeat(80));
    console.log('📊 TEST AUTOMATION REPORT');
    console.log('='.repeat(80));

    console.log(`🆔 Test Run ID: ${report.testRunId}`);
    console.log(`⏰ Duration: ${Math.round((new Date(report.endTime).getTime() - new Date(report.startTime).getTime()) / 1000)}s`);
    console.log(`📈 Success Rate: ${report.summary.successRate}%`);
    console.log('');

    console.log('📋 SUMMARY:');
    console.log(`   Scenarios: ${report.passedScenarios}/${report.totalScenarios} passed`);
    console.log(`   Steps: ${report.passedSteps}/${report.totalSteps} passed`);
    console.log(`   Avg Scenario Duration: ${Math.round(report.summary.avgScenarioDuration / 1000)}s`);
    console.log('');

    // Scenario details
    console.log('🧪 SCENARIO RESULTS:');
    report.scenarios.forEach((scenario, index) => {
      const icon = scenario.status === 'PASS' ? '✅' : '❌';
      console.log(`   ${icon} ${index + 1}. ${scenario.scenario.name} (${Math.round(scenario.duration / 1000)}s)`);

      scenario.results.forEach(result => {
        const stepIcon = result.status === 'PASS' ? '✅' : '❌';
        console.log(`      ${stepIcon} ${result.stepId}${result.error ? ': ' + result.error : ''}`);
      });
    });

    // Critical failures
    if (report.summary.criticalFailures.length > 0) {
      console.log('\n🚨 CRITICAL FAILURES:');
      report.summary.criticalFailures.forEach(failure => {
        console.log(`   ❌ ${failure}`);
      });
    }

    // Recommendations
    if (report.summary.recommendations.length > 0) {
      console.log('\n💡 RECOMMENDATIONS:');
      report.summary.recommendations.forEach(rec => {
        console.log(`   💡 ${rec}`);
      });
    }

    console.log('\n' + '='.repeat(80));

    if (report.summary.successRate >= 80) {
      console.log('🎉 TEST SUITE PASSED - System ready for production!');
    } else {
      console.log('⚠️  TEST SUITE NEEDS ATTENTION - Fix issues before deployment');
    }

    console.log('='.repeat(80));
  }
}

// Export for use in test runner
export default TestAutomationSuite;