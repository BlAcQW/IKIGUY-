"""
Hybrid Search Helper for Number-based Queries

This module provides utilities for combining keyword matching with vector search
to handle queries with numeric identifiers (community numbers, addresses, etc.).

Author: Claude Code
Date: October 30, 2025
"""

import re
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


def extract_community_number(query: str) -> Optional[int]:
    """
    Extract community number from query text.
    
    Examples:
        "community 5" → 5
        "comm 12" → 12
        "tema community 10" → 10
        "providers in community 25" → 25
    
    Args:
        query: User query text
        
    Returns:
        Community number if found, None otherwise
    """
    query_upper = query.upper()
    
    # Patterns for community numbers
    patterns = [
        r'COMMUNITY\s+(\d+)',
        r'COMM\.?\s+(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query_upper)
        if match:
            return int(match.group(1))
    
    return None


def extract_location_keywords(query: str) -> List[str]:
    """
    Extract location-related keywords from query.

    Args:
        query: User query text

    Returns:
        List of location keywords found
    """
    query_upper = query.upper()
    keywords = []

    # Common location prefixes in Ghana
    location_patterns = [
        r'(TEMA)',
        r'(ACCRA)',
        r'(KUMASI)',
        r'(MADINA)',
        r'(ADENTA)',
        r'(ASHAIMAN)',
    ]

    for pattern in location_patterns:
        if re.search(pattern, query_upper):
            match = re.search(pattern, query_upper)
            if match:
                keywords.append(match.group(1))

    return keywords


def extract_market_location(query: str) -> Optional[str]:
    """
    Extract market/central business district location from query.

    These locations often have lower vector similarity scores and need
    special handling with increased k value for better retrieval.

    Examples:
        "providers in Makola" → "MAKOLA"
        "doctors at Tudu" → "TUDU"
        "clinics in Accra Central" → "ACCRA CENTRAL"

    Args:
        query: User query text

    Returns:
        Market location name if found, None otherwise
    """
    query_upper = query.upper()

    # Market and central business district locations that need hybrid search
    # Reason: These locations have lower semantic similarity in vector search
    market_locations = [
        'MAKOLA',
        'TUDU',
        'ACCRA CENTRAL',
        'KANESHIE',
        'MADINA MARKET',
        'OKAISHIE',
    ]

    for location in market_locations:
        if location in query_upper:
            return location

    return None


def build_title_pattern(query: str, community_num: Optional[int] = None) -> Optional[str]:
    """
    Build a title pattern for exact matching based on query analysis.
    
    Args:
        query: User query text
        community_num: Extracted community number
        
    Returns:
        Title pattern for matching, or None
    """
    if not community_num:
        return None
    
    query_upper = query.upper()
    
    # Check if query mentions TEMA
    if 'TEMA' in query_upper:
        return f"Healthcare Providers in TEMA COMMUNITY {community_num}"
    
    # Check if query mentions ASHAIMAN
    if 'ASHAIMAN' in query_upper:
        return f"Healthcare Providers in ASHAIMAN COMMUNITY {community_num}"
    
    # Generic community pattern
    # Try to detect location from query or use generic pattern
    location_keywords = extract_location_keywords(query)
    
    if location_keywords:
        # Use first location keyword found
        return f"Healthcare Providers in {location_keywords[0]} COMMUNITY {community_num}"
    
    # If no specific location, try both common patterns
    return f"COMMUNITY {community_num}"


def should_use_hybrid_search(query: str) -> Tuple[bool, Optional[dict]]:
    """
    Determine if hybrid search should be used and return search parameters.

    Hybrid search is needed for:
    - Community number queries (e.g., "Community 5")
    - Market/CBD location queries (e.g., "Makola", "Tudu")

    Args:
        query: User query text

    Returns:
        Tuple of (should_use_hybrid, search_params)
        where search_params is a dict with extracted parameters or None
    """
    community_num = extract_community_number(query)
    market_location = extract_market_location(query)

    # Check for community number queries
    if community_num:
        title_pattern = build_title_pattern(query, community_num)

        search_params = {
            "community_number": community_num,
            "title_pattern": title_pattern,
            "location_keywords": extract_location_keywords(query),
            "search_type": "community_number"
        }

        logger.info(f"🔍 Hybrid search triggered: community={community_num}, pattern='{title_pattern}'")
        return True, search_params

    # Check for market/CBD location queries
    if market_location:
        # For market locations, we need enhanced retrieval but no specific title pattern
        # Reason: Vector embeddings have low similarity for market areas
        search_params = {
            "market_location": market_location,
            "title_pattern": f"Healthcare Providers in {market_location}",
            "location_keywords": [market_location],
            "search_type": "market_location"
        }

        logger.info(f"🔍 Hybrid search triggered for market location: '{market_location}'")
        return True, search_params

    return False, None


def filter_docs_by_title_match(docs: List, title_pattern: str) -> List:
    """
    Filter documents by exact title matching.

    Args:
        docs: List of retrieved documents
        title_pattern: Pattern to match in document titles

    Returns:
        Filtered list of documents
    """
    if not title_pattern or not docs:
        logger.info(f"⚠️  No filtering: title_pattern={title_pattern}, docs={len(docs) if docs else 0}")
        return docs

    filtered = []
    pattern_upper = title_pattern.upper()

    logger.info(f"🔍 Filtering {len(docs)} docs for pattern: '{pattern_upper}'")

    for i, doc in enumerate(docs):
        # Check if document has metadata with title
        if hasattr(doc, 'metadata') and 'title' in doc.metadata:
            doc_title = doc.metadata['title'].upper()
            logger.info(f"   Doc {i+1}: '{doc_title}'")

            # Exact match or contains match
            if pattern_upper in doc_title or doc_title in pattern_upper:
                filtered.append(doc)
                logger.info(f"      ✅ MATCH!")
            else:
                logger.info(f"      ❌ No match")
        else:
            logger.info(f"   Doc {i+1}: No metadata or title")

    if filtered:
        logger.info(f"✅ Filtered: {len(docs)} docs → {len(filtered)} docs")
        return filtered
    else:
        logger.warning(f"⚠️  No matches found, returning all {len(docs)} docs")
        return docs  # Return original if no matches found
