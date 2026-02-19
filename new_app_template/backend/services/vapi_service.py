"""
Vapi Service for New App

This service extends the shared VAPIService with app-specific business logic.
"""

from shared.integration.vapi import VAPIService, VAPIAgent, VAPICall
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NewAppVapiService(VAPIService):
    """
    New App-specific Vapi service.

    Extends shared VAPIService with app-specific:
    - User management
    - Assistant creation with business rules
    - Usage tracking
    - Analytics
    """

    def __init__(self, config, app_db):
        """
        Initialize NewAppVapiService.

        Args:
            config: Vapi configuration (VAPIConfig)
            app_db: App-specific database connection (MongoDB)
        """
        # Initialize parent VAPIService with shared configuration
        super().__init__(config)

        # App-specific attributes
        self.app_db = app_db
        self.logger = logging.getLogger(__name__)

    async def create_app_assistant(
        self,
        user_id: str,
        name: str,
        system_prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create assistant with app-specific business logic.

        This method demonstrates the pattern of:
        1. App-specific validation (check user exists, check limits)
        2. Use inherited method from VAPIService
        3. App-specific post-processing (database, analytics)

        Args:
            user_id: User ID in app database
            name: Assistant name
            system_prompt: System prompt for assistant
            **kwargs: Additional assistant configuration

        Returns:
            Dict containing Vapi response + app-specific data

        Raises:
            ValueError: If user not found or limits exceeded
        """
        # Step 1: App-specific validation
        user = await self.app_db.users.find_one({"_id": user_id})
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check user's assistant limit
        if await self._user_has_max_assistants(user_id):
            raise ValueError(
                f"User {user_id} has reached maximum assistants limit"
            )

        # Step 2: Use inherited method from VAPIService
        self.logger.info(f"Creating assistant '{name}' for user {user_id}")

        agent = VAPIAgent(
            name=name,
            system_prompt=system_prompt,
            voice=kwargs.get("voice", "alloy"),
            language=kwargs.get("language", "en"),
            model=kwargs.get("model", "gpt-4o-mini"),
            provider=kwargs.get("provider", "openai"),
            first_message=kwargs.get("first_message"),
            end_call_message=kwargs.get("end_call_message")
        )

        # Call parent's generic method
        vapi_response = await self.create_assistant(agent)

        # Step 3: App-specific post-processing
        # Store in app database
        app_assistant = {
            "user_id": user_id,
            "vapi_id": vapi_response["id"],
            "name": name,
            "status": "active",
            "created_at": datetime.utcnow(),
            "credits_used": 1,
            "total_calls": 0
        }
        result = await self.app_db.assistants.insert_one(app_assistant)

        # Log to app analytics
        await self._log_assistant_creation(user_id, vapi_response["id"])

        # Update user's credits
        await self._deduct_user_credits(user_id, credits=1)

        return {
            **vapi_response,
            "app_assistant_id": str(result.inserted_id),
            "user_id": user_id
        }

    async def initiate_app_call(
        self,
        user_id: str,
        assistant_id: str,
        phone_number: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Initiate call with app-specific business logic.

        Args:
            user_id: User ID
            assistant_id: App assistant ID (not Vapi ID)
            phone_number: Phone number to call
            **kwargs: Additional call parameters

        Returns:
            Dict containing call details
        """
        # Validate user
        user = await self.app_db.users.find_one({"_id": user_id})
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check user has enough credits
        if not await self._user_has_credits(user_id, required=2):
            raise ValueError(f"User {user_id} has insufficient credits")

        # Get assistant
        assistant = await self.app_db.assistants.find_one({
            "_id": assistant_id,
            "user_id": user_id
        })
        if not assistant:
            raise ValueError(f"Assistant {assistant_id} not found")

        # Use inherited method
        call = await self.initiate_call(
            assistant_id=assistant["vapi_id"],
            phone_number=phone_number,
            task=kwargs.get("task")
        )

        # Store call in app database
        app_call = {
            "user_id": user_id,
            "assistant_id": assistant_id,
            "vapi_call_id": call["id"],
            "phone_number": phone_number,
            "status": call["status"],
            "initiated_at": datetime.utcnow(),
            "credits_charged": 2
        }
        await self.app_db.calls.insert_one(app_call)

        # Deduct credits
        await self._deduct_user_credits(user_id, credits=2)

        # Track analytics
        await self._log_call_initiated(user_id, call["id"])

        return call

    async def get_user_assistants(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get user's assistants with Vapi data.

        Args:
            user_id: User ID
            limit: Max results
            offset: Pagination offset

        Returns:
            List of assistants with Vapi + app data
        """
        # Get from app database
        app_assistants = await self.app_db.assistants.find(
            {"user_id": user_id}
        ).skip(offset).limit(limit).to_list(length=limit)

        # Enrich with Vapi data using inherited method
        enriched = []
        for app_assistant in app_assistants:
            try:
                vapi_data = await self.get_assistant(app_assistant["vapi_id"])
                enriched.append({
                    **vapi_data,
                    "app_assistant_id": str(app_assistant["_id"]),
                    "total_calls": app_assistant.get("total_calls", 0)
                })
            except Exception as e:
                self.logger.error(
                    f"Failed to get Vapi data for {app_assistant['vapi_id']}: {e}"
                )
                # Return app data only
                enriched.append({
                    "id": app_assistant["vapi_id"],
                    "name": app_assistant["name"],
                    "app_assistant_id": str(app_assistant["_id"]),
                    "total_calls": app_assistant.get("total_calls", 0),
                    "error": "Failed to fetch Vapi data"
                })

        return enriched

    async def _user_has_max_assistants(self, user_id: str) -> bool:
        """Check if user has reached assistant limit."""
        count = await self.app_db.assistants.count_documents({
            "user_id": user_id,
            "status": "active"
        })
        return count >= 10  # Example limit

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

    async def _log_assistant_creation(self, user_id: str, assistant_id: str):
        """Log assistant creation to analytics."""
        await self.app_db.analytics_events.insert_one({
            "event_type": "assistant_created",
            "user_id": user_id,
            "assistant_id": assistant_id,
            "timestamp": datetime.utcnow(),
            "credits_charged": 1
        })

    async def _log_call_initiated(self, user_id: str, call_id: str):
        """Log call initiation to analytics."""
        await self.app_db.analytics_events.insert_one({
            "event_type": "call_initiated",
            "user_id": user_id,
            "call_id": call_id,
            "timestamp": datetime.utcnow(),
            "credits_charged": 2
        })
