"""Industry service for managing industry configurations in MongoDB."""

import os
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from ..models import BaseModel
from pydantic import Field


class Industry(BaseModel):
    """Industry model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Display name of the industry")
    description: str = Field(..., description="Detailed description of the industry")
    standard_integrations: List[Dict[str, Any]] = Field(default_factory=list, description="Standard tools and integrations")
    icon: str = Field(default="Building", description="Icon identifier for UI display")
    color: str = Field(default="#6366f1", description="Brand color for the industry")
    is_active: bool = Field(default=True, description="Whether this industry is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class IndustryCreate(BaseModel):
    """Industry creation model."""
    name: str
    description: str
    standard_integrations: List[Dict[str, Any]] = Field(default_factory=list)
    icon: str = "Building"
    color: str = "#6366f1"


class IndustryUpdate(BaseModel):
    """Industry update model."""
    name: Optional[str] = None
    description: Optional[str] = None
    standard_integrations: Optional[List[Dict[str, Any]]] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


class MongoDBIndustryService:
    """MongoDB-based industry service."""

    def __init__(self):
        """Initialize the industry service."""
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.industries: Optional[Collection] = None
        self._connect()

    def _connect(self):
        """Connect to MongoDB."""
        try:
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
            database_name = os.getenv("MONGO_CORE_DATABASE", "kasaai_core")

            self.client = MongoClient(mongodb_url)
            self.db = self.client[database_name]
            self.industries = self.db["industries"]

            # Create indexes
            try:
                self.industries.create_index("name", unique=True)
                self.industries.create_index("is_active")
            except Exception:
                # Indexes might already exist
                pass

        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    def create_industry(self, industry_data: IndustryCreate) -> Industry:
        """Create a new industry.

        Args:
            industry_data: Industry creation data.

        Returns:
            Industry: The created industry.
        """
        industry = Industry(
            name=industry_data.name,
            description=industry_data.description,
            standard_integrations=industry_data.standard_integrations,
            icon=industry_data.icon,
            color=industry_data.color
        )

        # Insert industry
        self.industries.insert_one(industry.model_dump())
        return industry

    def get_industry(self, industry_id: str) -> Optional[Industry]:
        """Get an industry by ID.

        Args:
            industry_id: Industry ID.

        Returns:
            Industry: Industry if found, None otherwise.
        """
        doc = self.industries.find_one({"id": industry_id})
        return Industry(**doc) if doc else None

    def get_industry_by_name(self, name: str) -> Optional[Industry]:
        """Get an industry by name.

        Args:
            name: Industry name.

        Returns:
            Industry: Industry if found, None otherwise.
        """
        doc = self.industries.find_one({"name": name, "is_active": True})
        return Industry(**doc) if doc else None

    def list_industries(self, active_only: bool = True) -> List[Industry]:
        """List all industries.

        Args:
            active_only: Whether to return only active industries.

        Returns:
            List[Industry]: List of industries.
        """
        query = {"is_active": True} if active_only else {}
        docs = list(self.industries.find(query).sort("name", 1))
        return [Industry(**doc) for doc in docs]

    def update_industry(self, industry_id: str, update_data: IndustryUpdate) -> Optional[Industry]:
        """Update an industry.

        Args:
            industry_id: Industry ID.
            update_data: Update data.

        Returns:
            Industry: Updated industry if found, None otherwise.
        """
        # Prepare update data
        update_dict = {}
        for field, value in update_data.model_dump(exclude_unset=True).items():
            if value is not None:
                update_dict[field] = value

        if not update_dict:
            return self.get_industry(industry_id)

        update_dict["updated_at"] = datetime.utcnow()

        # Update industry
        result = self.industries.update_one(
            {"id": industry_id},
            {"$set": update_dict}
        )

        if result.modified_count > 0:
            return self.get_industry(industry_id)
        return None

    def delete_industry(self, industry_id: str) -> bool:
        """Delete an industry (soft delete).

        Args:
            industry_id: Industry ID.

        Returns:
            bool: True if deleted successfully, False otherwise.
        """
        result = self.industries.update_one(
            {"id": industry_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def get_industry_integrations(self, industry_id: str) -> List[Dict[str, Any]]:
        """Get standard integrations for an industry.

        Args:
            industry_id: Industry ID.

        Returns:
            List[Dict]: List of standard integrations.
        """
        industry = self.get_industry(industry_id)
        return industry.standard_integrations if industry else []

    def populate_default_industries(self) -> List[Industry]:
        """Populate default industries based on current automation templates.

        Returns:
            List[Industry]: List of created industries.
        """
        # Define default industries with descriptions and standard integrations
        default_industries = [
            {
                "name": "Education",
                "description": "Educational institutions including schools, universities, and training centers",
                "icon": "GraduationCap",
                "color": "#10b981",
                "standard_integrations": [
                    {
                        "name": "Student Information System",
                        "type": "database",
                        "description": "Integration with student records and enrollment systems",
                        "common_apis": ["Blackboard", "Canvas", "Moodle"]
                    },
                    {
                        "name": "Email Notifications",
                        "type": "communication",
                        "description": "Email integration for student and parent communications",
                        "common_apis": ["Gmail", "Outlook", "SendGrid"]
                    },
                    {
                        "name": "Calendar Systems",
                        "type": "scheduling",
                        "description": "Integration with academic calendars and scheduling",
                        "common_apis": ["Google Calendar", "Outlook Calendar"]
                    }
                ]
            },
            {
                "name": "Finance",
                "description": "Financial services including banks, credit unions, and investment firms",
                "icon": "CreditCard",
                "color": "#3b82f6",
                "standard_integrations": [
                    {
                        "name": "Core Banking System",
                        "type": "database",
                        "description": "Integration with customer accounts and transaction systems",
                        "common_apis": ["Temenos", "FIS", "Jack Henry"]
                    },
                    {
                        "name": "CRM Systems",
                        "type": "customer_management",
                        "description": "Customer relationship management integration",
                        "common_apis": ["Salesforce", "HubSpot", "Microsoft Dynamics"]
                    },
                    {
                        "name": "Fraud Detection",
                        "type": "security",
                        "description": "Real-time fraud monitoring and alerts",
                        "common_apis": ["FICO", "SAS", "IBM Watson"]
                    },
                    {
                        "name": "Document Management",
                        "type": "compliance",
                        "description": "Secure document storage and compliance tracking",
                        "common_apis": ["DocuSign", "Adobe Sign", "SharePoint"]
                    }
                ]
            },
            {
                "name": "Healthcare",
                "description": "Healthcare providers including hospitals, clinics, and medical practices",
                "icon": "Heart",
                "color": "#ef4444",
                "standard_integrations": [
                    {
                        "name": "Electronic Health Records",
                        "type": "database",
                        "description": "Integration with patient records and medical history",
                        "common_apis": ["Epic", "Cerner", "AllScripts"]
                    },
                    {
                        "name": "Appointment Scheduling",
                        "type": "scheduling",
                        "description": "Patient appointment booking and management",
                        "common_apis": ["SimplePractice", "Athenahealth", "NextGen"]
                    },
                    {
                        "name": "Insurance Verification",
                        "type": "verification",
                        "description": "Real-time insurance eligibility and benefits verification",
                        "common_apis": ["Change Healthcare", "Availity", "Waystar"]
                    },
                    {
                        "name": "HIPAA Compliance",
                        "type": "compliance",
                        "description": "Healthcare data protection and compliance monitoring",
                        "common_apis": ["Compliancy Group", "HIPAA One", "Clearwater"]
                    }
                ]
            },
            {
                "name": "Insurance",
                "description": "Insurance companies providing auto, home, life, and commercial insurance",
                "icon": "Shield",
                "color": "#8b5cf6",
                "standard_integrations": [
                    {
                        "name": "Policy Management System",
                        "type": "database",
                        "description": "Integration with policy records and customer information",
                        "common_apis": ["Guidewire", "Duck Creek", "Insurity"]
                    },
                    {
                        "name": "Claims Processing",
                        "type": "workflow",
                        "description": "Automated claims intake and processing workflows",
                        "common_apis": ["Guidewire ClaimCenter", "Mitchell", "CCC"]
                    },
                    {
                        "name": "Underwriting Tools",
                        "type": "assessment",
                        "description": "Risk assessment and underwriting decision support",
                        "common_apis": ["LexisNexis", "ISO", "Verisk"]
                    },
                    {
                        "name": "Payment Processing",
                        "type": "financial",
                        "description": "Premium collection and claims payment processing",
                        "common_apis": ["Stripe", "PayPal", "ACH Direct"]
                    }
                ]
            },
            {
                "name": "Real Estate",
                "description": "Real estate agencies, brokers, and property management companies",
                "icon": "Home",
                "color": "#f59e0b",
                "standard_integrations": [
                    {
                        "name": "MLS Systems",
                        "type": "database",
                        "description": "Multiple Listing Service integration for property data",
                        "common_apis": ["RETS", "Bridge API", "Spark API"]
                    },
                    {
                        "name": "CRM Systems",
                        "type": "customer_management",
                        "description": "Lead management and client relationship tracking",
                        "common_apis": ["Chime", "Wise Agent", "Top Producer"]
                    },
                    {
                        "name": "Lead Generation",
                        "type": "marketing",
                        "description": "Automated lead capture and qualification",
                        "common_apis": ["Zillow", "Realtor.com", "BoldLeads"]
                    },
                    {
                        "name": "Transaction Management",
                        "type": "workflow",
                        "description": "Contract and closing process management",
                        "common_apis": ["DocuSign", "Dotloop", "SkySlope"]
                    }
                ]
            },
            {
                "name": "Retail",
                "description": "Retail businesses including e-commerce, brick-and-mortar stores, and omnichannel retailers",
                "icon": "ShoppingBag",
                "color": "#ec4899",
                "standard_integrations": [
                    {
                        "name": "E-commerce Platforms",
                        "type": "platform",
                        "description": "Integration with online store and product catalog",
                        "common_apis": ["Shopify", "WooCommerce", "Magento", "BigCommerce"]
                    },
                    {
                        "name": "Inventory Management",
                        "type": "operations",
                        "description": "Real-time inventory tracking and management",
                        "common_apis": ["TradeGecko", "Skubana", "Cin7"]
                    },
                    {
                        "name": "Payment Processing",
                        "type": "financial",
                        "description": "Multi-channel payment processing and fraud protection",
                        "common_apis": ["Stripe", "Square", "PayPal", "Adyen"]
                    },
                    {
                        "name": "Customer Support",
                        "type": "communication",
                        "description": "Omnichannel customer service and support ticketing",
                        "common_apis": ["Zendesk", "Freshdesk", "Intercom"]
                    },
                    {
                        "name": "Marketing Automation",
                        "type": "marketing",
                        "description": "Email marketing and customer segmentation",
                        "common_apis": ["Mailchimp", "Klaviyo", "Constant Contact"]
                    }
                ]
            },
            {
                "name": "Generic",
                "description": "General business processes that apply across multiple industries",
                "icon": "Settings",
                "color": "#6b7280",
                "standard_integrations": [
                    {
                        "name": "CRM Systems",
                        "type": "customer_management",
                        "description": "General customer relationship management",
                        "common_apis": ["Salesforce", "HubSpot", "Pipedrive"]
                    },
                    {
                        "name": "Email Integration",
                        "type": "communication",
                        "description": "Email sending and automation",
                        "common_apis": ["Gmail", "Outlook", "SendGrid", "Mailgun"]
                    },
                    {
                        "name": "Calendar Systems",
                        "type": "scheduling",
                        "description": "Appointment and meeting scheduling",
                        "common_apis": ["Google Calendar", "Outlook Calendar", "Calendly"]
                    },
                    {
                        "name": "Document Management",
                        "type": "productivity",
                        "description": "File storage and document collaboration",
                        "common_apis": ["Google Drive", "Dropbox", "SharePoint"]
                    },
                    {
                        "name": "Analytics & Reporting",
                        "type": "analytics",
                        "description": "Business intelligence and reporting tools",
                        "common_apis": ["Google Analytics", "Tableau", "Power BI"]
                    }
                ]
            }
        ]

        created_industries = []
        for industry_data in default_industries:
            # Check if industry already exists
            existing = self.get_industry_by_name(industry_data["name"])
            if not existing:
                industry_create = IndustryCreate(**industry_data)
                industry = self.create_industry(industry_create)
                created_industries.append(industry)
                print(f"Created industry: {industry.name}")
            else:
                print(f"Industry already exists: {industry_data['name']}")
                created_industries.append(existing)

        return created_industries


# Global service instance
industry_service = MongoDBIndustryService()