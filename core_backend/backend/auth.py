"""Authentication utilities for service tokens."""

import os
from fastapi import Header, HTTPException, Depends

from .models import ServiceAccount
from .services import service_account_service


def get_current_account(x_service_token: str = Header(...)) -> ServiceAccount:
    """Authenticate the request using a service token.

    Args:
        x_service_token (str): Token provided in ``X-Service-Token`` header.

    Returns:
        ServiceAccount: The matching service account.

    Raises:
        HTTPException: If the token is invalid.
    """
    account = service_account_service.get_by_token(x_service_token)
    if not account:
        raise HTTPException(status_code=401, detail="Invalid service token")
    return account


def get_current_tenant_id(account: ServiceAccount = Depends(get_current_account)) -> str:
    """Get the current tenant ID from the authenticated account.

    Args:
        account (ServiceAccount): The authenticated service account.

    Returns:
        str: The tenant ID associated with the account.

    Raises:
        HTTPException: If the account has no tenant ID.
    """
    if not account.tenant_id:
        raise HTTPException(status_code=400, detail="Account has no associated tenant")
    return account.tenant_id


def get_api_deploy_key(authorization: str = Header(...)) -> str:
    """Authenticate the request using API deploy key.

    Args:
        authorization (str): Authorization header in format ``Bearer {API_DEPLOY_KEY}``.

    Returns:
        str: The API deploy key if valid.

    Raises:
        HTTPException: If the authorization header is invalid or key doesn't match.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    api_key = authorization.replace("Bearer ", "")
    expected_key = os.getenv("API_DEPLOY_KEY")
    if not expected_key:
        raise HTTPException(status_code=500, detail="API deploy key not configured")
    if api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API deploy key")
    return api_key


def get_current_user(account: ServiceAccount = Depends(get_current_account)) -> dict:
    """Get the current user info from the authenticated account.
    
    Args:
        account (ServiceAccount): The authenticated service account.
        
    Returns:
        dict: User info including tenant_id.
    """
    return {
        "tenant_id": account.tenant_id,
        "account_id": account.id,
        "name": account.name
    }


async def get_current_user_mongo(authorization: str = Header(...)) -> dict:
    """Get the current user info from MongoDB JWT token.

    Args:
        authorization (str): Authorization header in format ``Bearer {token}``.

    Returns:
        dict: User info including email and metadata from MongoDB JWT.

    Raises:
        HTTPException: If the authorization header is invalid.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.replace("Bearer ", "")

    # Import here to avoid circular imports
    from .services.auth_service import get_auth_service

    try:
        auth_service = await get_auth_service()
        user_data = await auth_service.get_current_user(token)
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


async def get_user_from_header(
    authorization: str = Header(None),
    x_user_id: str = Header(None, alias="X-User-Id")
) -> dict:
    """Get user info from either Bearer token OR X-User-Id header.

    This supports two authentication patterns:
    1. Direct frontend calls: Bearer token with JWT authentication
    2. Developer Platform proxying: X-User-Id header with user context

    Args:
        authorization: Optional Authorization header with Bearer token
        x_user_id: Optional X-User-Id header for proxied requests

    Returns:
        dict: User info including user_id/sub

    Raises:
        HTTPException: If neither auth method is provided or both fail
    """
    # If X-User-Id is provided, use it (for Developer Platform proxying)
    if x_user_id:
        return {
            "user_id": x_user_id,
            "sub": x_user_id,  # Add 'sub' for compatibility with existing code
            "source": "developer_platform"
        }

    # Otherwise, try Bearer token authentication
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")

        from .services.auth_service import get_auth_service

        try:
            auth_service = await get_auth_service()
            user_data = await auth_service.get_current_user(token)
            return user_data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

    # No authentication provided
    raise HTTPException(
        status_code=401,
        detail="Authentication required: provide either Bearer token or X-User-Id header"
    )


# Backwards compatibility - use MongoDB auth by default
get_current_user_bearer = get_current_user_mongo
