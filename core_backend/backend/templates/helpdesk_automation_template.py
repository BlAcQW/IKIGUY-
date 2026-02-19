"""
Helpdesk Automation Template for MTN Ghana Customer Support.

This template creates a comprehensive helpdesk automation that integrates:
- Freshdesk for ticket management
- Resend for email notifications
- Tavily for web search capabilities
- Calendly for appointment scheduling
- Supabase for data storage
- VAPI for voice interactions
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List

def create_helpdesk_automation_template() -> Dict[str, Any]:
    """
    Create a comprehensive helpdesk automation template for MTN Ghana.

    Returns:
        Dict containing the complete automation template configuration
    """

    # MTN Ghana company information
    mtn_ghana_info = {
        "company_name": "MTN Ghana",
        "website": "https://mtn.com.gh/",
        "description": "Leading telecommunications company in Ghana providing voice, data, and digital services",
        "services": [
            "Mobile voice and data services",
            "Internet and broadband",
            "Mobile money (MoMo)",
            "Digital services",
            "Enterprise solutions"
        ],
        "support_hours": "24/7 customer support",
        "contact_info": {
            "customer_service": "100",
            "whatsapp": "+233554300000",
            "website": "https://mtn.com.gh/",
            "app": "MyMTN App"
        }
    }

    # System prompt for the voice agent
    system_prompt = f"""You are an intelligent customer service agent for {mtn_ghana_info['company_name']}, Ghana's leading telecommunications provider.

COMPANY CONTEXT:
- {mtn_ghana_info['description']}
- Services: {', '.join(mtn_ghana_info['services'])}
- Website: {mtn_ghana_info['website']}
- Customer Service: {mtn_ghana_info['contact_info']['customer_service']}
- WhatsApp: {mtn_ghana_info['contact_info']['whatsapp']}

YOUR ROLE:
You are a helpful, professional, and knowledgeable customer service representative. You can:
1. Answer questions about MTN services, plans, and pricing
2. Help with account issues and billing inquiries
3. Provide technical support for network and device issues
4. Create support tickets for complex issues
5. Schedule appointments with specialists
6. Search for current information when needed
7. Transfer calls to human agents when necessary

CAPABILITIES:
- Create tickets in Freshdesk for complex issues
- Send email notifications to customers
- Search the web for current information about MTN services
- Check calendar availability and schedule appointments
- Save all interactions to the database for quality assurance

TRANSFER PROTOCOL:
If a customer requests to speak with a human agent or if you encounter a question you cannot answer, politely explain that you'll transfer them to a human representative and use the transfer function.

TONE: Professional, helpful, and empathetic. Always greet customers warmly and thank them for choosing MTN Ghana.

LANGUAGE: Primarily English, but acknowledge that customers may speak local languages and offer to help in English.

Remember: You represent MTN Ghana's commitment to excellent customer service. Always strive to resolve issues efficiently while maintaining a positive customer experience."""

    # N8N Workflow Configuration
    n8n_workflow = {
        "name": "MTN Ghana Helpdesk Automation",
        "nodes": [
            {
                "id": "webhook-trigger",
                "name": "Webhook Trigger",
                "type": "n8n-nodes-base.webhook",
                "position": [240, 300],
                "parameters": {
                    "httpMethod": "POST",
                    "path": "mtn-helpdesk",
                    "responseMode": "responseNode",
                    "options": {}
                }
            },
            {
                "id": "determine-action",
                "name": "Determine Action",
                "type": "n8n-nodes-base.switch",
                "position": [460, 300],
                "parameters": {
                    "values": {
                        "options": [
                            {
                                "value": "create_ticket",
                                "conditions": {
                                    "options": {
                                        "caseSensitive": True,
                                        "leftValue": "={{$json.action}}",
                                        "operation": "equal",
                                        "rightValue": "create_ticket"
                                    }
                                }
                            },
                            {
                                "value": "send_email",
                                "conditions": {
                                    "options": {
                                        "caseSensitive": True,
                                        "leftValue": "={{$json.action}}",
                                        "operation": "equal",
                                        "rightValue": "send_email"
                                    }
                                }
                            },
                            {
                                "value": "search_web",
                                "conditions": {
                                    "options": {
                                        "caseSensitive": True,
                                        "leftValue": "={{$json.action}}",
                                        "operation": "equal",
                                        "rightValue": "search_web"
                                    }
                                }
                            },
                            {
                                "value": "schedule_appointment",
                                "conditions": {
                                    "options": {
                                        "caseSensitive": True,
                                        "leftValue": "={{$json.action}}",
                                        "operation": "equal",
                                        "rightValue": "schedule_appointment"
                                    }
                                }
                            },
                            {
                                "value": "save_interaction",
                                "conditions": {
                                    "options": {
                                        "caseSensitive": True,
                                        "leftValue": "={{$json.action}}",
                                        "operation": "equal",
                                        "rightValue": "save_interaction"
                                    }
                                }
                            }
                        ]
                    }
                }
            },
            {
                "id": "freshdesk-create-ticket",
                "name": "Create Freshdesk Ticket",
                "type": "n8n-nodes-base.httpRequest",
                "position": [720, 140],
                "parameters": {
                    "url": "={{$json.freshdesk_url}}/api/v2/tickets",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpBasicAuth",
                    "httpMethod": "POST",
                    "sendHeaders": True,
                    "headerParameters": {
                        "parameters": [
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
                                "value": "={{$json.ticket_subject}}"
                            },
                            {
                                "name": "description",
                                "value": "={{$json.ticket_description}}"
                            },
                            {
                                "name": "email",
                                "value": "={{$json.customer_email}}"
                            },
                            {
                                "name": "priority",
                                "value": "={{$json.priority || 2}}"
                            },
                            {
                                "name": "status",
                                "value": 2
                            },
                            {
                                "name": "source",
                                "value": 7
                            }
                        ]
                    }
                }
            },
            {
                "id": "resend-email",
                "name": "Send Email via Resend",
                "type": "n8n-nodes-base.httpRequest",
                "position": [720, 260],
                "parameters": {
                    "url": "https://api.resend.com/emails",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "httpMethod": "POST",
                    "sendHeaders": True,
                    "headerParameters": {
                        "parameters": [
                            {
                                "name": "Authorization",
                                "value": "Bearer ={{$json.resend_api_key}}"
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
                                "name": "from",
                                "value": "MTN Ghana Support <support@mtn.com.gh>"
                            },
                            {
                                "name": "to",
                                "value": ["ailabsafrica@gmail.com"]
                            },
                            {
                                "name": "subject",
                                "value": "={{$json.email_subject}}"
                            },
                            {
                                "name": "html",
                                "value": "={{$json.email_content}}"
                            }
                        ]
                    }
                }
            },
            {
                "id": "tavily-search",
                "name": "Search Web with Tavily",
                "type": "n8n-nodes-base.httpRequest",
                "position": [720, 380],
                "parameters": {
                    "url": "https://api.tavily.com/search",
                    "httpMethod": "POST",
                    "sendHeaders": True,
                    "headerParameters": {
                        "parameters": [
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
                                "name": "api_key",
                                "value": "={{$json.tavily_api_key}}"
                            },
                            {
                                "name": "query",
                                "value": "={{$json.search_query}}"
                            },
                            {
                                "name": "search_depth",
                                "value": "basic"
                            },
                            {
                                "name": "include_answer",
                                "value": True
                            },
                            {
                                "name": "include_domains",
                                "value": ["mtn.com.gh"]
                            },
                            {
                                "name": "max_results",
                                "value": 5
                            }
                        ]
                    }
                }
            },
            {
                "id": "calendly-availability",
                "name": "Check Calendly Availability",
                "type": "n8n-nodes-base.httpRequest",
                "position": [720, 500],
                "parameters": {
                    "url": "https://api.calendly.com/availability",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "httpMethod": "GET",
                    "sendHeaders": True,
                    "headerParameters": {
                        "parameters": [
                            {
                                "name": "Authorization",
                                "value": "Bearer ={{$json.calendly_api_key}}"
                            }
                        ]
                    },
                    "sendQuery": True,
                    "queryParameters": {
                        "parameters": [
                            {
                                "name": "start_time",
                                "value": "={{$json.start_time}}"
                            },
                            {
                                "name": "end_time",
                                "value": "={{$json.end_time}}"
                            }
                        ]
                    }
                }
            },
            {
                "id": "supabase-save",
                "name": "Save to Supabase",
                "type": "n8n-nodes-base.httpRequest",
                "position": [720, 620],
                "parameters": {
                    "url": "={{$json.supabase_url}}/rest/v1/helpdesk-assistant",
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
                    "httpMethod": "POST",
                    "sendHeaders": True,
                    "headerParameters": {
                        "parameters": [
                            {
                                "name": "Authorization",
                                "value": "Bearer ={{$json.supabase_key}}"
                            },
                            {
                                "name": "Content-Type",
                                "value": "application/json"
                            },
                            {
                                "name": "Prefer",
                                "value": "return=minimal"
                            }
                        ]
                    },
                    "sendBody": True,
                    "bodyParameters": {
                        "parameters": [
                            {
                                "name": "call_id",
                                "value": "={{$json.call_id}}"
                            },
                            {
                                "name": "customer_phone",
                                "value": "={{$json.customer_phone}}"
                            },
                            {
                                "name": "customer_email",
                                "value": "={{$json.customer_email}}"
                            },
                            {
                                "name": "interaction_type",
                                "value": "={{$json.interaction_type}}"
                            },
                            {
                                "name": "summary",
                                "value": "={{$json.interaction_summary}}"
                            },
                            {
                                "name": "resolution_status",
                                "value": "={{$json.resolution_status}}"
                            },
                            {
                                "name": "created_at",
                                "value": "={{new Date().toISOString()}}"
                            },
                            {
                                "name": "metadata",
                                "value": "={{JSON.stringify($json.metadata || {})}}"
                            }
                        ]
                    }
                }
            },
            {
                "id": "response-formatter",
                "name": "Format Response",
                "type": "n8n-nodes-base.function",
                "position": [940, 400],
                "parameters": {
                    "functionCode": """
const action = $input.first()?.json?.action;
const result = $input.first()?.json;

let response = {
    success: true,
    action: action,
    timestamp: new Date().toISOString()
};

switch(action) {
    case 'create_ticket':
        response.ticket_id = result.id;
        response.message = 'Support ticket created successfully';
        break;
    case 'send_email':
        response.email_id = result.id;
        response.message = 'Email sent successfully';
        break;
    case 'search_web':
        response.search_results = result.results;
        response.answer = result.answer;
        response.message = 'Web search completed';
        break;
    case 'schedule_appointment':
        response.availability = result.collection;
        response.message = 'Availability retrieved';
        break;
    case 'save_interaction':
        response.message = 'Interaction saved to database';
        break;
    default:
        response.message = 'Action completed';
}

return { json: response };
"""
                }
            },
            {
                "id": "webhook-response",
                "name": "Webhook Response",
                "type": "n8n-nodes-base.respondToWebhook",
                "position": [1160, 400],
                "parameters": {
                    "responseBody": "={{JSON.stringify($json)}}",
                    "options": {
                        "responseHeaders": {
                            "entries": [
                                {
                                    "name": "Content-Type",
                                    "value": "application/json"
                                }
                            ]
                        }
                    }
                }
            }
        ],
        "connections": {
            "Webhook Trigger": {
                "main": [
                    [
                        {
                            "node": "Determine Action",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Determine Action": {
                "main": [
                    [
                        {
                            "node": "Create Freshdesk Ticket",
                            "type": "main",
                            "index": 0
                        }
                    ],
                    [
                        {
                            "node": "Send Email via Resend",
                            "type": "main",
                            "index": 0
                        }
                    ],
                    [
                        {
                            "node": "Search Web with Tavily",
                            "type": "main",
                            "index": 0
                        }
                    ],
                    [
                        {
                            "node": "Check Calendly Availability",
                            "type": "main",
                            "index": 0
                        }
                    ],
                    [
                        {
                            "node": "Save to Supabase",
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
                            "node": "Format Response",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Send Email via Resend": {
                "main": [
                    [
                        {
                            "node": "Format Response",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Search Web with Tavily": {
                "main": [
                    [
                        {
                            "node": "Format Response",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Check Calendly Availability": {
                "main": [
                    [
                        {
                            "node": "Format Response",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Save to Supabase": {
                "main": [
                    [
                        {
                            "node": "Format Response",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Format Response": {
                "main": [
                    [
                        {
                            "node": "Webhook Response",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            }
        }
    }

    # Complete automation template
    template = {
        "id": "helpdesk-automation-mtn-ghana",
        "template_name": "MTN Ghana Helpdesk Automation",
        "description": "Comprehensive helpdesk automation for MTN Ghana customer support with voice AI, ticket management, email notifications, web search, appointment scheduling, and data logging",
        "category": "helpdesk",
        "industry_id": "generic",
        "industry_name": "Generic",
        "version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "tags": [
            "helpdesk",
            "customer-support",
            "telecommunications",
            "voice-ai",
            "ticket-management",
            "email-automation",
            "appointment-scheduling",
            "web-search",
            "data-logging"
        ],

        # Company and branding information
        "company_info": mtn_ghana_info,

        # VAPI Configuration
        "vapi_config": {
            "model": {
                "provider": "openai",
                "model": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 500,
                "system_message": system_prompt
            },
            "voice": {
                "provider": "elevenlabs",
                "voice_id": "burt",
                "stability": 0.5,
                "similarity_boost": 0.7,
                "optimize_streaming_latency": 3
            },
            "first_message": f"Hello! Thank you for calling {mtn_ghana_info['company_name']}. I'm your AI assistant here to help you with any questions or concerns you may have about our services. How can I assist you today?",
            "transfer_phone_number": "+12397783680",
            "server_url": "",  # Will be populated during deployment
            "server_url_secret": "",  # Will be populated during deployment
            "end_call_message": "Thank you for choosing MTN Ghana. Have a great day!",
            "max_duration_seconds": 600,
            "silence_timeout_seconds": 30,
            "response_delay_seconds": 0.4,
            "llm_request_delay_seconds": 0.1,
            "num_words_to_interrupt_assistant": 2,
            "max_interruptions": 3,
            "interruption_threshold": 100,
            "backchanneling_enabled": True,
            "background_sound": "office",
            "background_denoising_enabled": True
        },

        # N8N Workflow
        "n8n_workflow": n8n_workflow,

        # Integration configurations
        "integrations": {
            "freshdesk": {
                "enabled": True,
                "url": "https://ailabs-888099064326049059.myfreshworks.com/",
                "api_key_env": "FRESHDESK_API_KEY",
                "default_priority": 2,
                "default_status": 2,
                "source": 7  # API source
            },
            "resend": {
                "enabled": True,
                "api_key_env": "RESEND_API_KEY",
                "from_email": "MTN Ghana Support <support@mtn.com.gh>",
                "default_to": "ailabsafrica@gmail.com"
            },
            "tavily": {
                "enabled": True,
                "api_key_env": "TAVILY_API_KEY",
                "search_depth": "basic",
                "max_results": 5,
                "include_domains": ["mtn.com.gh"]
            },
            "calendly": {
                "enabled": True,
                "api_key_env": "CALENDLY_API_KEY",
                "user_uri": "",  # To be configured during setup
                "event_type_uri": ""  # To be configured during setup
            },
            "supabase": {
                "enabled": True,
                "url_env": "DEMO_SUPABASE_URL",
                "key_env": "DEMO_SUPABASE_SUPABASE_KEY",
                "table": "helpdesk-assistant",
                "schema": {
                    "call_id": "text",
                    "customer_phone": "text",
                    "customer_email": "text",
                    "interaction_type": "text",
                    "summary": "text",
                    "resolution_status": "text",
                    "created_at": "timestamp",
                    "metadata": "jsonb"
                }
            }
        },

        # Tools available to the AI agent
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "create_support_ticket",
                    "description": "Create a support ticket in Freshdesk for complex issues that require human intervention",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "subject": {
                                "type": "string",
                                "description": "Brief subject line for the ticket"
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of the customer's issue"
                            },
                            "customer_email": {
                                "type": "string",
                                "description": "Customer's email address"
                            },
                            "priority": {
                                "type": "integer",
                                "description": "Priority level: 1=Low, 2=Medium, 3=High, 4=Urgent",
                                "enum": [1, 2, 3, 4]
                            }
                        },
                        "required": ["subject", "description", "customer_email"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_email_notification",
                    "description": "Send email notification about the customer interaction",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "subject": {
                                "type": "string",
                                "description": "Email subject line"
                            },
                            "content": {
                                "type": "string",
                                "description": "HTML email content"
                            },
                            "customer_info": {
                                "type": "string",
                                "description": "Customer information for the email"
                            }
                        },
                        "required": ["subject", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_information",
                    "description": "Search for current information about MTN services, plans, or policies",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for current information"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_appointment_availability",
                    "description": "Check availability for scheduling appointments with MTN specialists",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Start date for availability check (ISO format)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date for availability check (ISO format)"
                            },
                            "appointment_type": {
                                "type": "string",
                                "description": "Type of appointment needed"
                            }
                        },
                        "required": ["start_date", "end_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "transfer_to_human",
                    "description": "Transfer the call to a human agent when requested or when unable to resolve the issue",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string",
                                "description": "Reason for transferring to human agent"
                            },
                            "summary": {
                                "type": "string",
                                "description": "Summary of the conversation so far"
                            }
                        },
                        "required": ["reason"]
                    }
                }
            }
        ],

        # Configuration parameters for deployment
        "config_parameters": {
            "phone_number": {
                "type": "string",
                "label": "Phone Number",
                "description": "VAPI phone number for the helpdesk",
                "required": True
            },
            "transfer_number": {
                "type": "string",
                "label": "Transfer Number",
                "description": "Phone number to transfer calls to human agents",
                "default": "+12397783680",
                "required": True
            },
            "freshdesk_domain": {
                "type": "string",
                "label": "Freshdesk Domain",
                "description": "Your Freshdesk domain URL",
                "default": "https://ailabs-888099064326049059.myfreshworks.com/",
                "required": True
            },
            "notification_email": {
                "type": "string",
                "label": "Notification Email",
                "description": "Email address to receive helpdesk notifications",
                "default": "ailabsafrica@gmail.com",
                "required": True
            },
            "company_name": {
                "type": "string",
                "label": "Company Name",
                "description": "Your company name for the voice agent",
                "default": "MTN Ghana",
                "required": True
            },
            "company_website": {
                "type": "string",
                "label": "Company Website",
                "description": "Your company website URL",
                "default": "https://mtn.com.gh/",
                "required": False
            }
        },

        # Deployment requirements
        "deployment_requirements": {
            "api_keys": [
                "VAPI_API_KEY",
                "OPENAI_API_KEY",
                "FRESHDESK_API_KEY",
                "RESEND_API_KEY",
                "TAVILY_API_KEY",
                "CALENDLY_API_KEY",
                "DEMO_SUPABASE_URL",
                "DEMO_SUPABASE_SUPABASE_KEY"
            ],
            "external_services": [
                "vapi.ai",
                "openai.com",
                "freshdesk.com",
                "resend.com",
                "tavily.com",
                "calendly.com",
                "supabase.com"
            ],
            "database_tables": [
                {
                    "name": "helpdesk-assistant",
                    "schema": {
                        "call_id": "text PRIMARY KEY",
                        "customer_phone": "text",
                        "customer_email": "text",
                        "interaction_type": "text",
                        "summary": "text",
                        "resolution_status": "text",
                        "created_at": "timestamp DEFAULT NOW()",
                        "metadata": "jsonb"
                    }
                }
            ]
        },

        # Usage and billing estimates
        "usage_estimates": {
            "monthly_calls": 1000,
            "avg_call_duration": "3 minutes",
            "estimated_costs": {
                "vapi": "$50-100/month",
                "openai": "$30-60/month",
                "other_services": "$20-40/month",
                "total": "$100-200/month"
            }
        },

        # Success metrics and KPIs
        "success_metrics": [
            "Call resolution rate",
            "Average handling time",
            "Customer satisfaction score",
            "Ticket creation rate",
            "Transfer rate to human agents",
            "First call resolution rate"
        ]
    }

    return template

if __name__ == "__main__":
    template = create_helpdesk_automation_template()
    print(json.dumps(template, indent=2))