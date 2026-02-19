"""Billing Routes for StudyFlow"""

import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../..")))

from apps.shared.routes.billing_routes import create_billing_router
from apps.shared.services.billing_service import get_billing_service
from app.core.auth import get_current_user

# Create billing router with StudyFlow's auth dependency
billing_router = create_billing_router(get_current_user, get_billing_service)

# Export as router so it can be included in API
router = billing_router
router.prefix = "/organizations/{organization_id}"
router.tags = ["Billing"]
