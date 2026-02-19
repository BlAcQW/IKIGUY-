"""
Email Account Management Routes for KasaAI Developer Platform.

This module provides email account management API endpoints using the EmailAccountService.
Allows developers to programmatically create, disable, enable, and manage email accounts
on the iRedMail server (mail.ailabsafrica.com).
"""

from fastapi import APIRouter, Header, HTTPException
from typing import Dict, Optional, Any
from pydantic import BaseModel, EmailStr, Field
import logging

from ..api_consolidation import (
    StandardAPIResponse,
    create_success_response,
    handle_api_exception,
)

# Import shared email account service
import sys
sys.path.insert(0, "/opt/kasaai/apps")
from shared.services.email_account_service import get_email_account_service

# Create router
router = APIRouter(prefix="/v1/email", tags=["Email Account Management"])

# Initialize email service
email_service = get_email_account_service()

logger = logging.getLogger(__name__)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateEmailAccountRequest(BaseModel):
    """Request model for creating an email account."""

    first_name: str = Field(..., description="Employee first name", min_length=1)
    last_name: str = Field(..., description="Employee last name", min_length=1)
    email: Optional[EmailStr] = Field(None, description="Email address (auto-generated if not provided)")
    quota_mb: Optional[int] = Field(512, description="Mailbox quota in MB", ge=1, le=10240)


class EmailAccountStatusRequest(BaseModel):
    """Request model for email status operations."""

    email: EmailStr = Field(..., description="Email address to check/modify")


class GenerateEmailRequest(BaseModel):
    """Request model for generating email address."""

    first_name: str = Field(..., description="Employee first name", min_length=1)
    last_name: str = Field(..., description="Employee last name", min_length=1)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/accounts", response_model=StandardAPIResponse)
async def create_email_account(
    request: CreateEmailAccountRequest,
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """
    Create a new email account on iRedMail server.

    **Auto-generates email** if not provided: firstname.lastname@ailabsafrica.com
    **Handles duplicates**: Adds numeric suffix (john.doe2@, john.doe3@, etc.)
    **Returns temporary password** for initial login.

    **Example Request**:
    ```json
    {
        "first_name": "John",
        "last_name": "Doe",
        "quota_mb": 512
    }
    ```

    **Example Response**:
    ```json
    {
        "success": true,
        "data": {
            "email": "john.doe@ailabsafrica.com",
            "password": "rA9#mK2$pQ8@vL4!",
            "status": "created",
            "created_at": "2025-11-03T21:15:00.123456",
            "quota_mb": 512
        },
        "message": "Email account created successfully"
    }
    ```

    **Rate Limits**: 10 requests per minute per API key
    **Quota Costs**: 1 credit per account created
    """
    try:
        result = await email_service.create_account(
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            quota_mb=request.quota_mb
        )

        return create_success_response(
            data=result,
            message="Email account created successfully"
        )
    except Exception as e:
        logger.error(f"Failed to create email account: {str(e)}")
        return handle_api_exception(e, "Failed to create email account")


@router.post("/accounts/disable", response_model=StandardAPIResponse)
async def disable_email_account(
    request: EmailAccountStatusRequest,
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """
    Disable an email account (user cannot login, but emails are preserved).

    **Use case**: Employee termination, temporary suspension
    **Data preservation**: All emails and folders are kept
    **Reversible**: Can be re-enabled with /accounts/enable

    **Example Request**:
    ```json
    {
        "email": "john.doe@ailabsafrica.com"
    }
    ```

    **Example Response**:
    ```json
    {
        "success": true,
        "data": {
            "email": "john.doe@ailabsafrica.com",
            "status": "disabled",
            "message": "Account disabled successfully"
        },
        "message": "Email account disabled successfully"
    }
    ```

    **Rate Limits**: 10 requests per minute per API key
    **Quota Costs**: Free (no credit charge)
    """
    try:
        result = await email_service.disable_account(email=request.email)

        return create_success_response(
            data=result,
            message="Email account disabled successfully"
        )
    except Exception as e:
        logger.error(f"Failed to disable email account: {str(e)}")
        return handle_api_exception(e, "Failed to disable email account")


@router.post("/accounts/enable", response_model=StandardAPIResponse)
async def enable_email_account(
    request: EmailAccountStatusRequest,
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """
    Re-enable a previously disabled email account.

    **Use case**: Restore access after suspension
    **Effect**: User can login and access emails again

    **Example Request**:
    ```json
    {
        "email": "john.doe@ailabsafrica.com"
    }
    ```

    **Example Response**:
    ```json
    {
        "success": true,
        "data": {
            "email": "john.doe@ailabsafrica.com",
            "status": "enabled",
            "message": "Account enabled successfully"
        },
        "message": "Email account enabled successfully"
    }
    ```

    **Rate Limits**: 10 requests per minute per API key
    **Quota Costs**: Free (no credit charge)
    """
    try:
        result = await email_service.enable_account(email=request.email)

        return create_success_response(
            data=result,
            message="Email account enabled successfully"
        )
    except Exception as e:
        logger.error(f"Failed to enable email account: {str(e)}")
        return handle_api_exception(e, "Failed to enable email account")


@router.post("/accounts/check", response_model=StandardAPIResponse)
async def check_email_exists(
    request: EmailAccountStatusRequest,
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """
    Check if an email account exists on the server.

    **Use case**: Verify before creating, check for duplicates

    **Example Request**:
    ```json
    {
        "email": "john.doe@ailabsafrica.com"
    }
    ```

    **Example Response**:
    ```json
    {
        "success": true,
        "data": {
            "email": "john.doe@ailabsafrica.com",
            "exists": true
        },
        "message": "Email check completed successfully"
    }
    ```

    **Rate Limits**: 20 requests per minute per API key
    **Quota Costs**: Free (no credit charge)
    """
    try:
        exists = await email_service.check_exists(email=request.email)

        return create_success_response(
            data={
                "email": request.email,
                "exists": exists
            },
            message="Email check completed successfully"
        )
    except Exception as e:
        logger.error(f"Failed to check email existence: {str(e)}")
        return handle_api_exception(e, "Failed to check email existence")


@router.post("/accounts/generate-email", response_model=StandardAPIResponse)
async def generate_email_address(
    request: GenerateEmailRequest,
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """
    Generate and preview an email address without creating the account.

    **Use case**: Preview email before creation, check availability
    **Format**: firstname.lastname@ailabsafrica.com
    **Duplicate handling**: Adds numeric suffix if already exists

    **Example Request**:
    ```json
    {
        "first_name": "John",
        "last_name": "Doe"
    }
    ```

    **Example Response**:
    ```json
    {
        "success": true,
        "data": {
            "email": "john.doe@ailabsafrica.com",
            "available": true
        },
        "message": "Email generated successfully"
    }
    ```

    **Rate Limits**: 20 requests per minute per API key
    **Quota Costs**: Free (no credit charge)
    """
    try:
        email = await email_service.generate_email(
            first_name=request.first_name,
            last_name=request.last_name
        )

        # Check if email exists
        exists = await email_service.check_exists(email=email)

        return create_success_response(
            data={
                "email": email,
                "available": not exists
            },
            message="Email generated successfully"
        )
    except Exception as e:
        logger.error(f"Failed to generate email: {str(e)}")
        return handle_api_exception(e, "Failed to generate email")


@router.get("/config", response_model=StandardAPIResponse)
async def get_email_config(x_api_key: str = Header(...)) -> StandardAPIResponse:
    """
    Get email service configuration and limits.

    **Returns**: Domain, default quota, rate limits, etc.

    **Example Response**:
    ```json
    {
        "success": true,
        "data": {
            "domain": "ailabsafrica.com",
            "default_quota_mb": 512,
            "max_quota_mb": 10240,
            "rate_limits": {
                "create": "10 per minute",
                "check": "20 per minute"
            },
            "features": {
                "auto_generation": true,
                "duplicate_handling": true,
                "quota_customization": true
            }
        },
        "message": "Email configuration retrieved successfully"
    }
    ```

    **Rate Limits**: 100 requests per minute per API key
    **Quota Costs**: Free (no credit charge)
    """
    try:
        config = {
            "domain": "ailabsafrica.com",
            "default_quota_mb": 512,
            "max_quota_mb": 10240,
            "rate_limits": {
                "create": "10 per minute",
                "disable": "10 per minute",
                "enable": "10 per minute",
                "check": "20 per minute",
                "generate": "20 per minute",
                "config": "100 per minute"
            },
            "features": {
                "auto_generation": True,
                "duplicate_handling": True,
                "quota_customization": True,
                "account_suspension": True,
                "account_restoration": True
            },
            "server": {
                "webmail_url": "https://mail.ailabsafrica.com",
                "smtp_server": "mail.ailabsafrica.com",
                "smtp_port": 587,
                "imap_server": "mail.ailabsafrica.com",
                "imap_port": 993
            }
        }

        return create_success_response(
            data=config,
            message="Email configuration retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get email config: {str(e)}")
        return handle_api_exception(e, "Failed to get email configuration")
