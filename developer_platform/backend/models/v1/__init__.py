"""
API v1 Models

These models define the stable public API contract for v1.
"""

from .vapi_models import (
    # Request models
    CreateAssistantRequest,
    UpdateAssistantRequest,
    InitiateCallRequest,
    # Response models
    AssistantResponse,
    CallResponse,
    ListAssistantsResponse,
    ListCallsResponse,
    ErrorResponse,
    ErrorDetail,
    # Enums
    CallTypeEnum,
    VoiceProvider,
)

from .n8n_models import (
    # Request models
    CreateWorkflowRequest,
    UpdateWorkflowRequest,
    ExecuteWorkflowRequest,
    # Response models
    WorkflowResponse,
    ExecutionResponse,
    ListWorkflowsResponse,
    ListExecutionsResponse,
    # Enums
    WorkflowStatus,
    ExecutionStatus,
)

__all__ = [
    # Vapi models
    "CreateAssistantRequest",
    "UpdateAssistantRequest",
    "InitiateCallRequest",
    "AssistantResponse",
    "CallResponse",
    "ListAssistantsResponse",
    "ListCallsResponse",
    "ErrorResponse",
    "ErrorDetail",
    "CallTypeEnum",
    "VoiceProvider",
    # n8n models
    "CreateWorkflowRequest",
    "UpdateWorkflowRequest",
    "ExecuteWorkflowRequest",
    "WorkflowResponse",
    "ExecutionResponse",
    "ListWorkflowsResponse",
    "ListExecutionsResponse",
    "WorkflowStatus",
    "ExecutionStatus",
]
