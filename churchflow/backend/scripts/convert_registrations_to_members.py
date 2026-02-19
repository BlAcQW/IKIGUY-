#!/usr/bin/env python3
"""
IMPACT 2025 Registration to Member/First-Timer Conversion Script.

This script processes IMPACT 2025 conference registrations and:
1. For registrations where user has branch_id -> ensures they are marked as members
2. For registrations where user has no branch_id -> creates first-timer records

Key IDs:
- IMPACT 2025 Conference ID: 68fbc116ca541168d5ea195e
- Action Chapel Organization ID: 68fbb1cf8b6890654df914ca

Usage:
    # Analyze only (no changes)
    python convert_registrations_to_members.py --analyze

    # Dry run (show what would be done)
    python convert_registrations_to_members.py --dry-run

    # Execute (actually create records)
    python convert_registrations_to_members.py --execute

Author: AI Labs Africa
Date: December 2025
"""

import argparse
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Configuration
MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/"
DATABASE_NAME = "churchflow"

# IMPACT 2025 Conference ID
IMPACT_CONF_ID = ObjectId("68fbc116ca541168d5ea195e")

# Action Chapel International Organization ID
ACTION_CHAPEL_ORG_ID = ObjectId("68fbb1cf8b6890654df914ca")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RegistrationConverter:
    """Handles conversion of registrations to members/first-timers."""

    def __init__(self, db):
        """
        Initialize converter.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.stats = {
            "total_registrations": 0,
            "registrations_with_user": 0,
            "registrations_without_user": 0,
            "users_with_branch": 0,
            "users_without_branch": 0,
            "first_timers_created": 0,
            "first_timers_already_exist": 0,
            "users_already_members": 0,
            "errors": 0
        }

    async def analyze(self) -> Dict:
        """
        Analyze registrations without making changes.

        Returns:
            Dict with analysis results
        """
        logger.info("=" * 60)
        logger.info("ANALYZING IMPACT 2025 REGISTRATIONS")
        logger.info("=" * 60)

        # Get all IMPACT 2025 registrations
        registrations = await self.db.conference_registrations.find(
            {"conference_id": IMPACT_CONF_ID}
        ).to_list(None)

        self.stats["total_registrations"] = len(registrations)
        logger.info(f"Total registrations: {len(registrations)}")

        # Analyze each registration
        unique_phones = set()
        phones_with_user = set()
        phones_without_user = set()
        phones_user_with_branch = set()
        phones_user_without_branch = set()
        phones_already_first_timer = set()

        for reg in registrations:
            phone = reg.get("user_phone", "").strip()
            if not phone:
                continue

            unique_phones.add(phone)

            # Check if user exists
            user = await self.db.users.find_one({"phone": phone})
            if user:
                phones_with_user.add(phone)
                if user.get("branch_id"):
                    phones_user_with_branch.add(phone)
                else:
                    phones_user_without_branch.add(phone)
            else:
                phones_without_user.add(phone)

            # Check if first-timer exists
            ft = await self.db.first_timers.find_one({
                "phone": phone,
                "organization_id": ACTION_CHAPEL_ORG_ID
            })
            if ft:
                phones_already_first_timer.add(phone)

        logger.info(f"\nUnique phone numbers: {len(unique_phones)}")
        logger.info(f"Phones with existing user: {len(phones_with_user)}")
        logger.info(f"  - Users with branch: {len(phones_user_with_branch)}")
        logger.info(f"  - Users without branch: {len(phones_user_without_branch)}")
        logger.info(f"Phones without user: {len(phones_without_user)}")
        logger.info(f"Phones already first-timer: {len(phones_already_first_timer)}")

        # Determine actions needed
        phones_need_first_timer = phones_user_without_branch - phones_already_first_timer
        phones_new_no_user = phones_without_user - phones_already_first_timer

        logger.info(f"\n--- ACTIONS NEEDED ---")
        logger.info(f"Users without branch needing first-timer: {len(phones_need_first_timer)}")
        logger.info(f"New phones without user needing first-timer: {len(phones_new_no_user)}")
        logger.info(f"Total first-timers to create: {len(phones_need_first_timer) + len(phones_new_no_user)}")

        return {
            "total_registrations": len(registrations),
            "unique_phones": len(unique_phones),
            "phones_with_user": len(phones_with_user),
            "phones_without_user": len(phones_without_user),
            "phones_user_with_branch": len(phones_user_with_branch),
            "phones_user_without_branch": len(phones_user_without_branch),
            "phones_already_first_timer": len(phones_already_first_timer),
            "phones_need_first_timer": len(phones_need_first_timer),
            "phones_new_no_user": len(phones_new_no_user),
            "total_to_create": len(phones_need_first_timer) + len(phones_new_no_user)
        }

    async def process_registrations(self, dry_run: bool = True) -> Dict:
        """
        Process registrations and create first-timers as needed.

        Args:
            dry_run: If True, don't actually create records

        Returns:
            Dict with processing results
        """
        mode = "DRY RUN" if dry_run else "EXECUTING"
        logger.info("=" * 60)
        logger.info(f"PROCESSING REGISTRATIONS ({mode})")
        logger.info("=" * 60)

        # Get all IMPACT 2025 registrations
        registrations = await self.db.conference_registrations.find(
            {"conference_id": IMPACT_CONF_ID}
        ).to_list(None)

        self.stats["total_registrations"] = len(registrations)
        logger.info(f"Processing {len(registrations)} registrations...")

        # Track processed phones to avoid duplicates
        processed_phones = set()
        created_first_timers = []
        skipped_already_exists = []
        skipped_has_branch = []
        errors = []

        # Get admin user for created_by field
        admin_user = await self.db.users.find_one({
            "organization_id": ACTION_CHAPEL_ORG_ID,
            "roles": "admin"
        })
        admin_user_id = admin_user["_id"] if admin_user else ObjectId()

        batch_size = 100
        for i, reg in enumerate(registrations):
            if (i + 1) % batch_size == 0:
                logger.info(f"Processed {i + 1}/{len(registrations)} registrations...")

            phone = reg.get("user_phone", "").strip()
            if not phone or phone in processed_phones:
                continue

            processed_phones.add(phone)
            name = reg.get("user_name", "").strip()
            email = reg.get("user_email")

            try:
                # Check if user exists
                user = await self.db.users.find_one({"phone": phone})

                if user and user.get("branch_id"):
                    # User exists with branch - already a member
                    skipped_has_branch.append({
                        "phone": phone,
                        "name": name,
                        "branch_id": str(user.get("branch_id"))
                    })
                    self.stats["users_with_branch"] += 1
                    continue

                # Check if first-timer already exists
                existing_ft = await self.db.first_timers.find_one({
                    "phone": phone,
                    "organization_id": ACTION_CHAPEL_ORG_ID
                })

                if existing_ft:
                    skipped_already_exists.append({
                        "phone": phone,
                        "name": name,
                        "first_timer_id": str(existing_ft["_id"])
                    })
                    self.stats["first_timers_already_exist"] += 1
                    continue

                # Parse name into first/last
                name_parts = name.split() if name else ["Unknown"]
                first_name = name_parts[0] if name_parts else "Unknown"
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "Unknown"

                # Create first-timer record
                first_timer_data = {
                    "organization_id": ACTION_CHAPEL_ORG_ID,
                    "branch_id": None,  # External visitor - no branch
                    "first_name": first_name,
                    "last_name": last_name,
                    "full_name": name or "Unknown",
                    "phone": phone,
                    "email": email,
                    "gender": None,
                    "address": None,
                    "visit_date": reg.get("created_at", datetime.utcnow()),
                    "visit_type": "first_time",
                    "service_attended": "IMPACT 2025",
                    "interest_type": "visitor",
                    "wants_membership": False,
                    "wants_discipleship": False,
                    "how_heard_about_us": "IMPACT 2025 Conference",
                    "invited_by": None,
                    "follow_up_status": "pending",
                    "follow_up_notes": f"Auto-created from IMPACT 2025 registration (Code: {reg.get('registration_code', 'N/A')})",
                    "assigned_to_user_id": None,
                    "last_contact_date": None,
                    "next_follow_up_date": None,
                    "converted_to_member": False,
                    "member_id": user["_id"] if user else None,  # Link to existing user if any
                    "conversion_date": None,
                    "created_by_user_id": admin_user_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "is_active": True
                }

                if not dry_run:
                    result = await self.db.first_timers.insert_one(first_timer_data)
                    first_timer_id = str(result.inserted_id)
                else:
                    first_timer_id = "DRY_RUN_ID"

                created_first_timers.append({
                    "phone": phone,
                    "name": name,
                    "email": email,
                    "first_timer_id": first_timer_id,
                    "had_user": user is not None
                })
                self.stats["first_timers_created"] += 1

            except Exception as e:
                errors.append({
                    "phone": phone,
                    "name": name,
                    "error": str(e)
                })
                self.stats["errors"] += 1
                logger.error(f"Error processing {phone}: {e}")

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total registrations processed: {len(registrations)}")
        logger.info(f"Unique phones processed: {len(processed_phones)}")
        logger.info(f"First-timers created: {len(created_first_timers)}")
        logger.info(f"Skipped (already first-timer): {len(skipped_already_exists)}")
        logger.info(f"Skipped (has branch - member): {len(skipped_has_branch)}")
        logger.info(f"Errors: {len(errors)}")

        if dry_run:
            logger.info("\n*** DRY RUN - No records were created ***")
            logger.info("Run with --execute to create records")

        return {
            "mode": "dry_run" if dry_run else "executed",
            "total_registrations": len(registrations),
            "unique_phones": len(processed_phones),
            "first_timers_created": created_first_timers,
            "skipped_already_exists": skipped_already_exists,
            "skipped_has_branch": skipped_has_branch,
            "errors": errors,
            "stats": self.stats
        }

    async def verify_results(self) -> Dict:
        """
        Verify the results after execution.

        Returns:
            Dict with verification results
        """
        logger.info("=" * 60)
        logger.info("VERIFYING RESULTS")
        logger.info("=" * 60)

        # Count first-timers
        ft_count = await self.db.first_timers.count_documents({
            "organization_id": ACTION_CHAPEL_ORG_ID
        })

        # Count first-timers from IMPACT
        ft_impact_count = await self.db.first_timers.count_documents({
            "organization_id": ACTION_CHAPEL_ORG_ID,
            "service_attended": "IMPACT 2025"
        })

        # Count pending follow-ups
        pending_count = await self.db.first_timers.count_documents({
            "organization_id": ACTION_CHAPEL_ORG_ID,
            "follow_up_status": "pending"
        })

        logger.info(f"Total first-timers in organization: {ft_count}")
        logger.info(f"First-timers from IMPACT 2025: {ft_impact_count}")
        logger.info(f"Pending follow-ups: {pending_count}")

        return {
            "total_first_timers": ft_count,
            "impact_first_timers": ft_impact_count,
            "pending_follow_ups": pending_count
        }


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert IMPACT 2025 registrations to members/first-timers"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze registrations without making changes"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually create first-timer records"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify results after execution"
    )

    args = parser.parse_args()

    if not any([args.analyze, args.dry_run, args.execute, args.verify]):
        parser.print_help()
        return

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    try:
        converter = RegistrationConverter(db)

        if args.analyze:
            result = await converter.analyze()
            print(f"\nAnalysis complete. Results: {result}")

        if args.dry_run:
            result = await converter.process_registrations(dry_run=True)
            print(f"\nDry run complete. Would create {len(result['first_timers_created'])} first-timers")

        if args.execute:
            confirm = input("\nThis will create first-timer records. Continue? (yes/no): ")
            if confirm.lower() == "yes":
                result = await converter.process_registrations(dry_run=False)
                print(f"\nExecution complete. Created {len(result['first_timers_created'])} first-timers")
            else:
                print("Cancelled.")

        if args.verify:
            result = await converter.verify_results()
            print(f"\nVerification complete. Results: {result}")

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
