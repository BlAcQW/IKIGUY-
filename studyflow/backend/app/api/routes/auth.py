"""
Authentication routes for StudyFlow.

Handles user registration, login, and profile management.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr

from app.models.user import User, UserCreate, UserUpdate, UserResponse, UserRole
from app.services.user_service import UserService
from app.core.auth import get_current_user, get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    """
    Registration request model.

    Attributes:
        email: User email
        phone: User phone number (optional)
        role: User role
        full_name: User's full name
        grade: Grade level (for students)
        school_id: School ID (optional)
        parent_id: Parent ID (for students, optional)
    """
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: UserRole
    full_name: str
    grade: Optional[int] = None
    school_id: Optional[str] = None
    parent_id: Optional[str] = None


class RegisterResponse(BaseModel):
    """Registration response model."""
    user: UserResponse
    message: str


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Register a new user.

    After Supabase authentication, this endpoint creates the user profile
    in the StudyFlow database.

    Args:
        request: Registration data
        current_user: Current authenticated user from Supabase

    Returns:
        Created user profile

    Raises:
        HTTPException: If user already exists or validation fails
    """
    try:
        # Get Supabase user ID
        supabase_id = current_user.get("sub")
        if not supabase_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid authentication token"
            )

        # Check if user already registered
        existing_user = await UserService.get_user_by_supabase_id(supabase_id)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already registered"
            )

        # Create user
        user_data = UserCreate(
            supabase_id=supabase_id,
            email=request.email or current_user.get("email"),
            phone=request.phone or current_user.get("phone"),
            role=request.role,
            full_name=request.full_name,
            grade=request.grade,
            school_id=request.school_id,
            parent_id=request.parent_id
        )

        user = await UserService.create_user(user_data)

        logger.info(f"User registered: {user.id} ({user.role.value})")

        return RegisterResponse(
            user=UserResponse(
                id=user.id,
                email=user.email,
                phone=user.phone,
                role=user.role,
                full_name=user.full_name,
                grade=user.grade,
                school_id=user.school_id,
                is_active=user.is_active,
                created_at=user.created_at
            ),
            message="User registered successfully"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get current user profile.

    Returns the profile of the currently authenticated user.

    Args:
        current_user_id: Current user's Supabase ID

    Returns:
        User profile

    Raises:
        HTTPException: If user not found
    """
    # Get user by Supabase ID
    user = await UserService.get_user_by_supabase_id(current_user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. Please complete registration."
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        role=user.role,
        full_name=user.full_name,
        grade=user.grade,
        school_id=user.school_id,
        is_active=user.is_active,
        created_at=user.created_at
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    update_data: UserUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Update current user profile.

    Allows user to update their own profile information.

    Args:
        update_data: Fields to update
        current_user_id: Current user's Supabase ID

    Returns:
        Updated user profile

    Raises:
        HTTPException: If user not found or update fails
    """
    # Get user by Supabase ID
    user = await UserService.get_user_by_supabase_id(current_user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    # Update user
    updated_user = await UserService.update_user(user.id, update_data)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

    logger.info(f"User updated: {updated_user.id}")

    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        phone=updated_user.phone,
        role=updated_user.role,
        full_name=updated_user.full_name,
        grade=updated_user.grade,
        school_id=updated_user.school_id,
        is_active=updated_user.is_active,
        created_at=updated_user.created_at
    )


@router.post("/link-student")
async def link_student_to_parent(
    student_email: EmailStr,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Link a student to parent account.

    Allows parents to link their children's accounts.

    Args:
        student_email: Student's email address
        current_user_id: Current user's Supabase ID

    Returns:
        Success message

    Raises:
        HTTPException: If parent/student not found or linking fails
    """
    # Get parent
    parent = await UserService.get_user_by_supabase_id(current_user_id)

    if not parent or parent.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can link students"
        )

    # Get student
    student = await UserService.get_user_by_email(student_email)

    if not student or student.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Link student to parent
    success = await UserService.link_student_to_parent(student.id, parent.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to link student"
        )

    logger.info(f"Student {student.id} linked to parent {parent.id}")

    return {
        "message": f"Student {student.full_name} linked successfully",
        "student_id": student.id
    }


@router.get("/my-students", response_model=List[UserResponse])
async def get_my_students(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get all students linked to current parent.

    Returns list of students for the authenticated parent.

    Args:
        current_user_id: Current user's Supabase ID

    Returns:
        List of linked students

    Raises:
        HTTPException: If parent not found
    """
    # Get parent
    parent = await UserService.get_user_by_supabase_id(current_user_id)

    if not parent or parent.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access student list"
        )

    # Get students
    students = await UserService.get_parent_students(parent.id)

    return [
        UserResponse(
            id=student.id,
            email=student.email,
            phone=student.phone,
            role=student.role,
            full_name=student.full_name,
            grade=student.grade,
            school_id=student.school_id,
            is_active=student.is_active,
            created_at=student.created_at
        )
        for student in students
    ]
