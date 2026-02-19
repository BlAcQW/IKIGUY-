"""
Conference Analytics API routes for ChurchFlow.

Provides endpoints for analyzing conference attendees by branch, country, and session.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from bson import ObjectId
import logging
import phonenumbers
from phonenumbers import geocoder
import sys
import os

# Add shared services to path
shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../shared'))
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

from app.core.database import get_database
from app.api.dependencies import require_coordinator_or_admin
from app.models.user import User

logger = logging.getLogger(__name__)

# Import Gemini service
try:
    from integration.gemini_service import get_gemini_service
    GEMINI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Gemini service not available: {e}")
    GEMINI_AVAILABLE = False
    get_gemini_service = None

router = APIRouter(tags=["Conference Analytics"])


def get_country_from_phone(phone: str) -> tuple:
    """
    Extract country code and country name from phone number.

    Args:
        phone: Phone number in any format

    Returns:
        Tuple of (country_code, country_name) or ("Unknown", "Unknown") if parsing fails
    """
    try:
        parsed = phonenumbers.parse(phone, None)
        country_code = phonenumbers.region_code_for_number(parsed)
        country_name = geocoder.description_for_number(parsed, "en")
        
        if country_code and country_name:
            return (country_code, country_name)
    except Exception:
        pass
    
    return ("Unknown", "Unknown")


class BranchAnalyticsItem(BaseModel):
    """Single branch analytics item."""
    branch_id: str
    branch_name: str
    branch_location: Optional[str] = None
    branch_region: Optional[str] = None
    total_registrations: int
    percentage: float
    checked_in_count: int
    checked_in_percentage: float
    countries: Dict[str, int] = Field(default_factory=dict)


class CountryAnalyticsItem(BaseModel):
    """Single country analytics item."""
    country_code: str
    country_name: str
    total_registrations: int
    percentage: float
    checked_in_count: int
    checked_in_percentage: float
    branches: Dict[str, int] = Field(default_factory=dict)


class SessionAnalyticsItem(BaseModel):
    """Single session analytics item."""
    session_id: str
    session_name: str
    day_number: int
    day_label: str
    total_checked_in: int
    percentage: float
    unique_attendees: int


class ConferenceAnalyticsResponse(BaseModel):
    """Conference analytics response."""
    conference_id: str
    conference_name: str
    total_registrations: int
    total_checked_in: int
    by_branch: List[BranchAnalyticsItem]
    by_country: List[CountryAnalyticsItem]
    by_session: List[SessionAnalyticsItem]
    top_branches: List[BranchAnalyticsItem]
    top_countries: List[CountryAnalyticsItem]
    top_sessions: List[SessionAnalyticsItem]


@router.get(
    "/conferences/{conference_id}/analytics",
    response_model=ConferenceAnalyticsResponse,
    summary="Get conference analytics",
    description="Get comprehensive analytics for a conference including breakdowns by branch, country, and session."
)
async def get_conference_analytics(
    conference_id: str,
    current_user: User = Depends(require_coordinator_or_admin)
):
    """
    Get comprehensive analytics for a conference.

    Provides breakdowns by:
    - Branch (with country distribution)
    - Country (with branch distribution)
    - Session (check-in statistics)

    Args:
        conference_id: Conference ID
        current_user: Current authenticated user (coordinator or admin)

    Returns:
        ConferenceAnalyticsResponse with all analytics data
    """
    db = get_database()

    try:
        if not ObjectId.is_valid(conference_id):
            raise HTTPException(status_code=400, detail="Invalid conference ID")

        conf_oid = ObjectId(conference_id)

        # Get conference
        conference = await db.conferences.find_one({"_id": conf_oid})
        if not conference:
            raise HTTPException(status_code=404, detail="Conference not found")

        conference_name = conference.get("name", "Unknown Conference")

        # Get all registrations for this conference
        registrations = await db.conference_registrations.find({
            "conference_id": conf_oid,
            "status": "confirmed"
        }).to_list(length=None)

        total_registrations = len(registrations)

        # Get all branches
        branches = {}
        for branch in await db.branches.find({}).to_list(length=None):
            branches[str(branch["_id"])] = {
                "name": branch.get("name"),
                "location": branch.get("location"),
                "region": branch.get("region")
            }

        # Get all sessions
        sessions = {}
        for session in await db.conference_sessions.find({
            "conference_id": conf_oid
        }).to_list(length=None):
            sessions[str(session["_id"])] = {
                "name": session.get("name"),
                "day_number": session.get("day_number"),
                "day_label": session.get("day_label", f"Day {session.get('day_number', 0)}")
            }

        # Get session attendance counts
        session_attendance_counts = {}
        for session_id in sessions.keys():
            count = await db.session_attendance.count_documents({
                "session_id": ObjectId(session_id),
                "conference_id": conf_oid
            })
            session_attendance_counts[session_id] = count

        # Aggregate by branch
        branch_stats = {}
        branch_countries = {}

        # Aggregate by country
        country_stats = {}
        country_branches = {}

        # Track checked-in registrations
        checked_in_reg_ids = set()
        for reg in registrations:
            if reg.get("checked_in", False):
                checked_in_reg_ids.add(str(reg["_id"]))

        total_checked_in = len(checked_in_reg_ids)

        # Process registrations
        for reg in registrations:
            phone = reg.get("user_phone", "")
            branch_id = reg.get("branch_id")
            reg_id = str(reg["_id"])
            is_checked_in = reg_id in checked_in_reg_ids

            # Get country from phone
            country_code, country_name = get_country_from_phone(phone)

            # Process branch statistics
            if branch_id:
                branch_str = str(branch_id)
                if branch_str not in branch_stats:
                    branch_info = branches.get(branch_str, {})
                    branch_stats[branch_str] = {
                        "branch_id": branch_str,
                        "branch_name": branch_info.get("name", "Unknown Branch"),
                        "branch_location": branch_info.get("location"),
                        "branch_region": branch_info.get("region"),
                        "total_registrations": 0,
                        "checked_in_count": 0,
                        "countries": {}
                    }
                    branch_countries[branch_str] = {}

                branch_stats[branch_str]["total_registrations"] += 1
                if is_checked_in:
                    branch_stats[branch_str]["checked_in_count"] += 1

                # Track countries in this branch
                if country_name not in branch_countries[branch_str]:
                    branch_countries[branch_str][country_name] = 0
                branch_countries[branch_str][country_name] += 1

            # Process country statistics
            if country_code not in country_stats:
                country_stats[country_code] = {
                    "country_code": country_code,
                    "country_name": country_name,
                    "total_registrations": 0,
                    "checked_in_count": 0,
                    "branches": {}
                }
                country_branches[country_code] = {}

            country_stats[country_code]["total_registrations"] += 1
            if is_checked_in:
                country_stats[country_code]["checked_in_count"] += 1

            # Track branches in this country
            if branch_id:
                branch_str = str(branch_id)
                branch_name = branches.get(branch_str, {}).get("name", "Unknown")
                if branch_name not in country_branches[country_code]:
                    country_branches[country_code][branch_name] = 0
                country_branches[country_code][branch_name] += 1

        # Calculate percentages and format branch data
        by_branch = []
        for branch_id, stats in branch_stats.items():
            percentage = (stats["total_registrations"] / total_registrations * 100) if total_registrations > 0 else 0
            checked_in_pct = (stats["checked_in_count"] / stats["total_registrations"] * 100) if stats["total_registrations"] > 0 else 0

            by_branch.append(BranchAnalyticsItem(
                branch_id=branch_id,
                branch_name=stats["branch_name"],
                branch_location=stats["branch_location"],
                branch_region=stats["branch_region"],
                total_registrations=stats["total_registrations"],
                percentage=round(percentage, 2),
                checked_in_count=stats["checked_in_count"],
                checked_in_percentage=round(checked_in_pct, 2),
                countries=branch_countries.get(branch_id, {})
            ))

        # Calculate percentages and format country data
        by_country = []
        for country_code, stats in country_stats.items():
            percentage = (stats["total_registrations"] / total_registrations * 100) if total_registrations > 0 else 0
            checked_in_pct = (stats["checked_in_count"] / stats["total_registrations"] * 100) if stats["total_registrations"] > 0 else 0

            by_country.append(CountryAnalyticsItem(
                country_code=country_code,
                country_name=stats["country_name"],
                total_registrations=stats["total_registrations"],
                percentage=round(percentage, 2),
                checked_in_count=stats["checked_in_count"],
                checked_in_percentage=round(checked_in_pct, 2),
                branches=country_branches.get(country_code, {})
            ))

        # Format session data
        by_session = []
        for session_id, session_info in sessions.items():
            attendance_count = session_attendance_counts.get(session_id, 0)
            percentage = (attendance_count / total_registrations * 100) if total_registrations > 0 else 0

            # Get unique attendees for this session
            unique_attendees = await db.session_attendance.distinct(
                "registration_id",
                {"session_id": ObjectId(session_id), "conference_id": conf_oid}
            )

            by_session.append(SessionAnalyticsItem(
                session_id=session_id,
                session_name=session_info["name"],
                day_number=session_info["day_number"],
                day_label=session_info["day_label"],
                total_checked_in=attendance_count,
                percentage=round(percentage, 2),
                unique_attendees=len(unique_attendees)
            ))

        # Get top items (sorted by count, descending)
        top_branches = sorted(by_branch, key=lambda x: x.total_registrations, reverse=True)[:10]
        top_countries = sorted(by_country, key=lambda x: x.total_registrations, reverse=True)[:10]
        top_sessions = sorted(by_session, key=lambda x: x.total_checked_in, reverse=True)[:10]

        return ConferenceAnalyticsResponse(
            conference_id=conference_id,
            conference_name=conference_name,
            total_registrations=total_registrations,
            total_checked_in=total_checked_in,
            by_branch=by_branch,
            by_country=by_country,
            by_session=by_session,
            top_branches=top_branches,
            top_countries=top_countries,
            top_sessions=top_sessions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conference analytics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conference analytics: {str(e)}"
        )


@router.get(
    "/conferences/{conference_id}/analytics/search",
    summary="Search conference analytics",
    description="Search and filter conference analytics by country or branch."
)
async def search_conference_analytics(
    conference_id: str,
    country: Optional[str] = Query(None, description="Filter by country name or code"),
    branch: Optional[str] = Query(None, description="Filter by branch name"),
    current_user: User = Depends(require_coordinator_or_admin)
):
    """
    Search and filter conference analytics.

    Args:
        conference_id: Conference ID
        country: Optional country filter (name or code)
        branch: Optional branch name filter
        current_user: Current authenticated user (coordinator or admin)

    Returns:
        Filtered analytics data
    """
    db = get_database()

    try:
        if not ObjectId.is_valid(conference_id):
            raise HTTPException(status_code=400, detail="Invalid conference ID")

        conf_oid = ObjectId(conference_id)

        # Get conference
        conference = await db.conferences.find_one({"_id": conf_oid})
        if not conference:
            raise HTTPException(status_code=404, detail="Conference not found")

        # Build filter query
        filter_query = {
            "conference_id": conf_oid,
            "status": "confirmed"
        }

        # Apply country filter
        if country:
            # Get all registrations and filter by country
            all_regs = await db.conference_registrations.find(filter_query).to_list(length=None)
            matching_reg_ids = []
            
            for reg in all_regs:
                phone = reg.get("user_phone", "")
                country_code, country_name = get_country_from_phone(phone)
                
                if (country.lower() in country_name.lower() or 
                    country.upper() == country_code):
                    matching_reg_ids.append(reg["_id"])
            
            if matching_reg_ids:
                filter_query["_id"] = {"$in": matching_reg_ids}
            else:
                # No matches, return empty result
                return {
                    "conference_id": conference_id,
                    "conference_name": conference.get("name"),
                    "total_registrations": 0,
                    "registrations": []
                }

        # Apply branch filter
        if branch:
            # Find matching branch IDs
            matching_branches = await db.branches.find({
                "name": {"$regex": branch, "$options": "i"}
            }).to_list(length=None)
            
            if matching_branches:
                branch_ids = [b["_id"] for b in matching_branches]
                if "_id" in filter_query:
                    # Combine with existing filter - filter by branch_id
                    existing_ids = filter_query["_id"]["$in"]
                    # Get registrations that match both country and branch
                    matching_regs = await db.conference_registrations.find({
                        "_id": {"$in": existing_ids},
                        "branch_id": {"$in": branch_ids}
                    }).to_list(length=None)
                    matching_reg_ids = [r["_id"] for r in matching_regs]
                    
                    if matching_reg_ids:
                        filter_query["_id"] = {"$in": matching_reg_ids}
                    else:
                        # No matches, return empty result
                        return {
                            "conference_id": conference_id,
                            "conference_name": conference.get("name"),
                            "total_registrations": 0,
                            "registrations": []
                        }
                else:
                    filter_query["branch_id"] = {"$in": branch_ids}
            else:
                # No matching branches
                return {
                    "conference_id": conference_id,
                    "conference_name": conference.get("name"),
                    "total_registrations": 0,
                    "registrations": []
                }

        # Get filtered registrations
        registrations = await db.conference_registrations.find(filter_query).to_list(length=None)

        # Format response
        results = []
        for reg in registrations:
            phone = reg.get("user_phone", "")
            country_code, country_name = get_country_from_phone(phone)
            
            branch_id = reg.get("branch_id")
            branch_name = None
            if branch_id:
                branch = await db.branches.find_one({"_id": branch_id})
                if branch:
                    branch_name = branch.get("name")

            results.append({
                "id": str(reg["_id"]),
                "user_name": reg.get("user_name"),
                "user_phone": phone,
                "user_email": reg.get("user_email"),
                "country_code": country_code,
                "country_name": country_name,
                "branch_id": str(branch_id) if branch_id else None,
                "branch_name": branch_name,
                "church_name": reg.get("church_name"),
                "registration_code": reg.get("registration_code"),
                "checked_in": reg.get("checked_in", False),
                "status": reg.get("status")
            })

        return {
            "conference_id": conference_id,
            "conference_name": conference.get("name"),
            "total_registrations": len(results),
            "filters": {
                "country": country,
                "branch": branch
            },
            "registrations": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search conference analytics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search conference analytics: {str(e)}"
        )


class SummaryRequest(BaseModel):
    """Request model for generating analytics summary."""
    summary_type: str = Field(..., description="Type of summary to generate")
    custom_prompt: Optional[str] = Field(None, description="Custom prompt for summary generation")


class SummaryResponse(BaseModel):
    """Response model for analytics summary."""
    summary: str
    summary_type: str
    generated_at: str


@router.post(
    "/conferences/{conference_id}/analytics/summary",
    response_model=SummaryResponse,
    summary="Generate AI summary of conference analytics",
    description="Generate an AI-powered summary of conference analytics using Gemini."
)
async def generate_analytics_summary(
    conference_id: str,
    request: SummaryRequest,
    current_user: User = Depends(require_coordinator_or_admin)
):
    """
    Generate an AI-powered summary of conference analytics.

    Args:
        conference_id: Conference ID
        request: Summary request with type and optional custom prompt
        current_user: Current authenticated user (coordinator or admin)

    Returns:
        SummaryResponse with generated summary
    """
    if not GEMINI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Gemini service not available. Please configure GEMINI_API_KEY."
        )

    db = get_database()

    try:
        if not ObjectId.is_valid(conference_id):
            raise HTTPException(status_code=400, detail="Invalid conference ID")

        conf_oid = ObjectId(conference_id)

        # Get conference
        conference = await db.conferences.find_one({"_id": conf_oid})
        if not conference:
            raise HTTPException(status_code=404, detail="Conference not found")

        conference_name = conference.get("name", "Unknown Conference")

        # Get analytics data
        analytics_response = await get_conference_analytics(conference_id, current_user)
        analytics_data = analytics_response.dict()

        # Build summary prompt based on type
        summary_prompts = {
            "overview": f"""
Generate a comprehensive overview summary of the conference analytics for "{conference_name}".

Key Metrics:
- Total Registrations: {analytics_data['total_registrations']}
- Total Checked In: {analytics_data['total_checked_in']}
- Branches Represented: {len(analytics_data['by_branch'])}
- Countries Represented: {len(analytics_data['by_country'])}

Top 5 Branches:
{chr(10).join([f"- {b['branch_name']}: {b['total_registrations']} registrations ({b['percentage']:.1f}%)" for b in analytics_data['top_branches'][:5]])}

Top 5 Countries:
{chr(10).join([f"- {c['country_name']}: {c['total_registrations']} registrations ({c['percentage']:.1f}%)" for c in analytics_data['top_countries'][:5]])}

Provide a concise, professional summary highlighting key insights, trends, and notable statistics.
""",
            "branch_analysis": f"""
Analyze the branch distribution for "{conference_name}".

Branch Statistics:
{chr(10).join([f"- {b['branch_name']} ({b.get('branch_location', 'N/A')}): {b['total_registrations']} registrations ({b['percentage']:.1f}%), {b['checked_in_count']} checked in ({b['checked_in_percentage']:.1f}%)" for b in analytics_data['by_branch']])}

Provide insights on:
1. Which branches have the highest participation
2. Check-in rates by branch
3. Geographic distribution patterns
4. Any notable trends or outliers
""",
            "country_analysis": f"""
Analyze the country distribution for "{conference_name}".

Country Statistics:
{chr(10).join([f"- {c['country_name']} ({c['country_code']}): {c['total_registrations']} registrations ({c['percentage']:.1f}%), {c['checked_in_count']} checked in ({c['checked_in_percentage']:.1f}%)" for c in analytics_data['by_country']])}

Provide insights on:
1. International reach and diversity
2. Top contributing countries
3. Check-in rates by country
4. Geographic distribution patterns
""",
            "session_attendance": f"""
Analyze session attendance for "{conference_name}".

Session Statistics:
{chr(10).join([f"- {s['session_name']} ({s['day_label']}): {s['total_checked_in']} check-ins ({s['percentage']:.1f}%), {s['unique_attendees']} unique attendees" for s in analytics_data['by_session']])}

Provide insights on:
1. Most attended sessions
2. Attendance trends across days
3. Session engagement patterns
4. Recommendations for future sessions
""",
            "check_in_performance": f"""
Analyze check-in performance for "{conference_name}".

Overall Check-in Stats:
- Total Registrations: {analytics_data['total_registrations']}
- Total Checked In: {analytics_data['total_checked_in']}
- Overall Check-in Rate: {(analytics_data['total_checked_in'] / analytics_data['total_registrations'] * 100) if analytics_data['total_registrations'] > 0 else 0:.1f}%

Branch Check-in Rates:
{chr(10).join([f"- {b['branch_name']}: {b['checked_in_count']}/{b['total_registrations']} ({b['checked_in_percentage']:.1f}%)" for b in analytics_data['top_branches'][:10]])}

Provide insights on:
1. Overall check-in performance
2. Branches with best/worst check-in rates
3. Potential issues or patterns
4. Recommendations for improvement
""",
            "custom": request.custom_prompt or "Generate a summary of the conference analytics."
        }

        # Get the prompt
        if request.summary_type in summary_prompts:
            prompt = summary_prompts[request.summary_type]
        else:
            # Use custom prompt or default
            prompt = request.custom_prompt or summary_prompts["overview"]

        # Add analytics context to custom prompts
        if request.summary_type == "custom" and request.custom_prompt:
            prompt = f"""
Analytics Data for "{conference_name}":
- Total Registrations: {analytics_data['total_registrations']}
- Total Checked In: {analytics_data['total_checked_in']}
- Branches: {len(analytics_data['by_branch'])}
- Countries: {len(analytics_data['by_country'])}
- Sessions: {len(analytics_data['by_session'])}

User Request: {request.custom_prompt}

Please provide a detailed analysis based on the above data.
"""

        # Get Gemini service and generate summary
        gemini_service = get_gemini_service()
        
        if not gemini_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Gemini API key not configured. Please set GEMINI_API_KEY environment variable."
            )

        result = await gemini_service.generate_content(
            prompt=prompt,
            temperature=0.7,
            max_output_tokens=2000,
            timeout=60.0
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail="Failed to generate summary from Gemini"
            )

        from datetime import datetime
        return SummaryResponse(
            summary=result["content"],
            summary_type=request.summary_type,
            generated_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate analytics summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate analytics summary: {str(e)}"
        )

