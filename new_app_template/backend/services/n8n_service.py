"""
n8n Service for New App

This service extends the shared N8NIntegration with app-specific business logic.
"""

from shared.integration.n8n import N8NIntegration, N8NConfig, N8NWorkflow
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NewAppN8NService(N8NIntegration):
    """
    New App-specific n8n service.

    Extends shared N8NIntegration with app-specific:
    - User workflow management
    - Workflow templates
    - Usage tracking
    - Business rules enforcement
    """

    def __init__(self, config: N8NConfig, app_db):
        """
        Initialize NewAppN8NService.

        Args:
            config: N8N configuration
            app_db: App-specific database connection (MongoDB)
        """
        # Initialize parent N8NIntegration with shared configuration
        super().__init__(config)

        # App-specific attributes
        self.app_db = app_db
        self.logger = logging.getLogger(__name__)

    async def create_app_workflow(
        self,
        user_id: str,
        workflow_name: str,
        nodes: List[Dict[str, Any]],
        connections: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create workflow with app-specific business logic.

        This method demonstrates:
        1. User validation
        2. Workflow naming conventions (user prefix)
        3. Tagging for organization
        4. Using inherited method from N8NIntegration
        5. Database tracking

        Args:
            user_id: User ID
            workflow_name: Workflow name
            nodes: Workflow nodes
            connections: Node connections
            **kwargs: Additional workflow configuration

        Returns:
            Dict containing workflow data

        Raises:
            ValueError: If user not found or limits exceeded
        """
        # Step 1: Validate user
        user = await self.app_db.users.find_one({"_id": user_id})
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check workflow limit
        if await self._user_has_max_workflows(user_id):
            raise ValueError("User has reached maximum workflows limit")

        # Step 2: Prepare workflow data with app conventions
        self.logger.info(f"Creating workflow '{workflow_name}' for user {user_id}")

        # Add user prefix and tags
        full_name = f"{user['username']}-{workflow_name}"
        tags = [
            f"user:{user_id}",
            "app:new_app",
            *kwargs.get("tags", [])
        ]

        # Step 3: Use inherited method from N8NIntegration
        workflow = await self.create_workflow(
            name=full_name,
            nodes=nodes,
            connections=connections,
            tags=tags,
            settings=kwargs.get("settings", {})
        )

        # Step 4: Store in app database
        app_workflow = {
            "user_id": user_id,
            "n8n_id": workflow.id,
            "name": workflow_name,  # Store without prefix
            "active": workflow.active,
            "created_at": datetime.utcnow(),
            "execution_count": 0,
            "credits_used": 1
        }
        result = await self.app_db.workflows.insert_one(app_workflow)

        # Step 5: Analytics and credits
        await self._log_workflow_creation(user_id, workflow.id)
        await self._deduct_user_credits(user_id, credits=1)

        return {
            "id": workflow.id,
            "name": workflow.name,
            "active": workflow.active,
            "app_workflow_id": str(result.inserted_id),
            "user_id": user_id
        }

    async def trigger_app_workflow(
        self,
        user_id: str,
        app_workflow_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger workflow with app-specific business logic.

        Args:
            user_id: User ID
            app_workflow_id: App workflow ID (not n8n ID)
            data: Data to pass to workflow

        Returns:
            Execution details
        """
        # Validate user
        user = await self.app_db.users.find_one({"_id": user_id})
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check credits
        if not await self._user_has_credits(user_id, required=1):
            raise ValueError("Insufficient credits")

        # Get workflow
        workflow = await self.app_db.workflows.find_one({
            "_id": app_workflow_id,
            "user_id": user_id
        })
        if not workflow:
            raise ValueError(f"Workflow {app_workflow_id} not found")

        # Use inherited method
        execution = await self.trigger_workflow(
            workflow_id=workflow["n8n_id"],
            data=data or {}
        )

        # Update database
        await self.app_db.workflows.update_one(
            {"_id": app_workflow_id},
            {
                "$inc": {"execution_count": 1},
                "$set": {"last_executed": datetime.utcnow()}
            }
        )

        # Store execution
        await self.app_db.workflow_executions.insert_one({
            "user_id": user_id,
            "app_workflow_id": app_workflow_id,
            "n8n_execution_id": execution.id,
            "status": execution.status.value,
            "started_at": datetime.utcnow(),
            "credits_charged": 1
        })

        # Deduct credits and log
        await self._deduct_user_credits(user_id, credits=1)
        await self._log_workflow_execution(user_id, execution.id)

        return {
            "execution_id": execution.id,
            "workflow_id": workflow["n8n_id"],
            "status": execution.status.value,
            "started_at": execution.started_at
        }

    async def get_user_workflows(
        self,
        user_id: str,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get user's workflows with n8n data.

        Args:
            user_id: User ID
            active_only: Only return active workflows
            limit: Max results
            offset: Pagination offset

        Returns:
            List of workflows with n8n + app data
        """
        # Build query
        query = {"user_id": user_id}
        if active_only:
            query["active"] = True

        # Get from app database
        app_workflows = await self.app_db.workflows.find(query).skip(
            offset
        ).limit(limit).to_list(length=limit)

        # Enrich with n8n data using inherited method
        enriched = []
        for app_workflow in app_workflows:
            try:
                n8n_workflow = await self.get_workflow(app_workflow["n8n_id"])
                enriched.append({
                    "id": n8n_workflow.id,
                    "name": n8n_workflow.name,
                    "active": n8n_workflow.active,
                    "app_workflow_id": str(app_workflow["_id"]),
                    "execution_count": app_workflow.get("execution_count", 0),
                    "created_at": app_workflow["created_at"]
                })
            except Exception as e:
                self.logger.error(
                    f"Failed to get n8n data for {app_workflow['n8n_id']}: {e}"
                )
                # Return app data only
                enriched.append({
                    "id": app_workflow["n8n_id"],
                    "name": app_workflow["name"],
                    "app_workflow_id": str(app_workflow["_id"]),
                    "execution_count": app_workflow.get("execution_count", 0),
                    "error": "Failed to fetch n8n data"
                })

        return enriched

    async def create_workflow_from_template(
        self,
        user_id: str,
        template_name: str,
        workflow_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create workflow from predefined template.

        This demonstrates app-specific workflow templates.

        Args:
            user_id: User ID
            template_name: Template name (e.g., "webhook_notifier", "data_processor")
            workflow_name: Custom workflow name

        Returns:
            Created workflow
        """
        # Get template
        template = await self._get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        # Use custom name or template name
        name = workflow_name or template["name"]

        # Create workflow using template
        return await self.create_app_workflow(
            user_id=user_id,
            workflow_name=name,
            nodes=template["nodes"],
            connections=template["connections"],
            tags=["template:" + template_name]
        )

    async def _get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow template from app database.

        In a real app, you would have a collection of predefined templates.
        """
        # Example: fetch from database
        template = await self.app_db.workflow_templates.find_one({
            "name": template_name,
            "active": True
        })

        if not template:
            # Return a default template as fallback
            return self._get_default_template(template_name)

        return template

    def _get_default_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get built-in default templates."""
        templates = {
            "webhook_notifier": {
                "name": "Webhook Notifier",
                "nodes": [
                    {
                        "name": "Webhook",
                        "type": "n8n-nodes-base.webhook",
                        "position": [250, 300],
                        "parameters": {
                            "path": "notify",
                            "httpMethod": "POST"
                        }
                    },
                    {
                        "name": "Send Notification",
                        "type": "n8n-nodes-base.emailSend",
                        "position": [450, 300],
                        "parameters": {
                            "subject": "Notification",
                            "text": "={{ $json.message }}"
                        }
                    }
                ],
                "connections": {
                    "Webhook": {
                        "main": [[{"node": "Send Notification", "type": "main", "index": 0}]]
                    }
                }
            },
            "data_processor": {
                "name": "Data Processor",
                "nodes": [
                    {
                        "name": "Webhook",
                        "type": "n8n-nodes-base.webhook",
                        "position": [250, 300],
                        "parameters": {"path": "process"}
                    },
                    {
                        "name": "Process Data",
                        "type": "n8n-nodes-base.function",
                        "position": [450, 300],
                        "parameters": {
                            "functionCode": "return items;"
                        }
                    }
                ],
                "connections": {
                    "Webhook": {
                        "main": [[{"node": "Process Data", "type": "main", "index": 0}]]
                    }
                }
            }
        }

        return templates.get(template_name)

    async def _user_has_max_workflows(self, user_id: str) -> bool:
        """Check if user has reached workflow limit."""
        count = await self.app_db.workflows.count_documents({
            "user_id": user_id
        })
        return count >= 20  # Example limit

    async def _user_has_credits(self, user_id: str, required: int) -> bool:
        """Check if user has enough credits."""
        user = await self.app_db.users.find_one({"_id": user_id})
        return user and user.get("credits", 0) >= required

    async def _deduct_user_credits(self, user_id: str, credits: int):
        """Deduct credits from user account."""
        await self.app_db.users.update_one(
            {"_id": user_id},
            {
                "$inc": {"credits": -credits},
                "$set": {"last_activity": datetime.utcnow()}
            }
        )

    async def _log_workflow_creation(self, user_id: str, workflow_id: str):
        """Log workflow creation to analytics."""
        await self.app_db.analytics_events.insert_one({
            "event_type": "workflow_created",
            "user_id": user_id,
            "workflow_id": workflow_id,
            "timestamp": datetime.utcnow(),
            "credits_charged": 1
        })

    async def _log_workflow_execution(self, user_id: str, execution_id: str):
        """Log workflow execution to analytics."""
        await self.app_db.analytics_events.insert_one({
            "event_type": "workflow_executed",
            "user_id": user_id,
            "execution_id": execution_id,
            "timestamp": datetime.utcnow(),
            "credits_charged": 1
        })
