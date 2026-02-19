"""
Populate StudyFlow with Shield International School Data

Creates realistic study materials, students, sessions, and questions
based on Shield International School's Cambridge International curriculum.
"""

import sys
import os
from datetime import datetime, timedelta
import random
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings

async def populate_shield_data():
    """Populate database with Shield International School data."""

    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client.get_database()

    print("🏫 Populating Shield International School Data...")
    print(f"📊 Database: studyflow")

    # Clear existing data (optional - comment out if you want to keep existing)
    print("\n🗑️  Clearing existing data...")
    await db.materials.delete_many({})
    await db.study_sessions.delete_many({})
    await db.questions.delete_many({})
    await db.users.delete_many({"email": {"$regex": "@shield.edu.gh$"}})

    # Create Shield International School users (students)
    print("\n👥 Creating students...")
    students = []
    student_names = [
        ("Kwame", "Mensah"), ("Akua", "Asante"), ("Kofi", "Boateng"),
        ("Ama", "Osei"), ("Kwabena", "Agyeman"), ("Abena", "Owusu"),
        ("Yaw", "Adjei"), ("Afia", "Darko"), ("Kwesi", "Annan"),
        ("Efua", "Ansah"), ("Kojo", "Appiah"), ("Adwoa", "Asare"),
        ("Yaa", "Frimpong"), ("Kofi", "Mensah"), ("Akosua", "Boateng")
    ]

    student_roles = {
        "little_explorers": ["student", "parent"],
        "early_years": ["student", "parent"],
        "junior_school": ["student"],
        "middle_school": ["student"],
        "upper_secondary": ["student"],
    }

    for first_name, last_name in student_names:
        level = random.choice(list(student_roles.keys()))
        email = f"{first_name.lower()}.{last_name.lower()}@shield.edu.gh"

        student = {
            "user_id": str(ObjectId()),
            "email": email,
            "name": f"{first_name} {last_name}",
            "role": random.choice(student_roles[level]),
            "school_level": level,
            "grade": random.randint(1, 13),
            "created_at": datetime.utcnow() - timedelta(days=random.randint(30, 365))
        }
        students.append(student)
        await db.users.insert_one(student)

    print(f"✅ Created {len(students)} students")

    # Create study materials for Cambridge curriculum subjects
    print("\n📚 Creating study materials...")
    materials = []

    # Mathematics materials
    math_materials = [
        {
            "title": "Cambridge IGCSE Mathematics - Algebra Fundamentals",
            "subject": "Mathematics",
            "level": "IGCSE",
            "description": "Comprehensive guide to algebraic expressions, equations, and inequalities following Cambridge IGCSE syllabus.",
            "content": "This material covers fundamental algebraic concepts including linear equations, quadratic expressions, simultaneous equations, and algebraic fractions. Students will learn problem-solving techniques essential for Cambridge examinations.",
            "grade_level": "9-10",
            "keywords": ["algebra", "equations", "IGCSE", "mathematics", "Cambridge"],
        },
        {
            "title": "Cambridge Primary Mathematics - Number Operations",
            "subject": "Mathematics",
            "level": "Primary",
            "description": "Foundation number work including addition, subtraction, multiplication, and division.",
            "content": "Covers place value, mental calculation strategies, written methods for all four operations, and real-world problem solving using numbers up to 1,000,000.",
            "grade_level": "4-6",
            "keywords": ["numbers", "operations", "primary", "mathematics", "Cambridge"],
        },
        {
            "title": "A-Level Pure Mathematics - Calculus",
            "subject": "Mathematics",
            "level": "A-Level",
            "description": "Advanced calculus concepts for Cambridge A-Level Mathematics.",
            "content": "Differentiation and integration techniques, applications to curves, maxima and minima problems, differential equations, and numerical methods.",
            "grade_level": "12-13",
            "keywords": ["calculus", "A-Level", "differentiation", "integration", "Cambridge"],
        },
    ]

    # Science materials
    science_materials = [
        {
            "title": "Cambridge IGCSE Biology - Cell Structure and Organization",
            "subject": "Biology",
            "level": "IGCSE",
            "description": "Detailed study of cell structure, specialization, and organization in living organisms.",
            "content": "Covers prokaryotic and eukaryotic cells, cell organelles and their functions, cell specialization, levels of organization from cells to organisms, and practical microscopy techniques.",
            "grade_level": "9-10",
            "keywords": ["biology", "cells", "IGCSE", "organisms", "Cambridge"],
        },
        {
            "title": "Cambridge IGCSE Chemistry - Atomic Structure and Bonding",
            "subject": "Chemistry",
            "level": "IGCSE",
            "description": "Foundation chemistry concepts about atoms, elements, and chemical bonding.",
            "content": "Atomic structure, periodic table, electron configuration, ionic bonding, covalent bonding, metallic bonding, and properties of compounds.",
            "grade_level": "9-10",
            "keywords": ["chemistry", "atoms", "bonding", "IGCSE", "Cambridge"],
        },
        {
            "title": "Cambridge IGCSE Physics - Forces and Motion",
            "subject": "Physics",
            "level": "IGCSE",
            "description": "Study of forces, motion, and their effects on objects.",
            "content": "Newton's laws of motion, speed and velocity, acceleration, mass and weight, momentum, energy conservation, and work done.",
            "grade_level": "9-10",
            "keywords": ["physics", "forces", "motion", "IGCSE", "Cambridge"],
        },
    ]

    # Language materials
    language_materials = [
        {
            "title": "Cambridge IGCSE English Language - Reading Comprehension",
            "subject": "English Language",
            "level": "IGCSE",
            "description": "Advanced reading strategies and comprehension techniques for Cambridge examinations.",
            "content": "Analyzing fiction and non-fiction texts, identifying main ideas and supporting details, understanding writer's techniques, making inferences, and responding to reading passages.",
            "grade_level": "9-10",
            "keywords": ["English", "reading", "comprehension", "IGCSE", "Cambridge"],
        },
        {
            "title": "Cambridge Primary English - Creative Writing",
            "subject": "English Language",
            "level": "Primary",
            "description": "Developing creative writing skills for primary students.",
            "content": "Story structures, character development, descriptive language, dialogue writing, and editing techniques.",
            "grade_level": "4-6",
            "keywords": ["English", "writing", "creative", "primary", "Cambridge"],
        },
        {
            "title": "Cambridge IGCSE Literature - Poetry Analysis",
            "subject": "Literature",
            "level": "IGCSE",
            "description": "Techniques for analyzing and responding to poetry.",
            "content": "Poetic devices, themes, structure, context, comparative analysis, and essay writing skills.",
            "grade_level": "9-10",
            "keywords": ["literature", "poetry", "analysis", "IGCSE", "Cambridge"],
        },
    ]

    # Social Studies materials
    social_studies_materials = [
        {
            "title": "Cambridge IGCSE Geography - Physical Geography",
            "subject": "Geography",
            "level": "IGCSE",
            "description": "Study of physical geographical processes and landforms.",
            "content": "Plate tectonics, weathering and erosion, rivers and coasts, weather and climate, and ecosystems.",
            "grade_level": "9-10",
            "keywords": ["geography", "physical", "landforms", "IGCSE", "Cambridge"],
        },
        {
            "title": "Cambridge IGCSE History - World War II",
            "subject": "History",
            "level": "IGCSE",
            "description": "Comprehensive study of World War II causes, events, and consequences.",
            "content": "Origins of the war, major battles and campaigns, Holocaust, home fronts, and post-war settlement.",
            "grade_level": "9-10",
            "keywords": ["history", "WWII", "warfare", "IGCSE", "Cambridge"],
        },
    ]

    # ICT materials
    ict_materials = [
        {
            "title": "Cambridge IGCSE Computer Science - Programming Fundamentals",
            "subject": "Computer Science",
            "level": "IGCSE",
            "description": "Introduction to programming concepts and Python language.",
            "content": "Variables, data types, operators, conditional statements, loops, functions, and basic algorithms.",
            "grade_level": "9-10",
            "keywords": ["computer science", "programming", "Python", "IGCSE", "Cambridge"],
        },
    ]

    all_materials = (math_materials + science_materials + language_materials +
                    social_studies_materials + ict_materials)

    for mat_data in all_materials:
        material = {
            "material_id": str(ObjectId()),
            "title": mat_data["title"],
            "subject": mat_data["subject"],
            "level": mat_data["level"],
            "description": mat_data["description"],
            "content": mat_data["content"],
            "grade_level": mat_data["grade_level"],
            "keywords": mat_data["keywords"],
            "school": "Shield International School",
            "curriculum": "Cambridge International",
            "file_path": f"/materials/{mat_data['subject'].lower().replace(' ', '_')}_{ObjectId()}.pdf",
            "file_type": "pdf",
            "file_size": random.randint(500000, 5000000),
            "uploaded_by": "admin@shield.edu.gh",
            "upload_date": datetime.utcnow() - timedelta(days=random.randint(1, 90)),
            "status": "processed",
            "downloads": random.randint(5, 150),
            "views": random.randint(20, 500),
        }
        materials.append(material)
        await db.materials.insert_one(material)

    print(f"✅ Created {len(materials)} study materials")

    # Create study sessions
    print("\n📖 Creating study sessions...")
    sessions = []

    for _ in range(50):  # Create 50 study sessions
        student = random.choice(students)
        material = random.choice(materials)

        start_time = datetime.utcnow() - timedelta(days=random.randint(0, 30))
        duration = random.randint(15, 120)  # 15 to 120 minutes

        session = {
            "session_id": str(ObjectId()),
            "user_id": student["user_id"],
            "material_id": material["material_id"],
            "start_time": start_time,
            "end_time": start_time + timedelta(minutes=duration),
            "duration_minutes": duration,
            "progress": random.randint(0, 100),
            "completed": random.choice([True, False]),
            "notes": f"Studying {material['subject']} - {material['level']}",
        }
        sessions.append(session)
        await db.study_sessions.insert_one(session)

    print(f"✅ Created {len(sessions)} study sessions")

    # Create questions/interactions
    print("\n❓ Creating questions and interactions...")
    questions = []

    sample_questions = [
        "Can you explain the difference between mitosis and meiosis?",
        "How do I solve quadratic equations using the formula?",
        "What are the main themes in Shakespeare's Macbeth?",
        "What caused World War I?",
        "How does photosynthesis work?",
        "Can you help me understand Pythagoras' theorem?",
        "What is the structure of an atom?",
        "How do I write a persuasive essay?",
        "What is the water cycle?",
        "Can you explain Newton's laws of motion?",
    ]

    for _ in range(100):  # Create 100 questions
        student = random.choice(students)
        material = random.choice(materials)

        question = {
            "question_id": str(ObjectId()),
            "user_id": student["user_id"],
            "material_id": material["material_id"],
            "question_text": random.choice(sample_questions),
            "answer_text": "Detailed answer would be provided by the AI tutor based on the study material context.",
            "confidence_score": random.uniform(0.7, 0.99),
            "timestamp": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            "helpful": random.choice([True, False, None]),
        }
        questions.append(question)
        await db.questions.insert_one(question)

    print(f"✅ Created {len(questions)} questions")

    # Summary
    print("\n" + "="*60)
    print("✅ Shield International School Data Population Complete!")
    print("="*60)
    print(f"👥 Students: {len(students)}")
    print(f"📚 Study Materials: {len(materials)}")
    print(f"📖 Study Sessions: {len(sessions)}")
    print(f"❓ Questions: {len(questions)}")
    print("\n🎓 School: Shield International School, Adenta, Ghana")
    print("🌍 Curriculum: Cambridge International Education")
    print("📧 Contact: info@shield.edu.gh | 0550011122")
    print("="*60)

    client.close()

if __name__ == "__main__":
    asyncio.run(populate_shield_data())
