"""
Base adapter for tool-specific location processing behavior

Defines the interface for customizing location processing
behavior for different tools and use cases.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

from ..database.models import LocationResult, ToolContext, LanguageContext
from ..core_service import GhanaianLocationService

logger = logging.getLogger(__name__)


class BaseLocationAdapter(ABC):
    """
    Abstract base class for tool-specific location adapters

    Allows customization of location processing behavior while
    maintaining consistent API across different tools.
    """

    def __init__(self, location_service: GhanaianLocationService):
        """
        Initialize adapter with core location service

        Args:
            location_service: Core Ghanaian location service
        """
        self.location_service = location_service
        self.tool_context = self.get_tool_context()

    @abstractmethod
    def get_tool_context(self) -> ToolContext:
        """Get the tool context for this adapter"""
        pass

    async def process_location(self,
                             query: str,
                             additional_context: Optional[Dict[str, Any]] = None) -> LocationResult:
        """
        Process location with tool-specific customizations

        Args:
            query: Location query from user
            additional_context: Tool-specific context data

        Returns:
            LocationResult with tool-specific optimizations
        """
        # Pre-processing customization
        processed_query = await self.preprocess_query(query, additional_context)

        # Core location processing
        result = await self.location_service.process_location_query(
            query=processed_query,
            context=self.tool_context,
            language=self.get_language_preference(additional_context),
            include_pronunciation=self.should_include_pronunciation(additional_context),
            max_alternatives=self.get_max_alternatives(additional_context)
        )

        # Post-processing customization
        customized_result = await self.postprocess_result(result, additional_context)

        return customized_result

    async def optimize_response_text(self,
                                   response_text: str,
                                   additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Optimize response text with tool-specific pronunciation preferences

        Args:
            response_text: Original response text
            additional_context: Tool-specific context

        Returns:
            Optimized response text
        """
        # Apply tool-specific text preprocessing
        preprocessed_text = await self.preprocess_response_text(response_text, additional_context)

        # Core TTS optimization
        optimized_text = await self.location_service.optimize_response_for_tts(
            preprocessed_text, context=self.tool_context
        )

        # Apply tool-specific post-processing
        final_text = await self.postprocess_response_text(optimized_text, additional_context)

        return final_text

    # Abstract methods for customization

    async def preprocess_query(self,
                             query: str,
                             context: Optional[Dict[str, Any]] = None) -> str:
        """
        Preprocess query before location matching

        Override to implement tool-specific query preprocessing

        Args:
            query: Original query
            context: Tool-specific context

        Returns:
            Preprocessed query
        """
        return query

    async def postprocess_result(self,
                               result: LocationResult,
                               context: Optional[Dict[str, Any]] = None) -> LocationResult:
        """
        Postprocess result after location matching

        Override to implement tool-specific result customizations

        Args:
            result: Original location result
            context: Tool-specific context

        Returns:
            Customized location result
        """
        return result

    async def preprocess_response_text(self,
                                     text: str,
                                     context: Optional[Dict[str, Any]] = None) -> str:
        """
        Preprocess response text before TTS optimization

        Override to implement tool-specific text preprocessing

        Args:
            text: Original response text
            context: Tool-specific context

        Returns:
            Preprocessed text
        """
        return text

    async def postprocess_response_text(self,
                                      text: str,
                                      context: Optional[Dict[str, Any]] = None) -> str:
        """
        Postprocess response text after TTS optimization

        Override to implement tool-specific text postprocessing

        Args:
            text: TTS-optimized text
            context: Tool-specific context

        Returns:
            Final processed text
        """
        return text

    # Configuration methods

    def get_language_preference(self, context: Optional[Dict[str, Any]] = None) -> LanguageContext:
        """
        Get language preference for this tool

        Override to customize language handling

        Args:
            context: Tool-specific context

        Returns:
            Preferred language context
        """
        return LanguageContext.ENGLISH

    def should_include_pronunciation(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if pronunciation guidance should be included

        Override to customize pronunciation inclusion

        Args:
            context: Tool-specific context

        Returns:
            True if pronunciation should be included
        """
        return True

    def get_max_alternatives(self, context: Optional[Dict[str, Any]] = None) -> int:
        """
        Get maximum number of alternative matches to return

        Override to customize alternative count

        Args:
            context: Tool-specific context

        Returns:
            Maximum number of alternatives
        """
        return 3

    def get_confidence_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Get minimum confidence threshold for matches

        Override to customize confidence requirements

        Args:
            context: Tool-specific context

        Returns:
            Minimum confidence threshold (0.0-1.0)
        """
        return 0.6

    # Utility methods

    def extract_context_value(self,
                            context: Optional[Dict[str, Any]],
                            key: str,
                            default: Any = None) -> Any:
        """
        Safely extract value from context dictionary

        Args:
            context: Context dictionary
            key: Key to extract
            default: Default value if key not found

        Returns:
            Context value or default
        """
        if context is None:
            return default
        return context.get(key, default)

    async def record_tool_specific_feedback(self,
                                          original_query: str,
                                          result: LocationResult,
                                          user_feedback: Optional[str] = None,
                                          session_id: Optional[str] = None) -> bool:
        """
        Record tool-specific user feedback for learning

        Args:
            original_query: Original user query
            result: System result
            user_feedback: User correction or feedback
            session_id: Session identifier

        Returns:
            True if feedback was recorded successfully
        """
        try:
            if user_feedback and result.corrected_location:
                return await self.location_service.learn_from_user_correction(
                    original_query=original_query,
                    system_interpretation=result.corrected_location,
                    user_correction=user_feedback,
                    confidence_before=result.confidence,
                    context=self.tool_context,
                    session_id=session_id
                )
            return True
        except Exception as e:
            logger.error(f"Failed to record tool-specific feedback: {e}")
            return False