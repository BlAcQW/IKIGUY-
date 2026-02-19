/**
 * N8N Workflow Auto-Generation System
 *
 * This service automatically generates n8n workflows for voice campaigns
 * with proper VAPI integration, data processing, and follow-up actions.
 */

interface CampaignConfig {
  name: string;
  description: string;
  vapiAssistantId: string;
  vapiPhoneId: string;
  testAudienceNumbers: string[];
  integrations: string[];
  automationSteps: Array<{
    id: string;
    name: string;
    type: 'trigger' | 'action' | 'condition' | 'transform';
    config: Record<string, any>;
  }>;
  desiredOutcomes: string[];
  launchConfig: {
    maxConcurrentCalls: number;
    dailyLimit: number;
    callWindow: { start: string; end: string };
  };
}

interface N8NWorkflow {
  name: string;
  active: boolean;
  nodes: N8NNode[];
  connections: Record<string, any>;
  settings: Record<string, any>;
  staticData?: Record<string, any>;
}

interface N8NNode {
  parameters: Record<string, any>;
  type: string;
  typeVersion: number;
  position: [number, number];
  id: string;
  name: string;
  credentials?: Record<string, any>;
}

export class N8NWorkflowGenerator {
  private static readonly N8N_API_URL = 'https://automate.inspirecreations.it.com/api/v1';
  private static readonly N8N_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MTBhMTUzMi04YmRkLTRkYjAtYjU1OS01ZTIxYTAzNjI4ODMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU2NDQxNjg4fQ.oAcaO5v0As8jl543StOB87l21jkURptt7bn9X6E7NcU';

  /**
   * Generate a complete n8n workflow for a voice campaign
   */
  static async generateVoiceCampaignWorkflow(config: CampaignConfig): Promise<N8NWorkflow> {
    const workflowId = `voice-campaign-${Date.now()}`;
    const nodes: N8NNode[] = [];
    const connections: Record<string, any> = {};

    // 1. Create webhook trigger for campaign initiation
    const webhookNode = this.createWebhookTrigger(workflowId);
    nodes.push(webhookNode);

    // 2. Create campaign scheduler if needed
    const schedulerNode = this.createCampaignScheduler(config);
    nodes.push(schedulerNode);

    // 3. Create audience processor
    const audienceNode = this.createAudienceProcessor(config);
    nodes.push(audienceNode);

    // 4. Create rate limiter
    const rateLimiterNode = this.createRateLimiter(config);
    nodes.push(rateLimiterNode);

    // 5. Create VAPI call initiator
    const vapiNode = this.createVAPICallNode(config);
    nodes.push(vapiNode);

    // 6. Create call result processor
    const processorNode = this.createCallResultProcessor(config);
    nodes.push(processorNode);

    // 7. Create outcome handler
    const outcomeNode = this.createOutcomeHandler(config);
    nodes.push(outcomeNode);

    // 8. Create integration handlers based on selected integrations
    const integrationNodes = this.createIntegrationHandlers(config);
    nodes.push(...integrationNodes);

    // 9. Create analytics and reporting nodes
    const analyticsNode = this.createAnalyticsHandler(config);
    nodes.push(analyticsNode);

    // 10. Create error handler
    const errorNode = this.createErrorHandler(config);
    nodes.push(errorNode);

    // 11. Build connections between nodes
    this.buildNodeConnections(nodes, connections);

    return {
      name: `${config.name} - Voice Campaign Workflow`,
      active: false, // Start inactive for testing
      nodes,
      connections,
      settings: {
        executionOrder: 'v1',
        saveDataErrorExecution: 'all',
        saveDataSuccessExecution: 'all',
        saveManualExecutions: true,
        callerPolicy: 'workflowsFromSameOwner',
        timezone: 'America/New_York'
      },
      staticData: {
        campaignConfig: config,
        stats: {
          totalCalls: 0,
          successfulCalls: 0,
          failedCalls: 0,
          outcomes: {}
        }
      }
    };
  }

  /**
   * Create webhook trigger node for campaign initiation
   */
  private static createWebhookTrigger(workflowId: string): N8NNode {
    return {
      parameters: {
        httpMethod: 'POST',
        path: `voice-campaign/${workflowId}`,
        responseMode: 'responseNode',
        options: {}
      },
      type: 'n8n-nodes-base.webhook',
      typeVersion: 2,
      position: [0, 0],
      id: 'webhook-trigger',
      name: 'Campaign Webhook Trigger'
    };
  }

  /**
   * Create campaign scheduler for managing call timing
   */
  private static createCampaignScheduler(config: CampaignConfig): N8NNode {
    return {
      parameters: {
        jsCode: `
          // Campaign scheduling logic
          const now = new Date();
          const callWindow = $json.campaignConfig?.launchConfig?.callWindow;

          if (!callWindow) {
            return [{ json: { proceed: true, reason: 'No call window restrictions' } }];
          }

          const startTime = new Date();
          const [startHour, startMin] = callWindow.start.split(':').map(Number);
          startTime.setHours(startHour, startMin, 0, 0);

          const endTime = new Date();
          const [endHour, endMin] = callWindow.end.split(':').map(Number);
          endTime.setHours(endHour, endMin, 0, 0);

          const withinWindow = now >= startTime && now <= endTime;

          return [{
            json: {
              proceed: withinWindow,
              reason: withinWindow ? 'Within call window' : \`Outside call window (\${callWindow.start}-\${callWindow.end})\`,
              currentTime: now.toISOString(),
              callWindow: callWindow
            }
          }];
        `
      },
      type: 'n8n-nodes-base.code',
      typeVersion: 2,
      position: [200, 0],
      id: 'campaign-scheduler',
      name: 'Campaign Scheduler'
    };
  }

  /**
   * Create audience processor for handling contact lists
   */
  private static createAudienceProcessor(config: CampaignConfig): N8NNode {
    return {
      parameters: {
        jsCode: `
          // Process audience data
          const contacts = $json.contacts || [];
          const testMode = $json.testMode || false;
          const testNumbers = ${JSON.stringify(config.testAudienceNumbers)};

          let processedContacts = contacts;

          // Use test numbers if in test mode
          if (testMode) {
            processedContacts = testNumbers.map((number, index) => ({
              phone_number: number,
              first_name: \`Test\${index + 1}\`,
              test_contact: true,
              contact_id: \`test-\${index}\`
            }));
          }

          // Filter out invalid numbers
          processedContacts = processedContacts.filter(contact => {
            const phone = contact.phone_number;
            return phone && phone.match(/^\\+?[1-9]\\d{1,14}$/);
          });

          return processedContacts.map(contact => ({
            json: {
              ...contact,
              campaign_id: '${config.name}',
              processed_at: new Date().toISOString()
            }
          }));
        `
      },
      type: 'n8n-nodes-base.code',
      typeVersion: 2,
      position: [400, 0],
      id: 'audience-processor',
      name: 'Audience Processor'
    };
  }

  /**
   * Create rate limiter for managing concurrent calls
   */
  private static createRateLimiter(config: CampaignConfig): N8NNode {
    return {
      parameters: {
        jsCode: `
          // Rate limiting logic
          const maxConcurrent = ${config.launchConfig.maxConcurrentCalls};
          const dailyLimit = ${config.launchConfig.dailyLimit};

          // Check current active calls (would query database in real implementation)
          const activeCalls = $json.activeCalls || 0;
          const todaysCalls = $json.todaysCalls || 0;

          const canProceed = activeCalls < maxConcurrent && todaysCalls < dailyLimit;

          return [{
            json: {
              ...($json),
              rateLimitCheck: {
                canProceed: canProceed,
                activeCalls: activeCalls,
                maxConcurrent: maxConcurrent,
                todaysCalls: todaysCalls,
                dailyLimit: dailyLimit,
                reason: canProceed ? 'Within limits' :
                        activeCalls >= maxConcurrent ? 'Max concurrent calls reached' :
                        'Daily limit reached'
              }
            }
          }];
        `
      },
      type: 'n8n-nodes-base.code',
      typeVersion: 2,
      position: [600, 0],
      id: 'rate-limiter',
      name: 'Rate Limiter'
    };
  }

  /**
   * Create VAPI call initiation node
   */
  private static createVAPICallNode(config: CampaignConfig): N8NNode {
    return {
      parameters: {
        url: 'https://api.vapi.ai/call',
        authentication: 'genericCredentialType',
        genericAuthType: 'httpHeaderAuth',
        sendHeaders: true,
        headerParameters: {
          parameters: [
            {
              name: 'Authorization',
              value: `Bearer ${import.meta.env.VITE_VAPI_API_KEY}`
            }
          ]
        },
        sendBody: true,
        specifyBody: 'json',
        jsonBody: `{
          "assistantId": "${config.vapiAssistantId}",
          "phoneNumberId": "${config.vapiPhoneId}",
          "customer": {
            "number": "={{ $json.phone_number }}",
            "name": "={{ $json.first_name }} {{ $json.last_name }}",
            "company": "={{ $json.company }}"
          },
          "metadata": {
            "campaign_id": "${config.name}",
            "contact_id": "={{ $json.contact_id }}",
            "test_contact": "={{ $json.test_contact }}",
            "initiated_at": "={{ new Date().toISOString() }}"
          }
        }`,
        options: {
          timeout: 30000,
          retry: {
            enabled: true,
            maxRetries: 2
          }
        }
      },
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 4.2,
      position: [800, 0],
      id: 'vapi-call-initiator',
      name: 'Initiate VAPI Call'
    };
  }

  /**
   * Create call result processor
   */
  private static createCallResultProcessor(config: CampaignConfig): N8NNode {
    return {
      parameters: {
        jsCode: `
          // Process VAPI call results
          const callResult = $json;
          const contact = $('audience-processor').item.json;

          // Extract key information from call
          const analysis = {
            call_id: callResult.id,
            status: callResult.status,
            duration: callResult.endedAt ?
                     new Date(callResult.endedAt).getTime() - new Date(callResult.startedAt).getTime() : 0,
            ended_reason: callResult.endedReason,
            cost: callResult.cost,
            transcript: callResult.transcript,

            // Outcome analysis
            outcome: this.analyzeCallOutcome(callResult, ${JSON.stringify(config.desiredOutcomes)}),

            // Metrics
            successful: callResult.status === 'ended' && callResult.endedReason !== 'customer-hung-up',
            quality_score: this.calculateQualityScore(callResult),

            // Contact info
            contact_id: contact.contact_id,
            phone_number: contact.phone_number,
            campaign_id: '${config.name}',

            // Timestamps
            processed_at: new Date().toISOString(),
            call_started_at: callResult.startedAt,
            call_ended_at: callResult.endedAt
          };

          return [{ json: analysis }];

          // Helper function to analyze call outcome
          function analyzeCallOutcome(callResult, desiredOutcomes) {
            const transcript = callResult.transcript || '';
            const outcomes = {};

            desiredOutcomes.forEach(outcome => {
              switch(outcome) {
                case 'book-appointments':
                  outcomes.appointment_booked = transcript.includes('appointment') ||
                                             transcript.includes('meeting') ||
                                             transcript.includes('schedule');
                  break;
                case 'collect-payments':
                  outcomes.payment_discussed = transcript.includes('payment') ||
                                             transcript.includes('pay') ||
                                             transcript.includes('invoice');
                  break;
                case 'gather-information':
                  outcomes.information_collected = transcript.includes('email') ||
                                                 transcript.includes('address') ||
                                                 transcript.includes('company');
                  break;
                case 'generate-leads':
                  outcomes.lead_qualified = transcript.includes('interested') ||
                                          transcript.includes('yes') ||
                                          transcript.includes('tell me more');
                  break;
              }
            });

            return outcomes;
          }

          // Helper function to calculate quality score
          function calculateQualityScore(callResult) {
            let score = 50; // Base score

            // Duration bonus
            const duration = callResult.endedAt ?
                           new Date(callResult.endedAt).getTime() - new Date(callResult.startedAt).getTime() : 0;
            if (duration > 60000) score += 20; // 1+ minute
            if (duration > 180000) score += 10; // 3+ minutes

            // Completion bonus
            if (callResult.endedReason === 'assistant-ended') score += 20;

            // Transcript analysis bonus
            const transcript = callResult.transcript || '';
            if (transcript.length > 100) score += 10;

            return Math.min(100, Math.max(0, score));
          }
        `
      },
      type: 'n8n-nodes-base.code',
      typeVersion: 2,
      position: [1000, 0],
      id: 'call-result-processor',
      name: 'Process Call Results'
    };
  }

  /**
   * Create outcome handler for different campaign outcomes
   */
  private static createOutcomeHandler(config: CampaignConfig): N8NNode {
    return {
      parameters: {
        rules: {
          values: config.desiredOutcomes.map((outcome, index) => ({
            conditions: {
              options: {
                caseSensitive: true,
                leftValue: '',
                typeValidation: 'strict',
                version: 2
              },
              conditions: [{
                leftValue: `={{ $json.outcome.${this.getOutcomeKey(outcome)} }}`,
                rightValue: 'true',
                operator: {
                  type: 'boolean',
                  operation: 'equals'
                }
              }],
              combinator: 'and'
            }
          }))
        },
        options: {}
      },
      type: 'n8n-nodes-base.switch',
      typeVersion: 3.2,
      position: [1200, 0],
      id: 'outcome-handler',
      name: 'Outcome Router'
    };
  }

  /**
   * Create integration handler nodes based on selected integrations
   */
  private static createIntegrationHandlers(config: CampaignConfig): N8NNode[] {
    const nodes: N8NNode[] = [];
    let yOffset = 200;

    config.integrations.forEach((integration, index) => {
      const node = this.createIntegrationNode(integration, index, yOffset);
      if (node) {
        nodes.push(node);
        yOffset += 100;
      }
    });

    return nodes;
  }

  /**
   * Create specific integration node
   */
  private static createIntegrationNode(integration: string, index: number, yOffset: number): N8NNode | null {
    const basePosition: [number, number] = [1400, yOffset];

    switch (integration) {
      case 'email':
        return {
          parameters: {
            resource: 'email',
            operation: 'send',
            message: {
              to: '={{ $json.email || "admin@company.com" }}',
              subject: `Follow-up from Voice Campaign: {{ $json.campaign_id }}`,
              message: `
                Hello {{ $json.first_name || "there" }},

                Thank you for taking our call today. Here's a summary of our conversation:

                Call Duration: {{ Math.round($json.duration / 1000) }} seconds
                Outcome: {{ Object.keys($json.outcome).filter(k => $json.outcome[k]).join(', ') }}

                {{ $json.outcome.appointment_booked ? 'We look forward to our scheduled meeting!' : '' }}
                {{ $json.outcome.payment_discussed ? 'Please review the payment information we discussed.' : '' }}

                Best regards,
                Your AI Assistant Team
              `,
              options: {}
            }
          },
          type: 'n8n-nodes-base.gmail',
          typeVersion: 2.1,
          position: basePosition,
          id: `email-integration-${index}`,
          name: 'Send Follow-up Email'
        };

      case 'calendar':
        return {
          parameters: {
            resource: 'event',
            operation: 'create',
            calendarId: 'primary',
            summary: 'Follow-up Meeting - {{ $json.first_name }}',
            start: {
              dateTime: '={{ DateTime.now().plus({days: 1}).set({hour: 14, minute: 0}).toISO() }}',
              timeZone: 'America/New_York'
            },
            end: {
              dateTime: '={{ DateTime.now().plus({days: 1}).set({hour: 15, minute: 0}).toISO() }}',
              timeZone: 'America/New_York'
            },
            description: `
              Follow-up meeting scheduled from voice campaign call.

              Contact: {{ $json.first_name }} {{ $json.last_name }}
              Phone: {{ $json.phone_number }}
              Call Duration: {{ Math.round($json.duration / 1000) }} seconds

              Call Summary:
              {{ Object.keys($json.outcome).filter(k => $json.outcome[k]).join(', ') }}
            `,
            attendees: [
              { email: '={{ $json.email }}' }
            ]
          },
          type: 'n8n-nodes-base.googleCalendar',
          typeVersion: 1.2,
          position: basePosition,
          id: `calendar-integration-${index}`,
          name: 'Schedule Follow-up Meeting'
        };

      case 'crm':
        return {
          parameters: {
            resource: 'deal',
            operation: 'create',
            dealProperties: {
              title: 'Voice Campaign Lead - {{ $json.first_name }} {{ $json.last_name }}',
              value: '{{ $json.outcome.lead_qualified ? 5000 : 1000 }}',
              currency: 'USD',
              stage: '{{ $json.outcome.appointment_booked ? "MEETING_SCHEDULED" : "CONTACTED" }}',
              source: 'Voice Campaign',
              contactId: '={{ $json.contact_id }}',
              customFields: {
                campaign_id: '{{ $json.campaign_id }}',
                call_duration: '{{ $json.duration }}',
                quality_score: '{{ $json.quality_score }}',
                outcomes: '{{ Object.keys($json.outcome).filter(k => $json.outcome[k]).join(", ") }}'
              }
            }
          },
          type: 'n8n-nodes-base.pipedrive',
          typeVersion: 1,
          position: basePosition,
          id: `crm-integration-${index}`,
          name: 'Create CRM Lead'
        };

      case 'sms':
        return {
          parameters: {
            resource: 'message',
            operation: 'send',
            body: `Hi {{ $json.first_name }}, thanks for taking our call! {{ $json.outcome.appointment_booked ? 'Looking forward to our meeting.' : 'We\'ll follow up with more information soon.' }}`,
            to: '={{ $json.phone_number }}',
            from: '+18885551234'
          },
          type: 'n8n-nodes-base.twilio',
          typeVersion: 2,
          position: basePosition,
          id: `sms-integration-${index}`,
          name: 'Send Follow-up SMS'
        };

      case 'database':
        return {
          parameters: {
            operation: 'insert',
            table: 'voice_campaign_results',
            columns: 'campaign_id,contact_id,phone_number,call_id,duration,outcome,quality_score,created_at',
            additionalFields: {},
            options: {},
            queryBatching: 'single'
          },
          type: 'n8n-nodes-base.postgres',
          typeVersion: 2.4,
          position: basePosition,
          id: `database-integration-${index}`,
          name: 'Store Results in Database'
        };

      default:
        return null;
    }
  }

  /**
   * Create analytics handler for campaign metrics
   */
  private static createAnalyticsHandler(config: CampaignConfig): N8NNode {
    return {
      parameters: {
        jsCode: `
          // Analytics and reporting
          const result = $json;
          const campaignId = '${config.name}';

          // Calculate metrics
          const metrics = {
            campaign_id: campaignId,
            timestamp: new Date().toISOString(),

            // Call metrics
            total_calls: 1,
            successful_calls: result.successful ? 1 : 0,
            failed_calls: result.successful ? 0 : 1,
            avg_duration: result.duration,
            avg_quality_score: result.quality_score,

            // Outcome metrics
            outcomes: result.outcome,

            // Cost metrics
            total_cost: result.cost || 0,
            cost_per_successful_call: result.successful && result.cost ? result.cost : 0,

            // Time metrics
            hour_of_day: new Date().getHours(),
            day_of_week: new Date().getDay()
          };

          // Send to analytics endpoint (could be Google Analytics, Mixpanel, etc.)
          return [{
            json: {
              ...result,
              analytics: metrics,
              // Webhook payload for analytics service
              analytics_webhook: {
                event: 'voice_campaign_call_completed',
                properties: metrics
              }
            }
          }];
        `
      },
      type: 'n8n-nodes-base.code',
      typeVersion: 2,
      position: [1600, 0],
      id: 'analytics-handler',
      name: 'Analytics & Reporting'
    };
  }

  /**
   * Create error handler for failed calls and exceptions
   */
  private static createErrorHandler(config: CampaignConfig): N8NNode {
    return {
      parameters: {
        resource: 'message',
        operation: 'sendMessage',
        chatId: '@voice_campaign_alerts', // Telegram chat for alerts
        text: `🚨 Voice Campaign Error Alert

Campaign: ${config.name}
Contact: {{ $json.phone_number }}
Error: {{ $json.error?.message || 'Unknown error' }}
Time: {{ new Date().toISOString() }}

Please investigate and take appropriate action.`,
        additionalFields: {
          parseMode: 'Markdown'
        }
      },
      type: 'n8n-nodes-base.telegram',
      typeVersion: 1.2,
      position: [1600, 200],
      id: 'error-handler',
      name: 'Error Alert Handler'
    };
  }

  /**
   * Build connections between workflow nodes
   */
  private static buildNodeConnections(nodes: N8NNode[], connections: Record<string, any>): void {
    // Main flow connections
    connections['Campaign Webhook Trigger'] = {
      main: [[{ node: 'Campaign Scheduler', type: 'main', index: 0 }]]
    };

    connections['Campaign Scheduler'] = {
      main: [[{ node: 'Audience Processor', type: 'main', index: 0 }]]
    };

    connections['Audience Processor'] = {
      main: [[{ node: 'Rate Limiter', type: 'main', index: 0 }]]
    };

    connections['Rate Limiter'] = {
      main: [[{ node: 'Initiate VAPI Call', type: 'main', index: 0 }]]
    };

    connections['Initiate VAPI Call'] = {
      main: [
        [{ node: 'Process Call Results', type: 'main', index: 0 }],
        [{ node: 'Error Alert Handler', type: 'main', index: 0 }] // Error path
      ]
    };

    connections['Process Call Results'] = {
      main: [
        [{ node: 'Outcome Router', type: 'main', index: 0 }],
        [{ node: 'Analytics & Reporting', type: 'main', index: 0 }]
      ]
    };

    // Connect outcome router to integration handlers
    const integrationNodes = nodes.filter(node => node.id.includes('integration'));
    if (integrationNodes.length > 0) {
      connections['Outcome Router'] = {
        main: integrationNodes.map(node => [{ node: node.name, type: 'main', index: 0 }])
      };
    }
  }

  /**
   * Deploy workflow to n8n instance
   */
  static async deployWorkflow(workflow: N8NWorkflow): Promise<{ id: string; webhookUrl: string }> {
    try {
      const response = await fetch(`${this.N8N_API_URL}/workflows`, {
        method: 'POST',
        headers: {
          'X-N8N-API-KEY': this.N8N_API_KEY,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(workflow)
      });

      if (!response.ok) {
        throw new Error(`Failed to deploy workflow: ${response.statusText}`);
      }

      const deployedWorkflow = await response.json();

      // Generate webhook URL
      const webhookUrl = `${this.N8N_API_URL.replace('/api/v1', '')}/webhook/${deployedWorkflow.id}`;

      return {
        id: deployedWorkflow.id,
        webhookUrl
      };

    } catch (error) {
      console.error('Workflow deployment failed:', error);
      throw error;
    }
  }

  /**
   * Activate deployed workflow
   */
  static async activateWorkflow(workflowId: string): Promise<void> {
    try {
      await fetch(`${this.N8N_API_URL}/workflows/${workflowId}/activate`, {
        method: 'POST',
        headers: {
          'X-N8N-API-KEY': this.N8N_API_KEY,
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('Failed to activate workflow:', error);
      throw error;
    }
  }

  /**
   * Execute workflow with test data
   */
  static async executeWorkflow(workflowId: string, testData: any): Promise<any> {
    try {
      const response = await fetch(`${this.N8N_API_URL}/workflows/${workflowId}/execute`, {
        method: 'POST',
        headers: {
          'X-N8N-API-KEY': this.N8N_API_KEY,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          data: testData
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to execute workflow: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Workflow execution failed:', error);
      throw error;
    }
  }

  /**
   * Monitor workflow execution status
   */
  static async getWorkflowExecutions(workflowId: string, limit: number = 10): Promise<any[]> {
    try {
      const response = await fetch(`${this.N8N_API_URL}/executions?filter={"workflowId":"${workflowId}"}&limit=${limit}`, {
        headers: {
          'X-N8N-API-KEY': this.N8N_API_KEY,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to get executions: ${response.statusText}`);
      }

      const result = await response.json();
      return result.data || [];

    } catch (error) {
      console.error('Failed to get workflow executions:', error);
      throw error;
    }
  }

  /**
   * Helper method to get outcome key for switch conditions
   */
  private static getOutcomeKey(outcome: string): string {
    const outcomeMap: Record<string, string> = {
      'book-appointments': 'appointment_booked',
      'collect-payments': 'payment_discussed',
      'gather-information': 'information_collected',
      'generate-leads': 'lead_qualified',
      'provide-support': 'support_provided'
    };
    return outcomeMap[outcome] || 'unknown';
  }
}

export default N8NWorkflowGenerator;