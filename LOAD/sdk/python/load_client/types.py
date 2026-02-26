"""Pydantic models for LOAD API entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Organization(BaseModel):
    id: str
    name: str
    slug: str
    plan: Literal["FREE", "PRO", "ENTERPRISE"] = "FREE"
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


class User(BaseModel):
    id: str
    email: str
    name: str
    role: Literal["OWNER", "ADMIN", "MEMBER"]

    model_config = {"populate_by_name": True}


class AssistantModel(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4"
    temperature: float | None = None
    max_tokens: int | None = Field(None, alias="maxTokens")
    system_prompt: str | None = Field(None, alias="systemPrompt")

    model_config = {"populate_by_name": True}


class AssistantVoice(BaseModel):
    provider: str = "openai"
    voice_id: str = Field("alloy", alias="voiceId")
    speed: float | None = None

    model_config = {"populate_by_name": True}


class AssistantTranscriber(BaseModel):
    provider: str = "openai"
    model: str = "whisper-1"
    language: str = "en"

    model_config = {"populate_by_name": True}


class Assistant(BaseModel):
    id: str
    organization_id: str = Field(alias="organizationId")
    name: str
    model: AssistantModel
    voice: AssistantVoice
    transcriber: AssistantTranscriber
    first_message: str | None = Field(None, alias="firstMessage")
    end_call_message: str | None = Field(None, alias="endCallMessage")
    end_call_phrases: list[str] = Field(default_factory=list, alias="endCallPhrases")
    metadata: dict[str, Any] | None = None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


class Call(BaseModel):
    id: str
    organization_id: str = Field(alias="organizationId")
    assistant_id: str = Field(alias="assistantId")
    type: Literal["WEB", "INBOUND", "OUTBOUND"]
    status: Literal["QUEUED", "RINGING", "IN_PROGRESS", "ENDED", "FAILED"]
    phone_number_id: str | None = Field(None, alias="phoneNumberId")
    customer_number: str | None = Field(None, alias="customerNumber")
    started_at: datetime | None = Field(None, alias="startedAt")
    ended_at: datetime | None = Field(None, alias="endedAt")
    duration: int | None = None
    end_reason: str | None = Field(None, alias="endReason")
    transcript: Any | None = None
    recording_url: str | None = Field(None, alias="recordingUrl")
    cost: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime = Field(alias="createdAt")

    model_config = {"populate_by_name": True}


class PhoneNumber(BaseModel):
    id: str
    organization_id: str = Field(alias="organizationId")
    number: str
    twilio_sid: str | None = Field(None, alias="twilioSid")
    assistant_id: str | None = Field(None, alias="assistantId")
    name: str | None = None
    provider: str = "TWILIO"
    status: str = "ACTIVE"
    metadata: dict[str, Any] | None = None
    created_at: datetime = Field(alias="createdAt")

    model_config = {"populate_by_name": True}


class SquadMember(BaseModel):
    assistant_id: str = Field(alias="assistantId")
    transfer_conditions: list[dict[str, Any]] = Field(
        default_factory=list, alias="transferConditions"
    )

    model_config = {"populate_by_name": True}


class Squad(BaseModel):
    id: str
    organization_id: str = Field(alias="organizationId")
    name: str
    members: list[SquadMember]
    metadata: dict[str, Any] | None = None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


class Tool(BaseModel):
    id: str
    organization_id: str = Field(alias="organizationId")
    type: Literal["FUNCTION", "TRANSFER_CALL", "END_CALL"] = "FUNCTION"
    name: str
    description: str | None = None
    function: dict[str, Any] | None = None
    server_url: str | None = Field(None, alias="serverUrl")
    metadata: dict[str, Any] | None = None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


class Campaign(BaseModel):
    id: str
    organization_id: str = Field(alias="organizationId")
    name: str
    assistant_id: str = Field(alias="assistantId")
    phone_number_id: str = Field(alias="phoneNumberId")
    status: Literal["DRAFT", "RUNNING", "PAUSED", "COMPLETED"] = "DRAFT"
    contacts: list[dict[str, Any]] = Field(default_factory=list)
    schedule: dict[str, Any] | None = None
    stats: dict[str, Any] | None = None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


class Webhook(BaseModel):
    id: str
    organization_id: str = Field(alias="organizationId")
    url: str
    events: list[str]
    secret: str
    active: bool = True
    created_at: datetime = Field(alias="createdAt")

    model_config = {"populate_by_name": True}
