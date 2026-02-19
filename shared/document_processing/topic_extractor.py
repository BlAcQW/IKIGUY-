"""
AI-powered topic extraction for documents.

Extracts meaningful topics from document content using AI (Gemini)
with multiple fallback strategies.

Author: KasaAI Team
Date: 2025-11-28
"""

import json
import logging
import re
from typing import List, Optional

logger = logging.getLogger(__name__)


class TopicExtractor:
    """
    AI-powered topic extraction service.

    Extracts educational/descriptive topics from documents using:
    1. AI content analysis (primary)
    2. AI title analysis (fallback)
    3. Basic pattern matching (last resort)
    """

    def __init__(self, gemini_service=None):
        """
        Initialize topic extractor.

        Args:
            gemini_service: Optional GeminiService instance.
                           If not provided, will try to import from shared.
        """
        self._gemini = gemini_service

    @property
    def gemini(self):
        """Lazy load Gemini service."""
        if self._gemini is None:
            try:
                from shared.integration.gemini_service import GeminiService

                self._gemini = GeminiService()
            except Exception as e:
                logger.warning(f"Could not initialize Gemini: {e}")
                self._gemini = None
        return self._gemini

    async def extract_from_content(
        self,
        content: str,
        title: str = "",
        category: str = "",
        max_topics: int = 5,
    ) -> List[str]:
        """
        Extract topics from document content using AI.

        Args:
            content: Document text content
            title: Document title (optional context)
            category: Document category/subject (optional context)
            max_topics: Maximum number of topics to return

        Returns:
            List of extracted topics
        """
        try:
            if not self.gemini or not self.gemini.is_available():
                logger.warning("Gemini not available, using title fallback")
                return await self.extract_from_title(title, category, max_topics)

            # Truncate content if too long
            content_preview = content[:3000] if len(content) > 3000 else content

            prompt = f"""Analyze this document and extract {max_topics} specific, meaningful topics.

Document Title: {title}
Category: {category}

Content Preview:
{content_preview}

Extract topics that are:
- Specific concepts or themes covered in the document
- Meaningful and descriptive
- Useful for categorization and search
- Not generic (avoid words like "Introduction", "Overview", "Basics")

Return ONLY a JSON array: ["Topic 1", "Topic 2", "Topic 3"]
No explanation, just the array:"""

            response = await self.gemini.generate_content(
                prompt=prompt, temperature=0.2, max_output_tokens=300
            )

            content_response = response.get("content", "[]")

            # Try to parse JSON
            json_match = re.search(r"\[.*?\]", content_response, re.DOTALL)
            if json_match:
                topics = json.loads(json_match.group())
                if isinstance(topics, list) and len(topics) > 0:
                    logger.info(f"AI extracted content-based topics: {topics}")
                    return topics[:max_topics]

            # Fallback to title extraction
            logger.warning("Content extraction failed, using title fallback")
            return await self.extract_from_title(title, category, max_topics)

        except Exception as e:
            logger.error(f"Error in content-based topic extraction: {e}")
            return await self.extract_from_title(title, category, max_topics)

    async def extract_from_title(
        self,
        title: str,
        category: str = "",
        max_topics: int = 5,
    ) -> List[str]:
        """
        Extract topics from document title using AI.

        Args:
            title: Document title
            category: Document category/subject
            max_topics: Maximum number of topics

        Returns:
            List of extracted topics
        """
        try:
            if not self.gemini or not self.gemini.is_available():
                logger.warning("Gemini not available, using basic extraction")
                return self.extract_basic(title, category, max_topics)

            prompt = f"""Extract {max_topics} relevant topics from this document.

Title: "{title}"
Category: "{category}"

Output ONLY a JSON array like: ["Topic 1", "Topic 2", "Topic 3"]
No explanation, just the array:"""

            response = await self.gemini.generate_content(
                prompt=prompt, temperature=0.1, max_output_tokens=300
            )

            content = response.get("content", "[]")

            # Try to parse JSON
            json_match = re.search(r"\[.*?\]", content, re.DOTALL)
            if json_match:
                topics = json.loads(json_match.group())
                if isinstance(topics, list) and len(topics) > 0:
                    logger.info(f"AI extracted title-based topics: {topics}")
                    return topics[:max_topics]

            # Fallback to basic
            logger.warning("AI title extraction failed, using basic")
            return self.extract_basic(title, category, max_topics)

        except Exception as e:
            logger.error(f"Error in AI title topic extraction: {e}")
            return self.extract_basic(title, category, max_topics)

    def extract_basic(
        self,
        title: str,
        category: str = "",
        max_topics: int = 5,
    ) -> List[str]:
        """
        Extract topics using basic pattern matching.

        Args:
            title: Document title
            category: Document category
            max_topics: Maximum topics to return

        Returns:
            List of extracted topics
        """
        topics = []

        # Clean title - remove common prefixes
        clean_title = title
        prefixes = [
            "Cambridge IGCSE",
            "A-Level",
            "Cambridge Primary",
            "IGCSE",
            "A Level",
            "Chapter",
            "Part",
            "Section",
        ]
        for prefix in prefixes:
            clean_title = clean_title.replace(prefix, "").strip()

        # Split by common separators
        parts = re.split(r"[-_:\|,]", clean_title)

        for part in parts:
            part = part.strip()
            # Skip empty, short, or generic parts
            if len(part) > 3 and part.lower() not in [
                "the",
                "and",
                "for",
                "with",
                "notes",
                "chapter",
                "part",
                "pdf",
                "doc",
            ]:
                topics.append(part.title())

        # Add category if not already in topics
        if category and category.title() not in topics:
            topics.insert(0, category.title())

        # Deduplicate while preserving order
        seen = set()
        unique_topics = []
        for topic in topics:
            topic_lower = topic.lower()
            if topic_lower not in seen:
                seen.add(topic_lower)
                unique_topics.append(topic)

        return unique_topics[:max_topics]

    def extract_from_keywords(
        self,
        content: str,
        max_topics: int = 5,
    ) -> List[str]:
        """
        Extract topics using keyword frequency analysis.

        Args:
            content: Document text content
            max_topics: Maximum topics to return

        Returns:
            List of extracted topics based on frequency
        """
        # Find capitalized words/phrases (potential topics)
        pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"
        potential_topics = re.findall(pattern, content)

        # Count occurrences
        topic_counts = {}
        for topic in potential_topics:
            if len(topic) > 3:  # Skip short words
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Sort by frequency and return top N
        sorted_topics = sorted(
            topic_counts.items(), key=lambda x: x[1], reverse=True
        )
        return [topic for topic, count in sorted_topics[:max_topics]]

    @staticmethod
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

    @staticmethod
    def merge_topics(
        topics1: List[str],
        topics2: List[str],
        max_topics: int = 10,
    ) -> List[str]:
        """
        Merge two topic lists, removing duplicates.

        Args:
            topics1: First list of topics
            topics2: Second list of topics
            max_topics: Maximum topics to return

        Returns:
            Merged topic list
        """
        seen = set()
        merged = []

        for topic in topics1 + topics2:
            topic_lower = topic.lower().strip()
            if topic_lower not in seen and len(topic) > 0:
                seen.add(topic_lower)
                merged.append(topic)

        return merged[:max_topics]


# Module-level convenience function
async def extract_topics(
    content: str = "",
    title: str = "",
    category: str = "",
    max_topics: int = 5,
) -> List[str]:
    """
    Convenience function to extract topics.

    Args:
        content: Document content (preferred)
        title: Document title
        category: Document category
        max_topics: Maximum topics

    Returns:
        List of extracted topics
    """
    extractor = TopicExtractor()

    if content:
        return await extractor.extract_from_content(
            content, title, category, max_topics
        )
    elif title:
        return await extractor.extract_from_title(title, category, max_topics)
    else:
        return []
