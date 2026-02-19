"""
Populate EventFlow database with IMPACT 2025 Conference data.

Creates a vibrant, engaging event with tasks, timeline, and details.
"""
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from bson import ObjectId


# Connection string
username = "admin"
password = "aawwER4444%"
host = "127.0.0.1"
port = "27017"
database = "kasaai_eventflow"

MONGODB_URL = os.getenv("MONGODB_URL", f"mongodb://{quote_plus(username)}:{quote_plus(password)}@{host}:{port}/{database}?authSource=admin")


def populate_data():
    """Populate the database with IMPACT 2025 conference data."""
    client = MongoClient(MONGODB_URL)
    db = client[database]

    print("🚀 Starting EventFlow data population...")
    print(f"📦 Database: {database}")

    # Clear existing data
    print("🗑️  Clearing existing data...")
    db.events.delete_many({})
    db.tasks.delete_many({})
    db.responsible_persons.delete_many({})

    # Create IMPACT 2025 Event
    print("📅 Creating IMPACT 2025 Conference...")

    # Organizer ID (sample user)
    organizer_id = str(ObjectId())

    event_data = {
        "name": "IMPACT 2025 Conference",
        "type": "conference",
        "date": datetime(2025, 11, 30, 9, 0),  # Nov 30, 2025 9:00 AM
        "location": "Action Chapel International Prayer Cathedral, 37 Spintex Road, Accra",
        "num_guests": 10000,
        "budget_min": 200000.0,
        "budget_max": 500000.0,
        "status": "planning",
        "organizer_id": organizer_id,
        "description": """Every time the Spirit of God moves, lives are changed and destinies are rewritten.

IMPACT 2025 is an 8-day divine impartation conference featuring a dynamic lineup of international speakers including:

🎤 Apostle Joshua Selman - President, Eternity Network International
🎤 Rev. Eastwood Anaba - Founder, Eastwood Anaba Ministries
🎤 Bishop Bernard Ogyiri Asare - Founder, Zion Praise Chapel International
🎤 Rev. Dr. Robert Ampiah-Kwofi - Resident Pastor, Action Chapel International
🎤 Apostle Isi Igenegba - Lead Pastor, Celebration Church International
🎤 Rev. Dr. David Antwi - Founding Pastor, Kharis Church London

Theme: "Let There Be A Performance"
📅 November 30 - December 7, 2025
📍 Action Chapel International Prayer Cathedral
👥 Expected Attendance: 10,000+

Contact: impact@actionchapel.net | +233262626906
Website: https://actionchapel.net/impact/""",
        "documents": [
            "https://actionchapel.net/impact/",
        ],
        "tags": ["conference", "spiritual", "youth", "international", "worship", "impact2025"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    event_result = db.events.insert_one(event_data)
    event_id = str(event_result.inserted_id)
    print(f"✅ Created event: IMPACT 2025 (ID: {event_id})")

    # Create Responsible Persons (Event Team)
    print("👥 Creating event team...")

    team_members = [
        {
            "name": "Pastor Daniel Mensah",
            "role": "Event Coordinator",
            "phone": "+233262626906",
            "email": "daniel.mensah@actionchapel.net",
            "department": "Operations",
            "availability": "full-time",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Grace Osei",
            "role": "Logistics Manager",
            "phone": "+233244123456",
            "email": "grace.osei@actionchapel.net",
            "department": "Logistics",
            "availability": "full-time",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Emmanuel Boateng",
            "role": "Technical Director",
            "phone": "+233244234567",
            "email": "emmanuel.boateng@actionchapel.net",
            "department": "Technical",
            "availability": "full-time",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Akua Serwaa",
            "role": "Hospitality Lead",
            "phone": "+233244345678",
            "email": "akua.serwaa@actionchapel.net",
            "department": "Hospitality",
            "availability": "full-time",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Kwame Asante",
            "role": "Finance Manager",
            "phone": "+233244456789",
            "email": "kwame.asante@actionchapel.net",
            "department": "Finance",
            "availability": "full-time",
            "created_at": datetime.utcnow()
        }
    ]

    team_results = db.responsible_persons.insert_many(team_members)
    team_ids = [str(id) for id in team_results.inserted_ids]
    print(f"✅ Created {len(team_ids)} team members")

    # Create Event Tasks
    print("📋 Creating event tasks...")

    # Calculate task deadlines based on event date
    event_date = datetime(2025, 11, 30, 9, 0)

    tasks_data = [
        # Venue & Logistics
        {
            "event_id": event_id,
            "title": "Confirm venue booking and capacity",
            "description": "Verify Prayer Cathedral booking for 10,000 attendees, confirm seating arrangement and accessibility",
            "category": "venue",
            "priority": "high",
            "status": "in-progress",
            "assigned_to": team_ids[1],  # Grace Osei
            "deadline": event_date - timedelta(days=90),
            "cost_estimate": 50000.0,
            "notes": "Need wheelchair accessibility confirmation",
            "created_at": datetime.utcnow()
        },
        {
            "event_id": event_id,
            "title": "Arrange transportation for out-of-town attendees",
            "description": "Organize buses from Kumasi, Takoradi, Ho, Cape Coast, and other cities",
            "category": "logistics",
            "priority": "high",
            "status": "pending",
            "assigned_to": team_ids[1],
            "deadline": event_date - timedelta(days=45),
            "cost_estimate": 80000.0,
            "created_at": datetime.utcnow()
        },
        {
            "event_id": event_id,
            "title": "Book hotels for international speakers",
            "description": "Reserve 5-star accommodation for 6 international speakers (7 nights each)",
            "category": "hospitality",
            "priority": "high",
            "status": "pending",
            "assigned_to": team_ids[3],  # Akua Serwaa
            "deadline": event_date - timedelta(days=60),
            "cost_estimate": 120000.0,
            "created_at": datetime.utcnow()
        },

        # Technical Setup
        {
            "event_id": event_id,
            "title": "Setup professional sound system",
            "description": "Install high-quality PA system for 10,000 capacity venue with backup systems",
            "category": "technical",
            "priority": "critical",
            "status": "pending",
            "assigned_to": team_ids[2],  # Emmanuel Boateng
            "deadline": event_date - timedelta(days=7),
            "cost_estimate": 45000.0,
            "created_at": datetime.utcnow()
        },
        {
            "event_id": event_id,
            "title": "Install LED screens and live streaming equipment",
            "description": "Setup multiple LED screens and 4K streaming for online viewers",
            "category": "technical",
            "priority": "high",
            "status": "pending",
            "assigned_to": team_ids[2],
            "deadline": event_date - timedelta(days=7),
            "cost_estimate": 60000.0,
            "created_at": datetime.utcnow()
        },
        {
            "event_id": event_id,
            "title": "Setup stage lighting and effects",
            "description": "Professional lighting design with intelligent lights and atmospheric effects",
            "category": "technical",
            "priority": "medium",
            "status": "pending",
            "assigned_to": team_ids[2],
            "deadline": event_date - timedelta(days=5),
            "cost_estimate": 35000.0,
            "created_at": datetime.utcnow()
        },

        # Marketing & Registration
        {
            "event_id": event_id,
            "title": "Launch online registration portal",
            "description": "Deploy EventFlow registration system with QR codes and mobile check-in",
            "category": "marketing",
            "priority": "high",
            "status": "completed",
            "assigned_to": team_ids[0],  # Pastor Daniel
            "deadline": event_date - timedelta(days=120),
            "completed_at": datetime.utcnow() - timedelta(days=15),
            "cost_estimate": 15000.0,
            "created_at": datetime.utcnow()
        },
        {
            "event_id": event_id,
            "title": "Design and print promotional materials",
            "description": "Create banners, flyers, posters, and social media graphics",
            "category": "marketing",
            "priority": "high",
            "status": "in-progress",
            "assigned_to": team_ids[0],
            "deadline": event_date - timedelta(days=75),
            "cost_estimate": 25000.0,
            "created_at": datetime.utcnow()
        },
        {
            "event_id": event_id,
            "title": "Run social media advertising campaign",
            "description": "Facebook, Instagram, Twitter ads targeting youth and Christians in Ghana",
            "category": "marketing",
            "priority": "medium",
            "status": "pending",
            "assigned_to": team_ids[0],
            "deadline": event_date - timedelta(days=60),
            "cost_estimate": 40000.0,
            "created_at": datetime.utcnow()
        },

        # Hospitality & Catering
        {
            "event_id": event_id,
            "title": "Arrange catering for 10,000 attendees",
            "description": "Daily meals and refreshments for 8 days - breakfast, lunch, and snacks",
            "category": "catering",
            "priority": "critical",
            "status": "pending",
            "assigned_to": team_ids[3],
            "deadline": event_date - timedelta(days=30),
            "cost_estimate": 200000.0,
            "created_at": datetime.utcnow()
        },
        {
            "event_id": event_id,
            "title": "Setup water and refreshment stations",
            "description": "Install 20 water stations throughout venue with continuous supply",
            "category": "hospitality",
            "priority": "high",
            "status": "pending",
            "assigned_to": team_ids[3],
            "deadline": event_date - timedelta(days=3),
            "cost_estimate": 15000.0,
            "created_at": datetime.utcnow()
        },
        {
            "event_id": event_id,
            "title": "Organize VIP lounge for speakers",
            "description": "Dedicated lounge with refreshments and amenities for all speakers",
            "category": "hospitality",
            "priority": "medium",
            "status": "pending",
            "assigned_to": team_ids[3],
            "deadline": event_date - timedelta(days=5),
            "cost_estimate": 30000.0,
            "created_at": datetime.utcnow()
        },

        # Security & Safety
        {
            "event_id": event_id,
            "title": "Hire professional security team",
            "description": "100 security personnel for crowd control and safety (8 days)",
            "category": "security",
            "priority": "critical",
            "status": "in-progress",
            "assigned_to": team_ids[0],
            "deadline": event_date - timedelta(days=40),
            "cost_estimate": 80000.0,
            "created_at": datetime.utcnow()
        },
        {
            "event_id": event_id,
            "title": "Setup medical and first aid stations",
            "description": "3 medical stations with trained nurses and ambulance on standby",
            "category": "safety",
            "priority": "critical",
            "status": "pending",
            "assigned_to": team_ids[1],
            "deadline": event_date - timedelta(days=20),
            "cost_estimate": 25000.0,
            "created_at": datetime.utcnow()
        },
        {
            "event_id": event_id,
            "title": "Install fire safety equipment",
            "description": "Fire extinguishers, emergency exits marking, and evacuation plan",
            "category": "safety",
            "priority": "high",
            "status": "pending",
            "assigned_to": team_ids[1],
            "deadline": event_date - timedelta(days=10),
            "cost_estimate": 10000.0,
            "created_at": datetime.utcnow()
        },

        # Finance & Administration
        {
            "event_id": event_id,
            "title": "Finalize conference budget and approval",
            "description": "Get board approval for GHS 500,000 conference budget",
            "category": "finance",
            "priority": "critical",
            "status": "completed",
            "assigned_to": team_ids[4],  # Kwame Asante
            "deadline": event_date - timedelta(days=150),
            "completed_at": datetime.utcnow() - timedelta(days=30),
            "cost_estimate": 0.0,
            "created_at": datetime.utcnow()
        },
        {
            "event_id": event_id,
            "title": "Process speaker honorariums and travel",
            "description": "Arrange payments and travel reimbursements for 6 international speakers",
            "category": "finance",
            "priority": "high",
            "status": "in-progress",
            "assigned_to": team_ids[4],
            "deadline": event_date - timedelta(days=45),
            "cost_estimate": 150000.0,
            "created_at": datetime.utcnow()
        },
        {
            "event_id": event_id,
            "title": "Print conference materials and booklets",
            "description": "10,000 conference programs, notebooks, and devotional materials",
            "category": "materials",
            "priority": "medium",
            "status": "pending",
            "assigned_to": team_ids[0],
            "deadline": event_date - timedelta(days=25),
            "cost_estimate": 45000.0,
            "created_at": datetime.utcnow()
        },

        # Volunteer Coordination
        {
            "event_id": event_id,
            "title": "Recruit and train 500 volunteers",
            "description": "Ushers, parking attendants, hospitality, tech support, and prayer teams",
            "category": "volunteers",
            "priority": "high",
            "status": "in-progress",
            "assigned_to": team_ids[0],
            "deadline": event_date - timedelta(days=35),
            "cost_estimate": 50000.0,
            "notes": "Need volunteer coordination app",
            "created_at": datetime.utcnow()
        },
        {
            "event_id": event_id,
            "title": "Conduct volunteer orientation sessions",
            "description": "4 training sessions for all volunteers covering roles and procedures",
            "category": "volunteers",
            "priority": "medium",
            "status": "pending",
            "assigned_to": team_ids[0],
            "deadline": event_date - timedelta(days=15),
            "cost_estimate": 8000.0,
            "created_at": datetime.utcnow()
        },

        # Worship & Program
        {
            "event_id": event_id,
            "title": "Coordinate worship team rehearsals",
            "description": "Schedule and conduct rehearsals for 100-member choir and band",
            "category": "program",
            "priority": "high",
            "status": "in-progress",
            "assigned_to": team_ids[2],
            "deadline": event_date - timedelta(days=20),
            "cost_estimate": 20000.0,
            "created_at": datetime.utcnow()
        },
        {
            "event_id": event_id,
            "title": "Finalize 8-day conference schedule",
            "description": "Daily program with speaker slots, worship sessions, and break times",
            "category": "program",
            "priority": "high",
            "status": "completed",
            "assigned_to": team_ids[0],
            "deadline": event_date - timedelta(days=90),
            "completed_at": datetime.utcnow() - timedelta(days=20),
            "cost_estimate": 0.0,
            "created_at": datetime.utcnow()
        }
    ]

    task_results = db.tasks.insert_many(tasks_data)
    task_ids = [str(id) for id in task_results.inserted_ids]
    print(f"✅ Created {len(task_ids)} tasks")

    # Summary
    print("\n" + "="*50)
    print("✨ IMPACT 2025 Conference Data Population Complete!")
    print("="*50)
    print(f"\n📊 Summary:")
    print(f"  🎯 Event: IMPACT 2025 Conference")
    print(f"  📅 Date: November 30 - December 7, 2025")
    print(f"  📍 Location: Action Chapel Spintex, Accra")
    print(f"  👥 Expected Attendance: 10,000")
    print(f"  💰 Budget: GHS 200,000 - 500,000")
    print(f"\n  📋 Tasks Created: {len(task_ids)}")
    print(f"     ✅ Completed: {sum(1 for task in tasks_data if task['status'] == 'completed')}")
    print(f"     🔄 In Progress: {sum(1 for task in tasks_data if task['status'] == 'in-progress')}")
    print(f"     ⏳ Pending: {sum(1 for task in tasks_data if task['status'] == 'pending')}")
    print(f"\n  👥 Team Members: {len(team_ids)}")
    print(f"\n🔗 Event ID: {event_id}")
    print(f"🌐 Ready to view at: https://eventflow.ailabsafrica.com")
    print("="*50 + "\n")

    client.close()


if __name__ == "__main__":
    populate_data()
