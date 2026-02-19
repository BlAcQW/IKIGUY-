/**
 * Comprehensive Monitoring Integration Standards
 *
 * Standardized monitoring, analytics, and health tracking for all automation templates.
 * Based on successful implementations in Claims Processing and Medical Exam Scheduling.
 */

export interface MonitoringIntegration {
  enabled: boolean;
  healthTracking: boolean;
  performanceMetrics: boolean;
  costTracking: boolean;
  realTimeAlerts: boolean;
  complianceMonitoring: boolean;
  endpoints: MonitoringEndpoints;
  alertThresholds: AlertThresholds;
  dashboardConfig: DashboardConfig;
}

export interface MonitoringEndpoints {
  healthCheck: string;
  metricsCollection: string;
  errorTracking: string;
  performanceAnalytics: string;
  complianceAudit: string;
  webhookIntegration: string;
}

export interface AlertThresholds {
  errorRate: number; // percentage
  responseTime: number; // milliseconds
  costSpike: number; // multiplier
  failureCount: number; // absolute count
  complianceViolation: boolean;
}

export interface DashboardConfig {
  realTimeMetrics: string[];
  historicalTrends: string[];
  complianceReports: string[];
  costAnalytics: string[];
  customWidgets: DashboardWidget[];
}

export interface DashboardWidget {
  id: string;
  type: 'chart' | 'metric' | 'table' | 'alert';
  title: string;
  dataSource: string;
  refreshInterval: number;
  config: Record<string, any>;
}

/**
 * Standard Monitoring Configuration for Insurance Templates
 */
export const INSURANCE_MONITORING_STANDARDS: MonitoringIntegration = {
  enabled: true,
  healthTracking: true,
  performanceMetrics: true,
  costTracking: true,
  realTimeAlerts: true,
  complianceMonitoring: true,

  endpoints: {
    healthCheck: '{{api_base_url}}/api/monitoring/automation-health',
    metricsCollection: '{{api_base_url}}/api/monitoring/metrics',
    errorTracking: '{{api_base_url}}/api/monitoring/error-tracking',
    performanceAnalytics: '{{api_base_url}}/api/monitoring/performance',
    complianceAudit: '{{api_base_url}}/api/monitoring/compliance',
    webhookIntegration: '{{api_base_url}}/api/monitoring/webhook/{{template_id}}'
  },

  alertThresholds: {
    errorRate: 5.0, // 5%
    responseTime: 30000, // 30 seconds
    costSpike: 2.0, // 200% of baseline
    failureCount: 10, // 10 failures in 5 minutes
    complianceViolation: true
  },

  dashboardConfig: {
    realTimeMetrics: [
      'execution_count',
      'success_rate',
      'average_response_time',
      'cost_per_execution',
      'active_workflows',
      'error_rate'
    ],
    historicalTrends: [
      'daily_execution_volume',
      'weekly_success_trends',
      'monthly_cost_analysis',
      'quarterly_performance_review'
    ],
    complianceReports: [
      'naic_compliance_score',
      'sox_audit_trail',
      'data_retention_status',
      'regulatory_violations'
    ],
    costAnalytics: [
      'cost_breakdown_by_service',
      'cost_trend_analysis',
      'budget_variance',
      'roi_metrics'
    ],
    customWidgets: [
      {
        id: 'customer_satisfaction',
        type: 'metric',
        title: 'Customer Satisfaction Score',
        dataSource: 'vapi_analytics',
        refreshInterval: 30000,
        config: {
          metric: 'average_satisfaction',
          format: 'percentage',
          target: 85
        }
      },
      {
        id: 'claims_processing_time',
        type: 'chart',
        title: 'Claims Processing Time Trend',
        dataSource: 'claims_metrics',
        refreshInterval: 60000,
        config: {
          chartType: 'line',
          timeRange: '24h',
          aggregation: 'average'
        }
      }
    ]
  }
};

/**
 * Healthcare Monitoring Standards (HIPAA Compliant)
 */
export const HEALTHCARE_MONITORING_STANDARDS: MonitoringIntegration = {
  ...INSURANCE_MONITORING_STANDARDS,
  complianceMonitoring: true,

  endpoints: {
    ...INSURANCE_MONITORING_STANDARDS.endpoints,
    complianceAudit: '{{api_base_url}}/api/monitoring/hipaa-compliance'
  },

  dashboardConfig: {
    ...INSURANCE_MONITORING_STANDARDS.dashboardConfig,
    complianceReports: [
      'hipaa_compliance_score',
      'audit_trail_completeness',
      'data_encryption_status',
      'patient_data_access_log'
    ],
    customWidgets: [
      {
        id: 'appointment_efficiency',
        type: 'metric',
        title: 'Appointment Scheduling Efficiency',
        dataSource: 'appointment_metrics',
        refreshInterval: 30000,
        config: {
          metric: 'booking_success_rate',
          format: 'percentage',
          target: 90
        }
      },
      {
        id: 'no_show_prediction_accuracy',
        type: 'chart',
        title: 'No-Show Prediction Accuracy',
        dataSource: 'prediction_analytics',
        refreshInterval: 60000,
        config: {
          chartType: 'gauge',
          timeRange: '7d',
          target: 85
        }
      }
    ]
  }
};

/**
 * Monitoring Configuration Generator
 */
export function generateMonitoringConfig(
  templateId: string,
  industry: 'insurance' | 'healthcare' | 'finance',
  customConfig?: Partial<MonitoringIntegration>
): MonitoringIntegration {
  const baseConfig = industry === 'healthcare'
    ? HEALTHCARE_MONITORING_STANDARDS
    : INSURANCE_MONITORING_STANDARDS;

  const config = {
    ...baseConfig,
    ...customConfig,
    endpoints: {
      ...baseConfig.endpoints,
      webhookIntegration: baseConfig.endpoints.webhookIntegration.replace('{{template_id}}', templateId),
      ...customConfig?.endpoints
    }
  };

  return config;
}

/**
 * n8n Monitoring Integration Nodes
 */
export const N8N_MONITORING_NODES = {
  healthCheckNode: {
    id: 'health_check',
    name: 'Update Automation Health',
    type: 'n8n-nodes-base.httpRequest',
    typeVersion: 3,
    parameters: {
      url: '={{$env.API_BASE_URL}}/api/monitoring/automation-health',
      method: 'POST',
      sendBody: true,
      bodyContentType: 'json',
      jsonBody: `{
        "automationId": "={{$workflow.name}}",
        "templateId": "={{$env.TEMPLATE_ID}}",
        "tenantId": "={{$env.TENANT_ID}}",
        "executionId": "={{$execution.id}}",
        "status": "completed",
        "timestamp": "={{new Date().toISOString()}}",
        "processingTime": "={{(new Date() - new Date($execution.startedAt)) / 1000}}",
        "memoryUsage": "={{$env.MEMORY_USAGE}}",
        "nodeCount": "={{Object.keys($workflow.nodes).length}}"
      }`,
      options: {
        timeout: 10000,
        retry: {
          enabled: true,
          maxRetries: 2
        }
      }
    },
    continueOnFail: true
  },

  errorTrackingNode: {
    id: 'error_tracking',
    name: 'Track Execution Error',
    type: 'n8n-nodes-base.httpRequest',
    typeVersion: 3,
    parameters: {
      url: '={{$env.API_BASE_URL}}/api/monitoring/error-tracking',
      method: 'POST',
      sendBody: true,
      bodyContentType: 'json',
      jsonBody: `{
        "automationId": "={{$workflow.name}}",
        "executionId": "={{$execution.id}}",
        "error": "={{$json.error}}",
        "errorNode": "={{$json.errorNode}}",
        "timestamp": "={{new Date().toISOString()}}",
        "severity": "high",
        "context": "={{$json}}"
      }`,
      options: {
        timeout: 5000
      }
    },
    continueOnFail: true
  },

  performanceTrackingNode: {
    id: 'performance_tracking',
    name: 'Track Performance Metrics',
    type: 'n8n-nodes-base.httpRequest',
    typeVersion: 3,
    parameters: {
      url: '={{$env.API_BASE_URL}}/api/monitoring/performance',
      method: 'POST',
      sendBody: true,
      bodyContentType: 'json',
      jsonBody: `{
        "automationId": "={{$workflow.name}}",
        "executionId": "={{$execution.id}}",
        "metrics": {
          "executionTime": "={{(new Date() - new Date($execution.startedAt)) / 1000}}",
          "nodeExecutions": "={{$json.nodeExecutions}}",
          "dataTransferred": "={{$json.dataSize}}",
          "apiCalls": "={{$json.apiCallCount}}",
          "cost": "={{$json.estimatedCost}}"
        },
        "timestamp": "={{new Date().toISOString()}}"
      }`
    },
    continueOnFail: true
  },

  costTrackingNode: {
    id: 'cost_tracking',
    name: 'Track Execution Costs',
    type: 'n8n-nodes-base.function',
    typeVersion: 1,
    parameters: {
      functionCode: `
// Calculate execution costs
const executionData = items[0].json;

// Base execution cost
let totalCost = 0.001; // Base n8n execution cost

// VAPI call costs
if (executionData.vapiCallDuration) {
  totalCost += (executionData.vapiCallDuration / 60) * 0.02; // $0.02 per minute
}

// AI/LLM costs
if (executionData.aiApiCalls) {
  totalCost += executionData.aiApiCalls * 0.001; // $0.001 per API call
}

// External API costs
if (executionData.externalApiCalls) {
  totalCost += executionData.externalApiCalls * 0.0001; // $0.0001 per call
}

// Storage costs
if (executionData.dataStored) {
  totalCost += (executionData.dataStored / 1024 / 1024) * 0.00001; // $0.00001 per MB
}

return [{
  json: {
    ...executionData,
    cost: {
      total: totalCost,
      breakdown: {
        execution: 0.001,
        vapi: executionData.vapiCallDuration ? (executionData.vapiCallDuration / 60) * 0.02 : 0,
        ai: executionData.aiApiCalls ? executionData.aiApiCalls * 0.001 : 0,
        api: executionData.externalApiCalls ? executionData.externalApiCalls * 0.0001 : 0,
        storage: executionData.dataStored ? (executionData.dataStored / 1024 / 1024) * 0.00001 : 0
      }
    },
    timestamp: new Date().toISOString()
  }
}];
`
    }
  },

  alertingNode: {
    id: 'real_time_alerting',
    name: 'Send Real-time Alert',
    type: 'n8n-nodes-base.httpRequest',
    typeVersion: 3,
    parameters: {
      url: '={{$env.API_BASE_URL}}/api/monitoring/alerts',
      method: 'POST',
      sendBody: true,
      bodyContentType: 'json',
      jsonBody: `{
        "automationId": "={{$workflow.name}}",
        "alertType": "={{$json.alertType}}",
        "severity": "={{$json.severity}}",
        "message": "={{$json.message}}",
        "threshold": "={{$json.threshold}}",
        "actualValue": "={{$json.actualValue}}",
        "timestamp": "={{new Date().toISOString()}}",
        "channels": ["email", "slack", "webhook"]
      }`
    },
    continueOnFail: true
  }
};

/**
 * Monitoring Workflow Enhancement
 */
export function enhanceWorkflowWithMonitoring(
  workflow: any,
  monitoringConfig: MonitoringIntegration
): any {
  const enhancedWorkflow = { ...workflow };

  // Add monitoring nodes
  const monitoringNodes = [
    N8N_MONITORING_NODES.healthCheckNode,
    N8N_MONITORING_NODES.errorTrackingNode,
    N8N_MONITORING_NODES.performanceTrackingNode,
    N8N_MONITORING_NODES.costTrackingNode
  ];

  // Add monitoring nodes to workflow
  enhancedWorkflow.nodes = [...enhancedWorkflow.nodes, ...monitoringNodes];

  // Add monitoring connections
  const lastNodeId = workflow.nodes[workflow.nodes.length - 1].id;
  enhancedWorkflow.connections[lastNodeId] = {
    main: [[{ node: 'health_check', type: 'main', index: 0 }]]
  };

  enhancedWorkflow.connections['health_check'] = {
    main: [[{ node: 'performance_tracking', type: 'main', index: 0 }]]
  };

  enhancedWorkflow.connections['performance_tracking'] = {
    main: [[{ node: 'cost_tracking', type: 'main', index: 0 }]]
  };

  // Add error handling connections
  workflow.nodes.forEach(node => {
    if (node.type !== 'n8n-nodes-base.respondToWebhook') {
      // Add error connection to error tracking node
      if (!enhancedWorkflow.connections[node.id]) {
        enhancedWorkflow.connections[node.id] = { main: [] };
      }
      enhancedWorkflow.connections[node.id].error = [
        [{ node: 'error_tracking', type: 'main', index: 0 }]
      ];
    }
  });

  return enhancedWorkflow;
}

/**
 * Real-time Monitoring Dashboard Configuration
 */
export const REAL_TIME_DASHBOARD_CONFIG = {
  refreshInterval: 5000, // 5 seconds
  autoRefresh: true,
  themes: {
    light: {
      primary: '#007bff',
      success: '#28a745',
      warning: '#ffc107',
      danger: '#dc3545'
    },
    dark: {
      primary: '#0d6efd',
      success: '#198754',
      warning: '#ffc107',
      danger: '#dc3545'
    }
  },
  widgets: {
    executionRate: {
      type: 'metric',
      title: 'Executions/Min',
      size: 'small',
      format: 'number'
    },
    successRate: {
      type: 'gauge',
      title: 'Success Rate',
      size: 'medium',
      target: 95
    },
    responseTime: {
      type: 'line-chart',
      title: 'Response Time Trend',
      size: 'large',
      timeRange: '1h'
    },
    costTrend: {
      type: 'area-chart',
      title: 'Cost Trend',
      size: 'medium',
      timeRange: '24h'
    }
  }
};