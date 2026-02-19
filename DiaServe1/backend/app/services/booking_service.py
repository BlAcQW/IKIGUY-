"""
Booking Service

Business logic for property tour bookings, availability checking,
and reminder management.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.booking import (
    Booking,
    BookingCreate,
    BookingUpdate,
    BookingStatus,
    BookingType,
    AvailabilitySlot,
    Reminder,
    ReminderStatus,
    AgentAvailability,
    WaitlistEntry
)
from app.services.agent_service import AgentService
from app.services.notification_service import BookingNotificationService


class BookingService:
    """Service for managing property tour bookings"""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.bookings_collection = database["bookings"]
        self.agent_availability_collection = database["agent_availability"]
        self.waitlist_collection = database["booking_waitlist"]
        self.notification_service = BookingNotificationService(database)

    async def create_booking(
        self,
        booking_data: BookingCreate,
        organization_id: str,
        user_id: Optional[str] = None
    ) -> Booking:
        """
        Create a new booking.

        Args:
            booking_data: Booking creation data
            organization_id: Organization ID
            user_id: User ID making the booking

        Returns:
            Created booking

        Raises:
            ValueError: If time slot is not available
        """
        # Check availability
        is_available = await self.check_availability(
            property_id=booking_data.property_id,
            start_time=booking_data.scheduled_at,
            duration_minutes=booking_data.duration_minutes,
            organization_id=organization_id
        )

        if not is_available:
            raise ValueError("Selected time slot is not available")

        # Find available agent
        agent_id = await self._find_available_agent(
            scheduled_at=booking_data.scheduled_at,
            duration_minutes=booking_data.duration_minutes,
            organization_id=organization_id
        )

        # Generate contact_id if not provided
        contact_id = booking_data.contact_id or f"contact_{str(uuid.uuid4())}"

        # Create booking
        booking = Booking(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            property_id=booking_data.property_id,
            contact_id=contact_id,
            agent_id=agent_id,
            scheduled_at=booking_data.scheduled_at,
            duration_minutes=booking_data.duration_minutes,
            booking_type=booking_data.booking_type,
            status=BookingStatus.REQUESTED,
            contact_name=booking_data.contact_name,
            contact_email=booking_data.contact_email,
            contact_phone=booking_data.contact_phone,
            notes=booking_data.notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Schedule reminders
        booking.reminders = self._create_reminders(booking)

        # Save to database
        await self.bookings_collection.insert_one(booking.dict())

        # Send notifications (non-blocking - don't fail booking if email fails)
        try:
            # Send confirmation to customer
            await self.notification_service.send_booking_confirmation(booking)

            # Send notification to agent if assigned
            if agent_id:
                agent_service = AgentService(self.db)
                agent = await agent_service.get_agent(agent_id, organization_id)
                if agent:
                    await self.notification_service.send_agent_notification(booking, agent)
        except Exception as e:
            # Log error but don't fail the booking
            import logging
            logging.error(f"Failed to send booking notifications for {booking.id}: {e}")

        return booking

    async def get_booking(self, booking_id: str, organization_id: str) -> Optional[Booking]:
        """Get booking by ID"""
        booking_dict = await self.bookings_collection.find_one({
            "id": booking_id,
            "organization_id": organization_id
        })

        if not booking_dict:
            return None

        return Booking(**booking_dict)

    async def list_bookings(
        self,
        organization_id: str,
        property_id: Optional[str] = None,
        contact_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        status: Optional[BookingStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Booking], int]:
        """
        List bookings with filters.

        Returns:
            Tuple of (bookings list, total count)
        """
        query = {"organization_id": organization_id}

        if property_id:
            query["property_id"] = property_id
        if contact_id:
            query["contact_id"] = contact_id
        if agent_id:
            query["agent_id"] = agent_id
        if status:
            query["status"] = status.value

        # Date range filter
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["scheduled_at"] = date_query

        # Get total count
        total = await self.bookings_collection.count_documents(query)

        # Get paginated results
        cursor = self.bookings_collection.find(query).sort("scheduled_at", -1).skip(offset).limit(limit)
        bookings_list = await cursor.to_list(length=limit)

        bookings = [Booking(**doc) for doc in bookings_list]

        return bookings, total

    async def update_booking(
        self,
        booking_id: str,
        updates: BookingUpdate,
        organization_id: str
    ) -> Optional[Booking]:
        """Update booking"""
        # Get old booking first to track status changes
        old_booking = await self.get_booking(booking_id, organization_id)
        if not old_booking:
            return None

        old_status = old_booking.status

        update_dict = updates.dict(exclude_unset=True)
        update_dict["updated_at"] = datetime.utcnow()

        # Handle status-specific timestamps
        if updates.status:
            if updates.status == BookingStatus.CONFIRMED:
                update_dict["confirmed_at"] = datetime.utcnow()
            elif updates.status == BookingStatus.COMPLETED:
                update_dict["completed_at"] = datetime.utcnow()
            elif updates.status == BookingStatus.CANCELLED:
                update_dict["cancelled_at"] = datetime.utcnow()

        # Handle rescheduling
        if updates.scheduled_at:
            is_available = await self.check_availability(
                property_id=old_booking.property_id,
                start_time=updates.scheduled_at,
                duration_minutes=updates.duration_minutes or old_booking.duration_minutes,
                organization_id=organization_id,
                exclude_booking_id=booking_id
            )

            if not is_available:
                raise ValueError("New time slot is not available")

            update_dict["status"] = BookingStatus.RESCHEDULED.value
            # Recreate reminders for new time
            old_booking.scheduled_at = updates.scheduled_at
            update_dict["reminders"] = [r.dict() for r in self._create_reminders(old_booking)]

        result = await self.bookings_collection.find_one_and_update(
            {"id": booking_id, "organization_id": organization_id},
            {"$set": update_dict},
            return_document=True
        )

        if not result:
            return None

        updated_booking = Booking(**result)

        # Send status change notification if status changed
        if updates.status and updates.status != old_status:
            try:
                await self.notification_service.send_booking_status_update(
                    updated_booking,
                    old_status,
                    updated_booking.status
                )
            except Exception as e:
                # Log error but don't fail the update
                import logging
                logging.error(f"Failed to send status update notification for {booking_id}: {e}")

        return updated_booking

    async def cancel_booking(self, booking_id: str, organization_id: str) -> Optional[Booking]:
        """Cancel a booking"""
        updates = BookingUpdate(
            status=BookingStatus.CANCELLED
        )
        return await self.update_booking(booking_id, updates, organization_id)

    async def check_availability(
        self,
        property_id: str,
        start_time: datetime,
        duration_minutes: int,
        organization_id: str,
        exclude_booking_id: Optional[str] = None
    ) -> bool:
        """
        Check if a time slot is available for booking.

        Args:
            property_id: Property ID
            start_time: Requested start time
            duration_minutes: Duration in minutes
            organization_id: Organization ID
            exclude_booking_id: Booking ID to exclude (for rescheduling)

        Returns:
            True if available, False otherwise
        """
        end_time = start_time + timedelta(minutes=duration_minutes)

        # Build query for overlapping bookings
        query = {
            "organization_id": organization_id,
            "property_id": property_id,
            "status": {"$in": [
                BookingStatus.REQUESTED.value,
                BookingStatus.CONFIRMED.value,
                BookingStatus.RESCHEDULED.value
            ]},
            "$or": [
                # Booking starts during this slot
                {
                    "scheduled_at": {"$lt": end_time},
                    "$expr": {
                        "$gt": [
                            {"$add": ["$scheduled_at", {"$multiply": ["$duration_minutes", 60000]}]},
                            start_time
                        ]
                    }
                }
            ]
        }

        if exclude_booking_id:
            query["id"] = {"$ne": exclude_booking_id}

        overlapping_count = await self.bookings_collection.count_documents(query)

        return overlapping_count == 0

    async def get_available_slots(
        self,
        property_id: str,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int,
        organization_id: str
    ) -> List[AvailabilitySlot]:
        """
        Get list of available time slots for a property.

        Args:
            property_id: Property ID
            start_date: Start of date range
            end_date: End of date range
            duration_minutes: Desired booking duration
            organization_id: Organization ID

        Returns:
            List of available slots
        """
        slots = []

        # Generate potential slots (every 30 minutes during business hours)
        current = start_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end = end_date.replace(hour=18, minute=0, second=0, microsecond=0)

        while current < end:
            # Skip non-business hours (before 9am or after 6pm)
            if 9 <= current.hour < 18:
                slot_end = current + timedelta(minutes=duration_minutes)

                # Check availability
                is_available = await self.check_availability(
                    property_id=property_id,
                    start_time=current,
                    duration_minutes=duration_minutes,
                    organization_id=organization_id
                )

                # Find available agent
                agent_id = None
                if is_available:
                    agent_id = await self._find_available_agent(
                        scheduled_at=current,
                        duration_minutes=duration_minutes,
                        organization_id=organization_id
                    )

                slot = AvailabilitySlot(
                    start_time=current,
                    end_time=slot_end,
                    available=is_available,
                    agent_id=agent_id,
                    reason=None if is_available else "Time slot already booked"
                )

                slots.append(slot)

            # Move to next slot (30-minute intervals)
            current += timedelta(minutes=30)

        return slots

    def _create_reminders(self, booking: Booking) -> List[Reminder]:
        """Create reminder schedule for a booking"""
        reminders = []

        # 24-hour reminder
        reminder_24h = Reminder(
            type="24h",
            scheduled_at=booking.scheduled_at - timedelta(hours=24),
            status=ReminderStatus.PENDING,
            channel="email"
        )
        reminders.append(reminder_24h)

        # 1-hour reminder
        reminder_1h = Reminder(
            type="1h",
            scheduled_at=booking.scheduled_at - timedelta(hours=1),
            status=ReminderStatus.PENDING,
            channel="sms"
        )
        reminders.append(reminder_1h)

        # Post-tour follow-up (2 hours after scheduled end)
        tour_end = booking.scheduled_at + timedelta(minutes=booking.duration_minutes)
        reminder_followup = Reminder(
            type="post-tour",
            scheduled_at=tour_end + timedelta(hours=2),
            status=ReminderStatus.PENDING,
            channel="email"
        )
        reminders.append(reminder_followup)

        return reminders

    async def _find_available_agent(
        self,
        scheduled_at: datetime,
        duration_minutes: int,
        organization_id: str
    ) -> Optional[str]:
        """
        Find an available agent for the time slot.

        Uses AgentService to check availability and workload.

        Args:
            scheduled_at: Booking start time
            duration_minutes: Booking duration
            organization_id: Organization ID

        Returns:
            Agent ID if found, None if no agents available
        """
        agent_service = AgentService(self.db)

        # Get all available agents for this time slot
        available_agents = await agent_service.get_available_agents(
            organization_id=organization_id,
            start_time=scheduled_at,
            duration_minutes=duration_minutes
        )

        if not available_agents:
            return None

        # Sort by workload (total bookings) to distribute evenly
        # Agent with fewer total bookings gets priority
        sorted_agents = sorted(available_agents, key=lambda a: a.total_bookings)

        # Return the agent with the least bookings
        return sorted_agents[0].id

    async def mark_no_show(self, booking_id: str, organization_id: str) -> Optional[Booking]:
        """Mark booking as no-show"""
        updates = BookingUpdate(status=BookingStatus.NO_SHOW)
        return await self.update_booking(booking_id, updates, organization_id)

    async def complete_booking(
        self,
        booking_id: str,
        organization_id: str,
        rating: Optional[int] = None,
        feedback: Optional[str] = None
    ) -> Optional[Booking]:
        """Mark booking as completed"""
        updates = BookingUpdate(
            status=BookingStatus.COMPLETED,
            rating=rating,
            feedback=feedback
        )
        return await self.update_booking(booking_id, updates, organization_id)

    async def add_to_waitlist(
        self,
        property_id: str,
        contact_name: str,
        contact_email: Optional[str],
        contact_phone: Optional[str],
        preferred_dates: List[datetime],
        contact_id: Optional[str] = None
    ) -> WaitlistEntry:
        """Add contact to property waitlist"""
        entry = WaitlistEntry(
            id=str(uuid.uuid4()),
            property_id=property_id,
            contact_id=contact_id,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            preferred_dates=preferred_dates,
            notified=False,
            created_at=datetime.utcnow()
        )

        await self.waitlist_collection.insert_one(entry.dict())
        return entry

    async def get_upcoming_reminders(self, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """
        Get reminders that need to be sent in the next N hours.

        Returns list of {booking, reminder} dicts.
        """
        now = datetime.utcnow()
        cutoff = now + timedelta(hours=hours_ahead)

        # Find bookings with pending reminders
        query = {
            "reminders": {
                "$elemMatch": {
                    "status": ReminderStatus.PENDING.value,
                    "scheduled_at": {
                        "$gte": now,
                        "$lte": cutoff
                    }
                }
            }
        }

        cursor = self.bookings_collection.find(query)
        bookings_list = await cursor.to_list(length=1000)

        results = []
        for booking_dict in bookings_list:
            booking = Booking(**booking_dict)
            for reminder in booking.reminders:
                if (reminder.status == ReminderStatus.PENDING and
                    now <= reminder.scheduled_at <= cutoff):
                    results.append({
                        "booking": booking,
                        "reminder": reminder
                    })

        return results

    # ==================== Admin Booking Management Methods ====================

    async def create_booking_with_override(
        self,
        booking_data: BookingCreate,
        organization_id: str,
        admin_email: str,
        admin_id: str,
        override_availability: bool = False
    ) -> Booking:
        """
        Create booking with optional availability override (admin only).

        Args:
            booking_data: Booking creation data
            organization_id: Organization ID
            admin_email: Admin's email
            admin_id: Admin's ID
            override_availability: Skip availability check

        Returns:
            Created booking

        Raises:
            ValueError: If slot is unavailable and override not enabled
        """
        # Check availability unless override enabled
        if not override_availability:
            is_available = await self.check_availability(
                property_id=booking_data.property_id,
                start_time=booking_data.scheduled_at,
                duration_minutes=booking_data.duration_minutes,
                organization_id=organization_id
            )
            if not is_available:
                raise ValueError("Selected time slot is not available")

        # Find available agent (or None if overriding)
        agent_id = await self._find_available_agent(
            scheduled_at=booking_data.scheduled_at,
            duration_minutes=booking_data.duration_minutes,
            organization_id=organization_id
        ) if not override_availability else None

        contact_id = booking_data.contact_id or f"contact_{str(uuid.uuid4())}"

        booking = Booking(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            property_id=booking_data.property_id,
            contact_id=contact_id,
            agent_id=agent_id,
            scheduled_at=booking_data.scheduled_at,
            duration_minutes=booking_data.duration_minutes,
            booking_type=booking_data.booking_type,
            status=BookingStatus.REQUESTED,
            contact_name=booking_data.contact_name,
            contact_email=booking_data.contact_email,
            contact_phone=booking_data.contact_phone,
            notes=booking_data.notes,
            admin_override=override_availability,
            admin_override_reason=None,  # Will be set from booking_data if provided
            manually_created_by=admin_email,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        booking.reminders = self._create_reminders(booking)
        await self.bookings_collection.insert_one(booking.dict())

        # Log admin action
        await self._log_admin_action(
            booking_id=booking.id,
            organization_id=organization_id,
            action_type="manual_create",
            admin_email=admin_email,
            admin_id=admin_id,
            details={
                "override_availability": override_availability,
                "property_id": booking_data.property_id,
                "scheduled_at": booking_data.scheduled_at.isoformat()
            }
        )

        return booking

    async def reassign_agent(
        self,
        booking_id: str,
        new_agent_id: str,
        organization_id: str,
        admin_email: str,
        admin_id: str
    ) -> Optional[Booking]:
        """
        Reassign booking to a different agent (admin only).

        Args:
            booking_id: Booking ID
            new_agent_id: New agent ID
            organization_id: Organization ID
            admin_email: Admin's email
            admin_id: Admin's ID

        Returns:
            Updated booking or None if not found

        Raises:
            ValueError: If new agent doesn't exist
        """
        booking = await self.get_booking(booking_id, organization_id)
        if not booking:
            return None

        old_agent_id = booking.agent_id

        # Update booking
        result = await self.bookings_collection.find_one_and_update(
            {"id": booking_id, "organization_id": organization_id},
            {
                "$set": {
                    "agent_id": new_agent_id,
                    "reassigned_by": admin_email,
                    "reassigned_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            },
            return_document=True
        )

        updated_booking = Booking(**result)

        # Log admin action
        await self._log_admin_action(
            booking_id=booking_id,
            organization_id=organization_id,
            action_type="reassign_agent",
            admin_email=admin_email,
            admin_id=admin_id,
            details={
                "old_agent_id": old_agent_id,
                "new_agent_id": new_agent_id
            }
        )

        return updated_booking

    async def bulk_update_status(
        self,
        booking_ids: List[str],
        status: BookingStatus,
        organization_id: str,
        admin_email: str,
        admin_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bulk update booking statuses (admin only).

        Args:
            booking_ids: List of booking IDs
            status: New status
            organization_id: Organization ID
            admin_email: Admin's email
            admin_id: Admin's ID
            reason: Optional reason for bulk action

        Returns:
            Dict with success/failure counts and details
        """
        success_count = 0
        failed_count = 0
        failed_bookings = []

        for booking_id in booking_ids:
            try:
                updates = BookingUpdate(status=status)
                booking = await self.update_booking(
                    booking_id=booking_id,
                    updates=updates,
                    organization_id=organization_id
                )

                if booking:
                    success_count += 1

                    # Log admin action
                    await self._log_admin_action(
                        booking_id=booking_id,
                        organization_id=organization_id,
                        action_type=f"bulk_{status.value}",
                        admin_email=admin_email,
                        admin_id=admin_id,
                        details={"reason": reason, "status": status.value}
                    )
                else:
                    failed_count += 1
                    failed_bookings.append({
                        "id": booking_id,
                        "reason": "Booking not found"
                    })
            except Exception as e:
                failed_count += 1
                failed_bookings.append({
                    "id": booking_id,
                    "reason": str(e)
                })

        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_bookings": failed_bookings,
            "message": f"Successfully updated {success_count} booking(s), {failed_count} failed"
        }

    async def _log_admin_action(
        self,
        booking_id: str,
        organization_id: str,
        action_type: str,
        admin_email: str,
        admin_id: str,
        details: Dict[str, Any]
    ):
        """
        Log admin action to audit trail.

        Args:
            booking_id: Booking ID
            organization_id: Organization ID
            action_type: Type of action performed
            admin_email: Admin's email
            admin_id: Admin's ID
            details: Action-specific details
        """
        action_log_collection = self.db["booking_action_logs"]

        log_entry = {
            "id": str(uuid.uuid4()),
            "booking_id": booking_id,
            "organization_id": organization_id,
            "action_type": action_type,
            "admin_email": admin_email,
            "admin_id": admin_id,
            "details": details,
            "timestamp": datetime.utcnow()
        }

        await action_log_collection.insert_one(log_entry)

    async def get_booking_action_logs(
        self,
        booking_id: str,
        organization_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get audit trail for a booking.

        Args:
            booking_id: Booking ID
            organization_id: Organization ID

        Returns:
            List of action logs sorted by timestamp (newest first)
        """
        action_log_collection = self.db["booking_action_logs"]

        cursor = action_log_collection.find({
            "booking_id": booking_id,
            "organization_id": organization_id
        }).sort("timestamp", -1)

        logs = await cursor.to_list(length=100)
        return logs
