"""
Feedback API for bug reports and user feedback.

Allows users to report bugs directly from the app,
which are sent to Slack and Linear for tracking.

Uses centralized bug report service from apps.shared.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from apps.shared.services.bug_report_service import submit_bug_report as shared_submit_bug_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


class BugReport(BaseModel):
    """Bug report submission from frontend."""
    title: str
    description: str
    type: str  # bug, crash, ui, feature, other
    url: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    browser: Optional[str] = None
    timestamp: str


@router.post("/bug-report")
async def submit_bug_report_endpoint(
    bug_report: BugReport
) -> dict:
    """
    Submit a bug report.

    The report is:
    1. Sent to Slack for immediate notification
    2. Created as an issue in Linear for project management

    Args:
        bug_report: Bug report details

    Returns:
        Success message with Linear issue details
    """
    try:
        # Use centralized bug report service
        result = await shared_submit_bug_report(
            title=bug_report.title,
            description=bug_report.description,
            bug_type=bug_report.type,
            url=bug_report.url,
            user_email=bug_report.user_email,
            user_id=bug_report.user_id,
            browser=bug_report.browser,
            timestamp=bug_report.timestamp,
            app_name="KasaAI Core"
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Failed to submit bug report")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting bug report: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to submit bug report. Please try again or contact support."
        )
