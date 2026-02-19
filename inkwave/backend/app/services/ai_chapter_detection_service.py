"""
AI-Enhanced Chapter Detection Service.

Uses Gemini AI to intelligently detect chapter boundaries in book text,
especially for books with non-standard chapter formats.

Features:
- Detects chapters with creative titles (not just "Chapter 1")
- Multi-language chapter detection
- Falls back to regex detection if AI fails
- Caches results to avoid repeated API calls
"""

import logging
import json
import re
import sys
from typing import List, Dict, Any, Optional

# Add shared services to path
sys.path.insert(0, '/opt/kasaai/apps')

from shared.integration.gemini_service import get_gemini_service

logger = logging.getLogger(__name__)


class AIChapterDetectionService:
    """
    Service for AI-enhanced chapter detection using Gemini.

    Analyzes book text to identify chapter boundaries even when
    chapters don't follow standard naming conventions.
    """

    def __init__(self):
        """Initialize the AI chapter detection service."""
        self.gemini = get_gemini_service()

    def is_available(self) -> bool:
        """
        Check if AI chapter detection is available.

        Returns:
            bool: True if Gemini API is configured
        """
        return self.gemini.is_available()

    async def detect_chapters(
        self,
        chunks: List[Any],
        book_title: str = "",
        max_sample_chunks: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Detect chapters in text chunks using AI.

        Args:
            chunks: List of text chunks (objects with 'content' or dict with 'text')
            book_title: Title of the book for context
            max_sample_chunks: Maximum chunks to sample for detection

        Returns:
            List of chapter dictionaries with:
            - chunk_index: Index where chapter starts
            - title: Detected chapter title
            - confidence: Detection confidence (high/medium/low)
        """
        if not self.is_available():
            logger.warning("Gemini not available, AI chapter detection skipped")
            return []

        try:
            # Extract text from chunks
            chunk_texts = []
            for idx, chunk in enumerate(chunks[:max_sample_chunks]):
                if isinstance(chunk, dict):
                    text = chunk.get('content') or chunk.get('text', '')
                elif hasattr(chunk, 'content'):
                    text = chunk.content
                elif hasattr(chunk, 'text'):
                    text = chunk.text
                else:
                    text = str(chunk)

                # Truncate long chunks for the prompt
                truncated = text[:500] if len(text) > 500 else text
                chunk_texts.append(f"[CHUNK {idx}]\n{truncated}")

            # Build the prompt
            prompt = self._build_detection_prompt(chunk_texts, book_title)

            # Call Gemini
            result = await self.gemini.extract_structured_data(
                prompt=prompt,
                max_output_tokens=2000,
                temperature=0.1  # Low temperature for consistency
            )

            # Parse the response
            chapters = self._parse_ai_response(result)

            logger.info(f"AI detected {len(chapters)} chapters in '{book_title}'")
            return chapters

        except Exception as e:
            logger.error(f"AI chapter detection failed: {e}")
            return []

    def _build_detection_prompt(
        self,
        chunk_texts: List[str],
        book_title: str
    ) -> str:
        """
        Build the prompt for chapter detection.

        Args:
            chunk_texts: List of chunk text samples
            book_title: Book title for context

        Returns:
            Formatted prompt string
        """
        chunks_sample = "\n\n".join(chunk_texts)

        prompt = f"""You are an expert at analyzing book structure. Analyze the following text chunks from a book and identify where chapters begin.

BOOK TITLE: {book_title or "Unknown"}

INSTRUCTIONS:
1. Look for chapter boundaries - these could be:
   - Standard formats: "Chapter 1", "CHAPTER ONE", "Part I"
   - Creative titles: "The Beginning", "A New Dawn", "Introduction"
   - Numbered sections: "1.", "Section 1", "I."
   - Multi-language: "Capitulo", "Chapitre", "Kapitel"
   - All-caps section headers
   - Lines that start with distinctive formatting

2. For each chapter you find, provide:
   - The CHUNK NUMBER where it starts (the number in [CHUNK X])
   - The exact TITLE as it appears in the text
   - Your CONFIDENCE level (high/medium/low)

3. Return ONLY valid JSON in this exact format:
{{
  "chapters": [
    {{"chunk_index": 0, "title": "Introduction", "confidence": "high"}},
    {{"chunk_index": 5, "title": "Chapter 1: The Beginning", "confidence": "high"}}
  ]
}}

4. If you cannot find any clear chapter boundaries, return:
{{"chapters": []}}

TEXT CHUNKS TO ANALYZE:
{chunks_sample}

IMPORTANT: Return ONLY the JSON object, no other text or explanation."""

        return prompt

    def _parse_ai_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse the AI response to extract chapter information.

        Args:
            response: Raw response from Gemini

        Returns:
            List of chapter dictionaries
        """
        try:
            # Clean up the response - remove markdown code blocks if present
            cleaned = response.strip()
            if cleaned.startswith("```"):
                # Remove markdown code block
                lines = cleaned.split("\n")
                # Remove first and last lines (```json and ```)
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines)

            # Parse JSON
            data = json.loads(cleaned)

            chapters = data.get("chapters", [])

            # Validate each chapter
            validated = []
            for ch in chapters:
                if isinstance(ch, dict) and "chunk_index" in ch and "title" in ch:
                    validated.append({
                        "chunk_index": int(ch["chunk_index"]),
                        "title": str(ch["title"]).strip()[:100],  # Limit title length
                        "confidence": ch.get("confidence", "medium")
                    })

            # Sort by chunk_index
            validated.sort(key=lambda x: x["chunk_index"])

            return validated

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Raw response: {response[:500]}...")
            return []
        except Exception as e:
            logger.error(f"Error parsing AI chapter response: {e}")
            return []

    async def detect_chapters_with_fallback(
        self,
        chunks: List[Any],
        book_title: str = "",
        use_ai: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Detect chapters with regex first, then AI enhancement.

        Strategy:
        1. First try regex detection (fast, free)
        2. If only 1 chapter found and use_ai=True, try AI detection
        3. Return best result

        Args:
            chunks: List of text chunks
            book_title: Book title for context
            use_ai: Whether to use AI for enhanced detection

        Returns:
            List of chapter dictionaries
        """
        # First try regex detection
        regex_chapters = self._detect_chapters_regex(chunks)

        logger.info(f"Regex detected {len(regex_chapters)} chapters")

        # If regex found multiple chapters or AI is disabled, return regex results
        if len(regex_chapters) > 1 or not use_ai:
            return regex_chapters

        # If only 0-1 chapters found, try AI detection
        if self.is_available():
            logger.info("Attempting AI-enhanced chapter detection...")
            ai_chapters = await self.detect_chapters(chunks, book_title)

            if len(ai_chapters) > len(regex_chapters):
                logger.info(f"AI found more chapters ({len(ai_chapters)}) than regex ({len(regex_chapters)})")
                return ai_chapters

        return regex_chapters

    def _detect_chapters_regex(self, chunks: List[Any]) -> List[Dict[str, Any]]:
        """
        Detect chapters using regex patterns.

        Args:
            chunks: List of text chunks

        Returns:
            List of chapter dictionaries
        """
        chapters = []

        # Regex patterns for chapter detection
        chapter_regex = re.compile(
            r'^(chapter|part|section)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|'
            r'eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|'
            r'i{1,3}|iv|v|vi{1,3}|ix|x|xi{1,3})\s*[:\-]?\s*(.*)$',
            re.IGNORECASE | re.MULTILINE
        )

        def is_toc_line(line: str) -> bool:
            """Check if line looks like table of contents."""
            if line.count('.') > 5 and len(line) < 200:
                return True
            if re.search(r'\.\s*\d+\s*$', line):
                return True
            return False

        for idx, chunk in enumerate(chunks):
            # Extract text
            if isinstance(chunk, dict):
                text = chunk.get('content') or chunk.get('text', '')
            elif hasattr(chunk, 'content'):
                text = chunk.content
            elif hasattr(chunk, 'text'):
                text = chunk.text
            else:
                text = str(chunk)

            # Check all lines for chapter headings
            lines = text.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line or is_toc_line(line):
                    continue

                match = chapter_regex.match(line)
                if match:
                    chapter_type = match.group(1).capitalize()
                    chapter_num = match.group(2)
                    chapter_subtitle = match.group(3).strip() if match.group(3) else ""

                    if chapter_subtitle:
                        title = f"{chapter_type} {chapter_num}: {chapter_subtitle}"[:100]
                    else:
                        title = f"{chapter_type} {chapter_num}"[:100]

                    chapters.append({
                        "chunk_index": idx,
                        "title": title,
                        "confidence": "high"
                    })
                    break  # Only count first chapter per chunk

        return chapters


# Global service instance
_ai_chapter_service: Optional[AIChapterDetectionService] = None


async def get_ai_chapter_detection_service() -> AIChapterDetectionService:
    """
    Get or create the AI chapter detection service.

    Returns:
        AIChapterDetectionService instance
    """
    global _ai_chapter_service
    if _ai_chapter_service is None:
        _ai_chapter_service = AIChapterDetectionService()
    return _ai_chapter_service
