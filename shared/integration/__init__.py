"""
Integration Package

This package contains integration capabilities for the KasaAI platform.
Temporarily simplified to resolve dataclass field ordering issues.
"""

from .integration_manager import IntegrationManager

# Core integrations that are likely to work
from .email import (
    EmailIntegration,
    EmailProvider,
    EmailAttachment,
    EmailTemplate,
    EmailDeliveryReport,
)

from .sms import (
    SMSIntegration,
    SMSProvider,
    SMSDeliveryReport,
)

# Basic provider classes without complex dataclass issues
try:
    from .n8n import (
        N8NIntegration,
        N8NConfig,
        N8NWorkflow,
        N8NExecution,
        N8NWebhook,
    )
except ImportError:
    pass

# Export the integration manager as the main interface
__all__ = [
    'IntegrationManager',
    'EmailIntegration',
    'EmailProvider', 
    'EmailAttachment',
    'EmailTemplate',
    'EmailDeliveryReport',
    'SMSIntegration',
    'SMSProvider',
    'SMSDeliveryReport',
]