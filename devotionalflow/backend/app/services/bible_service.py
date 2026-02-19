"""
Bible API service for fetching scripture text.
Primary: API.Bible (scripture.api.bible) - Modern translations (NIV, ESV, NLT, etc.)
Fallback: bible-api.com (free, no auth) - Public domain translations
"""

import httpx
import logging
from typing import Optional, Dict, Any
import re
import os

logger = logging.getLogger(__name__)

# API.Bible configuration (primary source)
API_BIBLE_BASE_URL = "https://rest.api.bible/v1"
API_BIBLE_KEY = os.getenv("BIBLE_API_KEY", "")

# ESV API configuration (secondary source for ESV)
ESV_API_BASE_URL = "https://api.esv.org/v3/passage"
ESV_API_KEY = os.getenv("ESV_API_KEY", "")

# bible-api.com configuration (fallback)
BIBLE_API_BASE_URL = "https://bible-api.com"

# API.Bible translation mapping - English Bible translations (19 total)
# Note: Excludes specialized Bibles that use non-standard book names (e.g., Messianic, Septuagint, Hebrew names)
API_BIBLE_TRANSLATIONS = {
    # Modern Readable Translations
    "bsb": "bba9f40183526463-01",  # Berean Standard Bible
    "cev": "555fef9a6cb31151-01",  # Contemporary English Version
    "fbv": "65eec8e0b60e656b-01",  # Free Bible Version
    "t4t": "66c22495370cdfc0-01",  # Translation for Translators

    # Classic Translations
    "kjv": "de4e12af7f28f599-01",  # King James (Authorised) Version
    "kjvcpb": "55212e3cf5d04d49-01",  # Cambridge Paragraph Bible of the KJV
    "gnv": "c315fa9f71d4af3a-01",  # Geneva Bible
    "asv": "06125adad2d5898a-01",  # American Standard Version
    "rv": "40072c4a5aba4022-01",  # Revised Version 1885
    "dra": "179568874c45066f-01",  # Douay-Rheims American 1899

    # Literal & Scholarly Translations
    "lsv": "01b29f4b342acc35-01",  # Literal Standard Version
    "tcent": "32339cf2f720ff8e-01",  # Text-Critical English New Testament
    "f35": "2f0fd81d7b85b923-01",  # English New Testament According to Family 35

    # World English Bible Family
    "web": "9879dbb7cfe39e4d-01",  # World English Bible
    "webbe": "7142879509583d59-01",  # World English Bible British Edition
    "webu": "72f4e6dc683324df-01",  # World English Bible Updated
    "webus": "32664dc3288a28df-03",  # World English Bible, American English Edition

    # Contemporary English Version Variants
    "cevdci": "555fef9a6cb31151-02",  # CEV Interconfessional Edition
    "cevdco": "555fef9a6cb31151-03",  # CEV Old Tradition
}


async def fetch_scripture_from_api_bible(
    reference: str, translation: str = "kjv"
) -> Optional[Dict[str, Any]]:
    """
    Fetch scripture from API.Bible (primary source).
    Uses verses endpoint for accurate retrieval.
    Supports both translation abbreviations (e.g., 'kjv') and full Bible IDs (e.g., 'de4e12af7f28f599-01').
    """
    if not API_BIBLE_KEY:
        logger.warning("API.Bible key not configured, skipping")
        return None

    try:
        # Get Bible ID - check if it's already a full Bible ID or if we need to look it up
        if "-" in translation and len(translation) > 10:
            # Already a full Bible ID (e.g., 'de4e12af7f28f599-01')
            bible_id = translation
        else:
            # Look up abbreviation in our mapping
            bible_id = API_BIBLE_TRANSLATIONS.get(translation.lower())
            if not bible_id:
                logger.warning(f"Translation {translation} not found in API.Bible mapping, trying fallback")
                return None

        # Format reference for API.Bible (e.g., "JHN.3.16" or "JHN.3.16-JHN.3.17")
        # For simplicity, use passage endpoint which accepts human-readable references
        reference_clean = reference.strip()

        url = f"{API_BIBLE_BASE_URL}/bibles/{bible_id}/search"
        params = {"query": reference_clean, "limit": 1, "sort": "canonical"}
        headers = {"api-key": API_BIBLE_KEY}

        logger.info(f"Fetching from API.Bible: {reference} ({translation})")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()

            # API.Bible search endpoint returns "passages" or "verses"
            if not data.get("data"):
                logger.warning(f"No data found in API.Bible for {reference}")
                return None

            # Check for passages (search endpoint) or verses (verses endpoint)
            passages = data["data"].get("passages", [])
            verses = data["data"].get("verses", [])

            if not passages and not verses:
                logger.warning(f"No passages or verses found in API.Bible for {reference}")
                return None

            # Extract text from passages or verses
            if passages:
                # Parse HTML content from passages and extract text
                import re
                combined_text = ""
                for passage in passages:
                    content = passage.get("content", "")
                    # Remove HTML tags but preserve text
                    text_only = re.sub(r'<[^>]+>', '', content)
                    # Clean up extra whitespace
                    text_only = " ".join(text_only.split())
                    combined_text += text_only + " "

                # Build verses list from passages for consistency
                verses = [{
                    "reference": passage.get("reference", reference),
                    "text": re.sub(r'<[^>]+>', '', passage.get("content", "")),
                    "verse_id": passage.get("id", "")
                } for passage in passages]
            else:
                # Use verses directly if available
                combined_text = " ".join([v.get("text", "") for v in verses if v.get("text")])

            return {
                "reference": reference,
                "text": combined_text.strip(),
                "translation_id": translation.lower(),
                "translation_name": _get_translation_name(translation),
                "verses": verses,
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"API.Bible HTTP error for {reference}: {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"API.Bible error for {reference}: {e}")
        return None


async def fetch_scripture_from_free_api(
    reference: str, translation: str = "kjv"
) -> Optional[Dict[str, Any]]:
    """
    Fetch scripture from bible-api.com (fallback source).
    Supports public domain translations only.
    """
    try:
        reference_clean = reference.strip()
        url = f"{BIBLE_API_BASE_URL}/{reference_clean}"

        if translation and translation.lower() != "kjv":
            url += f"?translation={translation}"

        logger.info(f"Fetching from bible-api.com: {reference} ({translation})")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            data = response.json()

            return {
                "reference": data.get("reference", reference),
                "text": data.get("text", "").strip(),
                "translation_id": data.get("translation_id", translation),
                "translation_name": data.get("translation_name", "King James Version"),
                "verses": data.get("verses", []),
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"bible-api.com HTTP error for {reference}: {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"bible-api.com error for {reference}: {e}")
        return None


async def fetch_scripture_from_esv(
    reference: str,
    include_verse_numbers: bool = True,
    include_footnotes: bool = False,
    include_headings: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Fetch scripture from ESV API (Crossway).
    Provides access to English Standard Version.

    Args:
        reference: Scripture reference (e.g., "John 3:16", "Psalm 23")
        include_verse_numbers: Include verse numbers in text
        include_footnotes: Include footnote markers
        include_headings: Include section headings

    Returns:
        Dictionary with scripture data or None if failed
    """
    if not ESV_API_KEY:
        logger.warning("ESV API key not configured, skipping")
        return None

    try:
        reference_clean = reference.strip()
        url = f"{ESV_API_BASE_URL}/text/"
        params = {
            "q": reference_clean,
            "include-passage-references": "false",
            "include-verse-numbers": str(include_verse_numbers).lower(),
            "include-first-verse-numbers": str(include_verse_numbers).lower(),
            "include-footnotes": str(include_footnotes).lower(),
            "include-footnote-body": str(include_footnotes).lower(),
            "include-headings": str(include_headings).lower(),
            "include-short-copyright": "false",
            "include-selahs": "true",
            "indent-paragraphs": "0",
            "indent-poetry": "true",
            "line-length": "0",
        }
        headers = {"Authorization": f"Token {ESV_API_KEY}"}

        logger.info(f"Fetching from ESV API: {reference}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()

            # ESV API returns passages as a list
            passages = data.get("passages", [])
            if not passages:
                logger.warning(f"No passages found in ESV API for {reference}")
                return None

            # Combine all passages and clean up
            combined_text = " ".join(passages).strip()
            # Clean up extra whitespace while preserving paragraph breaks
            combined_text = re.sub(r' +', ' ', combined_text)
            combined_text = re.sub(r'\n\s*\n', '\n\n', combined_text)

            return {
                "reference": data.get("canonical", reference),
                "text": combined_text,
                "translation_id": "esv",
                "translation_name": "English Standard Version",
                "verses": [],  # ESV text endpoint doesn't provide verse breakdown
                "passage_meta": data.get("passage_meta", []),
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"ESV API HTTP error for {reference}: {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"ESV API error for {reference}: {e}")
        return None


async def fetch_esv_html(
    reference: str,
    include_footnotes: bool = True,
    include_headings: bool = True,
    include_css_link: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Fetch scripture from ESV API as formatted HTML.

    Args:
        reference: Scripture reference (e.g., "John 3:16", "Psalm 23")
        include_footnotes: Include footnote markers and body
        include_headings: Include section headings
        include_css_link: Include link to ESV stylesheet

    Returns:
        Dictionary with HTML content and metadata or None if failed
    """
    if not ESV_API_KEY:
        logger.warning("ESV API key not configured, skipping")
        return None

    try:
        reference_clean = reference.strip()
        url = f"{ESV_API_BASE_URL}/html/"
        params = {
            "q": reference_clean,
            "include-passage-references": "true",
            "include-verse-numbers": "true",
            "include-first-verse-numbers": "true",
            "include-footnotes": str(include_footnotes).lower(),
            "include-footnote-body": str(include_footnotes).lower(),
            "include-headings": str(include_headings).lower(),
            "include-short-copyright": "true",
            "include-css-link": str(include_css_link).lower(),
            "include-audio-link": "true",
        }
        headers = {"Authorization": f"Token {ESV_API_KEY}"}

        logger.info(f"Fetching HTML from ESV API: {reference}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()

            passages = data.get("passages", [])
            if not passages:
                logger.warning(f"No HTML passages found in ESV API for {reference}")
                return None

            return {
                "reference": data.get("canonical", reference),
                "html": "".join(passages),
                "translation_id": "esv",
                "translation_name": "English Standard Version",
                "passage_meta": data.get("passage_meta", []),
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"ESV HTML API error for {reference}: {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"ESV HTML API error for {reference}: {e}")
        return None


async def fetch_esv_audio_url(reference: str) -> Optional[Dict[str, Any]]:
    """
    Get audio URL for a scripture passage from ESV API.

    Args:
        reference: Scripture reference (e.g., "John 3:16", "Psalm 23")

    Returns:
        Dictionary with audio URL and metadata or None if failed
    """
    if not ESV_API_KEY:
        logger.warning("ESV API key not configured, skipping")
        return None

    try:
        reference_clean = reference.strip()
        url = f"{ESV_API_BASE_URL}/audio/"
        params = {"q": reference_clean}
        headers = {"Authorization": f"Token {ESV_API_KEY}"}

        logger.info(f"Fetching audio URL from ESV API: {reference}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Audio endpoint redirects to the audio file
            response = await client.get(url, params=params, headers=headers, follow_redirects=False)

            if response.status_code in (301, 302, 307, 308):
                audio_url = response.headers.get("Location")
                return {
                    "reference": reference_clean,
                    "audio_url": audio_url,
                    "translation_id": "esv",
                    "translation_name": "English Standard Version",
                }
            elif response.status_code == 200:
                # Some versions may return JSON with URL
                data = response.json()
                return {
                    "reference": data.get("canonical", reference_clean),
                    "audio_url": data.get("url") or data.get("audio_url"),
                    "translation_id": "esv",
                    "translation_name": "English Standard Version",
                }
            else:
                logger.warning(f"Unexpected response from ESV audio API: {response.status_code}")
                return None

    except httpx.HTTPStatusError as e:
        logger.error(f"ESV audio API error for {reference}: {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"ESV audio API error for {reference}: {e}")
        return None


async def search_esv(
    query: str,
    page_size: int = 20,
    page: int = 1,
) -> Optional[Dict[str, Any]]:
    """
    Search the ESV Bible for a keyword or phrase.

    Args:
        query: Search query (word or phrase)
        page_size: Number of results per page (max 100)
        page: Page number (1-indexed)

    Returns:
        Dictionary with search results or None if failed
    """
    if not ESV_API_KEY:
        logger.warning("ESV API key not configured, skipping")
        return None

    try:
        url = f"{ESV_API_BASE_URL}/search/"
        params = {
            "q": query.strip(),
            "page-size": min(page_size, 100),
            "page": max(page, 1),
        }
        headers = {"Authorization": f"Token {ESV_API_KEY}"}

        logger.info(f"Searching ESV API for: {query}")

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()

            return {
                "query": query,
                "page": data.get("page", page),
                "total_results": data.get("total_results", 0),
                "total_pages": data.get("total_pages", 0),
                "results": [
                    {
                        "reference": result.get("reference"),
                        "content": result.get("content"),
                    }
                    for result in data.get("results", [])
                ],
                "translation_id": "esv",
                "translation_name": "English Standard Version",
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"ESV search API error: {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"ESV search API error: {e}")
        return None


async def fetch_scripture(reference: str, translation: str = "kjv") -> Optional[Dict[str, Any]]:
    """
    Fetch scripture text from Bible APIs with fallback.

    Priority order: ESV API first (if requesting ESV), then API.Bible, then bible-api.com (public domain).

    Args:
        reference: Scripture reference (e.g., "John 3:16", "Psalm 23:1-6")
        translation: Bible translation (esv, kjv, web, etc.) or full Bible ID

    Returns:
        Dictionary with scripture data or None if failed

    Example response:
        {
            "reference": "John 3:16",
            "text": "For God so loved the world...",
            "translation_id": "niv",
            "translation_name": "New International Version",
            "verses": [...]
        }
    """
    # Try ESV API first if requesting ESV specifically
    if translation.lower() == "esv":
        logger.info(f"Trying ESV API for: {reference}")
        result = await fetch_scripture_from_esv(reference)
        if result:
            logger.info(f"Successfully fetched from ESV API: {reference}")
            return result

    # Try API.Bible second (supports modern translations)
    result = await fetch_scripture_from_api_bible(reference, translation)
    if result:
        logger.info(f"Successfully fetched from API.Bible: {reference}")
        return result

    # Fallback to free bible-api.com last (public domain only)
    logger.info(f"Trying fallback bible-api.com for: {reference}")
    result = await fetch_scripture_from_free_api(reference, translation)
    if result:
        logger.info(f"Successfully fetched from bible-api.com: {reference}")
        return result

    logger.error(f"All Bible APIs failed for: {reference} ({translation})")
    return None


def _get_translation_name(translation_id: str) -> str:
    """Get full name for translation ID."""
    names = {
        # Modern Readable Translations
        "esv": "English Standard Version",
        "bsb": "Berean Standard Bible",
        "cev": "Contemporary English Version",
        "fbv": "Free Bible Version",
        "t4t": "Translation for Translators",

        # Classic Translations
        "kjv": "King James Version",
        "kjvcpb": "Cambridge Paragraph Bible of the KJV",
        "gnv": "Geneva Bible",
        "asv": "American Standard Version",
        "rv": "Revised Version 1885",
        "dra": "Douay-Rheims American 1899",

        # Literal & Scholarly Translations
        "lsv": "Literal Standard Version",
        "tcent": "Text-Critical English New Testament",
        "f35": "English New Testament According to Family 35",

        # World English Bible Family
        "web": "World English Bible",
        "webbe": "World English Bible, British Edition",
        "webu": "World English Bible Updated",
        "webus": "World English Bible, American English Edition",
        "wmb": "World Messianic Bible",
        "wmbbe": "World Messianic Bible British Edition",

        # Specialized & Academic Translations
        "brenton": "Brenton English Translation of the Septuagint",
        "lxxup": "Brenton English Septuagint (Updated)",
        "ojps": "JPS TaNaKH 1917",
        "tojbt2011": "Orthodox Jewish Bible",
        "tojb2011": "Orthodox Jewish Bible",
        "oke": "Targum Onkelos Etheridge",

        # Contemporary English Version Variants
        "cevdci": "CEV Interconfessional Edition",
        "cevdco": "CEV Old Tradition",

        # Legacy/Fallback translations (from bible-api.com)
        "bbe": "Bible in Basic English",
        "ylt": "Young's Literal Translation",
        "oeb-us": "Open English Bible, US Edition",
        "clementine": "Clementine Latin Vulgate",
        "almeida": "João Ferreira de Almeida",
    }
    return names.get(translation_id.lower(), translation_id.upper())


async def fetch_multiple_scriptures(
    references: list[str], translation: str = "kjv"
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Fetch multiple scripture references concurrently.

    Args:
        references: List of scripture references
        translation: Bible translation (default: kjv)

    Returns:
        Dictionary mapping reference to scripture data
    """
    import asyncio

    tasks = {ref: fetch_scripture(ref, translation) for ref in references}
    results = await asyncio.gather(*tasks.values())

    return dict(zip(tasks.keys(), results))


async def fetch_available_bibles(language: Optional[str] = None) -> list[Dict[str, Any]]:
    """
    Fetch list of available Bible translations from API.Bible.

    Args:
        language: Optional language code filter (e.g., 'eng', 'spa', 'fra')

    Returns:
        List of Bible translations with metadata

    Example response:
        [
            {
                "id": "de4e12af7f28f599-01",
                "name": "King James (Authorised) Version",
                "abbreviation": "KJV",
                "language": "eng",
                "description": "English"
            },
            ...
        ]
    """
    if not API_BIBLE_KEY:
        logger.warning("API.Bible key not configured, returning empty list")
        return []

    try:
        url = f"{API_BIBLE_BASE_URL}/bibles"
        params = {}
        if language:
            params["language"] = language

        headers = {"api-key": API_BIBLE_KEY}

        logger.info(f"Fetching available Bibles from API.Bible (language: {language or 'all'})")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()

            # Use a dict to deduplicate by abbreviation (keep first occurrence)
            bibles_dict = {}
            for bible in data.get("data", []):
                abbr = bible.get("abbreviationLocal") or bible.get("abbreviation")

                # Skip if we already have this abbreviation
                if abbr in bibles_dict:
                    continue

                bibles_dict[abbr] = {
                    "id": bible["id"],
                    "name": bible.get("nameLocal") or bible.get("name"),
                    "abbreviation": abbr,
                    "language": bible.get("language", {}).get("id", "unknown"),
                    "description": bible.get("description") or bible.get("language", {}).get("name"),
                }

            # Convert dict to list
            bibles = list(bibles_dict.values())

            # Add ESV if API key is configured and language filter matches
            if ESV_API_KEY and (not language or language == "eng"):
                bibles.append({
                    "id": "esv",
                    "name": "English Standard Version",
                    "abbreviation": "ESV",
                    "language": "eng",
                    "description": "English Standard Version (ESV API)",
                })

            # Sort by abbreviation
            bibles = sorted(bibles, key=lambda x: x["abbreviation"])

            logger.info(f"Found {len(bibles)} unique Bibles (deduplicated, including ESV if available)")
            return bibles

    except httpx.HTTPStatusError as e:
        logger.error(f"API.Bible HTTP error: {e.response.status_code}")
        return []
    except Exception as e:
        logger.error(f"API.Bible error: {e}")
        return []


def parse_scripture_reference(reference: str) -> Optional[Dict[str, Any]]:
    """
    Parse a scripture reference into components.

    Args:
        reference: Scripture reference (e.g., "John 3:16-17", "1 Corinthians 13:4-7")

    Returns:
        Dictionary with parsed components:
        {
            "book": "John",
            "chapter": 3,
            "verse_start": 16,
            "verse_end": 17 (optional)
        }
    """
    try:
        # Pattern: "Book Chapter:Verse" or "Book Chapter:VerseStart-VerseEnd"
        # Handles: "John 3:16", "1 Corinthians 13:4-7", "Psalm 23:1-6"
        pattern = r"^(\d?\s?[A-Za-z]+)\s+(\d+):(\d+)(?:-(\d+))?$"
        match = re.match(pattern, reference.strip())

        if not match:
            logger.warning(f"Could not parse scripture reference: {reference}")
            return None

        book, chapter, verse_start, verse_end = match.groups()

        return {
            "book": book.strip(),
            "chapter": int(chapter),
            "verse_start": int(verse_start),
            "verse_end": int(verse_end) if verse_end else None,
        }

    except Exception as e:
        logger.error(f"Error parsing scripture reference {reference}: {e}")
        return None


def format_scripture_for_display(scripture_data: Dict[str, Any]) -> str:
    """
    Format scripture data for display in devotionals.

    Args:
        scripture_data: Scripture data from fetch_scripture()

    Returns:
        Formatted scripture text (without verse numbers)
    """
    if not scripture_data or not scripture_data.get("text"):
        return ""

    # Remove verse numbers like [1], [2], etc.
    text = scripture_data["text"]
    text = re.sub(r"\[\d+\]", "", text)

    # Clean up extra whitespace
    text = " ".join(text.split())

    return text.strip()
