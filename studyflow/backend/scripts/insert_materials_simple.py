#!/usr/bin/env python3
"""
Simple script to insert existing PDF materials into MongoDB.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from pymongo import MongoClient

# MongoDB connection
MONGODB_URI = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/studyflow?authSource=admin"

# Shield School ID
SHIELD_SCHOOL_ID = "68fbb76cf8e6506f864e8214"

# Storage path
STORAGE_PATH = Path("/opt/kasaai/apps/studyflow/storage/materials")

# Materials metadata
MATERIALS_META = {
    # Math - Primary
    "math_grade2_addition_and_subtraction.pdf": {
        "title": "Addition and Subtraction",
        "subject": "Mathematics",
        "grade": 2,
        "topics": ["addition", "subtraction", "basic arithmetic"],
        "description": "Learn fun ways to add and subtract numbers! Practice with colorful examples and exercises."
    },
    "math_grade3_multiplication_tables.pdf": {
        "title": "Multiplication Tables",
        "subject": "Mathematics",
        "grade": 3,
        "topics": ["multiplication", "times tables", "division"],
        "description": "Master multiplication with times tables and discover patterns! Make math fun and easy."
    },
    "math_grade4_fractions_and_decimals.pdf": {
        "title": "Fractions and Decimals",
        "subject": "Mathematics",
        "grade": 4,
        "topics": ["fractions", "decimals", "number sense"],
        "description": "Understanding fractions and decimals made simple with visual examples and practice."
    },
    "math_grade5_geometry_shapes.pdf": {
        "title": "Geometry Shapes",
        "subject": "Mathematics",
        "grade": 5,
        "topics": ["shapes", "angles", "measurement"],
        "description": "Explore the world of shapes, angles, and measurements through fun activities."
    },
    "math_grade6_percentages_and_ratios.pdf": {
        "title": "Percentages and Ratios",
        "subject": "Mathematics",
        "grade": 6,
        "topics": ["percentages", "ratios", "proportion"],
        "description": "Learn about percentages and ratios with real-world examples and applications."
    },

    # Math - Secondary
    "math_grade7_introduction_to_algebra.pdf": {
        "title": "Introduction to Algebra",
        "subject": "Mathematics",
        "grade": 7,
        "topics": ["algebra", "variables", "equations"],
        "description": "Begin your algebra journey! Learn to solve equations and work with variables."
    },
    "math_grade8_linear_equations.pdf": {
        "title": "Linear Equations",
        "subject": "Mathematics",
        "grade": 8,
        "topics": ["equations", "graphing", "linear functions"],
        "description": "Master linear equations and graphing techniques step by step."
    },
    "math_grade9_quadratic_equations.pdf": {
        "title": "Quadratic Equations",
        "subject": "Mathematics",
        "grade": 9,
        "topics": ["quadratics", "factoring", "parabolas"],
        "description": "Solve quadratic equations using multiple methods including factoring and the quadratic formula."
    },
    "math_grade10_trigonometry_basics.pdf": {
        "title": "Trigonometry Basics",
        "subject": "Mathematics",
        "grade": 10,
        "topics": ["trigonometry", "sine", "cosine", "tangent"],
        "description": "Introduction to trigonometric ratios and their applications in real-world problems."
    },
    "math_grade11_calculus_introduction.pdf": {
        "title": "Calculus Introduction",
        "subject": "Mathematics",
        "grade": 11,
        "topics": ["calculus", "derivatives", "limits"],
        "description": "Begin your calculus journey with limits, derivatives, and rates of change."
    },
    "math_grade12_advanced_calculus.pdf": {
        "title": "Advanced Calculus",
        "subject": "Mathematics",
        "grade": 12,
        "topics": ["integration", "differential equations"],
        "description": "Advanced calculus topics including integration techniques and differential equations."
    },

    # Science
    "science_grade2_plants_and_animals.pdf": {
        "title": "Plants and Animals",
        "subject": "Science",
        "grade": 2,
        "topics": ["plants", "animals", "living things"],
        "description": "Discover the amazing world of plants and animals and how they live and grow!"
    },
    "science_grade3_the_solar_system.pdf": {
        "title": "The Solar System",
        "subject": "Science",
        "grade": 3,
        "topics": ["planets", "space", "astronomy"],
        "description": "Take a journey through our solar system! Learn about planets, stars, and space."
    },
    "science_grade4_states_of_matter.pdf": {
        "title": "States of Matter",
        "subject": "Science",
        "grade": 4,
        "topics": ["solid", "liquid", "gas", "matter"],
        "description": "Explore the three states of matter and how they change from one to another."
    },
    "science_grade5_human_body_systems.pdf": {
        "title": "Human Body Systems",
        "subject": "Science",
        "grade": 5,
        "topics": ["body", "organs", "health"],
        "description": "Learn about the amazing systems in your body and how they work together."
    },
    "science_grade6_energy_and_forces.pdf": {
        "title": "Energy and Forces",
        "subject": "Science",
        "grade": 6,
        "topics": ["energy", "forces", "motion"],
        "description": "Understand energy, forces, and motion through experiments and examples."
    },
    "science_grade7_cell_biology.pdf": {
        "title": "Cell Biology",
        "subject": "Science",
        "grade": 7,
        "topics": ["cells", "biology", "microscopy"],
        "description": "Discover the building blocks of life! Learn about cells and their functions."
    },
    "science_grade8_chemical_reactions.pdf": {
        "title": "Chemical Reactions",
        "subject": "Science",
        "grade": 8,
        "topics": ["chemistry", "reactions", "elements"],
        "description": "Explore chemical reactions and how elements combine to form new substances."
    },
    "science_grade9_physics_-_motion.pdf": {
        "title": "Physics - Motion",
        "subject": "Science",
        "grade": 9,
        "topics": ["physics", "motion", "velocity"],
        "description": "Study the laws of motion and understand how objects move."
    },
    "science_grade10_genetics_and_dna.pdf": {
        "title": "Genetics and DNA",
        "subject": "Science",
        "grade": 10,
        "topics": ["genetics", "DNA", "heredity"],
        "description": "Unlock the secrets of heredity and DNA! Learn how traits are passed down."
    },
    "science_grade11_organic_chemistry.pdf": {
        "title": "Organic Chemistry",
        "subject": "Science",
        "grade": 11,
        "topics": ["chemistry", "organic compounds", "carbon"],
        "description": "Introduction to organic chemistry and the chemistry of carbon compounds."
    },
    "science_grade12_advanced_physics.pdf": {
        "title": "Advanced Physics",
        "subject": "Science",
        "grade": 12,
        "topics": ["physics", "quantum", "relativity"],
        "description": "Advanced physics concepts including quantum mechanics and relativity."
    },

    # English
    "english_grade2_phonics_and_reading.pdf": {
        "title": "Phonics and Reading",
        "subject": "English",
        "grade": 2,
        "topics": ["phonics", "reading", "spelling"],
        "description": "Build reading skills with phonics! Learn letter sounds and how to read words."
    },
    "english_grade3_grammar_basics.pdf": {
        "title": "Grammar Basics",
        "subject": "English",
        "grade": 3,
        "topics": ["grammar", "nouns", "verbs"],
        "description": "Master the building blocks of English grammar with fun examples."
    },
    "english_grade4_creative_writing.pdf": {
        "title": "Creative Writing",
        "subject": "English",
        "grade": 4,
        "topics": ["writing", "stories", "composition"],
        "description": "Unleash your creativity! Learn to write amazing stories and compositions."
    },
    "english_grade5_reading_comprehension.pdf": {
        "title": "Reading Comprehension",
        "subject": "English",
        "grade": 5,
        "topics": ["reading", "comprehension", "analysis"],
        "description": "Improve your reading comprehension skills and understand what you read."
    },
    "english_grade6_poetry_and_rhymes.pdf": {
        "title": "Poetry and Rhymes",
        "subject": "English",
        "grade": 6,
        "topics": ["poetry", "rhyme", "verse"],
        "description": "Explore the beautiful world of poetry and learn to write your own poems!"
    },
    "english_grade7_essay_writing.pdf": {
        "title": "Essay Writing",
        "subject": "English",
        "grade": 7,
        "topics": ["essay", "writing", "composition"],
        "description": "Learn to write clear, structured essays that express your ideas effectively."
    },
    "english_grade8_literature_analysis.pdf": {
        "title": "Literature Analysis",
        "subject": "English",
        "grade": 8,
        "topics": ["literature", "analysis", "themes"],
        "description": "Analyze literary works and understand themes, characters, and plot."
    },
    "english_grade9_shakespeare_studies.pdf": {
        "title": "Shakespeare Studies",
        "subject": "English",
        "grade": 9,
        "topics": ["Shakespeare", "drama", "literature"],
        "description": "Discover the timeless works of William Shakespeare and their enduring impact."
    },
    "english_grade10_argumentative_writing.pdf": {
        "title": "Argumentative Writing",
        "subject": "English",
        "grade": 10,
        "topics": ["argument", "persuasion", "debate"],
        "description": "Master the art of persuasive writing and build strong arguments."
    },
    "english_grade11_world_literature.pdf": {
        "title": "World Literature",
        "subject": "English",
        "grade": 11,
        "topics": ["literature", "global", "classics"],
        "description": "Explore literary works from around the world and different cultures."
    },
    "english_grade12_advanced_composition.pdf": {
        "title": "Advanced Composition",
        "subject": "English",
        "grade": 12,
        "topics": ["composition", "rhetoric", "style"],
        "description": "Advanced composition techniques for academic and professional writing."
    },

    # Other subjects (using math PDFs as placeholders - they were generated)
    "math_grade7_ancient_ghana_empire.pdf": {
        "title": "Ancient Ghana Empire",
        "subject": "History",
        "grade": 7,
        "topics": ["history", "Ghana", "empire", "Africa"],
        "description": "Explore the rich history of the Ancient Ghana Empire and West African civilizations."
    },
    "math_grade9_world_war_ii.pdf": {
        "title": "World War II",
        "subject": "History",
        "grade": 9,
        "topics": ["history", "WWII", "war", "conflict"],
        "description": "Study the causes, events, and consequences of World War II."
    },
    "math_grade8_african_geography.pdf": {
        "title": "African Geography",
        "subject": "Geography",
        "grade": 8,
        "topics": ["geography", "Africa", "maps"],
        "description": "Discover Africa's diverse geography, from deserts to rainforests."
    },
    "math_grade10_climate_and_weather.pdf": {
        "title": "Climate and Weather",
        "subject": "Geography",
        "grade": 10,
        "topics": ["climate", "weather", "environment"],
        "description": "Understand climate patterns and weather systems around the world."
    },
    "math_grade9_introduction_to_programming.pdf": {
        "title": "Introduction to Programming",
        "subject": "Computer Science",
        "grade": 9,
        "topics": ["programming", "coding", "Python"],
        "description": "Begin your coding journey! Learn programming basics with Python."
    },
    "math_grade11_web_development.pdf": {
        "title": "Web Development",
        "subject": "Computer Science",
        "grade": 11,
        "topics": ["HTML", "CSS", "JavaScript", "web"],
        "description": "Create websites! Learn HTML, CSS, and JavaScript for web development."
    },
    "math_grade7_basic_french_vocabulary.pdf": {
        "title": "Basic French Vocabulary",
        "subject": "French",
        "grade": 7,
        "topics": ["French", "vocabulary", "language"],
        "description": "Start learning French! Master essential vocabulary and phrases."
    },
    "math_grade9_french_grammar.pdf": {
        "title": "French Grammar",
        "subject": "French",
        "grade": 9,
        "topics": ["French", "grammar", "verbs"],
        "description": "Learn French grammar rules and verb conjugations."
    },
    "math_grade6_color_theory.pdf": {
        "title": "Color Theory",
        "subject": "Art",
        "grade": 6,
        "topics": ["art", "colors", "painting"],
        "description": "Discover how colors work together! Learn color theory for amazing artwork."
    },
    "math_grade8_drawing_techniques.pdf": {
        "title": "Drawing Techniques",
        "subject": "Art",
        "grade": 8,
        "topics": ["art", "drawing", "sketching"],
        "description": "Improve your drawing skills with professional techniques."
    },
    "math_grade5_music_notes_and_rhythm.pdf": {
        "title": "Music Notes and Rhythm",
        "subject": "Music",
        "grade": 5,
        "topics": ["music", "notes", "rhythm"],
        "description": "Learn to read music! Understand notes, rhythm, and musical notation."
    },
    "math_grade7_sports_and_fitness.pdf": {
        "title": "Sports and Fitness",
        "subject": "Physical Education",
        "grade": 7,
        "topics": ["sports", "fitness", "health"],
        "description": "Stay active and healthy! Learn about fitness, sports, and wellness."
    },
}


def main():
    print("🎨 Inserting materials into StudyFlow database...")
    print("=" * 80)

    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client['studyflow']
    collection = db['learning_materials']

    inserted_count = 0
    skipped_count = 0

    # Process each file
    for filename in STORAGE_PATH.glob("*.pdf"):
        try:
            if filename.name not in MATERIALS_META:
                print(f"⚠️  Skipping {filename.name} - no metadata")
                skipped_count += 1
                continue

            meta = MATERIALS_META[filename.name]

            # Check if material already exists
            existing = collection.find_one({
                "title": meta["title"],
                "school_id": SHIELD_SCHOOL_ID,
                "grade": meta["grade"]
            })

            if existing:
                print(f"⏭️  Skipping {meta['title']} Grade {meta['grade']} - already exists")
                skipped_count += 1
                continue

            # Get file info
            file_size = filename.stat().st_size

            # Create material document
            material_doc = {
                "title": meta["title"],
                "description": meta["description"],
                "file_name": filename.name,
                "file_path": str(filename),
                "file_size": file_size,
                "file_type": "application/pdf",
                "subject": meta["subject"],
                "topics": meta["topics"],
                "grade": meta["grade"],
                "school_id": SHIELD_SCHOOL_ID,
                "uploaded_by": "shield-admin",
                "status": "completed",
                "chunks_count": 0,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "processed_at": datetime.now(timezone.utc)
            }

            # Insert into database
            result = collection.insert_one(material_doc)

            inserted_count += 1
            print(f"✅ {meta['subject']} Grade {meta['grade']}: {meta['title']}")
            print(f"   📄 File: {filename.name} ({file_size / 1024:.1f} KB)")

        except Exception as e:
            print(f"❌ Error inserting {filename.name}: {str(e)}")
            skipped_count += 1

    client.close()

    print("\n" + "=" * 80)
    print(f"🎉 Successfully inserted {inserted_count} materials!")
    print(f"⏭️  Skipped {skipped_count} materials")
    print(f"\n✨ Shield International School's StudyFlow is now full of content!")


if __name__ == "__main__":
    main()
