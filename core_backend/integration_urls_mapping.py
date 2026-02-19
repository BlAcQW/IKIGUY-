"""
Integration API Reference and Documentation URLs
Comprehensive mapping of all 44 integrations to their official documentation
"""

INTEGRATION_URLS = {
    # Communication
    "chat": {
        "api_reference_url": "https://docs.pusher.com/channels/library_auth_reference/rest-api",
        "documentation_url": "https://pusher.com/docs/"
    },
    "email": {
        "api_reference_url": "https://developers.google.com/gmail/api/reference",
        "documentation_url": "https://developers.google.com/gmail/api/guides"
    },
    "sms": {
        "api_reference_url": "https://www.twilio.com/docs/sms/api",
        "documentation_url": "https://www.twilio.com/docs/sms"
    },
    "sms_providers": {
        "api_reference_url": "https://docs.telnyx.com/api/v2/messaging",
        "documentation_url": "https://developers.telnyx.com/docs/messaging"
    },
    "telegram": {
        "api_reference_url": "https://core.telegram.org/bots/api",
        "documentation_url": "https://core.telegram.org/bots"
    },
    "web_chat": {
        "api_reference_url": "https://developers.intercom.com/intercom-api-reference/reference",
        "documentation_url": "https://developers.intercom.com/building-apps"
    },
    "whatsapp": {
        "api_reference_url": "https://developers.facebook.com/docs/whatsapp/business-management-api",
        "documentation_url": "https://developers.facebook.com/docs/whatsapp"
    },
    "whatsapp_business": {
        "api_reference_url": "https://developers.facebook.com/docs/whatsapp/cloud-api/reference",
        "documentation_url": "https://developers.facebook.com/docs/whatsapp/cloud-api"
    },
    "vapi": {
        "api_reference_url": "https://docs.vapi.ai/api-reference",
        "documentation_url": "https://docs.vapi.ai/quickstart/introduction"
    },
    "discord": {
        "api_reference_url": "https://discord.com/developers/docs/reference",
        "documentation_url": "https://discord.com/developers/docs/intro"
    },

    # Payment Systems
    "bank_ussd": {
        "api_reference_url": "https://developer.mtn.com/docs/mobile-money/reference/ussd-api",
        "documentation_url": "https://developer.mtn.com/docs/mobile-money"
    },
    "ghana_interbank": {
        "api_reference_url": "https://developer.ghipss.net/api-reference",
        "documentation_url": "https://developer.ghipss.net/docs"
    },
    "local_payment_systems": {
        "api_reference_url": "https://docs.paystack.com/reference",
        "documentation_url": "https://paystack.com/docs"
    },
    "mtn_mobile_money": {
        "api_reference_url": "https://momodeveloper.mtn.com/api-documentation",
        "documentation_url": "https://momodeveloper.mtn.com/"
    },

    # Business Tools
    "freshdesk": {
        "api_reference_url": "https://developers.freshdesk.com/api/",
        "documentation_url": "https://developers.freshdesk.com/"
    },
    "freshsales": {
        "api_reference_url": "https://developers.freshsales.io/api/",
        "documentation_url": "https://developers.freshsales.io/"
    },
    "intercom": {
        "api_reference_url": "https://developers.intercom.com/intercom-api-reference/reference",
        "documentation_url": "https://developers.intercom.com/"
    },
    "mixpanel": {
        "api_reference_url": "https://developer.mixpanel.com/reference",
        "documentation_url": "https://developer.mixpanel.com/docs"
    },
    "pipedrive": {
        "api_reference_url": "https://developers.pipedrive.com/docs/api/v1",
        "documentation_url": "https://developers.pipedrive.com/"
    },
    "servicenow": {
        "api_reference_url": "https://docs.servicenow.com/bundle/tokyo-api-reference/page/build/applications/reference/api-rest/c_TableAPI.html",
        "documentation_url": "https://developer.servicenow.com/"
    },
    "zendesk": {
        "api_reference_url": "https://developer.zendesk.com/api-reference/",
        "documentation_url": "https://developer.zendesk.com/"
    },
    "zoho": {
        "api_reference_url": "https://www.zoho.com/crm/developer/docs/api/v2/",
        "documentation_url": "https://www.zoho.com/developer/"
    },
    "findhelp": {
        "api_reference_url": "https://developers.findhelp.org/api/reference",
        "documentation_url": "https://developers.findhelp.org/"
    },
    "grafana": {
        "api_reference_url": "https://grafana.com/docs/grafana/latest/developers/http_api/",
        "documentation_url": "https://grafana.com/docs/grafana/latest/developers/"
    },
    "prometheus": {
        "api_reference_url": "https://prometheus.io/docs/prometheus/latest/querying/api/",
        "documentation_url": "https://prometheus.io/docs/"
    },

    # Productivity & Cloud
    "google_analytics": {
        "api_reference_url": "https://developers.google.com/analytics/devguides/reporting/ga4/reference",
        "documentation_url": "https://developers.google.com/analytics"
    },
    "google_drive": {
        "api_reference_url": "https://developers.google.com/drive/api/reference/rest/v3",
        "documentation_url": "https://developers.google.com/drive/api/guides"
    },
    "google_maps_clinics": {
        "api_reference_url": "https://developers.google.com/maps/documentation/places/web-service/reference",
        "documentation_url": "https://developers.google.com/maps/documentation/places/web-service"
    },
    "google_workspace": {
        "api_reference_url": "https://developers.google.com/workspace/reference",
        "documentation_url": "https://developers.google.com/workspace"
    },
    "microsoft_365": {
        "api_reference_url": "https://docs.microsoft.com/en-us/graph/api/overview",
        "documentation_url": "https://docs.microsoft.com/en-us/graph/"
    },
    "microsoft_dynamics": {
        "api_reference_url": "https://docs.microsoft.com/en-us/dynamics365/customer-engagement/web-api/",
        "documentation_url": "https://docs.microsoft.com/en-us/dynamics365/"
    },
    "notion": {
        "api_reference_url": "https://developers.notion.com/reference",
        "documentation_url": "https://developers.notion.com/"
    },

    # ERP & Accounting
    "financial_systems": {
        "api_reference_url": "https://docs.xero.com/xero-accounting-api",
        "documentation_url": "https://developer.xero.com/"
    },
    "odoo": {
        "api_reference_url": "https://www.odoo.com/documentation/16.0/developer/reference/external_api.html",
        "documentation_url": "https://www.odoo.com/documentation/16.0/developer/"
    },
    "quickbooks": {
        "api_reference_url": "https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities",
        "documentation_url": "https://developer.intuit.com/app/developer/qbo/docs"
    },
    "mongodb": {
        "api_reference_url": "https://docs.mongodb.com/manual/reference/",
        "documentation_url": "https://docs.mongodb.com/"
    },

    # Automation Platforms
    "make": {
        "api_reference_url": "https://www.make.com/en/api-documentation",
        "documentation_url": "https://www.make.com/en/help"
    },
    "n8n": {
        "api_reference_url": "https://docs.n8n.io/api/",
        "documentation_url": "https://docs.n8n.io/"
    },
    "zapier": {
        "api_reference_url": "https://platform.zapier.com/reference",
        "documentation_url": "https://platform.zapier.com/docs"
    },

    # Payment Gateways
    "flutterwave": {
        "api_reference_url": "https://developer.flutterwave.com/reference",
        "documentation_url": "https://developer.flutterwave.com/docs"
    },
    "paystack": {
        "api_reference_url": "https://paystack.com/docs/api/",
        "documentation_url": "https://paystack.com/docs/"
    },

    # Specialized Services
    "confluence": {
        "api_reference_url": "https://developer.atlassian.com/cloud/confluence/rest/v2/",
        "documentation_url": "https://developer.atlassian.com/cloud/confluence/"
    },
    "discord": {
        "api_reference_url": "https://discord.com/developers/docs/reference",
        "documentation_url": "https://discord.com/developers/docs/"
    },
    "healthcare_systems": {
        "api_reference_url": "https://www.hl7.org/fhir/http.html",
        "documentation_url": "https://www.hl7.org/fhir/"
    },
    "integration_manager": {
        "api_reference_url": "https://docs.mulesoft.com/runtime-manager/runtime-manager-api",
        "documentation_url": "https://docs.mulesoft.com/runtime-manager/"
    },
    "types": {
        "api_reference_url": "https://json-schema.org/specification.html",
        "documentation_url": "https://json-schema.org/learn/"
    }
}