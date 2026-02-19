"""
Script to set up Shield International School as a demo account.

Creates:
1. School admin user in Supabase
2. School entry in MongoDB
3. Sample course materials (Math, English)
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, "/opt/kasaai/apps")
sys.path.insert(0, "/opt/kasaai/apps/studyflow/backend")

from app.core.database import mongodb
from app.core.supabase_client import supabase
from app.models.school import SchoolType, SubscriptionTier
from app.models.user import UserRole
from app.models.material import MaterialType, ProcessingStatus
from bson import ObjectId


async def create_school_admin_user():
    """
    Create Shield International School admin user in Supabase.

    Returns:
        Tuple of (user_id, email, password)
    """
    email = "admin@shield.edu.gh"
    password = "ShieldAdmin2024!"

    print(f"\n📝 Creating school admin user: {email}")

    try:
        # Check if user already exists
        response = supabase.auth.admin.list_users()
        existing_users = [u for u in response if u.email == email]

        if existing_users:
            user_id = existing_users[0].id
            print(f"✓ User already exists with ID: {user_id}")
            return user_id, email, password

        # Create new user
        auth_response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "role": UserRole.SCHOOL.value,
                "full_name": "Shield International School Admin"
            }
        })

        user_id = auth_response.user.id
        print(f"✓ Created admin user with ID: {user_id}")
        print(f"  Email: {email}")
        print(f"  Password: {password}")

        return user_id, email, password

    except Exception as e:
        print(f"✗ Error creating admin user: {str(e)}")
        raise


async def create_school_entry(admin_user_id: str):
    """
    Create Shield International School entry in MongoDB.

    Args:
        admin_user_id: Supabase user ID of school admin

    Returns:
        School ID
    """
    print(f"\n🏫 Creating Shield International School entry...")

    collection = mongodb.get_collection("schools")

    # Check if school already exists
    existing = await collection.find_one({"name": "Shield International School"})
    if existing:
        school_id = str(existing["_id"])
        print(f"✓ School already exists with ID: {school_id}")
        return school_id

    # Create school document
    school_doc = {
        "name": "Shield International School",
        "short_name": "Shield",
        "school_type": SchoolType.SECONDARY.value,
        "website": "https://shield.edu.gh/",
        "email": "info@shield.edu.gh",
        "phone": "+233 XXX XXX XXX",
        "address": "Accra, Ghana",
        "city": "Accra",
        "country": "Ghana",
        "logo_url": None,
        "admin_user_id": admin_user_id,
        "subscription_tier": SubscriptionTier.PREMIUM.value,
        "max_students": 500,
        "max_materials": 200,
        "allowed_subjects": [
            "Mathematics",
            "English Language",
            "Science",
            "Social Studies",
            "Integrated Science",
            "Physics",
            "Chemistry",
            "Biology",
            "History",
            "Geography",
            "French",
            "Computer Science"
        ],
        "metadata": {
            "demo_account": True,
            "setup_date": datetime.utcnow().isoformat()
        },
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await collection.insert_one(school_doc)
    school_id = str(result.inserted_id)

    print(f"✓ Created school with ID: {school_id}")
    print(f"  Name: Shield International School")
    print(f"  Tier: Premium")
    print(f"  Max Students: 500")
    print(f"  Max Materials: 200")

    return school_id


async def create_sample_materials(school_id: str, admin_user_id: str):
    """
    Create sample course materials for Shield International School.

    Args:
        school_id: School ID
        admin_user_id: Admin user ID
    """
    print(f"\n📚 Creating sample course materials...")

    collection = mongodb.get_collection("materials")

    materials = [
        # Mathematics Materials
        {
            "title": "Introduction to Algebra - Grade 10",
            "description": "Comprehensive introduction to algebraic concepts including variables, equations, and expressions.",
            "file_name": "algebra_intro_grade10.pdf",
            "file_path": "/materials/shield/math/algebra_intro_grade10.pdf",
            "file_size": 2048000,  # 2MB
            "file_type": MaterialType.PDF.value,
            "subject": "Mathematics",
            "topics": ["Algebra", "Equations", "Variables", "Expressions"],
            "grade": 10,
            "school_id": school_id,
            "uploaded_by": admin_user_id,
            "status": ProcessingStatus.COMPLETED.value,
            "chunks_count": 45,
            "embedding_collection": "studyflow_materials",
            "metadata": {
                "sample_material": True,
                "course_code": "MATH-10-ALG"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "processed_at": datetime.utcnow()
        },
        {
            "title": "Geometry Fundamentals - Grade 9",
            "description": "Basic geometric concepts including shapes, angles, theorems, and proofs.",
            "file_name": "geometry_fundamentals_grade9.pdf",
            "file_path": "/materials/shield/math/geometry_fundamentals_grade9.pdf",
            "file_size": 3145728,  # 3MB
            "file_type": MaterialType.PDF.value,
            "subject": "Mathematics",
            "topics": ["Geometry", "Shapes", "Angles", "Theorems", "Proofs"],
            "grade": 9,
            "school_id": school_id,
            "uploaded_by": admin_user_id,
            "status": ProcessingStatus.COMPLETED.value,
            "chunks_count": 52,
            "embedding_collection": "studyflow_materials",
            "metadata": {
                "sample_material": True,
                "course_code": "MATH-09-GEO"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "processed_at": datetime.utcnow()
        },
        {
            "title": "Calculus Basics - Grade 12",
            "description": "Introduction to differential and integral calculus with practical applications.",
            "file_name": "calculus_basics_grade12.pdf",
            "file_path": "/materials/shield/math/calculus_basics_grade12.pdf",
            "file_size": 4194304,  # 4MB
            "file_type": MaterialType.PDF.value,
            "subject": "Mathematics",
            "topics": ["Calculus", "Differentiation", "Integration", "Limits"],
            "grade": 12,
            "school_id": school_id,
            "uploaded_by": admin_user_id,
            "status": ProcessingStatus.COMPLETED.value,
            "chunks_count": 68,
            "embedding_collection": "studyflow_materials",
            "metadata": {
                "sample_material": True,
                "course_code": "MATH-12-CAL"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "processed_at": datetime.utcnow()
        },

        # English Language Materials
        {
            "title": "English Grammar and Composition - Grade 10",
            "description": "Comprehensive guide to English grammar, sentence structure, and essay writing.",
            "file_name": "english_grammar_grade10.pdf",
            "file_path": "/materials/shield/english/english_grammar_grade10.pdf",
            "file_size": 2621440,  # 2.5MB
            "file_type": MaterialType.PDF.value,
            "subject": "English Language",
            "topics": ["Grammar", "Composition", "Writing", "Sentence Structure"],
            "grade": 10,
            "school_id": school_id,
            "uploaded_by": admin_user_id,
            "status": ProcessingStatus.COMPLETED.value,
            "chunks_count": 58,
            "embedding_collection": "studyflow_materials",
            "metadata": {
                "sample_material": True,
                "course_code": "ENG-10-GRAM"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "processed_at": datetime.utcnow()
        },
        {
            "title": "Literature Analysis - Grade 11",
            "description": "Study of classic and contemporary literature with analysis techniques.",
            "file_name": "literature_analysis_grade11.pdf",
            "file_path": "/materials/shield/english/literature_analysis_grade11.pdf",
            "file_size": 3670016,  # 3.5MB
            "file_type": MaterialType.PDF.value,
            "subject": "English Language",
            "topics": ["Literature", "Analysis", "Poetry", "Prose", "Drama"],
            "grade": 11,
            "school_id": school_id,
            "uploaded_by": admin_user_id,
            "status": ProcessingStatus.COMPLETED.value,
            "chunks_count": 72,
            "embedding_collection": "studyflow_materials",
            "metadata": {
                "sample_material": True,
                "course_code": "ENG-11-LIT"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "processed_at": datetime.utcnow()
        },
        {
            "title": "Creative Writing Workshop - Grade 12",
            "description": "Advanced creative writing techniques including narrative, descriptive, and persuasive writing.",
            "file_name": "creative_writing_grade12.pdf",
            "file_path": "/materials/shield/english/creative_writing_grade12.pdf",
            "file_size": 1572864,  # 1.5MB
            "file_type": MaterialType.PDF.value,
            "subject": "English Language",
            "topics": ["Creative Writing", "Narrative", "Descriptive Writing", "Essays"],
            "grade": 12,
            "school_id": school_id,
            "uploaded_by": admin_user_id,
            "status": ProcessingStatus.COMPLETED.value,
            "chunks_count": 42,
            "embedding_collection": "studyflow_materials",
            "metadata": {
                "sample_material": True,
                "course_code": "ENG-12-CRW"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "processed_at": datetime.utcnow()
        }
    ]

    # Check for existing materials
    existing_count = await collection.count_documents({"school_id": school_id})
    if existing_count >= len(materials):
        print(f"✓ Sample materials already exist ({existing_count} materials)")
        return

    # Insert materials
    result = await collection.insert_many(materials)
    print(f"✓ Created {len(result.inserted_ids)} sample materials:")
    print(f"  - 3 Mathematics courses (Grades 9, 10, 12)")
    print(f"  - 3 English Language courses (Grades 10, 11, 12)")


async def main():
    """Main setup function."""
    print("=" * 60)
    print("Shield International School Setup")
    print("=" * 60)

    try:
        # Connect to MongoDB
        print("\n🔌 Connecting to MongoDB...")
        await mongodb.connect()
        print("✓ Connected to MongoDB")

        # Create admin user
        admin_user_id, email, password = await create_school_admin_user()

        # Create school entry
        school_id = await create_school_entry(admin_user_id)

        # Create sample materials
        await create_sample_materials(school_id, admin_user_id)

        print("\n" + "=" * 60)
        print("✅ Setup Complete!")
        print("=" * 60)
        print("\n📋 Login Credentials:")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"\n🏫 School ID: {school_id}")
        print("\n💡 You can now login to the StudyFlow portal with these credentials.")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        raise
    finally:
        # Disconnect
        await mongodb.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
