"""
Generic Consolidated Service Factory.
Creates consolidated service wrappers for any shared integration automatically.
"""

import asyncio
import logging
import os
import sys
import importlib
from typing import Dict, Any, Optional, List, Union, Type
from datetime import datetime
from pathlib import Path

# Add shared integration path
sys.path.append('/opt/kasaai/apps/shared')

logger = logging.getLogger(__name__)


class GenericConsolidatedServiceFactory:
    """Factory to create consolidated service wrappers for any shared integration."""

    @staticmethod
    def create_service(integration_name: str, config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a consolidated service wrapper for any integration.

        Args:
            integration_name: Name of the integration module (e.g., 'telegram', 'discord')
            config: Optional configuration dictionary

        Returns:
            Wrapped integration service instance
        """
        try:
            # Import the integration module
            module = importlib.import_module(f'integration.{integration_name}')

            # Find the main integration class (usually ends with 'Integration')
            integration_class = None
            config_class = None

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if hasattr(attr, '__name__'):
                    if attr_name.endswith('Integration') and attr_name != 'Integration':
                        integration_class = attr
                    elif attr_name.endswith('Config') and attr_name != 'Config':
                        config_class = attr

            if not integration_class:
                logger.warning(f"No integration class found for {integration_name}")
                return None

            # Create wrapper class dynamically
            class GenericServiceWrapper(integration_class):
                def __init__(self, wrapper_config: Optional[Dict[str, Any]] = None):
                    if config_class and wrapper_config:
                        # Use config class if available
                        integration_config = config_class(**wrapper_config)
                        super().__init__(integration_config)
                    elif wrapper_config:
                        # Pass config dict directly
                        super().__init__(wrapper_config)
                    else:
                        # Try to initialize with environment variables or defaults
                        try:
                            if config_class:
                                # Try to create empty config
                                integration_config = config_class()
                                super().__init__(integration_config)
                            else:
                                # Try empty initialization
                                super().__init__()
                        except Exception as e:
                            # Fallback - initialize with minimal config
                            logger.warning(f"Using minimal config for {integration_name}: {e}")

                            # Special handling for integrations that require config
                            if integration_name == 'email':
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
                                super().__init__(minimal_email_config)
                            elif integration_name == 'sms':
                                minimal_sms_config = {
                                    "default_provider": "vonage_sms",
                                    "providers": {
                                        "vonage": {
                                            "api_key": os.getenv("VONAGE_API_KEY", "4109fdf7"),
                                            "api_secret": os.getenv("VONAGE_API_SECRET", "mativo3saMI3cAWG")
                                        }
                                    },
                                    "from_number": os.getenv("SMS_FROM_NUMBER", "+12075218001")
                                }
                                super().__init__(minimal_sms_config)
                            elif integration_name == 'ai_powered_features':
                                minimal_ai_config = {
                                    "sentiment_threshold": 0.6,
                                    "engagement_threshold": 0.5,
                                    "objection_confidence_threshold": 0.7,
                                    "routing_confidence_threshold": 0.8,
                                    "sentiment_model": os.getenv("AI_SENTIMENT_MODEL", "cardiffnlp/twitter-roberta-base-sentiment-latest"),
                                    "summarization_model": os.getenv("AI_SUMMARIZATION_MODEL", "facebook/bart-large-cnn"),
                                    "objection_model": os.getenv("AI_OBJECTION_MODEL", "microsoft/DialoGPT-medium")
                                }
                                super().__init__(minimal_ai_config)
                            else:
                                super().__init__({})

                async def get_service_info(self) -> Dict[str, Any]:
                    """Get generic service information."""
                    return {
                        "service_name": f"{integration_name.title()} Consolidated",
                        "service_type": f"{integration_name.title()} Integration",
                        "version": "1.0.0",
                        "integration_name": integration_name,
                        "auto_generated": True,
                        "generated_at": datetime.utcnow().isoformat()
                    }

                async def test_connection_safe(self) -> Dict[str, Any]:
                    """Safe connection test with error handling."""
                    try:
                        if hasattr(self, 'test_connection'):
                            return await self.test_connection()
                        else:
                            return {"success": True, "message": "No test_connection method available"}
                    except Exception as e:
                        return {"success": False, "error": str(e)}

            # Create and return the wrapped instance
            return GenericServiceWrapper(config)

        except ImportError as e:
            logger.error(f"Could not import integration '{integration_name}': {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating service for '{integration_name}': {e}")
            return None

    @staticmethod
    def get_available_integrations() -> List[str]:
        """Get list of available integrations in shared directory."""
        shared_dir = Path('/opt/kasaai/apps/shared/integration')
        integrations = []

        for file_path in shared_dir.glob("*.py"):
            if not file_path.name.startswith('__') and not file_path.name.endswith('_mcp_server.py'):
                integration_name = file_path.stem
                if integration_name not in ['types', 'integration_manager', 'supabase_admin']:  # Skip utility modules
                    integrations.append(integration_name)

        return sorted(integrations)

    @staticmethod
    def create_all_services() -> Dict[str, Any]:
        """Create consolidated services for all available integrations."""
        services = {}
        available_integrations = GenericConsolidatedServiceFactory.get_available_integrations()

        for integration_name in available_integrations:
            try:
                service = GenericConsolidatedServiceFactory.create_service(integration_name)
                if service:
                    services[f"{integration_name}_consolidated"] = service
                    logger.info(f"Created consolidated service for {integration_name}")
                else:
                    logger.warning(f"Failed to create service for {integration_name}")
            except Exception as e:
                logger.error(f"Error creating service for {integration_name}: {e}")

        logger.info(f"Created {len(services)} consolidated services")
        return services


# Convenience function for getting a specific service
def get_consolidated_service(integration_name: str, config: Optional[Dict[str, Any]] = None) -> Any:
    """Get a consolidated service for a specific integration."""
    return GenericConsolidatedServiceFactory.create_service(integration_name, config)


# Create factory instance
service_factory = GenericConsolidatedServiceFactory()