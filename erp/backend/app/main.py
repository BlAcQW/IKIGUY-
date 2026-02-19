"""
KasaAI ERP - Enterprise Resource Planning System.

Organization-scoped ERP with Finance, HR, CRM, BI, and Project Management.
"""

import logging
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from app.config import settings
from app.core.database import connect_databases, disconnect_databases, MongoDB
from app.core.auth import initialize_auth
from app.api import api_router
from apps.shared.middleware import OrganizationContextMiddleware
from apps.shared.services.organization_service import get_organization_service
from apps.shared.startup import initialize_default_organization
from apps.shared.storage.hetzner_storage_box import get_storage, StorageProtocol
from apps.shared.services.file_upload_service import get_file_upload_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting ERP backend...")
    try:
        await connect_databases()
        initialize_auth()

        # Initialize organization service
        db = MongoDB.get_database()
        org_service = get_organization_service(db)
        await org_service.initialize_indexes()
        logger.info("✅ Organization service initialized")

        # Initialize default organization
        await initialize_default_organization()

        # Initialize ERP-specific indexes
        await initialize_erp_indexes(db)

        # Initialize Hetzner storage for file uploads
        try:
            storage = await get_storage(
                protocol=StorageProtocol.WEBDAV,
                base_path="kasaai/erp"
            )
            # Initialize file upload service with Hetzner storage
            await get_file_upload_service(storage_service=storage)
            logger.info("✅ Hetzner storage initialized for file uploads")
        except Exception as e:
            logger.warning(f"⚠️ Hetzner storage not available, using local storage: {str(e)}")
            # Initialize file upload service without storage (will use local)
            await get_file_upload_service()

        logger.info("✓ ERP backend started successfully")
    except Exception as e:
        logger.error(f"✗ Startup failed: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down ERP backend...")
    await disconnect_databases()
    logger.info("✓ ERP backend stopped")


async def initialize_erp_indexes(db):
    """Initialize database indexes for ERP collections."""
    # Reason: Ensure all organization-scoped collections have proper indexes
    collections = [
        "customers", "leads", "opportunities", "contacts", "activities", "crm_tasks",  # CRM
        "employees", "payroll", "benefits", "recruitment",  # HR
        "employee_onboarding", "onboarding_templates",  # Onboarding
        "accounts", "transactions", "invoices", "expenses", "budgets",  # Finance
        "projects", "tasks", "resources", "timesheets",  # Projects
        "reports", "dashboards", "kpis",  # BI
        "integrations", "workflows", "audit_logs",  # System
        "partnerships", "partnership_interactions",  # Partnerships
    ]

    for collection_name in collections:
        collection = db[collection_name]
        # Create organization_id index for all collections
        await collection.create_index("organization_id")
        await collection.create_index([("organization_id", 1), ("created_at", -1)])

    # Additional indexes for onboarding
    await db.employee_onboarding.create_index([("organization_id", 1), ("employee_id", 1)])
    await db.employee_onboarding.create_index([("organization_id", 1), ("department", 1)])
    await db.employee_onboarding.create_index([("organization_id", 1), ("onboarding_status", 1)])
    await db.onboarding_templates.create_index([("organization_id", 1), ("department", 1)])

    # Additional indexes for partnerships
    await db.partnerships.create_index([("organization_id", 1), ("stage", 1)])
    await db.partnerships.create_index([("organization_id", 1), ("partnership_type", 1)])
    await db.partnerships.create_index([("organization_id", 1), ("assigned_to", 1)])
    await db.partnership_interactions.create_index([("organization_id", 1), ("partnership_id", 1)])
    await db.partnership_interactions.create_index([("organization_id", 1), ("interaction_date", -1)])

    # Additional indexes for CRM activities
    await db.activities.create_index([("organization_id", 1), ("entity_type", 1), ("entity_id", 1)])
    await db.activities.create_index([("organization_id", 1), ("activity_type", 1)])
    await db.activities.create_index([("organization_id", 1), ("performed_by", 1)])
    await db.activities.create_index([("organization_id", 1), ("activity_date", -1)])
    await db.activities.create_index([("organization_id", 1), ("requires_follow_up", 1), ("follow_up_completed", 1)])
    await db.activities.create_index([("organization_id", 1), ("follow_up_date", 1)])

    # Additional indexes for CRM tasks
    await db.crm_tasks.create_index([("organization_id", 1), ("entity_type", 1), ("entity_id", 1)])
    await db.crm_tasks.create_index([("organization_id", 1), ("assigned_to", 1)])
    await db.crm_tasks.create_index([("organization_id", 1), ("assigned_by", 1)])
    await db.crm_tasks.create_index([("organization_id", 1), ("status", 1)])
    await db.crm_tasks.create_index([("organization_id", 1), ("priority", 1)])
    await db.crm_tasks.create_index([("organization_id", 1), ("due_date", 1)])
    await db.crm_tasks.create_index([("organization_id", 1), ("status", 1), ("due_date", 1)])
    await db.crm_tasks.create_index([("organization_id", 1), ("tags", 1)])

    # Indexes for file metadata
    await db.erp_file_metadata.create_index([("organization_id", 1), ("path", 1)])
    await db.erp_file_metadata.create_index([("organization_id", 1), ("expense_id", 1)])
    await db.erp_file_metadata.create_index([("organization_id", 1), ("category", 1)])
    await db.erp_file_metadata.create_index([("file_id", 1)])
    await db.erp_file_metadata.create_index([("storage_type", 1)])

    logger.info("✅ ERP indexes initialized")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise Resource Planning System with Organization Management",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Organization Context Middleware
app.add_middleware(OrganizationContextMiddleware)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount shared static files (for logo, etc.)
app.mount(
    "/shared",
    StaticFiles(directory="/opt/kasaai/apps/shared"),
    name="shared"
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": "KasaAI ERP",
        "tagline": "Comprehensive Enterprise Resource Planning for Growing Organizations",
        "version": "1.0.0",
        "status": "active",
        "environment": settings.ENVIRONMENT,
        "modules": [
            "Finance & Accounting",
            "Human Resources",
            "Customer Relationship Management",
            "Business Intelligence",
            "Integration & Automation",
            "Project Management",
            "Security & Compliance",
        ],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "erp-backend",
        "version": "1.0.0",
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for validation errors.

    Logs the full error details and returns a user-friendly message.
    """
    # Log the full error details
    errors = exc.errors()
    logger.error(f"Validation error on {request.method} {request.url.path}: {errors}")

    # Format errors for response
    formatted_errors = []
    for error in errors:
        field = " -> ".join(str(loc) for loc in error.get("loc", []))
        msg = error.get("msg", "Invalid value")
        formatted_errors.append(f"{field}: {msg}")

    return JSONResponse(
        status_code=422,
        content={
            "detail": "; ".join(formatted_errors),
            "errors": errors
        },
    )
