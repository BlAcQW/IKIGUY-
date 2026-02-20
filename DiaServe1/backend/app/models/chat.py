"""
Chat models for EstateFlow AI Chat Agent.

Handles property-related chat interactions with AI-powered question answering.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Role of the message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class QuestionCategory(str, Enum):
    """Category of the question being asked."""
    LOCATION = "location"  # Schools, amenities, neighborhood
    FINANCIAL = "financial"  # Mortgage, costs, pricing
    PROPERTY_FEATURES = "property_features"  # Bedrooms, bathrooms, amenities
    PET_POLICY = "pet_policy"  # Pet-related questions
    NEIGHBORHOOD_SAFETY = "neighborhood_safety"  # Safety, crime, walkability
    AVAILABILITY = "availability"  # Viewing, tours, availability
    GENERAL = "general"  # Other questions


class ChatMessage(BaseModel):
    """Individual chat message."""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatRequest(BaseModel):
    """Request for chat interaction."""
    property_id: str = Field(..., description="ID of the property being discussed")
    message: str = Field(..., min_length=1, max_length=1000, description="User's question or message")
    conversation_history: List[ChatMessage] = Field(default_factory=list, description="Previous messages in conversation")
    language: str = Field(default="en", description="Language code (en, es, fr)")

    class Config:
        json_schema_extra = {
            "example": {
                "property_id": "6935c3128719492c9b42beee",
                "message": "Can I keep a dog in this property?",
                "conversation_history": [],
                "language": "en"
            }
        }


class Source(BaseModel):
    """Source attribution for the response."""
    type: str = Field(..., description="Type of source (property_data, calculation, etc.)")
    field: Optional[str] = Field(None, description="Specific field used from property data")
    value: Optional[Any] = Field(None, description="Value from the source")


class ChatResponse(BaseModel):
    """Response from chat interaction."""
    reply: str = Field(..., description="AI-generated reply to the user's question")
    sources: List[Source] = Field(default_factory=list, description="Sources used to generate the reply")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    question_category: QuestionCategory = Field(..., description="Detected category of the question")
    suggested_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    model_used: str = Field(..., description="LLM model used for generation")

    class Config:
        json_schema_extra = {
            "example": {
                "reply": "Yes! Pets are allowed in this property with approval and a $500 deposit.",
                "sources": [
                    {
                        "type": "property_data",
                        "field": "features.pet_policy",
                        "value": "allowed_with_deposit"
                    }
                ],
                "confidence": 0.95,
                "question_category": "pet_policy",
                "suggested_questions": [
                    "What is the pet deposit amount?",
                    "Are there any breed restrictions?",
                    "Is there a dog park nearby?"
                ],
                "processing_time_ms": 1250.5,
                "model_used": "gemini-2.0-flash-exp"
            }
        }


class ChatSession(BaseModel):
    """Persistent chat session."""
    id: str
    property_id: str
    property_name: Optional[str] = None
    user_id: Optional[str] = None
    organization_id: str
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatSessionListResponse(BaseModel):
    """Paginated list of chat sessions."""
    conversations: List[ChatSession]
    total: int
    limit: int
    offset: int
