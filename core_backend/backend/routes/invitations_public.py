"""
Public Invitation Routes.

Public endpoints for accepting user invitations.
These routes do not require authentication.

Author: KasaAI Team
Date: 2025-11-23
"""

import logging
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any

from ..models.invitation import AcceptInvitationRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/invitations", tags=["invitations"])


@router.get("/{token}/details")
async def get_invitation_details(token: str):
    """
    Get invitation details by token (PUBLIC).

    Returns invitation information without accepting it.
    Useful for displaying invitation details on the acceptance page.

    Path parameters:
        - token: Invitation token from email

    Returns:
        Invitation details (email, inviter, role, expiry, etc.)
    """
    try:
        from ..services.invitation_service import get_invitation_service

        invitation_service = await get_invitation_service()

        # Get invitation
        invitation = await invitation_service.get_invitation_by_token(token)

        if not invitation:
            raise HTTPException(
                status_code=404,
                detail="Invitation not found or invalid token"
            )

        # Check if expired
        is_expired = invitation.is_expired
        is_valid = invitation.is_valid

        return {
            "success": True,
            "invitation": {
                "email": invitation.email,
                "invited_by": invitation.invited_by_name,
                "role": invitation.role,
                "message": invitation.message,
                "created_at": invitation.created_at.isoformat(),
                "expires_at": invitation.expires_at.isoformat(),
                "status": invitation.status,
                "is_expired": is_expired,
                "is_valid": is_valid,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching invitation details: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch invitation details: {str(e)}"
        )


@router.post("/{token}/accept")
async def accept_invitation(
    token: str,
    request: AcceptInvitationRequest,
    http_request: Request
):
    """
    Accept an invitation and create user account (PUBLIC).

    Creates a new user account based on the invitation and automatically
    registers them as an affiliate with the inviter's referral code.

    Path parameters:
        - token: Invitation token from email

    Request body:
        {
            "token": "abc123def456",  # Same as path param (for validation)
            "password": "SecureP@ssw0rd",
            "first_name": "John",
            "last_name": "Doe"
        }

    Returns:
        User details and authentication tokens
    """
    try:
        from ..services.invitation_service import get_invitation_service

        invitation_service = await get_invitation_service()

        # Validate token matches
        if request.token != token:
            raise HTTPException(
                status_code=400,
                detail="Token mismatch"
            )

        # Get client info
        client_ip = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent")

        # Accept invitation
        result = await invitation_service.accept_invitation(
            token=token,
            request=request,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting invitation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to accept invitation: {str(e)}"
        )
