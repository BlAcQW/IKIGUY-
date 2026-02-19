#!/usr/bin/env python3
"""
VAPI Squad Assistant Configurations
Creates router and 6 regional assistants for Premier Health Navigator
"""

import json
from regional_city_segmentation import REGIONAL_CITIES, get_region_keyterms

# VAPI API Configuration
VAPI_API_KEY = "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"
VAPI_BASE_URL = "https://api.vapi.ai"

# Current Assistant ID (for reference)
CURRENT_ASSISTANT_ID = "baa69b3a-8944-4557-9ef9-3a5aa6956eb3"

# Region mapping for transfer
REGION_MAPPING = {
    "Greater Accra": ["ACCRA", "TEMA", "MADINA", "LEGON", "DANSOMAN", "KANESHIE"],
    "Ashanti": ["KUMASI", "ASHANTI", "OBUASI", "MAMPONG"],
    "Northern Regions": ["TAMALE", "NORTHERN", "BOLGATANGA", "BOLGA", "WA", "BAWKU"],
    "Western and Central": ["TAKORADI", "WESTERN", "SEKONDI", "CAPE COAST", "CENTRAL", "TARKWA"],
    "Eastern and Volta": ["KOFORIDUA", "EASTERN", "HO", "VOLTA", "HOHOE", "NKAWKAW"],
    "Bono Regions": ["SUNYANI", "BONO", "TECHIMAN", "BEREKUM", "AHAFO"],
}


def create_router_assistant_config():
    """
    Create the main router assistant that asks for region and transfers

    Returns:
        dict: Router assistant configuration
    """
    # Get all region trigger words for router
    all_region_triggers = []
    for region, triggers in REGION_MAPPING.items():
        all_region_triggers.extend(triggers)

    config = {
        "name": "Premier Health Router",
        "model": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "messages": [
                {
                    "role": "system",
                    "content": """You are a routing assistant for Premier Health Insurance Navigator in Ghana.

Your ONLY job is to quickly identify which region the customer needs and transfer them to the appropriate regional specialist.

AVAILABLE REGIONS:
1. Greater Accra - Covers Accra, Tema, Madina, Legon, and surrounding areas
2. Ashanti - Covers Kumasi, Obuasi, Mampong, and Ashanti region
3. Northern Regions - Covers Tamale, Bolgatanga, Wa, Bawku, and all northern areas
4. Western and Central - Covers Takoradi, Sekondi, Cape Coast, Tarkwa, and surrounding areas
5. Eastern and Volta - Covers Koforidua, Ho, Hohoe, Nkawkaw, and surrounding areas
6. Bono, Bono East, and Ahafo - Covers Sunyani, Techiman, Berekum, and surrounding areas

ROUTING PROCESS:
1. Greet warmly: "Hello! Welcome to Premier Health. I'm here to help you find healthcare providers."
2. Ask for region: "Which region are you calling from? For example, Greater Accra, Ashanti, Northern, Western, Central, Eastern, Volta, or Bono?"
3. Listen for ANY city or region name mentioned
4. As SOON as you identify the region, transfer immediately using transfer_call tool
5. NEVER provide healthcare information yourself - always transfer

IMPORTANT:
- Be quick and efficient - identify region and transfer within 2 exchanges
- If customer mentions ANY city name, immediately identify its region and transfer
- If unsure, ask: "Are you in the Accra area, Kumasi area, Tamale area, or another region?"
- NEVER search for healthcare facilities - that's the regional assistant's job
- ALWAYS use transfer_call tool after identifying region

Example conversation:
Customer: "I need a doctor"
You: "I can help with that! Which region are you in? For example, Accra, Kumasi, Tamale, or another area?"
Customer: "I'm in Madina"
You: [Use transfer_call to Greater Accra specialist] "Transferring you to our Greater Accra specialist who knows all the healthcare facilities in your area..."

Example 2:
Customer: "I need emergency care in Kumasi"
You: [Immediately use transfer_call to Ashanti specialist] "Connecting you to our Ashanti region specialist right away..."

Be warm but BRIEF. Your goal is fast routing to the right specialist."""
                }
            ],
            "tools": [
                {
                    "type": "transferCall",
                    "destinations": [
                        {
                            "type": "assistant",
                            "assistantName": "Premier Health Greater Accra",
                            "message": "Let me connect you to our Greater Accra specialist who knows all the healthcare facilities in your area.",
                            "description": "Transfer to Greater Accra specialist for Accra, Tema, Madina, Legon, and surrounding areas"
                        },
                        {
                            "type": "assistant",
                            "assistantName": "Premier Health Ashanti",
                            "message": "Let me connect you to our Ashanti specialist who knows all the healthcare facilities in your area.",
                            "description": "Transfer to Ashanti specialist for Kumasi, Obuasi, Mampong, and surrounding areas"
                        },
                        {
                            "type": "assistant",
                            "assistantName": "Premier Health Northern Regions",
                            "message": "Let me connect you to our Northern regions specialist who knows all the healthcare facilities in your area.",
                            "description": "Transfer to Northern specialist for Tamale, Bolgatanga, Wa, Bawku, and surrounding areas"
                        },
                        {
                            "type": "assistant",
                            "assistantName": "Premier Health Western and Central",
                            "message": "Let me connect you to our Western and Central specialist who knows all the healthcare facilities in your area.",
                            "description": "Transfer to Western/Central specialist for Takoradi, Sekondi, Cape Coast, and surrounding areas"
                        },
                        {
                            "type": "assistant",
                            "assistantName": "Premier Health Eastern and Volta",
                            "message": "Let me connect you to our Eastern and Volta specialist who knows all the healthcare facilities in your area.",
                            "description": "Transfer to Eastern/Volta specialist for Koforidua, Ho, Hohoe, and surrounding areas"
                        },
                        {
                            "type": "assistant",
                            "assistantName": "Premier Health Bono Regions",
                            "message": "Let me connect you to our Bono specialist who knows all the healthcare facilities in your area.",
                            "description": "Transfer to Bono specialist for Sunyani, Techiman, Berekum, and surrounding areas"
                        }
                    ]
                }
            ]
        },
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-3",
            "language": "en-GB",
            "keyterm": all_region_triggers[:100]  # Limit to 100
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "EXAVITQu4vr4xnSDxMaL",  # Sarah - Soft, warm female voice
            "model": "eleven_turbo_v2_5"
        },
        "firstMessage": "Hello! Welcome to Premier Health. I'm here to help you find healthcare providers. Which region are you calling from? For example, Greater Accra, Ashanti, Northern, Western, Central, Eastern, Volta, or Bono?",
        "endCallMessage": "Thank you for calling Premier Health. Take care!",
        "endCallPhrases": ["goodbye", "bye", "end call", "hang up"],
        "recordingEnabled": True,
        "hipaaEnabled": False,
        "clientMessages": [
            "transcript",
            "hang",
            "function-call",
            "speech-update",
            "metadata",
            "conversation-update"
        ],
        "serverMessages": [
            "end-of-call-report",
            "status-update",
            "hang",
            "function-call"
        ],
        "silenceTimeoutSeconds": 30,
        "maxDurationSeconds": 600,
        "backgroundSound": "office",
        "backchannelingEnabled": False,
        "backgroundDenoisingEnabled": True,
        "modelOutputInMessagesEnabled": True
    }

    return config


def create_regional_assistant_config(region_name, region_cities):
    """
    Create a regional specialist assistant configuration

    Args:
        region_name (str): Name of region (e.g., "Greater Accra")
        region_cities (list): List of cities in the region

    Returns:
        dict: Regional assistant configuration
    """
    # Limit cities to 100 for Deepgram
    keyterm_cities = region_cities[:100]

    # Region-specific system prompts
    region_info = {
        "Greater Accra": "Greater Accra region, including Accra, Tema, Madina, and all surrounding areas",
        "Ashanti": "Ashanti region, including Kumasi, Obuasi, Mampong, and all surrounding areas",
        "Northern Regions": "Northern, Upper East, Upper West, and Savannah regions, including Tamale, Bolgatanga, Wa, and all surrounding areas",
        "Western and Central": "Western and Central regions, including Takoradi, Sekondi, Cape Coast, and all surrounding areas",
        "Eastern and Volta": "Eastern and Volta regions, including Koforidua, Ho, Hohoe, and all surrounding areas",
        "Bono Regions": "Bono, Bono East, and Ahafo regions, including Sunyani, Techiman, Berekum, and all surrounding areas"
    }

    config = {
        "name": f"Premier Health {region_name}",
        "model": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.7,
            "messages": [
                {
                    "role": "system",
                    "content": f"""You are Ama, a professional AI voice assistant for Premier Health Insurance Navigator. You are the specialist for {region_info[region_name]}.

CORE PRINCIPLES:
- Be helpful, accurate, and professional at all times
- Be engaging but CONCISE - complete your thought, then pause for response
- Only collect first name + use caller phone number automatically
- Never ask for email addresses or last names
- Provide clear, concise responses optimized for voice
- Escalate complex issues to human support when appropriate
- Always prioritize customer safety and satisfaction

YOUR REGION: {region_name}
You specialize in healthcare facilities in {region_info[region_name]}.

CONVERSATION STYLE:
- Warm, friendly, and professional Ghanaian tone
- Clear and easy to understand language (grade 4 level English)
- Keep responses SHORT and complete - don't ramble
- Never make lists or bullet points - speak conversationally
- Use words for amounts (say "forty five ghana cedis" instead of "45.00 GHC")
- Ask one question at a time
- Confirm understanding before proceeding
- When taking phone numbers or emails, always repeat them back to confirm

CRITICAL: COMPLETE INFORMATION DELIVERY
When providing search results:
1. State how many providers you found
2. Give ALL details for first 3 providers in ONE continuous statement
3. For each provider: name, location, and phone number

Example: "I found seven general practitioners in Madina. Here are the first three: Esidem Hospital, Crown Medical Center which accepts platinum and platinum plus plans at zero two zero four eight two six five seven five six, and Adenta Clinic."

AVAILABLE TOOLS:
1. query_premier_health_knowledge_base - find healthcare providers and services covered by premier health insurance in ghana

TOOL USAGE:
- Use tool results immediately and naturally in your response
- When you find responses, provide first 3 with name, phone numbers and location for each

Examples of queries to use this tool:
- "Find me doctors in Madina"
- "Emergency hospitals in Accra"
- "Pediatricians near East Legon"
- "I need a cardiologist"
- "What specialties does Premier Health cover?"

NO-HALLUCINATION POLICY (CRITICAL):
- ONLY answer using verified sources and tool results
- NEVER invent, speculate, or guess if information is missing
- Always base responses on actual query_premier_health_knowledge_base tool results
- If RAG tool returns low confidence, escalate immediately
- Never make promises or guarantees about coverage without verification
- Always add disclaimer: "This is general guidance. Please confirm details with your healthcare provider before making decisions."

MUST ESCALATE WHEN:
- Complex medical advice requested
- Policy questions or financial commitments
- Customer requests human support
- Location not found after spelling confirmation
- Personal or confidential data handling

ESCALATION EXAMPLE:
"I don't have complete information about that specific area. Let me connect you with our Premier Health support team who can help you directly. They'll call you back within 24 hours. Can I confirm your first name for the support ticket?"

EMERGENCY SEARCH:
Customer: "I need emergency help"
Assistant: "For life-threatening emergencies, please call the national ambulance service at one nine three immediately. I can also find you the nearest emergency hospital. What area are you in?"

IMPORTANT REMINDERS:
- Speak naturally and conversationally - no lists or bullet points
- Complete your full response before pausing
- Use grade 4 level English - simple, clear words everyone understands

Your goal is fast, efficient service using advanced RAG technology to provide accurate, context-aware healthcare information while maintaining a warm, professional Ghanaian voice."""
                }
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "query_premier_health_knowledge_base",
                        "description": "Search for healthcare providers and services covered by Premier Health Insurance in Ghana. Use this to find hospitals, clinics, doctors, specialists, and other medical services.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query. Include the type of provider (e.g., 'general practitioner', 'hospital', 'cardiologist') and location (e.g., 'Madina', 'East Legon', 'Accra'). Examples: 'general practitioners in Madina', 'emergency hospitals in Accra', 'pediatricians near Legon'"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }
            ],
            "toolIds": []
        },
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-3",
            "language": "en-GB",
            "keyterm": keyterm_cities
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "EXAVITQu4vr4xnSDxMaL",
            "model": "eleven_turbo_v2_5"
        },
        "firstMessage": f"Hello! I'm Ama, your Premier Health specialist for {region_name}. How can I help you find healthcare providers today?",
        "endCallMessage": "Thank you for calling Premier Health. Take care and stay healthy!",
        "endCallPhrases": ["goodbye", "bye", "end call", "hang up", "that's all", "thank you bye"],
        "recordingEnabled": True,
        "hipaaEnabled": False,
        "clientMessages": [
            "transcript",
            "hang",
            "function-call",
            "speech-update",
            "metadata",
            "conversation-update"
        ],
        "serverMessages": [
            "end-of-call-report",
            "status-update",
            "hang",
            "function-call"
        ],
        "silenceTimeoutSeconds": 30,
        "maxDurationSeconds": 1200,
        "backgroundSound": "office",
        "backchannelingEnabled": False,
        "backgroundDenoisingEnabled": True,
        "modelOutputInMessagesEnabled": True,
        "serverUrl": "https://api.ailabsafrica.com/vapi/webhooks/premier-health",
        "serverUrlSecret": "your-webhook-secret-here"
    }

    return config


def create_squad_config(router_id, regional_assistant_ids):
    """
    Create the squad configuration with router and all regional assistants

    Args:
        router_id (str): ID of router assistant
        regional_assistant_ids (dict): Dict mapping region names to assistant IDs

    Returns:
        dict: Squad configuration
    """
    members = [
        {
            "assistant": router_id,
            "assistantDestinations": [
                {
                    "type": "assistant",
                    "assistantName": f"Premier Health {region}",
                    "message": f"Let me connect you to our {region} specialist who knows all the healthcare facilities in your area.",
                    "description": f"Transfer to {region} specialist for healthcare queries in that region"
                }
                for region in REGIONAL_CITIES.keys()
            ]
        }
    ]

    # Add all regional assistants as members
    for region, assistant_id in regional_assistant_ids.items():
        members.append({
            "assistant": assistant_id
        })

    config = {
        "name": "Premier Health Navigator Squad",
        "members": members
    }

    return config


def export_all_configurations():
    """
    Export all assistant configurations to JSON files
    """
    # Create router config
    router_config = create_router_assistant_config()
    with open('/opt/kasaai/apps/automations/premier-health/config_router_assistant.json', 'w') as f:
        json.dump(router_config, f, indent=2)
    print("✓ Created router assistant configuration")

    # Create regional assistant configs
    for region, cities in REGIONAL_CITIES.items():
        regional_config = create_regional_assistant_config(region, cities)
        safe_filename = region.replace(" ", "_").replace(",", "").lower()
        filename = f'/opt/kasaai/apps/automations/premier-health/config_{safe_filename}_assistant.json'
        with open(filename, 'w') as f:
            json.dump(regional_config, f, indent=2)
        print(f"✓ Created {region} assistant configuration ({len(cities[:100])} cities)")

    # Create squad template (IDs will be filled in after deployment)
    squad_template = {
        "name": "Premier Health Navigator Squad",
        "members": [
            {
                "assistant": "{{ROUTER_ASSISTANT_ID}}",
                "assistantDestinations": [
                    {
                        "type": "assistant",
                        "assistantName": f"Premier Health {region}",
                        "message": f"Let me connect you to our {region} specialist.",
                        "description": f"Transfer to {region} for healthcare queries"
                    }
                    for region in REGIONAL_CITIES.keys()
                ]
            }
        ] + [
            {"assistant": "{{ASSISTANT_ID_" + region.replace(' ', '_').replace(',', '').upper() + "}}"}
            for region in REGIONAL_CITIES.keys()
        ]
    }

    with open('/opt/kasaai/apps/automations/premier-health/config_squad_template.json', 'w') as f:
        json.dump(squad_template, f, indent=2)
    print("✓ Created squad configuration template")

    print("\n" + "=" * 80)
    print("CONFIGURATION EXPORT COMPLETE")
    print("=" * 80)
    print(f"✓ Router assistant configuration: config_router_assistant.json")
    print(f"✓ {len(REGIONAL_CITIES)} regional assistant configurations")
    print(f"✓ Squad template: config_squad_template.json")
    print("\nNext step: Run deployment script to create assistants in VAPI")


if __name__ == "__main__":
    export_all_configurations()
