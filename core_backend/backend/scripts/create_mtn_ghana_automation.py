#!/usr/bin/env python3
"""
Script to create MTN Ghana helpdesk automation implementation.
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

def create_mtn_ghana_automation():
    """Create MTN Ghana automation implementation."""
    try:
        # Get the automation configs collection
        automation_configs_collection = get_collection("automation_configs")

        if automation_configs_collection is None:
            print("❌ Failed to connect to MongoDB")
            return None

        # Get the base template
        template = create_helpdesk_automation_template()

        # Create MTN Ghana specific automation config
        mtn_automation = {
            "automationName": "MTN Ghana Customer Support Helpdesk",
            "templateId": template["id"],
            "status": "DRAFT",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
            "userId": "system",  # System-created automation

            # Company Information
            "companyInfo": {
                "name": "MTN Ghana",
                "description": "Leading telecommunications company in Ghana providing voice, data, and digital services",
                "url": "https://mtn.com.gh/",
                "industry": "Telecommunications",
                "country": "Ghana",
                "services": [
                    "Mobile voice and data services",
                    "Internet and broadband",
                    "Mobile money (MoMo)",
                    "Digital services",
                    "Enterprise solutions"
                ],
                "supportHours": "24/7 customer support",
                "contactInfo": {
                    "customerService": "100",
                    "whatsapp": "+233554300000",
                    "website": "https://mtn.com.gh/",
                    "app": "MyMTN App"
                }
            },

            # VAPI Agent Configuration
            "vapiAgent": {
                "assistantId": "",  # To be set during deployment
                "phoneNumberId": "",  # To be set during deployment
                "systemPrompt": template["vapi_config"]["model"]["system_message"],
                "voiceSettings": {
                    "voiceId": "burt",
                    "model": "nova-2",
                    "maxDuration": 600,
                    "stability": 0.5,
                    "similarityBoost": 0.7,
                    "optimizeStreamingLatency": 3
                },
                "tools": template["tools"],
                "firstMessage": template["vapi_config"]["first_message"],
                "endCallMessage": template["vapi_config"]["end_call_message"],
                "transferPhoneNumber": template["vapi_config"]["transfer_phone_number"],
                "maxDurationSeconds": template["vapi_config"]["max_duration_seconds"],
                "silenceTimeoutSeconds": template["vapi_config"]["silence_timeout_seconds"],
                "responseDelaySeconds": template["vapi_config"]["response_delay_seconds"],
                "numWordsToInterruptAssistant": template["vapi_config"]["num_words_to_interrupt_assistant"],
                "maxInterruptions": template["vapi_config"]["max_interruptions"],
                "interruptionThreshold": template["vapi_config"]["interruption_threshold"],
                "backgroundSound": template["vapi_config"]["background_sound"],
                "backgroundDenoisingEnabled": template["vapi_config"]["background_denoising_enabled"]
            },

            # N8N Workflow Configuration
            "n8nWorkflow": {
                "workflowId": "",  # To be set during deployment
                "workflowName": "MTN Ghana Helpdesk Automation",
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
                    "settings": template["integrations"]["freshdesk"]
                },
                "resend": {
                    "enabled": True,
                    "apiKeyRequired": True,
                    "settings": template["integrations"]["resend"]
                },
                "tavily": {
                    "enabled": True,
                    "apiKeyRequired": True,
                    "settings": template["integrations"]["tavily"]
                },
                "calendly": {
                    "enabled": True,
                    "apiKeyRequired": True,
                    "settings": template["integrations"]["calendly"]
                },
                "supabase": {
                    "enabled": True,
                    "settings": template["integrations"]["supabase"]
                }
            },

            # Custom Tools Configuration
            "customTools": {
                "enabled": True,
                "tools": template["tools"]
            },

            # Demo Settings
            "demoSettings": {
                "enableDemo": True,
                "demoUrl": "",  # To be set during deployment
                "demoTitle": "MTN Ghana Customer Support Demo",
                "demoDescription": "Experience MTN Ghana's AI-powered customer support system",
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
                "retentionDays": 90
            },

            # Template metadata
            "templateName": template["template_name"],
            "templateVersion": template["version"],
            "category": template["category"],
            "industry": template["industry_name"],
            "tags": template["tags"] + ["mtn-ghana", "live-implementation"],
            "configParameters": template["config_parameters"],
            "deploymentRequirements": template["deployment_requirements"],
            "usageEstimates": template["usage_estimates"],
            "successMetrics": template["success_metrics"]
        }

        # Check if MTN Ghana automation already exists
        existing = automation_configs_collection.find_one({
            "automationName": mtn_automation["automationName"]
        })

        if existing:
            print(f"MTN Ghana automation already exists. Updating...")
            result = automation_configs_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": {**mtn_automation, "updatedAt": datetime.utcnow()}}
            )
            print(f"Updated automation. Modified count: {result.modified_count}")
            automation_id = str(existing["_id"])
        else:
            print(f"Creating new MTN Ghana automation...")
            result = automation_configs_collection.insert_one(mtn_automation)
            if result and result.inserted_id:
                print(f"Inserted automation with ID: {result.inserted_id}")
                automation_id = str(result.inserted_id)
            else:
                print("❌ Failed to insert automation - no result returned")
                print(f"Result: {result}")
                return None

        # Verify the automation was added/updated
        saved_automation = automation_configs_collection.find_one({"_id": ObjectId(automation_id)})
        if saved_automation:
            print(f"✅ MTN Ghana automation successfully saved:")
            print(f"   - ID: {automation_id}")
            print(f"   - Name: {saved_automation['automationName']}")
            print(f"   - Company: {saved_automation['companyInfo']['name']}")
            print(f"   - Status: {saved_automation['status']}")
            print(f"   - Template: {saved_automation['templateName']}")
            print(f"   - Category: {saved_automation['category']}")
            print(f"   - Integrations: {len(saved_automation['integrations'])}")
            print(f"   - Tools: {len(saved_automation['customTools']['tools'])}")
            print(f"   - Created: {saved_automation['createdAt']}")
        else:
            print("❌ Failed to save MTN Ghana automation")

        return automation_id

    except Exception as e:
        print(f"Error creating MTN Ghana automation: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    automation_id = create_mtn_ghana_automation()
    if automation_id:
        print(f"\n🎉 MTN Ghana automation created successfully with ID: {automation_id}")
        print(f"Access it at: https://api.ailabsafrica.com/automation-configs/{automation_id}")
    else:
        print("❌ Failed to create MTN Ghana automation")
        sys.exit(1)