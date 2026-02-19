#!/usr/bin/env python3
"""
Populate Integrations Database Script
Analyzes shared/integration files and populates the database with integration definitions
"""

import os
import sys
import json
import asyncio
from typing import List, Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.integration import (
    Integration, IntegrationProvider, IntegrationType, IntegrationStatus,
    IntegrationConfig, IntegrationCapability
)

def get_integration_definitions() -> List[Dict[str, Any]]:
    """
    Define all integrations based on analysis of shared/integration files.
    This replaces the hardcoded frontend array with a comprehensive database.
    """

    integrations = [
        # AI & Machine Learning
        {
            "name": "openai",
            "display_name": "OpenAI",
            "description": "GPT models for natural language processing and AI-powered conversations",
            "provider": IntegrationProvider.OPENAI,
            "integration_type": IntegrationType.LLM,
            "category": "ai_models",
            "website": "https://openai.com",
            "documentation_url": "https://platform.openai.com/docs",
            "icon": "🤖",
            "required_fields": ["api_key"],
            "capabilities": [
                {"name": "text_completion", "description": "Generate text completions", "method": "REST", "endpoint": "/v1/completions"},
                {"name": "chat_completion", "description": "Chat-based completions", "method": "REST", "endpoint": "/v1/chat/completions"},
                {"name": "embeddings", "description": "Generate text embeddings", "method": "REST", "endpoint": "/v1/embeddings"}
            ],
            "pricing_model": "usage_based",
            "compliance_certifications": ["SOC2", "GDPR"],
            "supported_operations": ["generate", "complete", "embed", "moderate"]
        },
        {
            "name": "anthropic",
            "display_name": "Anthropic",
            "description": "Claude AI models for advanced language understanding and reasoning",
            "provider": IntegrationProvider.ANTHROPIC,
            "integration_type": IntegrationType.LLM,
            "category": "ai_models",
            "website": "https://anthropic.com",
            "documentation_url": "https://docs.anthropic.com",
            "icon": "🧠",
            "required_fields": ["api_key"],
            "capabilities": [
                {"name": "messages", "description": "Send messages to Claude", "method": "REST", "endpoint": "/v1/messages"},
                {"name": "completions", "description": "Text completions", "method": "REST", "endpoint": "/v1/complete"}
            ],
            "pricing_model": "usage_based",
            "compliance_certifications": ["SOC2", "GDPR"],
            "supported_operations": ["message", "complete", "analyze"]
        },
        {
            "name": "elevenlabs",
            "display_name": "ElevenLabs",
            "description": "High-quality text-to-speech with natural voices and voice cloning",
            "provider": IntegrationProvider.ELEVENLABS,
            "integration_type": IntegrationType.TTS,
            "category": "voice_synthesis",
            "website": "https://elevenlabs.io",
            "documentation_url": "https://docs.elevenlabs.io",
            "icon": "🎙️",
            "required_fields": ["api_key"],
            "capabilities": [
                {"name": "text_to_speech", "description": "Convert text to speech", "method": "REST", "endpoint": "/v1/text-to-speech"},
                {"name": "voice_cloning", "description": "Clone voices", "method": "REST", "endpoint": "/v1/voices"},
                {"name": "speech_to_speech", "description": "Voice conversion", "method": "REST", "endpoint": "/v1/speech-to-speech"}
            ],
            "pricing_model": "usage_based",
            "supported_operations": ["synthesize", "clone", "convert"]
        },
        {
            "name": "deepgram",
            "display_name": "Deepgram",
            "description": "Real-time speech recognition and transcription with high accuracy",
            "provider": IntegrationProvider.DEEPGRAM,
            "integration_type": IntegrationType.STT,
            "category": "speech_recognition",
            "website": "https://deepgram.com",
            "documentation_url": "https://developers.deepgram.com",
            "icon": "🎤",
            "required_fields": ["api_key"],
            "capabilities": [
                {"name": "transcription", "description": "Transcribe audio files", "method": "REST", "endpoint": "/v1/listen"},
                {"name": "live_transcription", "description": "Real-time transcription", "method": "WebSocket", "endpoint": "/v1/listen"},
                {"name": "keyword_detection", "description": "Detect keywords in audio", "method": "REST", "endpoint": "/v1/listen"}
            ],
            "pricing_model": "usage_based",
            "supported_operations": ["transcribe", "stream", "detect"]
        },

        # Messaging & Communication
        {
            "name": "vonage_sms",
            "display_name": "Vonage SMS",
            "description": "Global SMS messaging service with reliable delivery and analytics",
            "provider": IntegrationProvider.VONAGE_SMS,
            "integration_type": IntegrationType.MESSAGING,
            "category": "sms",
            "website": "https://vonage.com",
            "documentation_url": "https://developer.nexmo.com",
            "icon": "📱",
            "required_fields": ["api_key", "api_secret"],
            "capabilities": [
                {"name": "send_sms", "description": "Send SMS messages", "method": "REST", "endpoint": "/v1/messages"},
                {"name": "delivery_receipt", "description": "Get delivery receipts", "method": "Webhook", "endpoint": "/webhooks/delivery-receipt"},
                {"name": "inbound_sms", "description": "Receive SMS messages", "method": "Webhook", "endpoint": "/webhooks/inbound-sms"}
            ],
            "pricing_model": "usage_based",
            "supported_operations": ["send", "receive", "track"]
        },
        {
            "name": "whatsapp_business",
            "display_name": "WhatsApp Business",
            "description": "WhatsApp Business API for customer messaging and automation",
            "provider": IntegrationProvider.WHATSAPP_BUSINESS,
            "integration_type": IntegrationType.MESSAGING,
            "category": "messaging",
            "website": "https://business.whatsapp.com",
            "documentation_url": "https://developers.facebook.com/docs/whatsapp",
            "icon": "💚",
            "required_fields": ["access_token", "phone_number_id"],
            "capabilities": [
                {"name": "send_message", "description": "Send messages", "method": "REST", "endpoint": "/messages"},
                {"name": "send_template", "description": "Send template messages", "method": "REST", "endpoint": "/messages"},
                {"name": "webhook", "description": "Receive messages", "method": "Webhook", "endpoint": "/webhooks"}
            ],
            "pricing_model": "usage_based",
            "compliance_certifications": ["GDPR", "CCPA"],
            "supported_operations": ["send", "receive", "template", "media"]
        },
        {
            "name": "telegram",
            "display_name": "Telegram",
            "description": "Telegram Bot API for messaging and automation",
            "provider": IntegrationProvider.TELEGRAM,
            "integration_type": IntegrationType.MESSAGING,
            "category": "messaging",
            "website": "https://telegram.org",
            "documentation_url": "https://core.telegram.org/bots/api",
            "icon": "✈️",
            "required_fields": ["bot_token"],
            "capabilities": [
                {"name": "send_message", "description": "Send messages", "method": "REST", "endpoint": "/sendMessage"},
                {"name": "send_photo", "description": "Send photos", "method": "REST", "endpoint": "/sendPhoto"},
                {"name": "get_updates", "description": "Get updates", "method": "REST", "endpoint": "/getUpdates"}
            ],
            "pricing_model": "free",
            "supported_operations": ["send", "receive", "media", "inline"]
        },
        {
            "name": "discord",
            "display_name": "Discord",
            "description": "Discord messaging and community platform integration",
            "provider": IntegrationProvider.DISCORD,
            "integration_type": IntegrationType.CHAT,
            "category": "messaging",
            "website": "https://discord.com",
            "documentation_url": "https://discord.com/developers/docs",
            "icon": "🎮",
            "required_fields": ["bot_token"],
            "capabilities": [
                {"name": "send_message", "description": "Send messages to channels", "method": "REST", "endpoint": "/channels/{channel.id}/messages"},
                {"name": "create_webhook", "description": "Create webhooks", "method": "REST", "endpoint": "/channels/{channel.id}/webhooks"},
                {"name": "manage_channels", "description": "Manage channels", "method": "REST", "endpoint": "/guilds/{guild.id}/channels"}
            ],
            "pricing_model": "free",
            "supported_operations": ["send", "receive", "webhook", "manage"]
        },

        # Email Services
        {
            "name": "sendgrid",
            "display_name": "SendGrid",
            "description": "Email delivery and marketing platform with high deliverability",
            "provider": IntegrationProvider.SENDGRID,
            "integration_type": IntegrationType.EMAIL,
            "category": "email",
            "website": "https://sendgrid.com",
            "documentation_url": "https://docs.sendgrid.com",
            "icon": "📧",
            "required_fields": ["api_key"],
            "capabilities": [
                {"name": "send_email", "description": "Send emails", "method": "REST", "endpoint": "/v3/mail/send"},
                {"name": "templates", "description": "Use email templates", "method": "REST", "endpoint": "/v3/templates"},
                {"name": "webhooks", "description": "Email events", "method": "Webhook", "endpoint": "/webhooks"}
            ],
            "pricing_model": "usage_based",
            "compliance_certifications": ["SOC2", "GDPR", "HIPAA"],
            "supported_operations": ["send", "template", "track", "analytics"]
        },
        {
            "name": "mailgun",
            "display_name": "Mailgun",
            "description": "Email automation service for developers with powerful APIs",
            "provider": IntegrationProvider.MAILGUN,
            "integration_type": IntegrationType.EMAIL,
            "category": "email",
            "website": "https://mailgun.com",
            "documentation_url": "https://documentation.mailgun.com",
            "icon": "🔫",
            "required_fields": ["api_key", "domain"],
            "capabilities": [
                {"name": "send_email", "description": "Send emails", "method": "REST", "endpoint": "/v3/{domain}/messages"},
                {"name": "email_validation", "description": "Validate email addresses", "method": "REST", "endpoint": "/v4/address/validate"},
                {"name": "webhooks", "description": "Email events", "method": "Webhook", "endpoint": "/webhooks"}
            ],
            "pricing_model": "usage_based",
            "supported_operations": ["send", "validate", "track", "route"]
        },

        # Payment & Financial
        {
            "name": "paystack",
            "display_name": "Paystack",
            "description": "African payment processing platform with comprehensive APIs",
            "provider": IntegrationProvider.PAYSTACK,
            "integration_type": IntegrationType.PAYMENT,
            "category": "payment",
            "website": "https://paystack.com",
            "documentation_url": "https://paystack.com/docs",
            "icon": "💳",
            "required_fields": ["secret_key"],
            "capabilities": [
                {"name": "initialize_transaction", "description": "Initialize payments", "method": "REST", "endpoint": "/transaction/initialize"},
                {"name": "verify_transaction", "description": "Verify payments", "method": "REST", "endpoint": "/transaction/verify"},
                {"name": "create_customer", "description": "Create customers", "method": "REST", "endpoint": "/customer"}
            ],
            "pricing_model": "transaction_fee",
            "compliance_certifications": ["PCI-DSS"],
            "supported_operations": ["pay", "verify", "refund", "subscription"]
        },
        {
            "name": "flutterwave",
            "display_name": "Flutterwave",
            "description": "Digital payment infrastructure for Africa with global reach",
            "provider": IntegrationProvider.FLUTTERWAVE,
            "integration_type": IntegrationType.PAYMENT,
            "category": "payment",
            "website": "https://flutterwave.com",
            "documentation_url": "https://developer.flutterwave.com",
            "icon": "🦋",
            "required_fields": ["secret_key"],
            "capabilities": [
                {"name": "standard_payment", "description": "Standard payments", "method": "REST", "endpoint": "/v3/payments"},
                {"name": "verify_transaction", "description": "Verify transactions", "method": "REST", "endpoint": "/v3/transactions"},
                {"name": "create_subaccount", "description": "Create subaccounts", "method": "REST", "endpoint": "/v3/subaccounts"}
            ],
            "pricing_model": "transaction_fee",
            "compliance_certifications": ["PCI-DSS"],
            "supported_operations": ["pay", "verify", "transfer", "subscription"]
        },
        {
            "name": "mtn_mobile_money",
            "display_name": "MTN Mobile Money",
            "description": "MTN Mobile Money payment integration for African markets",
            "provider": IntegrationProvider.MTN_MOBILE_MONEY,
            "integration_type": IntegrationType.BANKING,
            "category": "mobile_money",
            "website": "https://mtn.com",
            "documentation_url": "https://momodeveloper.mtn.com",
            "icon": "📱",
            "required_fields": ["subscription_key", "user_id", "api_key"],
            "capabilities": [
                {"name": "request_to_pay", "description": "Request payment", "method": "REST", "endpoint": "/collection/v1_0/requesttopay"},
                {"name": "get_transaction_status", "description": "Check status", "method": "REST", "endpoint": "/collection/v1_0/requesttopay"},
                {"name": "get_account_balance", "description": "Get balance", "method": "REST", "endpoint": "/collection/v1_0/account/balance"}
            ],
            "pricing_model": "transaction_fee",
            "data_residency": "africa",
            "supported_operations": ["pay", "check", "balance"]
        },
        {
            "name": "quickbooks",
            "display_name": "QuickBooks",
            "description": "Accounting and financial management integration",
            "provider": IntegrationProvider.QUICKBOOKS,
            "integration_type": IntegrationType.FINANCIAL,
            "category": "accounting",
            "website": "https://quickbooks.com",
            "documentation_url": "https://developer.intuit.com/app/developer/qbo/docs",
            "icon": "📊",
            "required_fields": ["client_id", "client_secret"],
            "capabilities": [
                {"name": "create_invoice", "description": "Create invoices", "method": "REST", "endpoint": "/v3/company/{realmId}/invoice"},
                {"name": "create_customer", "description": "Create customers", "method": "REST", "endpoint": "/v3/company/{realmId}/customer"},
                {"name": "get_reports", "description": "Generate reports", "method": "REST", "endpoint": "/v3/company/{realmId}/reports"}
            ],
            "pricing_model": "subscription",
            "compliance_certifications": ["SOC2", "GDPR"],
            "supported_operations": ["invoice", "payment", "report", "sync"]
        },

        # CRM & Sales
        {
            "name": "pipedrive",
            "display_name": "Pipedrive",
            "description": "Sales CRM and pipeline management with automation features",
            "provider": IntegrationProvider.PIPEDRIVE,
            "integration_type": IntegrationType.CRM,
            "category": "sales",
            "website": "https://pipedrive.com",
            "documentation_url": "https://developers.pipedrive.com",
            "icon": "🔄",
            "required_fields": ["api_token"],
            "capabilities": [
                {"name": "create_deal", "description": "Create deals", "method": "REST", "endpoint": "/v1/deals"},
                {"name": "create_person", "description": "Create contacts", "method": "REST", "endpoint": "/v1/persons"},
                {"name": "create_activity", "description": "Create activities", "method": "REST", "endpoint": "/v1/activities"}
            ],
            "pricing_model": "subscription",
            "compliance_certifications": ["GDPR", "SOC2"],
            "supported_operations": ["create", "update", "search", "sync"]
        },
        {
            "name": "freshsales",
            "display_name": "Freshsales",
            "description": "Customer relationship management platform with lead scoring",
            "provider": IntegrationProvider.FRESHSALES,
            "integration_type": IntegrationType.CRM,
            "category": "sales",
            "website": "https://freshsales.com",
            "documentation_url": "https://developers.freshworks.com/crm",
            "icon": "🌿",
            "required_fields": ["api_key"],
            "capabilities": [
                {"name": "create_contact", "description": "Create contacts", "method": "REST", "endpoint": "/api/contacts"},
                {"name": "create_deal", "description": "Create deals", "method": "REST", "endpoint": "/api/deals"},
                {"name": "create_task", "description": "Create tasks", "method": "REST", "endpoint": "/api/tasks"}
            ],
            "pricing_model": "subscription",
            "supported_operations": ["create", "update", "search", "report"]
        },
        {
            "name": "zoho_crm",
            "display_name": "Zoho CRM",
            "description": "Comprehensive customer management solution with automation",
            "provider": IntegrationProvider.ZOHO_CRM,
            "integration_type": IntegrationType.CRM,
            "category": "sales",
            "website": "https://zoho.com/crm",
            "documentation_url": "https://www.zoho.com/crm/developer",
            "icon": "🏢",
            "required_fields": ["client_id", "client_secret"],
            "capabilities": [
                {"name": "create_lead", "description": "Create leads", "method": "REST", "endpoint": "/crm/v2/Leads"},
                {"name": "create_contact", "description": "Create contacts", "method": "REST", "endpoint": "/crm/v2/Contacts"},
                {"name": "create_deal", "description": "Create deals", "method": "REST", "endpoint": "/crm/v2/Deals"}
            ],
            "pricing_model": "subscription",
            "supported_operations": ["create", "update", "search", "workflow"]
        },

        # Customer Support
        {
            "name": "freshdesk",
            "display_name": "Freshdesk",
            "description": "Customer service and support platform with multichannel support",
            "provider": IntegrationProvider.FRESHDESK,
            "integration_type": IntegrationType.SUPPORT,
            "category": "helpdesk",
            "website": "https://freshdesk.com",
            "documentation_url": "https://developers.freshdesk.com",
            "icon": "🎫",
            "required_fields": ["api_key"],
            "capabilities": [
                {"name": "create_ticket", "description": "Create support tickets", "method": "REST", "endpoint": "/api/v2/tickets"},
                {"name": "create_contact", "description": "Create contacts", "method": "REST", "endpoint": "/api/v2/contacts"},
                {"name": "add_note", "description": "Add ticket notes", "method": "REST", "endpoint": "/api/v2/tickets/{id}/notes"}
            ],
            "pricing_model": "subscription",
            "compliance_certifications": ["GDPR", "SOC2"],
            "supported_operations": ["create", "update", "search", "assign"]
        },
        {
            "name": "zendesk",
            "display_name": "Zendesk",
            "description": "Customer service and engagement platform with AI capabilities",
            "provider": IntegrationProvider.ZENDESK,
            "integration_type": IntegrationType.SUPPORT,
            "category": "helpdesk",
            "website": "https://zendesk.com",
            "documentation_url": "https://developer.zendesk.com",
            "icon": "🎯",
            "required_fields": ["api_token", "email"],
            "capabilities": [
                {"name": "create_ticket", "description": "Create tickets", "method": "REST", "endpoint": "/api/v2/tickets"},
                {"name": "create_user", "description": "Create users", "method": "REST", "endpoint": "/api/v2/users"},
                {"name": "search", "description": "Search tickets", "method": "REST", "endpoint": "/api/v2/search"}
            ],
            "pricing_model": "subscription",
            "compliance_certifications": ["GDPR", "SOC2", "HIPAA"],
            "supported_operations": ["create", "update", "search", "escalate"]
        },
        {
            "name": "intercom",
            "display_name": "Intercom",
            "description": "Customer messaging and engagement platform with live chat",
            "provider": IntegrationProvider.INTERCOM,
            "integration_type": IntegrationType.SUPPORT,
            "category": "messaging",
            "website": "https://intercom.com",
            "documentation_url": "https://developers.intercom.com",
            "icon": "💬",
            "required_fields": ["access_token"],
            "capabilities": [
                {"name": "create_contact", "description": "Create contacts", "method": "REST", "endpoint": "/contacts"},
                {"name": "send_message", "description": "Send messages", "method": "REST", "endpoint": "/messages"},
                {"name": "create_conversation", "description": "Create conversations", "method": "REST", "endpoint": "/conversations"}
            ],
            "pricing_model": "subscription",
            "supported_operations": ["message", "track", "segment", "automate"]
        },

        # Storage & Documentation
        {
            "name": "google_drive",
            "display_name": "Google Drive",
            "description": "Cloud storage and document management with collaboration features",
            "provider": IntegrationProvider.GOOGLE_DRIVE,
            "integration_type": IntegrationType.STORAGE,
            "category": "storage",
            "website": "https://drive.google.com",
            "documentation_url": "https://developers.google.com/drive",
            "icon": "💾",
            "required_fields": ["client_id", "client_secret"],
            "capabilities": [
                {"name": "upload_file", "description": "Upload files", "method": "REST", "endpoint": "/upload/drive/v3/files"},
                {"name": "create_folder", "description": "Create folders", "method": "REST", "endpoint": "/drive/v3/files"},
                {"name": "share_file", "description": "Share files", "method": "REST", "endpoint": "/drive/v3/files/{fileId}/permissions"}
            ],
            "pricing_model": "freemium",
            "compliance_certifications": ["GDPR", "SOC2"],
            "supported_operations": ["upload", "download", "share", "sync"]
        },
        {
            "name": "notion",
            "display_name": "Notion",
            "description": "All-in-one workspace for notes, docs, and collaboration",
            "provider": IntegrationProvider.NOTION,
            "integration_type": IntegrationType.STORAGE,
            "category": "productivity",
            "website": "https://notion.so",
            "documentation_url": "https://developers.notion.com",
            "icon": "📝",
            "required_fields": ["api_key"],
            "capabilities": [
                {"name": "create_page", "description": "Create pages", "method": "REST", "endpoint": "/v1/pages"},
                {"name": "update_page", "description": "Update pages", "method": "REST", "endpoint": "/v1/pages/{page_id}"},
                {"name": "query_database", "description": "Query databases", "method": "REST", "endpoint": "/v1/databases/{database_id}/query"}
            ],
            "pricing_model": "freemium",
            "supported_operations": ["create", "update", "query", "sync"]
        },

        # Analytics & Reporting
        {
            "name": "google_analytics",
            "display_name": "Google Analytics",
            "description": "Web analytics and reporting platform with advanced insights",
            "provider": IntegrationProvider.GOOGLE_ANALYTICS,
            "integration_type": IntegrationType.ANALYTICS,
            "category": "analytics",
            "website": "https://analytics.google.com",
            "documentation_url": "https://developers.google.com/analytics",
            "icon": "📈",
            "required_fields": ["client_id", "client_secret"],
            "capabilities": [
                {"name": "get_reports", "description": "Get analytics reports", "method": "REST", "endpoint": "/v4/reports:batchGet"},
                {"name": "create_custom_dimension", "description": "Create custom dimensions", "method": "REST", "endpoint": "/analytics/v3/management/accounts/{accountId}/webproperties/{webPropertyId}/customDimensions"},
                {"name": "real_time_reports", "description": "Real-time reports", "method": "REST", "endpoint": "/analytics/v3/data/realtime"}
            ],
            "pricing_model": "freemium",
            "compliance_certifications": ["GDPR"],
            "supported_operations": ["track", "report", "analyze", "segment"]
        },
        {
            "name": "mixpanel",
            "display_name": "Mixpanel",
            "description": "Product analytics for user engagement and behavior tracking",
            "provider": IntegrationProvider.MIXPANEL,
            "integration_type": IntegrationType.ANALYTICS,
            "category": "analytics",
            "website": "https://mixpanel.com",
            "documentation_url": "https://developer.mixpanel.com",
            "icon": "🎛️",
            "required_fields": ["project_token"],
            "capabilities": [
                {"name": "track_event", "description": "Track events", "method": "REST", "endpoint": "/track"},
                {"name": "create_profile", "description": "Create user profiles", "method": "REST", "endpoint": "/engage"},
                {"name": "export_events", "description": "Export events", "method": "REST", "endpoint": "/export"}
            ],
            "pricing_model": "usage_based",
            "supported_operations": ["track", "profile", "funnel", "cohort"]
        },

        # Workflow Automation
        {
            "name": "zapier",
            "display_name": "Zapier",
            "description": "Workflow automation between apps and services",
            "provider": IntegrationProvider.ZAPIER,
            "integration_type": IntegrationType.AUTOMATION,
            "category": "automation",
            "website": "https://zapier.com",
            "documentation_url": "https://zapier.com/developer",
            "icon": "⚡",
            "required_fields": ["api_key"],
            "capabilities": [
                {"name": "create_zap", "description": "Create automation workflows", "method": "REST", "endpoint": "/v1/zaps"},
                {"name": "trigger_zap", "description": "Trigger workflows", "method": "Webhook", "endpoint": "/hooks/catch"},
                {"name": "manage_webhooks", "description": "Manage webhooks", "method": "REST", "endpoint": "/v1/hooks"}
            ],
            "pricing_model": "subscription",
            "supported_operations": ["automate", "trigger", "webhook", "integrate"]
        },
        {
            "name": "n8n",
            "display_name": "n8n",
            "description": "Free and open workflow automation tool with visual editor",
            "provider": IntegrationProvider.N8N,
            "integration_type": IntegrationType.AUTOMATION,
            "category": "automation",
            "website": "https://n8n.io",
            "documentation_url": "https://docs.n8n.io",
            "icon": "🔗",
            "required_fields": ["api_key"],
            "capabilities": [
                {"name": "execute_workflow", "description": "Execute workflows", "method": "REST", "endpoint": "/webhook"},
                {"name": "manage_workflows", "description": "Manage workflows", "method": "REST", "endpoint": "/workflows"},
                {"name": "webhook_trigger", "description": "Webhook triggers", "method": "Webhook", "endpoint": "/webhook"}
            ],
            "pricing_model": "open_source",
            "supported_operations": ["execute", "schedule", "webhook", "monitor"]
        },
        {
            "name": "make",
            "display_name": "Make (Integromat)",
            "description": "Visual automation platform for connecting apps and services",
            "provider": IntegrationProvider.MAKE,
            "integration_type": IntegrationType.AUTOMATION,
            "category": "automation",
            "website": "https://make.com",
            "documentation_url": "https://www.make.com/en/api-documentation",
            "icon": "🔧",
            "required_fields": ["api_key"],
            "capabilities": [
                {"name": "run_scenario", "description": "Run automation scenarios", "method": "REST", "endpoint": "/v2/scenarios/{id}/run"},
                {"name": "create_webhook", "description": "Create webhooks", "method": "REST", "endpoint": "/v2/hooks"},
                {"name": "manage_scenarios", "description": "Manage scenarios", "method": "REST", "endpoint": "/v2/scenarios"}
            ],
            "pricing_model": "subscription",
            "supported_operations": ["automate", "schedule", "webhook", "monitor"]
        },

        # Productivity & Office Suites
        {
            "name": "microsoft_365",
            "display_name": "Microsoft 365",
            "description": "Complete Microsoft Office suite integration (Excel, Outlook, OneDrive, SharePoint)",
            "provider": IntegrationProvider.MICROSOFT_365,
            "integration_type": IntegrationType.PRODUCTIVITY,
            "category": "office_suite",
            "website": "https://microsoft.com/365",
            "documentation_url": "https://docs.microsoft.com/en-us/graph",
            "icon": "💼",
            "required_fields": ["client_id", "client_secret"],
            "capabilities": [
                {"name": "send_email", "description": "Send emails via Outlook", "method": "REST", "endpoint": "/v1.0/me/sendMail"},
                {"name": "create_document", "description": "Create documents", "method": "REST", "endpoint": "/v1.0/me/drive/root/children"},
                {"name": "calendar_events", "description": "Manage calendar", "method": "REST", "endpoint": "/v1.0/me/events"}
            ],
            "pricing_model": "subscription",
            "compliance_certifications": ["SOC2", "GDPR", "HIPAA"],
            "supported_operations": ["email", "document", "calendar", "collaboration"]
        },
        {
            "name": "google_workspace",
            "display_name": "Google Workspace",
            "description": "Google Workspace integration (Gmail, Docs, Sheets, Drive, Calendar)",
            "provider": IntegrationProvider.GOOGLE_WORKSPACE,
            "integration_type": IntegrationType.PRODUCTIVITY,
            "category": "office_suite",
            "website": "https://workspace.google.com",
            "documentation_url": "https://developers.google.com/workspace",
            "icon": "🌐",
            "required_fields": ["client_id", "client_secret"],
            "capabilities": [
                {"name": "send_email", "description": "Send emails via Gmail", "method": "REST", "endpoint": "/gmail/v1/users/me/messages/send"},
                {"name": "create_document", "description": "Create Google Docs", "method": "REST", "endpoint": "/docs/v1/documents"},
                {"name": "calendar_events", "description": "Manage Google Calendar", "method": "REST", "endpoint": "/calendar/v3/calendars/{calendarId}/events"}
            ],
            "pricing_model": "subscription",
            "compliance_certifications": ["SOC2", "GDPR"],
            "supported_operations": ["email", "document", "calendar", "collaboration"]
        },
        {
            "name": "confluence",
            "display_name": "Atlassian Confluence",
            "description": "Team collaboration and knowledge management platform",
            "provider": IntegrationProvider.CONFLUENCE,
            "integration_type": IntegrationType.PRODUCTIVITY,
            "category": "collaboration",
            "website": "https://atlassian.com/software/confluence",
            "documentation_url": "https://developer.atlassian.com/cloud/confluence",
            "icon": "📚",
            "required_fields": ["api_token", "email"],
            "capabilities": [
                {"name": "create_page", "description": "Create pages", "method": "REST", "endpoint": "/rest/api/content"},
                {"name": "update_page", "description": "Update pages", "method": "REST", "endpoint": "/rest/api/content/{id}"},
                {"name": "search_content", "description": "Search content", "method": "REST", "endpoint": "/rest/api/search"}
            ],
            "pricing_model": "subscription",
            "supported_operations": ["create", "update", "search", "collaborate"]
        },

        # Healthcare Systems
        {
            "name": "epic_ehr",
            "display_name": "Epic EHR",
            "description": "Epic Electronic Health Records system integration",
            "provider": IntegrationProvider.EPIC_EHR,
            "integration_type": IntegrationType.HEALTHCARE,
            "category": "ehr",
            "website": "https://epic.com",
            "documentation_url": "https://fhir.epic.com",
            "icon": "🏥",
            "required_fields": ["client_id", "client_secret"],
            "capabilities": [
                {"name": "get_patient", "description": "Get patient information", "method": "REST", "endpoint": "/api/FHIR/R4/Patient"},
                {"name": "create_appointment", "description": "Create appointments", "method": "REST", "endpoint": "/api/FHIR/R4/Appointment"},
                {"name": "get_observations", "description": "Get medical observations", "method": "REST", "endpoint": "/api/FHIR/R4/Observation"}
            ],
            "pricing_model": "enterprise",
            "compliance_certifications": ["HIPAA", "HL7"],
            "data_residency": "configurable",
            "supported_operations": ["read", "write", "search", "sync"]
        },
        {
            "name": "cerner_ehr",
            "display_name": "Cerner EHR",
            "description": "Cerner Electronic Health Records system integration",
            "provider": IntegrationProvider.CERNER_EHR,
            "integration_type": IntegrationType.HEALTHCARE,
            "category": "ehr",
            "website": "https://cerner.com",
            "documentation_url": "https://fhir.cerner.com",
            "icon": "⚕️",
            "required_fields": ["client_id", "client_secret"],
            "capabilities": [
                {"name": "get_patient", "description": "Get patient data", "method": "REST", "endpoint": "/v1/Patient"},
                {"name": "get_encounters", "description": "Get patient encounters", "method": "REST", "endpoint": "/v1/Encounter"},
                {"name": "get_conditions", "description": "Get patient conditions", "method": "REST", "endpoint": "/v1/Condition"}
            ],
            "pricing_model": "enterprise",
            "compliance_certifications": ["HIPAA", "HL7"],
            "supported_operations": ["read", "search", "monitor"]
        },

        # Enterprise Systems
        {
            "name": "servicenow",
            "display_name": "ServiceNow",
            "description": "IT service management and business process automation platform",
            "provider": IntegrationProvider.SERVICENOW,
            "integration_type": IntegrationType.ENTERPRISE,
            "category": "itsm",
            "website": "https://servicenow.com",
            "documentation_url": "https://developer.servicenow.com",
            "icon": "🛠️",
            "required_fields": ["username", "password", "instance_url"],
            "capabilities": [
                {"name": "create_incident", "description": "Create incidents", "method": "REST", "endpoint": "/api/now/table/incident"},
                {"name": "create_change_request", "description": "Create change requests", "method": "REST", "endpoint": "/api/now/table/change_request"},
                {"name": "get_cmdb", "description": "Access CMDB", "method": "REST", "endpoint": "/api/now/table/cmdb_ci"}
            ],
            "pricing_model": "subscription",
            "compliance_certifications": ["SOC2", "ISO27001"],
            "supported_operations": ["create", "update", "workflow", "report"]
        },
        {
            "name": "odoo",
            "display_name": "Odoo ERP",
            "description": "Open source enterprise resource planning system",
            "provider": IntegrationProvider.ODOO,
            "integration_type": IntegrationType.ERP,
            "category": "erp",
            "website": "https://odoo.com",
            "documentation_url": "https://www.odoo.com/documentation",
            "icon": "🏭",
            "required_fields": ["api_key", "database"],
            "capabilities": [
                {"name": "create_partner", "description": "Create business partners", "method": "XML-RPC", "endpoint": "/xmlrpc/2/object"},
                {"name": "create_sale_order", "description": "Create sales orders", "method": "XML-RPC", "endpoint": "/xmlrpc/2/object"},
                {"name": "inventory_management", "description": "Manage inventory", "method": "XML-RPC", "endpoint": "/xmlrpc/2/object"}
            ],
            "pricing_model": "open_source",
            "supported_operations": ["create", "update", "search", "report"]
        },
        {
            "name": "microsoft_dynamics",
            "display_name": "Microsoft Dynamics",
            "description": "Microsoft Dynamics CRM and ERP platform",
            "provider": IntegrationProvider.MICROSOFT_DYNAMICS,
            "integration_type": IntegrationType.ENTERPRISE,
            "category": "crm_erp",
            "website": "https://dynamics.microsoft.com",
            "documentation_url": "https://docs.microsoft.com/en-us/dynamics365",
            "icon": "🔷",
            "required_fields": ["client_id", "client_secret"],
            "capabilities": [
                {"name": "create_lead", "description": "Create leads", "method": "REST", "endpoint": "/api/data/v9.2/leads"},
                {"name": "create_account", "description": "Create accounts", "method": "REST", "endpoint": "/api/data/v9.2/accounts"},
                {"name": "create_opportunity", "description": "Create opportunities", "method": "REST", "endpoint": "/api/data/v9.2/opportunities"}
            ],
            "pricing_model": "subscription",
            "compliance_certifications": ["SOC2", "GDPR"],
            "supported_operations": ["create", "update", "search", "workflow"]
        },

        # Monitoring & Analytics
        {
            "name": "grafana",
            "display_name": "Grafana",
            "description": "Monitoring, visualization, and alerting platform",
            "provider": IntegrationProvider.GRAFANA,
            "integration_type": IntegrationType.MONITORING,
            "category": "monitoring",
            "website": "https://grafana.com",
            "documentation_url": "https://grafana.com/docs/grafana/latest/developers/http_api",
            "icon": "📊",
            "required_fields": ["api_key"],
            "capabilities": [
                {"name": "create_dashboard", "description": "Create dashboards", "method": "REST", "endpoint": "/api/dashboards/db"},
                {"name": "create_alert", "description": "Create alerts", "method": "REST", "endpoint": "/api/alerts"},
                {"name": "query_metrics", "description": "Query metrics", "method": "REST", "endpoint": "/api/datasources/proxy"}
            ],
            "pricing_model": "open_source",
            "supported_operations": ["monitor", "alert", "visualize", "query"]
        },
        {
            "name": "prometheus",
            "display_name": "Prometheus",
            "description": "Open source monitoring and alerting toolkit",
            "provider": IntegrationProvider.PROMETHEUS,
            "integration_type": IntegrationType.MONITORING,
            "category": "monitoring",
            "website": "https://prometheus.io",
            "documentation_url": "https://prometheus.io/docs/prometheus/latest/querying/api",
            "icon": "🔥",
            "required_fields": ["endpoint_url"],
            "capabilities": [
                {"name": "query_metrics", "description": "Query metrics", "method": "REST", "endpoint": "/api/v1/query"},
                {"name": "query_range", "description": "Query metric ranges", "method": "REST", "endpoint": "/api/v1/query_range"},
                {"name": "get_targets", "description": "Get monitoring targets", "method": "REST", "endpoint": "/api/v1/targets"}
            ],
            "pricing_model": "open_source",
            "supported_operations": ["query", "monitor", "alert", "scrape"]
        },

        # Banking & Financial Systems
        {
            "name": "ghana_interbank",
            "display_name": "Ghana Interbank Payment",
            "description": "Ghana banking and interbank payment system integration",
            "provider": IntegrationProvider.GHANA_INTERBANK,
            "integration_type": IntegrationType.BANKING,
            "category": "banking",
            "website": "https://bog.gov.gh",
            "documentation_url": "https://bog.gov.gh/payment-systems",
            "icon": "🏛️",
            "required_fields": ["institution_code", "api_key"],
            "capabilities": [
                {"name": "interbank_transfer", "description": "Interbank transfers", "method": "REST", "endpoint": "/api/v1/transfer"},
                {"name": "balance_inquiry", "description": "Account balance inquiry", "method": "REST", "endpoint": "/api/v1/balance"},
                {"name": "transaction_status", "description": "Transaction status", "method": "REST", "endpoint": "/api/v1/status"}
            ],
            "pricing_model": "transaction_fee",
            "data_residency": "ghana",
            "compliance_certifications": ["BOG"],
            "supported_operations": ["transfer", "inquiry", "status"]
        },
        {
            "name": "bank_ussd",
            "display_name": "Bank USSD Services",
            "description": "USSD-based banking services integration",
            "provider": IntegrationProvider.BANK_USSD,
            "integration_type": IntegrationType.BANKING,
            "category": "ussd",
            "website": "https://example.com",
            "documentation_url": "https://example.com/docs",
            "icon": "💰",
            "required_fields": ["ussd_code", "provider_id"],
            "capabilities": [
                {"name": "balance_check", "description": "Check account balance", "method": "USSD", "endpoint": "*123#"},
                {"name": "money_transfer", "description": "Transfer money", "method": "USSD", "endpoint": "*123*1#"},
                {"name": "airtime_purchase", "description": "Buy airtime", "method": "USSD", "endpoint": "*123*2#"}
            ],
            "pricing_model": "transaction_fee",
            "supported_operations": ["balance", "transfer", "purchase"]
        },

        # Other Integrations
        {
            "name": "web_chat",
            "display_name": "Web Chat Widget",
            "description": "Embeddable web chat widget for websites",
            "provider": IntegrationProvider.WEB_CHAT,
            "integration_type": IntegrationType.CHAT,
            "category": "messaging",
            "website": "https://kasaai.com",
            "documentation_url": "https://docs.kasaai.com/web-chat",
            "icon": "💬",
            "required_fields": ["widget_id"],
            "capabilities": [
                {"name": "embed_widget", "description": "Embed chat widget", "method": "JavaScript", "endpoint": "/widget.js"},
                {"name": "send_message", "description": "Send messages", "method": "WebSocket", "endpoint": "/chat"},
                {"name": "file_upload", "description": "Upload files", "method": "REST", "endpoint": "/upload"}
            ],
            "pricing_model": "usage_based",
            "supported_operations": ["chat", "upload", "customize"]
        },
        {
            "name": "mongodb",
            "display_name": "MongoDB",
            "description": "NoSQL database integration for document storage and retrieval",
            "provider": IntegrationProvider.MONGODB,
            "integration_type": IntegrationType.DATABASE,
            "category": "database",
            "website": "https://mongodb.com",
            "documentation_url": "https://docs.mongodb.com",
            "icon": "🍃",
            "required_fields": ["connection_string"],
            "capabilities": [
                {"name": "insert_document", "description": "Insert documents", "method": "Driver", "endpoint": "collection.insertOne"},
                {"name": "find_documents", "description": "Find documents", "method": "Driver", "endpoint": "collection.find"},
                {"name": "update_document", "description": "Update documents", "method": "Driver", "endpoint": "collection.updateOne"}
            ],
            "pricing_model": "usage_based",
            "supported_operations": ["create", "read", "update", "delete", "aggregate"]
        },
        {
            "name": "findhelp",
            "display_name": "FindHelp",
            "description": "Social services and community resource discovery platform",
            "provider": IntegrationProvider.FINDHELP,
            "integration_type": IntegrationType.API,
            "category": "social_services",
            "website": "https://findhelp.org",
            "documentation_url": "https://developers.findhelp.org",
            "icon": "🤝",
            "required_fields": ["api_key"],
            "capabilities": [
                {"name": "search_resources", "description": "Search community resources", "method": "REST", "endpoint": "/api/v1/resources"},
                {"name": "get_organizations", "description": "Get organizations", "method": "REST", "endpoint": "/api/v1/organizations"},
                {"name": "create_referral", "description": "Create referrals", "method": "REST", "endpoint": "/api/v1/referrals"}
            ],
            "pricing_model": "subscription",
            "supported_operations": ["search", "refer", "track"]
        }
    ]

    return integrations

async def create_integration_from_definition(definition: Dict[str, Any]) -> Integration:
    """Create an Integration model from definition dictionary."""

    # Create capabilities
    capabilities = []
    for cap_def in definition.get("capabilities", []):
        capability = IntegrationCapability(
            name=cap_def["name"],
            description=cap_def["description"],
            method=cap_def["method"],
            endpoint=cap_def.get("endpoint"),
            parameters=cap_def.get("parameters"),
            response_format=cap_def.get("response_format"),
            rate_limit=cap_def.get("rate_limit")
        )
        capabilities.append(capability)

    # Create basic config
    config = IntegrationConfig()

    integration = Integration(
        name=definition["name"],
        display_name=definition["display_name"],
        description=definition["description"],
        provider=definition["provider"],
        integration_type=definition["integration_type"],
        category=definition["category"],
        website=definition.get("website"),
        documentation_url=definition.get("documentation_url"),
        icon=definition.get("icon"),
        config=config,
        required_fields=definition.get("required_fields", []),
        capabilities=capabilities,
        supported_operations=definition.get("supported_operations", []),
        pricing_model=definition.get("pricing_model"),
        compliance_certifications=definition.get("compliance_certifications", []),
        data_residency=definition.get("data_residency"),
        free_tier_limits=definition.get("free_tier_limits"),
        usage_limits=definition.get("usage_limits")
    )

    return integration

async def populate_integrations():
    """Populate the database with integration definitions."""

    try:
        # Note: In a real implementation, you would connect to MongoDB here
        # For now, we'll simulate the database operations

        definitions = get_integration_definitions()
        integrations = []

        print(f"Creating {len(definitions)} integrations...")

        for definition in definitions:
            integration = await create_integration_from_definition(definition)
            integrations.append(integration)
            print(f"Created integration: {integration.display_name}")

        # In a real implementation, you would save to database here
        # Example:
        # collection = get_mongodb_collection("integrations")
        # for integration in integrations:
        #     await collection.insert_one(integration.dict())

        # For now, save to JSON file for testing
        integrations_data = [integration.dict() for integration in integrations]

        output_file = "/opt/kasaai/apps/core_backend/integrations_seed.json"
        with open(output_file, 'w') as f:
            json.dump(integrations_data, f, indent=2, default=str)

        print(f"\nSuccessfully created {len(integrations)} integrations!")
        print(f"Data saved to: {output_file}")

        # Print summary by type
        type_counts = {}
        for integration in integrations:
            int_type = integration.integration_type
            type_counts[int_type] = type_counts.get(int_type, 0) + 1

        print("\nIntegrations by type:")
        for int_type, count in sorted(type_counts.items()):
            print(f"  {int_type}: {count}")

        return integrations

    except Exception as e:
        print(f"Error populating integrations: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(populate_integrations())