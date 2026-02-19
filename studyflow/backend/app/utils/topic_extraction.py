"""
Topic extraction utilities for StudyFlow materials.

Extracts topics from material titles, subjects, and content using AI.

Created: 2025-11-19
Author: KasaAI
"""

import re
import sys
import json
import logging
from typing import List

# Add shared to path
sys.path.insert(0, "/opt/kasaai/apps")
from shared.integration.gemini_service import GeminiService

logger = logging.getLogger(__name__)


async def extract_topics_from_content(
    content: str,
    title: str = "",
    subject: str = ""
) -> List[str]:
    """
    Extract topics from material content using AI.

    Uses Gemini AI to analyze actual document content for accurate topics.

    Args:
        content: Material text content from RAG
        title: Material title (optional context)
        subject: Material subject (optional context)

    Returns:
        List of extracted topics
    """
    try:
        gemini = GeminiService()

        if not gemini.is_available():
            logger.warning("Gemini not available, falling back to title extraction")
            return await extract_topics_from_title_ai(title, subject)

        # Truncate content if too long (max ~3000 chars for context)
        content_preview = content[:3000] if len(content) > 3000 else content

        prompt = f"""Analyze this educational material and extract 3-5 specific, meaningful topics that students would study.

Material Title: {title}
Subject: {subject}

Content Preview:
{content_preview}

Extract topics that are:
- Specific concepts or skills covered in the material
- Educational and academic in nature
- Useful for students to understand what they'll learn
- Not generic (avoid words like "Introduction", "Overview", "Basics")

Return ONLY a JSON array: ["Topic 1", "Topic 2", "Topic 3"]
No explanation:"""

        response = await gemini.generate_content(
            prompt=prompt,
            temperature=0.2,
            max_output_tokens=300
        )

        content_response = response.get("content", "[]")

        # Try to parse JSON
        json_match = re.search(r'\[.*?\]', content_response, re.DOTALL)
        if json_match:
            topics = json.loads(json_match.group())
            if isinstance(topics, list) and len(topics) > 0:
                logger.info(f"AI extracted content-based topics: {topics}")
                return topics[:5]

        # Fallback
        logger.warning(f"Content-based extraction failed, using title fallback")
        return await extract_topics_from_title_ai(title, subject)

    except Exception as e:
        logger.error(f"Error in content-based topic extraction: {e}")
        return await extract_topics_from_title_ai(title, subject)


async def extract_topics_from_title_ai(title: str, subject: str = "") -> List[str]:
    """
    Extract topics from material title and subject using AI.

    Uses Gemini AI to generate meaningful, educational topics.

    Args:
        title: Material title
        subject: Material subject

    Returns:
        List of extracted topics
    """
    try:
        gemini = GeminiService()

        if not gemini.is_available():
            logger.warning("Gemini not available, falling back to basic extraction")
            return extract_topics_from_title(title, subject)

        prompt = f"""Extract 3-5 educational topics from this study material.

Title: "{title}"
Subject: "{subject}"

Output ONLY a JSON array like: ["Topic 1", "Topic 2", "Topic 3"]
No explanation, just the array:"""

        response = await gemini.generate_content(
            prompt=prompt,
            temperature=0.1,  # Very low temperature for consistent JSON
            max_output_tokens=500  # Increased tokens
        )

        # Extract JSON from response
        content = response.get("content", "[]")

        # Try to parse JSON
        json_match = re.search(r'\[.*?\]', content, re.DOTALL)
        if json_match:
            topics = json.loads(json_match.group())
            if isinstance(topics, list) and len(topics) > 0:
                logger.info(f"AI extracted topics for '{title}': {topics}")
                return topics[:5]  # Limit to 5

        # Fallback if AI fails
        logger.warning(f"AI topic extraction failed, using fallback for: {title}")
        return extract_topics_from_title(title, subject)

    except Exception as e:
        logger.error(f"Error in AI topic extraction: {e}")
        return extract_topics_from_title(title, subject)


def extract_topics_from_title(title: str, subject: str = "") -> List[str]:
    """
    Extract topics from material title and subject.

    Args:
        title: Material title
        subject: Material subject

    Returns:
        List of extracted topics
    """
    topics = []

    # Clean title - remove common prefixes/suffixes
    clean_title = title
    for prefix in ['Cambridge IGCSE', 'A-Level', 'Cambridge Primary', 'IGCSE', 'A Level']:
        clean_title = clean_title.replace(prefix, '').strip()

    # Split by common separators
    parts = re.split(r'[-_:\|]', clean_title)

    for part in parts:
        part = part.strip()
        # Skip empty, short, or generic parts
        if len(part) > 3 and part.lower() not in ['the', 'and', 'for', 'with', 'notes', 'chapter']:
            topics.append(part.title())

    # Add subject if not already in topics
    if subject and subject.title() not in topics:
        topics.insert(0, subject.title())

    # Deduplicate while preserving order
    seen = set()
    unique_topics = []
    for topic in topics:
        topic_lower = topic.lower()
        if topic_lower not in seen:
            seen.add(topic_lower)
            unique_topics.append(topic)

    return unique_topics[:5]  # Limit to 5 most relevant topics


def extract_topics_from_content_basic(content: str, max_topics: int = 5) -> List[str]:
    """
    Extract topics from material content using simple keyword extraction.

    This is a basic implementation. For production, consider using:
    - NLP libraries (spaCy, NLTK)
    - AI-powered topic extraction
    - TF-IDF analysis

    Args:
        content: Material text content
        max_topics: Maximum number of topics to extract

    Returns:
        List of extracted topics
    """
    # Simple implementation: extract capitalized phrases
    # This would be replaced with proper NLP in production

    # Find capitalized words/phrases
    pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    potential_topics = re.findall(pattern, content)

    # Count occurrences
    topic_counts = {}
    for topic in potential_topics:
        if len(topic) > 3:  # Skip short words
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

    # Sort by frequency and return top N
    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
    return [topic for topic, count in sorted_topics[:max_topics]]


def validate_topics(topics: List[str]) -> bool:
    """
    Validate that topics are properly formatted.

    Args:
        topics: List of topics

    Returns:
        True if valid, False otherwise
    """
    if not topics or not isinstance(topics, list):
        return False

    for topic in topics:
        if not isinstance(topic, str) or len(topic.strip()) == 0:
            return False

    return True


def merge_topics(topics1: List[str], topics2: List[str], max_topics: int = 10) -> List[str]:
    """
    Merge two topic lists, removing duplicates.

    Args:
        topics1: First list of topics
        topics2: Second list of topics
        max_topics: Maximum topics to return

    Returns:
        Merged topic list
    """
    # Combine and deduplicate
    seen = set()
    merged = []

    for topic in topics1 + topics2:
        topic_lower = topic.lower().strip()
        if topic_lower not in seen and len(topic) > 0:
            seen.add(topic_lower)
            merged.append(topic)

    return merged[:max_topics]
