"""
Integration Category Service for managing integration categories.
"""

import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from ..mongo import get_database


class IntegrationCategory(BaseModel):
    """Integration category model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Name of the integration category")
    description: str = Field(..., description="Description of the integration category")
    icon: str = Field(default="Puzzle")
    color: str = Field(default="#6366f1")
    total_integrations: int = Field(default=0, description="Number of integrations in this category")
    is_active: bool = Field(default=True)


class IntegrationCategoryCreate(BaseModel):
    """Model for creating integration categories."""
    name: str
    description: str
    icon: str = "Puzzle"
    color: str = "#6366f1"


class IntegrationCategoryUpdate(BaseModel):
    """Model for updating integration categories."""
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


class IntegrationCategoryService:
    """Service for managing integration categories."""

    def __init__(self):
        self.db = get_database()
        self.collection = self.db.integration_categories

    async def create_category(self, category_data: IntegrationCategoryCreate) -> IntegrationCategory:
        """Create a new integration category."""
        category = IntegrationCategory(**category_data.dict())
        result = await self.collection.insert_one(category.dict())
        if result.inserted_id:
            return category
        raise Exception("Failed to create integration category")

    async def get_category(self, category_id: str) -> Optional[IntegrationCategory]:
        """Get integration category by ID."""
        category_doc = await self.collection.find_one({"id": category_id})
        if category_doc:
            return IntegrationCategory(**category_doc)
        return None

    async def get_category_by_name(self, name: str) -> Optional[IntegrationCategory]:
        """Get integration category by name."""
        category_doc = await self.collection.find_one({"name": name})
        if category_doc:
            return IntegrationCategory(**category_doc)
        return None

    async def list_categories(self) -> List[IntegrationCategory]:
        """List all integration categories."""
        cursor = self.collection.find({"is_active": True})
        categories_docs = await cursor.to_list(length=None)
        return [IntegrationCategory(**doc) for doc in categories_docs]

    async def update_category(self, category_id: str, update_data: IntegrationCategoryUpdate) -> Optional[IntegrationCategory]:
        """Update an integration category."""
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        if not update_dict:
            return await self.get_category(category_id)

        result = await self.collection.update_one(
            {"id": category_id},
            {"$set": update_dict}
        )

        if result.modified_count > 0:
            return await self.get_category(category_id)
        return None

    async def delete_category(self, category_id: str) -> bool:
        """Delete an integration category (soft delete)."""
        result = await self.collection.update_one(
            {"id": category_id},
            {"$set": {"is_active": False}}
        )
        return result.modified_count > 0

    async def update_integration_count(self, category_id: str, count: int) -> bool:
        """Update the total integrations count for a category."""
        result = await self.collection.update_one(
            {"id": category_id},
            {"$set": {"total_integrations": count}}
        )
        return result.modified_count > 0

    async def populate_default_categories(self) -> List[IntegrationCategory]:
        """Populate default integration categories from SIMPLE_INTEGRATIONS_LIST."""
        default_categories = [
            {
                "name": "Communication",
                "description": "Multi-channel messaging and notifications including email, SMS, WhatsApp, chat systems, and voice communications",
                "icon": "MessageCircle",
                "color": "#10b981"
            },
            {
                "name": "Payment Systems",
                "description": "Financial transactions and payment processing including mobile money, bank USSD, and interbank systems",
                "icon": "CreditCard",
                "color": "#f59e0b"
            },
            {
                "name": "Business Tools",
                "description": "CRM, support, analytics, and business management platforms for customer service and sales operations",
                "icon": "Briefcase",
                "color": "#8b5cf6"
            },
            {
                "name": "Productivity & Cloud",
                "description": "Cloud services, office suites, collaboration tools, and document management systems",
                "icon": "Cloud",
                "color": "#06b6d4"
            },
            {
                "name": "ERP & Accounting",
                "description": "Enterprise resource planning and financial management systems for business operations",
                "icon": "Calculator",
                "color": "#ef4444"
            },
            {
                "name": "Automation Platforms",
                "description": "Workflow automation and integration platforms for connecting multiple applications",
                "icon": "Zap",
                "color": "#f97316"
            },
            {
                "name": "Payment Gateways",
                "description": "Online payment processing gateways and financial transaction services",
                "icon": "Wallet",
                "color": "#84cc16"
            },
            {
                "name": "Specialized Services",
                "description": "Industry-specific and custom integrations including healthcare, collaboration, and monitoring systems",
                "icon": "Settings",
                "color": "#6366f1"
            }
        ]

        created_categories = []
        for category_data in default_categories:
            existing = await self.get_category_by_name(category_data["name"])
            if not existing:
                category = await self.create_category(IntegrationCategoryCreate(**category_data))
                created_categories.append(category)
            else:
                created_categories.append(existing)

        return created_categories


# Global service instance
integration_category_service = IntegrationCategoryService()