#!/usr/bin/env python3
"""
Script to create Donewell Insurance Ghana helpdesk automation implementation.
This creates an actual automation config based on the helpdesk template.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from bson import ObjectId

# Add the backend to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from mongo import get_collection
from templates.helpdesk_automation_template import create_helpdesk_automation_template

def create_donewell_insurance_automation():
    """Create Donewell Insurance Ghana automation implementation."""
    try:
        # Get the automation configs collection
        automation_configs_collection = get_collection("automation_configs")

        if automation_configs_collection is None:
            print("❌ Failed to connect to MongoDB")
            return None

        # Get the base template
        template = create_helpdesk_automation_template()

        # Donewell Insurance company information
        donewell_info = {
            "company_name": "Donewell Insurance",
            "website": "https://www.donewellinsurance.com/",
            "description": "Leading insurance company in Ghana providing comprehensive insurance solutions and financial services",
            "services": [
                "Motor vehicle insurance",
                "Property and casualty insurance",
                "Life and health insurance",
                "Marine insurance",
                "Professional indemnity",
                "Travel insurance",
                "Corporate insurance solutions"
            ],
            "support_hours": "Monday to Friday: 8:00 AM - 5:00 PM",
            "contact_info": {
                "customer_service": "+233 302 685 685",
                "whatsapp": "+233 50 123 4567",
                "website": "https://www.donewellinsurance.com/",
                "email": "info@donewellinsurance.com"
            }
        }

        # Create system prompt for Donewell Insurance
        system_prompt = f"""You are an intelligent customer service agent for {donewell_info['company_name']}, Ghana's trusted insurance provider.

COMPANY CONTEXT:
- {donewell_info['description']}
- Services: {', '.join(donewell_info['services'])}
- Website: {donewell_info['website']}
- Customer Service: {donewell_info['contact_info']['customer_service']}
- WhatsApp: {donewell_info['contact_info']['whatsapp']}
- Email: {donewell_info['contact_info']['email']}

YOUR ROLE:
You are a professional, knowledgeable, and empathetic insurance customer service representative. You can:
1. Answer questions about insurance products, coverage, and premiums
2. Help with policy inquiries and claim processes
3. Provide guidance on insurance applications and renewals
4. Create support tickets for complex issues requiring specialist attention
5. Schedule appointments with insurance advisors
6. Search for current information about insurance regulations and policies
7. Transfer calls to human agents when necessary

CAPABILITIES:
- Create tickets in Freshdesk for complex insurance matters
- Send email notifications to customers about their policies
- Search the web for current insurance regulations and company updates
- Check calendar availability and schedule appointments with advisors
- Save all interactions to the database for quality assurance and compliance

TRANSFER PROTOCOL:
If a customer requests to speak with a human agent, has complex policy questions, or if you encounter a question you cannot answer confidently, politely explain that you'll transfer them to a specialist and use the transfer function.

TONE: Professional, trustworthy, and empathetic. Always greet customers warmly and thank them for choosing Donewell Insurance.

COMPLIANCE: Always remind customers that insurance decisions should be made carefully and encourage them to read policy documents thoroughly.

Remember: You represent Donewell Insurance's commitment to protecting what matters most to our customers. Always strive to provide accurate information while maintaining the highest standards of customer service."""

        # Create Donewell Insurance specific automation config
        donewell_automation = {
            "automationName": "Donewell Insurance Customer Support Helpdesk",
            "templateId": template["id"],
            "status": "DRAFT",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
            "userId": "system",  # System-created automation

            # Company Information
            "companyInfo": {
                "name": "Donewell Insurance",
                "description": donewell_info["description"],
                "url": "https://www.donewellinsurance.com/",
                "industry": "Insurance",
                "country": "Ghana",
                "services": donewell_info["services"],
                "supportHours": donewell_info["support_hours"],
                "contactInfo": donewell_info["contact_info"]
            },

            # VAPI Agent Configuration
            "vapiAgent": {
                "assistantId": "",  # To be set during deployment
                "phoneNumberId": "",  # To be set during deployment
                "systemPrompt": system_prompt,
                "voiceSettings": {
                    "voiceId": "jennifer",  # Different voice for insurance company
                    "model": "nova-2",
                    "maxDuration": 900,  # Longer duration for insurance inquiries
                    "stability": 0.6,
                    "similarityBoost": 0.8,
                    "optimizeStreamingLatency": 3
                },
                "tools": template["tools"],
                "firstMessage": f"Hello! Thank you for calling {donewell_info['company_name']}. I'm your AI assistant here to help you with any questions about our insurance products and services. How can I assist you today?",
                "endCallMessage": "Thank you for choosing Donewell Insurance. We're here to protect what matters most to you. Have a great day!",
                "transferPhoneNumber": "+233302685685",
                "maxDurationSeconds": 900,
                "silenceTimeoutSeconds": 40,  # Longer silence timeout for insurance
                "responseDelaySeconds": 0.5,
                "numWordsToInterruptAssistant": 3,
                "maxInterruptions": 2,
                "interruptionThreshold": 120,
                "backgroundSound": "office",
                "backgroundDenoisingEnabled": True
            },

            # N8N Workflow Configuration
            "n8nWorkflow": {
                "workflowId": "",  # To be set during deployment
                "workflowName": "Donewell Insurance Helpdesk Automation",
                "webhookUrl": "",  # To be set during deployment
                "workflowData": template["n8n_workflow"],
                "endpoints": {
                    "calendar": "/calendar/availability",
                    "tickets": "/tickets/create",
                    "availability": "/availability/check",
                    "escalation": "/escalation/route",
                    "analytics": "/analytics/track"
                }
            },

            # Integration Settings
            "integrations": {
                "freshdesk": {
                    "enabled": True,
                    "domain": "ailabs-888099064326049059.myfreshworks.com",
                    "apiKeyRequired": True,
                    "settings": {
                        **template["integrations"]["freshdesk"],
                        "source": 7,  # API source
                        "custom_fields": {
                            "policy_number": "",
                            "insurance_type": "",
                            "claim_number": ""
                        }
                    }
                },
                "resend": {
                    "enabled": True,
                    "apiKeyRequired": True,
                    "settings": {
                        **template["integrations"]["resend"],
                        "from_email": "Donewell Insurance Support <support@donewellinsurance.com>",
                        "default_to": "ailabsafrica@gmail.com"
                    }
                },
                "tavily": {
                    "enabled": True,
                    "apiKeyRequired": True,
                    "settings": {
                        **template["integrations"]["tavily"],
                        "include_domains": ["donewellinsurance.com", "naicom.gov.ng"]
                    }
                },
                "calendly": {
                    "enabled": True,
                    "apiKeyRequired": True,
                    "settings": template["integrations"]["calendly"]
                },
                "supabase": {
                    "enabled": True,
                    "settings": {
                        **template["integrations"]["supabase"],
                        "table": "helpdesk_demo"
                    }
                }
            },

            # Custom Tools Configuration
            "customTools": {
                "enabled": True,
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "create_insurance_ticket",
                            "description": "Create a support ticket for insurance-related issues that require specialist attention",
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
                                    "policy_number": {
                                        "type": "string",
                                        "description": "Customer's policy number if applicable"
                                    },
                                    "insurance_type": {
                                        "type": "string",
                                        "description": "Type of insurance (motor, life, property, etc.)"
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
                            "name": "search_insurance_information",
                            "description": "Search for current information about insurance products, regulations, or company policies",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "Search query for insurance information"
                                    }
                                },
                                "required": ["query"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "schedule_advisor_appointment",
                            "description": "Schedule appointment with insurance advisor for policy consultation",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "start_date": {
                                        "type": "string",
                                        "description": "Preferred start date for appointment (ISO format)"
                                    },
                                    "end_date": {
                                        "type": "string",
                                        "description": "Preferred end date for appointment (ISO format)"
                                    },
                                    "appointment_type": {
                                        "type": "string",
                                        "description": "Type of consultation needed (policy review, new insurance, claims, etc.)"
                                    },
                                    "customer_info": {
                                        "type": "string",
                                        "description": "Customer contact information"
                                    }
                                },
                                "required": ["start_date", "end_date", "appointment_type"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "transfer_to_specialist",
                            "description": "Transfer call to human insurance specialist when needed",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "reason": {
                                        "type": "string",
                                        "description": "Reason for transferring to specialist"
                                    },
                                    "specialist_type": {
                                        "type": "string",
                                        "description": "Type of specialist needed (claims, underwriting, sales, etc.)"
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
                ]
            },

            # Demo Settings
            "demoSettings": {
                "enableDemo": True,
                "demoUrl": "",  # To be set during deployment
                "demoTitle": "Donewell Insurance Customer Support Demo",
                "demoDescription": "Experience Donewell Insurance's AI-powered customer support system",
                "showMetrics": True,
                "allowPublicAccess": True
            },

            # Analytics Configuration
            "analytics": {
                "enabled": True,
                "trackCalls": True,
                "trackResolutions": True,
                "trackSatisfaction": True,
                "trackResponseTime": True,
                "retentionDays": 180,  # Longer retention for insurance compliance
                "complianceTracking": True
            },

            # Template metadata
            "templateName": template["template_name"],
            "templateVersion": template["version"],
            "category": template["category"],
            "industry": "Insurance",
            "tags": template["tags"] + ["donewell-insurance", "insurance", "ghana", "live-implementation"],
            "configParameters": {
                **template["config_parameters"],
                "company_name": {
                    "type": "string",
                    "label": "Company Name",
                    "description": "Insurance company name",
                    "default": "Donewell Insurance",
                    "required": True
                },
                "policy_search_enabled": {
                    "type": "boolean",
                    "label": "Enable Policy Search",
                    "description": "Allow searching for policy information",
                    "default": True,
                    "required": False
                }
            },
            "deploymentRequirements": {
                **template["deployment_requirements"],
                "compliance": [
                    "NAICOM regulations compliance",
                    "Data protection and privacy",
                    "Customer information security"
                ]
            },
            "usageEstimates": {
                "monthly_calls": 500,
                "avg_call_duration": "5 minutes",
                "estimated_costs": {
                    "vapi": "$30-60/month",
                    "openai": "$20-40/month",
                    "other_services": "$15-30/month",
                    "total": "$65-130/month"
                }
            },
            "successMetrics": [
                "Policy inquiry resolution rate",
                "Claims processing efficiency",
                "Customer satisfaction score",
                "Appointment booking rate",
                "Transfer rate to specialists",
                "First call resolution rate",
                "Compliance adherence rate"
            ]
        }

        # Check if Donewell Insurance automation already exists
        existing = automation_configs_collection.find_one({
            "automationName": donewell_automation["automationName"]
        })

        if existing:
            print(f"Donewell Insurance automation already exists. Updating...")
            result = automation_configs_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": {**donewell_automation, "updatedAt": datetime.utcnow()}}
            )
            print(f"Updated automation. Modified count: {result.modified_count}")
            automation_id = str(existing["_id"])
        else:
            print(f"Creating new Donewell Insurance automation...")
            result = automation_configs_collection.insert_one(donewell_automation)
            print(f"Inserted automation with ID: {result.inserted_id}")
            automation_id = str(result.inserted_id)

        # Verify the automation was added/updated
        saved_automation = automation_configs_collection.find_one({"_id": ObjectId(automation_id)})
        if saved_automation:
            print(f"✅ Donewell Insurance automation successfully saved:")
            print(f"   - ID: {automation_id}")
            print(f"   - Name: {saved_automation['automationName']}")
            print(f"   - Company: {saved_automation['companyInfo']['name']}")
            print(f"   - Status: {saved_automation['status']}")
            print(f"   - Template: {saved_automation['templateName']}")
            print(f"   - Industry: {saved_automation['industry']}")
            print(f"   - Integrations: {len(saved_automation['integrations'])}")
            print(f"   - Tools: {len(saved_automation['customTools']['tools'])}")
            print(f"   - Created: {saved_automation['createdAt']}")
        else:
            print("❌ Failed to save Donewell Insurance automation")

        return automation_id

    except Exception as e:
        print(f"Error creating Donewell Insurance automation: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    automation_id = create_donewell_insurance_automation()
    if automation_id:
        print(f"\n🎉 Donewell Insurance automation created successfully with ID: {automation_id}")
        print(f"Access it at: https://api.ailabsafrica.com/automation-configs/{automation_id}")
    else:
        print("❌ Failed to create Donewell Insurance automation")
        sys.exit(1)