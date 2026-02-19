"""
Populate ChurchFlow database with sample data from Action Chapel International
and Impact Conference 2025.
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


# Connection string with properly encoded password
username = "admin"
password = "aawwER4444%"  # Password contains % character
host = "127.0.0.1"
port = "27017"
database = "churchflow"

MONGODB_URL = os.getenv("MONGODB_URL", f"mongodb://{quote_plus(username)}:{quote_plus(password)}@{host}:{port}/{database}?authSource=admin")


def populate_data():
    """Populate the database with sample data."""
    client = MongoClient(MONGODB_URL)
    db = client.churchflow

    print("🔄 Starting data population...")

    # Clear existing data
    print("🗑️  Clearing existing data...")
    db.branches.delete_many({})
    db.conferences.delete_many({})
    db.bus_routes.delete_many({})
    db.registrations.delete_many({})

    # Create Action Chapel branches
    print("🏢 Creating branches...")
    branches_data = [
        {
            "name": "Action Chapel - Spintex",
            "location": "37 Spintex Road, Accra",
            "region": "Greater Accra",
            "capacity": 5000,
            "contact_phone": "+233262626906",
            "contact_email": "admin@actionchapel.net",
            "is_headquarters": True,
            "created_at": datetime.utcnow()
        },
        {
            "name": "Action Chapel - Legon",
            "location": "University of Ghana, Legon Campus",
            "region": "Greater Accra",
            "capacity": 800,
            "contact_phone": "+233262626906",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Action Chapel - Tema",
            "location": "Community 1, Tema",
            "region": "Greater Accra",
            "capacity": 1200,
            "contact_phone": "+233262626906",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Action Chapel - Kumasi (Abrepo Ark Cathedral)",
            "location": "Abrepo Asubonteng, Kumasi",
            "region": "Ashanti",
            "capacity": 2000,
            "contact_phone": "+233262626906",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Action Chapel - Takoradi",
            "location": "Market Circle, Takoradi",
            "region": "Western",
            "capacity": 600,
            "contact_phone": "+233262626906",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Action Chapel - Cape Coast",
            "location": "Cape Coast University Road",
            "region": "Central",
            "capacity": 500,
            "contact_phone": "+233262626906",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Action Chapel - Ho",
            "location": "Ho Municipal, Volta Region",
            "region": "Volta",
            "capacity": 400,
            "contact_phone": "+233262626906",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Action Chapel - Tamale",
            "location": "Tamale Central",
            "region": "Northern",
            "capacity": 600,
            "contact_phone": "+233262626906",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Action Chapel - Koforidua",
            "location": "Koforidua, Eastern Region",
            "region": "Eastern",
            "capacity": 500,
            "contact_phone": "+233262626906",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Action Chapel - Madina",
            "location": "Madina Market, Accra",
            "region": "Greater Accra",
            "capacity": 1000,
            "contact_phone": "+233262626906",
            "created_at": datetime.utcnow()
        }
    ]

    branch_results = db.branches.insert_many(branches_data)
    branch_ids = list(branch_results.inserted_ids)
    print(f"✅ Created {len(branch_ids)} branches")

    # Create Impact Conference 2025
    print("📅 Creating conference...")
    conference_data = {
        "name": "IMPACT 2025",
        "description": "Every time the Spirit of God moves, lives are changed and destinies are rewritten. Eight days of divine impartation with a dynamic lineup of speakers.",
        "theme": "Let There Be A Performance",
        "start_date": datetime(2025, 11, 30, 9, 0),  # Nov 30, 2025 9:00 AM
        "end_date": datetime(2025, 12, 7, 21, 0),    # Dec 7, 2025 9:00 PM
        "venue": "Action Chapel International Prayer Cathedral, 37 Spintex Road, Accra",
        "venue_latitude": 5.62564,
        "venue_longitude": -0.164432,
        "expected_attendance": 10000,
        "registration_open": True,
        "speakers": [
            {
                "name": "Apostle Joshua Selman",
                "title": "President, Eternity Network International",
                "image_url": "https://play-lh.googleusercontent.com/zKvj20CQfl4DJO97MW1RWpPLY40xqWLHmZqUW3VGVLCQJhlM9sC3aBfXG4sc5o6dYvUh",
                "bio": "A prophetic voice and teacher of the Word, passionate about the deeper things of God."
            },
            {
                "name": "Rev. Eastwood Anaba",
                "title": "Founder, Eastwood Anaba Ministries",
                "image_url": "https://eastwoodanaba.org.uk/wp-content/uploads/2021/02/Rev-Anaba_A.jpg",
                "bio": "Dynamic preacher and Bible teacher known for practical, transformational messages."
            },
            {
                "name": "Bishop Bernard Ogyiri Asare",
                "title": "Founder, Zion Praise Chapel International",
                "image_url": "https://lookaside.fbsbx.com/lookaside/crawler/media/?media_id=1075189857941281",
                "bio": "Apostolic leader with a heart for revival and spiritual awakening."
            },
            {
                "name": "Rev. Dr. Robert Ampiah-Kwofi",
                "title": "Resident Pastor, Action Chapel International",
                "image_url": "https://pbs.twimg.com/profile_images/1240310730072764419/639vvDGS_400x400.jpg",
                "bio": "Passionate minister with a calling to raise transformational leaders."
            },
            {
                "name": "Apostle Isi Igenegba",
                "title": "Lead Pastor, Celebration Church International",
                "image_url": "https://lookaside.instagram.com/seo/google_widget/crawler/?media_id=3248985699560630491",
                "bio": "Prophetic voice and worship leader passionate about the presence of God."
            },
            {
                "name": "Rev. Dr. David Antwi",
                "title": "Founding Pastor, Kharis Church London",
                "image_url": "https://via.placeholder.com/400x400/6B46C1/FFFFFF?text=Rev.+David+Antwi",
                "bio": "Church planter and revivalist with a heart for kingdom expansion."
            }
        ],
        "contact_phone": "+233262626906",
        "contact_email": "impact@actionchapel.net",
        "website": "https://actionchapel.net/impact/",
        "created_at": datetime.utcnow()
    }

    conference_result = db.conferences.insert_one(conference_data)
    conference_id = conference_result.inserted_id
    print(f"✅ Created conference: IMPACT 2025")

    # Create bus routes
    print("🚌 Creating bus routes...")
    bus_routes_data = [
        # Accra Routes
        {
            "name": "Legon to Spintex Route",
            "departure_location": "University of Ghana, Legon Main Gate",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "07:00 AM",
            "arrival_time": "08:00 AM",
            "capacity": 50,
            "available_seats": 43,
            "driver_name": "Kwame Mensah",
            "driver_phone": "+233244123456",
            "bus_number": "AC-001",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        {
            "name": "Madina to Spintex Route",
            "departure_location": "Madina Market",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "07:15 AM",
            "arrival_time": "08:00 AM",
            "capacity": 40,
            "available_seats": 35,
            "driver_name": "Yaw Boateng",
            "driver_phone": "+233244345678",
            "bus_number": "AC-002",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        {
            "name": "Dansoman to Spintex Route",
            "departure_location": "Dansoman Keep Fit Club",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "06:45 AM",
            "arrival_time": "08:15 AM",
            "capacity": 50,
            "available_seats": 41,
            "driver_name": "Abena Osei",
            "driver_phone": "+233244111333",
            "bus_number": "AC-003",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        {
            "name": "Kaneshie to Spintex Route",
            "departure_location": "Kaneshie First Light",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "07:00 AM",
            "arrival_time": "08:00 AM",
            "capacity": 45,
            "available_seats": 38,
            "driver_name": "Samuel Adjei",
            "driver_phone": "+233244222444",
            "bus_number": "AC-004",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        {
            "name": "Circle to Spintex Route",
            "departure_location": "Kwame Nkrumah Circle",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "07:10 AM",
            "arrival_time": "07:55 AM",
            "capacity": 50,
            "available_seats": 45,
            "driver_name": "Grace Amoah",
            "driver_phone": "+233244333555",
            "bus_number": "AC-005",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        {
            "name": "Achimota to Spintex Route",
            "departure_location": "Achimota Mall",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "06:50 AM",
            "arrival_time": "08:00 AM",
            "capacity": 50,
            "available_seats": 47,
            "driver_name": "Frank Mensah",
            "driver_phone": "+233244444666",
            "bus_number": "AC-006",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        {
            "name": "Adenta to Spintex Route",
            "departure_location": "Adenta Barrier",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "07:20 AM",
            "arrival_time": "08:05 AM",
            "capacity": 40,
            "available_seats": 32,
            "driver_name": "Ernestina Adom",
            "driver_phone": "+233244555777",
            "bus_number": "AC-007",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        {
            "name": "Teshie to Spintex Route",
            "departure_location": "Teshie Nungua Estate",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "07:25 AM",
            "arrival_time": "07:55 AM",
            "capacity": 35,
            "available_seats": 28,
            "driver_name": "Daniel Quartey",
            "driver_phone": "+233244666888",
            "bus_number": "AC-008",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        {
            "name": "Nungua to Spintex Route",
            "departure_location": "Nungua Barrier",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "07:30 AM",
            "arrival_time": "08:00 AM",
            "capacity": 40,
            "available_seats": 36,
            "driver_name": "Mary Tetteh",
            "driver_phone": "+233244777999",
            "bus_number": "AC-009",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        {
            "name": "Kasoa to Spintex Route",
            "departure_location": "Kasoa Toll Booth",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "06:30 AM",
            "arrival_time": "08:15 AM",
            "capacity": 60,
            "available_seats": 54,
            "driver_name": "Richard Okai",
            "driver_phone": "+233244888000",
            "bus_number": "AC-010",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        {
            "name": "East Legon to Spintex Route",
            "departure_location": "A&C Mall, East Legon",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "07:15 AM",
            "arrival_time": "07:50 AM",
            "capacity": 40,
            "available_seats": 37,
            "driver_name": "Patricia Darko",
            "driver_phone": "+233244999111",
            "bus_number": "AC-011",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        {
            "name": "Osu to Spintex Route",
            "departure_location": "Osu Oxford Street",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "07:20 AM",
            "arrival_time": "07:50 AM",
            "capacity": 35,
            "available_seats": 30,
            "driver_name": "Michael Nortey",
            "driver_phone": "+233244000222",
            "bus_number": "AC-012",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        {
            "name": "Labone to Spintex Route",
            "departure_location": "Labone Café",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "07:25 AM",
            "arrival_time": "07:55 AM",
            "capacity": 30,
            "available_seats": 25,
            "driver_name": "Janet Addo",
            "driver_phone": "+233244111444",
            "bus_number": "AC-013",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        {
            "name": "Airport Residential to Spintex Route",
            "departure_location": "Airport Residential Area",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "07:10 AM",
            "arrival_time": "07:45 AM",
            "capacity": 35,
            "available_seats": 31,
            "driver_name": "Albert Quaye",
            "driver_phone": "+233244222555",
            "bus_number": "AC-014",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        {
            "name": "Tema to Spintex Route",
            "departure_location": "Tema Community 1 Market",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "07:30 AM",
            "arrival_time": "08:15 AM",
            "capacity": 50,
            "available_seats": 42,
            "driver_name": "Kofi Asamoah",
            "driver_phone": "+233244234567",
            "bus_number": "AC-015",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        {
            "name": "Ashaiman to Spintex Route",
            "departure_location": "Ashaiman Market",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "07:00 AM",
            "arrival_time": "08:00 AM",
            "capacity": 45,
            "available_seats": 39,
            "driver_name": "Ibrahim Mohammed",
            "driver_phone": "+233244333666",
            "bus_number": "AC-016",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        {
            "name": "Weija to Spintex Route",
            "departure_location": "Weija Junction",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "06:40 AM",
            "arrival_time": "08:10 AM",
            "capacity": 50,
            "available_seats": 46,
            "driver_name": "Rebecca Ansah",
            "driver_phone": "+233244444777",
            "bus_number": "AC-017",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        },
        # Long Distance Routes
        {
            "name": "Kumasi to Spintex Route",
            "departure_location": "Abrepo Ark Cathedral, Kumasi",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "04:00 AM",
            "arrival_time": "08:30 AM",
            "capacity": 60,
            "available_seats": 52,
            "driver_name": "Kwabena Owusu",
            "driver_phone": "+233244456789",
            "bus_number": "AC-KM-001",
            "conference_id": str(conference_id),
            "is_long_distance": True,
            "created_at": datetime.utcnow()
        },
        {
            "name": "Takoradi to Spintex Route",
            "departure_location": "Action Chapel Takoradi, Market Circle",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "04:00 AM",
            "arrival_time": "08:30 AM",
            "capacity": 60,
            "available_seats": 55,
            "driver_name": "Ama Serwaa",
            "driver_phone": "+233244567890",
            "bus_number": "AC-TK-001",
            "conference_id": str(conference_id),
            "is_long_distance": True,
            "created_at": datetime.utcnow()
        },
        {
            "name": "Ho to Spintex Route",
            "departure_location": "Action Chapel Ho",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "05:00 AM",
            "arrival_time": "08:30 AM",
            "capacity": 50,
            "available_seats": 44,
            "driver_name": "Emmanuel Dzadey",
            "driver_phone": "+233244678901",
            "bus_number": "AC-HO-001",
            "conference_id": str(conference_id),
            "is_long_distance": True,
            "created_at": datetime.utcnow()
        },
        {
            "name": "Cape Coast to Spintex Route",
            "departure_location": "Action Chapel Cape Coast",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "05:00 AM",
            "arrival_time": "08:00 AM",
            "capacity": 50,
            "available_seats": 47,
            "driver_name": "Adjoa Mensah",
            "driver_phone": "+233244789012",
            "bus_number": "AC-CC-001",
            "conference_id": str(conference_id),
            "is_long_distance": True,
            "created_at": datetime.utcnow()
        },
        {
            "name": "Koforidua to Spintex Route",
            "departure_location": "Action Chapel Koforidua",
            "destination": "Action Chapel Spintex, 37 Spintex Road",
            "departure_time": "06:00 AM",
            "arrival_time": "08:00 AM",
            "capacity": 50,
            "available_seats": 48,
            "driver_name": "Joseph Tetteh",
            "driver_phone": "+233244890123",
            "bus_number": "AC-KF-001",
            "conference_id": str(conference_id),
            "created_at": datetime.utcnow()
        }
    ]

    bus_results = db.bus_routes.insert_many(bus_routes_data)
    bus_ids = list(bus_results.inserted_ids)
    print(f"✅ Created {len(bus_ids)} bus routes")

    # Create sample registrations
    print("👥 Creating sample registrations...")
    registrations_data = [
        {
            "conference_id": str(conference_id),
            "user_name": "John Mensah",
            "user_phone": "+233244111222",
            "user_email": "john.mensah@example.com",
            "branch_id": str(branch_ids[1]),  # Legon branch
            "requires_bus": True,
            "bus_route_id": str(bus_ids[0]),  # Legon to Spintex
            "registration_code": "IMP25-001",
            "checked_in": True,
            "created_at": datetime.utcnow() - timedelta(days=5)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Grace Osei",
            "user_phone": "+233244222333",
            "user_email": "grace.osei@example.com",
            "branch_id": str(branch_ids[2]),  # Tema branch
            "requires_bus": True,
            "bus_route_id": str(bus_ids[14]),  # Tema to Spintex
            "registration_code": "IMP25-002",
            "checked_in": True,
            "created_at": datetime.utcnow() - timedelta(days=4)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Emmanuel Boateng",
            "user_phone": "+233244333444",
            "user_email": "emmanuel.boateng@example.com",
            "branch_id": str(branch_ids[3]),  # Kumasi branch
            "requires_bus": True,
            "bus_route_id": str(bus_ids[17]),  # Kumasi to Spintex
            "registration_code": "IMP25-003",
            "special_needs": "Wheelchair accessible seating",
            "checked_in": False,
            "created_at": datetime.utcnow() - timedelta(days=3)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Akua Serwaa",
            "user_phone": "+233244444555",
            "user_email": "akua.serwaa@example.com",
            "branch_id": str(branch_ids[9]),  # Madina branch
            "requires_bus": True,
            "bus_route_id": str(bus_ids[1]),  # Madina to Spintex
            "registration_code": "IMP25-004",
            "checked_in": True,
            "created_at": datetime.utcnow() - timedelta(days=4)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Kwame Asante",
            "user_phone": "+233244555666",
            "user_email": "kwame.asante@example.com",
            "branch_id": str(branch_ids[0]),  # Spintex HQ
            "requires_bus": False,
            "registration_code": "IMP25-005",
            "checked_in": True,
            "created_at": datetime.utcnow() - timedelta(days=6)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Ama Owusu",
            "user_phone": "+233244666777",
            "user_email": "ama.owusu@example.com",
            "branch_id": str(branch_ids[1]),  # Legon
            "requires_bus": True,
            "bus_route_id": str(bus_ids[0]),
            "registration_code": "IMP25-006",
            "checked_in": False,
            "created_at": datetime.utcnow() - timedelta(days=2)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Kofi Adjei",
            "user_phone": "+233244777888",
            "user_email": "kofi.adjei@example.com",
            "branch_id": str(branch_ids[0]),  # Spintex
            "requires_bus": True,
            "bus_route_id": str(bus_ids[4]),  # Circle
            "registration_code": "IMP25-007",
            "checked_in": True,
            "created_at": datetime.utcnow() - timedelta(days=1)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Abena Frimpong",
            "user_phone": "+233244888999",
            "user_email": "abena.frimpong@example.com",
            "branch_id": str(branch_ids[9]),  # Madina
            "requires_bus": True,
            "bus_route_id": str(bus_ids[6]),  # Adenta
            "registration_code": "IMP25-008",
            "checked_in": False,
            "created_at": datetime.utcnow() - timedelta(hours=12)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Yaw Darkwa",
            "user_phone": "+233244000111",
            "user_email": "yaw.darkwa@example.com",
            "branch_id": str(branch_ids[0]),
            "requires_bus": True,
            "bus_route_id": str(bus_ids[2]),  # Dansoman
            "registration_code": "IMP25-009",
            "checked_in": True,
            "created_at": datetime.utcnow() - timedelta(days=7)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Efua Mensah",
            "user_phone": "+233244111000",
            "user_email": "efua.mensah@example.com",
            "branch_id": str(branch_ids[1]),
            "requires_bus": True,
            "bus_route_id": str(bus_ids[10]),  # East Legon
            "registration_code": "IMP25-010",
            "checked_in": False,
            "created_at": datetime.utcnow() - timedelta(hours=6)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Samuel Nkrumah",
            "user_phone": "+233244222111",
            "user_email": "samuel.nkrumah@example.com",
            "branch_id": str(branch_ids[0]),
            "requires_bus": True,
            "bus_route_id": str(bus_ids[9]),  # Kasoa
            "registration_code": "IMP25-011",
            "checked_in": True,
            "created_at": datetime.utcnow() - timedelta(days=3)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Adjoa Boateng",
            "user_phone": "+233244333222",
            "user_email": "adjoa.boateng@example.com",
            "branch_id": str(branch_ids[2]),  # Tema
            "requires_bus": True,
            "bus_route_id": str(bus_ids[8]),  # Nungua
            "registration_code": "IMP25-012",
            "checked_in": False,
            "created_at": datetime.utcnow() - timedelta(hours=18)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Kwesi Annan",
            "user_phone": "+233244444333",
            "user_email": "kwesi.annan@example.com",
            "branch_id": str(branch_ids[0]),
            "requires_bus": False,
            "registration_code": "IMP25-013",
            "checked_in": True,
            "created_at": datetime.utcnow() - timedelta(days=5)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Akosua Gyamfi",
            "user_phone": "+233244555444",
            "user_email": "akosua.gyamfi@example.com",
            "branch_id": str(branch_ids[4]),  # Takoradi
            "requires_bus": True,
            "bus_route_id": str(bus_ids[18]),  # Takoradi long distance
            "registration_code": "IMP25-014",
            "checked_in": False,
            "created_at": datetime.utcnow() - timedelta(days=2)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Ibrahim Agyei",
            "user_phone": "+233244666555",
            "user_email": "ibrahim.agyei@example.com",
            "branch_id": str(branch_ids[0]),
            "requires_bus": True,
            "bus_route_id": str(bus_ids[15]),  # Ashaiman
            "registration_code": "IMP25-015",
            "checked_in": True,
            "created_at": datetime.utcnow() - timedelta(days=4)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Ernestina Opoku",
            "user_phone": "+233244777666",
            "user_email": "ernestina.opoku@example.com",
            "branch_id": str(branch_ids[9]),
            "requires_bus": True,
            "bus_route_id": str(bus_ids[5]),  # Achimota
            "registration_code": "IMP25-016",
            "checked_in": False,
            "created_at": datetime.utcnow() - timedelta(hours=9)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Frederick Asare",
            "user_phone": "+233244888777",
            "user_email": "frederick.asare@example.com",
            "branch_id": str(branch_ids[5]),  # Cape Coast
            "requires_bus": True,
            "bus_route_id": str(bus_ids[20]),  # Cape Coast long distance
            "registration_code": "IMP25-017",
            "checked_in": False,
            "created_at": datetime.utcnow() - timedelta(days=1)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Beatrice Tetteh",
            "user_phone": "+233244999888",
            "user_email": "beatrice.tetteh@example.com",
            "branch_id": str(branch_ids[0]),
            "requires_bus": True,
            "bus_route_id": str(bus_ids[11]),  # Osu
            "registration_code": "IMP25-018",
            "checked_in": True,
            "created_at": datetime.utcnow() - timedelta(days=6)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Michael Ofosu",
            "user_phone": "+233244000999",
            "user_email": "michael.ofosu@example.com",
            "branch_id": str(branch_ids[1]),
            "requires_bus": True,
            "bus_route_id": str(bus_ids[12]),  # Labone
            "registration_code": "IMP25-019",
            "checked_in": False,
            "created_at": datetime.utcnow() - timedelta(hours=15)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Comfort Acheampong",
            "user_phone": "+233244111222",
            "user_email": "comfort.acheampong@example.com",
            "branch_id": str(branch_ids[6]),  # Ho
            "requires_bus": True,
            "bus_route_id": str(bus_ids[19]),  # Ho long distance
            "registration_code": "IMP25-020",
            "checked_in": False,
            "created_at": datetime.utcnow() - timedelta(days=3)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Daniel Owusu",
            "user_phone": "+233244222333",
            "user_email": "daniel.owusu@example.com",
            "branch_id": str(branch_ids[0]),
            "requires_bus": True,
            "bus_route_id": str(bus_ids[13]),  # Airport Residential
            "registration_code": "IMP25-021",
            "checked_in": True,
            "created_at": datetime.utcnow() - timedelta(days=2)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Esther Asante",
            "user_phone": "+233244333444",
            "user_email": "esther.asante@example.com",
            "branch_id": str(branch_ids[2]),
            "requires_bus": True,
            "bus_route_id": str(bus_ids[7]),  # Teshie
            "registration_code": "IMP25-022",
            "checked_in": False,
            "created_at": datetime.utcnow() - timedelta(hours=20)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Joseph Nkansah",
            "user_phone": "+233244444555",
            "user_email": "joseph.nkansah@example.com",
            "branch_id": str(branch_ids[0]),
            "requires_bus": True,
            "bus_route_id": str(bus_ids[16]),  # Weija
            "registration_code": "IMP25-023",
            "checked_in": True,
            "created_at": datetime.utcnow() - timedelta(days=5)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Patience Ofori",
            "user_phone": "+233244555666",
            "user_email": "patience.ofori@example.com",
            "branch_id": str(branch_ids[8]),  # Koforidua
            "requires_bus": True,
            "bus_route_id": str(bus_ids[21]),  # Koforidua long distance
            "registration_code": "IMP25-024",
            "checked_in": False,
            "created_at": datetime.utcnow() - timedelta(days=1)
        },
        {
            "conference_id": str(conference_id),
            "user_name": "Stephen Ansah",
            "user_phone": "+233244666777",
            "user_email": "stephen.ansah@example.com",
            "branch_id": str(branch_ids[0]),
            "requires_bus": True,
            "bus_route_id": str(bus_ids[3]),  # Kaneshie
            "registration_code": "IMP25-025",
            "checked_in": True,
            "created_at": datetime.utcnow() - timedelta(days=3)
        }
    ]

    registration_results = db.registrations.insert_many(registrations_data)
    print(f"✅ Created {len(registration_results.inserted_ids)} sample registrations")

    print("\n✅ Sample data population completed successfully!")
    print(f"\n📊 Summary:")
    print(f"  - Branches: {len(branch_ids)}")
    print(f"  - Conferences: 1 (IMPACT 2025)")
    print(f"  - Bus Routes: {len(bus_ids)}")
    print(f"  - Registrations: {len(registration_results.inserted_ids)}")
    print(f"\n🔗 Conference ID: {conference_id}")

    client.close()


if __name__ == "__main__":
    populate_data()
