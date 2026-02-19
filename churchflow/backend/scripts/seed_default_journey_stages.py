"""
Seed script for default journey stages.

Populates the database with predefined journey stages for:
- Spiritual Journey (First Timer → Baptized)
- Cell Journey (Cell Visitor → Cell Leader)
- Ministry Journey (Volunteer → Ministry Leader)

Usage:
    python scripts/seed_default_journey_stages.py [--organization-id ORG_ID]
"""

import asyncio
import sys
import os
from datetime import datetime
from bson import ObjectId

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import connect_to_mongodb, close_mongodb_connection, get_database
from app.models.journey_stage import JourneyStage, ScheduledFollowup


async def seed_spiritual_journey_stages(organization_id: str):
    """
    Seed spiritual journey stages.

    Progression: First Timer → Second Timer → Regular Attendee →
                 New Convert → Baptism Class → Baptized

    Args:
        organization_id: Organization ID to seed stages for
    """
    db = get_database()

    stages = [
        # Stage 1: First Timer
        JourneyStage(
            organization_id=ObjectId(organization_id),
            stage_name="first_timer",
            stage_display_name="First Timer",
            journey_type="spiritual",
            stage_order=1,
            is_custom=False,
            is_active=True,
            auto_send_welcome=True,
            welcome_delay_minutes=5,
            welcome_message_template=(
                "Hi {{name}}! 🙏 Welcome to {{church_name}}! We're so glad you joined us today. "
                "We'd love to stay connected with you. God bless! 💙"
            ),
            welcome_channels=["sms", "whatsapp"],
            scheduled_followups=[
                ScheduledFollowup(
                    delay_days=1,
                    message_template=(
                        "Hi {{name}}! Thank you for visiting {{church_name}} yesterday. "
                        "We hope you felt the presence of God. We'd love to see you again this Sunday! 🙌"
                    ),
                    communication_channels=["sms"]
                ),
                ScheduledFollowup(
                    delay_days=3,
                    message_template=(
                        "Hello {{name}}, this is {{cell_leader}} from {{church_name}}. "
                        "I'd love to personally welcome you and answer any questions you might have. "
                        "Can we chat briefly?"
                    ),
                    communication_channels=["voice"]
                ),
                ScheduledFollowup(
                    delay_days=7,
                    message_template=(
                        "Hi {{name}}! 👋 It's been a week since we first met! "
                        "We have an exciting service this Sunday. Would love to see you there! "
                        "Join us at {{service_time}}. 🎉"
                    ),
                    communication_channels=["whatsapp"]
                )
            ],
            description="New visitor attending for the first time"
        ),

        # Stage 2: Second Timer
        JourneyStage(
            organization_id=ObjectId(organization_id),
            stage_name="second_timer",
            stage_display_name="Second Timer",
            journey_type="spiritual",
            stage_order=2,
            is_custom=False,
            is_active=True,
            auto_send_welcome=True,
            welcome_delay_minutes=10,
            welcome_message_template=(
                "Welcome back, {{name}}! 🎊 We're thrilled to see you again at {{church_name}}! "
                "You're becoming part of our family. See you next time! 💙"
            ),
            welcome_channels=["whatsapp"],
            scheduled_followups=[
                ScheduledFollowup(
                    delay_days=3,
                    message_template=(
                        "Hi {{name}}! We'd love to invite you to join a cell group - "
                        "a small community where you can connect, grow, and build friendships. "
                        "{{cell_leader}} leads a group that meets {{meeting_day}}s. Interested? 😊"
                    ),
                    communication_channels=["whatsapp", "sms"]
                )
            ],
            description="Visitor attending for the second time"
        ),

        # Stage 3: Regular Attendee
        JourneyStage(
            organization_id=ObjectId(organization_id),
            stage_name="regular_attendee",
            stage_display_name="Regular Attendee",
            journey_type="spiritual",
            stage_order=3,
            is_custom=False,
            is_active=True,
            auto_send_welcome=True,
            welcome_delay_minutes=15,
            welcome_message_template=(
                "{{name}}, you're officially part of the family! ❤️ "
                "We're so blessed to have you at {{church_name}}. "
                "Let's continue this journey together!"
            ),
            welcome_channels=["whatsapp"],
            scheduled_followups=[
                ScheduledFollowup(
                    delay_days=7,
                    message_template=(
                        "Hi {{name}}! We're excited to introduce you to our membership pathway. "
                        "This is your next step to becoming a committed member of {{church_name}}. "
                        "Would you like to learn more? 📚"
                    ),
                    communication_channels=["whatsapp", "voice"]
                )
            ],
            description="Member attending regularly (3+ times)"
        ),

        # Stage 4: New Convert
        JourneyStage(
            organization_id=ObjectId(organization_id),
            stage_name="new_convert",
            stage_display_name="New Convert",
            journey_type="spiritual",
            stage_order=4,
            is_custom=False,
            is_active=True,
            auto_send_welcome=True,
            welcome_delay_minutes=5,
            welcome_message_template=(
                "Congratulations, {{name}}! 🎉🎊 Today marks the beginning of your new life in Christ! "
                "We're here to support you every step of the way. Welcome to the family! 💙✝️"
            ),
            welcome_channels=["whatsapp", "sms", "voice"],
            scheduled_followups=[
                ScheduledFollowup(
                    delay_days=1,
                    message_template=(
                        "Hi {{name}}! Your decision yesterday was powerful! 🙏 "
                        "We have a baptism class starting soon to help you grow in your faith. "
                        "Would you like to join? It starts {{baptism_class_date}}."
                    ),
                    communication_channels=["whatsapp", "sms"]
                ),
                ScheduledFollowup(
                    delay_days=7,
                    message_template=(
                        "Hello {{name}}, this is {{cell_leader}}. "
                        "I wanted to check in and see how your first week as a believer has been. "
                        "Do you have any questions about your faith journey?"
                    ),
                    communication_channels=["voice"]
                )
            ],
            description="Recently gave their life to Christ"
        ),

        # Stage 5: Baptism Class
        JourneyStage(
            organization_id=ObjectId(organization_id),
            stage_name="baptism_class",
            stage_display_name="Baptism Class",
            journey_type="spiritual",
            stage_order=5,
            is_custom=False,
            is_active=True,
            auto_send_welcome=True,
            welcome_delay_minutes=10,
            welcome_message_template=(
                "Welcome to Baptism Class, {{name}}! 📖 "
                "We're excited to prepare you for this important step. "
                "Classes are every {{class_day}} at {{class_time}}. See you there! ✝️"
            ),
            welcome_channels=["whatsapp", "sms"],
            scheduled_followups=[
                ScheduledFollowup(
                    delay_days=2,
                    message_template=(
                        "Hi {{name}}! Just a reminder: Baptism class this {{class_day}} at {{class_time}}. "
                        "Please bring your Bible and notebook. See you soon! 📚"
                    ),
                    communication_channels=["whatsapp", "sms"]
                ),
                ScheduledFollowup(
                    delay_days=7,
                    message_template=(
                        "{{name}}, you're doing great in baptism class! 🌟 "
                        "Keep it up! Your baptism date is approaching: {{baptism_date}}. "
                        "We're praying for you! 🙏"
                    ),
                    communication_channels=["whatsapp"]
                )
            ],
            description="Enrolled in baptism preparation class"
        ),

        # Stage 6: Baptized
        JourneyStage(
            organization_id=ObjectId(organization_id),
            stage_name="baptized",
            stage_display_name="Baptized",
            journey_type="spiritual",
            stage_order=6,
            is_custom=False,
            is_active=True,
            auto_send_welcome=True,
            welcome_delay_minutes=5,
            welcome_message_template=(
                "Congratulations on your baptism, {{name}}! 🎉💧 "
                "You publicly declared your faith today! We're so proud of you. "
                "Now let's continue growing together in Christ! ✝️❤️"
            ),
            welcome_channels=["whatsapp", "sms", "voice"],
            scheduled_followups=[
                ScheduledFollowup(
                    delay_days=3,
                    message_template=(
                        "Hi {{name}}! How does it feel to be baptized? 😊 "
                        "Your next step is to serve! We have opportunities in worship, "
                        "hospitality, media, and more. Would you like to explore serving?"
                    ),
                    communication_channels=["whatsapp", "voice"]
                ),
                ScheduledFollowup(
                    delay_days=14,
                    message_template=(
                        "{{name}}, we'd love to see you take leadership in a cell group! "
                        "Cell leader training starts {{training_date}}. "
                        "Would you be interested in learning more? 🌟"
                    ),
                    communication_channels=["whatsapp"]
                )
            ],
            description="Completed baptism"
        )
    ]

    # Insert stages
    inserted_count = 0
    for stage in stages:
        # Check if stage already exists
        existing = await db.journey_stages.find_one({
            "organization_id": ObjectId(organization_id),
            "journey_type": "spiritual",
            "stage_name": stage.stage_name
        })

        if not existing:
            stage_dict = stage.model_dump(by_alias=True, exclude={"id"})
            await db.journey_stages.insert_one(stage_dict)
            inserted_count += 1
            print(f"   ✅ Created spiritual stage: {stage.stage_display_name}")
        else:
            print(f"   ⏭️  Skipped (exists): {stage.stage_display_name}")

    return inserted_count


async def seed_cell_journey_stages(organization_id: str):
    """
    Seed cell journey stages.

    Progression: Cell Visitor → Cell Member → Cell Leader-in-Training → Cell Leader

    Args:
        organization_id: Organization ID to seed stages for
    """
    db = get_database()

    stages = [
        # Stage 1: Cell Visitor
        JourneyStage(
            organization_id=ObjectId(organization_id),
            stage_name="cell_visitor",
            stage_display_name="Cell Visitor",
            journey_type="cell",
            stage_order=1,
            is_custom=False,
            is_active=True,
            auto_send_welcome=True,
            welcome_delay_minutes=10,
            welcome_message_template=(
                "Welcome to our cell group, {{name}}! 🏠 "
                "We're so glad you joined us tonight. This is a place to belong, connect, and grow. "
                "See you next {{meeting_day}}! 💙"
            ),
            welcome_channels=["whatsapp"],
            scheduled_followups=[
                ScheduledFollowup(
                    delay_days=2,
                    message_template=(
                        "Hi {{name}}! Thanks for visiting our cell group. "
                        "We'd love to have you join us regularly. "
                        "Next meeting: {{meeting_day}} at {{meeting_time}}. See you there! 😊"
                    ),
                    communication_channels=["whatsapp"]
                )
            ],
            description="First-time cell group visitor"
        ),

        # Stage 2: Cell Member
        JourneyStage(
            organization_id=ObjectId(organization_id),
            stage_name="cell_member",
            stage_display_name="Cell Member",
            journey_type="cell",
            stage_order=2,
            is_custom=False,
            is_active=True,
            auto_send_welcome=True,
            welcome_delay_minutes=15,
            welcome_message_template=(
                "{{name}}, you're now officially part of our cell family! ❤️🏠 "
                "We're excited to journey together. Let's grow in faith and friendship! 🙏"
            ),
            welcome_channels=["whatsapp"],
            scheduled_followups=[
                ScheduledFollowup(
                    delay_days=14,
                    message_template=(
                        "Hi {{name}}! You've been such a blessing to our cell group. 🌟 "
                        "Have you thought about serving in a leadership role? "
                        "We have training opportunities if you're interested!"
                    ),
                    communication_channels=["whatsapp", "voice"]
                )
            ],
            description="Regular cell group member"
        ),

        # Stage 3: Cell Leader-in-Training
        JourneyStage(
            organization_id=ObjectId(organization_id),
            stage_name="cell_leader_training",
            stage_display_name="Cell Leader-in-Training",
            journey_type="cell",
            stage_order=3,
            is_custom=False,
            is_active=True,
            auto_send_welcome=True,
            welcome_delay_minutes=10,
            welcome_message_template=(
                "Welcome to cell leader training, {{name}}! 📚👥 "
                "You're being equipped to shepherd and lead others. "
                "Training sessions: {{training_day}}s at {{training_time}}. Let's do this! 🚀"
            ),
            welcome_channels=["whatsapp", "sms"],
            scheduled_followups=[
                ScheduledFollowup(
                    delay_days=7,
                    message_template=(
                        "Hi {{name}}! How's your leadership training going? 📖 "
                        "Remember, great leaders are made, not born. You're doing amazing! "
                        "Keep up the great work! 💪"
                    ),
                    communication_channels=["whatsapp"]
                )
            ],
            description="Training to become a cell leader"
        ),

        # Stage 4: Cell Leader
        JourneyStage(
            organization_id=ObjectId(organization_id),
            stage_name="cell_leader",
            stage_display_name="Cell Leader",
            journey_type="cell",
            stage_order=4,
            is_custom=False,
            is_active=True,
            auto_send_welcome=True,
            welcome_delay_minutes=5,
            welcome_message_template=(
                "Congratulations, {{name}}! 🎉👥 You're now a cell leader! "
                "God has called you to shepherd His people. We're here to support you. "
                "Let's build His kingdom together! ✝️💙"
            ),
            welcome_channels=["whatsapp", "sms", "voice"],
            scheduled_followups=[
                ScheduledFollowup(
                    delay_days=1,
                    message_template=(
                        "Hi Cell Leader {{name}}! 🌟 "
                        "Your first cell meeting is coming up. We're praying for you! "
                        "Remember: {{zone_leader}} is here if you need anything. You've got this! 💪"
                    ),
                    communication_channels=["whatsapp"]
                ),
                ScheduledFollowup(
                    delay_days=7,
                    message_template=(
                        "{{name}}, how was your first week as a cell leader? "
                        "Zone leader meeting is this {{meeting_day}} at {{meeting_time}}. "
                        "We'll discuss strategies and share wins. See you there! 👥"
                    ),
                    communication_channels=["whatsapp", "voice"]
                )
            ],
            description="Leading a cell group"
        )
    ]

    # Insert stages
    inserted_count = 0
    for stage in stages:
        # Check if stage already exists
        existing = await db.journey_stages.find_one({
            "organization_id": ObjectId(organization_id),
            "journey_type": "cell",
            "stage_name": stage.stage_name
        })

        if not existing:
            stage_dict = stage.model_dump(by_alias=True, exclude={"id"})
            await db.journey_stages.insert_one(stage_dict)
            inserted_count += 1
            print(f"   ✅ Created cell stage: {stage.stage_display_name}")
        else:
            print(f"   ⏭️  Skipped (exists): {stage.stage_display_name}")

    return inserted_count


async def seed_ministry_journey_stages(organization_id: str):
    """
    Seed ministry journey stages.

    Progression: Department Volunteer → Department Leader → Ministry Leader

    Args:
        organization_id: Organization ID to seed stages for
    """
    db = get_database()

    stages = [
        # Stage 1: Department Volunteer
        JourneyStage(
            organization_id=ObjectId(organization_id),
            stage_name="department_volunteer",
            stage_display_name="Department Volunteer",
            journey_type="ministry",
            stage_order=1,
            is_custom=False,
            is_active=True,
            auto_send_welcome=True,
            welcome_delay_minutes=10,
            welcome_message_template=(
                "Welcome to the {{department_name}} team, {{name}}! 🎉 "
                "We're so excited to have you serve with us. "
                "Your gifts and talents will make a difference! 💙"
            ),
            welcome_channels=["whatsapp"],
            scheduled_followups=[
                ScheduledFollowup(
                    delay_days=3,
                    message_template=(
                        "Hi {{name}}! How's your first week serving in {{department_name}}? "
                        "{{department_head}} is here if you have any questions. "
                        "We appreciate you! 🙏"
                    ),
                    communication_channels=["whatsapp"]
                )
            ],
            description="Serving as a volunteer in a department"
        ),

        # Stage 2: Department Leader
        JourneyStage(
            organization_id=ObjectId(organization_id),
            stage_name="department_leader",
            stage_display_name="Department Leader",
            journey_type="ministry",
            stage_order=2,
            is_custom=False,
            is_active=True,
            auto_send_welcome=True,
            welcome_delay_minutes=10,
            welcome_message_template=(
                "Congratulations, {{name}}! 🌟 You're now a leader in {{department_name}}! "
                "You'll be coordinating volunteers and ensuring excellence in service. "
                "Leadership training starts {{training_date}}. Let's lead well! 💪"
            ),
            welcome_channels=["whatsapp", "sms"],
            scheduled_followups=[
                ScheduledFollowup(
                    delay_days=7,
                    message_template=(
                        "Hi {{name}}! How's your first week leading in {{department_name}}? "
                        "Remember: leaders meeting this {{meeting_day}} at {{meeting_time}}. "
                        "We'll equip you with tools for success! 📚"
                    ),
                    communication_channels=["whatsapp"]
                )
            ],
            description="Leading a team within a department"
        ),

        # Stage 3: Ministry Leader
        JourneyStage(
            organization_id=ObjectId(organization_id),
            stage_name="ministry_leader",
            stage_display_name="Ministry Leader",
            journey_type="ministry",
            stage_order=3,
            is_custom=False,
            is_active=True,
            auto_send_welcome=True,
            welcome_delay_minutes=5,
            welcome_message_template=(
                "{{name}}, you're now a Ministry Leader! 🎊👑 "
                "You'll be overseeing multiple departments and shaping the direction of ministry. "
                "This is a great responsibility and privilege. We're praying for you! 🙏✝️"
            ),
            welcome_channels=["whatsapp", "sms", "voice"],
            scheduled_followups=[
                ScheduledFollowup(
                    delay_days=3,
                    message_template=(
                        "Hi {{name}}! Welcome to the ministry leadership team. "
                        "We have a strategy meeting this {{meeting_day}} at {{meeting_time}}. "
                        "Looking forward to hearing your vision! 🚀"
                    ),
                    communication_channels=["whatsapp", "voice"]
                ),
                ScheduledFollowup(
                    delay_days=14,
                    message_template=(
                        "{{name}}, as a ministry leader, you have access to advanced training resources. "
                        "Check out the leadership portal: {{portal_url}}. "
                        "Let's continue growing together! 📈"
                    ),
                    communication_channels=["whatsapp"]
                )
            ],
            description="Leading ministry direction and strategy"
        )
    ]

    # Insert stages
    inserted_count = 0
    for stage in stages:
        # Check if stage already exists
        existing = await db.journey_stages.find_one({
            "organization_id": ObjectId(organization_id),
            "journey_type": "ministry",
            "stage_name": stage.stage_name
        })

        if not existing:
            stage_dict = stage.model_dump(by_alias=True, exclude={"id"})
            await db.journey_stages.insert_one(stage_dict)
            inserted_count += 1
            print(f"   ✅ Created ministry stage: {stage.stage_display_name}")
        else:
            print(f"   ⏭️  Skipped (exists): {stage.stage_display_name}")

    return inserted_count


async def seed_all_journey_stages(organization_id: str = None):
    """
    Seed all journey stages for an organization.

    Args:
        organization_id: Organization ID (optional, defaults to first org in DB)
    """
    print("\n" + "="*60)
    print("   CHURCHFLOW JOURNEY STAGES SEED SCRIPT")
    print("="*60 + "\n")

    await connect_to_mongodb()
    db = get_database()

    # Get organization ID if not provided
    if not organization_id:
        # Get first organization from organizations collection
        first_org = await db.organizations.find_one({})
        if first_org:
            organization_id = str(first_org["_id"])
            print(f"ℹ️  Using organization: {first_org.get('name', 'Unknown')} ({organization_id})")
        else:
            print("❌ No organizations found. Please create an organization first.")
            await close_mongodb_connection()
            return
    else:
        # Verify organization exists
        org = await db.organizations.find_one({"_id": ObjectId(organization_id)})
        if org:
            print(f"ℹ️  Using organization: {org.get('name', 'Unknown')} ({organization_id})")
        else:
            print(f"❌ Organization {organization_id} not found.")
            await close_mongodb_connection()
            return

    print("\n📖 Seeding Spiritual Journey Stages...")
    spiritual_count = await seed_spiritual_journey_stages(organization_id)

    print("\n🏠 Seeding Cell Journey Stages...")
    cell_count = await seed_cell_journey_stages(organization_id)

    print("\n⛪ Seeding Ministry Journey Stages...")
    ministry_count = await seed_ministry_journey_stages(organization_id)

    # Summary
    total_inserted = spiritual_count + cell_count + ministry_count
    print("\n" + "="*60)
    print(f"   SEED COMPLETE")
    print("="*60)
    print(f"   Spiritual Journey: {spiritual_count} stages created")
    print(f"   Cell Journey:      {cell_count} stages created")
    print(f"   Ministry Journey:  {ministry_count} stages created")
    print(f"   TOTAL:             {total_inserted} stages created")
    print("="*60 + "\n")

    await close_mongodb_connection()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed default journey stages for ChurchFlow")
    parser.add_argument(
        "--organization-id",
        type=str,
        help="Organization ID to seed stages for (optional, uses first org if not provided)"
    )

    args = parser.parse_args()

    asyncio.run(seed_all_journey_stages(args.organization_id))
