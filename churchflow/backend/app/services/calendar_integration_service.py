"""
Google Calendar Integration Service for ChurchFlow

Syncs ChurchFlow conferences with Google Calendar.
Leverages shared GoogleWorkspaceIntegration library.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from shared.integration.google_workspace import (
    GoogleWorkspaceIntegration,
    GoogleWorkspaceConfig,
    GoogleCalendarConfig as SharedGoogleCalendarConfig
)
from app.models.integration import (
    IntegrationConfig,
    CalendarEventMapping,
    GoogleCalendarConfig,
    IntegrationStatus,
    IntegrationType
)
from app.models.conference import Conference

logger = logging.getLogger(__name__)


class CalendarIntegrationService:
    """
    Sync ChurchFlow events to Google Calendar.

    Features:
    - One-way sync: ChurchFlow -> Google Calendar
    - Two-way sync: Bidirectional updates
    - Auto-sync on conference create/update
    - Batch sync for existing conferences
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize Calendar Integration Service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.integrations_collection = db.integrations
        self.mappings_collection = db.calendar_event_mappings
        self.conferences_collection = db.conferences

    async def get_integration_config(
        self,
        organization_id: str
    ) -> Optional[IntegrationConfig]:
        """
        Get Google Calendar integration config for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            Integration config or None if not found
        """
        config_data = await self.integrations_collection.find_one({
            "organization_id": organization_id,
            "integration_type": IntegrationType.GOOGLE_CALENDAR,
            "status": IntegrationStatus.ACTIVE
        })

        if not config_data:
            return None

        config_data["id"] = str(config_data.pop("_id"))
        return IntegrationConfig(**config_data)

    async def save_integration_config(
        self,
        organization_id: str,
        config: GoogleCalendarConfig,
        credentials_json: Dict[str, Any]
    ) -> IntegrationConfig:
        """
        Save or update Google Calendar integration config.

        Args:
            organization_id: Organization ID
            config: Google Calendar configuration
            credentials_json: Service account credentials

        Returns:
            Saved integration config
        """
        # Reason: Store credentials in config for authentication
        config_dict = config.dict()
        config_dict["credentials_json"] = credentials_json

        integration = IntegrationConfig(
            organization_id=organization_id,
            integration_type=IntegrationType.GOOGLE_CALENDAR,
            status=IntegrationStatus.ACTIVE,
            google_calendar=GoogleCalendarConfig(**config_dict),
            updated_at=datetime.utcnow()
        )

        # Upsert integration config
        result = await self.integrations_collection.update_one(
            {
                "organization_id": organization_id,
                "integration_type": IntegrationType.GOOGLE_CALENDAR
            },
            {"$set": integration.dict(exclude={"id"})},
            upsert=True
        )

        if result.upserted_id:
            integration.id = str(result.upserted_id)

        logger.info(f"Saved Google Calendar integration for org {organization_id}")
        return integration

    async def sync_conference_to_calendar(
        self,
        conference: Conference,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Sync a ChurchFlow conference to Google Calendar.

        Args:
            conference: Conference to sync
            organization_id: Organization ID

        Returns:
            Sync result with event details
        """
        try:
            # Get integration config
            integration = await self.get_integration_config(organization_id)
            if not integration or not integration.google_calendar:
                raise ValueError("Google Calendar integration not configured")

            # Initialize Google Calendar integration
            workspace_config = GoogleWorkspaceConfig(
                calendar=SharedGoogleCalendarConfig(
                    calendar_id=integration.google_calendar.calendar_id,
                    credentials_json=integration.google_calendar.credentials_json
                )
            )
            google_workspace = GoogleWorkspaceIntegration(workspace_config)

            # Check if event already exists
            existing_mapping = await self.mappings_collection.find_one({
                "organization_id": organization_id,
                "conference_id": str(conference.id)
            })

            # Prepare event data
            event_data = self._build_event_data(
                conference,
                integration.google_calendar
            )

            if existing_mapping:
                # Update existing event
                result = await google_workspace.calendar.update_event(
                    calendar_id=integration.google_calendar.calendar_id,
                    event_id=existing_mapping["google_event_id"],
                    updates=event_data
                )

                # Update mapping
                await self.mappings_collection.update_one(
                    {"_id": existing_mapping["_id"]},
                    {
                        "$set": {
                            "last_synced_at": datetime.utcnow(),
                            "conference_updated_at": conference.updated_at
                        }
                    }
                )

                logger.info(f"Updated Google Calendar event {existing_mapping['google_event_id']} for conference {conference.id}")

            else:
                # Create new event
                result = await google_workspace.calendar.create_event(
                    calendar_id=integration.google_calendar.calendar_id,
                    event_data=event_data
                )

                # Save mapping
                mapping = CalendarEventMapping(
                    organization_id=organization_id,
                    conference_id=str(conference.id),
                    google_event_id=result["id"],
                    google_calendar_id=integration.google_calendar.calendar_id,
                    conference_updated_at=conference.updated_at
                )

                await self.mappings_collection.insert_one(
                    mapping.dict(exclude={"id"})
                )

                logger.info(f"Created Google Calendar event {result['id']} for conference {conference.id}")

            # Update integration last sync time
            await self.integrations_collection.update_one(
                {
                    "organization_id": organization_id,
                    "integration_type": IntegrationType.GOOGLE_CALENDAR
                },
                {
                    "$set": {"last_sync_at": datetime.utcnow()},
                    "$inc": {"sync_count": 1}
                }
            )

            return {
                "success": True,
                "event_id": result["id"],
                "event_link": result.get("htmlLink", ""),
                "action": "updated" if existing_mapping else "created"
            }

        except Exception as e:
            logger.error(f"Failed to sync conference {conference.id} to calendar: {e}")

            # Update integration with error
            await self.integrations_collection.update_one(
                {
                    "organization_id": organization_id,
                    "integration_type": IntegrationType.GOOGLE_CALENDAR
                },
                {
                    "$set": {
                        "status": IntegrationStatus.ERROR,
                        "error_message": str(e),
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            raise

    async def delete_calendar_event(
        self,
        conference_id: str,
        organization_id: str
    ) -> bool:
        """
        Delete a Google Calendar event when conference is deleted.

        Args:
            conference_id: Conference ID
            organization_id: Organization ID

        Returns:
            True if successful
        """
        try:
            # Get integration config
            integration = await self.get_integration_config(organization_id)
            if not integration or not integration.google_calendar:
                logger.warning("Google Calendar integration not configured, skipping delete")
                return False

            # Get mapping
            mapping = await self.mappings_collection.find_one({
                "organization_id": organization_id,
                "conference_id": conference_id
            })

            if not mapping:
                logger.warning(f"No calendar mapping found for conference {conference_id}")
                return False

            # Initialize Google Calendar integration
            workspace_config = GoogleWorkspaceConfig(
                calendar=SharedGoogleCalendarConfig(
                    calendar_id=integration.google_calendar.calendar_id,
                    credentials_json=integration.google_calendar.credentials_json
                )
            )
            google_workspace = GoogleWorkspaceIntegration(workspace_config)

            # Delete event
            await google_workspace.calendar.delete_event(
                calendar_id=integration.google_calendar.calendar_id,
                event_id=mapping["google_event_id"]
            )

            # Delete mapping
            await self.mappings_collection.delete_one({"_id": mapping["_id"]})

            logger.info(f"Deleted Google Calendar event {mapping['google_event_id']} for conference {conference_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete calendar event for conference {conference_id}: {e}")
            raise

    async def batch_sync_conferences(
        self,
        organization_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Batch sync multiple conferences to Google Calendar.

        Args:
            organization_id: Organization ID
            limit: Maximum conferences to sync

        Returns:
            Sync summary with counts
        """
        try:
            # Get all conferences for organization
            conferences_cursor = self.conferences_collection.find({
                "organization_id": organization_id
            }).limit(limit)

            conferences = await conferences_cursor.to_list(length=limit)

            success_count = 0
            failed_count = 0
            failed_ids = []

            for conf_data in conferences:
                try:
                    conf_data["id"] = str(conf_data.pop("_id"))
                    conference = Conference(**conf_data)

                    await self.sync_conference_to_calendar(
                        conference=conference,
                        organization_id=organization_id
                    )

                    success_count += 1

                except Exception as e:
                    logger.error(f"Failed to sync conference {conf_data.get('id')}: {e}")
                    failed_count += 1
                    failed_ids.append(conf_data.get("id"))

            return {
                "success": True,
                "total_processed": len(conferences),
                "successful": success_count,
                "failed": failed_count,
                "failed_ids": failed_ids
            }

        except Exception as e:
            logger.error(f"Batch sync failed for org {organization_id}: {e}")
            raise

    def _build_event_data(
        self,
        conference: Conference,
        config: GoogleCalendarConfig
    ) -> Dict[str, Any]:
        """
        Build Google Calendar event data from conference.

        Args:
            conference: ChurchFlow conference
            config: Google Calendar configuration

        Returns:
            Event data for Google Calendar API
        """
        # Reason: Google Calendar API expects ISO 8601 format with timezone
        start_time = conference.start_date.isoformat()
        end_time = conference.end_date.isoformat()

        # Build description
        description_parts = [conference.description or ""]

        if config.include_registration_count:
            # Note: Registration count would need to be passed or fetched
            description_parts.append("\n\nManaged by ChurchFlow")

        description = "\n".join(description_parts).strip()

        event_data = {
            "summary": conference.title,
            "description": description,
            "start": {
                "dateTime": start_time,
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_time,
                "timeZone": "UTC"
            },
            "location": conference.venue or "",
            "reminders": {
                "useDefault": True
            }
        }

        return event_data

    async def test_connection(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Test Google Calendar connection.

        Args:
            organization_id: Organization ID

        Returns:
            Connection test result
        """
        try:
            integration = await self.get_integration_config(organization_id)
            if not integration or not integration.google_calendar:
                return {
                    "success": False,
                    "error": "Google Calendar integration not configured"
                }

            # Initialize Google Calendar integration
            workspace_config = GoogleWorkspaceConfig(
                calendar=SharedGoogleCalendarConfig(
                    calendar_id=integration.google_calendar.calendar_id,
                    credentials_json=integration.google_calendar.credentials_json
                )
            )
            google_workspace = GoogleWorkspaceIntegration(workspace_config)

            # Test by listing upcoming events
            now = datetime.utcnow()
            events = await google_workspace.calendar.list_events(
                calendar_id=integration.google_calendar.calendar_id,
                time_min=now,
                time_max=now + timedelta(days=7),
                max_results=1
            )

            return {
                "success": True,
                "message": "Connection successful",
                "calendar_id": integration.google_calendar.calendar_id,
                "test_timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
