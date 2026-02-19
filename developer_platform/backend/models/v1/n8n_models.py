"""
n8n API v1 Request and Response Models

These models define the public API contract for n8n workflow operations in v1.
IMPORTANT: Once deployed, these models are STABLE and cannot have breaking changes.

Stability Promise:
- Field names cannot change
- Field types cannot change
- Required fields cannot become optional (or vice versa)
- New optional fields can be added
- Response fields can be added but not removed
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    """Workflow status options."""
    ACTIVE = "active"
    INACTIVE = "inactive"


class ExecutionStatus(str, Enum):
    """Workflow execution status options."""
    SUCCESS = "success"
    ERROR = "error"
    RUNNING = "running"
    WAITING = "waiting"


# ============================================================================
# REQUEST MODELS
# ============================================================================

class CreateWorkflowRequest(BaseModel):
    """
    Request model for creating a workflow.

    Example:
        ```json
        {
            "name": "Customer Onboarding",
            "nodes": [...],
            "connections": {...},
            "active": false
        }
        ```
    """
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Workflow name (3-100 characters)"
    )
    nodes: List[Dict[str, Any]] = Field(
        ...,
        description="Workflow nodes configuration"
    )
    connections: Dict[str, Any] = Field(
        ...,
        description="Node connections configuration"
    )
    active: bool = Field(
        default=False,
        description="Whether workflow is active"
    )
    settings: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Workflow settings"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Workflow tags for categorization"
    )

    @validator('nodes')
    def validate_nodes(cls, v):
        """Validate nodes list."""
        if not v or len(v) == 0:
            raise ValueError("Workflow must have at least one node")
        if len(v) > 100:
            raise ValueError("Workflow cannot have more than 100 nodes")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Customer Onboarding Workflow",
                "nodes": [
                    {
                        "id": "webhook",
                        "type": "n8n-nodes-base.webhook",
                        "name": "Webhook",
                        "parameters": {
                            "path": "customer-signup"
                        }
                    }
                ],
                "connections": {},
                "active": False,
                "settings": {},
                "tags": ["customer", "onboarding"]
            }
        }


class UpdateWorkflowRequest(BaseModel):
    """
    Request model for updating a workflow.
    All fields are optional - only provided fields will be updated.
    """
    name: Optional[str] = Field(
        None,
        min_length=3,
        max_length=100,
        description="Updated workflow name"
    )
    nodes: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Updated nodes configuration"
    )
    connections: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated connections configuration"
    )
    active: Optional[bool] = Field(
        None,
        description="Updated active status"
    )
    settings: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated settings"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Updated tags"
    )


class ExecuteWorkflowRequest(BaseModel):
    """
    Request model for executing a workflow.

    Example:
        ```json
        {
            "data": {
                "customer_email": "user@example.com",
                "customer_name": "John Doe"
            }
        }
        ```
    """
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Input data for workflow execution"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "customer_email": "user@example.com",
                    "customer_name": "John Doe",
                    "plan": "professional"
                }
            }
        }


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class WorkflowResponse(BaseModel):
    """
    Response model for workflow operations.

    This is the stable response format for v1.
    """
    id: str = Field(..., description="Workflow ID")
    name: str = Field(..., description="Workflow name")
    active: bool = Field(..., description="Whether workflow is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    tags: Optional[List[str]] = Field(default=None, description="Workflow tags")
    webhook_url: Optional[str] = Field(None, description="Webhook URL (if workflow has webhook trigger)")

    @classmethod
    def from_n8n_response(cls, n8n_data: dict):
        """
        Convert N8NService response to stable v1 API response.

        Args:
            n8n_data: Response from core backend N8NService

        Returns:
            WorkflowResponse with stable v1 fields
        """
        return cls(
            id=n8n_data.get("workflow_id") or n8n_data.get("id"),
            name=n8n_data.get("workflow_name") or n8n_data.get("name"),
            active=n8n_data.get("enabled") or n8n_data.get("active", False),
            created_at=n8n_data.get("created_at") or datetime.utcnow(),
            updated_at=n8n_data.get("updated_at"),
            tags=n8n_data.get("tags", []),
            webhook_url=n8n_data.get("webhook_urls", [None])[0] if n8n_data.get("webhook_urls") else None
        )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "wf_123abc",
                "name": "Customer Onboarding",
                "active": True,
                "created_at": "2025-10-23T12:00:00Z",
                "updated_at": "2025-10-23T12:30:00Z",
                "tags": ["customer", "onboarding"],
                "webhook_url": "https://automate.example.com/webhook/customer-signup"
            }
        }


class ExecutionResponse(BaseModel):
    """Response model for workflow execution operations."""
    id: str = Field(..., description="Execution ID")
    workflow_id: str = Field(..., description="Workflow ID that was executed")
    status: ExecutionStatus = Field(..., description="Execution status")
    started_at: datetime = Field(..., description="Execution start time")
    finished_at: Optional[datetime] = Field(None, description="Execution end time")
    duration: Optional[int] = Field(None, description="Execution duration in milliseconds")
    success: bool = Field(..., description="Whether execution was successful")
    error: Optional[str] = Field(None, description="Error message if execution failed")

    @classmethod
    def from_n8n_response(cls, n8n_data: dict):
        """Convert N8NService execution response to v1 API response."""
        return cls(
            id=n8n_data.get("execution_id") or n8n_data.get("id", "unknown"),
            workflow_id=n8n_data.get("workflow_id", ""),
            status=ExecutionStatus(n8n_data.get("status", "success")),
            started_at=n8n_data.get("started_at") or datetime.utcnow(),
            finished_at=n8n_data.get("finished_at"),
            duration=n8n_data.get("duration"),
            success=n8n_data.get("success", True),
            error=n8n_data.get("error")
        )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "exec_789xyz",
                "workflow_id": "wf_123abc",
                "status": "success",
                "started_at": "2025-10-23T12:05:00Z",
                "finished_at": "2025-10-23T12:05:30Z",
                "duration": 30000,
                "success": True,
                "error": None
            }
        }


class ListWorkflowsResponse(BaseModel):
    """Response model for listing workflows."""
    workflows: List[WorkflowResponse] = Field(..., description="List of workflows")
    total: int = Field(..., description="Total number of workflows")
    limit: int = Field(..., description="Requested limit")
    offset: int = Field(..., description="Requested offset")

    class Config:
        json_schema_extra = {
            "example": {
                "workflows": [
                    {
                        "id": "wf_123",
                        "name": "Customer Onboarding",
                        "active": True,
                        "created_at": "2025-10-23T12:00:00Z",
                        "tags": ["customer"]
                    }
                ],
                "total": 1,
                "limit": 10,
                "offset": 0
            }
        }


class ListExecutionsResponse(BaseModel):
    """Response model for listing workflow executions."""
    executions: List[ExecutionResponse] = Field(..., description="List of executions")
    total: int = Field(..., description="Total number of executions")
    limit: int = Field(..., description="Requested limit")
    offset: int = Field(..., description="Requested offset")

    class Config:
        json_schema_extra = {
            "example": {
                "executions": [
                    {
                        "id": "exec_789",
                        "workflow_id": "wf_123",
                        "status": "success",
                        "started_at": "2025-10-23T12:05:00Z",
                        "finished_at": "2025-10-23T12:05:30Z",
                        "duration": 30000,
                        "success": True
                    }
                ],
                "total": 1,
                "limit": 10,
                "offset": 0
            }
        }
