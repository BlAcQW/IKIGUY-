"""
API Key Authentication Dependency for Developer Platform.

Provides FastAPI dependencies for API key verification.
"""

import logging
from typing import Dict, Any
from fastapi import Header, HTTPException, Depends

logger = logging.getLogger(__name__)


async def verify_api_key(x_api_key: str = Header(..., description="API Key for authentication")) -> Dict[str, Any]:
    """
    Verify API key and return key details.

    This is a FastAPI dependency that can be used to protect endpoints:

    Example:
        @router.get("/protected")
        async def protected_endpoint(api_key_info: Dict = Depends(verify_api_key)):
            tenant_id = api_key_info["tenant_id"]
            ...

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        Dict containing API key details:
        - key_id: API key ID
        - tenant_id: Tenant ID
        - plan: Plan tier (free, starter, professional, enterprise)
        - scopes: List of allowed scopes

    Raises:
        HTTPException: If API key is invalid or disabled
    """
    try:
        # Import here to avoid circular imports
        from ..security import security_middleware

        # Verify API key
        key_info = await security_middleware.verify_api_key(x_api_key)

        # TODO: Get plan tier from database
        # For now, default to free tier
        key_info["plan"] = "free"

        return key_info

    except ValueError as e:
        logger.warning(f"API key verification failed: {e}")
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "AUTHENTICATION_ERROR",
                    "message": str(e),
                    "field": "x-api-key"
                },
                "request_id": f"req_{int(__import__('time').time())}",
                "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z"
            }
        )


async def verify_api_key_optional(
    x_api_key: str = Header(None, description="Optional API Key for authentication")
) -> Dict[str, Any] | None:
    """
    Verify API key if provided, otherwise return None.

    This is useful for endpoints that have both public and authenticated access.

    Args:
        x_api_key: Optional API key from X-API-Key header

    Returns:
        Dict with API key details or None if no key provided
    """
    if not x_api_key:
        return None

    try:
        return await verify_api_key(x_api_key)
    except HTTPException:
        return None


async def require_scopes(*required_scopes: str):
    """
    Create a dependency that requires specific scopes.

    Example:
        @router.post("/admin/action", dependencies=[Depends(require_scopes("admin", "write"))])
        async def admin_action():
            ...

    Args:
        *required_scopes: Required scopes

    Returns:
        Dependency function
    """
    async def check_scopes(api_key_info: Dict = Depends(verify_api_key)):
        """Check if API key has required scopes."""
        key_scopes = set(api_key_info.get("scopes", []))
        missing_scopes = set(required_scopes) - key_scopes

        if missing_scopes:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "AUTHORIZATION_ERROR",
                        "message": f"Missing required scopes: {', '.join(missing_scopes)}",
                        "field": None
                    },
                    "request_id": f"req_{int(__import__('time').time())}",
                    "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z"
                }
            )

        return api_key_info

    return check_scopes
