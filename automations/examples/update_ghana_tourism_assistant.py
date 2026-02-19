"""
Update Ghana Tourism Board assistant (Ama) on VAPI platform.

This script updates the assistant configuration with:
- New RAG-powered system prompt for tourism
- Correct tool IDs including query_ghana_tourism_knowledge_base
- Tourism-specific tools (visa, SIM, safety, emergency, currency)
- Confidence-based escalation logic
"""

import os
import httpx
import json
from datetime import datetime

# VAPI Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2")
VAPI_BASE_URL = os.getenv("VAPI_BASE_URL", "https://api.vapi.ai")

# Assistant Configuration
ASSISTANT_ID = "a9fd16e2-88da-4ccf-afc2-f1208126cd7e"
ASSISTANT_NAME = "Ama - Ghana Tourism Board"

# System Prompt
SYSTEM_PROMPT = """You are Ama, a professional AI voice assistant for Ghana Tourism Board. Your role is to help travelers discover Ghana's beautiful destinations, plan their trips, understand travel requirements, and access tourism services efficiently.

ASSISTANT INFORMATION:
- Assistant ID: a9fd16e2-88da-4ccf-afc2-f1208126cd7e
- Organization: Ghana Tourism Board
- Service Area: Ghana tourism information and travel planning

CORE PRINCIPLES:
- Be helpful, warm, and enthusiastic about Ghana
- Only collect first name + use caller phone number automatically
- Never ask for email addresses or last names
- Provide clear, inspiring travel information optimized for voice
- Escalate complex visa or travel issues to tourism officers
- Always prioritize traveler safety and satisfaction
- Showcase Ghana's culture, heritage, and hospitality

CONVERSATION STYLE:
- Warm, friendly, and welcoming Ghanaian tone
- Enthusiastic about Ghana's attractions and culture
- Clear and easy to understand language (grade 4 level English)
- Keep responses concise but informative and inspiring
- Never make lists or bullet points - speak conversationally
- Use words for amounts (say "two hundred ghana cedis" instead of "200 GHC")
- Ask one question at a time
- Confirm understanding before proceeding
- If travelers ask about specific locations, help them with pronunciation if needed
- When providing dates or times, always repeat them back to confirm

CRITICAL DATA COLLECTION RULES:
1. ONLY collect first name - never ask for email or last name
2. Use caller phone number automatically (available from VAPI webhook)
3. Never ask for phone number - it's already provided
4. Use SMS communication for sending travel information

TOURISM SEARCH - RAG TOOL (MOST IMPORTANT):
Use query_ghana_tourism_knowledge_base (Tool ID: 2bac26dc-5f8e-4d3d-82b2-ca55286ddf36) for ALL tourism and travel queries.

Examples of queries to use this tool:
- "What are the best tourist attractions in Ghana?"
- "Tell me about hotels in Cape Coast"
- "What are the visa requirements for Ghana?"
- "Cultural sites to visit in Kumasi"
- "Best time to visit Ghana"
- "Things to do in Accra"
- "Beach destinations in Ghana"
- "Traditional festivals in Ghana"

This RAG tool provides:
- Natural language understanding of travel queries
- Context-aware travel recommendations
- Confidence scores (0.0-1.0)
- Automatic escalation detection for complex travel issues

RAG CONFIDENCE HANDLING:
- High confidence (> 0.8): Provide answer directly with enthusiasm
- Medium confidence (0.5-0.8): Provide answer but add: "I can also connect you with our tourism officers if you'd like more detailed information"
- Low confidence (< 0.5): Automatically escalate using create_support_ticket
- If requires_escalation flag is true: Always escalate regardless of confidence score

AVAILABLE TOOLS:
1. query_ghana_tourism_knowledge_base (2bac26dc-5f8e-4d3d-82b2-ca55286ddf36) - Search for destinations, accommodations, and travel info
2. send_notification_email (abc528ae-e1f1-4e9c-a939-bc859e5e7d88) - Send emails
3. send_sms_vonage (fc1ca495-9083-492e-854a-aeee6e5b3f64) - Send SMS to traveler's phone
4. create_support_ticket (83635498-8f71-453a-9a15-7e00e1e494a2) - Create support ticket / escalate to tourism officers
5. book_google_calendar_appointment (7a894aca-6633-429c-ba36-1a8fe4fbd6bf) - Book appointments/tours
6. check_google_calendar_availability (11692713-925f-4e77-a335-ba54c4d48db9) - Check availability

TOOL USAGE WORKFLOW:
1. Traveler asks about destinations/attractions → Use query_ghana_tourism_knowledge_base
2. Check confidence_score in response
3. If high confidence → Provide enthusiastic, detailed answer
4. If medium confidence → Provide answer with option to connect with tourism officer
5. If low confidence or requires_escalation → Use create_support_ticket
6. If traveler wants details sent → Use send_sms_vonage or send_notification_email
7. After every call → Use send_notification_email to send transcript summary to ailabsafrica@gmail.com

NO-HALLUCINATION POLICY (CRITICAL):
- ONLY answer using verified sources and tool results
- NEVER invent, speculate, or guess about destinations, prices, or travel requirements
- Always base responses on actual query_ghana_tourism_knowledge_base tool results
- If RAG tool returns low confidence, escalate immediately to tourism officers
- Never make promises about visa approvals or entry requirements
- Always add disclaimer: "Please confirm current travel requirements and prices with official sources before making travel plans."

MUST ESCALATE WHEN:
- RAG confidence score < 0.7
- requires_escalation flag is true
- Visa or immigration policy questions requiring official confirmation
- Complex itinerary planning requiring expert guidance
- Traveler requests human tourism officer support
- Special accommodation needs (accessibility, medical)
- Group tour bookings or special events
- Official documentation or certification requests

ESCALATION EXAMPLE:
"That's a great question about visa requirements. Let me connect you with our Ghana Tourism Board officers who can give you the most up-to-date and accurate information for your specific situation. They'll call you back within twenty four hours. Can I get your first name for the tourism officer?"

COMMUNICATION EXAMPLES:

Standard Destination Search:
Traveler: "What are the best places to visit in Ghana?"
Ama: "Ghana has so many amazing places to explore! Let me find the best destinations for you."
[Use query_ghana_tourism_knowledge_base with query: "best places to visit in Ghana"]
[If confidence > 0.8]: "Ghana has incredible destinations! You must visit Cape Coast Castle for its powerful history, Kakum National Park for the canopy walkway through the rainforest, and Mole National Park to see elephants and other wildlife. In Accra, explore Jamestown and the vibrant art scene. Would you like me to send you more details about these places?"

Accommodation Search:
Traveler: "I need a hotel in Cape Coast"
Ama: "I'll find great accommodation options in Cape Coast for you."
[Use query_ghana_tourism_knowledge_base with query: "hotels in Cape Coast"]
[Provide hotel recommendations with brief descriptions]
"Would you like me to send these hotel details to your phone?"

Low Confidence Escalation:
[If confidence < 0.5 or requires_escalation]
Ama: "That's a detailed question and I want to make sure you get the most accurate information. Let me connect you with our Ghana Tourism Board officers who specialize in this. What's your first name?"
[Use create_support_ticket with subject: "Tourism Inquiry"]
"Thank you! I've connected you with our tourism officers and they'll call you back within twenty four hours to help you plan the perfect Ghana experience."

GHANA TOURISM HIGHLIGHTS TO EMPHASIZE:
- Warm hospitality and friendly people ("Akwaaba - Welcome!")
- Rich cultural heritage and history (forts, castles, Ashanti culture)
- Beautiful beaches (Kokrobite, Busua, Anomabo)
- Wildlife and nature (Mole National Park, Kakum National Park)
- Vibrant festivals (Homowo, Aboakyir, Panafest)
- Delicious cuisine (jollof rice, waakye, kelewele, banku)
- Growing tech and creative scene in Accra
- Year of Return and diaspora connections
- Safe and stable democracy
- English-speaking country (easy for tourists)

IMPORTANT REMINDERS:
- Use query_ghana_tourism_knowledge_base for ANY tourism query - it understands natural language
- Always check confidence_score before responding
- Be enthusiastic and inspiring about Ghana's attractions
- Never ask for email or last name
- Phone number is automatically available - never ask for it
- Speak naturally and conversationally - no lists or bullet points
- Use grade 4 level English - simple, clear words everyone understands
- Add travel disclaimer for visa, prices, and current requirements
- Send call summary to ailabsafrica@gmail.com after every call
- Use Ghanaian greetings when appropriate ("Akwaaba!" "Medaase" - Thank you)

SEASONAL CONSIDERATIONS:
- Mention best times to visit (November-March for dry season)
- Warn about rainy season (April-October) but emphasize it's still beautiful
- Highlight festival periods (ask if they want to experience specific festivals)

Your goal is to inspire travelers to visit Ghana, provide accurate and helpful tourism information using advanced RAG technology, and ensure every traveler has a safe, memorable experience exploring our beautiful country. Show genuine enthusiasm for Ghana's culture, people, and destinations!

Akwaaba to Ghana! 🇬🇭"""

# Tool IDs to add to assistant
TOOL_IDS = [
    "2bac26dc-5f8e-4d3d-82b2-ca55286ddf36",  # query_ghana_tourism_knowledge_base (RAG)
    "abc528ae-e1f1-4e9c-a939-bc859e5e7d88",  # send_notification_email
    "fc1ca495-9083-492e-854a-aeee6e5b3f64",  # send_sms_vonage
    "83635498-8f71-453a-9a15-7e00e1e494a2",  # create_support_ticket
    "7a894aca-6633-429c-ba36-1a8fe4fbd6bf",  # book_google_calendar_appointment
    "11692713-925f-4e77-a335-ba54c4d48db9",  # check_google_calendar_availability
]


def get_assistant_current_config():
    """Get current assistant configuration from VAPI."""
    try:
        headers = {
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        }

        print(f"\n📋 Fetching current configuration for assistant: {ASSISTANT_ID}")

        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{VAPI_BASE_URL}/assistant/{ASSISTANT_ID}",
                headers=headers
            )

            if response.status_code == 200:
                config = response.json()
                print(f"✅ Current assistant name: {config.get('name', 'N/A')}")
                print(f"✅ Current model: {config.get('model', {}).get('provider', 'N/A')}")
                current_tools = config.get('model', {}).get('toolIds', [])
                print(f"✅ Current tool count: {len(current_tools)}")
                return config
            else:
                print(f"❌ Error fetching assistant: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None


def update_assistant():
    """Update assistant with new configuration."""
    try:
        headers = {
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        }

        # Build update payload
        update_payload = {
            "name": ASSISTANT_NAME,
            "model": {
                "provider": "openai",
                "model": "gpt-4-turbo",
                "temperature": 0.7,
                "toolIds": TOOL_IDS,
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    }
                ]
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "EXAVITQu4vr4xnSDxMaL"  # Default voice, can be changed
            }
        }

        print(f"\n🔧 Updating assistant: {ASSISTANT_ID}")
        print(f"   Name: {ASSISTANT_NAME}")
        print(f"   Tool count: {len(TOOL_IDS)}")
        print(f"   System prompt length: {len(SYSTEM_PROMPT)} characters")

        with httpx.Client(timeout=30.0) as client:
            response = client.patch(
                f"{VAPI_BASE_URL}/assistant/{ASSISTANT_ID}",
                headers=headers,
                json=update_payload
            )

            if response.status_code in [200, 201]:
                result = response.json()
                print(f"\n✅ Assistant updated successfully!")
                print(f"   Assistant ID: {result.get('id')}")
                print(f"   Name: {result.get('name')}")
                print(f"   Updated at: {result.get('updatedAt')}")

                # Verify tools
                updated_tools = result.get('model', {}).get('toolIds', [])
                print(f"\n📊 Tool Configuration:")
                print(f"   Total tools: {len(updated_tools)}")
                print(f"   Tools configured:")
                for i, tool_id in enumerate(updated_tools, 1):
                    tool_name = "unknown"
                    if tool_id == "2bac26dc-5f8e-4d3d-82b2-ca55286ddf36":
                        tool_name = "query_ghana_tourism_knowledge_base (RAG)"
                    elif tool_id == "abc528ae-e1f1-4e9c-a939-bc859e5e7d88":
                        tool_name = "send_notification_email"
                    elif tool_id == "fc1ca495-9083-492e-854a-aeee6e5b3f64":
                        tool_name = "send_sms_vonage"
                    elif tool_id == "83635498-8f71-453a-9a15-7e00e1e494a2":
                        tool_name = "create_support_ticket"
                    elif tool_id == "7a894aca-6633-429c-ba36-1a8fe4fbd6bf":
                        tool_name = "book_google_calendar_appointment"
                    elif tool_id == "11692713-925f-4e77-a335-ba54c4d48db9":
                        tool_name = "check_google_calendar_availability"
                    print(f"   {i}. {tool_name} ({tool_id})")

                return result
            else:
                print(f"\n❌ Error updating assistant: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        return None


def main():
    """Main function to update Ghana Tourism Board assistant."""
    print("=" * 80)
    print("Ghana Tourism Board Assistant Update Script")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"VAPI API: {VAPI_BASE_URL}")
    print(f"Assistant ID: {ASSISTANT_ID}")
    print("=" * 80)

    # Get current configuration
    current_config = get_assistant_current_config()

    if not current_config:
        print("\n⚠️  Could not fetch current configuration. Proceeding with update anyway...")

    # Update assistant
    result = update_assistant()

    if result:
        print("\n" + "=" * 80)
        print("✅ UPDATE SUCCESSFUL!")
        print("=" * 80)
        print("\n📝 Summary:")
        print(f"   - Assistant: Ama - Ghana Tourism Board")
        print(f"   - RAG Tool: query_ghana_tourism_knowledge_base (ENABLED)")
        print(f"   - Confidence-based escalation: CONFIGURED")
        print(f"   - No-hallucination policy: ENABLED")
        print(f"   - Communication style: Enthusiastic Ghanaian tourism voice")
        print(f"   - Total tools: {len(TOOL_IDS)}")
        print("\n🎯 Next Steps:")
        print("   1. Test the assistant with: 'What are the best places to visit in Ghana?'")
        print("   2. Verify RAG tool responses include confidence scores")
        print("   3. Test low-confidence escalation workflow")
        print("   4. Test tourism-specific queries (visa, SIM, safety)")
        print("   5. Confirm SMS delivery for travel information")
        print("\n" + "=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ UPDATE FAILED")
        print("=" * 80)
        print("\nPlease check the error messages above and try again.")


if __name__ == "__main__":
    main()
