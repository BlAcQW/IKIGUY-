/**
 * Standardized n8n Workflow Orchestration Patterns
 *
 * Based on n8n community best practices and successful implementations.
 * These patterns ensure consistent, monitored, and scalable workflow design.
 */

export interface N8nWorkflowPattern {
  id: string;
  name: string;
  description: string;
  nodes: N8nNode[];
  connections: N8nConnections;
  settings: N8nWorkflowSettings;
  monitoring: N8nMonitoringConfig;
}

export interface N8nNode {
  id: string;
  name: string;
  type: string;
  typeVersion: number;
  position: [number, number];
  parameters: Record<string, any>;
  credentials?: Record<string, string>;
  continueOnFail?: boolean;
  alwaysOutputData?: boolean;
  executeOnce?: boolean;
}

export interface N8nConnections {
  [sourceNodeId: string]: {
    main: Array<Array<{
      node: string;
      type: string;
      index: number;
    }>>;
  };
}

export interface N8nWorkflowSettings {
  executionOrder: 'v0' | 'v1';
  saveManualExecutions: boolean;
  saveExecutionProgress: boolean;
  saveDataErrorExecution: 'all' | 'none';
  saveDataSuccessExecution: 'all' | 'none';
  executionTimeout: number;
  timezone: string;
}

export interface N8nMonitoringConfig {
  healthCheckEndpoint: string;
  errorNotificationWebhook: string;
  performanceMetricsEndpoint: string;
  alertThresholds: {
    executionTime: number;
    errorRate: number;
    memoryUsage: number;
  };
}

/**
 * Standard Insurance Customer Service n8n Workflow
 * Based on community template and best practices
 */
export const INSURANCE_CUSTOMER_SERVICE_WORKFLOW: N8nWorkflowPattern = {
  id: 'insurance_customer_service_vapi_n8n',
  name: 'Insurance Customer Service with VAPI + n8n',
  description: 'Complete customer service workflow with voice agent, case management, and monitoring',

  nodes: [
    {
      id: '1',
      name: 'VAPI Webhook Trigger',
      type: 'n8n-nodes-base.webhook',
      typeVersion: 1,
      position: [240, 300],
      parameters: {
        path: 'insurance-customer-service',
        httpMethod: 'POST',
        responseMode: 'responseNode',
        options: {
          allowedOrigins: '*'
        }
      },
      continueOnFail: false
    },

    {
      id: '2',
      name: 'Validate Customer Data',
      type: 'n8n-nodes-base.function',
      typeVersion: 1,
      position: [460, 300],
      parameters: {
        functionCode: `
// Validate incoming VAPI webhook data
const vapiData = items[0].json;

// Extract customer information
const customerInfo = {
  policyNumber: vapiData.metadata?.policyNumber || vapiData.call?.metadata?.policyNumber,
  customerName: vapiData.metadata?.customerName || vapiData.call?.metadata?.customerName,
  callId: vapiData.call?.id,
  timestamp: new Date().toISOString(),
  inquiryType: vapiData.metadata?.inquiryType || 'general',
  sentiment: vapiData.analysis?.sentiment || 'neutral'
};

// Validate required fields
if (!customerInfo.policyNumber || !customerInfo.customerName) {
  throw new Error('Missing required customer information');
}

return [{
  json: {
    ...customerInfo,
    validated: true,
    processingId: \`proc_\${Date.now()}\`
  }
}];
`
      },
      continueOnFail: false
    },

    {
      id: '3',
      name: 'Lookup Customer Record',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 3,
      position: [680, 300],
      parameters: {
        url: '={{$env.API_BASE_URL}}/api/customers/lookup',
        method: 'POST',
        sendBody: true,
        bodyContentType: 'json',
        jsonBody: `{
  "policyNumber": "={{$json.policyNumber}}",
  "customerName": "={{$json.customerName}}"
}`,
        options: {
          timeout: 30000,
          retry: {
            enabled: true,
            maxRetries: 3
          }
        }
      },
      continueOnFail: true
    },

    {
      id: '4',
      name: 'Customer Found?',
      type: 'n8n-nodes-base.if',
      typeVersion: 1,
      position: [900, 300],
      parameters: {
        conditions: {
          string: [
            {
              value1: '={{$json.customerId}}',
              operation: 'isNotEmpty'
            }
          ]
        }
      }
    },

    {
      id: '5',
      name: 'Create Service Case',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 3,
      position: [1120, 200],
      parameters: {
        url: '={{$env.API_BASE_URL}}/api/service-cases',
        method: 'POST',
        sendBody: true,
        bodyContentType: 'json',
        jsonBody: `{
  "customerId": "={{$node["Lookup Customer Record"].json.customerId}}",
  "policyNumber": "={{$json.policyNumber}}",
  "inquiryType": "={{$json.inquiryType}}",
  "callId": "={{$json.callId}}",
  "priority": "={{$json.sentiment === 'negative' ? 'high' : 'normal'}}",
  "source": "vapi_voice_call",
  "status": "open",
  "metadata": {
    "sentiment": "={{$json.sentiment}}",
    "processingId": "={{$json.processingId}}"
  }
}`
      },
      continueOnFail: false
    },

    {
      id: '6',
      name: 'Send Customer Not Found Alert',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 3,
      position: [1120, 400],
      parameters: {
        url: '={{$env.API_BASE_URL}}/api/alerts/customer-not-found',
        method: 'POST',
        sendBody: true,
        bodyContentType: 'json',
        jsonBody: `{
  "policyNumber": "={{$json.policyNumber}}",
  "customerName": "={{$json.customerName}}",
  "callId": "={{$json.callId}}",
  "timestamp": "={{$json.timestamp}}",
  "alert": "Customer lookup failed",
  "action": "Manual verification required"
}`
      },
      continueOnFail: false
    },

    {
      id: '7',
      name: 'Route by Inquiry Type',
      type: 'n8n-nodes-base.switch',
      typeVersion: 1,
      position: [1340, 200],
      parameters: {
        dataType: 'string',
        value1: '={{$json.inquiryType}}',
        rules: {
          rules: [
            {
              value2: 'claim',
              output: 0
            },
            {
              value2: 'payment',
              output: 1
            },
            {
              value2: 'policy_change',
              output: 2
            }
          ]
        },
        fallbackOutput: 3
      }
    },

    {
      id: '8',
      name: 'Process Claims Inquiry',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 3,
      position: [1560, 100],
      parameters: {
        url: '={{$env.API_BASE_URL}}/api/claims/process-inquiry',
        method: 'POST',
        sendBody: true,
        bodyContentType: 'json',
        jsonBody: `{
  "caseId": "={{$node["Create Service Case"].json.caseId}}",
  "customerId": "={{$node["Lookup Customer Record"].json.customerId}}",
  "inquiryDetails": "={{$json}}"
}`
      }
    },

    {
      id: '9',
      name: 'Process Payment Inquiry',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 3,
      position: [1560, 200],
      parameters: {
        url: '={{$env.API_BASE_URL}}/api/payments/process-inquiry',
        method: 'POST',
        sendBody: true,
        bodyContentType: 'json',
        jsonBody: `{
  "caseId": "={{$node["Create Service Case"].json.caseId}}",
  "customerId": "={{$node["Lookup Customer Record"].json.customerId}}",
  "inquiryDetails": "={{$json}}"
}`
      }
    },

    {
      id: '10',
      name: 'Process Policy Inquiry',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 3,
      position: [1560, 300],
      parameters: {
        url: '={{$env.API_BASE_URL}}/api/policies/process-inquiry',
        method: 'POST',
        sendBody: true,
        bodyContentType: 'json',
        jsonBody: `{
  "caseId": "={{$node["Create Service Case"].json.caseId}}",
  "customerId": "={{$node["Lookup Customer Record"].json.customerId}}",
  "inquiryDetails": "={{$json}}"
}`
      }
    },

    {
      id: '11',
      name: 'Process General Inquiry',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 3,
      position: [1560, 400],
      parameters: {
        url: '={{$env.API_BASE_URL}}/api/general/process-inquiry',
        method: 'POST',
        sendBody: true,
        bodyContentType: 'json',
        jsonBody: `{
  "caseId": "={{$node["Create Service Case"].json.caseId}}",
  "customerId": "={{$node["Lookup Customer Record"].json.customerId}}",
  "inquiryDetails": "={{$json}}"
}`
      }
    },

    {
      id: '12',
      name: 'Update Automation Health',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 3,
      position: [1780, 250],
      parameters: {
        url: '={{$env.API_BASE_URL}}/api/monitoring/automation-health',
        method: 'POST',
        sendBody: true,
        bodyContentType: 'json',
        jsonBody: `{
  "automationId": "insurance_customer_service",
  "templateId": "insurance_customer_service_automation",
  "tenantId": "={{$env.TENANT_ID}}",
  "executionId": "={{$execution.id}}",
  "status": "completed",
  "processingTime": "={{$workflow.createdAt}}",
  "customerSatisfaction": "={{$json.sentiment === 'positive' ? 8 : $json.sentiment === 'negative' ? 4 : 6}}",
  "resolutionTime": "={{(new Date() - new Date($workflow.createdAt)) / 1000}}",
  "caseId": "={{$node["Create Service Case"].json.caseId}}"
}`
      },
      continueOnFail: true
    },

    {
      id: '13',
      name: 'Send Success Response',
      type: 'n8n-nodes-base.respondToWebhook',
      typeVersion: 1,
      position: [2000, 250],
      parameters: {
        respondWith: 'json',
        responseBody: `{
  "status": "success",
  "message": "Customer service request processed successfully",
  "caseId": "={{$node["Create Service Case"].json.caseId}}",
  "processingId": "={{$json.processingId}}",
  "timestamp": "={{new Date().toISOString()}}"
}`
      }
    },

    {
      id: '14',
      name: 'Handle Error',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 3,
      position: [1340, 500],
      parameters: {
        url: '={{$env.API_BASE_URL}}/api/monitoring/error-tracking',
        method: 'POST',
        sendBody: true,
        bodyContentType: 'json',
        jsonBody: `{
  "automationId": "insurance_customer_service",
  "error": "={{$json.error}}",
  "callId": "={{$json.callId}}",
  "timestamp": "={{new Date().toISOString()}}",
  "severity": "high"
}`
      },
      continueOnFail: true
    },

    {
      id: '15',
      name: 'Send Error Response',
      type: 'n8n-nodes-base.respondToWebhook',
      typeVersion: 1,
      position: [1560, 500],
      parameters: {
        respondWith: 'json',
        responseBody: `{
  "status": "error",
  "message": "Error processing customer service request",
  "error": "={{$json.error}}",
  "timestamp": "={{new Date().toISOString()}}"
}`,
        responseCode: 500
      }
    }
  ],

  connections: {
    '1': { main: [[{ node: '2', type: 'main', index: 0 }]] },
    '2': { main: [[{ node: '3', type: 'main', index: 0 }]] },
    '3': { main: [[{ node: '4', type: 'main', index: 0 }]] },
    '4': {
      main: [
        [{ node: '5', type: 'main', index: 0 }],
        [{ node: '6', type: 'main', index: 0 }]
      ]
    },
    '5': { main: [[{ node: '7', type: 'main', index: 0 }]] },
    '6': { main: [[{ node: '14', type: 'main', index: 0 }]] },
    '7': {
      main: [
        [{ node: '8', type: 'main', index: 0 }],
        [{ node: '9', type: 'main', index: 0 }],
        [{ node: '10', type: 'main', index: 0 }],
        [{ node: '11', type: 'main', index: 0 }]
      ]
    },
    '8': { main: [[{ node: '12', type: 'main', index: 0 }]] },
    '9': { main: [[{ node: '12', type: 'main', index: 0 }]] },
    '10': { main: [[{ node: '12', type: 'main', index: 0 }]] },
    '11': { main: [[{ node: '12', type: 'main', index: 0 }]] },
    '12': { main: [[{ node: '13', type: 'main', index: 0 }]] },
    '14': { main: [[{ node: '15', type: 'main', index: 0 }]] }
  },

  settings: {
    executionOrder: 'v1',
    saveManualExecutions: true,
    saveExecutionProgress: true,
    saveDataErrorExecution: 'all',
    saveDataSuccessExecution: 'all',
    executionTimeout: 300,
    timezone: 'America/New_York'
  },

  monitoring: {
    healthCheckEndpoint: '/api/monitoring/automation-health',
    errorNotificationWebhook: '/api/monitoring/webhook/error',
    performanceMetricsEndpoint: '/api/monitoring/performance',
    alertThresholds: {
      executionTime: 60000, // 60 seconds
      errorRate: 0.05, // 5%
      memoryUsage: 512 // 512MB
    }
  }
};

/**
 * Standard n8n Workflow Generator
 */
export function generateN8nWorkflow(
  templateId: string,
  workflowConfig: {
    name: string;
    description: string;
    webhookPath: string;
    customNodes?: Partial<N8nNode>[];
    industry?: 'insurance' | 'healthcare' | 'finance';
    monitoringEnabled?: boolean;
  }
): N8nWorkflowPattern {
  const baseWorkflow = { ...INSURANCE_CUSTOMER_SERVICE_WORKFLOW };

  // Customize for template
  baseWorkflow.id = templateId;
  baseWorkflow.name = workflowConfig.name;
  baseWorkflow.description = workflowConfig.description;

  // Update webhook path
  baseWorkflow.nodes[0].parameters.path = workflowConfig.webhookPath;

  // Add custom nodes if provided
  if (workflowConfig.customNodes) {
    workflowConfig.customNodes.forEach((customNode, index) => {
      const nodeId = `custom_${index + 20}`;
      baseWorkflow.nodes.push({
        id: nodeId,
        name: customNode.name || `Custom Node ${index + 1}`,
        type: customNode.type || 'n8n-nodes-base.httpRequest',
        typeVersion: customNode.typeVersion || 3,
        position: customNode.position || [1800 + (index * 200), 300],
        parameters: customNode.parameters || {},
        ...customNode
      });
    });
  }

  return baseWorkflow;
}

/**
 * n8n Best Practices Configuration
 */
export const N8N_BEST_PRACTICES = {
  errorHandling: {
    continueOnFail: true,
    retryOnFail: true,
    maxRetries: 3,
    waitBetweenTries: 2000
  },

  performance: {
    executeOnce: false,
    alwaysOutputData: false,
    timeout: 30000
  },

  security: {
    validateInputData: true,
    sanitizeOutputData: true,
    useCredentialStore: true
  },

  monitoring: {
    logExecutions: true,
    trackPerformance: true,
    alertOnFailure: true,
    healthChecks: true
  }
};