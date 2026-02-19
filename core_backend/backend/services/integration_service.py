"""Consolidated Integration Service for all 44 integrations with MCP support."""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import importlib
from pathlib import Path
from .n8n_service import N8NService
from .chat_service import chat_service
from .email_service import email_service
from .freshdesk_service import freshdesk_service
from .freshdesk_consolidated_service import freshdesk_consolidated_service
from .vonage_consolidated_service import vonage_consolidated_service
from .resend_consolidated_service import resend_consolidated_service
from .tavily_consolidated_service import tavily_consolidated_service
from .calendly_consolidated_service import calendly_consolidated_service
from .firecrawl_consolidated_service import firecrawl_consolidated_service
from .brave_consolidated_service import brave_consolidated_service
from .hubspot_consolidated_service import hubspot_consolidated_service
from .telegram_consolidated_service import telegram_consolidated_service
# from .discord_consolidated_service import discord_consolidated_service
# from .zendesk_consolidated_service import zendesk_consolidated_service
from .generic_consolidated_service import service_factory, get_consolidated_service
from .paystack_service import paystack_service
from .stripe_service import stripe_service

# Import unified VAPI service from shared location
import sys
sys.path.append('/opt/kasaai/apps/shared')
from integration.vapi import vapi_service

logger = logging.getLogger(__name__)

# Import MCP mappings
try:
    from ...integration_mcp_mapping import INTEGRATION_MCP_ENDPOINTS, MCP_INTEGRATION_STATS
    from ...integration_urls_mapping import INTEGRATION_URLS
except ImportError:
    logger.warning("MCP and URL mappings not available")
    INTEGRATION_MCP_ENDPOINTS = {}
    INTEGRATION_URLS = {}
    MCP_INTEGRATION_STATS = {}


class IntegrationCategory(str, Enum):
    """Integration categories matching our catalog."""
    COMMUNICATION = "communication"
    PAYMENT_SYSTEMS = "payment_systems"
    BUSINESS_TOOLS = "business_tools"
    PRODUCTIVITY_CLOUD = "productivity_cloud"
    ERP_ACCOUNTING = "erp_accounting"
    AUTOMATION_PLATFORMS = "automation_platforms"
    PAYMENT_GATEWAYS = "payment_gateways"
    SPECIALIZED_SERVICES = "specialized_services"


class IntegrationService:
    """Consolidated service for all 44 integrations with MCP and API support."""

    # Complete integration mapping by category
    INTEGRATION_CATALOG = {
        IntegrationCategory.COMMUNICATION: [
            "chat", "email", "sms", "sms_providers", "telegram",
            "web_chat", "whatsapp", "whatsapp_business", "discord", "vapi"
        ],
        IntegrationCategory.PAYMENT_SYSTEMS: [
            "bank_ussd", "ghana_interbank", "local_payment_systems",
            "mtn_mobile_money"
        ],
        IntegrationCategory.BUSINESS_TOOLS: [
            "freshdesk", "freshsales", "hubspot", "intercom", "mixpanel", "pipedrive",
            "servicenow", "zendesk", "zoho", "findhelp", "grafana", "prometheus"
        ],
        IntegrationCategory.PRODUCTIVITY_CLOUD: [
            "google_analytics", "google_drive", "google_maps_clinics",
            "google_workspace", "microsoft_365", "microsoft_dynamics", "notion"
        ],
        IntegrationCategory.ERP_ACCOUNTING: [
            "financial_systems", "odoo", "quickbooks", "mongodb"
        ],
        IntegrationCategory.AUTOMATION_PLATFORMS: [
            "make", "n8n", "zapier"
        ],
        IntegrationCategory.PAYMENT_GATEWAYS: [
            "flutterwave", "paystack", "stripe"
        ],
        IntegrationCategory.SPECIALIZED_SERVICES: [
            "confluence", "healthcare_systems", "integration_manager", "types", "firecrawl", "brave"
        ]
    }

    def __init__(self):
        """Initialize the consolidated integration service."""
        self.integrations = {}
        self.integration_metadata = {}
        self.mcp_endpoints = INTEGRATION_MCP_ENDPOINTS
        self.integration_urls = INTEGRATION_URLS
        self.dedicated_services = {}
        self._initialize_dedicated_services()
        self._load_all_integrations()

    def _initialize_dedicated_services(self):
        """Initialize dedicated services safely."""
        try:
            self.dedicated_services["chat"] = chat_service
            self.dedicated_services["email"] = email_service
            self.dedicated_services["freshdesk"] = freshdesk_service
            self.dedicated_services["freshdesk_consolidated"] = freshdesk_consolidated_service
            self.dedicated_services["vonage_consolidated"] = vonage_consolidated_service
            self.dedicated_services["resend_consolidated"] = resend_consolidated_service
            self.dedicated_services["tavily_consolidated"] = tavily_consolidated_service
            self.dedicated_services["calendly_consolidated"] = calendly_consolidated_service
            self.dedicated_services["firecrawl_consolidated"] = firecrawl_consolidated_service
            self.dedicated_services["brave_consolidated"] = brave_consolidated_service
            self.dedicated_services["hubspot_consolidated"] = hubspot_consolidated_service
            self.dedicated_services["telegram_consolidated"] = telegram_consolidated_service
            # self.dedicated_services["discord_consolidated"] = discord_consolidated_service
            # self.dedicated_services["zendesk_consolidated"] = zendesk_consolidated_service
            self.dedicated_services["paystack"] = paystack_service
            self.dedicated_services["vapi"] = vapi_service
            self.dedicated_services["stripe"] = stripe_service
            self.dedicated_services["n8n"] = N8NService()

            # Auto-generate consolidated services for remaining integrations
            self._auto_generate_missing_services()

            logger.info(f"Initialized {len(self.dedicated_services)} dedicated services")
        except Exception as e:
            logger.error(f"Error initializing dedicated services: {e}")
            # Fallback - initialize empty services dict
            self.dedicated_services = {}

    def _auto_generate_missing_services(self):
        """Auto-generate consolidated services for integrations that don't have manual implementations."""
        try:
            # Get all available integrations from shared directory
            available_integrations = service_factory.get_available_integrations()

            # List of integrations that already have manual consolidated services
            manual_services = {
                'brave', 'calendly', 'firecrawl', 'freshdesk', 'hubspot',
                'resend', 'supabase', 'tavily', 'vonage', 'vapi', 'telegram',
                'discord', 'zendesk'
            }

            # Skip utility/special modules
            skip_modules = {'types', 'integration_manager', 'supabase_admin'}

            auto_generated = 0
            for integration_name in available_integrations:
                if integration_name not in manual_services and integration_name not in skip_modules:
                    try:
                        service = get_consolidated_service(integration_name)
                        if service:
                            self.dedicated_services[f"{integration_name}_consolidated"] = service
                            auto_generated += 1
                            logger.debug(f"Auto-generated service for {integration_name}")
                    except Exception as e:
                        logger.warning(f"Failed to auto-generate service for {integration_name}: {e}")

            logger.info(f"Auto-generated {auto_generated} consolidated services")

        except Exception as e:
            logger.error(f"Error in auto-generation of services: {e}")

    def _load_all_integrations(self):
        """Load all 44 integrations dynamically with error handling."""
        total_loaded = 0

        for category, integration_names in self.INTEGRATION_CATALOG.items():
            category_loaded = 0

            for integration_name in integration_names:
                try:
                    integration_instance = self._load_integration(integration_name)
                    if integration_instance:
                        self.integrations[integration_name] = integration_instance
                        self._set_integration_metadata(integration_name, category)
                        total_loaded += 1
                        category_loaded += 1

                except Exception as e:
                    logger.warning(f"Failed to load integration '{integration_name}': {e}")

            logger.info(f"Loaded {category_loaded}/{len(integration_names)} integrations for {category.value}")

        logger.info(f"Successfully loaded {total_loaded}/44 integrations total")

    def _load_integration(self, integration_name: str) -> Optional[Any]:
        """Load a specific integration class from shared package."""
        try:
            # Import the integration module
            module_path = f"apps.shared.integration.{integration_name}"
            module = importlib.import_module(module_path)

            # Find the main integration class (various naming patterns)
            possible_class_names = [
                f"{integration_name.title().replace('_', '')}Service",
                f"{integration_name.title().replace('_', '')}Integration",
                f"{integration_name.title().replace('_', '')}",
                f"{integration_name.upper().replace('_', '')}Service",
                # Specific known patterns
                "BankUSSDService", "GhanaInterbankService", "PaystackService",
                "FlutterwaveService", "MTNMobileMoneyService", "LocalPaymentSystemsService",
                "EHRIntegrationManager", "FindHelpIntegration", "GoogleMapsClinicsIntegration",
                "N8NIntegration", "IntegrationManager"
            ]

            for class_name in possible_class_names:
                if hasattr(module, class_name):
                    integration_class = getattr(module, class_name)

                    # Special handling for integrations that require config
                    if integration_name == 'email':
                        import os
                        minimal_email_config = {
                            "provider": "smtp",
                            "smtp_host": os.getenv("EMAIL_SMTP_HOST", "localhost"),
                            "smtp_port": int(os.getenv("EMAIL_SMTP_PORT", "587")),
                            "smtp_username": os.getenv("EMAIL_SMTP_USERNAME", "noreply@ailabsafrica.com"),
                            "smtp_password": os.getenv("EMAIL_SMTP_PASSWORD", "noreply_secure_2025"),
                            "use_tls": True,
                            "use_ssl": False,
                            "from_email": os.getenv("EMAIL_FROM", "noreply@ailabsafrica.com"),
                            "from_name": os.getenv("EMAIL_FROM_NAME", "AI Labs Africa")
                        }
                        return integration_class(minimal_email_config)
                    elif integration_name == 'sms':
                        import os
                        minimal_sms_config = {
                            "provider": "vonage_sms",
                            "vonage_api_key": os.getenv("VONAGE_API_KEY", "4109fdf7"),
                            "vonage_api_secret": os.getenv("VONAGE_API_SECRET", "mativo3saMI3cAWG"),
                            "from_number": os.getenv("SMS_FROM_NUMBER", "AI Labs Africa")
                        }
                        return integration_class(minimal_sms_config)
                    elif integration_name == 'google_workspace':
                        import os
                        from apps.shared.integration.google_workspace import (
                            GoogleWorkspaceConfig, GoogleCalendarConfig,
                            GoogleSheetsConfig, GoogleDocsConfig
                        )
                        # Configure with service account credentials
                        credentials_path = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH")
                        credentials_json_str = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_JSON")
                        credentials_json = None
                        if credentials_json_str:
                            import json
                            credentials_json = json.loads(credentials_json_str)

                        config = GoogleWorkspaceConfig(
                            calendar=GoogleCalendarConfig(
                                calendar_id="ailabsafrica@gmail.com",
                                credentials_path=credentials_path,
                                credentials_json=credentials_json
                            ),
                            service_account_email=os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL")
                        )
                        return integration_class(config)
                    elif integration_name == 'google_drive':
                        import os
                        from apps.shared.integration.google_drive import GoogleDriveConfig
                        config = GoogleDriveConfig(
                            service_account_file=os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH")
                        )
                        return integration_class(config)
                    else:
                        return integration_class()

            # If no specific class found, try to find any class that looks like an integration
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    attr_name not in ['BaseModel', 'Enum', 'datetime'] and
                    not attr_name.startswith('_')):

                    # Special handling for integrations that require config
                    if integration_name == 'email':
                        import os
                        minimal_email_config = {
                            "provider": "smtp",
                            "smtp_host": os.getenv("EMAIL_SMTP_HOST", "localhost"),
                            "smtp_port": int(os.getenv("EMAIL_SMTP_PORT", "587")),
                            "smtp_username": os.getenv("EMAIL_SMTP_USERNAME", "noreply@ailabsafrica.com"),
                            "smtp_password": os.getenv("EMAIL_SMTP_PASSWORD", "noreply_secure_2025"),
                            "use_tls": True,
                            "use_ssl": False,
                            "from_email": os.getenv("EMAIL_FROM", "noreply@ailabsafrica.com"),
                            "from_name": os.getenv("EMAIL_FROM_NAME", "AI Labs Africa")
                        }
                        return attr(minimal_email_config)
                    elif integration_name == 'sms':
                        import os
                        minimal_sms_config = {
                            "provider": "vonage_sms",
                            "vonage_api_key": os.getenv("VONAGE_API_KEY", "4109fdf7"),
                            "vonage_api_secret": os.getenv("VONAGE_API_SECRET", "mativo3saMI3cAWG"),
                            "from_number": os.getenv("SMS_FROM_NUMBER", "AI Labs Africa")
                        }
                        return attr(minimal_sms_config)
                    elif integration_name == 'ai_powered_features':
                        import os
                        minimal_ai_config = {
                            "sentiment_threshold": 0.6,
                            "engagement_threshold": 0.5,
                            "objection_confidence_threshold": 0.7,
                            "routing_confidence_threshold": 0.8,
                            "sentiment_model": os.getenv("AI_SENTIMENT_MODEL", "cardiffnlp/twitter-roberta-base-sentiment-latest"),
                            "summarization_model": os.getenv("AI_SUMMARIZATION_MODEL", "facebook/bart-large-cnn"),
                            "objection_model": os.getenv("AI_OBJECTION_MODEL", "microsoft/DialoGPT-medium")
                        }
                        return attr(minimal_ai_config)
                    elif integration_name == 'google_workspace':
                        import os
                        from apps.shared.integration.google_workspace import (
                            GoogleWorkspaceConfig, GoogleCalendarConfig,
                            GoogleSheetsConfig, GoogleDocsConfig
                        )
                        # Configure with service account credentials
                        credentials_path = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH")
                        credentials_json_str = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_JSON")
                        credentials_json = None
                        if credentials_json_str:
                            import json
                            credentials_json = json.loads(credentials_json_str)

                        config = GoogleWorkspaceConfig(
                            calendar=GoogleCalendarConfig(
                                calendar_id="ailabsafrica@gmail.com",
                                credentials_path=credentials_path,
                                credentials_json=credentials_json
                            ),
                            service_account_email=os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL")
                        )
                        return attr(config)
                    elif integration_name == 'google_drive':
                        import os
                        from apps.shared.integration.google_drive import GoogleDriveConfig
                        config = GoogleDriveConfig(
                            service_account_file=os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH")
                        )
                        return attr(config)
                    else:
                        return attr()

            logger.warning(f"No integration class found in module {module_path}")
            return None

        except ImportError as e:
            logger.warning(f"Module not found for integration '{integration_name}': {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading integration '{integration_name}': {e}")
            return None

    def _set_integration_metadata(self, integration_name: str, category: IntegrationCategory):
        """Set metadata for an integration including MCP and URL info."""
        self.integration_metadata[integration_name] = {
            "category": category.value,
            "loaded": True,
            "has_mcp": integration_name in self.mcp_endpoints and self.mcp_endpoints[integration_name].get("mcp_available", False),
            "mcp_server": self.mcp_endpoints.get(integration_name, {}).get("mcp_server_name"),
            "mcp_endpoint": self.mcp_endpoints.get(integration_name, {}).get("mcp_endpoint_url"),
            "api_reference_url": self.integration_urls.get(integration_name, {}).get("api_reference_url"),
            "documentation_url": self.integration_urls.get(integration_name, {}).get("documentation_url"),
            "provider": getattr(self.integrations.get(integration_name), 'provider', integration_name)
        }

    async def test_integration(self, integration_name: str, config: Dict[str, Any], tenant_id: str = "default") -> Dict[str, Any]:
        """
        Test an integration with given configuration.

        Args:
            integration_name: Name of integration to test
            config: Configuration parameters for the integration
            tenant_id: Tenant identifier for the test

        Returns:
            Test result with success status and details
        """
        try:
            # Check if we have a dedicated service for this integration
            if integration_name in self.dedicated_services:
                dedicated_service = self.dedicated_services[integration_name]
                if hasattr(dedicated_service, 'test_connection'):
                    result = await dedicated_service.test_connection()
                    return {
                        "success": result.get("success", False),
                        "message": result.get("message", f"{integration_name} test completed"),
                        "integration_name": integration_name,
                        "service_type": "dedicated",
                        "result_details": result
                    }
                else:
                    return {
                        "success": True,
                        "message": f"Dedicated {integration_name} service loaded successfully",
                        "integration_name": integration_name,
                        "service_type": "dedicated",
                        "capabilities": getattr(dedicated_service, 'get_capabilities', lambda: {})(),
                        "test_note": "Service loaded but no test_connection method available"
                    }

            if integration_name not in self.integrations:
                return {
                    "success": False,
                    "message": f"Integration '{integration_name}' not loaded or not supported",
                    "integration_name": integration_name,
                    "tenant_id": tenant_id,
                    "available_integrations": list(self.integrations.keys())[:10],
                    "dedicated_services": list(self.dedicated_services.keys())
                }

            integration = self.integrations[integration_name]
            metadata = self.integration_metadata.get(integration_name, {})

            # Perform basic connection test
            if hasattr(integration, 'test_connection'):
                if asyncio.iscoroutinefunction(integration.test_connection):
                    result = await integration.test_connection(config)
                else:
                    result = integration.test_connection(config)
            elif hasattr(integration, 'health_check'):
                if asyncio.iscoroutinefunction(integration.health_check):
                    result = await integration.health_check(config)
                else:
                    result = integration.health_check(config)
            else:
                # Fallback to basic initialization test
                result = True

            return {
                "success": bool(result),
                "message": f"Integration '{integration_name}' test {'passed' if result else 'failed'}",
                "integration_name": integration_name,
                "tenant_id": tenant_id,
                "category": metadata.get("category"),
                "provider": metadata.get("provider"),
                "has_mcp": metadata.get("has_mcp", False),
                "mcp_server": metadata.get("mcp_server"),
                "result_details": result if isinstance(result, dict) else None
            }

        except Exception as e:
            logger.error(f"Integration test failed for {integration_name}: {e}")
            return {
                "success": False,
                "message": f"Integration test error: {str(e)}",
                "integration_name": integration_name,
                "tenant_id": tenant_id,
                "error": str(e)
            }

    async def execute_integration(self, integration_name: str, action: str, config: Dict[str, Any], data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute an integration action.

        Args:
            integration_name: Name of integration
            action: Action to perform
            config: Integration configuration
            data: Data for the action

        Returns:
            Execution result
        """
        try:
            # Check if we have a dedicated service for this integration
            if integration_name in self.dedicated_services:
                dedicated_service = self.dedicated_services[integration_name]
                # Try to execute the action on the dedicated service
                if hasattr(dedicated_service, action):
                    method = getattr(dedicated_service, action)
                    if asyncio.iscoroutinefunction(method):
                        if data:
                            result = await method(config, **data)
                        else:
                            result = await method(config)
                    else:
                        if data:
                            result = method(config, **data)
                        else:
                            result = method(config)

                    return {
                        "success": True,
                        "result": result,
                        "integration_name": integration_name,
                        "action": action,
                        "service_type": "dedicated"
                    }
                else:
                    capabilities = getattr(dedicated_service, 'get_capabilities', lambda: {})().get('capabilities', [])
                    return {
                        "success": False,
                        "message": f"Action '{action}' not supported by {integration_name} service",
                        "available_actions": capabilities,
                        "service_type": "dedicated"
                    }

            if integration_name not in self.integrations:
                return {
                    "success": False,
                    "message": f"Integration '{integration_name}' not loaded or not supported",
                    "available_integrations": list(self.integrations.keys())[:10],
                    "dedicated_services": list(self.dedicated_services.keys())
                }

            integration = self.integrations[integration_name]
            metadata = self.integration_metadata.get(integration_name, {})

            # Execute the requested action
            if hasattr(integration, action):
                method = getattr(integration, action)

                # Handle both sync and async methods
                if asyncio.iscoroutinefunction(method):
                    if data:
                        result = await method(config, data)
                    else:
                        result = await method(config)
                else:
                    if data:
                        result = method(config, data)
                    else:
                        result = method(config)

                return {
                    "success": True,
                    "result": result,
                    "integration_name": integration_name,
                    "action": action,
                    "category": metadata.get("category"),
                    "provider": metadata.get("provider")
                }
            else:
                # Get available methods for better error message
                available_methods = [method for method in dir(integration) if not method.startswith('_')]

                return {
                    "success": False,
                    "message": f"Action '{action}' not supported for integration '{integration_name}'",
                    "available_actions": available_methods[:10]  # Show first 10 methods
                }

        except Exception as e:
            logger.error(f"Integration execution failed: {e}")
            return {
                "success": False,
                "message": f"Integration execution error: {str(e)}",
                "integration_name": integration_name,
                "action": action,
                "error": str(e)
            }

    def get_integration(self, integration_name: str) -> Optional[Any]:
        """Get a specific integration instance."""
        return self.integrations.get(integration_name)

    def list_integrations(self, category: Optional[str] = None, has_mcp: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        List all available integrations with filtering options.

        Args:
            category: Filter by category
            has_mcp: Filter by MCP availability

        Returns:
            List of integration info dictionaries
        """
        results = []

        for name, metadata in self.integration_metadata.items():
            # Apply filters
            if category and metadata.get("category") != category:
                continue
            if has_mcp is not None and metadata.get("has_mcp") != has_mcp:
                continue

            results.append({
                "name": name,
                "category": metadata.get("category"),
                "provider": metadata.get("provider"),
                "loaded": name in self.integrations,
                "has_mcp": metadata.get("has_mcp", False),
                "mcp_server": metadata.get("mcp_server"),
                "api_reference_url": metadata.get("api_reference_url"),
                "documentation_url": metadata.get("documentation_url")
            })

        return sorted(results, key=lambda x: (x["category"], x["name"]))

    def get_integration_capabilities(self, integration_name: str) -> Dict[str, Any]:
        """Get integration capabilities and available methods."""
        try:
            # Check dedicated services first
            if integration_name in self.dedicated_services:
                dedicated_service = self.dedicated_services[integration_name]
                if hasattr(dedicated_service, 'get_capabilities'):
                    return dedicated_service.get_capabilities()
                else:
                    # Extract capabilities from service methods
                    methods = [method for method in dir(dedicated_service)
                             if not method.startswith('_') and callable(getattr(dedicated_service, method))]
                    return {
                        "service": integration_name,
                        "service_type": "dedicated",
                        "capabilities": methods,
                        "configured": True,
                        "methods_available": len(methods)
                    }

            if integration_name not in self.integrations:
                # Check if it's in our catalog but not loaded
                for category, integrations in self.INTEGRATION_CATALOG.items():
                    if integration_name in integrations:
                        return {
                            "service": integration_name,
                            "service_type": "catalog",
                            "category": category.value,
                            "configured": False,
                            "status": "not_loaded",
                            "message": f"Integration '{integration_name}' is available but not loaded"
                        }

                return {
                    "service": integration_name,
                    "configured": False,
                    "status": "not_found",
                    "message": f"Integration '{integration_name}' not found",
                    "available_integrations": list(self.dedicated_services.keys()) + list(self.integrations.keys()),
                    "dedicated_services": list(self.dedicated_services.keys())
                }

        except Exception as e:
            logger.error(f"Error getting capabilities for {integration_name}: {e}")
            return {
                "service": integration_name,
                "error": str(e),
                "configured": False
            }

        integration = self.integrations[integration_name]
        metadata = self.integration_metadata.get(integration_name, {})

        # Get all public methods
        methods = [method for method in dir(integration) if not method.startswith('_')]

        # Categorize methods
        test_methods = [m for m in methods if 'test' in m.lower() or 'health' in m.lower()]
        action_methods = [m for m in methods if m not in test_methods and callable(getattr(integration, m))]

        return {
            "integration_name": integration_name,
            "category": metadata.get("category"),
            "provider": metadata.get("provider"),
            "has_mcp": metadata.get("has_mcp", False),
            "mcp_server": metadata.get("mcp_server"),
            "mcp_endpoint": metadata.get("mcp_endpoint"),
            "api_reference_url": metadata.get("api_reference_url"),
            "documentation_url": metadata.get("documentation_url"),
            "test_methods": test_methods,
            "action_methods": action_methods,
            "total_methods": len(methods)
        }

    def get_supported_integrations(self) -> Dict[str, Any]:
        """Get comprehensive integration statistics and categorization."""
        stats = {
            "total_integrations": len(self.integrations),
            "total_possible": 44,
            "loaded_percentage": round((len(self.integrations) / 44) * 100, 1),
            "by_category": {},
            "mcp_enabled": len([name for name, meta in self.integration_metadata.items() if meta.get("has_mcp")]),
            "mcp_servers": list(set([
                meta.get("mcp_server") for meta in self.integration_metadata.values()
                if meta.get("mcp_server")
            ])),
            "loaded_integrations": list(self.integrations.keys()),
            "failed_integrations": []
        }

        # Count by category
        for category in IntegrationCategory:
            expected = len(self.INTEGRATION_CATALOG[category])
            loaded = len([
                name for name in self.INTEGRATION_CATALOG[category]
                if name in self.integrations
            ])
            stats["by_category"][category.value] = {
                "loaded": loaded,
                "expected": expected,
                "percentage": round((loaded / expected) * 100, 1) if expected > 0 else 0,
                "integrations": [
                    name for name in self.INTEGRATION_CATALOG[category]
                    if name in self.integrations
                ]
            }

        # Find failed integrations
        all_expected = []
        for integrations in self.INTEGRATION_CATALOG.values():
            all_expected.extend(integrations)
        stats["failed_integrations"] = [
            name for name in all_expected if name not in self.integrations
        ]

        return stats

    def get_mcp_integrations(self) -> Dict[str, Any]:
        """Get all MCP-enabled integrations."""
        mcp_integrations = {}

        for name, metadata in self.integration_metadata.items():
            if metadata.get("has_mcp"):
                mcp_integrations[name] = {
                    "mcp_server": metadata.get("mcp_server"),
                    "mcp_endpoint": metadata.get("mcp_endpoint"),
                    "category": metadata.get("category"),
                    "loaded": name in self.integrations
                }

        return {
            "mcp_integrations": mcp_integrations,
            "total_mcp_enabled": len(mcp_integrations),
            "mcp_coverage_stats": MCP_INTEGRATION_STATS
        }

    async def get_n8n_workflows(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get N8N workflows using consolidated N8NService."""
        n8n_service = N8NService()
        return await n8n_service.list_workflows(config or {})

    async def create_n8n_workflow_from_template(self, template_id: int, campaign_data: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create N8N workflow from template using consolidated N8NService."""
        n8n_service = N8NService()
        return await n8n_service.create_workflow_from_template(template_id, campaign_data)

    async def trigger_n8n_workflow(self, workflow_id: str, data: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger N8N workflow execution using consolidated N8NService."""
        n8n_service = N8NService()
        return await n8n_service.trigger_workflow(workflow_id, data)

    async def get_n8n_workflow_status(self, workflow_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get N8N workflow status using consolidated N8NService."""
        n8n_service = N8NService()
        return await n8n_service.get_workflow_status(workflow_id)


    async def search_n8n_templates(self, query: str, category: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Search N8N templates using consolidated N8NService."""
        n8n_service = N8NService()
        return await n8n_service.search_workflow_template(query, category=category or "")


# Global consolidated integration service instance
integration_service = IntegrationService()