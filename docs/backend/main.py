"""
KasaAI Documentation Server with Authentication and User Management

Features:
- Public access to main documentation
- Protected internal documentation with role-based access
- User signup and management
- Document visibility controls
- Admin dashboard
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add parent directory to path for shared imports
apps_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, apps_path)
kasaai_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, kasaai_root)

from apps.shared.auth.supabase_auth import get_current_user, get_current_user_optional, get_supabase_client
from supabase import create_client, Client
from apps.shared.services.unified_email_service import get_email_service

# Import local modules
from docs_models import (
    UserRole, DocumentVisibility, UserCreate, UserUpdate, User,
    DocumentMetadataCreate, DocumentMetadataUpdate, LoginRequest, LoginResponse
)
import docs_database as db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="KasaAI Documentation",
    description="Public and internal documentation for KasaAI platform with user management",
    version="2.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://docs.ailabsafrica.com",
        "https://developer.ailabsafrica.com",
        "https://kasaai.ailabsafrica.com",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get environment variables
UNIVERSAL_ADMIN_EMAILS = os.getenv("UNIVERSAL_ADMIN_EMAILS", "").split(",")
UNIVERSAL_ADMIN_USER_IDS = os.getenv("UNIVERSAL_ADMIN_USER_IDS", "").split(",")

# Path to Docusaurus build
DOCS_BUILD_PATH = Path(__file__).parent.parent / "build"


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await db.init_database()
    logger.info("Database initialized")


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom exception handler for better user-friendly error messages.

    Provides HTML responses for browser requests and JSON for API requests.
    """
    # Check if this is a request for internal docs (HTML)
    is_internal_request = request.url.path.startswith("/internal/")
    accept_header = request.headers.get("accept", "")
    wants_html = "text/html" in accept_header

    # For internal docs auth errors, return user-friendly HTML page
    if is_internal_request and wants_html and exc.status_code in [401, 403]:
        return HTMLResponse(
            content=f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authentication Required - KasaAI Documentation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            padding: 3rem;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 500px;
            text-align: center;
        }}
        h1 {{
            color: #2d3748;
            margin-bottom: 1rem;
            font-size: 2rem;
        }}
        .icon {{
            font-size: 4rem;
            margin-bottom: 1rem;
        }}
        p {{
            color: #4a5568;
            margin-bottom: 1.5rem;
            line-height: 1.6;
        }}
        .btn {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 0.75rem 2rem;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 500;
            transition: background 0.3s;
            margin: 0.5rem;
        }}
        .btn:hover {{
            background: #5a67d8;
        }}
        .btn-secondary {{
            background: #48bb78;
        }}
        .btn-secondary:hover {{
            background: #38a169;
        }}
        .info {{
            background: #edf2f7;
            padding: 1rem;
            border-radius: 6px;
            margin-top: 1.5rem;
            font-size: 0.9rem;
            color: #2d3748;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">🔒</div>
        <h1>Authentication Required</h1>
        <p>
            This is <strong>internal documentation</strong> for AI Labs Africa employees only.
            You need to be logged in with an authorized account to access this content.
        </p>
        <div>
            <a href="/api/auth/login" class="btn">Log In</a>
            <a href="/" class="btn btn-secondary">View Public Docs</a>
        </div>
        <div class="info">
            <strong>Need access?</strong><br>
            Contact your administrator or sign up for an account. Only employees with
            <em>internal</em> or <em>admin</em> roles can access internal documentation.
        </div>
    </div>
</body>
</html>
            """,
            status_code=exc.status_code
        )

    # For API requests or other errors, return JSON
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )


def get_supabase_admin_client() -> Client:
    """
    Get Supabase admin client with service role key.
    Used for operations that bypass email confirmation.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_role_key:
        raise RuntimeError(
            "Supabase admin credentials not configured. "
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables."
        )

    return create_client(supabase_url, service_role_key)


def is_universal_admin(user: Dict[str, Any]) -> bool:
    """Check if user is a universal admin."""
    user_email = user.get("email", "")
    user_id = user.get("id", "")

    return (
        user_email in UNIVERSAL_ADMIN_EMAILS or
        user_id in UNIVERSAL_ADMIN_USER_IDS
    )


async def get_user_role(user: Dict[str, Any]) -> UserRole:
    """Get user's role from database or determine from universal admin status."""
    # Check if universal admin first
    if is_universal_admin(user):
        return UserRole.ADMIN

    # Check database for custom role
    user_data = await db.get_user_by_id(user["id"])
    if user_data:
        return UserRole(user_data.get("role", "public"))

    return UserRole.PUBLIC


async def verify_admin(user: dict = Depends(get_current_user)) -> dict:
    """Verify user is an admin."""
    role = await get_user_role(user)
    if role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


async def verify_internal_access(user: dict = Depends(get_current_user)) -> dict:
    """Verify user has access to internal documentation."""
    role = await get_user_role(user)
    if role not in [UserRole.ADMIN, UserRole.INTERNAL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Internal documentation access required"
        )
    return user


async def check_document_access(path: str, user: Optional[dict] = None) -> bool:
    """Check if user can access a document based on its visibility."""
    # Get document metadata
    doc_metadata = await db.get_document_metadata(path)

    if not doc_metadata:
        # If no metadata, check path prefix
        if path.startswith("internal/"):
            # Internal docs require authentication
            if not user:
                return False
            role = await get_user_role(user)
            return role in [UserRole.ADMIN, UserRole.INTERNAL]
        # Public by default
        return True

    # Check based on visibility setting
    if doc_metadata["visibility"] == DocumentVisibility.PUBLIC:
        return True

    # Internal docs require authentication
    if not user:
        return False

    role = await get_user_role(user)
    return role in [UserRole.ADMIN, UserRole.INTERNAL]


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/signup", response_model=LoginResponse)
async def signup(user_create: UserCreate):
    """Register a new user."""
    try:
        # Use admin client to create user without email confirmation
        admin_supabase = get_supabase_admin_client()

        # Create user in Supabase with admin client (bypasses email confirmation)
        response = admin_supabase.auth.admin.create_user({
            "email": user_create.email,
            "password": user_create.password,
            "email_confirm": True,  # Auto-confirm email
            "user_metadata": {
                "full_name": user_create.full_name or ""
            }
        })

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )

        # Create user in our database
        user_data = {
            "supabase_id": response.user.id,
            "email": user_create.email,
            "full_name": user_create.full_name,
            "role": UserRole.PUBLIC.value,  # Default role
            "is_active": True
        }
        await db.create_user(user_data)

        # Send welcome email using shared email service
        try:
            email_service = get_email_service()
            full_name = user_create.full_name or user_create.email.split('@')[0]

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to KasaAI Documentation! 🎉</h1>
                    </div>
                    <div class="content">
                        <h2>Hi {full_name},</h2>
                        <p>Thank you for signing up for KasaAI Documentation access!</p>

                        <p>Your account has been created with the following details:</p>
                        <ul>
                            <li><strong>Email:</strong> {user_create.email}</li>
                            <li><strong>Role:</strong> Public Access</li>
                        </ul>

                        <h3>What you can access:</h3>
                        <p>✅ All public documentation<br>
                        ✅ API reference guides<br>
                        ✅ Use case examples<br>
                        ✅ Getting started tutorials</p>

                        <h3>Need internal access?</h3>
                        <p>If you need access to internal documentation, please contact an administrator to upgrade your account role.</p>

                        <a href="https://docs.ailabsafrica.com" class="button">Browse Documentation</a>

                        <p>If you have any questions, feel free to reach out to our support team.</p>

                        <p>Best regards,<br>
                        <strong>The KasaAI Team</strong></p>
                    </div>
                    <div class="footer">
                        <p>This email was sent to {user_create.email} because you signed up for KasaAI Documentation.</p>
                        <p>&copy; 2025 AI Labs Africa. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            plain_body = f"""
            Welcome to KasaAI Documentation!

            Hi {full_name},

            Thank you for signing up for KasaAI Documentation access!

            Your account has been created:
            - Email: {user_create.email}
            - Role: Public Access

            What you can access:
            ✅ All public documentation
            ✅ API reference guides
            ✅ Use case examples
            ✅ Getting started tutorials

            Need internal access?
            If you need access to internal documentation, please contact an administrator.

            Visit: https://docs.ailabsafrica.com

            Best regards,
            The KasaAI Team
            """

            email_result = await email_service.send_email(
                to=user_create.email,
                subject="Welcome to KasaAI Documentation! 🎉",
                body=plain_body,
                html_body=html_body,
                from_name="KasaAI Documentation"
            )

            if email_result.get("success"):
                logger.info(f"✅ Welcome email sent to {user_create.email}")
            else:
                logger.warning(f"⚠️ Failed to send welcome email: {email_result.get('error')}")
        except Exception as e:
            # Don't fail signup if email fails
            logger.error(f"❌ Welcome email error: {e}")

        # Now sign in the user to get access tokens
        regular_supabase = get_supabase_client()
        login_response = regular_supabase.auth.sign_in_with_password({
            "email": user_create.email,
            "password": user_create.password
        })

        return LoginResponse(
            access_token=login_response.session.access_token if login_response.session else "",
            refresh_token=login_response.session.refresh_token if login_response.session else "",
            user={
                "id": response.user.id,
                "email": response.user.email,
                "full_name": user_create.full_name,
                "role": UserRole.PUBLIC.value
            }
        )
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/auth/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    """Login user."""
    try:
        supabase = get_supabase_client()

        response = supabase.auth.sign_in_with_password({
            "email": login_request.email,
            "password": login_request.password
        })

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Get user role from database
        user_data = await db.get_user_by_id(response.user.id)
        role = user_data.get("role", UserRole.PUBLIC.value) if user_data else UserRole.PUBLIC.value

        return LoginResponse(
            access_token=response.session.access_token if response.session else "",
            refresh_token=response.session.refresh_token if response.session else "",
            user={
                "id": response.user.id,
                "email": response.user.email,
                "full_name": user_data.get("full_name", "") if user_data else "",
                "role": role
            }
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@app.get("/api/auth/verify")
async def verify_auth(user: Optional[dict] = Depends(get_current_user_optional)):
    """Verify authentication status and get user role."""
    if user:
        role = await get_user_role(user)
        user_data = await db.get_user_by_id(user["id"])

        return {
            "authenticated": True,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "display_name": user.get("display_name", ""),
                "full_name": user_data.get("full_name", "") if user_data else "",
                "role": role.value
            },
            "is_admin": role == UserRole.ADMIN,
            "has_internal_access": role in [UserRole.ADMIN, UserRole.INTERNAL]
        }
    else:
        return {
            "authenticated": False,
            "is_admin": False,
            "has_internal_access": False
        }


# ============================================================================
# User Management Endpoints (Admin Only)
# ============================================================================

@app.get("/api/admin/users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    admin: dict = Depends(verify_admin)
):
    """List all users (admin only)."""
    users = await db.list_users(skip, limit)

    # Convert MongoDB documents to JSON-serializable format
    result = []
    for user in users:
        user["_id"] = str(user["_id"])
        user["created_at"] = user["created_at"].isoformat()
        user["updated_at"] = user["updated_at"].isoformat()
        result.append(user)

    return result


@app.get("/api/admin/users/{user_id}")
async def get_user(
    user_id: str,
    admin: dict = Depends(verify_admin)
):
    """Get user by ID (admin only)."""
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user["_id"] = str(user["_id"])
    user["created_at"] = user["created_at"].isoformat()
    user["updated_at"] = user["updated_at"].isoformat()
    return user


@app.put("/api/admin/users/{user_id}")
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    admin: dict = Depends(verify_admin)
):
    """Update user (admin only)."""
    # Check user exists
    existing_user = await db.get_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prepare update data
    update_data = {}
    if user_update.full_name is not None:
        update_data["full_name"] = user_update.full_name
    if user_update.role is not None:
        update_data["role"] = user_update.role.value
    if user_update.is_active is not None:
        update_data["is_active"] = user_update.is_active

    # Update user
    updated_user = await db.update_user(user_id, update_data)

    if updated_user:
        updated_user["_id"] = str(updated_user["_id"])
        updated_user["created_at"] = updated_user["created_at"].isoformat()
        updated_user["updated_at"] = updated_user["updated_at"].isoformat()

    return updated_user


@app.delete("/api/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: dict = Depends(verify_admin)
):
    """Delete user (admin only)."""
    success = await db.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {"message": "User deleted successfully"}


# ============================================================================
# Document Metadata Endpoints (Admin Only)
# ============================================================================

@app.get("/api/admin/documents")
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    admin: dict = Depends(verify_admin)
):
    """List all document metadata (admin only)."""
    docs = await db.list_document_metadata(skip, limit)

    # Convert MongoDB documents to JSON-serializable format
    result = []
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        doc["created_at"] = doc["created_at"].isoformat()
        doc["updated_at"] = doc["updated_at"].isoformat()
        result.append(doc)

    return result


@app.post("/api/admin/documents")
async def create_document_metadata(
    metadata: DocumentMetadataCreate,
    admin: dict = Depends(verify_admin)
):
    """Create document metadata (admin only)."""
    metadata_dict = metadata.dict()
    created = await db.create_document_metadata(metadata_dict)

    if created:
        created["_id"] = str(created["_id"])
        created["created_at"] = created["created_at"].isoformat()
        created["updated_at"] = created["updated_at"].isoformat()

    return created


@app.put("/api/admin/documents/{path:path}")
async def update_document_metadata(
    path: str,
    metadata: DocumentMetadataUpdate,
    admin: dict = Depends(verify_admin)
):
    """Update document metadata (admin only)."""
    # Check document exists
    existing = await db.get_document_metadata(path)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document metadata not found"
        )

    # Prepare update data
    update_data = {}
    if metadata.visibility is not None:
        update_data["visibility"] = metadata.visibility.value
    if metadata.title is not None:
        update_data["title"] = metadata.title
    if metadata.description is not None:
        update_data["description"] = metadata.description

    # Update document
    updated = await db.update_document_metadata(path, update_data)

    if updated:
        updated["_id"] = str(updated["_id"])
        updated["created_at"] = updated["created_at"].isoformat()
        updated["updated_at"] = updated["updated_at"].isoformat()

    return updated


@app.delete("/api/admin/documents/{path:path}")
async def delete_document_metadata(
    path: str,
    admin: dict = Depends(verify_admin)
):
    """Delete document metadata (admin only)."""
    success = await db.delete_document_metadata(path)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document metadata not found"
        )

    return {"message": "Document metadata deleted successfully"}


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "KasaAI Documentation",
        "version": "2.0.0",
        "features": ["user_management", "role_based_access", "document_visibility"]
    }


# ============================================================================
# Documentation Serving Endpoints
# ============================================================================

@app.get("/internal/{path:path}")
async def serve_internal_docs(
    path: str,
    user: dict = Depends(verify_internal_access)
):
    """Serve internal documentation (requires internal access or admin role)."""
    # Check document-level access
    has_access = await check_document_access(f"internal/{path}", user)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this document"
        )

    # Construct full path
    file_path = DOCS_BUILD_PATH / "internal" / path

    # If path is directory, serve index.html
    if file_path.is_dir():
        file_path = file_path / "index.html"

    # Check if file exists
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Internal documentation not found: {path}"
        )

    # Security check
    try:
        file_path.resolve().relative_to(DOCS_BUILD_PATH.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return FileResponse(file_path)


@app.get("/{path:path}")
async def serve_docs(
    path: str,
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """Serve public documentation (authentication optional)."""
    # Check document-level access
    has_access = await check_document_access(path, user)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this document. Please login."
        )

    # Construct full path
    file_path = DOCS_BUILD_PATH / path

    # If path is empty or directory, serve index.html
    if not path or file_path.is_dir():
        file_path = DOCS_BUILD_PATH / "index.html"

    # If file doesn't exist, serve index.html (for SPA routing)
    if not file_path.exists() or not file_path.is_file():
        file_path = DOCS_BUILD_PATH / "index.html"

    # Security check
    try:
        file_path.resolve().relative_to(DOCS_BUILD_PATH.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return FileResponse(file_path)


if __name__ == "__main__":
    import uvicorn

    # Check if build directory exists
    if not DOCS_BUILD_PATH.exists():
        logger.error(f"Documentation build not found at {DOCS_BUILD_PATH}")
        logger.error("Please run 'npm run build' in the docs directory first")
        sys.exit(1)

    logger.info(f"Serving documentation from {DOCS_BUILD_PATH}")
    logger.info(f"Universal admin emails: {UNIVERSAL_ADMIN_EMAILS}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=30035,
        log_level="info"
    )
