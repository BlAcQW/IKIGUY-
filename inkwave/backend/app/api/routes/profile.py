"""
User Profile API Routes.

Endpoints for managing user profiles and preferences.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from pydantic import BaseModel, Field, HttpUrl
import logging

from app.core.database import Database
from app.services.user_service import UserService
from apps.shared.auth.supabase_auth import get_current_user

logger = logging.getLogger(__name__)


# Pydantic schemas for requests
class VoicePreferencesUpdate(BaseModel):
    """Voice preferences update schema."""

    provider_id: Optional[str] = None
    voice_id: Optional[str] = None
    speed: Optional[float] = Field(None, ge=0.5, le=2.0)
    language: Optional[str] = None
    voice_clone_reference: Optional[str] = None


class InteractionPreferencesUpdate(BaseModel):
    """Interaction preferences update schema."""

    explanation_depth: Optional[str] = Field(None, pattern="^(brief|detailed)$")
    discussion_topics: Optional[list[str]] = None


class ProfileUpdate(BaseModel):
    """User profile update schema."""

    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[str] = None  # YYYY-MM-DD format
    preferred_voice: Optional[str] = None
    playback_speed: Optional[float] = Field(None, ge=0.5, le=2.0)
    reading_level: Optional[str] = Field(
        None, pattern="^(beginner|intermediate|advanced)$"
    )
    voice_preferences: Optional[VoicePreferencesUpdate] = None
    interaction_preferences: Optional[InteractionPreferencesUpdate] = None


class AvatarUrlUpdate(BaseModel):
    """Avatar URL update schema."""

    avatar_url: HttpUrl = Field(..., description="Avatar image URL from the web")


class PrivacySettingsUpdate(BaseModel):
    """Privacy settings update schema."""

    profile_visibility: Optional[str] = Field(
        None, pattern="^(public|followers_only|private)$"
    )
    show_currently_reading: Optional[bool] = None
    show_reading_history: Optional[bool] = None
    show_library: Optional[bool] = None
    show_listening_stats: Optional[bool] = None
    show_followers_list: Optional[bool] = None
    show_following_list: Optional[bool] = None
    show_follower_count: Optional[bool] = None
    show_following_count: Optional[bool] = None
    appear_in_leaderboard: Optional[bool] = None
    leaderboard_display_mode: Optional[str] = Field(
        None, pattern="^(opt_out|anonymous|full_profile)$"
    )
    discoverable_by_search: Optional[bool] = None
    allow_follow_requests: Optional[bool] = None
    require_follow_approval: Optional[bool] = None


# Initialize router
router = APIRouter(prefix="/profile", tags=["Profile"])


# Dependency to get user service
def get_user_service() -> UserService:
    """
    Get UserService instance.

    Returns:
        UserService: User service instance
    """
    db = Database.get_database()
    return UserService(db)


@router.get("", summary="Get current user profile")
async def get_profile(
    user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get current user's profile and preferences.

    Returns:
        User profile with all settings including:
        - Basic user info (email, display_name, avatar_url)
        - Voice preferences (provider, voice, speed, language)
        - Reading preferences (reading_level)
        - Interaction preferences (explanation_depth, discussion_topics)

    Requires authentication.
    """
    user_id = user["id"]

    # Get or create user profile
    user_profile = await user_service.get_or_create_user(
        user_id=user_id,
        email=user.get("email", ""),
        display_name=user.get("display_name"),
        avatar_url=user.get("avatar_url"),
    )

    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    # Return profile
    return {
        "user_id": user_profile.user_id,
        "email": user_profile.email,
        "display_name": user_profile.display_name,
        "avatar_url": user_profile.avatar_url,
        "profile": {
            "preferred_voice": user_profile.profile.preferred_voice,
            "playback_speed": user_profile.profile.playback_speed,
            "reading_level": user_profile.profile.reading_level,
            "voice_preferences": {
                "provider_id": user_profile.profile.voice_preferences.provider_id,
                "voice_id": user_profile.profile.voice_preferences.voice_id,
                "speed": user_profile.profile.voice_preferences.speed,
                "language": user_profile.profile.voice_preferences.language,
                "voice_clone_reference": user_profile.profile.voice_preferences.voice_clone_reference,
            },
            "interaction_preferences": {
                "explanation_depth": user_profile.profile.interaction_preferences.explanation_depth,
                "discussion_topics": user_profile.profile.interaction_preferences.discussion_topics,
            },
        },
        "wallet_id": user_profile.wallet_id,
        "credits": user_profile.credits,
        "is_admin": user_profile.is_admin,
        "role": user_profile.role.value if hasattr(user_profile.role, 'value') else str(user_profile.role),
        "created_at": user_profile.created_at.isoformat(),
        "last_active": user_profile.last_active.isoformat(),
    }


@router.put("", summary="Update user profile")
async def update_profile(
    updates: ProfileUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update current user's profile and preferences.

    Accepts partial updates - only provided fields will be updated.

    Body:
        - display_name: User display name
        - avatar_url: User avatar URL
        - preferred_voice: Preferred voice (legacy)
        - playback_speed: Playback speed (0.5 - 2.0)
        - reading_level: Reading level (beginner/intermediate/advanced)
        - voice_preferences: Voice preferences object
        - interaction_preferences: Interaction preferences object

    Returns:
        Updated user profile

    Requires authentication.
    """
    user_id = user["id"]

    # Convert to dict and remove None values
    update_dict = updates.model_dump(exclude_none=True)

    # Update profile
    updated_user = await user_service.update_user_profile(user_id, update_dict)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    # Return updated profile
    return {
        "user_id": updated_user.user_id,
        "email": updated_user.email,
        "display_name": updated_user.display_name,
        "avatar_url": updated_user.avatar_url,
        "profile": {
            "preferred_voice": updated_user.profile.preferred_voice,
            "playback_speed": updated_user.profile.playback_speed,
            "reading_level": updated_user.profile.reading_level,
            "voice_preferences": {
                "provider_id": updated_user.profile.voice_preferences.provider_id,
                "voice_id": updated_user.profile.voice_preferences.voice_id,
                "speed": updated_user.profile.voice_preferences.speed,
                "language": updated_user.profile.voice_preferences.language,
                "voice_clone_reference": updated_user.profile.voice_preferences.voice_clone_reference,
            },
            "interaction_preferences": {
                "explanation_depth": updated_user.profile.interaction_preferences.explanation_depth,
                "discussion_topics": updated_user.profile.interaction_preferences.discussion_topics,
            },
        },
        "wallet_id": updated_user.wallet_id,
        "credits": updated_user.credits,
        "is_admin": updated_user.is_admin,
        "created_at": updated_user.created_at.isoformat(),
        "last_active": updated_user.last_active.isoformat(),
    }


@router.put("/voice-preferences", summary="Update voice preferences")
async def update_voice_preferences(
    preferences: VoicePreferencesUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update voice preferences only.

    Body:
        - provider_id: TTS provider ID
        - voice_id: Voice identifier
        - speed: Playback speed (0.5 - 2.0)
        - language: Language code (e.g., 'en', 'es', 'fr')
        - voice_clone_reference: URL to reference audio for cloning

    Returns:
        Updated voice preferences

    Requires authentication.
    """
    user_id = user["id"]

    # Convert to dict and remove None values
    prefs_dict = preferences.model_dump(exclude_none=True)

    # Update voice preferences
    updated_user = await user_service.update_voice_preferences(user_id, prefs_dict)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    # Return updated voice preferences
    return {
        "provider_id": updated_user.profile.voice_preferences.provider_id,
        "voice_id": updated_user.profile.voice_preferences.voice_id,
        "speed": updated_user.profile.voice_preferences.speed,
        "language": updated_user.profile.voice_preferences.language,
        "voice_clone_reference": updated_user.profile.voice_preferences.voice_clone_reference,
    }


@router.put("/interaction-preferences", summary="Update interaction preferences")
async def update_interaction_preferences(
    preferences: InteractionPreferencesUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update interaction preferences only.

    Body:
        - explanation_depth: Explanation depth (brief or detailed)
        - discussion_topics: List of preferred discussion topics

    Returns:
        Updated interaction preferences

    Requires authentication.
    """
    user_id = user["id"]

    # Convert to dict and remove None values
    prefs_dict = preferences.model_dump(exclude_none=True)

    # Update interaction preferences
    updated_user = await user_service.update_interaction_preferences(
        user_id, prefs_dict
    )

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    # Return updated interaction preferences
    return {
        "explanation_depth": updated_user.profile.interaction_preferences.explanation_depth,
        "discussion_topics": updated_user.profile.interaction_preferences.discussion_topics,
    }


@router.put("/reading-level", summary="Update reading level")
async def update_reading_level(
    reading_level: str,
    user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update reading level preference.

    Query Parameters:
        - reading_level: Reading level (beginner, intermediate, or advanced)

    Returns:
        Updated reading level

    Requires authentication.
    """
    user_id = user["id"]

    # Validate reading level
    valid_levels = ["beginner", "intermediate", "advanced"]
    if reading_level not in valid_levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid reading level. Must be one of: {', '.join(valid_levels)}",
        )

    # Update reading level
    updated_user = await user_service.update_reading_level(user_id, reading_level)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    # Return updated reading level
    return {"reading_level": updated_user.profile.reading_level}


@router.post("/avatar/upload", summary="Upload avatar image")
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Upload avatar image file.

    Accepts image files (JPEG, PNG, WebP) up to 5MB.

    Returns:
        Avatar URL and success message

    Requires authentication.
    """
    user_id = user["id"]

    try:
        # Construct base URL from request
        base_url = str(request.base_url).rstrip("/")

        # Upload avatar
        avatar_url = await user_service.upload_avatar(user_id, file, base_url)

        return {
            "avatar_url": avatar_url,
            "message": "Avatar uploaded successfully",
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Avatar upload failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar",
        )


@router.put("/avatar/url", summary="Set avatar from URL")
async def update_avatar_url(
    avatar_data: AvatarUrlUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Set avatar from web URL.

    Accepts a URL to an image file on the web.

    Body:
        - avatar_url: HTTP/HTTPS URL to avatar image

    Returns:
        Success message with avatar URL

    Requires authentication.
    """
    user_id = user["id"]

    try:
        # Update avatar URL
        updated_user = await user_service.update_user_profile(
            user_id, {"avatar_url": str(avatar_data.avatar_url)}
        )

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found",
            )

        return {
            "avatar_url": updated_user.avatar_url,
            "message": "Avatar URL updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar URL update failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update avatar URL",
        )


@router.get("/stats", summary="Get user reading statistics")
async def get_stats(
    user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get user reading statistics.

    Returns:
        - books_started: Number of books started
        - questions_asked: Number of questions asked
        - listening_time_minutes: Total listening time in minutes

    Requires authentication.
    """
    user_id = user.get("id") or user.get("user_id")
    
    # Fallback to other possible user ID fields
    if not user_id:
        user_id = user.get("sub") or user.get("tenant_id") or user.get("account_id")

    logger.info(f"Getting stats for user_id: {user_id} (from user keys: {list(user.keys())})")

    try:
        # Get user stats
        stats = await user_service.get_user_stats(user_id)
        
        logger.info(f"Stats for user {user_id}: listening_time_minutes={stats.get('listening_time_minutes', 0)}")

        return stats

    except Exception as e:
        logger.error(f"Failed to get stats for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics",
        )


@router.get("/privacy", summary="Get privacy settings")
async def get_privacy_settings(
    user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get current user's privacy settings.

    Returns:
        Privacy settings for social features

    Requires authentication.
    """
    user_id = user["id"]

    # Get user profile
    user_profile = await user_service.get_or_create_user(
        user_id=user_id,
        email=user.get("email", ""),
        display_name=user.get("display_name"),
        avatar_url=user.get("avatar_url"),
    )

    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    # Return privacy settings
    privacy = user_profile.privacy_settings
    return {
        "profile_visibility": privacy.profile_visibility,
        "show_currently_reading": privacy.show_currently_reading,
        "show_reading_history": privacy.show_reading_history,
        "show_library": privacy.show_library,
        "show_listening_stats": privacy.show_listening_stats,
        "show_followers_list": privacy.show_followers_list,
        "show_following_list": privacy.show_following_list,
        "show_follower_count": privacy.show_follower_count,
        "show_following_count": privacy.show_following_count,
        "appear_in_leaderboard": privacy.appear_in_leaderboard,
        "leaderboard_display_mode": privacy.leaderboard_display_mode,
        "discoverable_by_search": privacy.discoverable_by_search,
        "allow_follow_requests": privacy.allow_follow_requests,
        "require_follow_approval": privacy.require_follow_approval,
        "updated_at": privacy.updated_at.isoformat(),
    }


@router.put("/privacy", summary="Update privacy settings")
async def update_privacy_settings(
    settings: PrivacySettingsUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update privacy settings.

    Allows granular control over what information is visible to other users.

    Body:
        - profile_visibility: Profile visibility (public/followers_only/private)
        - show_currently_reading: Show books currently reading
        - show_reading_history: Show completed books
        - show_library: Show entire library
        - show_listening_stats: Show listening hours/stats
        - show_followers_list: Allow others to see followers list
        - show_following_list: Allow others to see following list
        - show_follower_count: Show follower count
        - show_following_count: Show following count
        - appear_in_leaderboard: Opt into leaderboard
        - leaderboard_display_mode: How to appear (opt_out/anonymous/full_profile)
        - discoverable_by_search: Can be found via search
        - allow_follow_requests: Allow others to follow
        - require_follow_approval: Require approval for follows

    Returns:
        Updated privacy settings

    Requires authentication.
    """
    user_id = user["id"]

    # Convert to dict and remove None values
    settings_dict = settings.model_dump(exclude_none=True)

    if not settings_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No settings provided",
        )

    # Update privacy settings in database
    from datetime import datetime
    db = Database.get_database()

    # Build update query
    update_query = {}
    for key, value in settings_dict.items():
        update_query[f"privacy_settings.{key}"] = value

    update_query["privacy_settings.updated_at"] = datetime.utcnow()

    # Update user
    result = await db.users.find_one_and_update(
        {"user_id": user_id},
        {"$set": update_query},
        return_document=True,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    # Return updated settings
    privacy = result.get("privacy_settings", {})
    return {
        "profile_visibility": privacy.get("profile_visibility"),
        "show_currently_reading": privacy.get("show_currently_reading"),
        "show_reading_history": privacy.get("show_reading_history"),
        "show_library": privacy.get("show_library"),
        "show_listening_stats": privacy.get("show_listening_stats"),
        "show_followers_list": privacy.get("show_followers_list"),
        "show_following_list": privacy.get("show_following_list"),
        "show_follower_count": privacy.get("show_follower_count"),
        "show_following_count": privacy.get("show_following_count"),
        "appear_in_leaderboard": privacy.get("appear_in_leaderboard"),
        "leaderboard_display_mode": privacy.get("leaderboard_display_mode"),
        "discoverable_by_search": privacy.get("discoverable_by_search"),
        "allow_follow_requests": privacy.get("allow_follow_requests"),
        "require_follow_approval": privacy.get("require_follow_approval"),
        "updated_at": privacy.get("updated_at"),
    }


@router.put("/privacy/preset/{preset}", summary="Apply privacy preset")
async def apply_privacy_preset(
    preset: str,
    user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Apply a privacy preset (quick privacy configuration).

    Presets:
    - private: All features disabled, profile private
    - friends: Visible to followers only, some features enabled
    - public: Public profile, all features enabled

    Path Parameters:
        - preset: Preset name (private/friends/public)

    Returns:
        Updated privacy settings

    Requires authentication.
    """
    user_id = user["id"]

    # Validate preset
    valid_presets = ["private", "friends", "public"]
    if preset not in valid_presets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid preset. Must be one of: {', '.join(valid_presets)}",
        )

    # Define presets
    from datetime import datetime
    presets = {
        "private": {
            "profile_visibility": "private",
            "show_currently_reading": False,
            "show_reading_history": False,
            "show_library": False,
            "show_listening_stats": False,
            "show_followers_list": False,
            "show_following_list": False,
            "show_follower_count": False,
            "show_following_count": False,
            "appear_in_leaderboard": False,
            "leaderboard_display_mode": "opt_out",
            "discoverable_by_search": False,
            "allow_follow_requests": False,
            "require_follow_approval": False,
        },
        "friends": {
            "profile_visibility": "followers_only",
            "show_currently_reading": True,
            "show_reading_history": True,
            "show_library": False,
            "show_listening_stats": True,
            "show_followers_list": True,
            "show_following_list": True,
            "show_follower_count": True,
            "show_following_count": True,
            "appear_in_leaderboard": True,
            "leaderboard_display_mode": "full_profile",
            "discoverable_by_search": True,
            "allow_follow_requests": True,
            "require_follow_approval": False,
        },
        "public": {
            "profile_visibility": "public",
            "show_currently_reading": True,
            "show_reading_history": True,
            "show_library": True,
            "show_listening_stats": True,
            "show_followers_list": True,
            "show_following_list": True,
            "show_follower_count": True,
            "show_following_count": True,
            "appear_in_leaderboard": True,
            "leaderboard_display_mode": "full_profile",
            "discoverable_by_search": True,
            "allow_follow_requests": True,
            "require_follow_approval": False,
        },
    }

    settings = presets[preset]

    # Update privacy settings
    db = Database.get_database()

    update_query = {}
    for key, value in settings.items():
        update_query[f"privacy_settings.{key}"] = value

    update_query["privacy_settings.updated_at"] = datetime.utcnow()

    # Update user
    result = await db.users.find_one_and_update(
        {"user_id": user_id},
        {"$set": update_query},
        return_document=True,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    logger.info(f"Applied privacy preset '{preset}' for user {user_id}")

    # Return updated settings
    privacy = result.get("privacy_settings", {})
    return {
        "preset": preset,
        "settings": {
            "profile_visibility": privacy.get("profile_visibility"),
            "show_currently_reading": privacy.get("show_currently_reading"),
            "show_reading_history": privacy.get("show_reading_history"),
            "show_library": privacy.get("show_library"),
            "show_listening_stats": privacy.get("show_listening_stats"),
            "show_followers_list": privacy.get("show_followers_list"),
            "show_following_list": privacy.get("show_following_list"),
            "show_follower_count": privacy.get("show_follower_count"),
            "show_following_count": privacy.get("show_following_count"),
            "appear_in_leaderboard": privacy.get("appear_in_leaderboard"),
            "leaderboard_display_mode": privacy.get("leaderboard_display_mode"),
            "discoverable_by_search": privacy.get("discoverable_by_search"),
            "allow_follow_requests": privacy.get("allow_follow_requests"),
            "require_follow_approval": privacy.get("require_follow_approval"),
            "updated_at": privacy.get("updated_at"),
        },
    }
