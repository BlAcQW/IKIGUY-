"""
Linear API integration service for creating and managing issues.

This service handles all interactions with the Linear API,
including creating issues from bug reports.
"""

import logging
import os
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class LinearService:
    """Service for interacting with Linear API via GraphQL."""

    def __init__(self):
        """Initialize Linear service with API credentials."""
        self.api_key = os.getenv('LINEAR_API_KEY', 'lin_api_WV0znMAxWXISYSzHIqHfOm6bPhTg7EUZsr7LuW1e')
        self.team_id = os.getenv('LINEAR_TEAM_ID')  # Optional, can be set in .env
        self.todo_state_id = os.getenv('LINEAR_TODO_STATE_ID')  # Optional
        self.bug_label_id = os.getenv('LINEAR_BUG_LABEL_ID')  # Optional
        self.api_url = 'https://api.linear.app/graphql'

        if not self.api_key:
            logger.warning("LINEAR_API_KEY not configured. Linear integration disabled.")

    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for Linear API requests.

        Returns:
            Dictionary of headers including authorization.
        """
        return {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }

    def _map_bug_type_to_priority(self, bug_type: str) -> int:
        """
        Map bug report type to Linear priority.

        Args:
            bug_type: Type of bug (bug, crash, ui, feature, other)

        Returns:
            Priority level (1=urgent, 2=high, 3=medium, 4=low)
        """
        priority_map = {
            'crash': 1,  # Urgent
            'bug': 2,    # High
            'ui': 3,     # Medium
            'feature': 4,  # Low
            'other': 3   # Medium
        }
        return priority_map.get(bug_type, 3)

    async def create_issue(
        self,
        title: str,
        description: str,
        bug_type: str = 'bug',
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new issue in Linear.

        Args:
            title: Issue title
            description: Issue description
            bug_type: Type of bug report
            metadata: Additional metadata (user_email, url, browser, etc.)

        Returns:
            Created issue data including ID and URL, or None if failed
        """
        if not self.api_key:
            logger.warning("Linear API key not configured. Skipping issue creation.")
            return None

        try:
            # Build enhanced description with metadata
            full_description = self._build_description(description, metadata)

            # Determine priority based on bug type
            priority = self._map_bug_type_to_priority(bug_type)

            # Build GraphQL mutation
            mutation = """
            mutation CreateIssue($input: IssueCreateInput!) {
                issueCreate(input: $input) {
                    success
                    issue {
                        id
                        identifier
                        title
                        url
                    }
                }
            }
            """

            # Build input variables
            input_data = {
                "title": title,
                "description": full_description,
                "priority": priority,
            }

            # Add optional fields if configured
            if self.team_id:
                input_data["teamId"] = self.team_id
            if self.todo_state_id:
                input_data["stateId"] = self.todo_state_id
            if self.bug_label_id:
                input_data["labelIds"] = [self.bug_label_id]

            variables = {"input": input_data}

            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=self._get_headers(),
                    json={"query": mutation, "variables": variables},
                    timeout=15.0
                )

                if response.status_code == 200:
                    data = response.json()

                    # Check for GraphQL errors
                    if 'errors' in data:
                        logger.error(f"Linear GraphQL errors: {data['errors']}")
                        return None

                    # Extract issue data
                    issue_data = data.get('data', {}).get('issueCreate', {})

                    if issue_data.get('success'):
                        issue = issue_data.get('issue', {})
                        logger.info(f"Linear issue created: {issue.get('identifier')} - {title}")
                        return {
                            'id': issue.get('id'),
                            'identifier': issue.get('identifier'),
                            'title': issue.get('title'),
                            'url': issue.get('url')
                        }
                    else:
                        logger.error("Linear issue creation failed - success=false")
                        return None
                else:
                    logger.error(f"Linear API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error creating Linear issue: {e}")
            return None

    def _build_description(
        self,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build enhanced issue description with metadata.

        Args:
            description: Original bug description
            metadata: Additional metadata to include

        Returns:
            Formatted markdown description
        """
        parts = [description]

        if metadata:
            parts.append("\n\n---\n### 📋 Bug Report Details")

            # Add reporter info
            if metadata.get('user_email'):
                parts.append(f"**Reporter:** {metadata['user_email']}")

            # Add URL
            if metadata.get('url'):
                parts.append(f"**Page:** {metadata['url']}")

            # Add timestamp
            if metadata.get('timestamp'):
                parts.append(f"**Reported:** {metadata['timestamp']}")

            # Add browser info
            if metadata.get('browser'):
                browser_info = metadata['browser'][:200]  # Truncate long user agents
                parts.append(f"**Browser:** `{browser_info}`")

            # Add MongoDB report ID for reference
            if metadata.get('report_id'):
                parts.append(f"**Report ID:** `{metadata['report_id']}`")

        return "\n\n".join(parts)


# Singleton instance
_linear_service: Optional[LinearService] = None


def get_linear_service() -> LinearService:
    """
    Get or create Linear service singleton instance.

    Returns:
        LinearService instance
    """
    global _linear_service
    if _linear_service is None:
        _linear_service = LinearService()
    return _linear_service
