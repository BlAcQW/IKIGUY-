"""Default English translation service."""

class TranslationService:
    """Mock English translation service used as fallback."""

    def translate(self, text: str) -> str:
        """Return the text with an English marker."""
        return f"en:{text}"
