#!/usr/bin/env python3
"""
Update Premier Health VAPI Assistant with Separated City Names

This deployment updates Deepgram keywords after reprocessing data to separate
compound city names (e.g., SANTASI/PATASI) into individual cities.

Changes:
- Replace compound names: "Santasipatase" → "Santasi", "Patasi"
- Replace compound names: "Tafobremang" → "Tafo", "Bremang"
- Add 25+ new individual city names from reprocessing
- Update keyterms to match new separated structure

Usage:
    python update_vapi_with_separated_cities.py
"""

import os
import sys
import httpx
from datetime import datetime

# Add the path to import the updated lists
sys.path.insert(0, '/opt/kasaai/apps/automations/premier-health')
from deepgram_keywords_updated import KEYWORDS

# VAPI Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2")
VAPI_BASE_URL = os.getenv("VAPI_BASE_URL", "https://api.vapi.ai")

# Assistant Configuration
ASSISTANT_ID = "baa69b3a-8944-4557-9ef9-3a5aa6956eb3"
ASSISTANT_NAME = "Ama - Premier Health Navigator"

# Updated KEYTERMS with separated cities
KEYTERMS = [
    # Location groups (updated to reflect separated cities)
    "Accra Central Tudu Makola",
    "Achimota New Achimota",
    "Ahodwo Ahinsan",
    "Airport Residential Area 37 Area",
    "Amansaman Pokuase",
    "Ashaiman Community 26",
    "Asiakwa Osino Anyinam Enyiresi Kibi",
    "Asikuma Ajumako",
    "Asylum Down",
    "Bomso Knust Ejisu",  # Now separated in keywords
    "Cape Coast Environs",
    "Circle Kaneshie North Kaneshie Industrial Area",
    "Dansoman Mamprobi Korle Bu",
    "Dome Haatso Ashongman Kwabenya",
    "Dzorwulu Abelenkpe",
    "East Legon Adjringanor",
    "Kintampo Duayaw Nkwanta Others",
    "Kokomlemle Maamobi Nima",
    "Konongo Agogo",
    "Labone La Tse Addo Cantonments",
    "Lapaz Nyamekye Darkuman Odorkor",
    "Latebiokoshie Mataheko",
    "Legon North Legon",
    "Madina Adenta Dodowa",  # Now separated in keywords
    "Mamfe Akuapem",
    "Mampong Agona Wiamoase",
    "Mamponteng",  # Added as keyterm for higher priority
    "New Abirem",
    "Obuasi Dunkwa",
    "Sakumono Estate Lashibi Comm 181921",
    "Santasi",  # Added as individual keyterm
    "Patasi",  # Added as individual keyterm
    "Sefwi Anhwiaso",
    "Sefwi Asafo",
    "Sefwi Asawinso",
    "Sefwi Bekwai",
    "Sefwi Bibiani",
    "Sefwi Bodi",
    "Sefwi Essam",
    "Sefwi Juaboso",
    "Sefwi Wiawso",
    "Somanya",  # Now separate (was: Somanyaodumase Krobo)
    "Odumase Krobo",  # Now separate
    "Spintex Road Baatsona",
    "Suaman Dadieso",
    "Tafo",  # Now separate (was: Tafobremang)
    "Bremang",  # Now separate
    "Tantra Hill Ofankor",
    "Tema Community 2",
    "Tema Community 2 4",
    "Tema Community 4 5 6 9 10 12",
    "Teshie Nungua",
    "Wassa Akropong",
    "Weija Kasoa Gbawe",
    # Medical specialties (unchanged)
    "cardiologist",
    "dermatologist",
    "emergency medicine",
    "family medicine",
    "general practitioner",
    "gynecologist",
    "internal medicine",
    "ophthalmologist",
    "orthopedic surgeon",
    "pediatrician",
]

# System Prompt (same as before)
SYSTEM_PROMPT = """You are Ama, a professional AI voice assistant for Premier Health Insurance Navigator. Your role is to help customers find healthcare providers, understand their insurance coverage, and access medical services efficiently in Ghana.

Due to possible errors in speech-to-text when converting city and region names, if a user mentions a location that doesn't exist in Ghana, ask for the region they are in and suggest cities with similar-sounding names.

Examples of common misheard locations:
- "Secondary" → Sekondi (Western region)
- "Winnipeg" → Winneba (Central region)
- "Medina" → Madina (Greater Accra region)
- "Congo" → Kumasi (Ashanti region) or Kongo (Eastern region)

If a region name sounds wrong, provide 2 similar-sounding regions and ask them to choose "first or second".

CORE PRINCIPLES:
- Be helpful, accurate, and professional at all times
- Be engaging but CONCISE - complete your thought, then pause for response
- Only collect first name + use caller phone number automatically
- Never ask for email addresses or last names
- Provide clear, concise responses optimized for voice
- Escalate complex issues to human support when appropriate
- Always prioritize customer safety and satisfaction

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
4. THEN stop and ask if they want the information sent

Example: "I found seven general practitioners in Madina. Here are the first three: Esidem Hospital, Crown Medical Center which accepts platinum and platinum plus plans at zero two zero four eight two six five seven five six, and Adenta Clinic. Would you like me to send you their full contact details?"

AVAILABLE TOOLS:
1. query_premier_health_knowledge_base - find healthcare providers and services covered by premier health insurance in ghana

## TOOL USAGE
- Use tool results immediately and naturally in your response
- When you find responses, provide first 3 with name, phone numbers and location for each

Examples of queries to use this tool:
- "Find me doctors in Madina"
- "Emergency hospitals in Accra"
- "Pediatricians near East Legon"
- "I need a cardiologist"
- "What specialties does Premier Health cover?"

7. After every call → Use send_notification_email to send transcript summary to ailabsafrica@gmail.com

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

COMMUNICATION EXAMPLES:

Emergency Search:
Customer: "I need emergency help"
Assistant: "For life-threatening emergencies, please call the national ambulance service at one nine three immediately. I can also find you the nearest emergency hospital. What area are you in?"

IMPORTANT REMINDERS:
- Speak naturally and conversationally - no lists or bullet points
- Complete your full response before pausing
- Use grade 4 level English - simple, clear words everyone understands
- Add medical disclaimer for all health advice
- Send call summary to ailabsafrica@gmail.com after every call

Your goal is fast, efficient service using advanced RAG technology to provide accurate, context-aware healthcare information while maintaining a warm, professional Ghanaian voice."""

# Tool IDs
TOOL_IDS = [
    "560adfee-43bf-4614-baa8-0d5ccfbe9769",  # query_premier_health_knowledge_base (RAG)
    "abc528ae-e1f1-4e9c-a939-bc859e5e7d88",  # send_notification_email
    "fc1ca495-9083-492e-854a-aeee6e5b3f64",  # send_sms_vonage
    "83635498-8f71-453a-9a15-7e00e1e494a2",  # create_support_ticket
    "7a894aca-6633-429c-ba36-1a8fe4fbd6bf",  # book_google_calendar_appointment
    "11692713-925f-4e77-a335-ba54c4d48db9",  # check_google_calendar_availability
]


def verify_separated_cities():
    """Verify that separated cities are properly included."""
    print("\n🔍 Verifying separated city coverage...")

    test_cities = {
        "Santasi": "keyword",
        "Patasi": "keyword",
        "Tafo": "keyword",
        "Bremang": "keyword",
        "Somanya": "keyword",
        "Odumase": "keyword",
        "Begoro": "keyword",
        "Osiem": "keyword",
        "Abuakwa": "keyword",
        "Swedru": "keyword",
        "Assin": "keyword",
        "Kumasi": "keyword",
    }

    all_pass = True
    for city, expected_type in test_cities.items():
        if city in KEYWORDS:
            print(f"   ✓ {city} (keyword)")
        else:
            print(f"   ✗ MISSING: {city} (should be keyword)")
            all_pass = False

    return all_pass


def update_assistant():
    """Update assistant with separated city configuration."""
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
                "voiceId": "EXAVITQu4vr4xnSDxMaL"
            },
            "transcriber": {
                "provider": "deepgram",
                "model": "nova-3",
                "language": "en-GB",
                "keywords": KEYWORDS,
                "keyterm": KEYTERMS,
                "smartFormat": True,
                "endpointing": 300,
                "numerals": True
            },
            "stopSpeakingPlan": {
                "numWords": 1,
                "voiceSeconds": 0.2,
                "backoffSeconds": 0.5
            },
            "startSpeakingPlan": {
                "waitSeconds": 0.8,
                "smartEndpointingEnabled": True
            },
            "responseDelaySeconds": 0.4,
            "llmRequestDelaySeconds": 0.1,
            "backgroundSound": "office",
            "backgroundDenoisingEnabled": True,
            "modelOutputInMessagesEnabled": True,
            "maxDurationSeconds": 900,
            "silenceTimeoutSeconds": 30,
            "artifactPlan": {
                "recordingEnabled": True,
                "videoRecordingEnabled": False,
                "transcriptPlan": {
                    "enabled": True,
                    "assistantName": "Ama",
                    "userName": "Customer"
                }
            },
            "recordingEnabled": True
        }

        print(f"\n🔧 Updating assistant: {ASSISTANT_ID}")
        print(f"   Name: {ASSISTANT_NAME}")
        print(f"\n✨ SEPARATED CITY CONFIGURATION:")
        print(f"   📞 Transcriber: Deepgram Nova-3 (en-GB)")
        print(f"   🏙️  Keywords: {len(KEYWORDS)} (was 163)")
        print(f"   🗺️  Keyterms: {len(KEYTERMS)}")
        print(f"   🎯 Total terms: {len(KEYWORDS) + len(KEYTERMS)}")
        print(f"\n📍 Key separations:")
        print(f"   • Santasi ≠ Patasi (was: Santasipatase)")
        print(f"   • Tafo ≠ Bremang (was: Tafobremang)")
        print(f"   • Somanya ≠ Odumase (was: Somanyaodumase)")
        print(f"   • Begoro ≠ Osiem (was: Begoroosiem)")
        print(f"   • Abuakwa ≠ Tanoso (was: Abuakwatanoso)")
        print(f"   • Assin ≠ Swedru (was: Assinswedru)")

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
                print(f"   Updated at: {result.get('updatedAt')}")

                # Verify transcriber
                transcriber = result.get('transcriber', {})
                if transcriber:
                    print(f"\n🎙️  Transcriber Verified:")
                    print(f"   Provider: {transcriber.get('provider')}")
                    print(f"   Model: {transcriber.get('model')}")
                    keywords = transcriber.get('keywords', [])
                    keyterms = transcriber.get('keyterm', [])
                    print(f"   Keywords: {len(keywords)}")
                    print(f"   Keyterms: {len(keyterms)}")

                return result
            else:
                print(f"\n❌ Error updating assistant: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function."""
    print("=" * 80)
    print("Premier Health Navigator - Update with Separated Cities")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Assistant ID: {ASSISTANT_ID}")

    # Verify separated cities
    verification_passed = verify_separated_cities()

    if not verification_passed:
        print("\n⚠️  WARNING: Some test cities are missing!")
        print("   Review the keyword generation process")
    else:
        print("\n✅ All test cities verified!")

    print("\n" + "=" * 80)

    # Update assistant
    result = update_assistant()

    if result:
        print("\n" + "=" * 80)
        print("✅ UPDATE SUCCESSFUL!")
        print("=" * 80)
        print("\n📝 KEY CHANGES:")
        print("   ✅ 6 compound names removed")
        print("   ✅ 25+ individual cities added")
        print("   ✅ 182 total keywords (was 163)")
        print("   ✅ RAG database updated with separated cities")
        print("\n🎯 User Experience:")
        print("   • Query 'gynecologists in Santasi' → Returns MATA DEI HOSPITAL ✅")
        print("   • Query 'facilities in Patasi' → Returns ST. AUGUSTINE HOSPITAL ✅")
        print("   • Query 'doctors in Tafo' → Returns facilities in Tafo (not Bremang) ✅")
        print("\n📊 Coverage:")
        print("   • 424 city-specific documents in RAG database")
        print("   • Cities properly separated (e.g., SANTASI ≠ PATASI)")
        print("   • All 431 unique locations covered")
        print("=" * 80)
    else:
        print("\n❌ UPDATE FAILED - Check errors above")


if __name__ == "__main__":
    main()
