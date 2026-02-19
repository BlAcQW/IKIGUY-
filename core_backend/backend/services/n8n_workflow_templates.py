"""
N8N workflow templates for enhanced helpdesk automation.
Creates comprehensive workflows that integrate VAPI, RAG, Freshdesk, and analytics.
"""

import json
import uuid
from typing import Dict, List, Any
from datetime import datetime

class N8NWorkflowTemplates:
    """Service for generating N8N workflow templates."""

    def __init__(self):
        self.supabase_url = f"https://ljzbzjgvwzivpmlmuxhx.supabase.co"
        self.vonage_api_url = "https://api.nexmo.com"
        self.freshdesk_url = "https://ailabs-888099064326049059.myfreshworks.com"

    def create_complete_helpdesk_workflow(self, company_name: str, vapi_assistant_id: str) -> Dict[str, Any]:
        """
        Create complete N8N workflow for helpdesk automation.
        Flow: VAPI webhook → classify → RAG/answer → escalate → Freshdesk → notify → analytics

        Args:
            company_name: Company name for workflow identification
            vapi_assistant_id: VAPI assistant ID for integration

        Returns:
            Complete N8N workflow JSON
        """
        workflow_id = f"helpdesk-{uuid.uuid4().hex[:8]}"

        workflow = {
            "name": f"{company_name} - Complete Helpdesk Automation",
            "active": True,
            "nodes": [
                self._create_webhook_trigger_node(),
                self._create_extract_call_data_node(),
                self._create_classify_intent_node(),
                self._create_rag_query_node(),
                self._create_confidence_check_node(),
                self._create_answer_response_node(),
                self._create_escalation_decision_node(),
                self._create_freshdesk_ticket_node(),
                self._create_vonage_callback_node(),
                self._create_supabase_logging_node(),
                self._create_analytics_event_node(),
                self._create_metabase_sync_node()
            ],
            "connections": self._create_workflow_connections(),
            "settings": {
                "executionOrder": "v1",
                "saveDataErrorExecution": "all",
                "saveDataSuccessExecution": "all",
                "saveExecutionProgress": True,
                "saveManualExecutions": True,
                "callerPolicy": "workflowsFromSameOwner",
                "errorWorkflow": "",
                "timezone": "America/New_York"
            },
            "staticData": {
                "company_name": company_name,
                "vapi_assistant_id": vapi_assistant_id,
                "created_at": datetime.utcnow().isoformat()
            },
            "meta": {
                "templateCredsSetupCompleted": True
            },
            "pinData": {},
            "versionId": "1"
        }

        return workflow

    def _create_webhook_trigger_node(self) -> Dict[str, Any]:
        """Create VAPI webhook trigger node."""
        return {
            "parameters": {
                "httpMethod": "POST",
                "path": "vapi-helpdesk-webhook",
                "responseMode": "responseNode",
                "options": {}
            },
            "id": "webhook-trigger",
            "name": "VAPI Webhook Trigger",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 1,
            "position": [100, 200],
            "webhookId": str(uuid.uuid4())
        }

    def _create_extract_call_data_node(self) -> Dict[str, Any]:
        """Extract and structure call data from VAPI webhook."""
        return {
            "parameters": {
                "jsCode": """
// Extract call data from VAPI webhook
const payload = $input.all()[0].json;

return {
  call_id: payload.call?.id || 'unknown',
  customer_phone: payload.call?.customer?.number || payload.phoneNumber,
  customer_email: payload.call?.customer?.email,
  transcript: payload.transcript || payload.message,
  call_status: payload.call?.status || 'completed',
  call_duration: payload.call?.endedAt ?
    new Date(payload.call.endedAt) - new Date(payload.call.startedAt) : 0,
  timestamp: new Date().toISOString(),
  assistant_id: payload.call?.assistantId,
  call_type: payload.type || 'voice_call'
};
                """
            },
            "id": "extract-call-data",
            "name": "Extract Call Data",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [300, 200]
        }

    def _create_classify_intent_node(self) -> Dict[str, Any]:
        """Classify customer intent using OpenAI."""
        return {
            "parameters": {
                "resource": "text",
                "operation": "complete",
                "model": "gpt-3.5-turbo",
                "prompt": """
Classify the customer intent from this call transcript. Return only the classification:

Transcript: {{ $json.transcript }}

Classifications:
- information_request: Customer wants information about products/services
- technical_support: Customer has technical issues or questions
- billing_inquiry: Customer has billing or payment questions
- appointment_booking: Customer wants to schedule an appointment
- complaint: Customer is filing a complaint or expressing dissatisfaction
- general_inquiry: General questions not fitting other categories
- emergency: Urgent issues requiring immediate attention

Intent:
                """,
                "options": {
                    "temperature": 0.1,
                    "maxTokens": 50
                }
            },
            "id": "classify-intent",
            "name": "Classify Intent",
            "type": "n8n-nodes-base.openAi",
            "typeVersion": 1,
            "position": [500, 200]
        }

    def _create_rag_query_node(self) -> Dict[str, Any]:
        """Query RAG system for relevant information."""
        return {
            "parameters": {
                "requestMethod": "POST",
                "url": "https://api.ailabsafrica.com/helpdesk/rag/query",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "Authorization",
                            "value": "Bearer {{ $credentials.ailabs_api.access_token }}"
                        },
                        {
                            "name": "Content-Type",
                            "value": "application/json"
                        }
                    ]
                },
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {
                            "name": "query",
                            "value": "={{ $node['Extract Call Data'].json.transcript }}"
                        },
                        {
                            "name": "company_name",
                            "value": "={{ $workflow.staticData.company_name }}"
                        },
                        {
                            "name": "context",
                            "value": "={{ { 'intent': $node['Classify Intent'].json.choices[0].text.trim(), 'call_id': $node['Extract Call Data'].json.call_id } }}"
                        }
                    ]
                },
                "options": {
                    "timeout": 30000
                }
            },
            "id": "rag-query",
            "name": "RAG Knowledge Query",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4,
            "position": [700, 200]
        }

    def _create_confidence_check_node(self) -> Dict[str, Any]:
        """Check RAG response confidence for escalation decision."""
        return {
            "parameters": {
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "leftValue": "",
                        "typeValidation": "strict"
                    },
                    "conditions": [
                        {
                            "id": "high-confidence",
                            "leftValue": "={{ $json.confidence }}",
                            "rightValue": 0.7,
                            "operator": {
                                "type": "number",
                                "operation": "gte"
                            }
                        },
                        {
                            "id": "escalation-needed",
                            "leftValue": "={{ $json.should_escalate }}",
                            "rightValue": "true",
                            "operator": {
                                "type": "boolean",
                                "operation": "equal"
                            }
                        }
                    ],
                    "combineOperation": "any"
                },
                "options": {}
            },
            "id": "confidence-check",
            "name": "Confidence & Escalation Check",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": [900, 200]
        }

    def _create_answer_response_node(self) -> Dict[str, Any]:
        """Send answer back to customer via VAPI."""
        return {
            "parameters": {
                "requestMethod": "POST",
                "url": "https://api.vapi.ai/call/{{ $node['Extract Call Data'].json.call_id }}/respond",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "Authorization",
                            "value": "Bearer {{ $credentials.vapi.private_key }}"
                        },
                        {
                            "name": "Content-Type",
                            "value": "application/json"
                        }
                    ]
                },
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {
                            "name": "message",
                            "value": "={{ $node['RAG Knowledge Query'].json.answer }}"
                        },
                        {
                            "name": "endCall",
                            "value": "={{ $node['RAG Knowledge Query'].json.confidence > 0.8 ? true : false }}"
                        }
                    ]
                }
            },
            "id": "answer-response",
            "name": "Send Answer to Customer",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4,
            "position": [1100, 100]
        }

    def _create_escalation_decision_node(self) -> Dict[str, Any]:
        """Route to escalation path based on confidence/flags."""
        return {
            "parameters": {
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "leftValue": "",
                        "typeValidation": "strict"
                    },
                    "conditions": [
                        {
                            "id": "needs-escalation",
                            "leftValue": "={{ $node['RAG Knowledge Query'].json.should_escalate }}",
                            "rightValue": "true",
                            "operator": {
                                "type": "boolean",
                                "operation": "equal"
                            }
                        }
                    ],
                    "combineOperation": "any"
                }
            },
            "id": "escalation-decision",
            "name": "Escalation Decision",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": [1100, 300]
        }

    def _create_freshdesk_ticket_node(self) -> Dict[str, Any]:
        """Create Freshdesk ticket for escalated cases."""
        return {
            "parameters": {
                "requestMethod": "POST",
                "url": f"{self.freshdesk_url}/api/v2/tickets",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "Authorization",
                            "value": "Basic {{ $credentials.freshdesk.encoded_key }}"
                        },
                        {
                            "name": "Content-Type",
                            "value": "application/json"
                        }
                    ]
                },
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {
                            "name": "subject",
                            "value": "Escalated Call: {{ $node['Extract Call Data'].json.transcript.substring(0, 50) }}..."
                        },
                        {
                            "name": "description",
                            "value": """**Escalated Voice Call**

**Customer:** {{ $node['Extract Call Data'].json.customer_phone }}
**Call ID:** {{ $node['Extract Call Data'].json.call_id }}
**Intent:** {{ $node['Classify Intent'].json.choices[0].text.trim() }}

**Transcript:**
{{ $node['Extract Call Data'].json.transcript }}

**Escalation Reason:** {{ $node['RAG Knowledge Query'].json.escalation_reason }}

**RAG Response:** {{ $node['RAG Knowledge Query'].json.answer }}
**Confidence:** {{ $node['RAG Knowledge Query'].json.confidence }}"""
                        },
                        {
                            "name": "email",
                            "value": "={{ $node['Extract Call Data'].json.customer_email || 'customer+' + $node['Extract Call Data'].json.call_id + '@ailabsafrica.com' }}"
                        },
                        {
                            "name": "priority",
                            "value": "={{ $node['RAG Knowledge Query'].json.escalation_reason?.includes('urgent') ? 4 : 2 }}"
                        },
                        {
                            "name": "status",
                            "value": 2
                        },
                        {
                            "name": "source",
                            "value": 7
                        },
                        {
                            "name": "tags",
                            "value": ["vapi-escalation", "voice-call"]
                        }
                    ]
                }
            },
            "id": "create-freshdesk-ticket",
            "name": "Create Freshdesk Ticket",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4,
            "position": [1300, 400]
        }

    def _create_vonage_callback_node(self) -> Dict[str, Any]:
        """Schedule callback via Vonage for high priority escalations."""
        return {
            "parameters": {
                "requestMethod": "POST",
                "url": f"{self.vonage_api_url}/v1/calls",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "Authorization",
                            "value": "Bearer {{ $credentials.vonage.jwt_token }}"
                        },
                        {
                            "name": "Content-Type",
                            "value": "application/json"
                        }
                    ]
                },
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {
                            "name": "to",
                            "value": [{"type": "phone", "number": "={{ $node['Extract Call Data'].json.customer_phone }}"}]
                        },
                        {
                            "name": "from",
                            "value": {"type": "phone", "number": "+1234567890"}
                        },
                        {
                            "name": "answer_url",
                            "value": ["https://api.ailabsafrica.com/vonage/callback-answer"]
                        },
                        {
                            "name": "answer_method",
                            "value": "GET"
                        }
                    ]
                }
            },
            "id": "vonage-callback",
            "name": "Schedule Vonage Callback",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4,
            "position": [1500, 500]
        }

    def _create_supabase_logging_node(self) -> Dict[str, Any]:
        """Log call details and outcomes to Supabase."""
        return {
            "parameters": {
                "operation": "insert",
                "table": "helpdesk_call_logs",
                "data": """{{
  {
    "call_id": $node['Extract Call Data'].json.call_id,
    "customer_phone": $node['Extract Call Data'].json.customer_phone,
    "customer_email": $node['Extract Call Data'].json.customer_email,
    "transcript": $node['Extract Call Data'].json.transcript,
    "intent": $node['Classify Intent'].json.choices[0].text.trim(),
    "rag_confidence": $node['RAG Knowledge Query'].json.confidence,
    "rag_answer": $node['RAG Knowledge Query'].json.answer,
    "escalated": ($node['RAG Knowledge Query'].json.should_escalate ? true : false),
    "escalation_reason": $node['RAG Knowledge Query'].json.escalation_reason,
    "freshdesk_ticket_id": $node['Create Freshdesk Ticket']?.json?.id,
    "call_duration": $node['Extract Call Data'].json.call_duration,
    "timestamp": $node['Extract Call Data'].json.timestamp,
    "company_name": $workflow.staticData.company_name,
    "assistant_id": $workflow.staticData.vapi_assistant_id
  }
}}"""
            },
            "id": "supabase-logging",
            "name": "Log to Supabase",
            "type": "n8n-nodes-base.supabase",
            "typeVersion": 1,
            "position": [1300, 100]
        }

    def _create_analytics_event_node(self) -> Dict[str, Any]:
        """Send analytics event for dashboard metrics."""
        return {
            "parameters": {
                "requestMethod": "POST",
                "url": "https://api.ailabsafrica.com/analytics/events",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "Authorization",
                            "value": "Bearer {{ $credentials.ailabs_api.access_token }}"
                        },
                        {
                            "name": "Content-Type",
                            "value": "application/json"
                        }
                    ]
                },
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {
                            "name": "event_type",
                            "value": "helpdesk_call_completed"
                        },
                        {
                            "name": "properties",
                            "value": """{{
  {
    "call_id": $node['Extract Call Data'].json.call_id,
    "company": $workflow.staticData.company_name,
    "intent": $node['Classify Intent'].json.choices[0].text.trim(),
    "rag_confidence": $node['RAG Knowledge Query'].json.confidence,
    "escalated": ($node['RAG Knowledge Query'].json.should_escalate ? true : false),
    "call_duration": $node['Extract Call Data'].json.call_duration,
    "resolution_method": ($node['RAG Knowledge Query'].json.should_escalate ? "escalated" : "self_service"),
    "customer_satisfaction": null,
    "first_contact_resolution": (!$node['RAG Knowledge Query'].json.should_escalate ? true : false)
  }
}}"""
                        },
                        {
                            "name": "timestamp",
                            "value": "={{ new Date().toISOString() }}"
                        }
                    ]
                }
            },
            "id": "analytics-event",
            "name": "Send Analytics Event",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4,
            "position": [1500, 100]
        }

    def _create_metabase_sync_node(self) -> Dict[str, Any]:
        """Trigger Metabase data refresh for dashboards."""
        return {
            "parameters": {
                "requestMethod": "POST",
                "url": "https://metabase.ailabsafrica.com/api/card/{{ $credentials.metabase.helpdesk_dashboard_id }}/refresh",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "X-Metabase-Session",
                            "value": "{{ $credentials.metabase.session_token }}"
                        }
                    ]
                }
            },
            "id": "metabase-sync",
            "name": "Refresh Metabase Dashboard",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4,
            "position": [1700, 100]
        }

    def _create_workflow_connections(self) -> Dict[str, Any]:
        """Create connections between workflow nodes."""
        return {
            "VAPI Webhook Trigger": {
                "main": [
                    [
                        {
                            "node": "Extract Call Data",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Extract Call Data": {
                "main": [
                    [
                        {
                            "node": "Classify Intent",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Classify Intent": {
                "main": [
                    [
                        {
                            "node": "RAG Knowledge Query",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "RAG Knowledge Query": {
                "main": [
                    [
                        {
                            "node": "Confidence & Escalation Check",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Confidence & Escalation Check": {
                "main": [
                    [
                        {
                            "node": "Send Answer to Customer",
                            "type": "main",
                            "index": 0
                        }
                    ],
                    [
                        {
                            "node": "Escalation Decision",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Send Answer to Customer": {
                "main": [
                    [
                        {
                            "node": "Log to Supabase",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Escalation Decision": {
                "main": [
                    [],
                    [
                        {
                            "node": "Create Freshdesk Ticket",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Create Freshdesk Ticket": {
                "main": [
                    [
                        {
                            "node": "Schedule Vonage Callback",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Schedule Vonage Callback": {
                "main": [
                    [
                        {
                            "node": "Log to Supabase",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Log to Supabase": {
                "main": [
                    [
                        {
                            "node": "Send Analytics Event",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Send Analytics Event": {
                "main": [
                    [
                        {
                            "node": "Refresh Metabase Dashboard",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            }
        }

    def create_sla_monitoring_workflow(self, company_name: str) -> Dict[str, Any]:
        """
        Create SLA monitoring workflow for tracking response times and escalations.

        Args:
            company_name: Company name for workflow identification

        Returns:
            SLA monitoring workflow JSON
        """
        return {
            "name": f"{company_name} - SLA Monitoring",
            "active": True,
            "nodes": [
                {
                    "parameters": {
                        "rule": {
                            "interval": [
                                {
                                    "field": "minutes",
                                    "minutesInterval": 15
                                }
                            ]
                        }
                    },
                    "id": "sla-check-trigger",
                    "name": "SLA Check Trigger",
                    "type": "n8n-nodes-base.cron",
                    "typeVersion": 1,
                    "position": [100, 200]
                },
                {
                    "parameters": {
                        "operation": "select",
                        "table": "helpdesk_call_logs",
                        "where": "created_at > NOW() - INTERVAL '24 hours'"
                    },
                    "id": "get-recent-calls",
                    "name": "Get Recent Calls",
                    "type": "n8n-nodes-base.supabase",
                    "typeVersion": 1,
                    "position": [300, 200]
                }
            ],
            "connections": {
                "SLA Check Trigger": {
                    "main": [
                        [
                            {
                                "node": "Get Recent Calls",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                }
            }
        }

# Global template service instance
n8n_workflow_templates = N8NWorkflowTemplates()