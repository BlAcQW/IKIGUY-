"""
Reminder Worker Service

Background service that processes and sends booking reminders at scheduled times.
Uses APScheduler for periodic task execution.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.booking import Booking, ReminderStatus, BookingStatus
from app.services.notification_service import BookingNotificationService
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)


class ReminderWorker:
    """
    Background worker for processing and sending booking reminders.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize reminder worker.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.bookings_collection = db["bookings"]
        self.notification_service = BookingNotificationService(db)
        self.agent_service = AgentService(db)
        self.is_running = False

    async def process_pending_reminders(self):
        """
        Process all pending reminders that are due.

        This method is called periodically by the scheduler.
        """
        try:
            logger.info("Starting reminder processing cycle...")

            # Get current time with small buffer (1 minute) to catch reminders that are due
            now = datetime.utcnow()
            buffer_time = now + timedelta(minutes=1)

            # Find all bookings with pending reminders that are due
            query = {
                "reminders": {
                    "$elemMatch": {
                        "status": ReminderStatus.PENDING.value,
                        "scheduled_at": {"$lte": buffer_time}
                    }
                },
                # Only send reminders for active bookings (not cancelled or completed yet)
                "status": {
                    "$in": [
                        BookingStatus.REQUESTED.value,
                        BookingStatus.CONFIRMED.value,
                        BookingStatus.RESCHEDULED.value,
                        BookingStatus.COMPLETED.value  # Include completed for post-tour reminders
                    ]
                }
            }

            cursor = self.bookings_collection.find(query)
            bookings_list = await cursor.to_list(length=None)

            if not bookings_list:
                logger.info("No pending reminders found")
                return

            logger.info(f"Found {len(bookings_list)} bookings with pending reminders")

            # Process each booking
            processed_count = 0
            sent_count = 0
            failed_count = 0

            for booking_dict in bookings_list:
                booking = Booking(**booking_dict)

                # Process each pending reminder in this booking
                for idx, reminder in enumerate(booking.reminders):
                    if (reminder.status == ReminderStatus.PENDING and
                            reminder.scheduled_at <= buffer_time):

                        processed_count += 1

                        # Determine if we should send this reminder
                        should_send = self._should_send_reminder(booking, reminder.type)

                        if not should_send:
                            logger.info(
                                f"Skipping {reminder.type} reminder for booking {booking.id} "
                                f"(status: {booking.status})"
                            )
                            # Mark as sent anyway to avoid retrying
                            await self._update_reminder_status(
                                booking.id,
                                idx,
                                ReminderStatus.SENT,
                                now
                            )
                            continue

                        # Send the reminder
                        try:
                            logger.info(
                                f"Sending {reminder.type} reminder for booking {booking.id} "
                                f"to {booking.contact_email}"
                            )

                            result = await self.notification_service.send_reminder(
                                booking=booking,
                                reminder_type=reminder.type
                            )

                            if result.get("success"):
                                # Update reminder status to SENT
                                await self._update_reminder_status(
                                    booking.id,
                                    idx,
                                    ReminderStatus.SENT,
                                    now,
                                    result.get("message_id")
                                )
                                sent_count += 1
                                logger.info(
                                    f"Successfully sent {reminder.type} reminder for "
                                    f"booking {booking.id}"
                                )
                            else:
                                # Update reminder status to FAILED
                                await self._update_reminder_status(
                                    booking.id,
                                    idx,
                                    ReminderStatus.FAILED,
                                    now
                                )
                                failed_count += 1
                                logger.error(
                                    f"Failed to send {reminder.type} reminder for "
                                    f"booking {booking.id}: {result.get('error')}"
                                )

                        except Exception as e:
                            # Update reminder status to FAILED
                            await self._update_reminder_status(
                                booking.id,
                                idx,
                                ReminderStatus.FAILED,
                                now
                            )
                            failed_count += 1
                            logger.error(
                                f"Exception sending {reminder.type} reminder for "
                                f"booking {booking.id}: {e}",
                                exc_info=True
                            )

            logger.info(
                f"Reminder processing complete. Processed: {processed_count}, "
                f"Sent: {sent_count}, Failed: {failed_count}"
            )

        except Exception as e:
            logger.error(f"Error in reminder processing cycle: {e}", exc_info=True)

    def _should_send_reminder(self, booking: Booking, reminder_type: str) -> bool:
        """
        Determine if a reminder should be sent based on booking status and reminder type.

        Args:
            booking: Booking object
            reminder_type: Type of reminder ('24h', '1h', 'post-tour')

        Returns:
            True if reminder should be sent, False otherwise
        """
        # Post-tour reminders should only be sent for completed bookings
        if reminder_type == "post-tour":
            return booking.status == BookingStatus.COMPLETED

        # Pre-tour reminders (24h, 1h) should only be sent for active bookings
        if reminder_type in ["24h", "1h"]:
            return booking.status in [
                BookingStatus.REQUESTED,
                BookingStatus.CONFIRMED,
                BookingStatus.RESCHEDULED
            ]

        # Default: don't send
        return False

    async def _update_reminder_status(
        self,
        booking_id: str,
        reminder_index: int,
        new_status: ReminderStatus,
        sent_at: Optional[datetime] = None,
        message_id: Optional[str] = None
    ):
        """
        Update the status of a specific reminder in a booking.

        Args:
            booking_id: Booking ID
            reminder_index: Index of the reminder in the reminders array
            new_status: New reminder status
            sent_at: Timestamp when reminder was sent
            message_id: Message ID from email provider
        """
        update_dict = {
            f"reminders.{reminder_index}.status": new_status.value,
            "updated_at": datetime.utcnow()
        }

        if sent_at:
            update_dict[f"reminders.{reminder_index}.sent_at"] = sent_at

        if message_id:
            update_dict[f"reminders.{reminder_index}.message_id"] = message_id

        await self.bookings_collection.update_one(
            {"id": booking_id},
            {"$set": update_dict}
        )

    async def cleanup_old_reminders(self):
        """
        Clean up old failed reminders that are past their scheduled time.

        This runs less frequently (e.g., once per day) to prevent database bloat.
        """
        try:
            logger.info("Starting reminder cleanup...")

            # Mark failed reminders older than 24 hours as expired
            cutoff_time = datetime.utcnow() - timedelta(days=1)

            # Find bookings with old failed reminders
            query = {
                "reminders": {
                    "$elemMatch": {
                        "status": ReminderStatus.FAILED.value,
                        "scheduled_at": {"$lt": cutoff_time}
                    }
                }
            }

            # For now, we just log them. In production, you might want to:
            # 1. Archive them to a separate collection
            # 2. Send alerts to admins
            # 3. Retry sending if appropriate

            cursor = self.bookings_collection.find(query)
            count = await self.bookings_collection.count_documents(query)

            if count > 0:
                logger.warning(f"Found {count} bookings with old failed reminders")
                # You could implement cleanup logic here
            else:
                logger.info("No old failed reminders found")

        except Exception as e:
            logger.error(f"Error in reminder cleanup: {e}", exc_info=True)

    async def get_reminder_stats(self) -> dict:
        """
        Get statistics about reminders in the system.

        Returns:
            Dictionary with reminder statistics
        """
        try:
            pipeline = [
                {"$unwind": "$reminders"},
                {
                    "$group": {
                        "_id": "$reminders.status",
                        "count": {"$sum": 1}
                    }
                }
            ]

            cursor = self.bookings_collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)

            stats = {
                "pending": 0,
                "sent": 0,
                "failed": 0,
                "total": 0
            }

            for result in results:
                status = result["_id"]
                count = result["count"]
                stats[status] = count
                stats["total"] += count

            # Get upcoming reminders (due in next hour)
            now = datetime.utcnow()
            upcoming_cutoff = now + timedelta(hours=1)

            upcoming_count = await self.bookings_collection.count_documents({
                "reminders": {
                    "$elemMatch": {
                        "status": ReminderStatus.PENDING.value,
                        "scheduled_at": {"$gte": now, "$lte": upcoming_cutoff}
                    }
                }
            })

            stats["upcoming_next_hour"] = upcoming_count

            return stats

        except Exception as e:
            logger.error(f"Error getting reminder stats: {e}", exc_info=True)
            return {}


# Singleton instance
_reminder_worker_instance: Optional[ReminderWorker] = None


def get_reminder_worker(db: AsyncIOMotorDatabase) -> ReminderWorker:
    """
    Get or create the reminder worker singleton instance.

    Args:
        db: MongoDB database instance

    Returns:
        ReminderWorker instance
    """
    global _reminder_worker_instance

    if _reminder_worker_instance is None:
        _reminder_worker_instance = ReminderWorker(db)

    return _reminder_worker_instance
