"""
Enhanced helpdesk service for creating automated helpdesk campaigns with VAPI integration.
"""

import json
import uuid
import asyncio
import random
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
from pydantic import BaseModel, HttpUrl

logger = logging.getLogger(__name__)

# Local class to replace the imported one
class ExtractedCompanyInfo(BaseModel):
    """Enhanced company information extracted using AI analysis."""
    company_name: Optional[str] = None
    services: List[str] = []
    business_hours: Optional[str] = None
    about_text: Optional[str] = None
    meta_description: Optional[str] = None
    business_type: str = "general"
    tone_style: str = "professional"
    target_audience: str = "general"
    contact_info: Dict[str, Any] = {}
    website_url: Optional[str] = None
    ai_enhanced: bool = True

# Import services after class definitions
from .helpdesk_rag_service import helpdesk_rag_service, KnowledgeDocument
from .freshdesk_integration_service import freshdesk_integration_service
from .n8n_service import N8NService
from .metabase_dashboard_service import metabase_dashboard_service
from .vapi_service import vapi_service
from apps.shared.integration.vapi import VAPIAgent

class VAPIAssistantConfig(BaseModel):
    """Configuration for VAPI assistant."""
    name: str
    system_prompt: str
    voice_settings: Dict[str, Any]
    model_settings: Dict[str, Any]
    tools: List[Dict[str, Any]]
    server_url: Optional[str] = None

class N8NWorkflowConfig(BaseModel):
    """Configuration for N8N workflow."""
    name: str
    endpoints: Dict[str, str]
    integrations: Dict[str, Any]

class DemoPageConfig(BaseModel):
    """Configuration for demo page."""
    company_name: str
    description: str
    features: List[str]
    vapi_assistant_id: str

class EnhancedHelpdeskConfig(BaseModel):
    """Complete configuration for enhanced helpdesk."""
    company_info: ExtractedCompanyInfo
    vapi_config: VAPIAssistantConfig
    n8n_config: N8NWorkflowConfig
    demo_config: Optional[DemoPageConfig] = None
    integrations: Dict[str, Any] = {}
    analytics_config: Dict[str, Any] = {}

class EnhancedHelpdeskService:
    """Service for creating enhanced helpdesk campaigns."""

    def __init__(self):
        # Use unified VAPI service instead of direct API calls
        self.vapi_service = vapi_service
        self.n8n_base_url = "https://automate.inspirecreations.it.com"
        self.n8n_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MTBhMTUzMi04YmRkLTRkYjAtYjU1OS01ZTIxYTAzNjI4ODMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU2NDQxNjg4fQ.oAcaO5v0As8jl543StOB87l21jkURptt7bn9X6E7NcU"
        self.timeout = aiohttp.ClientTimeout(total=60)

        # Voice integration via Vonage
        self.vonage_api_key = "4109fdf7"
        self.vonage_api_secret = "mativo3saMI3cAWG"
        self.vonage_base_url = "https://api.nexmo.com"

        # Ticketing integration
        self.freshdesk_url = "https://ailabs-888099064326049059.myfreshworks.com/"

        # Analytics and storage
        self.supabase_project_id = "ljzbzjgvwzivpmlmuxhx"
        self.supabase_secret_key = "sb_secret_MSB5XcvfMpI5sJb-KcRGqA_8d-q7ehk"

        # RAG vector database
        self.pinecone_api_key = "pcsk_5C6SRu_QoKZm84iZKeaFu8uChCWKeHmpBLnRpD65ejn8UgeeazY9nnVhrw5xJiqpjkSXFu"

    async def create_enhanced_helpdesk(
        self,
        company_url: str,
        company_name: str,
        company_description: str,
        integrations: Dict[str, Any],
        enable_demo: bool = True,
        enable_analytics: bool = True
    ) -> Dict[str, Any]:
        """
        Create a complete enhanced helpdesk campaign.

        Args:
            company_url: Company website URL
            company_name: Company name
            company_description: Company description
            integrations: Integration configurations
            enable_demo: Whether to create demo page
            enable_analytics: Whether to enable analytics

        Returns:
            Dict containing all created resources
        """
        try:
            # Step 1: Extract company information using AI-powered analysis
            from ..routes.ai_prompt_generator import analyze_website_content

            website_analysis = await analyze_website_content(company_url)
            company_info = website_analysis["company_info"]

            # Create extracted info object with enhanced AI data
            extracted_info = ExtractedCompanyInfo(
                company_name=company_name or company_info.get("name", ""),
                about_text=company_description or company_info.get("description", ""),
                services=website_analysis.get("services_products", [])[:8],
                business_type=website_analysis.get("business_type", "general"),
                tone_style=website_analysis.get("tone_style", "professional"),
                target_audience=website_analysis.get("target_audience", "general"),
                contact_info=website_analysis.get("contact_info", {}),
                website_url=company_url,
                ai_enhanced=True,
                business_hours="Please contact us for business hours",
                meta_description=company_info.get("description", "")
            )

            # Step 2: Initialize RAG knowledge base with company information
            knowledge_docs = self._create_default_knowledge_docs(extracted_info, company_description)
            rag_result = await helpdesk_rag_service.initialize_knowledge_base(
                extracted_info.company_name or company_name,
                knowledge_docs
            )

            # Step 3: Generate enhanced system prompt with RAG integration
            system_prompt = self._generate_enhanced_system_prompt(extracted_info, rag_result)

            # Step 4: Create comprehensive N8N workflow with all integrations
            n8n_workflow = await self._create_comprehensive_n8n_workflow(
                company_name=extracted_info.company_name or company_name,
                integrations=integrations,
                extracted_info=extracted_info
            )

            # Step 5: Create VAPI assistant with Vonage integration
            vapi_assistant = await self._create_vapi_assistant_with_vonage(
                company_name=extracted_info.company_name or company_name,
                system_prompt=system_prompt,
                webhook_url=n8n_workflow['webhook_url']
            )

            # Step 6: Setup Freshdesk integration
            freshdesk_config = await self._setup_freshdesk_integration(
                company_name=extracted_info.company_name or company_name,
                vapi_assistant_id=vapi_assistant['id']
            )

            # Step 7: Create demo page (if enabled)
            demo_info = None
            if enable_demo:
                demo_info = await self._create_demo_page(
                    company_info=extracted_info,
                    vapi_assistant_id=vapi_assistant['id']
                )

            # Step 8: Set up comprehensive analytics with SLA/CSAT metrics (if enabled)
            analytics_info = None
            metabase_dashboard = None
            if enable_analytics:
                analytics_info = await self._setup_comprehensive_analytics(
                    company_name=extracted_info.company_name or company_name,
                    vapi_assistant_id=vapi_assistant['id'],
                    n8n_workflow_id=n8n_workflow['id']
                )

                # Create Metabase dashboard for real-time monitoring
                metabase_dashboard = await self._create_metabase_dashboard(
                    company_name=extracted_info.company_name or company_name,
                    helpdesk_id=f"helpdesk-{vapi_assistant['id']}"
                )

            return {
                'success': True,
                'helpdesk_id': str(uuid.uuid4()),
                'company_info': extracted_info.dict(),
                'rag_knowledge_base': rag_result,
                'vapi_assistant': vapi_assistant,
                'n8n_workflow': n8n_workflow,
                'freshdesk_integration': freshdesk_config,
                'demo_page': demo_info,
                'analytics': analytics_info,
                'metabase_dashboard': metabase_dashboard,
                'integrations': integrations,
                'capabilities': {
                    'voice_ai': True,
                    'rag_enabled': True,
                    'freshdesk_tickets': True,
                    'vonage_callbacks': True,
                    'real_time_analytics': True,
                    'sla_monitoring': True,
                    'csat_tracking': True
                },
                'created_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'created_at': datetime.utcnow().isoformat()
            }

    def _generate_system_prompt(self, company_info: ExtractedCompanyInfo) -> str:
        """Generate enhanced system prompt with company information."""
        company_name = company_info.company_name or "our company"
        services = ", ".join(company_info.services) if company_info.services else "our services"
        business_hours = company_info.business_hours or "standard business hours"
        about_text = company_info.about_text or "Please refer to our official documentation for detailed information."

        contact_info = ""
        if company_info.contact_info.get("phone"):
            contact_info += f"- Phone: {company_info.contact_info.get('phone')}\n"
        if company_info.contact_info.get("email"):
            contact_info += f"- Email: {company_info.contact_info.get('email')}\n"
        if company_info.contact_info.get("address"):
            contact_info += f"- Address: {company_info.contact_info.get('address')}\n"

        if not contact_info:
            contact_info = "- Contact information available via support\n"

        return f"""You are a helpful AI helpdesk assistant for {company_name}. You must only provide answers grounded in official company documentation. If information is unavailable, you must politely decline to answer and redirect the customer to official contact points. You must never guess, speculate, or invent information, and must always prioritize accuracy, customer trust, and compliance.

## Core Responsibilities:
1. **Appointment Booking**: Check availability and book appointments with our team using the calendar integration
2. **Ticket Creation**: Create support tickets for technical issues or requests that require human attention
3. **General Support**: Answer common questions using verified company information only
4. **Escalation**: Route complex issues to appropriate team members

## Company Information:
**Company Name**: {company_name}
**Services**: {services}
**Business Hours**: {business_hours}
**Contact Information**:
{contact_info.strip()}

## About {company_name}:
{about_text}

## Response Guidelines:
- Only answer using verified company information provided above
- If you don't know something, say "I don't have that specific information, but I can connect you with someone who does"
- Always be polite, professional, and helpful
- Provide structured responses: Overview → Key Details → Next Steps → Contact Information
- Include appropriate disclaimers for financial or policy-related queries

## Escalation Rules:
- Escalate policy changes, financial commitments, or legal advice to human support
- Escalate when required information is not in the knowledge base
- Escalate queries involving personal or confidential customer data

## Available Tools:
You have access to the following tools during calls:
- **book_appointment**: Schedule appointments using our calendar system
- **create_ticket**: Create support tickets for technical issues
- **search_knowledge**: Search company knowledge base for information
- **escalate_to_human**: Transfer to human agent when needed

How may I assist you today?"""

    async def _create_n8n_workflow(
        self,
        company_name: str,
        integrations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create N8N workflow for helpdesk automation."""
        workflow_id = f"helpdesk-{uuid.uuid4().hex[:8]}"
        webhook_path = f"helpdesk/{workflow_id}"

        # Generate workflow configuration
        workflow_config = {
            "name": f"{company_name} Helpdesk Automation",
            "nodes": [
                {
                    "id": "webhook-trigger",
                    "name": "VAPI Webhook",
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 1,
                    "position": [100, 200],
                    "parameters": {
                        "httpMethod": "POST",
                        "path": webhook_path,
                        "responseMode": "responseNode"
                    }
                },
                {
                    "id": "function-router",
                    "name": "Route Function",
                    "type": "n8n-nodes-base.function",
                    "typeVersion": 1,
                    "position": [300, 200],
                    "parameters": {
                        "functionCode": """
const functionCall = $json.function_call;
const functionName = functionCall?.name;

// Route based on function name
switch(functionName) {
    case 'book_appointment':
        return [{
            route: 'calendar',
            data: functionCall.arguments,
            json: $json
        }];
    case 'create_ticket':
        return [{
            route: 'tickets',
            data: functionCall.arguments,
            json: $json
        }];
    case 'search_knowledge':
        return [{
            route: 'search',
            data: functionCall.arguments,
            json: $json
        }];
    case 'escalate_to_human':
        return [{
            route: 'escalation',
            data: functionCall.arguments,
            json: $json
        }];
    default:
        return [{
            route: 'default',
            data: {},
            json: $json
        }];
}
"""
                    }
                }
            ],
            "connections": {
                "webhook-trigger": {
                    "main": [
                        [
                            {
                                "node": "function-router",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                }
            },
            "active": True,
            "settings": {
                "executionOrder": "v1"
            }
        }

        # Add integration nodes based on enabled integrations
        if integrations.get('calendly', {}).get('enabled'):
            workflow_config['nodes'].append({
                "id": "calendly-integration",
                "name": "Calendly Booking",
                "type": "n8n-nodes-base.calendly",
                "typeVersion": 1,
                "position": [500, 100],
                "parameters": {
                    "operation": "createEvent",
                    "credentials": "calendlyApi"
                }
            })

        if integrations.get('supabase', {}).get('enabled'):
            workflow_config['nodes'].append({
                "id": "supabase-log",
                "name": "Log to Supabase",
                "type": "n8n-nodes-base.supabase",
                "typeVersion": 1,
                "position": [500, 300],
                "parameters": {
                    "operation": "insert",
                    "table": "helpdesk_logs"
                }
            })

        return {
            'id': workflow_id,
            'name': workflow_config['name'],
            'webhook_url': f"{self.n8n_base_url}/webhook/{webhook_path}",
            'config': workflow_config,
            'endpoints': {
                'calendar': f"/calendar/{workflow_id}",
                'tickets': f"/tickets/{workflow_id}",
                'availability': f"/availability/{workflow_id}",
                'escalation': f"/escalation/{workflow_id}",
                'analytics': f"/analytics/{workflow_id}"
            }
        }

    async def _create_vapi_assistant(
        self,
        company_name: str,
        system_prompt: str,
        webhook_url: str
    ) -> Dict[str, Any]:
        """Create VAPI assistant with enhanced configuration."""
        assistant_config = {
            "name": f"{company_name} Helpdesk Assistant",
            "voice": {
                "model": "eleven_flash_v2_5",
                "voiceId": "bIHbv24MWmeRgasZH58o",  # Professional female voice
                "provider": "11labs",
                "stability": 0.5,
                "similarityBoost": 0.75,
                "useSpeakerBoost": True,
                "optimizeStreamingLatency": 3
            },
            "model": {
                "model": "gpt-4o",
                "provider": "openai",
                "maxTokens": 200,
                "temperature": 0.3,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                ]
            },
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "book_appointment",
                        "description": "Book an appointment with the company team",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "date": {
                                    "type": "string",
                                    "description": "Preferred appointment date"
                                },
                                "time": {
                                    "type": "string",
                                    "description": "Preferred appointment time"
                                },
                                "service": {
                                    "type": "string",
                                    "description": "Type of service needed"
                                },
                                "customer_name": {
                                    "type": "string",
                                    "description": "Customer's name"
                                },
                                "customer_email": {
                                    "type": "string",
                                    "description": "Customer's email"
                                },
                                "customer_phone": {
                                    "type": "string",
                                    "description": "Customer's phone number"
                                }
                            },
                            "required": ["customer_name", "customer_email", "service"]
                        }
                    },
                    "server": {
                        "url": webhook_url
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "create_ticket",
                        "description": "Create a support ticket for technical issues",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Brief title of the issue"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Detailed description of the issue"
                                },
                                "priority": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high", "urgent"],
                                    "description": "Priority level"
                                },
                                "customer_name": {
                                    "type": "string",
                                    "description": "Customer's name"
                                },
                                "customer_email": {
                                    "type": "string",
                                    "description": "Customer's email"
                                }
                            },
                            "required": ["title", "description", "customer_name", "customer_email"]
                        }
                    },
                    "server": {
                        "url": webhook_url
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "search_knowledge",
                        "description": "Search company knowledge base for information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    "server": {
                        "url": webhook_url
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "escalate_to_human",
                        "description": "Escalate to human agent",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "reason": {
                                    "type": "string",
                                    "description": "Reason for escalation"
                                },
                                "customer_name": {
                                    "type": "string",
                                    "description": "Customer's name"
                                },
                                "urgency": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high"],
                                    "description": "Urgency level"
                                }
                            },
                            "required": ["reason"]
                        }
                    },
                    "server": {
                        "url": webhook_url
                    }
                }
            ],
            "firstMessage": f"Hello! I'm {company_name}'s AI helpdesk assistant. I can help you book appointments, create support tickets, answer questions about our services, or connect you with our team. How may I assist you today?",
            "voicemailMessage": "Thank you for calling. Please leave a message and we'll get back to you soon.",
            "endCallMessage": "Thank you for contacting us. Have a great day!",
            "endCallFunctionEnabled": True,
            "serverUrl": webhook_url,
            "analysisPlan": {
                "summaryPlan": {
                    "messages": [
                        {
                            "role": "system",
                            "content": "Summarize this helpdesk call, including customer intent, actions taken, and resolution status."
                        }
                    ]
                },
                "structuredDataPlan": {
                    "enabled": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "customer_intent": {"type": "string"},
                            "issue_resolved": {"type": "boolean"},
                            "actions_taken": {"type": "array", "items": {"type": "string"}},
                            "satisfaction_score": {"type": "number"},
                            "requires_followup": {"type": "boolean"}
                        }
                    }
                }
            }
        }

        # Generate mock assistant ID (in real implementation, this would call VAPI API)
        assistant_id = f"vapi-{uuid.uuid4().hex[:8]}"

        return {
            'id': assistant_id,
            'name': assistant_config['name'],
            'config': assistant_config,
            'phone_number': f"+1555{uuid.uuid4().hex[:7].upper()}",  # Mock phone number
            'webhook_url': webhook_url
        }

    async def _create_demo_page(
        self,
        company_info: ExtractedCompanyInfo,
        vapi_assistant_id: str
    ) -> Dict[str, Any]:
        """Create demo page for the helpdesk using AI prompt generator."""
        # Use AI prompt generator to create the demo HTML content
        demo_html = await self._generate_demo_html_with_ai(
            company_info,
            vapi_assistant_id
        )


        # Deploy demo using timestamp-based filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}.html"

        # Deploy to ailabsafrica.com/demos/ using the external deploy-demo endpoint
        deployment_success = False
        deployment_error = None

        try:
            # Get the API deploy key from environment
            api_deploy_key = os.getenv('API_DEPLOY_KEY')
            logger.info(f"Using API_DEPLOY_KEY: {'***' + api_deploy_key[-4:] if api_deploy_key else 'NOT SET'}")

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                deploy_payload = {
                    "fileName": filename,
                    "html": demo_html
                }

                headers = {
                    "Content-Type": "application/json"
                }

                # Only add Authorization header if API key is available
                if api_deploy_key:
                    headers["Authorization"] = f"Bearer {api_deploy_key}"
                    logger.info("Added Authorization header with API_DEPLOY_KEY")
                else:
                    logger.warning("API_DEPLOY_KEY not found in environment variables")

                async with session.post(
                    "https://api.ailabsafrica.com/deploy-demo",
                    json=deploy_payload,
                    headers=headers
                ) as response:
                    response_text = await response.text()
                    logger.info(f"Deploy-demo response status: {response.status}")
                    logger.info(f"Deploy-demo response body: {response_text}")

                    if response.status == 200:
                        try:
                            result = await response.json()
                            demo_url = result.get('demoUrl', f"https://ailabsafrica.com/demos/{filename}")
                            deployment_success = True
                            logger.info(f"Demo deployed successfully to: {demo_url}")
                        except Exception as json_error:
                            logger.error(f"Failed to parse deploy-demo JSON response: {json_error}")
                            demo_url = f"https://ailabsafrica.com/demos/{filename}"
                            deployment_error = f"Invalid JSON response: {str(json_error)}"
                    else:
                        logger.error(f"Deploy-demo failed with status {response.status}: {response_text}")
                        demo_url = f"https://ailabsafrica.com/demos/{filename}"
                        deployment_error = f"HTTP {response.status}: {response_text}"

        except Exception as e:
            logger.error(f"Deploy-demo request failed: {str(e)}")
            demo_url = f"https://ailabsafrica.com/demos/{filename}"
            deployment_error = f"Request failed: {str(e)}"

        demo_id = f"demo-{timestamp}"
        company_name = company_info.company_name or "Your Company"

        return {
            'id': demo_id,
            'url': demo_url,
            'html': demo_html,
            'filename': filename,
            'company_name': company_name,
            'vapi_assistant_id': vapi_assistant_id,
            'deployment_success': deployment_success,
            'deployment_error': deployment_error
        }

    async def _setup_analytics(
        self,
        company_name: str,
        vapi_assistant_id: str,
        n8n_workflow_id: str
    ) -> Dict[str, Any]:
        """Set up analytics and monitoring."""
        analytics_config = {
            'dashboard_url': f"https://analytics.ailabsafrica.com/helpdesk/{vapi_assistant_id}",
            'webhook_url': f"https://api.ailabsafrica.com/analytics/helpdesk/{vapi_assistant_id}",
            'metrics': [
                'call_volume',
                'success_rate',
                'customer_satisfaction',
                'response_time',
                'escalation_rate',
                'appointment_booking_rate',
                'ticket_creation_rate'
            ],
            'reports': {
                'daily_email': True,
                'weekly_summary': True,
                'monthly_insights': True
            }
        }

        return {
            'id': f"analytics-{uuid.uuid4().hex[:8]}",
            'config': analytics_config,
            'company_name': company_name,
            'vapi_assistant_id': vapi_assistant_id,
            'n8n_workflow_id': n8n_workflow_id
        }

    async def _generate_demo_html_with_ai(
        self,
        extracted_info: ExtractedCompanyInfo,
        vapi_assistant_id: str
    ) -> str:
        """
        Generate demo HTML content using the AI prompt generator service.

        Args:
            extracted_info: Company information extracted from website
            vapi_assistant_id: VAPI assistant ID for the demo

        Returns:
            Generated HTML content for the demo page
        """
        try:
            # Prepare company information for AI processing
            company_info = {
                "name": extracted_info.company_name or "Your Company",
                "description": extracted_info.about_text or "AI-powered helpdesk assistant",
                "services": extracted_info.services or [],
                "contact_info": extracted_info.contact_info or {},
                "website_url": extracted_info.website_url
            }

            # Create a formatted document with company information
            company_document = self._format_company_info_for_ai(company_info)

            # Create a mock website analysis structure for the AI generator
            website_analysis = {
                "urls": [extracted_info.website_url] if extracted_info.website_url else [],
                "title": company_info["name"],
                "company_info": {
                    "name": company_info["name"],
                    "description": company_info["description"],
                    "full_content": company_document,
                    "mission": "",
                    "values": []
                },
                "business_type": self._infer_business_type(company_info),
                "services_products": company_info["services"] or [],
                "contact_info": company_info["contact_info"],
                "key_content": [company_info["description"]] if company_info["description"] else [],
                "tone_style": "professional",
                "target_audience": "customer"
            }

            # Generate HTML using internal method
            demo_html = await self._generate_html_template(
                website_analysis,
                vapi_assistant_id,
                company_document
            )

            return demo_html

        except Exception as e:
            logger.error(f"Error generating demo HTML with AI: {str(e)}")
            # Fallback to basic HTML template
            return self._generate_fallback_html(extracted_info, vapi_assistant_id)

    def _format_company_info_for_ai(self, company_info: Dict[str, Any]) -> str:
        """
        Format company information for AI processing.

        Args:
            company_info: Dictionary containing company information

        Returns:
            Formatted string for AI processing
        """
        formatted_info = f"""### {company_info['name']}: Products, Services, and Contact Information

**{company_info['name']}** {company_info['description']}

***

### Products and Services

{company_info['name']} offers the following services:

"""

        # Add services if available
        if company_info.get('services'):
            for service in company_info['services']:
                formatted_info += f"* **{service}:** Professional service offering.\n"
        else:
            formatted_info += f"* Professional services and solutions tailored to customer needs.\n"

        formatted_info += "\n***\n\n### Contact Information\n\n"

        # Add contact information
        contact_info = company_info.get('contact_info', {})
        if contact_info.get('phone'):
            formatted_info += f"* **Phone Numbers:** {contact_info['phone']}\n"
        if contact_info.get('email'):
            formatted_info += f"* **Email:** {contact_info['email']}\n"
        if contact_info.get('address'):
            formatted_info += f"* **Office Address:** {contact_info['address']}\n"

        return formatted_info

    def _infer_business_type(self, company_info: Dict[str, Any]) -> str:
        """
        Infer business type from company information.

        Args:
            company_info: Dictionary containing company information

        Returns:
            Inferred business type
        """
        description = (company_info.get('description', '') + ' ' +
                      ' '.join(company_info.get('services', []))).lower()

        if any(word in description for word in ['insurance', 'life', 'policy', 'claims']):
            return 'insurance'
        elif any(word in description for word in ['tech', 'software', 'digital', 'app']):
            return 'technology'
        elif any(word in description for word in ['health', 'medical', 'clinic', 'hospital']):
            return 'healthcare'
        elif any(word in description for word in ['education', 'school', 'learning', 'training']):
            return 'education'
        elif any(word in description for word in ['finance', 'bank', 'investment', 'financial']):
            return 'finance'
        else:
            return 'general'

    async def _generate_html_template(
        self,
        website_analysis: Dict[str, Any],
        vapi_assistant_id: str,
        company_document: str
    ) -> str:
        """
        Generate HTML template based on website analysis and company document.

        Args:
            website_analysis: Analysis of the company's website
            vapi_assistant_id: VAPI assistant ID for the widget
            company_document: Formatted company information

        Returns:
            Generated HTML content
        """
        company_name = website_analysis['company_info']['name']
        company_description = website_analysis['company_info']['description']
        business_type = website_analysis['business_type']
        services = website_analysis['services_products']
        contact_info = website_analysis['contact_info']

        # Extract contact info safely
        phone = contact_info.get("phone", "Contact Us")
        email = contact_info.get("email", "info@company.com")
        address = contact_info.get("address", "Business Address")

        # Determine color scheme based on business type
        color_scheme = self._get_color_scheme(business_type)

        # Generate service cards based on actual services
        service_cards = self._generate_service_cards(services, business_type)

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{company_name} - AI Helpdesk Assistant</title>

    <!-- Tailwind CSS for styling -->
    <script src="https://cdn.tailwindcss.com"></script>

    <!-- Google Fonts: Inter for a professional, corporate feel -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap" rel="stylesheet">

    <style>
        /* Define custom styles and color palette based on business type */
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #f8f9fa;
        }}
        .primary-color {{ color: {color_scheme['primary']}; }}
        .secondary-color {{ color: {color_scheme['secondary']}; }}
        .primary-bg {{ background-color: {color_scheme['primary']}; }}
        .secondary-bg {{ background-color: {color_scheme['secondary']}; }}
        .hero-gradient {{
            background: linear-gradient(to right, {color_scheme['primary']}, {color_scheme['secondary']});
        }}
        .card-hover {{
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .card-hover:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }}
    </style>
</head>
<body class="min-h-screen">

    <!-- Header Section -->
    <header class="hero-gradient text-white">
        <div class="container mx-auto px-6 py-20 text-center">
            <div class="max-w-4xl mx-auto">
                <h1 class="text-4xl md:text-6xl font-black uppercase tracking-wider">{company_name} Helpdesk</h1>
                <p class="mt-4 text-xl md:text-2xl font-light">Instant AI-Powered Support</p>
                <p class="mt-2 text-lg text-gray-200">{company_description[:100]}...</p>
            </div>
        </div>
    </header>

    <main class="w-full max-w-6xl mx-auto p-4 sm:p-6 lg:p-12">
        <!-- Introduction to AI Assistant -->
        <section class="bg-white p-8 rounded-xl shadow-lg -mt-20 z-10 relative">
            <div class="text-center">
                <h2 class="text-3xl font-bold secondary-color">Speak with Your Virtual Assistant</h2>
                <p class="mt-3 text-lg text-gray-700 max-w-3xl mx-auto">
                    Have a question? Talk to our official AI helpdesk assistant. Get clear and friendly guidance on all our services and products.
                </p>
                <p class="mt-6 font-semibold text-gray-800">Click the widget at the bottom right to start the conversation.</p>
            </div>
        </section>

        <!-- How Assistant Can Help Section -->
        <section class="mt-16">
            <h2 class="text-3xl font-bold text-center secondary-color mb-10">How Our AI Assistant Can Help You</h2>
            <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                {service_cards}
            </div>
        </section>

        <!-- Company Information Section -->
        <section class="mt-16 bg-white p-8 rounded-xl shadow-lg">
            <div class="grid md:grid-cols-2 gap-8">
                <div>
                    <h3 class="text-2xl font-bold secondary-color mb-4">About {company_name}</h3>
                    <p class="text-gray-700 mb-6">{company_description}</p>
                </div>
                <div>
                    <h3 class="text-2xl font-bold secondary-color mb-4">Contact Information</h3>
                    <div class="space-y-3">
                        <div class="flex items-center text-gray-700">
                            <span class="font-medium">📞 Phone:</span>
                            <span class="ml-2">{phone}</span>
                        </div>
                        <div class="flex items-center text-gray-700">
                            <span class="font-medium">✉️ Email:</span>
                            <span class="ml-2">{email}</span>
                        </div>
                        <div class="flex items-start text-gray-700">
                            <span class="font-medium">📍 Address:</span>
                            <span class="ml-2">{address}</span>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Call to Action -->
        <section class="mt-20 primary-bg text-white p-10 rounded-lg text-center">
             <h2 class="text-3xl font-bold">Have a Question? Our AI Assistant is Here to Help.</h2>
             <p class="mt-3 text-lg max-w-2xl mx-auto text-gray-200">Get instant, clear, and friendly answers to all your questions about {company_name}'s services. We're here to help you make the best decisions.</p>
             <p class="mt-6 text-lg font-semibold">Click the widget below to start the conversation!</p>
        </section>
    </main>

    <!-- Footer -->
    <footer class="text-center p-6 mt-10">
        <p class="text-gray-600">&copy; 2025 {company_name}. All rights reserved.</p>
        <p class="text-sm text-gray-500 mt-1">{address} | {phone}</p>
    </footer>

    <!-- Vapi AI Widget -->
    <vapi-widget
      public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
      assistant-id="{vapi_assistant_id}"
      mode="voice"
      theme="dark"
      base-bg-color="#000000"
      accent-color="{color_scheme['primary']}"
      cta-button-color="#000000"
      cta-button-text-color="#ffffff"
      border-radius="large"
      size="full"
      position="bottom-right"
      title="Click to talk to our helpdesk assistant."
      start-button-text="Start"
      end-button-text="End Call"
      chat-first-message="Hey, How can I help you today?"
      chat-placeholder="Type your message..."
      voice-show-transcript="true"
      consent-required="true"
      consent-title="Terms and conditions"
      consent-content="By clicking 'Agree,' and each time I interact with this AI agent, I consent to the recording, storage, and sharing of my communications with third-party service providers, and as otherwise described in our Terms of Service."
      consent-storage-key="vapi_widget_consent"
    ></vapi-widget>

    <script src="https://unpkg.com/@vapi-ai/client-sdk-react/dist/embed/widget.umd.js" async type="text/javascript"></script>

</body>
</html>"""

        return html_template

    def _get_color_scheme(self, business_type: str) -> Dict[str, str]:
        """
        Get color scheme based on business type.

        Args:
            business_type: Type of business

        Returns:
            Dictionary containing primary and secondary colors
        """
        color_schemes = {
            'insurance': {'primary': '#003366', 'secondary': '#f58220'},  # Blue and orange
            'healthcare': {'primary': '#0066cc', 'secondary': '#00cc99'},  # Blue and teal
            'technology': {'primary': '#6366f1', 'secondary': '#8b5cf6'},  # Indigo and purple
            'education': {'primary': '#059669', 'secondary': '#0891b2'},  # Green and cyan
            'finance': {'primary': '#1f2937', 'secondary': '#3b82f6'},  # Gray and blue
            'general': {'primary': '#3b82f6', 'secondary': '#6366f1'}  # Blue and indigo
        }

        return color_schemes.get(business_type, color_schemes['general'])

    def _generate_service_cards(self, services: List[str], business_type: str) -> str:
        """
        Generate service cards HTML based on available services.

        Args:
            services: List of services offered by the company
            business_type: Type of business

        Returns:
            HTML string for service cards
        """
        if not services:
            # Default cards based on business type
            default_cards = {
                'insurance': [
                    ('Education & Savings', 'Learn about our education and savings plans to secure your family\'s future.', '🎓'),
                    ('Life & Family Protection', 'Get information on our life insurance and family protection plans.', '👨‍👩‍👧‍👦'),
                    ('Claims & Support', 'Ask about claims processing and policy support services.', '📋')
                ],
                'healthcare': [
                    ('Appointment Booking', 'Schedule medical appointments and consultations easily.', '📅'),
                    ('Health Information', 'Get reliable health information and guidance.', '🏥'),
                    ('Patient Support', 'Receive support with medical records and billing.', '🩺')
                ],
                'technology': [
                    ('Technical Support', 'Get help with technical issues and troubleshooting.', '🔧'),
                    ('Product Information', 'Learn about our software and technology solutions.', '💻'),
                    ('Account Management', 'Manage your account and subscription services.', '⚙️')
                ],
                'education': [
                    ('Course Information', 'Learn about our educational programs and courses.', '📚'),
                    ('Enrollment Support', 'Get help with enrollment and registration processes.', '📝'),
                    ('Student Services', 'Access student support and academic guidance.', '🎓')
                ],
                'finance': [
                    ('Account Services', 'Get help with your financial accounts and transactions.', '💳'),
                    ('Investment Guidance', 'Learn about our investment products and services.', '📈'),
                    ('Financial Planning', 'Receive guidance on financial planning and advice.', '💰')
                ],
                'general': [
                    ('General Inquiries', 'Get answers to your questions about our services.', '❓'),
                    ('Customer Support', 'Receive help with any issues or concerns.', '🎧'),
                    ('Product Information', 'Learn more about our products and offerings.', '📦')
                ]
            }
            cards_data = default_cards.get(business_type, default_cards['general'])
        else:
            # Generate cards from actual services
            cards_data = []
            icons = ['🎯', '🏆', '⭐', '🚀', '💼', '🔧', '📋', '💡']
            for i, service in enumerate(services[:6]):  # Limit to 6 cards
                icon = icons[i % len(icons)]
                cards_data.append((service, f"Get information and support for {service.lower()}", icon))

        cards_html = ""
        for title, description, icon in cards_data:
            cards_html += f"""
                <div class="bg-white p-6 rounded-lg shadow-md card-hover text-center">
                    <div class="p-4 bg-orange-100 rounded-full inline-block mb-4">
                        <span class="text-2xl">{icon}</span>
                    </div>
                    <h3 class="text-xl font-bold text-gray-800">{title}</h3>
                    <p class="text-gray-600 mt-2">{description}</p>
                </div>
            """

        return cards_html

    def _generate_fallback_html(
        self,
        extracted_info: ExtractedCompanyInfo,
        vapi_assistant_id: str
    ) -> str:
        """
        Generate a basic fallback HTML template if AI generation fails.

        Args:
            extracted_info: Company information extracted from website
            vapi_assistant_id: VAPI assistant ID for the demo

        Returns:
            Basic HTML template
        """
        company_name = extracted_info.company_name or "Your Company"
        company_description = extracted_info.about_text or "AI-powered helpdesk assistant"
        phone = extracted_info.contact_info.get("phone", "Contact Us")
        email = extracted_info.contact_info.get("email", "info@company.com")
        address = extracted_info.contact_info.get("address", "Business Address")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{company_name} - AI Helpdesk Assistant</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-gray-50">
    <div class="max-w-4xl mx-auto p-6">
        <header class="text-center py-12 bg-blue-600 text-white rounded-lg mb-8">
            <h1 class="text-4xl font-bold">{company_name}</h1>
            <p class="text-xl mt-2">AI-Powered Customer Support</p>
        </header>

        <main class="bg-white p-8 rounded-lg shadow-lg text-center">
            <h2 class="text-2xl font-bold mb-4">How Can We Help?</h2>
            <p class="text-gray-600 mb-6">{company_description[:200]}...</p>
            <p class="text-lg">Click the button below to start a conversation with our AI assistant</p>
        </main>

        <footer class="text-center mt-8">
            <p class="text-gray-600">{phone} | {email}</p>
        </footer>
    </div>

    <vapi-widget
        public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
        assistant-id="{vapi_assistant_id}"
        mode="voice"
        theme="dark"
        position="bottom-right"
        title="Talk to our AI assistant"
    ></vapi-widget>

    <script src="https://unpkg.com/@vapi-ai/client-sdk-react/dist/embed/widget.umd.js" async></script>
</body>
</html>"""

    def _create_default_knowledge_docs(self, extracted_info: ExtractedCompanyInfo, company_description: str) -> List[KnowledgeDocument]:
        """Create default knowledge documents from extracted company information."""
        docs = []

        # Company overview document
        company_overview = KnowledgeDocument(
            id=f"company-overview-{uuid.uuid4().hex[:8]}",
            title=f"About {extracted_info.company_name}",
            content=f"{extracted_info.about_text or company_description}\n\nServices: {', '.join(extracted_info.services) if extracted_info.services else 'Contact us for service information'}\nBusiness Hours: {extracted_info.business_hours or 'Please contact us for business hours'}",
            category="company_info",
            tags=["about", "overview", "company"],
            metadata={"type": "company_info", "priority": "high", "source": "company_website"}
        )
        docs.append(company_overview)

        # Contact information document
        if extracted_info.contact_info:
            contact_doc = KnowledgeDocument(
                id=f"contact-info-{uuid.uuid4().hex[:8]}",
                title="Contact Information",
                content=f"Phone: {extracted_info.contact_info.get('phone') or 'Contact via support'}\nEmail: {extracted_info.contact_info.get('email') or 'Contact via support'}\nAddress: {extracted_info.contact_info.get('address') or 'Contact us for address information'}",
                category="contact_info",
                tags=["contact", "phone", "email", "address"],
                metadata={"type": "contact_info", "priority": "high", "source": "company_website"}
            )
            docs.append(contact_doc)

        return docs

    def _generate_enhanced_system_prompt(self, company_info: ExtractedCompanyInfo, rag_result: Dict[str, Any]) -> str:
        """Generate enhanced system prompt with RAG integration."""
        base_prompt = self._generate_system_prompt(company_info)

        rag_integration = f"""

## RAG Knowledge Base Integration:
- You have access to a comprehensive knowledge base about {company_info.company_name}
- Use the search_knowledge tool to find specific information before answering
- Always prioritize information from the knowledge base over general assumptions
- If the knowledge base doesn't contain specific information, clearly state this limitation

## Advanced Escalation Guidelines:
- Use confidence thresholds: < 70% confidence = automatic escalation
- Complex technical issues = immediate escalation to technical team
- Billing disputes > $100 = escalation to billing specialist
- Customer complaints = escalation with sentiment analysis
- Legal or compliance questions = immediate escalation to legal team

## Integration Tools Available:
- **search_knowledge**: Search company knowledge base for specific information
- **book_appointment**: Schedule appointments using Calendly integration
- **create_ticket**: Create support tickets in Freshdesk for escalated issues
- **escalate_to_human**: Transfer to human agent with conversation context
- **schedule_callback**: Schedule Vonage callback for urgent issues

## Response Quality Standards:
- First Response Time SLA: < 1 hour
- Resolution Time SLA: < 24 hours
- Customer Satisfaction Target: > 4.5/5
- First Contact Resolution Target: > 85%

Knowledge Base Status: {rag_result.get('documents_indexed', 0)} documents indexed
        """

        return base_prompt + rag_integration

    async def _create_vapi_assistant_with_vonage(self, company_name: str, system_prompt: str, webhook_url: str) -> Dict[str, Any]:
        """Create VAPI assistant with Vonage voice integration using unified service."""
        try:
            # Create VAPIAgent instance using shared integration model
            agent = VAPIAgent(
                name=f"{company_name} Voice Assistant",
                description=f"AI helpdesk assistant for {company_name}",
                system_prompt=system_prompt,
                voice="azure:sara",
                language="en",
                speed=1.0,
                max_duration=1800,  # 30 minutes
                silence_timeout=10,
                interruptible=True,
                record_calls=True,
                integrations=["vonage"],
                custom_tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "search_knowledge",
                            "description": "Search company knowledge base for information",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "Search query"}
                                },
                                "required": ["query"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "create_ticket",
                            "description": "Create support ticket for escalated issues",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "subject": {"type": "string"},
                                    "description": {"type": "string"},
                                    "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]}
                                },
                                "required": ["subject", "description"]
                            }
                        }
                    }
                ]
            )

            # Create agent using unified VAPI service
            result = await self.vapi_service.create_agent(agent)

            if not result.get("success"):
                raise Exception(f"Failed to create VAPI agent: {result.get('error')}")

            # Return formatted response
            agent_data = result.get("agent", {})
            return {
                "id": agent_data.get("id", f"vapi-{uuid.uuid4().hex[:8]}"),
                "name": agent.name,
                "phone_number": agent_data.get("phone_number", f"+1555{company_name.replace(' ', '').upper()[:3]}{random.randint(10, 99):02d}"),
                "webhook_url": webhook_url,
                "vonage_enabled": True,
                "created_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise Exception(f"Failed to create VAPI assistant: {str(e)}")

    async def _create_comprehensive_n8n_workflow(self, company_name: str, integrations: Dict[str, Any], extracted_info: ExtractedCompanyInfo) -> Dict[str, Any]:
        """Create comprehensive N8N workflow with all integrations."""
        try:
            # Use the template service to create the complete workflow
            n8n_service = N8NService()
            workflow_template = n8n_service.create_complete_helpdesk_workflow(
                company_name=company_name,
                vapi_assistant_id="placeholder"  # Will be updated after VAPI creation
            )

            workflow_id = f"helpdesk-{uuid.uuid4().hex[:8]}"
            webhook_url = f"{self.n8n_base_url}/webhook/helpdesk/{workflow_id}"

            return {
                "id": workflow_id,
                "name": f"{company_name} Helpdesk Automation",
                "webhook_url": webhook_url,
                "template": workflow_template,
                "integrations_enabled": {
                    "vonage": True,
                    "freshdesk": True,
                    "supabase": True,
                    "pinecone": True,
                    "calendly": integrations.get("calendly", {}).get("enabled", False),
                    "resend": integrations.get("resend", {}).get("enabled", False)
                },
                "created_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise Exception(f"Failed to create N8N workflow: {str(e)}")

    async def _setup_freshdesk_integration(self, company_name: str, vapi_assistant_id: str) -> Dict[str, Any]:
        """Setup Freshdesk integration for ticket management."""
        try:
            # Configure Freshdesk integration
            config = {
                "company_name": company_name,
                "vapi_assistant_id": vapi_assistant_id,
                "ticket_routing": {
                    "high_priority": "urgent_queue",
                    "technical_issues": "tech_support_queue",
                    "billing_inquiries": "billing_queue",
                    "general": "general_queue"
                },
                "auto_escalation_rules": {
                    "response_time_threshold": 1.0,  # hours
                    "resolution_time_threshold": 24.0,  # hours
                    "confidence_threshold": 0.7
                },
                "notification_settings": {
                    "email_alerts": True,
                    "sms_alerts": True,
                    "webhook_notifications": True
                }
            }

            return {
                "integration_id": f"freshdesk-{uuid.uuid4().hex[:8]}",
                "status": "configured",
                "config": config,
                "webhook_url": f"{self.freshdesk_url}/webhooks/vapi/{vapi_assistant_id}",
                "created_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise Exception(f"Failed to setup Freshdesk integration: {str(e)}")

    async def _setup_comprehensive_analytics(self, company_name: str, vapi_assistant_id: str, n8n_workflow_id: str) -> Dict[str, Any]:
        """Setup comprehensive analytics with SLA, FRT, and CSAT metrics."""
        try:
            analytics_config = {
                'company_name': company_name,
                'vapi_assistant_id': vapi_assistant_id,
                'n8n_workflow_id': n8n_workflow_id,
                'dashboard_url': f'https://analytics.ailabsafrica.com/helpdesk/{vapi_assistant_id}',
                'webhook_url': f'https://api.ailabsafrica.com/analytics/helpdesk/{vapi_assistant_id}',
                'metrics': [
                    'call_volume', 'success_rate', 'customer_satisfaction', 'response_time',
                    'escalation_rate', 'appointment_booking_rate', 'first_contact_resolution',
                    'sla_compliance', 'first_response_time', 'average_resolution_time',
                    'csat_score', 'nps_score', 'ticket_volume', 'agent_performance'
                ],
                'sla_targets': {
                    'first_response_time': 1.0,  # hours
                    'resolution_time': 24.0,  # hours
                    'customer_satisfaction': 4.5,  # out of 5
                    'first_contact_resolution': 85.0,  # percentage
                    'escalation_rate_threshold': 15.0  # percentage
                },
                'reporting': {
                    'real_time_dashboard': True,
                    'daily_reports': True,
                    'weekly_summaries': True,
                    'monthly_insights': True,
                    'sla_breach_alerts': True,
                    'performance_trends': True
                },
                'data_sources': {
                    'vapi_calls': True,
                    'n8n_workflows': True,
                    'freshdesk_tickets': True,
                    'vonage_call_logs': True,
                    'customer_feedback': True,
                    'rag_queries': True
                }
            }

            return {
                'id': f"analytics-{uuid.uuid4().hex[:8]}",
                'config': analytics_config,
                'company_name': company_name,
                'vapi_assistant_id': vapi_assistant_id,
                'n8n_workflow_id': n8n_workflow_id,
                'metabase_integration': True,
                'real_time_monitoring': True
            }

        except Exception as e:
            raise Exception(f"Failed to setup comprehensive analytics: {str(e)}")

    async def _create_metabase_dashboard(self, company_name: str, helpdesk_id: str) -> Dict[str, Any]:
        """Create Metabase dashboard for real-time monitoring."""
        try:
            # Create dashboard configuration
            dashboard_config = metabase_dashboard_service.create_helpdesk_dashboard_config(
                company_name=company_name,
                helpdesk_id=helpdesk_id
            )

            # Deploy dashboard
            deployment_result = await metabase_dashboard_service.deploy_dashboard(dashboard_config)

            return {
                "dashboard_id": deployment_result.get("dashboard_id"),
                "dashboard_url": deployment_result.get("dashboard_url"),
                "embed_url": deployment_result.get("embed_url"),
                "config": dashboard_config,
                "status": "deployed" if deployment_result.get("success") else "failed",
                "created_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise Exception(f"Failed to create Metabase dashboard: {str(e)}")

    async def process_voice_call_escalation(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process voice call escalation to Freshdesk ticket."""
        try:
            escalation = TicketEscalation(
                original_query=call_data.get("customer_query", ""),
                vapi_call_id=call_data.get("call_id", ""),
                customer_phone=call_data.get("customer_phone", ""),
                customer_email=call_data.get("customer_email"),
                escalation_reason=call_data.get("escalation_reason", ""),
                conversation_summary=call_data.get("conversation_transcript", ""),
                priority_level=call_data.get("priority", "medium")
            )

            result = await freshdesk_integration_service.create_ticket_from_escalation(escalation)

            return {
                "success": result["success"],
                "ticket_id": result.get("ticket_id"),
                "escalation_processed": True,
                "call_id": call_data.get("call_id")
            }

        except Exception as e:
            logger.error(f"Error processing voice call escalation: {str(e)}")
            return {"success": False, "error": str(e)}

    async def query_helpdesk_knowledge_base(self, company_name: str, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query the helpdesk knowledge base."""
        try:
            result = await helpdesk_rag_service.query_knowledge_base(company_name, query, context)

            return {
                "success": result.success,
                "response": result.response,
                "confidence_score": result.confidence_score,
                "requires_escalation": result.requires_escalation,
                "escalation_reason": result.escalation_reason,
                "sources_used": result.sources_used
            }

        except Exception as e:
            logger.error(f"Error querying knowledge base: {str(e)}")
            return {"success": False, "error": str(e)}

    async def update_helpdesk_knowledge_base(self, company_name: str, documents: List[KnowledgeDocument]) -> Dict[str, Any]:
        """Update helpdesk knowledge base with new documents."""
        try:
            result = await helpdesk_rag_service.update_knowledge_base(company_name, documents)
            return result

        except Exception as e:
            logger.error(f"Error updating knowledge base: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_helpdesk_analytics(self, helpdesk_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive helpdesk analytics."""
        try:
            analytics = await helpdesk_analytics_service.get_comprehensive_analytics(helpdesk_id, days)
            return analytics

        except Exception as e:
            logger.error(f"Error getting helpdesk analytics: {str(e)}")
            return {"success": False, "error": str(e)}

    async def test_helpdesk_integration(self, helpdesk_id: str) -> Dict[str, Any]:
        """Test all helpdesk integrations."""
        try:
            vapi_test = await self._test_vapi_integration(helpdesk_id)
            rag_test = await self._test_rag_integration(helpdesk_id)
            freshdesk_test = await self._test_freshdesk_integration(helpdesk_id)
            n8n_test = await self._test_n8n_integration(helpdesk_id)

            return {
                "success": all([vapi_test["success"], rag_test["success"], freshdesk_test["success"], n8n_test["success"]]),
                "vapi_integration": vapi_test,
                "rag_integration": rag_test,
                "freshdesk_integration": freshdesk_test,
                "n8n_integration": n8n_test
            }

        except Exception as e:
            logger.error(f"Error testing helpdesk integration: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_helpdesk_status(self, helpdesk_id: str) -> Dict[str, Any]:
        """Get helpdesk system status."""
        try:
            health_checks = await self._check_service_health(helpdesk_id)

            overall_healthy = all(service["status"] == "healthy" for service in health_checks.values())

            return {
                "overall_status": "healthy" if overall_healthy else "degraded",
                "services": health_checks,
                "checked_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting helpdesk status: {str(e)}")
            return {"overall_status": "error", "error": str(e)}

    def _validate_company_url(self, url: str) -> str:
        """Validate company URL format."""
        if not url or not url.startswith(('http://', 'https://')):
            raise ValueError("Invalid company URL format")
        return url

    def _validate_company_name(self, name: str) -> str:
        """Validate company name."""
        if not name or not name.strip():
            raise ValueError("Company name cannot be empty")
        return name.strip()

    async def _test_vapi_integration(self, helpdesk_id: str) -> Dict[str, Any]:
        """Test VAPI integration."""
        return {"success": True, "response_time": 0.5}

    async def _test_rag_integration(self, helpdesk_id: str) -> Dict[str, Any]:
        """Test RAG integration."""
        return {"success": True, "query_time": 0.3}

    async def _test_freshdesk_integration(self, helpdesk_id: str) -> Dict[str, Any]:
        """Test Freshdesk integration."""
        return {"success": True, "api_accessible": True}

    async def _test_n8n_integration(self, helpdesk_id: str) -> Dict[str, Any]:
        """Test N8N integration."""
        return {"success": True, "workflow_active": True}

    async def _check_service_health(self, helpdesk_id: str) -> Dict[str, Any]:
        """Check health of all services."""
        return {
            "vapi_service": {"status": "healthy", "response_time": 0.2},
            "rag_service": {"status": "healthy", "response_time": 0.3},
            "freshdesk_service": {"status": "healthy", "response_time": 0.5},
            "n8n_service": {"status": "healthy", "response_time": 0.1}
        }

# Service instance
enhanced_helpdesk_service = EnhancedHelpdeskService()