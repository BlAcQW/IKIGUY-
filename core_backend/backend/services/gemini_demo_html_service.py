"""
Gemini-powered Demo HTML Generation Service

Generates professional, customized HTML demo pages for VAPI voice assistants
using Google's Gemini AI to create context-aware content.
"""

import logging
import os
import re
from typing import Dict, Any, Optional

from .gemini_service import get_gemini_service

logger = logging.getLogger(__name__)


class GeminiDemoHTMLService:
    """Service for generating demo HTML pages using Gemini AI."""

    def __init__(self):
        self.vapi_public_key = os.getenv("VAPI_PUBLIC_API_KEY", "0c22dcea-0d6c-4fc0-8fb2-93292d8575e8")

    async def generate_demo_html(
        self,
        company_info: Dict[str, Any],
        vapi_assistant_id: str,
        automation_type: str = "sales",
        extracted_content: str = ""
    ) -> Dict[str, Any]:
        """
        Generate a professional demo HTML page using Gemini AI.

        Args:
            company_info (Dict[str, Any]): Company information from extraction
            vapi_assistant_id (str): VAPI assistant ID for the widget
            automation_type (str): Type of automation (sales, helpdesk, etc.)
            extracted_content (str): Raw website content for context

        Returns:
            Dict[str, Any]: Response containing HTML content and generation metadata
        """
        try:
            logger.info(f"🎨 Generating demo HTML for {company_info.get('name', 'Unknown')} using Gemini")

            # Get Gemini service
            gemini_service = get_gemini_service()

            if not gemini_service or not gemini_service.api_key:
                logger.warning("❌ Gemini API key not available, using fallback HTML")
                fallback_html = self._build_fallback_html(company_info, vapi_assistant_id, automation_type)
                return {
                    "html": fallback_html,
                    "method": "fallback",
                    "notification": {
                        "type": "warning",
                        "message": "🚫 Gemini AI unavailable - Using basic HTML template",
                        "emoji": "🚫",
                        "reason": "gemini_api_key_missing"
                    }
                }

            # Extract company details
            company_name = company_info.get('name', 'Your Company')
            services = company_info.get('services', [])
            description = company_info.get('description', '')
            about_text = company_info.get('aboutText', '')
            business_hours = company_info.get('businessHours', 'Standard business hours')
            contact_info = company_info.get('contactInfo', {})

            # Map automation type to user-friendly description
            assistant_type_map = {
                'sales': 'sales assistant',
                'helpdesk': 'customer support assistant',
                'healthcare': 'healthcare assistant',
                'lead_generation': 'lead generation assistant',
                'appointment_booking': 'appointment booking assistant',
                'customer_support': 'customer success assistant'
            }

            assistant_description = assistant_type_map.get(automation_type, 'assistant')
            assistant_name = f"{company_name} AI {assistant_description.title()}"

            # Build comprehensive prompt
            prompt = self._build_gemini_prompt(
                company_name=company_name,
                assistant_name=assistant_name,
                assistant_description=assistant_description,
                vapi_assistant_id=vapi_assistant_id,
                services=services,
                description=description,
                about_text=about_text,
                business_hours=business_hours,
                contact_info=contact_info,
                extracted_content=extracted_content
            )

            # Generate HTML with Gemini
            # Reason: Reduced timeout from 60s to 45s and tokens from 8192 to 6000 for faster generation
            response = await gemini_service.generate_content(
                prompt=prompt,
                temperature=0.3,
                max_output_tokens=6000,
                timeout=45.0
            )

            if response.get('success') and response.get('content'):
                generated_html = response['content']
                logger.info("✅ Gemini HTML generation successful")

                # Clean up any markdown formatting
                clean_html = self._clean_html_response(generated_html)

                # Validate the HTML contains required elements
                if self._validate_html(clean_html, vapi_assistant_id):
                    return {
                        "html": clean_html,
                        "method": "gemini",
                        "notification": {
                            "type": "success",
                            "message": "🎨 Professional HTML generated using Gemini AI",
                            "emoji": "🎨",
                            "reason": "gemini_success"
                        }
                    }
                else:
                    logger.warning("⚠️ Generated HTML failed validation, using fallback")
                    fallback_html = self._build_fallback_html(company_info, vapi_assistant_id, automation_type)
                    return {
                        "html": fallback_html,
                        "method": "fallback",
                        "notification": {
                            "type": "warning",
                            "message": "⚠️ AI-generated HTML failed validation - Using basic template",
                            "emoji": "⚠️",
                            "reason": "validation_failed"
                        }
                    }
            else:
                logger.error(f"❌ Gemini HTML generation failed: {response.get('error', 'Unknown error')}")
                fallback_html = self._build_fallback_html(company_info, vapi_assistant_id, automation_type)
                return {
                    "html": fallback_html,
                    "method": "fallback",
                    "notification": {
                        "type": "error",
                        "message": f"❌ Gemini AI generation failed - Using basic template",
                        "emoji": "❌",
                        "reason": "gemini_generation_failed",
                        "details": response.get('error', 'Unknown error')
                    }
                }

        except Exception as e:
            logger.error(f"❌ Demo HTML generation error: {str(e)}")
            fallback_html = self._build_fallback_html(company_info, vapi_assistant_id, automation_type)
            return {
                "html": fallback_html,
                "method": "fallback",
                "notification": {
                    "type": "error",
                    "message": "❌ Unexpected error occurred - Using basic template",
                    "emoji": "❌",
                    "reason": "unexpected_error",
                    "details": str(e)
                }
            }

    def _build_gemini_prompt(
        self,
        company_name: str,
        assistant_name: str,
        assistant_description: str,
        vapi_assistant_id: str,
        services: list,
        description: str,
        about_text: str,
        business_hours: str,
        contact_info: dict,
        extracted_content: str
    ) -> str:
        """Build the Gemini prompt for HTML generation."""

        services_text = ", ".join(services[:4]) if services else "professional services"
        phone = contact_info.get('phone', '')
        email = contact_info.get('email', '')
        address = contact_info.get('address', '')

        return f"""You are generating a professional landing page for {company_name}, featuring their AI {assistant_description} named "{assistant_name}".

COMPANY INFORMATION:
- Company: {company_name}
- Description: {description}
- About: {about_text}
- Services: {services_text}
- Business Hours: {business_hours}
- Phone: {phone}
- Email: {email}
- Address: {address}

WEBSITE CONTENT:
{extracted_content[:2000] if extracted_content else 'No additional website content available'}

CRITICAL WIDGET REQUIREMENT - THIS IS MANDATORY:
You MUST include the EXACT Vapi widget code provided below. DO NOT create any custom JavaScript. DO NOT use window.Vapi, vapi.start(), or any other implementation. The widget code below is REQUIRED and CANNOT be modified in any way.

EXACT WIDGET CODE TO COPY (DO NOT CHANGE ANYTHING):
<vapi-widget
  public-key="{self.vapi_public_key}"
  assistant-id="{vapi_assistant_id}"
  mode="voice"
  theme="dark"
  base-bg-color="#000000"
  accent-color="#14B8A6"
  cta-button-color="#000000"
  cta-button-text-color="#ffffff"
  border-radius="large"
  size="full"
  position="bottom-right"
  title="Talk to {assistant_name}"
  start-button-text="Start Call"
  end-button-text="End Call"
  chat-first-message="Hello! How can I help you today?"
  chat-placeholder="Type your message..."
  voice-show-transcript="true"
  consent-required="true"
  consent-title="Terms and conditions"
  consent-content="By clicking 'Agree,' and each time I interact with this AI agent, I consent to the recording, storage, and sharing of my communications with third-party service providers, and as otherwise described in our Terms of Service."
  consent-storage-key="vapi_widget_consent"
></vapi-widget>

<script src="https://unpkg.com/@vapi-ai/client-sdk-react/dist/embed/widget.umd.js" async type="text/javascript"></script>

FORBIDDEN - DO NOT USE:
- new window.Vapi()
- vapi.start()
- cdn.jsdelivr.net
- onclick handlers for calls
- placeholder API keys
- any custom JavaScript for Vapi

DESIGN REQUIREMENTS:
1. Create a modern, professional landing page
2. Use Tailwind CSS via CDN
3. Include compelling copy based on company information
4. Add 4 relevant service cards based on their actual services
5. Use appropriate industry colors (banking: blue, healthcare: teal, tech: purple)
6. Place the EXACT widget code at the end of body tag
7. Make it conversion-focused and visually appealing
8. Include company contact information if available
9. Use the company's actual services and description
10. Create industry-appropriate hero section

Generate ONLY the complete HTML page with the exact widget code included. Do not add explanations or markdown formatting."""

    def _clean_html_response(self, html: str) -> str:
        """Clean up Gemini response to extract pure HTML."""
        # Remove any markdown code block formatting
        html = re.sub(r'^```html\n?', '', html)
        html = re.sub(r'\n?```$', '', html)
        html = re.sub(r'^html\n', '', html)
        return html.strip()

    def _validate_html(self, html: str, vapi_assistant_id: str) -> bool:
        """Validate that the generated HTML contains required elements."""
        # Check for basic HTML structure
        if not html.startswith('<!DOCTYPE html>'):
            return False

        # Check for VAPI widget
        if f'assistant-id="{vapi_assistant_id}"' not in html:
            return False

        # Check for widget script
        if 'widget.umd.js' not in html:
            return False

        return True

    def _build_fallback_html(
        self,
        company_info: Dict[str, Any],
        vapi_assistant_id: str,
        automation_type: str
    ) -> str:
        """Build a fallback HTML page when Gemini is unavailable."""

        company_name = company_info.get('name', 'Your Company')
        services = company_info.get('services', [])
        description = company_info.get('description', '')
        contact_info = company_info.get('contactInfo', {})

        # Generate service cards based on available services or industry defaults
        if services:
            feature_cards = self._generate_service_cards(services[:4])
        else:
            feature_cards = self._generate_default_cards(automation_type)

        phone = contact_info.get('phone', '')
        email = contact_info.get('email', '')

        assistant_name = f"{company_name} AI Assistant"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{company_name} - AI Voice Assistant Demo</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {{
            font-family: 'Inter', sans-serif;
        }}
        .hero {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .service-card {{
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .service-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body class="bg-gray-50">

    <!-- Hero Section -->
    <header class="hero text-white py-20">
        <div class="container mx-auto px-6 text-center">
            <h1 class="text-5xl font-bold mb-4">{company_name}</h1>
            <h2 class="text-2xl mb-6">AI Voice Assistant Demo</h2>
            <p class="text-xl mb-8 max-w-2xl mx-auto">{description or f'Experience intelligent conversation with our AI assistant. Get expert help and support through voice interaction.'}</p>
            <div class="bg-white bg-opacity-20 rounded-lg p-4 inline-block">
                <p class="text-lg">🎤 Try our voice assistant now using the widget in the bottom-right corner!</p>
            </div>
        </div>
    </header>

    <!-- Services Section -->
    <section class="py-16">
        <div class="container mx-auto px-6">
            <h2 class="text-4xl font-bold text-center mb-12 text-gray-800">Our Services</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                {feature_cards}
            </div>
        </div>
    </section>

    <!-- About Section -->
    <section class="bg-white py-16">
        <div class="container mx-auto px-6 text-center">
            <h2 class="text-4xl font-bold mb-8 text-gray-800">About {company_name}</h2>
            <p class="text-lg text-gray-600 max-w-3xl mx-auto mb-8">{company_info.get('aboutText', description) or f'{company_name} is committed to providing exceptional service and innovative solutions to meet your needs.'}</p>
            <div class="bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg p-6 max-w-2xl mx-auto">
                <h3 class="text-2xl font-bold mb-4">Ready to Get Started?</h3>
                <p class="text-lg">Click the voice assistant widget to experience our AI-powered support!</p>
            </div>
        </div>
    </section>

    <!-- Contact Section -->
    <section class="bg-gray-100 py-16">
        <div class="container mx-auto px-6 text-center">
            <h2 class="text-4xl font-bold mb-8 text-gray-800">Contact Us</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
                {f'<div class="bg-white rounded-lg p-6 shadow-md"><i class="fas fa-phone text-3xl text-blue-600 mb-4"></i><h3 class="text-xl font-semibold mb-2">Phone</h3><p class="text-gray-600">{phone}</p></div>' if phone else ''}
                {f'<div class="bg-white rounded-lg p-6 shadow-md"><i class="fas fa-envelope text-3xl text-blue-600 mb-4"></i><h3 class="text-xl font-semibold mb-2">Email</h3><p class="text-gray-600">{email}</p></div>' if email else ''}
                <div class="bg-white rounded-lg p-6 shadow-md">
                    <i class="fas fa-robot text-3xl text-blue-600 mb-4"></i>
                    <h3 class="text-xl font-semibold mb-2">AI Assistant</h3>
                    <p class="text-gray-600">Available 24/7 via voice chat</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-800 text-white py-8">
        <div class="container mx-auto px-6 text-center">
            <p>&copy; 2025 {company_name}. All rights reserved.</p>
            <p class="mt-2 text-gray-400">Powered by AI Voice Technology</p>
        </div>
    </footer>

<vapi-widget
  public-key="{self.vapi_public_key}"
  assistant-id="{vapi_assistant_id}"
  mode="voice"
  theme="dark"
  base-bg-color="#000000"
  accent-color="#14B8A6"
  cta-button-color="#000000"
  cta-button-text-color="#ffffff"
  border-radius="large"
  size="full"
  position="bottom-right"
  title="Talk to {assistant_name}"
  start-button-text="Start Call"
  end-button-text="End Call"
  chat-first-message="Hello! How can I help you today?"
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

    def _generate_service_cards(self, services: list) -> str:
        """Generate service cards from actual company services."""
        icons = ['fas fa-star', 'fas fa-cog', 'fas fa-users', 'fas fa-chart-line']
        cards = []

        for i, service in enumerate(services):
            icon = icons[i % len(icons)]
            cards.append(f"""
                <div class="service-card bg-white rounded-lg shadow-md p-6">
                    <i class="{icon} text-3xl text-blue-600 mb-4"></i>
                    <h3 class="text-xl font-semibold text-gray-800 mb-2">{service}</h3>
                    <p class="text-gray-600">Professional {service.lower()} services tailored to your needs.</p>
                </div>
            """)

        return ''.join(cards)

    def _generate_default_cards(self, automation_type: str) -> str:
        """Generate default service cards based on automation type."""
        type_cards = {
            'sales': [
                {'icon': 'fas fa-handshake', 'title': 'Lead Qualification', 'desc': 'Intelligent lead scoring and qualification'},
                {'icon': 'fas fa-chart-line', 'title': 'Sales Analytics', 'desc': 'Real-time sales performance tracking'},
                {'icon': 'fas fa-calendar-check', 'title': 'Appointment Booking', 'desc': 'Seamless meeting scheduling'},
                {'icon': 'fas fa-phone', 'title': '24/7 Support', 'desc': 'Round-the-clock customer assistance'}
            ],
            'helpdesk': [
                {'icon': 'fas fa-headset', 'title': 'Customer Support', 'desc': 'Expert assistance for all inquiries'},
                {'icon': 'fas fa-ticket-alt', 'title': 'Ticket Management', 'desc': 'Efficient issue tracking and resolution'},
                {'icon': 'fas fa-clock', 'title': 'Quick Response', 'desc': 'Fast response times guaranteed'},
                {'icon': 'fas fa-users', 'title': 'Expert Team', 'desc': 'Dedicated support professionals'}
            ],
            'healthcare': [
                {'icon': 'fas fa-user-md', 'title': 'Medical Assistance', 'desc': 'Professional healthcare guidance'},
                {'icon': 'fas fa-calendar-alt', 'title': 'Appointments', 'desc': 'Easy appointment scheduling'},
                {'icon': 'fas fa-shield-alt', 'title': 'HIPAA Compliant', 'desc': 'Secure and private consultations'},
                {'icon': 'fas fa-stethoscope', 'title': 'Expert Care', 'desc': 'Quality healthcare services'}
            ]
        }

        cards = type_cards.get(automation_type, type_cards['sales'])
        html_cards = []

        for card in cards:
            html_cards.append(f"""
                <div class="service-card bg-white rounded-lg shadow-md p-6">
                    <i class="{card['icon']} text-3xl text-blue-600 mb-4"></i>
                    <h3 class="text-xl font-semibold text-gray-800 mb-2">{card['title']}</h3>
                    <p class="text-gray-600">{card['desc']}</p>
                </div>
            """)

        return ''.join(html_cards)


# Singleton instance
_demo_html_service = None

async def get_demo_html_service() -> GeminiDemoHTMLService:
    """Get the singleton demo HTML service instance."""
    global _demo_html_service
    if _demo_html_service is None:
        _demo_html_service = GeminiDemoHTMLService()
    return _demo_html_service