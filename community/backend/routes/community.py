"""
Community management routes for African Language Community Platform.

Handles gamification, leaderboards, proposals, and real-time collaboration.
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, Query, status, Body
from typing import Optional, List, Dict, Any
import json

from models.user_models import User, Leaderboard
from models.responses import DataResponse, ListResponse
from routes.auth import get_current_user
from services.community_service import CommunityService
from services.websocket_service import WebSocketManager

router = APIRouter()
community_service = CommunityService()
websocket_manager = WebSocketManager()


@router.get("/leaderboard", response_model=ListResponse)
async def get_leaderboard(
    timeframe: str = Query("monthly", description="all_time, daily, weekly, monthly"),
    language: Optional[str] = Query(None, description="Filter by language code"),
    family: Optional[str] = Query(None, description="Filter by language family"),
    category: str = Query("total_points", description="Leaderboard category"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Get community leaderboard with various filters.

    Args:
        timeframe: Timeframe for leaderboard (all_time, daily, weekly, monthly)
        language: Optional language code filter
        family: Optional language family filter
        category: Ranking category (total_points, contributions, validations)
        page: Page number
        page_size: Items per page

    Returns:
        ListResponse: Ranked community members
    """
    try:
        # Map timeframe for service compatibility
        tf_map = {"monthly": "monthly", "weekly": "weekly", "daily": "daily", "all": "all_time"}
        tf = tf_map.get(timeframe, timeframe)

        leaderboard_data = await community_service.get_leaderboard(
            category=category,
            language_id=language,  # Service handles None gracefully
            timeframe=tf,
            limit=page_size * page  # Get enough for pagination
        )

        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated_data = leaderboard_data[start:end]
        total_count = len(leaderboard_data)

        return ListResponse.create(
            items=paginated_data,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve leaderboard: {str(e)}"
        )


@router.get("/achievements", response_model=DataResponse)
async def get_community_achievements():
    """
    Get all available community achievements and their requirements.

    Returns:
        DataResponse: List of achievements with descriptions and requirements
    """
    try:
        achievements = await community_service.get_all_achievements()

        return DataResponse(
            data=achievements,
            message="Community achievements retrieved successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve achievements: {str(e)}"
        )


@router.get("/achievements/user", response_model=DataResponse)
async def get_user_achievements(current_user: User = Depends(get_current_user)):
    """
    Get current user's achievements and progress.

    Args:
        current_user: Authenticated user

    Returns:
        DataResponse: User's achievements and progress toward unlockable achievements
    """
    try:
        user_achievements = await community_service.get_user_achievements(
            current_user.id
        )

        return DataResponse(
            data=user_achievements,
            message="User achievements retrieved successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user achievements: {str(e)}"
        )


@router.post("/proposals", response_model=DataResponse)
async def create_community_proposal(
    proposal_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new community governance proposal.

    Args:
        proposal_data: Proposal information (title, description, type, etc.)
        current_user: Authenticated user (must have proposal creation rights)

    Returns:
        DataResponse: Created proposal
    """
    try:
        # Check if user can create proposals
        if not current_user.can_create_proposals:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have proposal creation permissions"
            )

        proposal = await community_service.create_proposal(
            proposer_id=current_user.id,
            proposal_data=proposal_data
        )

        return DataResponse(
            data=proposal,
            message="Community proposal created successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Proposal creation failed: {str(e)}"
        )


@router.get("/proposals", response_model=ListResponse)
async def get_community_proposals(
    status_filter: str = Query("active", description="active, completed, expired"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Get community governance proposals.

    Args:
        status_filter: Filter by proposal status
        page: Page number
        page_size: Items per page

    Returns:
        ListResponse: Community proposals with pagination
    """
    try:
        proposals, total_count = await community_service.get_proposals(
            status_filter=status_filter,
            page=page,
            page_size=page_size
        )

        return ListResponse.create(
            items=proposals,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve proposals: {str(e)}"
        )


@router.post("/proposals/{proposal_id}/vote", response_model=DataResponse)
async def vote_on_proposal(
    proposal_id: str,
    vote_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Vote on a community proposal.

    Args:
        proposal_id: Proposal ID
        vote_data: Vote information (option, comment)
        current_user: Authenticated user

    Returns:
        DataResponse: Vote confirmation and updated proposal status
    """
    try:
        # Check voting eligibility
        can_vote = await community_service.can_user_vote(current_user.id, proposal_id)
        if not can_vote:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User cannot vote on this proposal"
            )

        vote_result = await community_service.cast_vote(
            proposal_id=proposal_id,
            voter_id=current_user.id,
            vote_data=vote_data
        )

        return DataResponse(
            data=vote_result,
            message="Vote cast successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voting failed: {str(e)}"
        )


@router.get("/stats/engagement", response_model=DataResponse)
async def get_community_engagement_stats():
    """
    Get community engagement statistics and health metrics.

    Returns:
        DataResponse: Community engagement statistics
    """
    try:
        engagement_stats = await community_service.get_engagement_statistics()

        return DataResponse(
            data=engagement_stats,
            message="Community engagement statistics retrieved successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve engagement statistics: {str(e)}"
        )


@router.get("/activity/feed", response_model=ListResponse)
async def get_community_activity_feed(
    language_family: Optional[str] = Query(None, description="Filter by language family"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Get community activity feed.

    Args:
        language_family: Optional language family filter
        page: Page number
        page_size: Items per page

    Returns:
        ListResponse: Recent community activities
    """
    try:
        activities, total_count = await community_service.get_activity_feed(
            language_family=language_family,
            page=page,
            page_size=page_size
        )

        return ListResponse.create(
            items=activities,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity feed: {str(e)}"
        )


@router.websocket("/live/{language_family}")
async def websocket_language_family_chat(
    websocket: WebSocket,
    language_family: str,
    current_user: User = Depends(get_current_user)
):
    """
    WebSocket endpoint for real-time language family collaboration.

    Args:
        websocket: WebSocket connection
        language_family: Language family room to join
        current_user: Authenticated user
    """
    await websocket_manager.connect(websocket, language_family, current_user.id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Process message based on type
            if message_data.get("type") == "chat":
                # Broadcast chat message
                await websocket_manager.broadcast_message(
                    language_family,
                    {
                        "type": "chat",
                        "user_id": str(current_user.id),
                        "username": current_user.username or current_user.full_name,
                        "message": message_data.get("message"),
                        "timestamp": message_data.get("timestamp")
                    }
                )

            elif message_data.get("type") == "validation_update":
                # Handle validation status updates
                await websocket_manager.broadcast_validation_update(
                    language_family,
                    message_data.get("submission_id"),
                    message_data.get("status")
                )

            elif message_data.get("type") == "submission_update":
                # Handle new submission notifications
                await websocket_manager.broadcast_submission_update(
                    language_family,
                    message_data
                )

    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket, language_family, current_user.id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket_manager.disconnect(websocket, language_family, current_user.id)


@router.get("/languages/{language_code}/contributors", response_model=ListResponse)
async def get_language_contributors(
    language_code: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Get top contributors for a specific language.

    Args:
        language_code: Language code
        page: Page number
        page_size: Items per page

    Returns:
        ListResponse: Language contributors with statistics
    """
    try:
        contributors, total_count = await community_service.get_language_contributors(
            language_code=language_code,
            page=page,
            page_size=page_size
        )

        return ListResponse.create(
            items=contributors,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve language contributors: {str(e)}"
        )


@router.post("/gamification/award-points", response_model=DataResponse)
async def award_points_manually(
    user_id: str,
    points: int,
    reason: str,
    current_user: User = Depends(get_current_user)
):
    """
    Manually award points to a user (moderator/admin only).

    Args:
        user_id: User to award points to
        points: Number of points to award
        reason: Reason for awarding points
        current_user: Authenticated user with admin rights

    Returns:
        DataResponse: Point award confirmation
    """
    try:
        # Check admin permissions
        if current_user.level not in ["expert", "guardian"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to award points manually"
            )

        award_result = await community_service.award_points_manually(
            user_id=user_id,
            points=points,
            reason=reason,
            awarded_by=current_user.id
        )

        return DataResponse(
            data=award_result,
            message=f"Awarded {points} points to user successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Point award failed: {str(e)}"
        )


@router.get("/channels", response_model=DataResponse)
async def get_language_channels():
    """
    Get all available language community channels.

    Returns:
        DataResponse: List of language channels
    """
    try:
        db = community_service._get_db
        # Get channels from database
        channels_db = await (await db()).community_channels.find(
            {"is_active": True}
        ).to_list(length=None)

        # Convert ObjectIds to strings
        channels = []
        for channel in channels_db:
            channel["_id"] = str(channel["_id"])
            channels.append(channel)

        return DataResponse(
            data={"channels": channels},
            message="Language channels retrieved successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve channels: {str(e)}"
        )


@router.get("/channels/{language_code}")
async def get_channel_by_language(language_code: str):
    """
    Get a specific language community channel.

    Args:
        language_code: Language code

    Returns:
        DataResponse: Channel details
    """
    try:
        db = await community_service._get_db()
        channel = await db.community_channels.find_one({
            "language_code": language_code,
            "is_active": True
        })

        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channel not found for language: {language_code}"
            )

        channel["_id"] = str(channel["_id"])

        return DataResponse(
            data=channel,
            message="Channel retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve channel: {str(e)}"
        )


@router.get("/languages/{language_code}/stats", response_model=DataResponse)
async def get_language_stats(language_code: str):
    """
    Get statistics for a specific language.

    Args:
        language_code: Language code

    Returns:
        DataResponse: Language statistics
    """
    try:
        db = await community_service._get_db()

        # Get language to verify it exists
        language = await db.languages.find_one({"code": language_code})
        if not language:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Language not found: {language_code}"
            )

        # Get submission count
        submissions_count = await db.submissions.count_documents({
            "language_code": language_code
        })

        # Get validation count
        validations_count = await db.validations.count_documents({
            "language_code": language_code
        })

        # Get contributor count
        contributors = await db.submissions.distinct(
            "contributor_id",
            {"language_code": language_code}
        )

        stats = {
            "language_code": language_code,
            "language_name": language.get("name", language_code),
            "submissions_count": submissions_count,
            "validations_count": validations_count,
            "contributors_count": len(contributors),
            "coverage_percent": language.get("coverage_percent", 0)
        }

        return DataResponse(
            data=stats,
            message="Language statistics retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve language stats: {str(e)}"
        )