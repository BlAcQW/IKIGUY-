"""
Centralized Bug Report Service for all KasaAI applications.

This service handles bug report submissions with:
- Slack webhook notifications
- Linear issue creation
- Consistent formatting across all apps

Usage:
    from apps.shared.services.bug_report_service import submit_bug_report

    result = await submit_bug_report(
        title="Login button not working",
        description="When I click login, nothing happens",
        bug_type="bug",
        url="https://kasaai.ailabsafrica.com/auth",
        user_email="user@example.com",
        user_id="12345",
        browser="Mozilla/5.0...",
    )
"""

import logging
import os
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)

# Import Linear service from same directory
try:
    from apps.shared.services.linear_service import get_linear_service
except ImportError:
    from .linear_service import get_linear_service


async def send_to_slack(
    title: str,
    description: str,
    bug_type: str,
    url: str,
    user_email: Optional[str] = None,
    user_id: Optional[str] = None,
    browser: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> bool:
    """
    Send bug report to Slack via webhook.

    Args:
        title: Bug report title
        description: Bug description
        bug_type: Type of bug (bug, crash, ui, feature, other)
        url: URL where bug occurred
        user_email: Reporter's email
        user_id: Reporter's user ID
        browser: Browser user agent
        timestamp: ISO timestamp of report

    Returns:
        True if successful, False otherwise
    """
    webhook_url = os.getenv(
        'SLACK_BUG_REPORT_WEBHOOK_URL',
        'https://hooks.slack.com/services/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'
    )

    if not webhook_url:
        logger.warning("SLACK_BUG_REPORT_WEBHOOK_URL not configured.")
        return False

    try:
        # Map type to emoji
        type_emoji = {
            'bug': '🐛',
            'crash': '💥',
            'ui': '🎨',
            'feature': '💡',
            'other': '❓'
        }
        emoji = type_emoji.get(bug_type, '🐛')

        # Format Slack message with rich blocks
        slack_message = {
            "text": f"{emoji} New Bug Report: {title}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} Bug Report: {title}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Type:*\n{bug_type.capitalize()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Reported By:*\n{user_email or 'Anonymous'}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Page:*\n{url}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:*\n{timestamp or 'N/A'}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Description:*\n{description}"
                    }
                }
            ]
        }

        # Add user ID if available
        if user_id:
            slack_message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*User ID:* `{user_id}`"
                }
            })

        # Add browser info if available
        if browser:
            slack_message["blocks"].append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Browser: {browser[:100]}..."
                    }
                ]
            })

        # Send to Slack
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=slack_message,
                timeout=10.0
            )

            if response.status_code == 200:
                logger.info(f"Bug report sent to Slack: {title}")
                return True
            else:
                logger.error(f"Failed to send to Slack. Status: {response.status_code}")
                return False

    except Exception as e:
        logger.error(f"Error sending bug report to Slack: {e}")
        return False


async def submit_bug_report(
    title: str,
    description: str,
    bug_type: str = 'bug',
    url: str = '',
    user_email: Optional[str] = None,
    user_id: Optional[str] = None,
    browser: Optional[str] = None,
    timestamp: Optional[str] = None,
    app_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Submit a bug report with Slack and Linear integration.

    This is the main entry point for all apps to submit bug reports.

    Args:
        title: Bug report title
        description: Bug description
        bug_type: Type of bug (bug, crash, ui, feature, other)
        url: URL where bug occurred
        user_email: Reporter's email
        user_id: Reporter's user ID
        browser: Browser user agent
        timestamp: ISO timestamp of report
        app_name: Name of the app reporting the bug (e.g., "KasaAI", "ChurchFlow")

    Returns:
        Dictionary with success status and details

    Example:
        result = await submit_bug_report(
            title="Cannot save settings",
            description="When clicking save, nothing happens",
            bug_type="bug",
            url="https://kasaai.ailabsafrica.com/settings",
            user_email="user@example.com",
            app_name="KasaAI B2C Portal"
        )
    """
    try:
        # Add app name to title if provided
        full_title = f"[{app_name}] {title}" if app_name else title

        # Send to Slack (non-blocking, don't fail if Slack fails)
        slack_sent = await send_to_slack(
            title=full_title,
            description=description,
            bug_type=bug_type,
            url=url,
            user_email=user_email,
            user_id=user_id,
            browser=browser,
            timestamp=timestamp,
        )

        # Create Linear issue (non-blocking, don't fail if Linear fails)
        linear_service = get_linear_service()
        linear_issue = await linear_service.create_issue(
            title=full_title,
            description=description,
            bug_type=bug_type,
            metadata={
                'user_email': user_email,
                'url': url,
                'browser': browser,
                'timestamp': timestamp,
                'user_id': user_id,
                'app_name': app_name,
            }
        )

        # Build response
        result = {
            "success": True,
            "message": "Bug report submitted successfully. Thank you!",
            "slack_sent": slack_sent,
        }

        if linear_issue:
            result["linear_issue"] = linear_issue
            logger.info(f"Linear issue created: {linear_issue.get('identifier')}")

        return result

    except Exception as e:
        logger.error(f"Error submitting bug report: {e}")
        return {
            "success": False,
            "message": f"Failed to submit bug report: {str(e)}",
            "slack_sent": False,
        }
