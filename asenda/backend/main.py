"""
Asenda.ai Backend API

FastAPI backend for lead capture, demo requests, and email automation.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .routes import leads_router, set_lead_service
from .services import EmailService, LeadService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:aawwER4444%40@127.0.0.1:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "asenda")
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", "hello@asenda.ai")
FROM_NAME = os.getenv("FROM_NAME", "Asenda AI")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Initialize services on startup
    logger.info("Initializing Asenda.ai backend services...")

    # Initialize email service
    email_service = EmailService(
        smtp_host=SMTP_HOST,
        smtp_port=SMTP_PORT,
        smtp_user=SMTP_USER,
        smtp_password=SMTP_PASSWORD,
        from_email=FROM_EMAIL,
        from_name=FROM_NAME,
    )

    # Initialize lead service
    lead_service = LeadService(
        mongo_uri=MONGO_URI,
        database_name=DATABASE_NAME,
        email_service=email_service,
    )

    # Set the lead service for routes
    set_lead_service(lead_service)

    logger.info("Asenda.ai backend services initialized successfully")

    yield

    # Cleanup on shutdown
    logger.info("Shutting down Asenda.ai backend services...")


# Create FastAPI app
app = FastAPI(
    title="Asenda.ai API",
    description="Backend API for Asenda.ai - Voice AI & Automation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://asenda.ai",
        "http://asenda.ai",
        "http://localhost:3000",
        "http://localhost:30050",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(leads_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Asenda.ai API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=30051,
        reload=True,
    )
