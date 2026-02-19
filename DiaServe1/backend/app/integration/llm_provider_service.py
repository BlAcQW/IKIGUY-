"""
LLM Provider Service (Stub) for EstateFlow.

Document generation AI features are deferred. This module provides
a stub implementation so that document_service.py does not crash on import.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class LLMProviderService:
    """
    Stub LLM provider service for AI-powered document template generation.

    The generate_template_with_ai method in DocumentService already uses
    mock logic, so this class is only needed to prevent import errors.
    """

    def __init__(self, **kwargs):
        logger.info("LLMProviderService initialized (stub mode)")

    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using LLM. (Not yet implemented)"""
        raise NotImplementedError(
            "LLM document generation not yet implemented. "
            "DocumentService uses mock templates instead."
        )
