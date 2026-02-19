"""
Username generator service for InkWave.

Generates deterministic, nature-inspired usernames for anonymous users.
"""

import hashlib
from typing import Optional


# Nature-inspired adjectives for username generation
ADJECTIVES = [
    "peaceful", "winding", "gentle", "ancient", "wise", "serene", "quiet", "flowing",
    "bright", "calm", "deep", "soft", "steady", "kind", "noble", "graceful",
    "pure", "still", "sacred", "eternal", "mystic", "golden", "silver", "crimson",
    "emerald", "azure", "amber", "crystal", "radiant", "luminous", "tranquil", "harmonious",
    "blissful", "vibrant", "resilient", "mighty", "elegant", "sublime", "verdant", "celestial",
    "pristine", "boundless", "infinite", "tender", "loyal", "brave", "spirited", "warm",
    "cool", "misty"
]

# Nature-inspired nouns for username generation
NOUNS = [
    "river", "mountain", "forest", "ocean", "meadow", "valley", "lake", "stream",
    "oak", "willow", "pine", "cedar", "maple", "birch", "elm", "aspen",
    "cypress", "redwood", "bamboo", "lotus", "jasmine", "lily", "rose", "orchid",
    "fern", "moss", "vine", "sage", "thyme", "lavender", "brook", "creek",
    "pond", "falls", "canyon", "ridge", "peak", "summit", "grove", "glade",
    "dell", "hollow", "shore", "coast", "reef", "tide", "wave", "breeze",
    "mist", "dawn"
]


def generate_anonymous_username(user_id: str) -> str:
    """
    Generate a deterministic nature-inspired username from user_id.

    Uses SHA256 hash of user_id to select adjective and noun from predefined lists.
    Same user_id will always generate the same username.

    Args:
        user_id: User ID (typically a UUID string)

    Returns:
        Generated username in format "{adjective}_{noun}" (e.g., "winding_river")

    Examples:
        >>> generate_anonymous_username("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        'peaceful_mountain'
        >>> # Same input always returns same output
        >>> generate_anonymous_username("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        'peaceful_mountain'
    """
    if not user_id:
        # Fallback for empty user_id (shouldn't happen)
        return "mysterious_wanderer"

    # Use SHA256 for better distribution than built-in hash()
    # This ensures consistent results across Python restarts
    hash_bytes = hashlib.sha256(user_id.encode('utf-8')).digest()

    # Convert first 8 bytes to integer for adjective selection
    adjective_hash = int.from_bytes(hash_bytes[:8], byteorder='big')
    adjective_index = adjective_hash % len(ADJECTIVES)

    # Convert next 8 bytes to integer for noun selection
    noun_hash = int.from_bytes(hash_bytes[8:16], byteorder='big')
    noun_index = noun_hash % len(NOUNS)

    # Generate username
    username = f"{ADJECTIVES[adjective_index]}_{NOUNS[noun_index]}"

    return username


def get_display_username(user_data: dict) -> Optional[str]:
    """
    Get display username for a user, using their real username/display_name if set,
    or generating a nature-inspired one if not.

    Args:
        user_data: User document from MongoDB

    Returns:
        Username to display (real or generated), or None if user_id not found

    Examples:
        >>> get_display_username({"user_id": "abc123", "username": "john_doe"})
        'john_doe'
        >>> get_display_username({"user_id": "abc123", "display_name": "anointed_one"})
        'anointed_one'
        >>> get_display_username({"user_id": "abc123", "username": None, "display_name": None})
        'peaceful_mountain'  # (generated from user_id)
    """
    # Use real username if set (priority 1)
    if user_data.get("username"):
        return user_data["username"]

    # Use display_name if set (priority 2)
    if user_data.get("display_name"):
        return user_data["display_name"]

    # Generate anonymous username (priority 3)
    user_id = user_data.get("user_id")
    if not user_id:
        return None

    return generate_anonymous_username(user_id)
