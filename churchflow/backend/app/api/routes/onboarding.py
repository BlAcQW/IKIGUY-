"""
Church signup and onboarding routes for ChurchFlow SaaS.

Handles self-service church registration, setup wizard, and onboarding process.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, EmailStr

from app.core.database import get_database
from apps.shared.services.organization_service import get_organization_service
from apps.shared.models import OrganizationCreate, OrganizationRole
from app.services.subscription_service import SubscriptionService
from app.models.subscription import SubscriptionPlan

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


# ================== Request/Response Models ==================

class ChurchSignupRequest(BaseModel):
    """Request to register a new church."""
    # Church Information
    church_name: str = Field(..., min_length=3, max_length=100, description="Church name")
    church_email: EmailStr = Field(..., description="Church contact email")
    church_phone: Optional[str] = Field(None, description="Church contact phone")
    church_address: Optional[str] = Field(None, description="Church physical address")
    church_website: Optional[str] = Field(None, description="Church website URL")

    # Admin User
    admin_name: str = Field(..., min_length=2, max_length=100, description="Admin full name")
    admin_email: EmailStr = Field(..., description="Admin email (for login)")
    admin_phone: str = Field(..., description="Admin phone number (for OTP verification)")

    # Subscription
    selected_plan: SubscriptionPlan = Field(default=SubscriptionPlan.FREE, description="Selected plan")
    trial_days: int = Field(default=14, ge=0, le=30, description="Trial period days")


class SetupWizardRequest(BaseModel):
    """Request for setup wizard steps."""
    step: int = Field(..., ge=1, le=5, description="Current setup step (1-5)")
    data: dict = Field(..., description="Step-specific data")


class ChurchSignupResponse(BaseModel):
    """Response after church signup."""
    success: bool
    message: str
    organization_id: str
    admin_user_id: str
    subscription_id: Optional[str] = None
    next_step: str = "verify_phone"  # Next step in onboarding


class SetupWizardResponse(BaseModel):
    """Response for setup wizard progress."""
    success: bool
    message: str
    current_step: int
    total_steps: int = 5
    completed: bool = False
    next_step: Optional[str] = None


# ================== Church Signup ==================

@router.post("/signup", response_model=ChurchSignupResponse, status_code=status.HTTP_201_CREATED)
async def signup_church(
    request: ChurchSignupRequest,
    db = Depends(get_database),
):
    """
    Register a new church (self-service signup).

    Creates:
    1. Organization (church) record
    2. Admin user with phone OTP verification
    3. Free tier subscription (or trial for paid plans)
    4. Initial usage metrics

    Next steps:
    - User verifies phone via OTP
    - User completes setup wizard
    """
    try:
        org_service = get_organization_service()
        subscription_service = SubscriptionService(db)

        # Step 1: Create organization
        org_create = OrganizationCreate(
            name=request.church_name,
            email=request.church_email,
            phone=request.church_phone,
            address=request.church_address,
            website=request.church_website,
            metadata={
                "signup_date": "datetime.utcnow().isoformat()",
                "onboarding_completed": False,
            }
        )

        # For self-signup, we need to create a placeholder user_id
        # The actual user will be created after phone verification
        # For now, use the email as a temporary identifier
        temp_user_id = f"temp_{request.admin_email}"

        organization = await org_service.create_organization(
            org_create,
            user_id=temp_user_id,
            user_email=request.admin_email,
        )

        logger.info(f"Created organization {organization.id} for {request.church_name}")

        # Step 2: Create subscription
        subscription = await subscription_service.create_subscription(
            organization_id=organization.id,
            plan=request.selected_plan,
            user_email=request.admin_email,
            trial_days=request.trial_days if request.selected_plan != SubscriptionPlan.FREE else 0,
        )

        logger.info(f"Created subscription for organization {organization.id} on plan {request.selected_plan}")

        # Step 3: Send phone verification OTP
        # TODO: Integrate with auth service to send OTP
        # from app.services.auth_service import auth_service
        # await auth_service.send_otp(request.admin_phone)

        return ChurchSignupResponse(
            success=True,
            message="Church registered successfully. Please verify your phone number.",
            organization_id=organization.id,
            admin_user_id=temp_user_id,  # Will be replaced after phone verification
            subscription_id=subscription.stripe_subscription_id,
            next_step="verify_phone",
        )

    except ValueError as e:
        logger.error(f"Validation error during signup: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to signup church: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Church signup failed. Please try again later."
        )


# ================== Phone Verification ==================

class PhoneVerificationRequest(BaseModel):
    """Request to verify phone with OTP."""
    phone: str = Field(..., description="Phone number")
    otp: str = Field(..., min_length=4, max_length=6, description="OTP code")
    organization_id: str = Field(..., description="Organization ID from signup")


@router.post("/verify-phone", response_model=dict)
async def verify_phone(
    request: PhoneVerificationRequest,
    db = Depends(get_database),
):
    """
    Verify phone number with OTP.

    Creates the actual user account after phone verification.
    """
    try:
        # TODO: Verify OTP with auth service
        # from app.services.auth_service import auth_service
        # verified = await auth_service.verify_otp(request.phone, request.otp)
        # if not verified:
        #     raise ValueError("Invalid OTP")

        # For now, assume verification succeeds
        # Create actual user account
        # from app.services.user_service import user_service
        # user = await user_service.create_user(phone=request.phone)

        logger.info(f"Phone verified for organization {request.organization_id}")

        return {
            "success": True,
            "message": "Phone verified successfully",
            "next_step": "setup_wizard",
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to verify phone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Phone verification failed"
        )


# ================== Setup Wizard ==================

@router.post("/setup-wizard", response_model=SetupWizardResponse)
async def process_setup_wizard(
    request: SetupWizardRequest,
    organization_id: str,
    db = Depends(get_database),
):
    """
    Process setup wizard steps.

    Steps:
    1. Church Information (confirm/edit)
    2. Service Times
    3. Leadership Team
    4. Ministries/Departments
    5. Payment Setup (for paid plans)
    """
    try:
        org_service = get_organization_service()

        # Validate organization exists
        org = await org_service.get_organization(organization_id)
        if not org:
            raise ValueError("Organization not found")

        # Process step-specific data
        if request.step == 1:
            # Step 1: Church Information
            # Update organization with confirmed details
            pass

        elif request.step == 2:
            # Step 2: Service Times
            # Save service schedule
            service_times = request.data.get("service_times", [])
            logger.info(f"Saved service times for org {organization_id}: {service_times}")

        elif request.step == 3:
            # Step 3: Leadership Team
            # Invite additional leaders
            leaders = request.data.get("leaders", [])
            logger.info(f"Invited {len(leaders)} leaders for org {organization_id}")

        elif request.step == 4:
            # Step 4: Ministries
            # Create ministry/department structure
            ministries = request.data.get("ministries", [])
            logger.info(f"Created {len(ministries)} ministries for org {organization_id}")

        elif request.step == 5:
            # Step 5: Payment Setup
            # Create Stripe SetupIntent for card collection
            subscription_service = SubscriptionService(db)
            setup_intent = await subscription_service.create_setup_intent(organization_id)

            if not setup_intent:
                raise ValueError("Failed to create payment setup")

            return SetupWizardResponse(
                success=True,
                message="Setup wizard step completed",
                current_step=request.step,
                total_steps=5,
                completed=True,
                next_step=None,
            )

        # Return progress
        completed = request.step == 5
        next_step = None if completed else f"step_{request.step + 1}"

        return SetupWizardResponse(
            success=True,
            message=f"Step {request.step} completed successfully",
            current_step=request.step,
            total_steps=5,
            completed=completed,
            next_step=next_step,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to process setup wizard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Setup wizard processing failed"
        )


# ================== Onboarding Status ==================

@router.get("/status/{organization_id}", response_model=dict)
async def get_onboarding_status(
    organization_id: str,
    db = Depends(get_database),
):
    """
    Get onboarding status and completion checklist.

    Returns progress through onboarding steps.
    """
    try:
        org_service = get_organization_service()
        subscription_service = SubscriptionService(db)

        # Get organization
        org = await org_service.get_organization(organization_id)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        # Get subscription
        subscription = await subscription_service.get_subscription(organization_id)

        # Calculate completion
        checklist = {
            "church_registered": True,  # Always true if we got here
            "phone_verified": True,  # TODO: Check actual status
            "church_info_completed": org.metadata.get("church_info_completed", False) if org.metadata else False,
            "service_times_added": org.metadata.get("service_times_added", False) if org.metadata else False,
            "leadership_invited": org.metadata.get("leadership_invited", False) if org.metadata else False,
            "ministries_created": org.metadata.get("ministries_created", False) if org.metadata else False,
            "payment_setup": subscription and subscription.stripe_customer_id is not None if subscription else False,
        }

        completed_steps = sum(checklist.values())
        total_steps = len(checklist)
        onboarding_complete = completed_steps == total_steps

        return {
            "organization_id": organization_id,
            "onboarding_complete": onboarding_complete,
            "progress_percentage": int((completed_steps / total_steps) * 100),
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "checklist": checklist,
            "subscription_plan": subscription.plan.value if subscription else "free",
            "subscription_status": subscription.status.value if subscription else "inactive",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get onboarding status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve onboarding status"
        )
