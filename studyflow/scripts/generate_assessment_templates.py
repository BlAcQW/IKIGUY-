"""
Generate Assessment Templates for Onboarding Modules.

Creates pre-configured assessment templates with AI-generated questions
for modules 2-10.

Usage:
    PYTHONPATH=/opt/kasaai:/opt/kasaai/apps/studyflow/backend:/opt/kasaai/apps \
    MONGODB_URL="mongodb://admin:aawwER4444%25@127.0.0.1:27017/studyflow?authSource=admin" \
    GEMINI_API_KEY="AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4" \
    /opt/kasaai/apps/venv/bin/python3 generate_assessment_templates.py

Author: KasaAI
Created: 2025-11-07
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add paths
sys.path.insert(0, "/opt/kasaai")
sys.path.insert(0, "/opt/kasaai/apps")

from motor.motor_asyncio import AsyncIOMotorClient
import google.generativeai as genai

# Configuration
MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://admin:aawwER4444%25@127.0.0.1:27017/studyflow?authSource=admin"
)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4")

MODULES_DIR = "/opt/kasaai/apps/studyflow/storage/onboarding_modules"
ORGANIZATION_ID = "ai_labs_org_001"
COLLECTION_NAME = "ai_labs_org_001_developer_onboarding"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


class AssessmentTemplateGenerator:
    """Generate assessment templates for onboarding modules."""

    def __init__(self):
        """Initialize generator."""
        self.client = AsyncIOMotorClient(MONGODB_URL)
        self.db = self.client.get_database()
        self.collection = self.db["assessment_sessions"]
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print("✓ Generator initialized")

    async def generate_all_templates(self):
        """Generate templates for modules 2-10."""
        print("\n" + "=" * 70)
        print("🎯 GENERATING ASSESSMENT TEMPLATES")
        print("=" * 70)

        modules_dir = Path(MODULES_DIR)
        module_files = sorted(modules_dir.glob("module_*.md"))

        # Skip module 1 (already has template from setup script)
        module_files = [f for f in module_files if "module_01" not in f.name]

        templates_created = 0

        for module_file in module_files:
            print(f"\n📝 Processing: {module_file.name}")

            # Read module content
            with open(module_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract metadata
            metadata = self._extract_metadata(module_file.name, content)

            # Generate questions
            questions = await self._generate_questions(content, metadata)

            if questions:
                # Create assessment template
                await self._create_template(metadata, questions)
                templates_created += 1
                print(f"  ✅ Created template with {len(questions)} questions")
            else:
                print(f"  ⚠️  Failed to generate questions")

        print("\n" + "=" * 70)
        print(f"✅ TEMPLATES GENERATED: {templates_created}")
        print("=" * 70)

        await self.client.close()

    def _extract_metadata(self, filename: str, content: str) -> Dict[str, Any]:
        """Extract module metadata."""
        import re

        # Module number
        match = re.search(r'module_(\d+)', filename)
        module_number = int(match.group(1)) if match else 0

        # Title
        title_match = re.search(r'^# Module \d+: (.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else f"Module {module_number}"

        # Topics
        topics_match = re.search(r'\*\*Topics Covered:\*\* (.+)$', content, re.MULTILINE)
        topics = []
        if topics_match:
            topics = [t.strip() for t in topics_match.group(1).split(',')]

        return {
            "module_number": module_number,
            "module_title": title,
            "topics": topics
        }

    async def _generate_questions(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate 5 assessment questions using Gemini.

        Args:
            content: Module content
            metadata: Module metadata

        Returns:
            List of question dictionaries
        """
        # Prepare prompt
        prompt = f"""Generate 5 assessment questions for this learning module.

Module Title: {metadata['module_title']}
Topics: {', '.join(metadata['topics'])}

Content:
{content[:3000]}

For each question, provide:
1. question_text: Clear, specific question
2. expected_answer: Concise correct answer (2-3 sentences)
3. key_concepts: List of 2-4 concepts being tested
4. difficulty: beginner, intermediate, or advanced

Requirements:
- 2 beginner questions (recall and understanding)
- 2 intermediate questions (application and analysis)
- 1 advanced question (synthesis and evaluation)
- Questions should test actual understanding, not just memorization
- Focus on practical application of concepts

Return ONLY valid JSON in this exact format:
[
  {{
    "question_text": "...",
    "expected_answer": "...",
    "key_concepts": ["concept1", "concept2"],
    "difficulty": "beginner"
  }},
  ...
]
"""

        try:
            # Generate questions
            response = self.model.generate_content(prompt)
            response_text = response.text

            # Extract JSON from response
            import json
            import re

            # Try to find JSON array in response
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                questions_json = json_match.group(0)
                questions = json.loads(questions_json)

                # Validate structure
                for q in questions:
                    if not all(k in q for k in ['question_text', 'expected_answer', 'key_concepts', 'difficulty']):
                        print(f"    ⚠️  Invalid question structure: {q}")
                        return []

                return questions
            else:
                print(f"    ⚠️  No JSON found in response")
                return []

        except Exception as e:
            print(f"    ❌ Error generating questions: {str(e)}")
            return []

    async def _create_template(
        self,
        metadata: Dict[str, Any],
        questions: List[Dict[str, Any]]
    ):
        """Create assessment template in database."""
        template_id = f"assessment_template_module_{metadata['module_number']:02d}"

        # Build questions list
        formatted_questions = []
        for q in questions:
            formatted_questions.append({
                "id": str(uuid.uuid4()),
                "question_text": q["question_text"],
                "expected_answer": q.get("expected_answer"),
                "key_concepts": q.get("key_concepts", []),
                "difficulty": q.get("difficulty", "intermediate"),
                "topic": metadata["module_title"],
                "subject": "Software Engineering",
                "max_score": 1.0
            })

        # Create template document
        template = {
            "_id": template_id,
            "organization_id": ORGANIZATION_ID,
            "user_id": "template",  # Indicates this is a template
            "assessment_type": "formative",
            "status": "template",  # Special status for templates
            "subject": "Software Engineering",
            "topics": metadata["topics"],
            "collection_name": COLLECTION_NAME,
            "questions": formatted_questions,
            "total_questions": len(formatted_questions),
            "metadata": {
                "module_number": metadata["module_number"],
                "module_title": metadata["module_title"],
                "is_template": True,
                "passing_score": 0.7,
                "estimated_time_minutes": 15
            },
            "created_at": datetime.utcnow()
        }

        # Upsert template
        await self.collection.update_one(
            {"_id": template_id},
            {"$set": template},
            upsert=True
        )


async def main():
    """Main entry point."""
    print("=" * 70)
    print("🎯 ASSESSMENT TEMPLATE GENERATION")
    print("=" * 70)

    generator = AssessmentTemplateGenerator()

    try:
        await generator.generate_all_templates()

        print(f"\n✅ Template generation complete!")
        print(f"\n🎯 Next steps:")
        print(f"   1. Review generated questions in MongoDB")
        print(f"   2. Test creating assessments from templates")
        print(f"   3. Refine questions based on student feedback")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
