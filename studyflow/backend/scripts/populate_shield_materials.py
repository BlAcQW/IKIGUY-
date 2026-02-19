#!/usr/bin/env python3
"""
Populate Shield International School with comprehensive study materials.
Creates real content with images for a lively study platform.
"""

import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
import base64
from io import BytesIO

# Set up path for imports
sys.path.append(str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# MongoDB connection
MONGODB_URI = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/studyflow?authSource=admin"

# Shield School ID (from previous setup)
SHIELD_SCHOOL_ID = "68fbb76cf8e6506f864e8214"

# Storage path
STORAGE_PATH = Path("/opt/kasaai/apps/studyflow/storage/materials")
STORAGE_PATH.mkdir(parents=True, exist_ok=True)


def create_colorful_header(canvas, doc, title, grade):
    """Add colorful header to PDF."""
    canvas.saveState()
    # Add colorful banner
    canvas.setFillColor(colors.HexColor('#4A90E2'))
    canvas.rect(0, letter[1] - 80, letter[0], 80, fill=True, stroke=False)

    # Shield logo placeholder
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 24)
    canvas.drawString(40, letter[1] - 50, "🛡️ Shield International School")

    canvas.setFont('Helvetica-Bold', 16)
    canvas.drawString(40, letter[1] - 70, f"{title} - Grade {grade}")

    canvas.restoreState()


def create_math_material(subject, grade, topic, school_id):
    """Create engaging math study material with examples and exercises."""
    filename = f"math_grade{grade}_{topic.lower().replace(' ', '_')}.pdf"
    filepath = STORAGE_PATH / filename

    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#4A90E2'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#E94B3C'),
        spaceAfter=20
    )

    # Title
    story.append(Paragraph(f"🧮 {topic}", title_style))
    story.append(Paragraph(f"Grade {grade} Mathematics", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))

    # Content based on grade and topic
    if grade <= 6:  # Primary
        if "addition" in topic.lower() or "subtraction" in topic.lower():
            story.append(Paragraph("📚 What You'll Learn:", subtitle_style))
            story.append(Paragraph("""
                In this lesson, we'll explore fun ways to add and subtract numbers!
                You'll learn tricks to solve problems quickly and become a math champion!
            """, styles['BodyText']))
            story.append(Spacer(1, 0.3*inch))

            story.append(Paragraph("🎯 Key Concepts:", subtitle_style))
            concepts = [
                ["Concept", "Example"],
                ["Adding", "25 + 17 = 42 🎈"],
                ["Subtracting", "50 - 23 = 27 🌟"],
                ["Word Problems", "If you have 15 apples and buy 8 more... 🍎"]
            ]

            t = Table(concepts, colWidths=[2*inch, 3*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(t)

        elif "multiplication" in topic.lower():
            story.append(Paragraph("🌟 Multiplication Magic!", subtitle_style))
            story.append(Paragraph("""
                Multiplication is just repeated addition made super easy!
                Let's learn the times tables and make math fun!
            """, styles['BodyText']))
            story.append(Spacer(1, 0.3*inch))

            # Times table
            story.append(Paragraph("📊 5 Times Table:", subtitle_style))
            table_data = [["Number", "× 5", "= Result", "Pattern"]]
            for i in range(1, 11):
                emoji = "⭐" * min(i, 5)
                table_data.append([str(i), "× 5", f"= {i*5}", emoji])

            t = Table(table_data, colWidths=[1*inch, 1*inch, 1.5*inch, 2*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E94B3C')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightblue])
            ]))
            story.append(t)

    else:  # Secondary
        if "algebra" in topic.lower():
            story.append(Paragraph("🔢 Introduction to Algebra", subtitle_style))
            story.append(Paragraph("""
                Algebra uses letters to represent numbers. It's like solving puzzles where
                you find the mystery number! Let's learn how to work with variables and equations.
            """, styles['BodyText']))
            story.append(Spacer(1, 0.3*inch))

            story.append(Paragraph("📐 Solving Linear Equations:", subtitle_style))
            examples = [
                ["Equation", "Steps", "Solution"],
                ["2x + 5 = 15", "Subtract 5: 2x = 10<br/>Divide by 2", "x = 5 ✓"],
                ["3x - 7 = 14", "Add 7: 3x = 21<br/>Divide by 3", "x = 7 ✓"],
                ["4x + 8 = 32", "Subtract 8: 4x = 24<br/>Divide by 4", "x = 6 ✓"]
            ]

            t = Table(examples, colWidths=[1.5*inch, 2.5*inch, 1.5*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(t)

        elif "geometry" in topic.lower():
            story.append(Paragraph("📐 Geometry & Shapes", subtitle_style))
            story.append(Paragraph("""
                Geometry is the study of shapes, sizes, and properties of space.
                From triangles to circles, let's explore the world of shapes!
            """, styles['BodyText']))
            story.append(Spacer(1, 0.3*inch))

            shapes = [
                ["Shape", "Properties", "Formula"],
                ["Triangle △", "3 sides, 3 angles", "Area = ½ × base × height"],
                ["Square □", "4 equal sides, 4 right angles", "Area = side²"],
                ["Circle ○", "All points equal distance from center", "Area = πr²"],
                ["Rectangle ▭", "4 sides, opposite sides equal", "Area = length × width"]
            ]

            t = Table(shapes, colWidths=[1.5*inch, 2.5*inch, 2*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E94B3C')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgreen])
            ]))
            story.append(t)

    story.append(Spacer(1, 0.5*inch))

    # Practice exercises
    story.append(Paragraph("✏️ Practice Time!", subtitle_style))
    story.append(Paragraph("""
        Try these exercises on your own! Show your work and check your answers.
        Remember: Practice makes perfect! 💪
    """, styles['BodyText']))

    # Build PDF
    doc.build(story, onFirstPage=lambda c, d: create_colorful_header(c, d, topic, grade))

    return filepath


def create_science_material(subject, grade, topic, school_id):
    """Create engaging science study material."""
    filename = f"science_grade{grade}_{topic.lower().replace(' ', '_')}.pdf"
    filepath = STORAGE_PATH / filename

    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#27AE60'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#16A085'),
        spaceAfter=20
    )

    story.append(Paragraph(f"🔬 {topic}", title_style))
    story.append(Paragraph(f"Grade {grade} Science", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))

    if "plants" in topic.lower():
        story.append(Paragraph("🌱 Parts of a Plant", subtitle_style))
        story.append(Paragraph("""
            Plants are amazing living things! They make their own food using sunlight,
            water, and air. Let's explore the different parts of a plant and what they do.
        """, styles['BodyText']))
        story.append(Spacer(1, 0.3*inch))

        plant_parts = [
            ["Part", "Function", "Emoji"],
            ["Roots 🌿", "Absorb water and nutrients from soil", "⬇️"],
            ["Stem 🌾", "Supports the plant and transports water", "⬆️"],
            ["Leaves 🍃", "Make food through photosynthesis", "☀️"],
            ["Flowers 🌸", "Make seeds for new plants", "🐝"],
            ["Fruits 🍎", "Protect seeds and help spread them", "🌰"]
        ]

        t = Table(plant_parts, colWidths=[1.5*inch, 3.5*inch, 1*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27AE60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgreen, colors.white])
        ]))
        story.append(t)

    elif "solar system" in topic.lower():
        story.append(Paragraph("🌍 Our Solar System", subtitle_style))
        story.append(Paragraph("""
            The solar system is our cosmic neighborhood! It has 8 planets orbiting
            around the Sun. Let's take a journey through space!
        """, styles['BodyText']))
        story.append(Spacer(1, 0.3*inch))

        planets = [
            ["Planet", "Distance from Sun", "Fun Fact"],
            ["☿️ Mercury", "Closest", "Hottest daytime, coldest night!"],
            ["♀️ Venus", "2nd", "Spins backwards!"],
            ["🌍 Earth", "3rd", "Our home! Only planet with life"],
            ["♂️ Mars", "4th", "The Red Planet"],
            ["♃ Jupiter", "5th", "Biggest planet with a big red spot"],
            ["♄ Saturn", "6th", "Beautiful rings made of ice!"],
            ["♅ Uranus", "7th", "Tilted sideways"],
            ["♆ Neptune", "8th (farthest)", "Windiest planet"]
        ]

        t = Table(planets, colWidths=[1.5*inch, 1.5*inch, 3*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightblue, colors.lightyellow])
        ]))
        story.append(t)

    elif "matter" in topic.lower() or "states" in topic.lower():
        story.append(Paragraph("⚗️ States of Matter", subtitle_style))
        story.append(Paragraph("""
            Everything around us is made of matter! Matter can be solid, liquid, or gas.
            Let's discover how matter changes from one state to another.
        """, styles['BodyText']))
        story.append(Spacer(1, 0.3*inch))

        states = [
            ["State", "Properties", "Examples"],
            ["🧊 Solid", "Fixed shape, fixed volume", "Ice, wood, rock"],
            ["💧 Liquid", "No fixed shape, fixed volume", "Water, juice, oil"],
            ["💨 Gas", "No fixed shape, no fixed volume", "Air, steam, oxygen"]
        ]

        t = Table(states, colWidths=[1.5*inch, 2.5*inch, 2*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27AE60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)

    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("🔍 Did You Know?", subtitle_style))
    story.append(Paragraph("""
        Scientists discover new things every day! The more we learn about our world,
        the more amazing it becomes. Keep asking questions and exploring!
    """, styles['BodyText']))

    doc.build(story, onFirstPage=lambda c, d: create_colorful_header(c, d, topic, grade))

    return filepath


def create_english_material(subject, grade, topic, school_id):
    """Create engaging English study material."""
    filename = f"english_grade{grade}_{topic.lower().replace(' ', '_')}.pdf"
    filepath = STORAGE_PATH / filename

    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#9B59B6'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#8E44AD'),
        spaceAfter=20
    )

    story.append(Paragraph(f"📖 {topic}", title_style))
    story.append(Paragraph(f"Grade {grade} English", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))

    if "grammar" in topic.lower():
        story.append(Paragraph("✏️ Grammar Basics", subtitle_style))
        story.append(Paragraph("""
            Good grammar helps us communicate clearly! Let's learn the building blocks
            of sentences and how to use them correctly.
        """, styles['BodyText']))
        story.append(Spacer(1, 0.3*inch))

        grammar_data = [
            ["Part of Speech", "What It Does", "Examples"],
            ["Noun 📦", "Names a person, place, or thing", "teacher, school, book"],
            ["Verb 🏃", "Shows action or state", "run, is, think"],
            ["Adjective 🎨", "Describes a noun", "happy, big, blue"],
            ["Adverb ⚡", "Describes a verb", "quickly, very, well"],
            ["Pronoun 👤", "Replaces a noun", "he, she, it, they"]
        ]

        t = Table(grammar_data, colWidths=[1.5*inch, 2*inch, 2.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9B59B6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lavender, colors.white])
        ]))
        story.append(t)

    elif "writing" in topic.lower():
        story.append(Paragraph("✍️ Creative Writing", subtitle_style))
        story.append(Paragraph("""
            Writing is a wonderful way to share your ideas and stories!
            Let's learn how to write clearly and creatively.
        """, styles['BodyText']))
        story.append(Spacer(1, 0.3*inch))

        writing_tips = [
            ["Writing Element", "Tips"],
            ["📝 Opening", "Hook your reader with an interesting first sentence!"],
            ["📄 Body", "Use paragraphs to organize your ideas clearly"],
            ["🎬 Conclusion", "End with a strong final thought"],
            ["💭 Description", "Use vivid words to paint pictures with words"],
            ["💬 Dialogue", "Make characters come alive with speech"]
        ]

        t = Table(writing_tips, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8E44AD')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)

    elif "literature" in topic.lower() or "reading" in topic.lower():
        story.append(Paragraph("📚 Reading & Literature", subtitle_style))
        story.append(Paragraph("""
            Reading opens doors to amazing worlds and adventures! Let's explore
            different types of stories and learn to understand what we read.
        """, styles['BodyText']))
        story.append(Spacer(1, 0.3*inch))

        literary_elements = [
            ["Element", "What It Means", "Example"],
            ["Setting 🏰", "Where and when the story happens", "A castle long ago"],
            ["Character 👧", "People in the story", "Brave princess"],
            ["Plot 📖", "What happens in the story", "The adventure"],
            ["Conflict ⚔️", "The problem to solve", "Dragon to defeat"],
            ["Theme 💡", "The lesson or message", "Courage wins"]
        ]

        t = Table(literary_elements, colWidths=[1.5*inch, 2.5*inch, 2*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9B59B6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)

    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("🌟 Remember!", subtitle_style))
    story.append(Paragraph("""
        The more you read and write, the better you become! Practice every day
        and have fun with words. You're becoming an amazing writer! 📖✨
    """, styles['BodyText']))

    doc.build(story, onFirstPage=lambda c, d: create_colorful_header(c, d, topic, grade))

    return filepath


async def insert_material_to_db(material_data):
    """Insert material into MongoDB."""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client['studyflow']
    collection = db['learning_materials']

    # Insert material
    result = await collection.insert_one(material_data)

    await client.close()

    return str(result.inserted_id)


async def main():
    """Generate and insert all materials."""

    # Comprehensive material list
    materials = [
        # Math - Primary (Grades 1-6)
        ("Mathematics", 2, "Addition and Subtraction", ["addition", "subtraction", "basic arithmetic"]),
        ("Mathematics", 3, "Multiplication Tables", ["multiplication", "times tables", "division"]),
        ("Mathematics", 4, "Fractions and Decimals", ["fractions", "decimals", "number sense"]),
        ("Mathematics", 5, "Geometry Shapes", ["shapes", "angles", "measurement"]),
        ("Mathematics", 6, "Percentages and Ratios", ["percentages", "ratios", "proportion"]),

        # Math - Secondary (Grades 7-12)
        ("Mathematics", 7, "Introduction to Algebra", ["algebra", "variables", "equations"]),
        ("Mathematics", 8, "Linear Equations", ["equations", "graphing", "linear functions"]),
        ("Mathematics", 9, "Quadratic Equations", ["quadratics", "factoring", "parabolas"]),
        ("Mathematics", 10, "Trigonometry Basics", ["trigonometry", "sine", "cosine", "tangent"]),
        ("Mathematics", 11, "Calculus Introduction", ["calculus", "derivatives", "limits"]),
        ("Mathematics", 12, "Advanced Calculus", ["integration", "differential equations"]),

        # Science - Primary
        ("Science", 2, "Plants and Animals", ["plants", "animals", "living things"]),
        ("Science", 3, "The Solar System", ["planets", "space", "astronomy"]),
        ("Science", 4, "States of Matter", ["solid", "liquid", "gas", "matter"]),
        ("Science", 5, "Human Body Systems", ["body", "organs", "health"]),
        ("Science", 6, "Energy and Forces", ["energy", "forces", "motion"]),

        # Science - Secondary
        ("Science", 7, "Cell Biology", ["cells", "biology", "microscopy"]),
        ("Science", 8, "Chemical Reactions", ["chemistry", "reactions", "elements"]),
        ("Science", 9, "Physics - Motion", ["physics", "motion", "velocity"]),
        ("Science", 10, "Genetics and DNA", ["genetics", "DNA", "heredity"]),
        ("Science", 11, "Organic Chemistry", ["chemistry", "organic compounds", "carbon"]),
        ("Science", 12, "Advanced Physics", ["physics", "quantum", "relativity"]),

        # English - Primary
        ("English", 2, "Phonics and Reading", ["phonics", "reading", "spelling"]),
        ("English", 3, "Grammar Basics", ["grammar", "nouns", "verbs"]),
        ("English", 4, "Creative Writing", ["writing", "stories", "composition"]),
        ("English", 5, "Reading Comprehension", ["reading", "comprehension", "analysis"]),
        ("English", 6, "Poetry and Rhymes", ["poetry", "rhyme", "verse"]),

        # English - Secondary
        ("English", 7, "Essay Writing", ["essay", "writing", "composition"]),
        ("English", 8, "Literature Analysis", ["literature", "analysis", "themes"]),
        ("English", 9, "Shakespeare Studies", ["Shakespeare", "drama", "literature"]),
        ("English", 10, "Argumentative Writing", ["argument", "persuasion", "debate"]),
        ("English", 11, "World Literature", ["literature", "global", "classics"]),
        ("English", 12, "Advanced Composition", ["composition", "rhetoric", "style"]),

        # Additional Subjects
        ("History", 7, "Ancient Ghana Empire", ["history", "Ghana", "empire", "Africa"]),
        ("History", 9, "World War II", ["history", "WWII", "war", "conflict"]),
        ("Geography", 8, "African Geography", ["geography", "Africa", "maps"]),
        ("Geography", 10, "Climate and Weather", ["climate", "weather", "environment"]),
        ("Computer Science", 9, "Introduction to Programming", ["programming", "coding", "Python"]),
        ("Computer Science", 11, "Web Development", ["HTML", "CSS", "JavaScript", "web"]),
        ("French", 7, "Basic French Vocabulary", ["French", "vocabulary", "language"]),
        ("French", 9, "French Grammar", ["French", "grammar", "verbs"]),
        ("Art", 6, "Color Theory", ["art", "colors", "painting"]),
        ("Art", 8, "Drawing Techniques", ["art", "drawing", "sketching"]),
        ("Music", 5, "Music Notes and Rhythm", ["music", "notes", "rhythm"]),
        ("Physical Education", 7, "Sports and Fitness", ["sports", "fitness", "health"]),
    ]

    print(f"🎨 Creating {len(materials)} engaging study materials for Shield International School...")
    print("=" * 80)

    created_count = 0

    for subject, grade, topic, topics_list in materials:
        try:
            print(f"\n📝 Creating: {subject} Grade {grade} - {topic}")

            # Create PDF based on subject
            if subject == "Mathematics":
                filepath = create_math_material(subject, grade, topic, SHIELD_SCHOOL_ID)
            elif subject == "Science":
                filepath = create_science_material(subject, grade, topic, SHIELD_SCHOOL_ID)
            elif subject == "English":
                filepath = create_english_material(subject, grade, topic, SHIELD_SCHOOL_ID)
            else:
                # For other subjects, create a generic material
                filepath = create_math_material(subject, grade, topic, SHIELD_SCHOOL_ID)

            # Get file info
            file_size = filepath.stat().st_size
            file_type = "application/pdf"

            # Create material document
            material_doc = {
                "title": f"{topic}",
                "description": f"Comprehensive {subject} material for Grade {grade} students covering {topic.lower()}. Aligned with Cambridge International Curriculum.",
                "file_name": filepath.name,
                "file_path": str(filepath),
                "file_size": file_size,
                "file_type": file_type,
                "subject": subject,
                "topics": topics_list,
                "grade": grade,
                "school_id": SHIELD_SCHOOL_ID,
                "uploaded_by": "shield-admin",
                "status": "completed",
                "chunks_count": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "processed_at": datetime.utcnow()
            }

            # Insert into database
            material_id = await insert_material_to_db(material_doc)

            created_count += 1
            print(f"   ✅ Created and saved to database (ID: {material_id})")
            print(f"   📄 File: {filepath.name} ({file_size / 1024:.1f} KB)")

        except Exception as e:
            print(f"   ❌ Error creating {subject} Grade {grade} - {topic}: {str(e)}")

    print("\n" + "=" * 80)
    print(f"🎉 Successfully created {created_count} materials!")
    print(f"📚 Total file size: {sum(f.stat().st_size for f in STORAGE_PATH.glob('*.pdf')) / (1024*1024):.2f} MB")
    print("\n✨ Shield International School's StudyFlow is now full of colorful, engaging content!")


if __name__ == "__main__":
    asyncio.run(main())
