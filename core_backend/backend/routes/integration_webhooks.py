"""
Integration webhook handlers for Vapi voice assistant.
Handles HubSpot, Email, Tavily, Supabase, and Calendly integrations.
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from decimal import Decimal
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

# Import wallet services
from ..services.usage_charge_service import UsageChargeService
from ..services.wallet_service import WalletService
from ..models.wallet import Currency
from ..mongo import get_database

# Import integration services
try:
    import requests
    from supabase import create_client, Client
    import hubspot
    from hubspot.crm.contacts import SimplePublicObjectInput
except ImportError as e:
    logging.warning(f"Some integration libraries not available: {e}")

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/integrations", tags=["vapi-integrations"])

# Configuration from environment
HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")
RESEND_API_KEY = os.getenv("RESEND_API")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
DEMO_SUPABASE_URL = os.getenv("DEMO_SUPABASE_URL")
DEMO_SUPABASE_KEY = os.getenv("DEMO_SUPABASE_SUPABASE_KEY")
CALENDLY_API_KEY = os.getenv("CALENDLY_API_KEY")
VONAGE_API_KEY = os.getenv("VONAGE_API_KEY")
VONAGE_API_SECRET = os.getenv("VONAGE_API_SECRET")

class VapiWebhookRequest(BaseModel):
    """Base model for Vapi webhook requests."""
    call: Optional[Dict[str, Any]] = None
    message: Optional[Dict[str, Any]] = None
    transcript: Optional[str] = None
    phoneNumber: Optional[str] = None
    customer: Optional[Dict[str, Any]] = None

@router.post("/vapi-webhook")
async def main_vapi_webhook(
    request: VapiWebhookRequest,
    background_tasks: BackgroundTasks
):
    """
    Main Vapi webhook handler that routes function calls to appropriate integrations.

    Webhook endpoint - organization context tracked in call metadata when available.
    """
    try:
        # Extract organization context from call metadata for tracking
        call_data = request.call or {}
        metadata = call_data.get("metadata", {})
        org_id = metadata.get("organization_id") if metadata else None

        logger.warning(f"🔍 WEBHOOK DEBUG: Received Vapi webhook call - Message type: {request.message.get('type') if request.message else 'N/A'}, Organization: {org_id or 'Not specified'}")
        if request.message:
            logger.warning(f"🔍 WEBHOOK DEBUG: Message content: {str(request.message)[:200]}...")

        # Log full request for debugging
        import json as json_module
        logger.warning(f"🔍 FULL REQUEST DEBUG: {json_module.dumps({k: v for k, v in request.dict().items() if v is not None}, indent=2)[:500]}...")

        # Check for VAPI event types (end-of-call-report, transcript, etc.)
        message_type = request.message.get("type") if request.message else None

        # Handle end-of-call-report event - triggers transcript summary and call logging
        if message_type == "end-of-call-report":
            logger.info("📞 VAPI Event: End of call report received - triggering post-call pipeline")
            result = await handle_end_of_call_report(request, background_tasks)
            return result

        # Handle transcript event - can be used for real-time processing
        if message_type == "transcript":
            logger.info("📝 VAPI Event: Transcript update received")
            result = await handle_transcript_event(request, background_tasks)
            return result

        # Extract function call information - support both formats
        function_call = request.message.get("function_call") if request.message else None
        tool_calls = request.message.get("toolCalls") if request.message else None

        if not function_call and not tool_calls:
            logger.warning("🔍 WEBHOOK DEBUG: No function call found - returning default response")
            return {
                "message": {
                    "type": "assistant",
                    "content": "I'm here to help you with HubSpot, email, research, data storage, and scheduling. How can I assist you today?"
                }
            }

        # Handle new VAPI toolCalls format
        if tool_calls and len(tool_calls) > 0:
            tool_call = tool_calls[0]  # Process first tool call
            function_call = {
                "name": tool_call.get("function", {}).get("name"),
                "arguments": tool_call.get("function", {}).get("arguments", {})
            }
            logger.warning(f"🔍 WEBHOOK DEBUG: Converted toolCalls format - {function_call}")

        function_name = function_call.get("name")
        function_args = function_call.get("arguments", {})

        # Parse arguments if they come as a JSON string
        if isinstance(function_args, str):
            try:
                import json
                function_args = json.loads(function_args)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse function arguments: {function_args}")
                return {
                    "message": {
                        "type": "assistant",
                        "content": "I received invalid function arguments. Please try again."
                    }
                }

        # 📊 COMPREHENSIVE LOGGING START
        logger.info("🔔" * 50)
        logger.info("📞 VAPI TOOL CALL INITIATED")
        logger.info("🔔" * 50)
        logger.info(f"📋 Function: {function_name}")
        logger.info(f"📝 Arguments: {function_args}")
        logger.info(f"📱 Call ID: {request.call.get('id') if request.call else 'N/A'}")
        logger.info(f"🏢 Organization: {org_id or 'Not specified'}")
        logger.info(f"☎️  Phone: {request.phoneNumber}")
        logger.info(f"🎤 Transcript: {request.transcript[:200] if request.transcript else 'N/A'}...")
        logger.info(f"⏰ Timestamp: {datetime.utcnow().isoformat()}")

        # Route to appropriate handler with error tracking
        start_time = time.time()
        try:
            if function_name == "save_customer_to_hubspot":
                result = await handle_hubspot_save(function_args, background_tasks)
            elif function_name == "send_notification_email":
                result = await handle_email_send(function_args, background_tasks)
            elif function_name == "search_web_information":
                result = await handle_web_search(function_args)
            elif function_name == "save_call_data":
                result = await handle_database_save(function_args, background_tasks)
            elif function_name == "schedule_appointment":
                result = await handle_calendar_booking(function_args, background_tasks)
            elif function_name == "check_calendar_availability":
                result = await handle_calendar_availability_check(function_args, background_tasks)
            elif function_name == "schedule_google_calendar_appointment":
                result = await handle_google_calendar_booking(function_args, background_tasks)
            elif function_name == "check_google_calendar_availability":
                result = await handle_google_calendar_availability_check(function_args, background_tasks)
            elif function_name == "send_sms":
                result = await handle_sms_send(function_args, background_tasks)
            elif function_name == "create_support_ticket":
                result = await handle_support_ticket_creation(function_args, background_tasks)
            else:
                logger.warning(f"Unknown function called: {function_name}")
                result = {
                    "message": {
                        "type": "assistant",
                        "content": f"I don't recognize the function '{function_name}'. I can help with HubSpot, email, research, data storage, calendar scheduling (Calendly & Google Calendar), availability checking, and SMS."
                    }
                }

            # 📊 COMPREHENSIVE RESPONSE LOGGING
            execution_time = round((time.time() - start_time) * 1000, 2)  # ms
            logger.info("✅" * 50)
            logger.info("📤 VAPI TOOL RESPONSE")
            logger.info("✅" * 50)
            logger.info(f"📋 Function: {function_name}")
            logger.info(f"⏱️  Execution Time: {execution_time}ms")
            logger.info(f"✅ Status: SUCCESS")
            logger.info(f"📤 Response Content: {result.get('message', {}).get('content', 'N/A')[:200]}...")
            logger.info(f"📊 Function Result: {result.get('message', {}).get('function_call_result', {})}")
            logger.info(f"⏰ Completed: {datetime.utcnow().isoformat()}")
            logger.info("✅" * 50)

            return result

        except Exception as function_error:
            # 📊 COMPREHENSIVE ERROR LOGGING
            execution_time = round((time.time() - start_time) * 1000, 2)  # ms
            logger.error("❌" * 50)
            logger.error("📤 VAPI TOOL ERROR")
            logger.error("❌" * 50)
            logger.error(f"📋 Function: {function_name}")
            logger.error(f"⏱️  Execution Time: {execution_time}ms")
            logger.error(f"❌ Status: ERROR")
            logger.error(f"🔴 Error: {str(function_error)}")
            logger.error(f"📝 Arguments: {function_args}")
            logger.error(f"⏰ Failed At: {datetime.utcnow().isoformat()}")
            logger.error("❌" * 50)

            # Return user-friendly error message
            return {
                "message": {
                    "type": "assistant",
                    "content": f"I encountered an issue with {function_name.replace('_', ' ')}. Let me try a different approach or you can contact support if this persists. Error: {str(function_error)[:100]}...",
                    "function_call_result": {
                        "success": False,
                        "error": str(function_error),
                        "function_name": function_name,
                        "debug_args": function_args
                    }
                }
            }

    except Exception as e:
        logger.error(f"Error in main webhook: {str(e)}")
        return {
            "message": {
                "type": "assistant",
                "content": "I'm experiencing technical difficulties. Please try again or contact support."
            }
        }

@router.post("/hubspot/webhook")
async def hubspot_webhook(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Handle HubSpot contact creation.

    Webhook endpoint - organization context tracked through main VAPI webhook.
    """
    logger.info(f"HubSpot webhook called with data: {str(request)[:200]}")
    return await handle_hubspot_save(request, background_tasks)

async def handle_hubspot_save(args: Dict[str, Any], background_tasks: BackgroundTasks):
    """Save customer contact to HubSpot CRM."""
    try:
        if not HUBSPOT_ACCESS_TOKEN:
            return {
                "message": {
                    "type": "assistant",
                    "content": "HubSpot integration is not configured. Please contact support to set up HubSpot access."
                }
            }

        # Prepare contact data
        contact_data = {
            "properties": {
                "firstname": args.get("firstName", ""),
                "lastname": args.get("lastName", ""),
                "email": args.get("email", ""),
                "phone": args.get("phone", ""),
                "company": args.get("company", ""),
                "hs_lead_status": "NEW",
                "lifecyclestage": "lead"
            }
        }

        # Add notes if provided
        if args.get("notes"):
            contact_data["properties"]["notes_last_contacted"] = args["notes"]

        # Create HubSpot client and save contact
        client = hubspot.Client.create(access_token=HUBSPOT_ACCESS_TOKEN)
        contact_input = SimplePublicObjectInput(properties=contact_data["properties"])

        # Try to create contact (or update if exists)
        try:
            api_response = client.crm.contacts.basic_api.create(
                simple_public_object_input=contact_input
            )
            contact_id = api_response.id

        except Exception as create_error:
            # If contact exists, try to update instead
            logger.info(f"Contact might exist, attempting update: {create_error}")

            # Search for existing contact by email
            search_request = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": args.get("email", "")
                            }
                        ]
                    }
                ]
            }

            search_response = client.crm.contacts.search_api.do_search(
                public_object_search_request=search_request
            )

            if search_response.results:
                # Update existing contact
                contact_id = search_response.results[0].id
                client.crm.contacts.basic_api.update(
                    contact_id=contact_id,
                    simple_public_object_input=contact_input
                )
            else:
                raise create_error

        customer_name = f"{args.get('firstName', '')} {args.get('lastName', '')}".strip()

        return {
            "message": {
                "type": "assistant",
                "content": f"Perfect! I've saved {customer_name}'s contact information to HubSpot CRM. The contact has been added with ID {contact_id} and marked as a new lead.",
                "function_call_result": {
                    "success": True,
                    "contact_id": contact_id,
                    "action": "hubspot_contact_saved"
                }
            }
        }

    except Exception as e:
        logger.error(f"HubSpot save error: {str(e)}")
        return {
            "message": {
                "type": "assistant",
                "content": f"I encountered an issue saving to HubSpot: {str(e)}. The contact information has been noted but please follow up manually."
            }
        }

@router.post("/resend/webhook")
async def resend_webhook(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Handle email sending via Resend.

    Webhook endpoint - organization context tracked through main VAPI webhook.
    """
    logger.info(f"Resend webhook called with data: {str(request)[:200]}")
    return await handle_email_send(request, background_tasks)

async def handle_email_send(args: Dict[str, Any], background_tasks: BackgroundTasks):
    """Send email notification using centralized email service."""
    try:
        # Import centralized email service from shared
        from ....shared.services.unified_email_service import get_email_service

        # Get the centralized email service
        email_service = get_email_service()

        # Prepare email data
        to_email = args.get("to_email", "ailabsafrica@gmail.com")
        subject = args.get("subject", "Voice Assistant Notification")
        message = args.get("message", "")
        customer_name = args.get("customer_name", "Customer")
        call_summary = args.get("call_summary", "No summary provided")

        # Create detailed email content
        email_content = f"""
        <html>
        <body>
        <h2>{subject}</h2>
        <p><strong>Customer:</strong> {customer_name}</p>
        <p><strong>Message:</strong></p>
        <p>{message}</p>
        <hr>
        <p><strong>Call Summary:</strong></p>
        <p>{call_summary}</p>
        <p><strong>Timestamp:</strong> {datetime.now().isoformat()}</p>
        </body>
        </html>
        """

        # Send email using centralized service (automatically uses SMTP with iRedMail)
        result = await email_service.send_email(
            to=to_email,
            subject=subject,
            body=message,
            html_body=email_content
        )

        if result.get("success"):
            email_id = result.get("message_id", "unknown")
            logger.warning(f"🔍 EMAIL SUCCESS DEBUG: Email sent to {to_email}, ID: {email_id}, Full result: {result}")
            return {
                "message": {
                    "type": "assistant",
                    "content": f"Email sent successfully to {to_email}! The notification has been delivered via local SMTP server with ID {email_id}.",
                    "function_call_result": {
                        "success": True,
                        "email_id": email_id,
                        "recipient": to_email,
                        "provider": "smtp",
                        "smtp_host": result.get("smtp_host", "localhost"),
                        "debug_email_result": result
                    }
                }
            }
        else:
            error_msg = result.get("error", "Unknown error")
            raise Exception(f"SMTP email error: {error_msg}")

    except Exception as e:
        logger.error(f"Email send error: {str(e)}")
        return {
            "message": {
                "type": "assistant",
                "content": f"I had trouble sending the email: {str(e)}. Please try again or contact support."
            }
        }

@router.post("/tavily/webhook")
async def tavily_webhook(request: Dict[str, Any]):
    """
    Handle web search via Tavily.

    Webhook endpoint - organization context tracked through main VAPI webhook.
    """
    logger.info(f"Tavily webhook called with query: {request.get('query', 'N/A')}")
    return await handle_web_search(request)

async def handle_web_search(args: Dict[str, Any]):
    """Search the web using Tavily API."""
    try:
        if not TAVILY_API_KEY:
            return {
                "message": {
                    "type": "assistant",
                    "content": "Web search service is not configured. Please contact support to enable search capabilities."
                }
            }

        query = args.get("query", "")
        max_results = args.get("max_results", 5)
        include_domains = args.get("include_domains", "")

        if not query:
            return {
                "message": {
                    "type": "assistant",
                    "content": "Please provide a search query. What would you like me to search for?"
                }
            }

        # Prepare Tavily search request
        search_data = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results
        }

        if include_domains:
            search_data["include_domains"] = [include_domains]

        # Perform search
        response = requests.post(
            "https://api.tavily.com/search",
            json=search_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            search_results = response.json()
            results = search_results.get("results", [])

            if results:
                # Format results for voice response
                summary = f"I found {len(results)} results for '{query}':\\n\\n"
                for i, result in enumerate(results[:3], 1):  # Limit to top 3 for voice
                    title = result.get("title", "No title")
                    content = result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", "")
                    summary += f"{i}. {title}\\n{content}\\n\\n"

                return {
                    "message": {
                        "type": "assistant",
                        "content": summary,
                        "function_call_result": {
                            "success": True,
                            "results_count": len(results),
                            "query": query,
                            "top_results": results[:3]
                        }
                    }
                }
            else:
                return {
                    "message": {
                        "type": "assistant",
                        "content": f"I couldn't find any results for '{query}'. Please try a different search term."
                    }
                }
        else:
            raise Exception(f"Search API error: {response.status_code}")

    except Exception as e:
        logger.error(f"Web search error: {str(e)}")
        return {
            "message": {
                "type": "assistant",
                "content": f"I encountered an issue with the web search: {str(e)}. Please try again."
            }
        }

@router.post("/calendly/webhook")
async def calendly_webhook(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Handle calendar appointment scheduling.

    Webhook endpoint - organization context tracked through main VAPI webhook.
    """
    logger.info(f"Calendly webhook called with data: {str(request)[:200]}")
    return await handle_calendar_booking(request, background_tasks)

async def handle_calendar_booking(args: Dict[str, Any], background_tasks: BackgroundTasks):
    """Schedule appointment using Calendly API."""
    try:
        if not CALENDLY_API_KEY:
            return {
                "message": {
                    "type": "assistant",
                    "content": "Calendar service is not configured. Please contact support to enable appointment scheduling."
                }
            }

        customer_name = args.get("customer_name", "")
        customer_email = args.get("customer_email", "")
        appointment_date = args.get("appointment_date", "")
        appointment_time = args.get("appointment_time", "")
        duration_minutes = args.get("duration_minutes", 30)
        meeting_type = args.get("meeting_type", "consultation")
        notes = args.get("notes", "")

        if not all([customer_name, customer_email, appointment_date, appointment_time]):
            return {
                "message": {
                    "type": "assistant",
                    "content": "I need the customer's name, email, preferred date, and time to schedule an appointment. Could you provide those details?"
                }
            }

        # Format datetime for calendar
        try:
            appointment_datetime = datetime.strptime(
                f"{appointment_date} {appointment_time}",
                "%Y-%m-%d %H:%M"
            )
            end_datetime = appointment_datetime + timedelta(minutes=duration_minutes)
        except ValueError:
            return {
                "message": {
                    "type": "assistant",
                    "content": "Please provide the date in YYYY-MM-DD format and time in HH:MM format (24-hour)."
                }
            }

        # Create calendar event data
        event_data = {
            "name": f"{meeting_type.title()} with {customer_name}",
            "start_time": appointment_datetime.isoformat(),
            "end_time": end_datetime.isoformat(),
            "description": f"Meeting type: {meeting_type}\\nNotes: {notes}",
            "invitees": [
                {
                    "email": customer_email,
                    "name": customer_name
                }
            ]
        }

        # Get Calendly integration directly to avoid circular import
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), "../../../shared"))

        from integration.calendly import CalendlyIntegration, CalendlyConfig

        # Initialize Calendly service directly with API key from environment
        calendly_config = CalendlyConfig(
            api_key=os.getenv("CALENDLY_API_KEY"),
            base_url="https://api.calendly.com"
        )
        calendly_service = CalendlyIntegration(calendly_config)

        # Get user's event types to find a suitable one
        user_response = await calendly_service.get_current_user()
        if not user_response.success:
            return {
                "message": {
                    "type": "assistant",
                    "content": f"I'm having trouble accessing the calendar service. Let me provide you with a scheduling link instead. Please contact support if this continues."
                }
            }

        # Get event types for the user
        user_uri = user_response.data.get('resource', {}).get('uri', '')
        event_types_response = await calendly_service.list_event_types(user_uri=user_uri)

        if not event_types_response.success or not event_types_response.data.get('collection'):
            return {
                "message": {
                    "type": "assistant",
                    "content": f"I couldn't find available calendar event types. Please visit https://calendly.com to set up your calendar first."
                }
            }

        # Use the first available event type (in production, you'd select based on meeting_type)
        event_types = event_types_response.data.get('collection', [])
        suitable_event_type = None

        # Look for an event type matching the meeting type or use the first one
        for event_type in event_types:
            if meeting_type.lower() in event_type.get('name', '').lower():
                suitable_event_type = event_type
                break

        if not suitable_event_type:
            suitable_event_type = event_types[0]  # Use first available

        event_type_uri = suitable_event_type.get('uri', '')

        # Generate scheduling link with prefilled data
        prefill_data = {
            "name": customer_name,
            "email": customer_email
        }

        link_response = await calendly_service.generate_scheduling_link(
            event_type_uri=event_type_uri,
            start_time=appointment_datetime.isoformat(),
            prefill_data=prefill_data
        )

        if link_response.success:
            scheduling_url = link_response.data.get('scheduling_url', '')
            appointment_id = f"link_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            return {
                "message": {
                    "type": "assistant",
                    "content": f"I've prepared a personalized scheduling link for your {duration_minutes}-minute {meeting_type} on {appointment_date} at {appointment_time}. Please complete your booking by visiting: {scheduling_url}",
                    "function_call_result": {
                        "success": True,
                        "appointment_id": appointment_id,
                        "scheduling_url": scheduling_url,
                        "date": appointment_date,
                        "time": appointment_time,
                        "duration": duration_minutes,
                        "attendee": customer_email,
                        "event_type": suitable_event_type.get('name', meeting_type)
                    }
                }
            }
        else:
            return {
                "message": {
                    "type": "assistant",
                    "content": f"I encountered an issue creating your scheduling link: {link_response.error}. Please try visiting https://calendly.com directly to book your appointment."
                }
            }

    except Exception as e:
        logger.error(f"Calendar booking error: {str(e)}")
        return {
            "message": {
                "type": "assistant",
                "content": f"I encountered an issue scheduling the appointment: {str(e)}. Please try again or contact support to book manually."
            }
        }

async def handle_calendar_availability_check(args: Dict[str, Any], background_tasks: BackgroundTasks):
    """Check calendar availability using Calendly API."""
    try:
        # Import Calendly integration classes
        sys.path.append('/opt/kasaai/apps/shared')
        from integration.calendly import CalendlyIntegration, CalendlyConfig

        if not CALENDLY_API_KEY:
            return {
                "message": {
                    "type": "assistant",
                    "content": "Calendar service is not configured. Please contact support to enable calendar availability checking."
                }
            }

        date = args.get("date", "")
        duration_minutes = args.get("duration_minutes", 30)
        meeting_type = args.get("meeting_type", "consultation")

        if not date:
            return {
                "message": {
                    "type": "assistant",
                    "content": "Please provide a date (YYYY-MM-DD format) to check availability."
                }
            }

        # Initialize Calendly service
        calendly_config = CalendlyConfig(
            api_key=CALENDLY_API_KEY,
            base_url="https://api.calendly.com"
        )
        calendly_service = CalendlyIntegration(calendly_config)

        # Get current user to get event types
        user_response = await calendly_service.get_current_user()
        if not user_response.success:
            return {
                "message": {
                    "type": "assistant",
                    "content": "I'm having trouble accessing the calendar service. Please try again later."
                }
            }

        # Get event types for the user
        user_uri = user_response.data.get('resource', {}).get('uri', '')
        event_types_response = await calendly_service.list_event_types(user_uri=user_uri)

        if not event_types_response.success or not event_types_response.data.get('collection'):
            return {
                "message": {
                    "type": "assistant",
                    "content": "I couldn't find available calendar event types. Please visit https://calendly.com to set up your calendar first."
                }
            }

        # Use the first available event type that matches duration
        event_types = event_types_response.data.get('collection', [])
        suitable_event_type = None

        for event_type in event_types:
            event_duration = event_type.get('duration', 30)
            if event_duration == duration_minutes:
                suitable_event_type = event_type
                break

        if not suitable_event_type:
            suitable_event_type = event_types[0]  # Use first available

        event_type_uri = suitable_event_type.get('uri', '')

        # Check availability for the requested date
        start_time = f"{date}T00:00:00Z"
        end_time = f"{date}T23:59:59Z"

        availability_response = await calendly_service.get_event_type_available_times(
            event_type_uri=event_type_uri,
            start_time=start_time,
            end_time=end_time
        )

        if availability_response.success and availability_response.data:
            available_times = availability_response.data.get('collection', [])
            if available_times:
                # Format availability information
                formatted_times = []
                for time_slot in available_times[:3]:  # Limit to 3 options
                    start_time = time_slot.get('start_time', '')
                    if start_time:
                        # Convert to more readable format
                        from datetime import datetime
                        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%H:%M')
                        formatted_times.append(formatted_time)

                available_times_text = ", ".join(formatted_times) if formatted_times else "various times"

                return {
                    "message": {
                        "type": "assistant",
                        "content": f"Today is {datetime.now().strftime('%Y-%m-%d')}. For {date}, I found availability for {duration_minutes}-minute {meeting_type} appointments at: {available_times_text}. Would you like me to schedule one of these times?",
                        "function_call_result": {
                            "success": True,
                            "date": date,
                            "available_times": formatted_times,
                            "event_type": suitable_event_type.get('name', 'Meeting'),
                            "duration": duration_minutes
                        }
                    }
                }
            else:
                return {
                    "message": {
                        "type": "assistant",
                        "content": f"Today is {datetime.now().strftime('%Y-%m-%d')}. Unfortunately, I don't see any available times for {date}. Please try a different date or visit https://calendly.com/ailabsafrica to see all available options."
                    }
                }
        else:
            return {
                "message": {
                    "type": "assistant",
                    "content": f"Today is {datetime.now().strftime('%Y-%m-%d')}. I'm having trouble checking availability for {date}. Please try again or visit https://calendly.com/ailabsafrica to see available times."
                }
            }

    except Exception as e:
        logger.error(f"Calendar availability check error: {str(e)}")
        return {
            "message": {
                "type": "assistant",
                "content": f"I encountered an issue checking calendar availability: {str(e)}. Please try again or contact support."
            }
        }

@router.post("/vonage/webhook")
async def vonage_webhook(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Handle SMS sending via Vonage.

    Webhook endpoint - organization context tracked through main VAPI webhook.
    """
    logger.info(f"Vonage webhook called with data: {str(request)[:200]}")
    return await handle_sms_send(request, background_tasks)

@router.post("/vonage/sms")
async def vonage_sms_endpoint(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Direct SMS endpoint for healthcare tools and other services.

    Webhook endpoint - organization context tracked through main VAPI webhook.
    """
    logger.info(f"Vonage SMS endpoint called with data: {str(request)[:200]}")
    return await handle_sms_send(request, background_tasks)

async def handle_sms_send(args: Dict[str, Any], background_tasks: BackgroundTasks):
    """Send SMS using Vonage API."""
    try:
        if not VONAGE_API_KEY or not VONAGE_API_SECRET:
            return {
                "message": {
                    "type": "assistant",
                    "content": "SMS service is not configured. Please contact support to enable SMS capabilities."
                }
            }

        to_number = args.get("to_number", "")
        message_text = args.get("message", "")
        from_number = args.get("from_number", "+12075218001")  # Default Vonage number

        if not to_number or not message_text:
            return {
                "message": {
                    "type": "assistant",
                    "content": "I need a phone number and message to send an SMS. Could you provide those details?"
                }
            }

        # Prepare SMS data for Vonage API
        sms_data = {
            "from": from_number,
            "to": to_number,
            "text": message_text,
            "type": "text"
        }

        # Send SMS using Vonage API
        auth = (VONAGE_API_KEY, VONAGE_API_SECRET)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(
            "https://rest.nexmo.com/sms/json",
            data=sms_data,
            auth=auth,
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            messages = result.get("messages", [])

            if messages and messages[0].get("status") == "0":
                message_id = messages[0].get("message-id", "unknown")

                # Track SMS cost
                try:
                    from ..services.vonage_cost_monitoring_service import get_vonage_cost_service
                    vonage_service = await get_vonage_cost_service()
                    cost_record = await vonage_service.track_sms_cost(
                        destination=to_number,
                        message_count=1
                    )
                    logger.info(f"Tracked SMS cost: ${cost_record.cost_amount}")
                except Exception as cost_error:
                    logger.error(f"Error tracking SMS cost: {str(cost_error)}")

                return {
                    "message": {
                        "type": "assistant",
                        "content": f"SMS sent successfully to {to_number}! The message has been delivered with ID {message_id}.",
                        "function_call_result": {
                            "success": True,
                            "message_id": message_id,
                            "to_number": to_number,
                            "from_number": from_number
                        }
                    }
                }
            else:
                error_text = messages[0].get("error-text", "Unknown error") if messages else "Unknown error"
                raise Exception(f"SMS delivery failed: {error_text}")
        else:
            raise Exception(f"Vonage API error: {response.status_code} - {response.text}")

    except Exception as e:
        logger.error(f"SMS send error: {str(e)}")
        return {
            "message": {
                "type": "assistant",
                "content": f"I had trouble sending the SMS: {str(e)}. Please try again or contact support."
            }
        }

@router.get("/health")
async def integrations_health():
    """Health check for all integration services."""
    health_status = {
        "status": "healthy",
        "integrations": {
            "hubspot": {
                "configured": bool(HUBSPOT_ACCESS_TOKEN),
                "status": "ready" if HUBSPOT_ACCESS_TOKEN else "not_configured"
            },
            "resend_email": {
                "configured": bool(RESEND_API_KEY),
                "status": "ready" if RESEND_API_KEY else "not_configured"
            },
            "tavily_search": {
                "configured": bool(TAVILY_API_KEY),
                "status": "ready" if TAVILY_API_KEY else "not_configured"
            },
            "mongodb": {
                "configured": True,  # MongoDB is configured via environment
                "status": "ready"
            },
            "calendly": {
                "configured": bool(CALENDLY_API_KEY),
                "status": "ready" if CALENDLY_API_KEY else "not_configured"
            },
            "vonage_sms": {
                "configured": bool(VONAGE_API_KEY and VONAGE_API_SECRET),
                "status": "ready" if (VONAGE_API_KEY and VONAGE_API_SECRET) else "not_configured"
            },
            "google_calendar": {
                "configured": bool(os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH") or os.getenv("GOOGLE_CALENDAR_CREDENTIALS_JSON")),
                "status": "ready" if (os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH") or os.getenv("GOOGLE_CALENDAR_CREDENTIALS_JSON")) else "not_configured",
                "features": ["actual_event_creation", "availability_checking", "google_meet_integration"]
            }
        }
    }

    return health_status

async def handle_support_ticket_creation(args: Dict[str, Any], background_tasks: BackgroundTasks):
    """Create a support ticket in HubSpot."""
    try:
        logger.info(f"Creating support ticket with args: {args} (type: {type(args)})")

        # Import HubSpot service with lazy initialization
        from ..services.hubspot_consolidated_service import get_hubspot_service
        hubspot_service = get_hubspot_service()

        # Ensure args is a dictionary
        if not isinstance(args, dict):
            logger.error(f"Args is not a dictionary: {type(args)}, value: {args}")
            return {
                "message": {
                    "type": "assistant",
                    "content": f"Invalid arguments format. Expected dictionary, got {type(args)}."
                }
            }

        # Extract ticket data from arguments
        subject = args.get("subject", "Support Request")
        content = args.get("content", "")
        priority = args.get("priority", "MEDIUM")
        category = args.get("category", "CUSTOMER_SERVICE")
        customer_name = args.get("customer_name", "")
        customer_phone = args.get("customer_phone", "")

        # Prepare ticket data with only basic required properties
        ticket_data = {
            "subject": subject,
            "content": content
        }

        # Add customer information to subject or content if provided
        if customer_name and customer_phone:
            ticket_data["subject"] = f"{subject} - {customer_name}"
            ticket_data["content"] = f"Customer: {customer_name}\nPhone: {customer_phone}\n\n{content}"
        elif customer_name:
            ticket_data["subject"] = f"{subject} - {customer_name}"
        elif customer_phone:
            ticket_data["content"] = f"Customer Phone: {customer_phone}\n\n{content}"

        # Create ticket using HubSpot service
        result = await hubspot_service.create_ticket(ticket_data)

        if result.get("success"):
            ticket_id = result.get("ticket_id", "Unknown")
            logger.warning(f"🔍 TICKET SUCCESS DEBUG: Ticket created with ID {ticket_id}, Full result: {result}")
            return {
                "message": {
                    "type": "assistant",
                    "content": f"Support ticket created successfully! Your ticket ID is {ticket_id}. Our team will review your request and get back to you soon.",
                    "function_call_result": {
                        "success": True,
                        "ticket_id": ticket_id,
                        "subject": subject,
                        "priority": priority,
                        "provider": "hubspot",
                        "debug_ticket_result": result
                    }
                }
            }
        else:
            error_message = result.get("message", "Unknown error occurred")
            logger.error(f"🔴 TICKET ERROR DEBUG: HubSpot ticket creation failed - {error_message}, Full result: {result}")
            return {
                "message": {
                    "type": "assistant",
                    "content": f"I encountered an issue creating your support ticket: {error_message}. Please try again or contact support directly.",
                    "function_call_result": {
                        "success": False,
                        "error": error_message,
                        "provider": "hubspot",
                        "debug_ticket_result": result,
                        "debug_args": args
                    }
                }
            }

    except Exception as e:
        logger.error(f"Support ticket creation error: {str(e)}")
        return {
            "message": {
                "type": "assistant",
                "content": f"I encountered an unexpected error while creating your support ticket: {str(e)}. Please contact support directly for assistance.",
                "function_call_result": {
                    "success": False,
                    "error": str(e),
                    "provider": "hubspot"
                }
            }
        }

async def charge_wallet_for_call(
    call_data: Dict[str, Any],
    call_id: str,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Charge user wallet for voice call usage.

    Calculates cost based on call duration and charges the user's wallet.
    """
    try:
        logger.info(f"💰 WALLET CHARGE: Processing charge for call {call_id}")

        # Extract call details
        # VAPI provides cost information in the call data
        vapi_cost = call_data.get("cost")  # VAPI's total cost
        ended_at = call_data.get("endedAt")
        started_at = call_data.get("startedAt") or call_data.get("createdAt")

        # Get user/customer ID from call metadata
        customer_data = call_data.get("customer", {})
        user_id = customer_data.get("userId") or customer_data.get("user_id")
        automation_id = call_data.get("assistantId") or call_data.get("assistant_id")

        if not user_id:
            logger.warning(f"💰 WALLET CHARGE: No user_id found in call data, skipping charge")
            return {
                "success": False,
                "error": "no_user_id",
                "message": "User ID not found in call data"
            }

        # Calculate duration if timestamps available
        duration_seconds = 0
        if ended_at and started_at:
            try:
                from dateutil import parser
                end_time = parser.parse(ended_at) if isinstance(ended_at, str) else ended_at
                start_time = parser.parse(started_at) if isinstance(started_at, str) else started_at
                duration_seconds = int((end_time - start_time).total_seconds())
            except Exception as e:
                logger.warning(f"Could not calculate duration: {e}")

        # Use VAPI cost if available, otherwise estimate
        if vapi_cost:
            # VAPI cost is already calculated
            cost = Decimal(str(vapi_cost))
        else:
            # Fallback: estimate cost at $0.10/minute
            cost_per_minute = Decimal("0.10")
            duration_minutes = Decimal(duration_seconds) / Decimal("60")
            cost = (duration_minutes * cost_per_minute).quantize(Decimal("0.01"))

        logger.info(f"💰 WALLET CHARGE: Calculated cost ${cost} for {duration_seconds}s call")

        # Initialize services
        db = get_database()
        wallet_service = WalletService(db)
        usage_charge_service = UsageChargeService(db, wallet_service)

        # Charge wallet
        charge_result = await usage_charge_service.charge_for_voice_call(
            user_id=user_id,
            call_id=call_id,
            duration_seconds=duration_seconds,
            cost_per_minute=Decimal("0.10"),  # Standard rate
            automation_id=automation_id,
            currency=Currency.USD
        )

        if charge_result["success"]:
            logger.info(f"💰 WALLET CHARGE SUCCESS: Charged ${charge_result['amount_charged']} from user {user_id}, New balance: ${charge_result['new_balance']}")

            # Check for low balance warning
            if charge_result.get("is_low_balance"):
                logger.warning(f"💰 LOW BALANCE WARNING: User {user_id} balance is low: ${charge_result['available_balance']}")
        else:
            logger.error(f"💰 WALLET CHARGE FAILED: {charge_result.get('message', 'Unknown error')}")

        return charge_result

    except Exception as e:
        logger.error(f"💰 WALLET CHARGE ERROR: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to charge wallet: {str(e)}"
        }


async def fetch_vapi_call_data(call_id: str) -> dict:
    """
    Fetch complete call data from VAPI API.

    The end-of-call-report webhook doesn't include startedAt, endedAt, or complete cost data.
    We need to fetch this from the VAPI API to get accurate duration and billing info.

    Args:
        call_id: The VAPI call ID

    Returns:
        dict: Complete call data from VAPI, or empty dict if fetch fails
    """
    import httpx
    import os

    vapi_api_key = os.getenv("VAPI_API_KEY")
    if not vapi_api_key:
        logger.error("❌ VAPI_API_KEY not found in environment")
        return {}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.vapi.ai/call/{call_id}",
                headers={"Authorization": f"Bearer {vapi_api_key}"}
            )

            if response.status_code == 200:
                logger.info(f"✅ Fetched complete call data from VAPI API for call {call_id}")
                return response.json()
            else:
                logger.error(f"❌ VAPI API returned {response.status_code} for call {call_id}: {response.text}")
                return {}

    except Exception as e:
        logger.error(f"❌ Failed to fetch call data from VAPI API: {e}")
        return {}


async def update_campaign_progress_from_webhook(
    campaign_id: str,
    call_id: str,
    call_data: dict,
    ended_reason: str
) -> dict:
    """
    Update campaign progress counters when a call completes via webhook.

    Args:
        campaign_id: Campaign ID from call metadata
        call_id: VAPI call ID
        call_data: Complete call data from VAPI
        ended_reason: Reason call ended

    Returns:
        dict: Update result
    """
    try:
        from ..services.campaign_execution_service import campaign_service

        # Extract call metrics
        duration = call_data.get("duration", 0) or 0

        # If duration is 0, calculate from timestamps
        if duration == 0:
            started_at = call_data.get("startedAt")
            ended_at = call_data.get("endedAt")

            if started_at and ended_at:
                try:
                    from dateutil import parser
                    start_time = parser.parse(started_at) if isinstance(started_at, str) else started_at
                    end_time = parser.parse(ended_at) if isinstance(ended_at, str) else ended_at
                    duration = int((end_time - start_time).total_seconds())
                    logger.info(f"📊 Calculated duration from timestamps: {duration}s (from {started_at} to {ended_at})")
                except Exception as duration_error:
                    logger.warning(f"⚠️ Could not calculate duration from timestamps: {duration_error}")

        cost = call_data.get("cost", 0) or 0
        status = call_data.get("status", "unknown")

        # Map VAPI status/ended_reason to our status
        our_status = "completed"
        if ended_reason in ["customer-did-not-answer", "customer-busy", "voicemail", "silence-timed-out"]:
            our_status = "no_answer"
        elif status in ["failed", "error"] or "error" in ended_reason.lower() or "failed" in ended_reason.lower():
            our_status = "failed"
        elif ended_reason in ["ended", "customer-ended-call", "assistant-ended-call", "exceeded-max-duration"]:
            our_status = "completed"

        logger.info(f"📊 Updating campaign {campaign_id} progress for call {call_id}: status={our_status}, duration={duration}s, cost=${cost}")

        # Update call record in campaign_calls collection
        await campaign_service.campaign_calls_collection.update_one(
            {"call_id": call_id},
            {
                "$set": {
                    "status": our_status,
                    "duration": duration,
                    "cost": cost,
                    "completed_at": datetime.now(timezone.utc)
                }
            }
        )

        # Get current campaign to calculate new averages
        campaign = await campaign_service.get_campaign(campaign_id)
        if not campaign:
            logger.warning(f"⚠️ Campaign {campaign_id} not found")
            return {"success": False, "error": "Campaign not found"}

        # Calculate new progress counters
        new_called = campaign.progress.called + 1
        new_completed = campaign.progress.completed + 1

        # Update status-specific counters
        increment_fields = {
            "progress.called": 1,
            "progress.completed": 1
        }

        if our_status == "completed":
            increment_fields["progress.successful"] = 1
        elif our_status == "failed":
            increment_fields["progress.failed"] = 1
        elif our_status == "no_answer":
            increment_fields["progress.no_answer"] = 1

        # Calculate new cost and avg duration
        new_total_cost = campaign.total_cost + cost
        new_avg_duration = ((campaign.avg_call_duration * campaign.progress.called) + duration) / new_called if new_called > 0 else 0

        # Update campaign
        await campaign_service.campaigns_collection.update_one(
            {"_id": campaign_id},
            {
                "$inc": increment_fields,
                "$set": {
                    "total_cost": new_total_cost,
                    "avg_call_duration": new_avg_duration,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

        logger.info(f"✅ Campaign progress updated: called={new_called}, cost=${new_total_cost:.2f}, avg_duration={new_avg_duration:.1f}s")

        return {
            "success": True,
            "campaign_id": campaign_id,
            "new_called": new_called,
            "new_total_cost": new_total_cost
        }

    except Exception as e:
        logger.error(f"❌ Failed to update campaign progress: {e}")
        return {"success": False, "error": str(e)}


async def handle_end_of_call_report(request: VapiWebhookRequest, background_tasks: BackgroundTasks):
    """
    Handle end-of-call-report webhook event.
    Triggers transcript summary and call logging pipeline.

    Extracts and logs organization context from call metadata.
    """
    try:
        logger.warning(f"📞 END-OF-CALL PROCESSING: Starting post-call pipeline")

        # Extract call data - VAPI sends it in request.call for end-of-call-report
        message_data = request.message or {}
        call_data = request.call or {}  # Call data is at top level for end-of-call-report
        artifact = message_data.get("artifact", {})

        # Extract call ID first so we can fetch complete data
        call_id = call_data.get("id", "unknown")

        # Fetch complete call data from VAPI API
        # Reason: end-of-call-report webhook doesn't include startedAt, endedAt, or complete cost
        if call_id != "unknown":
            logger.info(f"🔄 Fetching complete call data from VAPI API for call {call_id}")
            complete_call_data = await fetch_vapi_call_data(call_id)
            if complete_call_data:
                # Merge complete data with webhook data (webhook has transcript, complete has timestamps/cost)
                call_data = {**call_data, **complete_call_data}
                logger.info(f"✅ Merged complete call data: startedAt={call_data.get('startedAt')}, endedAt={call_data.get('endedAt')}, cost={call_data.get('cost')}")
            else:
                logger.warning(f"⚠️ Could not fetch complete call data from VAPI API, using webhook data only")

        # Debug log the structure
        if not call_data or call_data.get("id") == None:
            logger.warning(f"⚠️ Call data is empty or incomplete. message_data keys: {list(message_data.keys()) if message_data else 'None'}")
            logger.warning(f"⚠️ request.call: {request.call}")

        # Extract organization context from call metadata
        metadata = call_data.get("metadata", {})
        org_id = metadata.get("organization_id") if metadata else None
        automation_id = metadata.get("automation_id") if metadata else None
        campaign_id = metadata.get("campaign_id") or metadata.get("campaignId") if metadata else None
        assistant_id = call_data.get("assistantId") or call_data.get("assistant_id")

        # Extract key information (call_id already extracted above for API fetch)
        phone_number = request.phoneNumber or call_data.get("phoneNumber") or call_data.get("customer", {}).get("number", "unknown")
        ended_reason = message_data.get("endedReason", "unknown")
        transcript = artifact.get("transcript", "")
        messages = artifact.get("messages", [])

        logger.warning(f"📞 CALL DATA: ID={call_id}, Organization={org_id or 'Not specified'}, Campaign={campaign_id or 'N/A'}, Automation={automation_id or 'N/A'}, Assistant={assistant_id or 'N/A'}, Phone={phone_number}, Reason={ended_reason}, Transcript Length={len(transcript)}")

        results = []

        # 1. Generate AI transcript summary
        if transcript:
            summary_result = await generate_transcript_summary(
                call_id=call_id,
                transcript=transcript,
                background_tasks=background_tasks
            )
            results.append(("transcript_summary", summary_result))

        # 2. Log call details to database with organization context
        call_log_result = await log_call_details(
            call_id=call_id,
            phone_number=phone_number,
            transcript=transcript,
            ended_reason=ended_reason,
            messages=messages,
            call_data=call_data,
            background_tasks=background_tasks,
            organization_id=org_id,
            automation_id=automation_id,
            assistant_id=assistant_id,
            campaign_id=campaign_id
        )
        results.append(("call_logging", call_log_result))

        # 3. Update campaign progress if this is a campaign call
        if campaign_id:
            campaign_update_result = await update_campaign_progress_from_webhook(
                campaign_id=campaign_id,
                call_id=call_id,
                call_data=call_data,
                ended_reason=ended_reason
            )
            results.append(("campaign_progress", campaign_update_result))

        # 4. Send notification email to team (optional)
        if transcript:
            notification_result = await send_call_notification(
                call_id=call_id,
                phone_number=phone_number,
                transcript=transcript,
                ended_reason=ended_reason,
                background_tasks=background_tasks
            )
            results.append(("notification", notification_result))

        # 5. Charge wallet for call usage
        wallet_charge_result = await charge_wallet_for_call(
            call_data=call_data,
            call_id=call_id,
            background_tasks=background_tasks
        )
        results.append(("wallet_charge", wallet_charge_result))

        # Compile results
        successful_operations = [name for name, result in results if result.get("success")]
        failed_operations = [name for name, result in results if not result.get("success")]

        logger.info(f"📞 POST-CALL PIPELINE: Successful={successful_operations}, Failed={failed_operations}")

        return {
            "status": "processed",
            "call_id": call_id,
            "operations_completed": successful_operations,
            "operations_failed": failed_operations,
            "pipeline_results": dict(results)
        }

    except Exception as e:
        logger.error(f"📞 END-OF-CALL ERROR: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "call_id": call_data.get("id", "unknown") if 'call_data' in locals() else "unknown"
        }

async def handle_transcript_event(request: VapiWebhookRequest, background_tasks: BackgroundTasks):
    """
    Handle transcript webhook event for real-time processing.

    Extracts and logs organization context from call metadata.
    """
    try:
        message_data = request.message or {}
        call_data = request.call or {}

        # Extract organization context from call metadata
        metadata = call_data.get("metadata", {})
        org_id = metadata.get("organization_id") if metadata else None

        transcript_type = message_data.get("transcriptType", "unknown")
        transcript = message_data.get("transcript", "")
        role = message_data.get("role", "unknown")
        call_id = call_data.get("id", "unknown")

        logger.info(f"📝 TRANSCRIPT EVENT: Type={transcript_type}, Role={role}, Call={call_id}, Organization={org_id or 'Not specified'}, Text='{transcript[:100]}...'")

        # For now, just acknowledge receipt
        # Could be extended for real-time processing like sentiment analysis
        return {
            "status": "acknowledged",
            "call_id": call_id,
            "transcript_type": transcript_type,
            "role": role,
            "processed_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"📝 TRANSCRIPT EVENT ERROR: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

async def generate_transcript_summary(call_id: str, transcript: str, background_tasks: BackgroundTasks):
    """Generate AI-powered summary of call transcript."""
    try:
        # Use a simple summary for now - can be enhanced with proper AI service
        lines = transcript.split('\n')
        total_lines = len(lines)
        word_count = len(transcript.split())

        # Extract key points (simplified)
        key_points = []
        if "doctor" in transcript.lower() or "hospital" in transcript.lower():
            key_points.append("Healthcare inquiry")
        if "appointment" in transcript.lower() or "booking" in transcript.lower():
            key_points.append("Appointment request")
        if "emergency" in transcript.lower():
            key_points.append("Emergency situation")

        summary = f"Call summary: {total_lines} conversation turns, {word_count} words exchanged. " + \
                 f"Key topics: {', '.join(key_points) if key_points else 'General inquiry'}"

        logger.info(f"🤖 TRANSCRIPT SUMMARY: Generated for call {call_id}")
        return {
            "success": True,
            "summary": summary,
            "key_points": key_points,
            "word_count": word_count,
            "call_id": call_id
        }

    except Exception as e:
        logger.error(f"🤖 TRANSCRIPT SUMMARY ERROR: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "call_id": call_id
        }

async def log_call_details(call_id: str, phone_number: str, transcript: str,
                          ended_reason: str, messages: list, call_data: dict,
                          background_tasks: BackgroundTasks,
                          organization_id: Optional[str] = None,
                          automation_id: Optional[str] = None,
                          assistant_id: Optional[str] = None,
                          campaign_id: Optional[str] = None):
    """
    Log comprehensive call details to MongoDB collections.

    Saves to three collections:
    - vapi_calls: General call logs for /call-logs API
    - automation_calls: Automation-linked call records
    - campaign_calls: Campaign-specific tracking (only if campaign_id provided)

    Args:
        call_id: VAPI call ID
        phone_number: Customer phone number
        transcript: Call transcript
        ended_reason: Why the call ended
        messages: Call messages array
        call_data: Full VAPI call data
        background_tasks: FastAPI background tasks
        organization_id: Organization UUID for multi-tenant isolation
        automation_id: Automation config ID
        assistant_id: VAPI assistant ID
        campaign_id: Campaign ID (if this is a campaign call)
    """
    try:
        from ..mongo import get_database
        db = get_database()

        # Extract integrations/tools used from messages
        integrations_used = []
        tool_call_count = 0

        for message in messages:
            if not isinstance(message, dict):
                continue

            # Check for tool calls in various formats
            if message.get("role") == "tool_call" or message.get("type") == "tool-call":
                tool_name = message.get("name") or message.get("tool_name")
                if tool_name and tool_name not in integrations_used:
                    integrations_used.append(tool_name)
                    tool_call_count += 1

            if "function_call" in message:
                function_name = message["function_call"].get("name")
                if function_name and function_name not in integrations_used:
                    integrations_used.append(function_name)
                    tool_call_count += 1

            if "toolCalls" in message:
                for tool_call in message.get("toolCalls", []):
                    tool_name = tool_call.get("function", {}).get("name")
                    if tool_name and tool_name not in integrations_used:
                        integrations_used.append(tool_name)
                        tool_call_count += 1

        # Calculate duration from timestamps
        started_at = call_data.get("startedAt")
        ended_at = call_data.get("endedAt")
        duration = 0

        if started_at and ended_at:
            try:
                from dateutil import parser
                start_time = parser.parse(started_at) if isinstance(started_at, str) else started_at
                end_time = parser.parse(ended_at) if isinstance(ended_at, str) else ended_at
                duration = int((end_time - start_time).total_seconds())
            except Exception as e:
                logger.warning(f"Could not calculate duration: {e}")

        # Get cost from VAPI
        cost = call_data.get("cost", 0) or 0

        # Extract phone_id from call data
        phone_id = call_data.get("phoneNumberId") or call_data.get("phone_number_id")

        # Determine call status from ended_reason
        call_status = "completed"
        if ended_reason in ["customer-did-not-answer", "customer-busy", "voicemail",
                           "voicemail-reached", "no-answer", "no_answer_from_user", "silence-timed-out"]:
            call_status = "no_answer"
        elif ended_reason in ["error", "failed", "assistant-error"] or "error" in ended_reason.lower():
            call_status = "failed"

        now = datetime.utcnow()

        # 1. Save to vapi_calls (primary call logs for /call-logs API)
        vapi_calls = db["vapi_calls"]
        vapi_record = {
            "call_id": call_id,
            "organization_id": organization_id,
            "automation_id": automation_id,
            "campaign_id": campaign_id,
            "assistant_id": assistant_id or call_data.get("assistantId"),
            "phone_id": phone_id,
            "customer_phone": phone_number,
            "status": call_status,
            "ended_reason": ended_reason,
            "duration": duration,
            "cost": cost,
            "transcript": transcript,
            "messages": messages[:50] if messages else [],  # Limit messages stored
            "recording_url": call_data.get("recordingUrl") or call_data.get("recording_url"),
            "started_at": started_at,
            "ended_at": ended_at,
            "integrations_used": integrations_used,
            "tool_call_count": tool_call_count,
            "created_at": now,
            "updated_at": now
        }

        await vapi_calls.update_one(
            {"call_id": call_id},
            {"$set": vapi_record},
            upsert=True
        )
        logger.info(f"✅ VAPI_CALLS: Saved call {call_id} (org={organization_id}, status={call_status}, duration={duration}s, cost=${cost})")

        # 2. Save to automation_calls (for automation analytics)
        automation_calls = db["automation_calls"]
        automation_record = {
            "call_id": call_id,
            "organization_id": organization_id,
            "automation_id": automation_id,
            "campaign_id": campaign_id,
            "assistant_id": assistant_id or call_data.get("assistantId"),
            "phone_id": phone_id,
            "customer_number": phone_number,
            "status": call_status,
            "duration": duration,
            "vapi_cost": cost,
            "transcript": transcript[:2000] if transcript else "",
            "integrations_used": integrations_used,
            "tool_call_count": tool_call_count,
            "started_at": started_at or now,
            "ended_at": ended_at or now,
            "created_at": now
        }

        await automation_calls.update_one(
            {"call_id": call_id},
            {"$set": automation_record},
            upsert=True
        )
        logger.info(f"✅ AUTOMATION_CALLS: Saved call {call_id}")

        # 3. Save to campaign_calls (only if campaign_id provided)
        if campaign_id:
            campaign_calls = db["campaign_calls"]
            campaign_record = {
                "call_id": call_id,
                "campaign_id": campaign_id,
                "organization_id": organization_id,
                "automation_id": automation_id,
                "assistant_id": assistant_id,
                "phone_id": phone_id,
                "phone_number": phone_number,
                "status": call_status,
                "duration": duration,
                "cost": cost,
                "transcript": transcript,
                "recording_url": call_data.get("recordingUrl") or call_data.get("recording_url"),
                "ended_reason": ended_reason,
                "integrations_used": integrations_used,
                "tool_call_count": tool_call_count,
                "called_at": ended_at or now,
                "created_at": now
            }

            await campaign_calls.update_one(
                {"call_id": call_id},
                {"$set": campaign_record},
                upsert=True
            )
            logger.info(f"✅ CAMPAIGN_CALLS: Saved call {call_id} for campaign {campaign_id}")

        return {
            "success": True,
            "call_id": call_id,
            "status": call_status,
            "duration": duration,
            "cost": cost,
            "integrations_tracked": len(integrations_used)
        }

    except Exception as e:
        logger.error(f"❌ CALL LOGGING ERROR for {call_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "call_id": call_id
        }

async def send_call_notification(call_id: str, phone_number: str, transcript: str,
                                ended_reason: str, background_tasks: BackgroundTasks):
    """Send notification email about completed call."""
    try:
        # Generate summary for email
        summary = f"Call {call_id} completed with reason: {ended_reason}"

        # Truncate transcript for email
        email_transcript = transcript[:500] + "..." if len(transcript) > 500 else transcript

        # Use existing email handler
        email_args = {
            "to_email": "ailabsafrica@gmail.com",
            "subject": f"Call Report - {call_id}",
            "message": f"Call completed from {phone_number}. Transcript preview: {email_transcript}",
            "customer_name": f"Caller {phone_number}",
            "call_summary": summary
        }

        result = await handle_email_send(email_args, background_tasks)

        logger.info(f"📧 CALL NOTIFICATION: Sent email for call {call_id}")
        return {
            "success": True,
            "call_id": call_id,
            "email_result": result
        }

    except Exception as e:
        logger.error(f"📧 CALL NOTIFICATION ERROR: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "call_id": call_id
        }

async def handle_google_calendar_booking(args: Dict[str, Any], background_tasks: BackgroundTasks):
    """Create actual Google Calendar event entry."""
    try:
        # Import Google Calendar service
        from ..services.google_calendar_service import get_google_calendar_service, CalendarBookingRequest

        calendar_service = get_google_calendar_service()

        # Validate required fields
        customer_name = args.get("customer_name", "")
        customer_email = args.get("customer_email", "")
        appointment_date = args.get("appointment_date", "")
        appointment_time = args.get("appointment_time", "")
        duration_minutes = args.get("duration_minutes", 30)
        meeting_type = args.get("meeting_type", "consultation")
        notes = args.get("notes", "")

        if not all([customer_name, customer_email, appointment_date, appointment_time]):
            return {
                "message": {
                    "type": "assistant",
                    "content": "I need the customer's name, email, preferred date, and time to create a calendar appointment. Could you provide those details?"
                }
            }

        # Validate date format
        try:
            datetime.strptime(appointment_date, "%Y-%m-%d")
            datetime.strptime(appointment_time, "%H:%M")
        except ValueError:
            return {
                "message": {
                    "type": "assistant",
                    "content": "Please provide the date in YYYY-MM-DD format and time in HH:MM format (24-hour)."
                }
            }

        # Create booking request
        booking_request = CalendarBookingRequest(
            customer_name=customer_name,
            customer_email=customer_email,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            duration_minutes=duration_minutes,
            meeting_type=meeting_type,
            notes=notes,
            timezone="UTC"
        )

        # Create calendar event
        result = await calendar_service.create_calendar_event(booking_request)

        if result.get("success"):
            event_id = result.get("event_id", "unknown")
            event_link = result.get("event_link", "")
            meeting_link = result.get("meeting_link", "")

            response_content = f"Perfect! I've created a {duration_minutes}-minute {meeting_type} appointment for {customer_name} on {appointment_date} at {appointment_time}. "
            response_content += f"The calendar entry has been created with ID {event_id}."

            if meeting_link:
                response_content += f" A Google Meet link has been included: {meeting_link}"

            logger.info(f"✅ GOOGLE CALENDAR: Created event {event_id} for {customer_name}")

            return {
                "message": {
                    "type": "assistant",
                    "content": response_content,
                    "function_call_result": {
                        "success": True,
                        "calendar_entry_created": True,
                        "event_id": event_id,
                        "event_link": event_link,
                        "meeting_link": meeting_link,
                        "date": appointment_date,
                        "time": appointment_time,
                        "duration": duration_minutes,
                        "attendee": customer_email,
                        "meeting_type": meeting_type,
                        "provider": "google_calendar"
                    }
                }
            }
        else:
            error_msg = result.get("error", "Unknown error")
            if result.get("requires_setup"):
                error_msg = "Google Calendar is not configured. Please contact support to set up calendar integration."

            return {
                "message": {
                    "type": "assistant",
                    "content": f"I encountered an issue creating the calendar appointment: {error_msg}. Please try again or contact support."
                }
            }

    except Exception as e:
        logger.error(f"Google Calendar booking error: {str(e)}")
        return {
            "message": {
                "type": "assistant",
                "content": f"I encountered an issue with Google Calendar booking: {str(e)}. Please try again or contact support."
            }
        }

async def handle_google_calendar_availability_check(args: Dict[str, Any], background_tasks: BackgroundTasks):
    """Check Google Calendar availability for actual time slots."""
    try:
        # Import Google Calendar service
        from ..services.google_calendar_service import get_google_calendar_service, CalendarAvailabilityRequest

        calendar_service = get_google_calendar_service()

        date = args.get("date", "")
        duration_minutes = args.get("duration_minutes", 30)
        meeting_type = args.get("meeting_type", "consultation")

        if not date:
            return {
                "message": {
                    "type": "assistant",
                    "content": "Please provide a date (YYYY-MM-DD format) to check availability."
                }
            }

        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return {
                "message": {
                    "type": "assistant",
                    "content": "Please provide the date in YYYY-MM-DD format (e.g., 2025-09-25)."
                }
            }

        # Create availability request
        availability_request = CalendarAvailabilityRequest(
            date=date,
            duration_minutes=duration_minutes,
            meeting_type=meeting_type,
            timezone="UTC"
        )

        # Check availability
        result = await calendar_service.check_availability(availability_request)

        if result.get("success"):
            available_times = result.get("available_times", [])
            source = result.get("source", "google_calendar")
            today = datetime.now().strftime('%Y-%m-%d')

            if available_times:
                available_times_text = ", ".join(available_times[:3])  # Limit to 3 for voice

                response_content = f"Today is {today}. For {date}, I found availability for {duration_minutes}-minute {meeting_type} appointments at: {available_times_text}."

                if source == "google_calendar":
                    response_content += " These are real-time slots from Google Calendar."
                elif source == "mock_availability":
                    response_content += " (Note: Google Calendar not configured - showing sample times)"

                response_content += " Would you like me to schedule one of these times?"

                logger.info(f"📅 GOOGLE CALENDAR AVAILABILITY: Found {len(available_times)} slots for {date}")

                return {
                    "message": {
                        "type": "assistant",
                        "content": response_content,
                        "function_call_result": {
                            "success": True,
                            "date": date,
                            "available_times": available_times[:3],
                            "duration": duration_minutes,
                            "source": source,
                            "total_slots": result.get("total_slots_found", len(available_times)),
                            "provider": "google_calendar"
                        }
                    }
                }
            else:
                return {
                    "message": {
                        "type": "assistant",
                        "content": f"Today is {today}. Unfortunately, I don't see any available {duration_minutes}-minute slots for {date}. Please try a different date."
                    }
                }
        else:
            error_msg = result.get("error", "Unknown error")
            return {
                "message": {
                    "type": "assistant",
                    "content": f"I'm having trouble checking calendar availability: {error_msg}. Please try again."
                }
            }

    except Exception as e:
        logger.error(f"Google Calendar availability check error: {str(e)}")
        return {
            "message": {
                "type": "assistant",
                "content": f"I encountered an issue checking Google Calendar availability: {str(e)}. Please try again."
            }
        }