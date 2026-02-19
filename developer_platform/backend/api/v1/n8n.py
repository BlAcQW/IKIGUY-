"""
n8n API v1 Endpoints

Public, versioned, stable API for n8n workflow operations.

**Version:** 1.0.0
**Stability:** Stable - no breaking changes allowed
**Rate Limits:** 10 requests/minute (Free tier)
**Authentication:** API Key required (X-API-Key header)

Breaking changes require releasing v2.
"""

import sys
import os
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse

# Add core_backend to path for n8n service
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../core_backend/backend'))
from services.n8n_service import N8NService

# Import v1 models
from ...models.v1 import (
    CreateWorkflowRequest,
    UpdateWorkflowRequest,
    ExecuteWorkflowRequest,
    WorkflowResponse,
    ExecutionResponse,
    ListWorkflowsResponse,
    ListExecutionsResponse,
)

# Import middleware
from ...middleware.api_key_auth import verify_api_key
from ...middleware.rate_limiter import get_rate_limit_dependency
from ...middleware.usage_tracker import usage_tracker

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/workflows",
    tags=["Workflows v1"],
    responses={
        401: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    }
)

# Helper function to get n8n service
def get_n8n_service() -> N8NService:
    """Get n8n service instance."""
    return N8NService(
        n8n_api_url=os.getenv("N8N_API_URL", "https://automate.inspirecreations.it.com"),
        n8n_api_key=os.getenv("N8N_API_KEY")
    )


@router.post(
    "/",
    response_model=WorkflowResponse,
    status_code=201,
    summary="Create workflow",
    description="""
    Create a new n8n workflow with specified configuration.

    **Rate Limit:** 10 requests/minute
    **Cost:** 1 credit per workflow

    **Example Request:**
    ```json
    {
        "name": "Customer Onboarding",
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
        "active": false
    }
    ```

    **Example Response:**
    ```json
    {
        "id": "wf_123abc",
        "name": "Customer Onboarding",
        "active": false,
        "created_at": "2025-10-23T12:00:00Z",
        "webhook_url": "https://automate.example.com/webhook/customer-signup"
    }
    ```

    **Error Codes:**
    - `400` - Invalid request (e.g., invalid nodes configuration)
    - `401` - Invalid API key
    - `429` - Rate limit exceeded or quota exceeded
    - `500` - Internal server error
    """,
    response_description="Successfully created workflow"
)
async def create_workflow(
    request: CreateWorkflowRequest,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """
    Create a new n8n workflow.

    This endpoint creates an n8n workflow with the specified configuration.
    The workflow can be activated after creation.
    """
    try:
        logger.info(f"Creating workflow: {request.name}")

        # Usage tracking handled automatically by middleware

        # Get n8n service
        n8n_service = get_n8n_service()

        # Prepare workflow data
        workflow_data = {
            "name": request.name,
            "nodes": request.nodes,
            "connections": request.connections,
            "active": request.active,
            "settings": request.settings or {},
            "tags": request.tags or []
        }

        # Create workflow using n8n service
        result = await n8n_service.create_workflow(workflow_data)

        if not result.get("success"):
            error_msg = result.get("error", "Failed to create workflow")
            logger.error(f"Workflow creation failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "CREATION_FAILED",
                        "message": error_msg
                    },
                    "request_id": f"req_{datetime.utcnow().timestamp()}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        # Convert to stable v1 response
        response = WorkflowResponse.from_n8n_response(result)

        logger.info(f"Workflow created successfully: {response.id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred"
                },
                "request_id": f"req_{datetime.utcnow().timestamp()}",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/",
    response_model=ListWorkflowsResponse,
    summary="List workflows",
    description="""
    Retrieve a list of your workflows with pagination.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Query Parameters:**
    - `limit`: Maximum number of workflows to return (1-100, default: 10)
    - `offset`: Number of workflows to skip (default: 0)

    **Example Response:**
    ```json
    {
        "workflows": [
            {
                "id": "wf_123",
                "name": "Customer Onboarding",
                "active": true,
                "created_at": "2025-10-23T12:00:00Z",
                "tags": ["customer"]
            }
        ],
        "total": 1,
        "limit": 10,
        "offset": 0
    }
    ```
    """,
    response_description="List of workflows"
)
async def list_workflows(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of workflows to return"),
    offset: int = Query(0, ge=0, description="Number of workflows to skip"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """List all workflows with pagination."""
    try:
        logger.info(f"Listing workflows (limit: {limit}, offset: {offset})")

        # Get workflows from N8N service
        n8n_service = get_n8n_service()
        result = await n8n_service.get_workflows(limit=limit + offset)

        # Extract workflows and apply pagination
        all_workflows = result.get("data", [])
        paginated_workflows = all_workflows[offset:offset + limit]

        # Convert to response models
        workflows = []
        for wf_data in paginated_workflows:
            workflows.append(WorkflowResponse(
                id=wf_data.get("id"),
                name=wf_data.get("name", "Untitled Workflow"),
                active=wf_data.get("active", False),
                created_at=wf_data.get("createdAt"),
                updated_at=wf_data.get("updatedAt"),
                tags=wf_data.get("tags", [])
            ))

        return ListWorkflowsResponse(
            workflows=workflows,
            total=len(all_workflows),
            limit=limit,
            offset=offset
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing workflows: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Get workflow",
    description="""
    Retrieve details of a specific workflow by ID.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Path Parameters:**
    - `workflow_id`: The workflow ID to retrieve

    **Example Response:**
    ```json
    {
        "id": "wf_123abc",
        "name": "Customer Onboarding",
        "active": true,
        "created_at": "2025-10-23T12:00:00Z",
        "webhook_url": "https://automate.example.com/webhook/customer-signup"
    }
    ```
    """,
    response_description="Workflow details"
)
async def get_workflow(
    workflow_id: str = Path(..., description="Workflow ID"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Get workflow details by ID."""
    try:
        logger.info(f"Getting workflow: {workflow_id}")

        # Get n8n service
        n8n_service = get_n8n_service()

        # Get workflow status
        result = await n8n_service.get_workflow_status(workflow_id)

        if not result:
            logger.error(f"Workflow not found: {workflow_id}")
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Convert to stable v1 response
        return WorkflowResponse.from_n8n_response(result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Update workflow",
    description="""
    Update an existing workflow's configuration.

    Only provided fields will be updated. Omitted fields remain unchanged.

    **Rate Limit:** 10 requests/minute
    **Cost:** 1 credit per update

    **Example Request:**
    ```json
    {
        "name": "Updated Customer Onboarding",
        "active": true
    }
    ```
    """,
    response_description="Updated workflow"
)
async def update_workflow(
    request: UpdateWorkflowRequest,
    workflow_id: str = Path(..., description="Workflow ID"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Update workflow configuration."""
    try:
        logger.info(f"Updating workflow: {workflow_id}")

        # Usage tracking handled automatically by middleware

        # Get n8n service
        n8n_service = get_n8n_service()

        # Update workflow using n8n service
        result = await n8n_service.update_workflow_config(
            workflow_id=workflow_id,
            name=request.name,
            active=request.active,
            nodes=request.nodes,
            connections=request.connections,
            settings=request.settings,
            tags=request.tags
        )

        if not result.get("success"):
            error_msg = result.get("error", "Failed to update workflow")
            logger.error(f"Workflow update failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "UPDATE_FAILED",
                        "message": error_msg
                    },
                    "request_id": f"req_{datetime.utcnow().timestamp()}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        # Convert updated workflow to v1 response
        workflow_data = result.get("data", {})
        response = WorkflowResponse(
            id=workflow_data.get("id"),
            name=workflow_data.get("name", "Untitled Workflow"),
            active=workflow_data.get("active", False),
            created_at=workflow_data.get("createdAt"),
            updated_at=workflow_data.get("updatedAt"),
            tags=workflow_data.get("tags", [])
        )

        logger.info(f"Workflow updated successfully: {response.id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/{workflow_id}",
    status_code=204,
    summary="Delete workflow",
    description="""
    Delete a workflow permanently.

    **Warning:** This action cannot be undone.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Response:** 204 No Content on success
    """,
    response_description="Workflow deleted successfully"
)
async def delete_workflow(
    workflow_id: str = Path(..., description="Workflow ID"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Delete workflow by ID."""
    try:
        logger.info(f"Deleting workflow: {workflow_id}")

        # Get n8n service
        n8n_service = get_n8n_service()

        # Delete workflow
        success = await n8n_service.delete_workflow_by_id(workflow_id)

        if not success:
            logger.error(f"Failed to delete workflow: {workflow_id}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Workflow not found or could not be deleted"
                    },
                    "request_id": f"req_{datetime.utcnow().timestamp()}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        logger.info(f"Workflow deleted successfully: {workflow_id}")
        return JSONResponse(status_code=204, content=None)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/{workflow_id}/activate",
    response_model=WorkflowResponse,
    summary="Activate workflow",
    description="""
    Activate a workflow to start processing triggers.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free
    """,
    response_description="Workflow activated successfully"
)
async def activate_workflow(
    workflow_id: str = Path(..., description="Workflow ID"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Activate workflow."""
    try:
        logger.info(f"Activating workflow: {workflow_id}")

        # Get n8n service
        n8n_service = get_n8n_service()

        # Activate workflow
        success = await n8n_service.activate_workflow(workflow_id)

        if not success:
            logger.error(f"Failed to activate workflow: {workflow_id}")
            raise HTTPException(status_code=400, detail="Failed to activate workflow")

        # Get updated workflow status
        result = await n8n_service.get_workflow_status(workflow_id)
        return WorkflowResponse.from_n8n_response(result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error activating workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# EXECUTIONS ENDPOINTS
# ============================================================================

executions_router = APIRouter(
    prefix="/api/v1/executions",
    tags=["Executions v1"],
    responses={
        401: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    }
)


@executions_router.post(
    "/",
    response_model=ExecutionResponse,
    status_code=201,
    summary="Execute workflow",
    description="""
    Execute a workflow with optional input data.

    **Rate Limit:** 10 requests/minute
    **Cost:** Variable (based on workflow complexity and execution time)

    **Example Request:**
    ```json
    {
        "workflow_id": "wf_123abc",
        "data": {
            "customer_email": "user@example.com",
            "customer_name": "John Doe"
        }
    }
    ```

    **Example Response:**
    ```json
    {
        "id": "exec_789xyz",
        "workflow_id": "wf_123abc",
        "status": "success",
        "started_at": "2025-10-23T12:05:00Z",
        "finished_at": "2025-10-23T12:05:30Z",
        "duration": 30000,
        "success": true
    }
    ```
    """,
    response_description="Workflow executed successfully"
)
async def execute_workflow(
    workflow_id: str = Query(..., description="Workflow ID to execute"),
    request: ExecuteWorkflowRequest = ...,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Execute a workflow with input data."""
    try:
        logger.info(f"Executing workflow: {workflow_id}")

        # Usage tracking handled automatically by middleware

        # Get n8n service
        n8n_service = get_n8n_service()

        # Execute workflow
        result = await n8n_service.trigger_workflow(
            workflow_id=workflow_id,
            data=request.data or {}
        )

        if not result.get("success"):
            error_msg = result.get("error", "Failed to execute workflow")
            logger.error(f"Workflow execution failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

        # Convert to stable v1 response
        response = ExecutionResponse.from_n8n_response(result)

        logger.info(f"Workflow executed successfully: {response.id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error executing workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@executions_router.get(
    "/",
    response_model=ListExecutionsResponse,
    summary="List executions",
    description="""
    Retrieve workflow execution history with pagination.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Query Parameters:**
    - `workflow_id`: Filter by workflow ID (optional)
    - `limit`: Maximum number of executions to return (1-100, default: 10)
    - `offset`: Number of executions to skip (default: 0)
    """,
    response_description="List of executions"
)
async def list_executions(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of executions to return"),
    offset: int = Query(0, ge=0, description="Number of executions to skip"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """List execution history with pagination."""
    try:
        logger.info(f"Listing executions (workflow: {workflow_id}, limit: {limit}, offset: {offset})")

        # Get executions from N8N service
        n8n_service = get_n8n_service()
        result = await n8n_service.get_executions(
            workflow_id=workflow_id,
            limit=limit + offset
        )

        # Extract executions and apply pagination
        all_executions = result.get("data", [])
        paginated_executions = all_executions[offset:offset + limit]

        # Convert to response models
        executions = []
        for exec_data in paginated_executions:
            status = exec_data.get("status", "unknown")
            # Determine success based on status
            success = status in ["success", "running"]

            executions.append(ExecutionResponse(
                id=exec_data.get("id"),
                workflow_id=exec_data.get("workflowId"),
                status=status,
                started_at=exec_data.get("startedAt"),
                finished_at=exec_data.get("stoppedAt"),
                success=success
            ))

        return ListExecutionsResponse(
            executions=executions,
            total=len(all_executions),
            limit=limit,
            offset=offset
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing executions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@executions_router.get(
    "/{execution_id}",
    response_model=ExecutionResponse,
    summary="Get execution details",
    description="""
    Retrieve details of a specific workflow execution by ID.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free
    """,
    response_description="Execution details"
)
async def get_execution(
    execution_id: str = Path(..., description="Execution ID"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Get execution details by ID."""
    try:
        logger.info(f"Getting execution: {execution_id}")

        # Get n8n service
        n8n_service = get_n8n_service()

        # Get execution details
        exec_data = await n8n_service.get_execution_by_id(execution_id)

        if not exec_data:
            logger.warning(f"Execution not found: {execution_id}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Execution not found"
                    },
                    "request_id": f"req_{datetime.utcnow().timestamp()}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        # Convert to ExecutionResponse
        status = exec_data.get("status", "unknown")
        success = status in ["success", "running"]

        response = ExecutionResponse(
            id=exec_data.get("id"),
            workflow_id=exec_data.get("workflowId"),
            status=status,
            started_at=exec_data.get("startedAt"),
            finished_at=exec_data.get("stoppedAt"),
            success=success
        )

        logger.info(f"Retrieved execution: {execution_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# Export both routers
__all__ = ["router", "executions_router"]
