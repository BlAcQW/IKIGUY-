"""Twi translation service for testing."""

class TranslationService:
    """Mock Twi translation service."""

    def translate(self, text: str) -> str:
        """Pretend to translate text into Twi."""
        return f"twi:{text}"
