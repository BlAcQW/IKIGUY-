"""
Campaign Execution Service.

Manages the execution of automation campaigns, including sequential calling
of audience contacts, progress tracking, and outcome analysis.
"""

import asyncio
import logging
from datetime import datetime, timezone, time as dt_time
from typing import Any, Dict, List, Optional
from bson import ObjectId

from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models.campaign import (
    AutomationCampaign,
    CampaignCall,
    CampaignContact,
    CampaignConfig,
    CampaignProgress,
    CampaignCreateRequest,
    CampaignStatusResponse,
    CampaignAnalyticsResponse,
    CallObjection,
    CallOutcome
)
from ..mongo import get_collection

logger = logging.getLogger(__name__)


class CampaignExecutionService:
    """
    Service for managing automation campaign execution.

    Handles campaign creation, execution, pause/resume, and analytics.
    """

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        """
        Initialize campaign execution service.

        Args:
            db: MongoDB database instance (optional, will use default if not provided)
        """
        # Store db only if provided (avoid truth value testing on database objects)
        self.db = db if db is not None else None
        self.campaigns_collection = get_collection("automation_campaigns")
        self.campaign_calls_collection = get_collection("campaign_calls")
        self.audiences_collection = get_collection("audiences")
        self.audience_contacts_collection = get_collection("audience_contacts")
        self.automations_collection = get_collection("automation_configs")

        # Background task tracking
        self._running_campaigns: Dict[str, asyncio.Task] = {}

    async def create_campaign(
        self,
        request: CampaignCreateRequest,
        user_id: str,
        organization_id: Optional[str] = None
    ) -> AutomationCampaign:
        """
        Create a new campaign linking an automation to an audience.

        Args:
            request: Campaign creation request
            user_id: User creating the campaign
            organization_id: Optional organization ID

        Returns:
            Created campaign

        Raises:
            ValueError: If automation or audience not found
        """
        # Fetch automation details
        automation = await self.automations_collection.find_one(
            {"_id": ObjectId(request.automation_id)}
        )
        if not automation:
            raise ValueError(f"Automation {request.automation_id} not found")

        # Fetch audience details
        audience = await self.audiences_collection.find_one(
            {"id": request.audience_id}
        )
        if not audience:
            raise ValueError(f"Audience {request.audience_id} not found")

        # Count contacts in audience
        # Reason: Contacts are stored separately in audience_contacts collection, use size field
        audience_size = audience.get("size", 0)
        if audience_size == 0:
            raise ValueError("Audience has no contacts")

        # Create campaign
        campaign_id = str(ObjectId())
        now = datetime.now(timezone.utc)

        campaign = AutomationCampaign(
            id=campaign_id,
            automation_id=request.automation_id,
            automation_name=automation.get("automation_name", "Unknown"),
            audience_id=request.audience_id,
            audience_name=audience.get("name", "Unknown"),
            phone_id=request.phone_id,
            user_id=user_id,
            organization_id=organization_id,
            status="pending",
            progress=CampaignProgress(
                total_contacts=audience_size,
                pending=audience_size
            ),
            config=request.config or CampaignConfig(),
            created_at=now,
            updated_at=now
        )

        # Save to database
        campaign_dict = campaign.dict(exclude_none=True)
        campaign_dict["_id"] = campaign_id

        await self.campaigns_collection.insert_one(campaign_dict)

        logger.info(f"Created campaign {campaign_id} for automation {request.automation_id} with {audience_size} contacts")

        # Handle auto_start: if auto_start is true and start_time is set
        config = campaign.config
        if config.auto_start and config.start_time:
            try:
                now = datetime.now(timezone.utc)
                current_time = now.time()
                start_hour, start_minute = map(int, config.start_time.split(':'))
                start_window = dt_time(start_hour, start_minute)
                
                # If current time >= start_time, start immediately
                if current_time >= start_window:
                    logger.info(f"Auto-starting campaign {campaign_id} immediately (start_time {config.start_time} already reached)")
                    try:
                        await self.start_campaign(campaign_id)
                        # Refresh campaign to get updated status
                        campaign = await self.get_campaign(campaign_id)
                    except Exception as e:
                        logger.error(f"Failed to auto-start campaign {campaign_id}: {e}")
                        # Continue with pending status if auto-start fails
                else:
                    logger.info(f"Campaign {campaign_id} will auto-start at {config.start_time} UTC (current time: {current_time.strftime('%H:%M')})")
            except Exception as e:
                logger.warning(f"Error processing auto_start for campaign {campaign_id}: {e}")

        return campaign

    async def get_campaign(self, campaign_id: str) -> Optional[AutomationCampaign]:
        """
        Get campaign by ID.

        Args:
            campaign_id: Campaign ID (string or ObjectId)

        Returns:
            Campaign if found, None otherwise
        """
        # Try to find by string ID first
        doc = await self.campaigns_collection.find_one({"_id": campaign_id})
        
        # If not found and it looks like an ObjectId string, try converting
        if not doc and isinstance(campaign_id, str) and len(campaign_id) == 24:
            try:
                doc = await self.campaigns_collection.find_one({"_id": ObjectId(campaign_id)})
            except Exception:
                pass
        
        if not doc:
            return None

        doc["id"] = str(doc.pop("_id"))
        
        # Recalculate costs and duration from call records if missing or zero
        campaign_id = doc["id"]
        if (doc.get("total_cost", 0) == 0 or 
            doc.get("total_vapi_cost_usd", 0) == 0 or 
            doc.get("avg_call_duration", 0) == 0):
            
            calls_cursor = self.campaign_calls_collection.find({"campaign_id": campaign_id})
            total_vapi_cost = 0.0
            total_phone_cost = 0.0
            total_duration = 0
            completed_calls = 0
            
            async for call_doc in calls_cursor:
                # Sum VAPI costs (cost field in call records is VAPI cost)
                if call_doc.get("cost") and call_doc.get("cost") > 0:
                    total_vapi_cost += float(call_doc.get("cost", 0))
                
                # Calculate phone cost from duration if available
                if call_doc.get("duration") and call_doc.get("duration") > 0:
                    duration_seconds = int(call_doc.get("duration", 0))
                    total_duration += duration_seconds
                    completed_calls += 1
                    
                    # Calculate phone cost (0.15 GHC per minute)
                    duration_minutes = duration_seconds / 60.0
                    phone_cost_per_minute = 0.15  # Default rate
                    total_phone_cost += duration_minutes * phone_cost_per_minute
            
            # Update campaign document with calculated values
            if total_vapi_cost > 0:
                doc["total_vapi_cost_usd"] = total_vapi_cost
            if total_phone_cost > 0:
                doc["total_phone_cost_ghc"] = total_phone_cost
            if total_vapi_cost > 0 or total_phone_cost > 0:
                # Convert GHC to USD for total_cost (rough estimate: 1 GHC ≈ 0.08 USD)
                total_cost_usd = total_vapi_cost + (total_phone_cost * 0.08)
                doc["total_cost"] = total_cost_usd
            if completed_calls > 0:
                doc["avg_call_duration"] = total_duration / completed_calls
        
        return AutomationCampaign(**doc)

    async def list_campaigns(
        self,
        automation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AutomationCampaign]:
        """
        List campaigns with optional filtering.

        Args:
            automation_id: Filter by automation ID
            user_id: Filter by user ID
            status: Filter by status
            limit: Maximum number of results
            offset: Results offset for pagination

        Returns:
            List of campaigns
        """
        query = {}

        if automation_id:
            query["automation_id"] = automation_id
        if user_id:
            query["user_id"] = user_id
        if status:
            query["status"] = status

        cursor = self.campaigns_collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        campaigns = []

        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            
            # Calculate costs and duration from call records if missing or zero
            campaign_id = doc["id"]
            if (doc.get("total_cost", 0) == 0 or 
                doc.get("total_vapi_cost_usd", 0) == 0 or 
                doc.get("avg_call_duration", 0) == 0):
                
                calls_cursor = self.campaign_calls_collection.find({"campaign_id": campaign_id})
                total_vapi_cost = 0.0
                total_phone_cost = 0.0
                total_duration = 0
                completed_calls = 0
                
                async for call_doc in calls_cursor:
                    # Sum VAPI costs (cost field in call records is VAPI cost)
                    if call_doc.get("cost") and call_doc.get("cost") > 0:
                        total_vapi_cost += float(call_doc.get("cost", 0))
                    
                    # Calculate phone cost from duration if available
                    if call_doc.get("duration") and call_doc.get("duration") > 0:
                        duration_seconds = int(call_doc.get("duration", 0))
                        total_duration += duration_seconds
                        completed_calls += 1
                        
                        # Calculate phone cost (0.15 GHC per minute)
                        duration_minutes = duration_seconds / 60.0
                        phone_cost_per_minute = 0.15  # Default rate
                        total_phone_cost += duration_minutes * phone_cost_per_minute
                
                # Update campaign document with calculated values
                if total_vapi_cost > 0:
                    doc["total_vapi_cost_usd"] = total_vapi_cost
                if total_phone_cost > 0:
                    doc["total_phone_cost_ghc"] = total_phone_cost
                if total_vapi_cost > 0 or total_phone_cost > 0:
                    # Convert GHC to USD for total_cost (rough estimate: 1 GHC ≈ 0.08 USD)
                    total_cost_usd = total_vapi_cost + (total_phone_cost * 0.08)
                    doc["total_cost"] = total_cost_usd
                if completed_calls > 0:
                    doc["avg_call_duration"] = total_duration / completed_calls
            
            campaigns.append(AutomationCampaign(**doc))

        return campaigns

    async def start_campaign(self, campaign_id: str) -> AutomationCampaign:
        """
        Start campaign execution.

        Args:
            campaign_id: Campaign ID to start

        Returns:
            Updated campaign

        Raises:
            ValueError: If campaign not found or already running
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign.status == "running":
            raise ValueError("Campaign is already running")

        # Check if campaign is paused and if it's within calling window to resume
        if campaign.status == "paused" and campaign.config.start_time:
            # Check if current time is within calling window
            now = datetime.now(timezone.utc)
            current_time = now.time()
            try:
                start_time_str = campaign.config.start_time
                if start_time_str:
                    start_hour, start_minute = map(int, start_time_str.split(':'))
                    start_window = dt_time(start_hour, start_minute)
                    
                    # If we haven't reached start time yet, don't resume
                    if current_time < start_window:
                        logger.info(
                            f"Campaign {campaign_id} is paused and start time ({start_time_str}) not reached yet. "
                            f"Current time: {current_time.strftime('%H:%M')}"
                        )
                        raise ValueError(f"Campaign will resume at {start_time_str} UTC")
            except (ValueError, AttributeError) as e:
                if "Campaign will resume" in str(e):
                    raise  # Re-raise our custom error
                logger.warning(f"Invalid start_time format in campaign config: {e}")

        if campaign.status == "completed":
            # Reason: Frontend supports "Replay" on completed campaigns.
            # Instead of blocking, reset progress and metrics so the campaign
            # can be run again from the beginning.
            logger.info(f"Resetting completed campaign {campaign_id} for replay")
            await self.campaigns_collection.update_one(
                {"_id": campaign_id},
                {
                    "$set": {
                        "status": "pending",
                        # Reset progress counters while preserving total_contacts
                        "progress.triggered": 0,
                        "progress.completed": 0,
                        "progress.called": 0,
                        "progress.successful": 0,
                        "progress.failed": 0,
                        "progress.no_answer": 0,
                        "progress.conversion_count": 0,
                        "progress.current_contact_index": 0,
                        "progress.pending": campaign.progress.total_contacts,
                        # Reset aggregate metrics
                        "total_cost": 0.0,
                        "avg_call_duration": 0.0,
                        # Clear error / timing flags so new run is clean
                        "error_message": None,
                        "started_at": None,
                        "paused_at": None,
                        "completed_at": None,
                    }
                },
            )
            # Refresh local copy after reset
            campaign = await self.get_campaign(campaign_id)

        # Update status to running
        now = datetime.now(timezone.utc)
        await self.campaigns_collection.update_one(
            {"_id": campaign_id},
            {
                "$set": {
                    "status": "running",
                    "started_at": now if not campaign.started_at else campaign.started_at,
                    "paused_at": None,
                    "updated_at": now
                }
            }
        )

        # Start background execution task
        task = asyncio.create_task(self._execute_campaign(campaign_id))
        self._running_campaigns[campaign_id] = task

        logger.info(f"Started campaign {campaign_id}")

        return await self.get_campaign(campaign_id)

    async def pause_campaign(self, campaign_id: str) -> AutomationCampaign:
        """
        Pause campaign execution.

        Args:
            campaign_id: Campaign ID to pause

        Returns:
            Updated campaign

        Raises:
            ValueError: If campaign not found or not running
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign.status != "running":
            raise ValueError("Campaign is not running")

        # Update status to paused
        now = datetime.now(timezone.utc)
        await self.campaigns_collection.update_one(
            {"_id": campaign_id},
            {
                "$set": {
                    "status": "paused",
                    "paused_at": now,
                    "updated_at": now
                }
            }
        )

        # Cancel background task
        if campaign_id in self._running_campaigns:
            self._running_campaigns[campaign_id].cancel()
            del self._running_campaigns[campaign_id]

        logger.info(f"Paused campaign {campaign_id}")

        return await self.get_campaign(campaign_id)

    async def _pause_campaign_auto(self, campaign_id: str, reason: str) -> None:
        """
        Automatically pause campaign (internal method, doesn't raise errors).

        Args:
            campaign_id: Campaign ID to pause
            reason: Reason for pausing
        """
        try:
            campaign = await self.get_campaign(campaign_id)
            if not campaign or campaign.status != "running":
                return  # Campaign not running, nothing to pause

            # Update status to paused
            now = datetime.now(timezone.utc)
            await self.campaigns_collection.update_one(
                {"_id": campaign_id},
                {
                    "$set": {
                        "status": "paused",
                        "paused_at": now,
                        "updated_at": now,
                        "error_message": reason
                    }
                }
            )

            # Cancel background task
            if campaign_id in self._running_campaigns:
                self._running_campaigns[campaign_id].cancel()
                del self._running_campaigns[campaign_id]

            logger.info(f"Auto-paused campaign {campaign_id}: {reason}")
        except Exception as e:
            logger.error(f"Error auto-pausing campaign {campaign_id}: {e}")

    async def resume_campaign(self, campaign_id: str) -> AutomationCampaign:
        """
        Resume paused campaign.

        Args:
            campaign_id: Campaign ID to resume

        Returns:
            Updated campaign
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign.status != "paused":
            raise ValueError("Campaign is not paused")

        return await self.start_campaign(campaign_id)

    async def get_campaign_status(self, campaign_id: str) -> CampaignStatusResponse:
        """
        Get detailed campaign status including progress and estimates.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign status response

        Raises:
            ValueError: If campaign not found
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Get current and next contacts if available
        # Reason: Query audience by UUID id field, not MongoDB ObjectId
        audience = await self.audiences_collection.find_one({"id": campaign.audience_id})
        # Reason: Contacts are stored in separate collection, fetch them
        contacts = []
        if audience:
            cursor = self.audience_contacts_collection.find({"audience_id": campaign.audience_id})
            contacts = await cursor.to_list(length=None)

        current_contact = None
        next_contact = None

        if campaign.status == "running" and campaign.progress.current_contact_index < len(contacts):
            current_idx = campaign.progress.current_contact_index
            if current_idx < len(contacts):
                current_contact = CampaignContact(**contacts[current_idx])
            if current_idx + 1 < len(contacts):
                next_contact = CampaignContact(**contacts[current_idx + 1])

        # Estimate completion time
        estimated_completion = None
        if campaign.status == "running" and campaign.progress.called > 0:
            avg_call_time = campaign.avg_call_duration or 60  # Default 60 seconds
            delay = campaign.config.call_delay_seconds
            remaining_contacts = campaign.progress.pending
            estimated_seconds = remaining_contacts * (avg_call_time + delay)
            estimated_completion = datetime.now(timezone.utc).timestamp() + estimated_seconds
            estimated_completion = datetime.fromtimestamp(estimated_completion, tz=timezone.utc)

        # Estimate total cost
        estimated_total_cost = None
        if campaign.progress.called > 0:
            avg_cost = campaign.total_cost / campaign.progress.called
            estimated_total_cost = avg_cost * campaign.progress.total_contacts

        return CampaignStatusResponse(
            campaign=campaign,
            current_contact=current_contact,
            next_contact=next_contact,
            estimated_completion=estimated_completion,
            estimated_total_cost=estimated_total_cost
        )

    async def get_campaign_calls(
        self,
        campaign_id: str,
        page: int = 1,
        limit: int = 100,
        status_filter: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get paginated campaign calls.

        Args:
            campaign_id: Campaign ID
            page: Page number (1-indexed)
            limit: Number of calls per page
            status_filter: Optional status filter
            organization_id: Optional organization ID for multi-tenant isolation

        Returns:
            Dictionary with calls and pagination info
        """
        try:
            query = {"campaign_id": campaign_id}
            if status_filter:
                query["status"] = status_filter
            # Note: We don't filter by organization_id here because:
            # 1. Access control is already done at the campaign/automation level
            # 2. Legacy calls may not have organization_id field
            # 3. Campaign ID is unique and sufficient for filtering

            # Get total count
            total_count = await self.campaign_calls_collection.count_documents(query)

            # Calculate pagination
            skip = (page - 1) * limit

            # Get calls sorted by contact_index (order they were called)
            cursor = self.campaign_calls_collection.find(query).sort("contact_index", 1).skip(skip).limit(limit)
            calls = []
            async for doc in cursor:
                doc["id"] = str(doc.get("_id", ""))
                # Convert ObjectId to string if present
                if "_id" in doc:
                    del doc["_id"]
                calls.append(doc)

            return {
                "calls": calls,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_count,
                    "pages": (total_count + limit - 1) // limit if limit > 0 else 0
                }
            }
        except Exception as e:
            logger.error(f"Error getting campaign calls for {campaign_id}: {str(e)}")
            return {
                "calls": [],
                "pagination": {"page": 1, "limit": limit, "total": 0, "pages": 0},
                "error": str(e)
            }

    async def get_campaign_analytics(self, campaign_id: str) -> CampaignAnalyticsResponse:
        """
        Get comprehensive campaign analytics.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign analytics response

        Raises:
            ValueError: If campaign not found
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Get all campaign calls
        cursor = self.campaign_calls_collection.find({"campaign_id": campaign_id})
        calls = []
        async for doc in cursor:
            doc["id"] = doc.pop("_id")
            calls.append(CampaignCall(**doc))

        # Calculate outcome distribution
        outcome_distribution = {}
        for call in calls:
            if call.outcome:
                outcome = call.outcome.outcome
                outcome_distribution[outcome] = outcome_distribution.get(outcome, 0) + 1

        # Extract top objections
        objection_counts = {}
        for call in calls:
            if call.outcome and call.outcome.objections:
                for objection in call.outcome.objections:
                    key = f"{objection.category}:{objection.text}"
                    if key not in objection_counts:
                        objection_counts[key] = {
                            "category": objection.category,
                            "text": objection.text,
                            "count": 0
                        }
                    objection_counts[key]["count"] += 1

        top_objections = sorted(
            objection_counts.values(),
            key=lambda x: x["count"],
            reverse=True
        )[:10]

        # Calculate sentiment distribution
        sentiment_distribution = {}
        for call in calls:
            if call.outcome and call.outcome.sentiment:
                sentiment = call.outcome.sentiment
                sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1

        # Calculate cost metrics
        cost_per_call = campaign.total_cost / campaign.progress.called if campaign.progress.called > 0 else 0
        cost_per_conversion = campaign.total_cost / campaign.progress.conversion_count if campaign.progress.conversion_count > 0 else None

        # Calculate campaign duration
        campaign_duration = None
        if campaign.started_at:
            end_time = campaign.completed_at or datetime.now(timezone.utc)
            campaign_duration = (end_time - campaign.started_at).total_seconds()

        # Generate timeline data (calls per hour)
        timeline_data = await self._generate_timeline_data(campaign_id)

        # Get recent calls (last 10)
        recent_calls = sorted(calls, key=lambda x: x.created_at, reverse=True)[:10]

        return CampaignAnalyticsResponse(
            campaign_id=campaign_id,
            automation_name=campaign.automation_name,
            audience_name=campaign.audience_name,
            progress=campaign.progress,
            outcome_distribution=outcome_distribution,
            top_objections=top_objections,
            sentiment_distribution=sentiment_distribution,
            total_cost=campaign.total_cost,
            cost_per_call=cost_per_call,
            cost_per_conversion=cost_per_conversion,
            avg_call_duration=campaign.avg_call_duration,
            campaign_duration=campaign_duration,
            timeline_data=timeline_data,
            recent_calls=recent_calls
        )

    async def _execute_campaign(self, campaign_id: str):
        """
        Execute campaign by calling contacts in batches with concurrency control and intervals.

        Args:
            campaign_id: Campaign ID to execute
        """
        try:
            campaign = await self.get_campaign(campaign_id)
            if not campaign:
                logger.error(f"Campaign {campaign_id} not found")
                return

            # Get audience contacts
            # Reason: Query audience by UUID id field, not MongoDB ObjectId
            audience = await self.audiences_collection.find_one({"id": campaign.audience_id})
            if not audience:
                logger.error(f"Audience {campaign.audience_id} not found")
                await self._mark_campaign_failed(campaign_id, "Audience not found")
                return

            # Reason: Contacts are stored in separate audience_contacts collection
            cursor = self.audience_contacts_collection.find({"audience_id": campaign.audience_id})
            contacts = await cursor.to_list(length=None)
            if not contacts:
                logger.error(f"Audience {campaign.audience_id} has no contacts")
                await self._mark_campaign_failed(campaign_id, "No contacts in audience")
                return

            # Clean up phone numbers to fix any double country code issues
            def _clean_phone_number(phone: str) -> str:
                """Clean phone number to fix double country codes and ensure E.164 format."""
                if not phone:
                    return ""
                # Remove all non-digit characters except +
                normalized = "".join(c for c in phone if c.isdigit() or c == "+")
                if not normalized:
                    return ""
                # Remove all + signs and get digits only
                digits_only = normalized.replace("+", "")
                # Check for double country codes (e.g., 233233...)
                # Common country codes to check
                country_codes = ["233", "234", "254", "27", "256", "255", "251", "250", "1", "44", "33", "49", "91", "86"]
                for cc in country_codes:
                    if digits_only.startswith(cc + cc):
                        # Remove duplicate country code
                        digits_only = digits_only[len(cc):]
                        break
                # Ensure it starts with +
                return f"+{digits_only}" if digits_only else ""

            # Clean phone numbers in contacts
            for contact in contacts:
                if contact.get("phone"):
                    cleaned_phone = _clean_phone_number(contact["phone"])
                    if cleaned_phone:
                        contact["phone"] = cleaned_phone
                    else:
                        logger.warning(f"Invalid phone number in contact: {contact.get('phone')}")

            # Get automation details for triggering calls
            automation = await self.automations_collection.find_one({"_id": ObjectId(campaign.automation_id)})
            if not automation:
                logger.error(f"Automation {campaign.automation_id} not found")
                await self._mark_campaign_failed(campaign_id, "Automation not found")
                return

            # Start from current index (resume from where we left off)
            start_index = campaign.progress.current_contact_index

            # Get concurrency and interval settings from config
            max_concurrent = campaign.config.max_concurrent_calls or 1
            batch_interval = campaign.config.batch_interval_seconds or 10
            call_delay = campaign.config.call_delay_seconds or 30

            logger.info(
                f"Executing campaign {campaign_id} starting from contact {start_index}/{len(contacts)} "
                f"with max {max_concurrent} concurrent calls, batch interval {batch_interval}s"
            )
            
            # Helper function to check if current time is within allowed calling window
            def is_within_calling_window(config) -> bool:
                """Check if current time is within the allowed calling window."""
                if not config.start_time and not config.pause_time:
                    return True  # No time restrictions
                
                now = datetime.now(timezone.utc)
                current_time = now.time()
                
                try:
                    # Parse start_time and pause_time (format: HH:MM)
                    start_time_str = config.start_time
                    pause_time_str = config.pause_time
                    
                    if start_time_str:
                        start_hour, start_minute = map(int, start_time_str.split(':'))
                        start_window = dt_time(start_hour, start_minute)
                    else:
                        start_window = dt_time(0, 0)  # Default to midnight
                    
                    if pause_time_str:
                        pause_hour, pause_minute = map(int, pause_time_str.split(':'))
                        pause_window = dt_time(pause_hour, pause_minute)
                    else:
                        pause_window = dt_time(23, 59)  # Default to end of day
                    
                    # Handle case where pause_time is before start_time (e.g., 18:00 to 09:00)
                    if pause_window < start_window:
                        # Window spans midnight - current time should be >= start OR < pause
                        return current_time >= start_window or current_time < pause_window
                    else:
                        # Normal window - current time should be >= start AND < pause
                        return start_window <= current_time < pause_window
                        
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Invalid time format in campaign config: {e}")
                    return True  # Default to allowing calls if time format is invalid
            
            # Check if we should start/resume based on time window
            if not is_within_calling_window(campaign.config):
                logger.info(
                    f"Campaign {campaign_id} is outside calling window "
                    f"(start: {campaign.config.start_time}, pause: {campaign.config.pause_time}). "
                    f"Pausing campaign."
                )
                await self._pause_campaign_auto(campaign_id, "Outside calling time window")
                return

            # Create semaphore to limit concurrent calls
            semaphore = asyncio.Semaphore(max_concurrent)

            async def process_contact(idx: int, contact: dict):
                """Process a single contact with concurrency control."""
                async with semaphore:
                    # Check if campaign is still running
                    current_campaign = await self.get_campaign(campaign_id)
                    if current_campaign.status != "running":
                        logger.info(f"Campaign {campaign_id} stopped at contact {idx}")
                        return
                    
                    # Check time window before each call
                    if not is_within_calling_window(current_campaign.config):
                        logger.info(
                            f"Campaign {campaign_id} reached pause time ({current_campaign.config.pause_time}). "
                            f"Pausing at contact {idx}."
                        )
                        await self._pause_campaign_auto(campaign_id, f"Reached pause time {current_campaign.config.pause_time}")
                        return

                    try:
                        # Get assistant_id from automation for tracking
                        assistant_id = None
                        deployment_info = automation.get("deployment_info", {})
                        if deployment_info and isinstance(deployment_info, dict):
                            assistant_id = deployment_info.get("vapi_assistant_id")

                        if not assistant_id:
                            vapi_agent = automation.get("vapi_agent") or automation.get("vapiAgent", {})
                            if isinstance(vapi_agent, dict):
                                assistant_id = vapi_agent.get("assistant_id") or vapi_agent.get("assistantId")

                        if not assistant_id:
                            assistant_id = automation.get("assistant_id")

                        # Create campaign call record with organization context and phone tracking
                        call_record_id = await self._create_campaign_call_record(
                            campaign_id=campaign_id,
                            automation_id=campaign.automation_id,
                            contact=CampaignContact(**contact),
                            contact_index=idx,
                            organization_id=campaign.organization_id,
                            phone_id=campaign.phone_id,
                            assistant_id=assistant_id
                        )

                        # Increment triggered counter before making the call
                        await self._increment_triggered_count(campaign_id)

                        # Track recently called number
                        await self._add_recently_called_number(
                            campaign_id=campaign_id,
                            phone=contact.get("phone", "Unknown"),
                            name=contact.get("name"),
                            call_record_id=call_record_id
                        )

                        # Check if campaign should use Asterisk instead of VAPI
                        use_asterisk = campaign.config.use_asterisk if hasattr(campaign.config, 'use_asterisk') else False

                        if use_asterisk:
                            # Trigger Asterisk voice AI call
                            await self._trigger_asterisk_call(
                                automation=automation,
                                contact=contact,
                                campaign_id=campaign_id,
                                call_record_id=call_record_id
                            )
                        else:
                            # Trigger VAPI call (original behavior)
                            await self._trigger_call(
                                automation=automation,
                                contact=contact,
                                campaign_id=campaign_id,
                                call_record_id=call_record_id,
                                phone_id=campaign.phone_id
                            )

                        # Update campaign progress (current index)
                        await self._update_campaign_progress(
                            campaign_id=campaign_id,
                            current_index=idx + 1
                        )

                        # Wait for call delay before allowing next call from this slot
                        await asyncio.sleep(call_delay)

                    except Exception as e:
                        logger.error(f"Error processing contact {idx} in campaign {campaign_id}: {e}")
                        # Mark call as failed if call_record_id was created
                        try:
                            if 'call_record_id' in locals():
                                await self.campaign_calls_collection.update_one(
                                    {"_id": call_record_id},
                                    {
                                        "$set": {
                                            "status": "failed",
                                            "error_message": str(e),
                                            "completed_at": datetime.now(timezone.utc)
                                        }
                                    }
                                )
                                # Update campaign progress counters for failed call
                                await self.campaigns_collection.update_one(
                                    {"_id": campaign_id},
                                    {
                                        "$inc": {
                                            "progress.called": 1,
                                            "progress.completed": 1,
                                            "progress.failed": 1
                                        },
                                        "$set": {
                                            "updated_at": datetime.now(timezone.utc)
                                        }
                                    }
                                )
                        except Exception as update_error:
                            logger.error(f"Failed to update call record: {update_error}")

            # Process contacts in batches with intervals
            remaining_contacts = contacts[start_index:]
            total_remaining = len(remaining_contacts)

            for batch_start in range(0, total_remaining, max_concurrent):
                # Check if campaign is still running
                current_campaign = await self.get_campaign(campaign_id)
                if current_campaign.status != "running":
                    logger.info(f"Campaign {campaign_id} stopped at batch {batch_start}")
                    break

                # Get batch of contacts
                batch_end = min(batch_start + max_concurrent, total_remaining)
                batch_contacts = remaining_contacts[batch_start:batch_end]

                logger.info(
                    f"Processing batch {batch_start // max_concurrent + 1}: "
                    f"contacts {start_index + batch_start} to {start_index + batch_end - 1}"
                )

                # Create tasks for this batch
                batch_tasks = [
                    process_contact(start_index + batch_start + i, contact)
                    for i, contact in enumerate(batch_contacts)
                ]

                # Execute batch with concurrency control
                await asyncio.gather(*batch_tasks, return_exceptions=True)

                # Wait for batch interval before next batch (except for last batch)
                if batch_end < total_remaining:
                    logger.info(f"Waiting {batch_interval}s before next batch...")
                    await asyncio.sleep(batch_interval)

            # Only mark as completed if all contacts were actually processed
            # Check current campaign state to see if it was paused/stopped mid-execution
            final_campaign = await self.get_campaign(campaign_id)
            if final_campaign and final_campaign.progress.called >= final_campaign.progress.total_contacts:
                await self._mark_campaign_completed(campaign_id)
                logger.info(f"Campaign {campaign_id} completed successfully - all {final_campaign.progress.total_contacts} contacts processed")
            elif final_campaign and final_campaign.status == "running":
                # Campaign still running but loop ended - this shouldn't happen, mark as completed
                await self._mark_campaign_completed(campaign_id)
                logger.info(f"Campaign {campaign_id} completed - loop finished while still running")
            else:
                # Campaign was paused/stopped mid-execution, don't mark as completed
                logger.info(f"Campaign {campaign_id} execution stopped - status: {final_campaign.status if final_campaign else 'unknown'}, called: {final_campaign.progress.called if final_campaign else 0}/{final_campaign.progress.total_contacts if final_campaign else 0}")

        except asyncio.CancelledError:
            logger.info(f"Campaign {campaign_id} execution cancelled")
            raise
        except Exception as e:
            logger.error(f"Fatal error executing campaign {campaign_id}: {e}")
            await self._mark_campaign_failed(campaign_id, str(e))

    async def _create_campaign_call_record(
        self,
        campaign_id: str,
        automation_id: str,
        contact: CampaignContact,
        contact_index: int,
        organization_id: Optional[str] = None,
        phone_id: Optional[str] = None,
        assistant_id: Optional[str] = None
    ) -> str:
        """
        Create a campaign call record.

        Args:
            campaign_id: Campaign ID
            automation_id: Automation ID
            contact: Contact being called
            contact_index: Contact index in list
            organization_id: Optional organization ID for multi-tenant isolation
            phone_id: Optional phone number ID used for this call
            assistant_id: Optional assistant ID used for this call

        Returns:
            Call record ID
        """
        call_id = str(ObjectId())
        now = datetime.now(timezone.utc)

        call_record = CampaignCall(
            id=call_id,
            campaign_id=campaign_id,
            automation_id=automation_id,
            contact=contact,
            contact_index=contact_index,
            status="calling",
            created_at=now,
            called_at=now,
            phone_id=phone_id,
            assistant_id=assistant_id
        )

        call_dict = call_record.dict(exclude_none=True)
        call_dict["_id"] = call_id

        # Add organization_id for multi-tenant isolation
        if organization_id:
            call_dict["organization_id"] = organization_id

        await self.campaign_calls_collection.insert_one(call_dict)

        return call_id

    async def _trigger_call(
        self,
        automation: Dict[str, Any],
        contact: Dict[str, Any],
        campaign_id: str,
        call_record_id: str,
        phone_id: Optional[str] = None
    ):
        """
        Trigger a VAPI call for the contact.

        Args:
            automation: Automation configuration
            contact: Contact to call
            campaign_id: Campaign ID
            call_record_id: Call record ID
            phone_id: Optional VAPI phone number ID (overrides default)
        """
        # Import here to avoid circular dependency
        import httpx
        import os

        # Get assistant ID from automation
        # Check multiple possible locations in order of preference:
        # 1. deployment_info.vapi_assistant_id (deployed automations)
        # 2. vapi_agent.assistant_id (snake_case format)
        # 3. vapiAgent.assistantId (camelCase format)
        # 4. assistant_id (top-level field)
        assistant_id = None
        
        # Check deployment_info first (most common for deployed automations)
        deployment_info = automation.get("deployment_info", {})
        if deployment_info and deployment_info.get("vapi_assistant_id"):
            assistant_id = deployment_info.get("vapi_assistant_id")
            logger.info(f"Found assistant_id in deployment_info: {assistant_id}")
        
        # Check vapi_agent (snake_case)
        if not assistant_id:
            vapi_agent = automation.get("vapi_agent", {})
            if vapi_agent and vapi_agent.get("assistant_id"):
                assistant_id = vapi_agent.get("assistant_id")
                logger.info(f"Found assistant_id in vapi_agent: {assistant_id}")
        
        # Check vapiAgent (camelCase)
        if not assistant_id:
            vapi_agent_camel = automation.get("vapiAgent", {})
            if vapi_agent_camel and vapi_agent_camel.get("assistantId"):
                assistant_id = vapi_agent_camel.get("assistantId")
                logger.info(f"Found assistant_id in vapiAgent: {assistant_id}")
        
        # Check top-level field
        if not assistant_id:
            assistant_id = automation.get("assistant_id")
            if assistant_id:
                logger.info(f"Found assistant_id at top level: {assistant_id}")

        if not assistant_id:
            logger.error(f"Automation {automation.get('_id')} structure: {list(automation.keys())}")
            raise ValueError(f"No VAPI assistant ID found for automation {automation.get('_id')}. Checked deployment_info.vapi_assistant_id, vapi_agent.assistant_id, vapiAgent.assistantId, and assistant_id")

        # Use provided phone_id from campaign, or fallback to environment variable, or default
        # Priority: campaign phone_id > VAPI_PRIMARY_PHONE_ID env var > default phone ID
        if phone_id:
            phone_number_id = phone_id
            logger.info(f"Using campaign-selected phone number ID: {phone_number_id} for campaign {campaign_id}")
        else:
            phone_number_id = os.getenv("VAPI_PRIMARY_PHONE_ID")
            if phone_number_id:
                logger.info(f"Using VAPI_PRIMARY_PHONE_ID from environment: {phone_number_id} for campaign {campaign_id}")
            else:
                phone_number_id = "6c5af6e1-a2b7-41d6-ac04-4c9691bf73e4"
                logger.info(f"Using default phone number ID: {phone_number_id} for campaign {campaign_id}")

        # Import VAPI service
        import sys
        sys.path.append('/opt/kasaai/apps/shared')
        from integration.vapi import vapi_service

        # Ensure VAPI service is initialized with API key
        if not vapi_service.api_key:
            vapi_service.api_key = os.getenv("VAPI_API_KEY")
            if not vapi_service.api_key:
                raise ValueError("VAPI_API_KEY not configured in environment")
            # Reinitialize client with API key
            vapi_service._initialize_client()

        # Check if custom_settings_override exists and apply to VAPI assistant
        # This ensures that campaigns use the custom voice settings when making calls
        vapi_agent = automation.get("vapi_agent") or automation.get("vapiAgent", {})
        custom_override = vapi_agent.get("custom_settings_override") or vapi_agent.get("customSettingsOverride")

        if custom_override:
            logger.info(f"Custom settings override detected for automation {automation.get('_id')}, applying to VAPI assistant")
            # Apply custom settings to VAPI assistant before making the call
            await self._apply_custom_settings_to_vapi(assistant_id, vapi_agent, custom_override)

        logger.info(
            f"Triggering VAPI call: assistant_id={assistant_id}, "
            f"phone_id={phone_number_id}, customer={contact['phone']}, "
            f"custom_settings={'enabled' if custom_override else 'disabled'}"
        )

        # Use VAPI service to create call
        # Note: If custom_settings_override is configured, the assistant already has
        # custom provider webhooks set up, so VAPI will automatically route to our
        # custom TTS/ASR/LLM webhooks which use the custom settings
        result = await vapi_service.create_phone_call(
            phone_number_id=phone_number_id,
            customer_number=contact["phone"],
            assistant_id=assistant_id,
            metadata={
                "campaign_id": campaign_id,
                "call_record_id": call_record_id,
                "contact_name": contact.get("name"),
                "automation_id": str(automation["_id"])
            }
        )

        if result.get("success"):
            # VAPI response can have call_id at top level or in call object
            vapi_call_id = result.get("call_id") or result.get("call", {}).get("id")
            
            if not vapi_call_id:
                logger.warning(f"VAPI call succeeded but no call_id in response: {result}")
                # Try to extract from full response
                vapi_call_id = result.get("id")

            if vapi_call_id:
                # Update call record with VAPI call ID
                await self.campaign_calls_collection.update_one(
                    {"_id": call_record_id},
                    {"$set": {"call_id": vapi_call_id}}
                )

                logger.info(f"✅ Triggered call {vapi_call_id} for campaign {campaign_id} to {contact['phone']}")
            else:
                logger.error(f"❌ VAPI call succeeded but no call_id found in response: {result}")
                # Mark as failed since we can't track it
                await self.campaign_calls_collection.update_one(
                    {"_id": call_record_id},
                    {
                        "$set": {
                            "status": "failed",
                            "error_message": "VAPI call succeeded but no call_id returned",
                            "completed_at": datetime.now(timezone.utc)
                        }
                    }
                )
        else:
            error_msg = result.get("error", "Unknown error")
            status_code = result.get("status_code", "N/A")
            logger.error(
                f"❌ Failed to trigger call for campaign {campaign_id} to {contact['phone']}: "
                f"{error_msg} (status: {status_code})"
            )

            # Mark call as failed
            await self.campaign_calls_collection.update_one(
                {"_id": call_record_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": f"{error_msg} (HTTP {status_code})",
                        "completed_at": datetime.now(timezone.utc)
                    }
                }
            )

    async def _trigger_asterisk_call(
        self,
        automation: Dict[str, Any],
        contact: Dict[str, Any],
        campaign_id: str,
        call_record_id: str
    ):
        """
        Trigger a voice AI call through Asterisk instead of VAPI.

        This uses our own infrastructure with local TTS/ASR/LLM providers,
        resulting in $0 costs for voice synthesis and transcription.

        Args:
            automation: Automation configuration
            contact: Contact to call
            campaign_id: Campaign ID
            call_record_id: Call record ID
        """
        from .asterisk_voice_service import (
            AsteriskVoiceCallRequest,
            get_asterisk_voice_service,
        )

        try:
            # Get voice settings from automation config
            vapi_agent = automation.get("vapi_agent") or automation.get("vapiAgent", {})
            custom_override = vapi_agent.get("custom_settings_override") or vapi_agent.get("customSettingsOverride", {})

            # Build voice call request
            tts_settings = custom_override.get("tts", {})
            asr_settings = custom_override.get("asr", {})
            llm_settings = custom_override.get("llm", {})

            request = AsteriskVoiceCallRequest(
                destination=contact["phone"],
                automation_id=str(automation.get("_id", automation.get("id", ""))),
                source_number="0308249843",  # Default caller ID
                tts_provider=tts_settings.get("provider", "kokoro"),
                tts_voice=tts_settings.get("voice", "af_heart"),
                asr_provider=asr_settings.get("provider", "faster_whisper"),
                asr_model=asr_settings.get("model", "medium"),
                llm_provider=llm_settings.get("provider", "openai"),
                llm_model=llm_settings.get("model", "gpt-4o-mini"),
                campaign_id=campaign_id,
                contact_id=call_record_id,
            )

            # Get Asterisk voice service
            service = get_asterisk_voice_service()

            # Originate the call
            result = await service.originate_voice_call(request)

            if result.success:
                # Update call record with Asterisk call ID
                await self.campaign_calls_collection.update_one(
                    {"_id": call_record_id},
                    {
                        "$set": {
                            "call_id": result.call_id,
                            "use_asterisk": True
                        }
                    }
                )

                logger.info(
                    f"✅ Triggered Asterisk call {result.call_id} for campaign "
                    f"{campaign_id} to {contact['phone']}"
                )
            else:
                logger.error(
                    f"❌ Failed to trigger Asterisk call for campaign {campaign_id} "
                    f"to {contact['phone']}: {result.message}"
                )

                # Mark call as failed
                await self.campaign_calls_collection.update_one(
                    {"_id": call_record_id},
                    {
                        "$set": {
                            "status": "failed",
                            "error_message": result.message,
                            "completed_at": datetime.now(timezone.utc),
                            "use_asterisk": True
                        }
                    }
                )

        except Exception as e:
            logger.error(
                f"Error triggering Asterisk call for campaign {campaign_id}: {e}",
                exc_info=True
            )

            # Mark call as failed
            await self.campaign_calls_collection.update_one(
                {"_id": call_record_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": str(e),
                        "completed_at": datetime.now(timezone.utc),
                        "use_asterisk": True
                    }
                }
            )

    async def _apply_custom_settings_to_vapi(
        self,
        assistant_id: str,
        vapi_agent: Dict[str, Any],
        custom_override: Dict[str, Any]
    ):
        """
        Apply custom TTS/ASR/LLM settings to VAPI assistant.

        Uses VAPI's custom-voice and custom-transcriber providers to route
        to our custom endpoints (e.g., kokoro.ailabsafrica.com/synthesize).

        Args:
            assistant_id: VAPI assistant ID
            vapi_agent: VAPIAgent configuration
            custom_override: Custom settings override object
        """
        import httpx
        from .vapi_assistant_builder import build_vapi_assistant_config

        try:
            # Build VAPI-compatible config with custom provider URLs
            vapi_config = build_vapi_assistant_config(vapi_agent, assistant_id)

            # Only update voice and transcriber to preserve other assistant settings
            update_payload = {}
            if "voice" in vapi_config:
                update_payload["voice"] = vapi_config["voice"]
            if "transcriber" in vapi_config:
                update_payload["transcriber"] = vapi_config["transcriber"]
            if "metadata" in vapi_config:
                update_payload["metadata"] = vapi_config["metadata"]

            if not update_payload:
                logger.info(f"No custom settings to apply for assistant {assistant_id}")
                return

            # Update VAPI assistant
            vapi_api_key = os.getenv("VAPI_API_KEY")
            if not vapi_api_key:
                logger.error("VAPI_API_KEY not configured, cannot apply custom settings")
                return

            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"https://api.vapi.ai/assistant/{assistant_id}",
                    headers={
                        "Authorization": f"Bearer {vapi_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=update_payload,
                    timeout=30.0
                )

                if response.status_code == 200:
                    logger.info(f"Successfully applied custom settings to VAPI assistant {assistant_id}")
                    logger.info(f"Updated voice: {update_payload.get('voice', {}).get('provider', 'default')}")
                    logger.info(f"Updated transcriber: {update_payload.get('transcriber', {}).get('provider', 'default')}")
                else:
                    logger.error(
                        f"Failed to update VAPI assistant {assistant_id}: "
                        f"{response.status_code} - {response.text}"
                    )

        except Exception as e:
            logger.error(f"Error applying custom settings to VAPI assistant: {e}", exc_info=True)

    async def _increment_triggered_count(self, campaign_id: str):
        """
        Increment the triggered calls counter.

        Args:
            campaign_id: Campaign ID
        """
        await self.campaigns_collection.update_one(
            {"_id": campaign_id},
            {
                "$inc": {"progress.triggered": 1, "progress.pending": -1},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
        logger.info(f"Incremented triggered count for campaign {campaign_id}")

    async def _add_recently_called_number(
        self,
        campaign_id: str,
        phone: str,
        name: Optional[str] = None,
        call_record_id: Optional[str] = None
    ):
        """
        Add a recently called number to the campaign's recently_called_numbers list.
        Keeps only the last 20 numbers.

        Args:
            campaign_id: Campaign ID
            phone: Phone number that was called
            name: Optional contact name
            call_record_id: Optional call record ID
        """
        now = datetime.now(timezone.utc)
        called_entry = {
            "phone": phone,
            "name": name,
            "call_record_id": call_record_id,
            "called_at": now.isoformat(),
            "timestamp": now.timestamp()
        }

        # Get current campaign to access recently_called_numbers
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return

        # Get current list and add new entry
        recent_numbers = campaign.recently_called_numbers or []
        recent_numbers.append(called_entry)

        # Keep only last 20 entries
        if len(recent_numbers) > 20:
            recent_numbers = recent_numbers[-20:]

        # Update campaign
        await self.campaigns_collection.update_one(
            {"_id": campaign_id},
            {
                "$set": {
                    "recently_called_numbers": recent_numbers,
                    "updated_at": now
                }
            }
        )

    async def _update_campaign_progress(self, campaign_id: str, current_index: int):
        """
        Update campaign progress.

        Args:
            campaign_id: Campaign ID
            current_index: Current contact index
        """
        await self.campaigns_collection.update_one(
            {"_id": campaign_id},
            {
                "$set": {
                    "progress.current_contact_index": current_index,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

    async def _mark_campaign_completed(self, campaign_id: str):
        """
        Mark campaign as completed and trigger analytics sync.

        Args:
            campaign_id: Campaign ID
        """
        now = datetime.now(timezone.utc)
        await self.campaigns_collection.update_one(
            {"_id": campaign_id},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": now,
                    "updated_at": now
                }
            }
        )

        # Remove from running campaigns
        if campaign_id in self._running_campaigns:
            del self._running_campaigns[campaign_id]
        
        # Trigger analytics sync for the automation
        try:
            campaign = await self.get_campaign(campaign_id)
            if campaign and campaign.automation_id:
                logger.info(f"Triggering analytics sync for automation {campaign.automation_id} after campaign completion")
                from ..services.automation_analytics_service import AutomationAnalyticsService
                from ..mongo import get_database
                
                db = get_database()
                analytics_service = AutomationAnalyticsService(db)
                sync_result = await analytics_service.sync_automation_calls(
                    config_id=campaign.automation_id,
                    organization_id=campaign.organization_id if hasattr(campaign, 'organization_id') else None
                )
                if sync_result.get("success"):
                    logger.info(f"✅ Analytics synced: {sync_result.get('calls_synced', 0)} calls")
                else:
                    logger.warning(f"⚠️ Analytics sync failed: {sync_result.get('error')}")
        except Exception as sync_error:
            logger.warning(f"Failed to sync analytics after campaign completion: {sync_error}")

    async def _mark_campaign_failed(self, campaign_id: str, error_message: str):
        """
        Mark campaign as failed.

        Args:
            campaign_id: Campaign ID
            error_message: Error message
        """
        now = datetime.now(timezone.utc)
        await self.campaigns_collection.update_one(
            {"_id": campaign_id},
            {
                "$set": {
                    "status": "failed",
                    "error_message": error_message,
                    "completed_at": now,
                    "updated_at": now
                }
            }
        )

        # Remove from running campaigns
        if campaign_id in self._running_campaigns:
            del self._running_campaigns[campaign_id]

    async def _generate_timeline_data(self, campaign_id: str) -> List[Dict[str, Any]]:
        """
        Generate timeline data for charts.

        Args:
            campaign_id: Campaign ID

        Returns:
            List of timeline data points
        """
        # Group calls by hour
        pipeline = [
            {"$match": {"campaign_id": campaign_id, "status": "completed"}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d %H:00",
                            "date": "$called_at"
                        }
                    },
                    "calls": {"$sum": 1},
                    "conversions": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$outcome.outcome", "converted"]},
                                1,
                                0
                            ]
                        }
                    }
                }
            },
            {"$sort": {"_id": 1}}
        ]

        timeline_data = []
        async for doc in self.campaign_calls_collection.aggregate(pipeline):
            timeline_data.append({
                "time": doc["_id"],
                "calls": doc["calls"],
                "conversions": doc["conversions"]
            })

        return timeline_data

    async def update_campaign(self, campaign_id: str, config_update: Dict[str, Any]) -> AutomationCampaign:
        """
        Update campaign configuration and phone_id.

        Args:
            campaign_id: Campaign ID to update
            config_update: Dictionary of config fields and phone_id to update

        Returns:
            Updated campaign

        Raises:
            ValueError: If campaign not found or is running (must be paused first)
        """
        # Fetch campaign
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Cannot update running campaigns
        if campaign.status == "running":
            raise ValueError("Cannot update a running campaign. Pause it first.")

        # Extract allowed config fields
        allowed_config_fields = {
            "call_delay_seconds",
            "batch_interval_seconds",
            "max_retries",
            "retry_on_no_answer",
            "max_concurrent_calls",
            "start_time",
            "pause_time",
            "auto_start",
            "use_asterisk"
        }

        # Extract allowed top-level campaign fields
        allowed_campaign_fields = {
            "phone_id"
        }

        # Build update dict
        updates = {}
        for field, value in config_update.items():
            if field in allowed_config_fields:
                updates[f"config.{field}"] = value
            elif field in allowed_campaign_fields:
                updates[field] = value

        if not updates:
            raise ValueError("No valid configuration fields to update")

        # Update campaign
        now = datetime.now(timezone.utc)
        updates["updated_at"] = now

        await self.campaigns_collection.update_one(
            {"_id": campaign_id},
            {"$set": updates}
        )

        # Fetch and return updated campaign
        updated_campaign = await self.get_campaign(campaign_id)
        logger.info(f"Updated campaign {campaign_id} with fields: {updates}")

        return updated_campaign

    async def delete_campaign(self, campaign_id: str) -> bool:
        """
        Delete a campaign and all associated call records.

        Args:
            campaign_id: Campaign ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            # Check if campaign exists
            campaign = await self.get_campaign(campaign_id)
            if not campaign:
                logger.warning(f"Campaign {campaign_id} not found for deletion")
                return False

            # Delete all associated call records
            call_delete_result = await self.campaign_calls_collection.delete_many(
                {"campaign_id": campaign_id}
            )
            logger.info(f"Deleted {call_delete_result.deleted_count} call records for campaign {campaign_id}")

            # Delete the campaign
            campaign_delete_result = await self.campaigns_collection.delete_one(
                {"_id": campaign_id}
            )

            if campaign_delete_result.deleted_count == 0:
                logger.warning(f"Campaign {campaign_id} was not deleted")
                return False

            # Remove from running campaigns if active
            if campaign_id in self._running_campaigns:
                self._running_campaigns[campaign_id].cancel()
                del self._running_campaigns[campaign_id]
                logger.info(f"Cancelled running task for campaign {campaign_id}")

            logger.info(f"Successfully deleted campaign {campaign_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting campaign {campaign_id}: {e}")
            raise

    async def retry_missed_calls(self, campaign_id: str) -> Dict[str, Any]:
        """
        Retry missed calls for a campaign.
        
        Missed calls are defined as calls where:
        - status is 'failed', OR
        - duration is None/0/not set, OR
        - cost is None/0/not set
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Dictionary with retry_count indicating how many calls were queued for retry
            
        Raises:
            ValueError: If campaign not found or campaign is running
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
            
        # Only allow retry for paused or completed campaigns
        if campaign.status == "running":
            raise ValueError("Cannot retry missed calls while campaign is running. Please pause the campaign first.")
        
        # Find all missed calls: status=failed OR duration is None/0 OR cost is None/0
        query = {
            "campaign_id": campaign_id,
            "$or": [
                {"status": "failed"},
                {"duration": {"$in": [None, 0]}},
                {"cost": {"$in": [None, 0]}},
                {"duration": {"$exists": False}},
                {"cost": {"$exists": False}}
            ]
        }
        
        # Get all missed calls
        missed_calls = await self.campaign_calls_collection.find(query).to_list(length=None)
        
        if not missed_calls:
            return {"retry_count": 0, "message": "No missed calls found to retry"}
        
        retry_count = 0
        
        # Reset missed calls to pending status so they can be retried
        for call_doc in missed_calls:
            call_id = str(call_doc.get("_id", ""))
            contact_index = call_doc.get("contact_index", 0)
            
            # Reset the call record to pending
            await self.campaign_calls_collection.update_one(
                {"_id": call_doc["_id"]},
                {
                    "$set": {
                        "status": "pending",
                        "call_id": None,
                        "attempt_number": call_doc.get("attempt_number", 1) + 1,
                        "retry_reason": "Manual retry of missed call",
                        "error_message": None,
                        "completed_at": None,
                        "called_at": None
                    },
                    "$unset": {
                        "duration": "",
                        "cost": ""
                    }
                }
            )
            
            # Reset progress counters if needed (decrement failed count if status was failed)
            if call_doc.get("status") == "failed":
                await self.campaigns_collection.update_one(
                    {"_id": campaign_id},
                    {
                        "$inc": {
                            "progress.failed": -1,
                            "progress.pending": 1
                        },
                        "$set": {
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
            
            retry_count += 1
        
        # If campaign is completed, change status to paused so it can be resumed to retry the calls
        if campaign.status == "completed":
            await self.campaigns_collection.update_one(
                {"_id": campaign_id},
                {
                    "$set": {
                        "status": "paused",
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
        
        logger.info(f"Queued {retry_count} missed calls for retry in campaign {campaign_id}")
        
        return {
            "retry_count": retry_count,
            "message": f"Queued {retry_count} missed call{'s' if retry_count != 1 else ''} for retry"
        }

    async def update_call_outcome(
        self,
        call_id: str,
        outcome: CallOutcome,
        transcript: str,
        summary: str,
        duration: int,
        cost: float
    ):
        """
        Update campaign call with outcome data from webhook.

        Args:
            call_id: VAPI call ID
            outcome: Call outcome analysis
            transcript: Call transcript
            summary: AI summary
            duration: Call duration
            cost: Call cost
        """
        # Find call record by VAPI call ID
        call_record = await self.campaign_calls_collection.find_one({"call_id": call_id})
        
        # If not found, try alternative lookup by _id if call_id was passed as call_record_id
        if not call_record:
            logger.warning(f"Campaign call record not found for call_id {call_id}, trying alternative lookup")
            # Try to find by _id if call_id matches a record ID
            try:
                call_record = await self.campaign_calls_collection.find_one({"_id": call_id})
            except Exception:
                pass
        
        if not call_record:
            logger.warning(f"Campaign call record not found for call {call_id} - webhook may have arrived before call_id was set")
            return

        # Update call record
        now = datetime.now(timezone.utc)
        
        # Ensure duration is preserved if existing duration is valid and new one is 0
        final_duration = duration
        if duration == 0 and call_record.get("duration") and call_record.get("duration") > 0:
            final_duration = call_record.get("duration")
            logger.debug(f"Preserving existing duration {final_duration}s for call {call_id} (new duration was 0)")
        
        # Ensure cost is preserved if existing cost is valid and new one is 0
        final_cost = cost
        if cost == 0 and call_record.get("cost") and call_record.get("cost") > 0:
            final_cost = call_record.get("cost")
            logger.debug(f"Preserving existing cost ${final_cost} for call {call_id} (new cost was 0)")
        
        update_fields = {
            "status": "completed",
            "outcome": outcome.dict(),
            "transcript": transcript,
            "ai_summary": summary,
            "completed_at": now
        }
        
        # Only set duration if we have a valid value
        if final_duration > 0:
            update_fields["duration"] = final_duration
        # Only set cost if we have a valid value
        if final_cost > 0:
            update_fields["cost"] = final_cost
        
        await self.campaign_calls_collection.update_one(
            {"_id": call_record["_id"]},
            {"$set": update_fields}
        )

        # Update campaign totals
        campaign_id = call_record["campaign_id"]
        campaign = await self.get_campaign(campaign_id)

        if campaign:
            # Calculate phone cost
            phone_cost_per_minute = 0.15
            if campaign.phone_id:
                try:
                    from backend.services.phone_management_service import get_phone_manager
                    phone_manager = get_phone_manager()
                    phone = phone_manager.get_phone(campaign.phone_id)
                    if phone:
                        phone_cost_per_minute = phone.cost_per_minute
                except Exception as e:
                    logger.warning(f"Could not get phone rate for {campaign.phone_id}, using default: {e}")

            duration_minutes = duration / 60.0
            phone_cost_ghc = duration_minutes * phone_cost_per_minute

            # Calculate new averages
            called = campaign.progress.called + 1
            new_vapi_cost_usd = campaign.total_vapi_cost_usd + cost
            new_phone_cost_ghc = campaign.total_phone_cost_ghc + phone_cost_ghc
            new_total_cost = campaign.total_cost + cost + phone_cost_ghc
            new_avg_duration = ((campaign.avg_call_duration * campaign.progress.called) + duration) / called

            # Update progress based on outcome
            update_fields = {
                "progress.called": called,
                "progress.pending": campaign.progress.pending - 1,
                "total_cost": new_total_cost,
                "total_vapi_cost_usd": new_vapi_cost_usd,
                "total_phone_cost_ghc": new_phone_cost_ghc,
                "avg_call_duration": new_avg_duration,
                "updated_at": now
            }

            if outcome.outcome == "converted":
                update_fields["progress.conversion_count"] = campaign.progress.conversion_count + 1
                update_fields["progress.successful"] = campaign.progress.successful + 1
            elif outcome.outcome in ["error", "failed"]:
                update_fields["progress.failed"] = campaign.progress.failed + 1
            elif outcome.outcome == "no_answer":
                update_fields["progress.no_answer"] = campaign.progress.no_answer + 1
            else:
                update_fields["progress.successful"] = campaign.progress.successful + 1

            await self.campaigns_collection.update_one(
                {"_id": campaign_id},
                {"$set": update_fields}
            )

            logger.info(f"Updated campaign {campaign_id} with outcome from call {call_id}")

    async def mark_call_completed(
        self,
        campaign_id: str,
        call_id: str,
        status: str,
        cost: float = 0,
        duration: float = 0
    ):
        """
        Mark a campaign call as completed and update progress.

        Args:
            campaign_id: Campaign ID
            call_id: VAPI call ID
            status: Call status (completed, ended, failed, no-answer, etc.)
            cost: Call cost
            duration: Call duration in seconds
        """
        try:
            # Find call record by VAPI call ID
            call_record = await self.campaign_calls_collection.find_one({"call_id": call_id})
            if not call_record:
                logger.warning(f"Campaign call record not found for call {call_id}")
                return

            # Update campaign call record
            # Ensure both cost and duration are set properly
            update_fields = {
                "status": status,
                "completed_at": datetime.now(timezone.utc),
            }
            
            # Set cost if provided
            if cost > 0:
                update_fields["cost"] = cost
            elif call_record.get("cost") and call_record.get("cost") > 0:
                # Preserve existing cost if new one is not provided
                update_fields["cost"] = call_record.get("cost")
            
            # Set duration if provided, or try to preserve existing duration
            if duration > 0:
                update_fields["duration"] = duration
            elif call_record.get("duration") and call_record.get("duration") > 0:
                # Preserve existing duration if new one is not provided
                update_fields["duration"] = call_record.get("duration")
            
            await self.campaign_calls_collection.update_one(
                {"_id": call_record["_id"]},
                {"$set": update_fields}
            )

            # Update campaign progress
            campaign = await self.get_campaign(campaign_id)
            if campaign:
                # Increment completed counter
                new_completed = campaign.progress.completed + 1
                new_called = campaign.progress.called + 1
                new_pending = max(0, campaign.progress.pending - 1)

                # Determine if successful or failed based on status
                is_success = status in ["completed", "ended"]
                is_failed = status in ["failed", "error"]
                is_no_answer = status == "no_answer"

                new_successful = campaign.progress.successful + (1 if is_success else 0)
                new_failed = campaign.progress.failed + (1 if is_failed else 0)
                new_no_answer = campaign.progress.no_answer + (1 if is_no_answer else 0)

                # Calculate phone cost (duration × rate)
                # Get phone cost rate (default GHC 0.15/min if not found)
                phone_cost_per_minute = 0.15
                if campaign.phone_id:
                    try:
                        from backend.services.phone_management_service import get_phone_manager
                        phone_manager = get_phone_manager()
                        phone = phone_manager.get_phone(campaign.phone_id)
                        if phone:
                            phone_cost_per_minute = phone.cost_per_minute
                    except Exception as e:
                        logger.warning(f"Could not get phone rate for {campaign.phone_id}, using default: {e}")

                duration_minutes = duration / 60.0
                phone_cost_ghc = duration_minutes * phone_cost_per_minute

                # Update costs
                # cost = VAPI cost (USD), phone_cost_ghc = phone billing cost (GHC)
                new_vapi_cost_usd = campaign.total_vapi_cost_usd + cost
                new_phone_cost_ghc = campaign.total_phone_cost_ghc + phone_cost_ghc
                new_total_cost = campaign.total_cost + cost + phone_cost_ghc  # Combined cost

                new_avg_duration = (
                    (campaign.avg_call_duration * (new_called - 1) + duration) / new_called
                ) if new_called > 0 else duration

                # Convert campaign_id to ObjectId if it's a string (for MongoDB query)
                campaign_query_id = campaign_id
                if isinstance(campaign_id, str) and len(campaign_id) == 24:
                    try:
                        campaign_query_id = ObjectId(campaign_id)
                    except Exception:
                        # If conversion fails, use as-is
                        campaign_query_id = campaign_id
                
                update_result = await self.campaigns_collection.update_one(
                    {"_id": campaign_query_id},
                    {
                        "$set": {
                            "progress.completed": new_completed,
                            "progress.called": new_called,
                            "progress.pending": new_pending,
                            "progress.successful": new_successful,
                            "progress.failed": new_failed,
                            "progress.no_answer": new_no_answer,
                            "total_cost": new_total_cost,
                            "total_vapi_cost_usd": new_vapi_cost_usd,
                            "total_phone_cost_ghc": new_phone_cost_ghc,
                            "avg_call_duration": new_avg_duration,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                
                if update_result.matched_count == 0:
                    logger.warning(f"Campaign {campaign_id} not found for progress update")
                elif update_result.modified_count == 0:
                    logger.warning(f"Campaign {campaign_id} progress update had no effect (may already be updated)")
                else:
                    logger.info(f"Campaign {campaign_id} progress updated successfully (matched: {update_result.matched_count}, modified: {update_result.modified_count})")

                logger.info(
                    f"Campaign {campaign_id} progress updated: "
                    f"completed={new_completed}/{campaign.progress.total_contacts}, "
                    f"successful={new_successful}, failed={new_failed}, no_answer={new_no_answer}"
                )

        except Exception as e:
            logger.error(f"Error marking call completed for campaign {campaign_id}: {e}")
            raise


async def extract_call_outcome(transcript: str) -> CallOutcome:
    """
    Extract call outcome from transcript using AI analysis.

    Analyzes the transcript to determine:
    - Outcome type (converted, objection, no_answer, error, neutral)
    - Number of conversion signals
    - List of objections with categories
    - Overall sentiment

    Args:
        transcript: Call transcript text

    Returns:
        CallOutcome with extracted data
    """
    # Reason: Simple rule-based extraction for MVP, can be enhanced with AI models later
    try:
        transcript_lower = transcript.lower()

        # Detect conversion signals
        conversion_keywords = [
            "yes, i'm interested", "sign me up", "let's do it", "sounds good",
            "i'll take it", "when can we start", "how do i proceed", "send me the link",
            "i want to", "count me in", "i agree", "perfect"
        ]
        conversion_signals = sum(1 for keyword in conversion_keywords if keyword in transcript_lower)

        # Detect objections with categories
        objection_patterns = {
            "price": ["too expensive", "too pricey", "cost too much", "can't afford", "too high", "budget"],
            "timing": ["not right now", "maybe later", "call back", "not ready", "busy", "wrong time"],
            "interest": ["not interested", "don't need", "no thanks", "not for me", "pass"],
            "information": ["need more info", "tell me more", "not sure", "let me think", "need to check"]
        }

        objections = []
        for category, keywords in objection_patterns.items():
            for keyword in keywords:
                if keyword in transcript_lower:
                    # Find context around the objection
                    idx = transcript_lower.find(keyword)
                    context_start = max(0, idx - 50)
                    context_end = min(len(transcript), idx + len(keyword) + 50)
                    context = transcript[context_start:context_end].strip()

                    objections.append(CallObjection(
                        category=category,
                        text=keyword,
                        context=context,
                        confidence=0.8
                    ))
                    break  # Only add one objection per category

        # Determine sentiment
        positive_words = ["great", "excellent", "wonderful", "perfect", "love", "interested", "yes"]
        negative_words = ["no", "not", "don't", "can't", "won't", "never", "bad", "terrible"]

        positive_count = sum(1 for word in positive_words if word in transcript_lower)
        negative_count = sum(1 for word in negative_words if word in transcript_lower)

        if positive_count > negative_count * 1.5:
            sentiment = "positive"
        elif negative_count > positive_count * 1.5:
            sentiment = "negative"
        elif positive_count == 0 and negative_count == 0:
            sentiment = "neutral"
        else:
            sentiment = "mixed"

        # Determine outcome
        if conversion_signals >= 2:
            outcome = "converted"
        elif len(objections) > 0:
            outcome = "objection"
        elif len(transcript.strip()) < 50:
            outcome = "no_answer"
        elif "error" in transcript_lower or "failed" in transcript_lower:
            outcome = "error"
        else:
            outcome = "neutral"

        # Calculate confidence based on signal strength
        confidence = min(1.0, (conversion_signals * 0.2) + (len(objections) * 0.15) + 0.3)

        return CallOutcome(
            outcome=outcome,
            conversion_signals=conversion_signals,
            objections=objections,
            sentiment=sentiment,
            confidence=confidence
        )

    except Exception as e:
        logger.error(f"Error extracting call outcome: {e}")
        # Return default neutral outcome on error
        return CallOutcome(
            outcome="neutral",
            conversion_signals=0,
            objections=[],
            sentiment="neutral",
            confidence=0.0
        )


# Global service instance
_campaign_service: Optional[CampaignExecutionService] = None


def get_campaign_execution_service() -> CampaignExecutionService:
    """Get the global campaign execution service instance."""
    global _campaign_service

    if _campaign_service is None:
        _campaign_service = CampaignExecutionService()

    return _campaign_service


async def check_and_resume_paused_campaigns():
    """
    Check paused campaigns and automatically resume them if start_time is reached.
    Also check pending campaigns with auto_start enabled and start them if start_time is reached.
    
    This should be called periodically (e.g., every minute) to ensure campaigns
    automatically resume when their start_time window opens.
    """
    try:
        service = get_campaign_execution_service()
        
        now = datetime.now(timezone.utc)
        current_time = now.time()

        # Find all paused campaigns with auto_start enabled and start_time set
        # Only campaigns with auto_start=True should be auto-resumed
        paused_campaigns = await service.campaigns_collection.find({
            "status": "paused",
            "config.auto_start": True,
            "config.start_time": {"$exists": True, "$ne": None}
        }).to_list(length=None)

        # Find all pending campaigns with auto_start enabled and start_time set
        pending_campaigns = await service.campaigns_collection.find({
            "status": "pending",
            "config.auto_start": True,
            "config.start_time": {"$exists": True, "$ne": None}
        }).to_list(length=None)
        
        # Process paused campaigns (already filtered by auto_start=True in query)
        for campaign_doc in paused_campaigns:
            try:
                campaign_id = str(campaign_doc["_id"])
                config = campaign_doc.get("config", {})
                start_time_str = config.get("start_time")

                if not start_time_str:
                    continue

                # Parse start_time and check if we've reached it
                start_hour, start_minute = map(int, start_time_str.split(':'))
                start_window = dt_time(start_hour, start_minute)

                # Check if current time >= start_time (allow small buffer for timing)
                # Also check if campaign was paused due to time window
                error_message = campaign_doc.get("error_message", "")
                is_time_window_pause = (
                    "pause time" in error_message.lower() or
                    "calling time window" in error_message.lower() or
                    "outside calling" in error_message.lower()
                )

                if current_time >= start_window and is_time_window_pause:
                    # Resume the campaign (auto_start=True already verified by query)
                    logger.info(f"Auto-resuming campaign {campaign_id} - start_time ({start_time_str}) reached and auto_start=True")
                    try:
                        await service.resume_campaign(campaign_id)
                    except ValueError as e:
                        # Campaign might not be ready to resume yet, log and continue
                        logger.debug(f"Campaign {campaign_id} not ready to resume: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error checking campaign {campaign_doc.get('_id')} for auto-resume: {e}")
                continue
        
        # Process pending campaigns with auto_start
        for campaign_doc in pending_campaigns:
            try:
                campaign_id = str(campaign_doc["_id"])
                config = campaign_doc.get("config", {})
                start_time_str = config.get("start_time")
                auto_start = config.get("auto_start", False)
                
                if not start_time_str or not auto_start:
                    continue
                
                # Parse start_time and check if we've reached it
                start_hour, start_minute = map(int, start_time_str.split(':'))
                start_window = dt_time(start_hour, start_minute)
                
                if current_time >= start_window:
                    # Start the campaign
                    logger.info(f"Auto-starting campaign {campaign_id} - start_time ({start_time_str}) reached")
                    try:
                        await service.start_campaign(campaign_id)
                    except ValueError as e:
                        # Campaign might not be ready to start yet, log and continue
                        logger.debug(f"Campaign {campaign_id} not ready to start: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error checking campaign {campaign_doc.get('_id')} for auto-start: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error in check_and_resume_paused_campaigns: {e}")


async def resume_running_campaigns():
    """
    Resume all campaigns that were running before server restart.
    
    This should be called on server startup to ensure campaigns continue
    running even after server restarts.
    """
    try:
        service = get_campaign_execution_service()
        
        # Find all campaigns with status "running"
        running_campaigns = await service.campaigns_collection.find({
            "status": "running"
        }).to_list(length=None)
        
        if not running_campaigns:
            logger.info("No running campaigns to resume")
            return
        
        logger.info(f"Found {len(running_campaigns)} running campaigns to resume")
        
        for campaign_doc in running_campaigns:
            campaign_id = str(campaign_doc["_id"])
            try:
                # Check if campaign is already being tracked
                if campaign_id in service._running_campaigns:
                    logger.info(f"Campaign {campaign_id} already has active task, skipping")
                    continue
                
                # Verify campaign is still valid (not completed)
                campaign = await service.get_campaign(campaign_id)
                if not campaign:
                    logger.warning(f"Campaign {campaign_id} not found, marking as failed")
                    await service.campaigns_collection.update_one(
                        {"_id": ObjectId(campaign_id)},
                        {"$set": {"status": "failed", "error_message": "Campaign not found on resume"}}
                    )
                    continue
                
                # Check if campaign is actually complete
                if campaign.progress.called >= campaign.progress.total_contacts:
                    logger.info(f"Campaign {campaign_id} is complete, marking as completed")
                    await service.campaigns_collection.update_one(
                        {"_id": ObjectId(campaign_id)},
                        {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc)}}
                    )
                    continue
                
                # Resume the campaign by starting execution task
                logger.info(f"Resuming campaign {campaign_id} from contact {campaign.progress.current_contact_index}")
                task = asyncio.create_task(service._execute_campaign(campaign_id))
                service._running_campaigns[campaign_id] = task
                
            except Exception as e:
                logger.error(f"Failed to resume campaign {campaign_id}: {str(e)}")
                # Mark as failed but don't stop other campaigns
                try:
                    await service.campaigns_collection.update_one(
                        {"_id": ObjectId(campaign_id)},
                        {"$set": {"status": "failed", "error_message": f"Resume failed: {str(e)}"}}
                    )
                except Exception:
                    pass
        
        logger.info(f"Successfully resumed {len([c for c in running_campaigns if str(c['_id']) in service._running_campaigns])} campaigns")
        
    except Exception as e:
        logger.error(f"Error resuming running campaigns: {str(e)}")


# Export commonly used functions
campaign_service = get_campaign_execution_service()
