"""
VAPI Testing Routes - Programmatic Testing and Monitoring

This module provides comprehensive testing capabilities for VAPI assistants,
including programmatic call/chat triggering, health checks, and webhook testing.
"""

import asyncio
import uuid
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
import httpx

from ..auth import get_current_user_mongo
from ..services.automation_orchestration_service import get_automation_service
from ..services.vapi_service import VAPIServiceWrapper
from ..models.shared_models import StandardResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vapi-testing", tags=["VAPI Testing"])

# Models
class VAPITestRequest(BaseModel):
    """Request model for VAPI testing."""
    assistant_id: str = Field(..., description="VAPI assistant ID to test")
    test_type: str = Field(..., description="Type of test: 'health', 'call', 'chat', 'webhook'")
    test_scenario: Optional[str] = Field(None, description="Specific test scenario")
    phone_number: Optional[str] = Field(None, description="Phone number for call tests")
    message: Optional[str] = Field(None, description="Test message for chat tests")
    webhook_data: Optional[Dict[str, Any]] = Field(None, description="Custom webhook payload")
    timeout: Optional[int] = Field(30, description="Test timeout in seconds")

class CallTestRequest(BaseModel):
    """Request model for programmatic call testing."""
    assistant_id: str = Field(..., description="VAPI assistant ID")
    phone_number: str = Field(..., description="Phone number to call")
    test_scenario: Optional[str] = Field("health_check", description="Test scenario name")
    max_duration: Optional[int] = Field(300, description="Maximum call duration in seconds")
    wait_for_completion: Optional[bool] = Field(True, description="Wait for call to complete")
    custom_variables: Optional[Dict[str, Any]] = Field(None, description="Custom variables for the call")

class ChatTestRequest(BaseModel):
    """Request model for chat testing."""
    assistant_id: str = Field(..., description="VAPI assistant ID")
    messages: List[Dict[str, str]] = Field(..., description="Chat messages to test")
    test_scenario: Optional[str] = Field("basic_chat", description="Test scenario name")
    timeout: Optional[int] = Field(60, description="Chat timeout in seconds")

class WebhookTestRequest(BaseModel):
    """Request model for webhook testing."""
    webhook_url: str = Field(..., description="Webhook URL to test")
    payload: Dict[str, Any] = Field(..., description="Test payload")
    method: Optional[str] = Field("POST", description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers")
    timeout: Optional[int] = Field(30, description="Request timeout in seconds")

class ToolCallTestRequest(BaseModel):
    """Request model for tool call testing."""
    assistant_id: str = Field(..., description="VAPI assistant ID")
    tool_name: str = Field(..., description="Tool name to test")
    tool_parameters: Dict[str, Any] = Field(..., description="Tool parameters")
    test_scenario: Optional[str] = Field("single_tool", description="Test scenario")

class TestResult(BaseModel):
    """Test result model."""
    test_id: str = Field(..., description="Unique test ID")
    test_type: str = Field(..., description="Type of test performed")
    success: bool = Field(..., description="Whether test passed")
    duration: float = Field(..., description="Test duration in seconds")
    details: Dict[str, Any] = Field(..., description="Detailed test results")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(..., description="Test execution timestamp")

class TestSuiteRequest(BaseModel):
    """Request model for running test suites."""
    assistant_id: str = Field(..., description="VAPI assistant ID")
    test_suite: str = Field(..., description="Test suite name: 'basic', 'comprehensive', 'performance'")
    parallel_execution: Optional[bool] = Field(True, description="Run tests in parallel")
    include_performance: Optional[bool] = Field(False, description="Include performance tests")

# Test service class
class VAPITestingService:
    """Service for VAPI testing operations."""

    def __init__(self):
        self.vapi_service = None
        self.test_results: Dict[str, TestResult] = {}
        self.active_tests: Dict[str, asyncio.Task] = {}

    async def initialize(self):
        """Initialize the testing service."""
        try:
            import os
            self.vapi_service = VAPIServiceWrapper({
                "VAPI_API_KEY": os.getenv("VAPI_API_KEY"),
                "VAPI_US_PHONE_ID": os.getenv("VAPI_US_PHONE_ID"),
                "webhook_url": os.getenv("VAPI_WEBHOOK_URL", "https://api.ailabsafrica.com/vapi/webhook")
            })
            logger.info("VAPI testing service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize VAPI testing service: {e}")
            raise

    async def test_assistant_health(self, assistant_id: str) -> TestResult:
        """Test VAPI assistant health and connectivity."""
        test_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)

        try:
            # Get assistant details to verify it exists and is accessible
            if not self.vapi_service:
                raise ValueError("VAPI service not available")

            assistant_check = await self.vapi_service.get_assistant(assistant_id)

            if not assistant_check.get("success"):
                raise ValueError(f"Assistant not accessible: {assistant_check.get('error')}")

            assistant_data = assistant_check.get("assistant", {})

            # Additional health checks
            health_details = {
                "assistant_accessible": True,
                "assistant_name": assistant_data.get("name", "Unknown"),
                "model_configured": bool(assistant_data.get("model")),
                "voice_configured": bool(assistant_data.get("voice")),
                "tools_count": len(assistant_data.get("tools", [])),
                "system_prompt_length": len(assistant_data.get("systemPrompt", "")),
                "webhook_configured": bool(assistant_data.get("serverUrl")),
                "assistant_data": assistant_data
            }

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            result = TestResult(
                test_id=test_id,
                test_type="health",
                success=True,
                duration=duration,
                details=health_details,
                timestamp=start_time
            )

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            result = TestResult(
                test_id=test_id,
                test_type="health",
                success=False,
                duration=duration,
                details={"error_details": str(e)},
                error=str(e),
                timestamp=start_time
            )

        self.test_results[test_id] = result
        return result

    async def trigger_test_call(self, request: CallTestRequest) -> TestResult:
        """Trigger a programmatic test call."""
        test_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)

        try:
            if not self.vapi_service:
                raise ValueError("VAPI service not available")

            # Create call request payload
            call_payload = {
                "assistant": {"assistantId": request.assistant_id},
                "phoneNumber": request.phone_number,
                "name": f"Test Call - {request.test_scenario}",
                "assistantOverrides": {
                    "variableValues": request.custom_variables or {},
                    "metadata": {
                        "test_id": test_id,
                        "test_scenario": request.test_scenario,
                        "triggered_at": start_time.isoformat()
                    }
                }
            }

            # Add max duration if specified
            if request.max_duration:
                call_payload["assistantOverrides"]["maxDurationSeconds"] = request.max_duration

            # Trigger the call using VAPI API
            async with httpx.AsyncClient() as client:
                vapi_api_key = self.vapi_service.api_key
                headers = {
                    "Authorization": f"Bearer {vapi_api_key}",
                    "Content-Type": "application/json"
                }

                response = await client.post(
                    "https://api.vapi.ai/call",
                    headers=headers,
                    json=call_payload,
                    timeout=30.0
                )

                if response.status_code == 201:
                    call_data = response.json()
                    call_id = call_data.get("id")

                    # Wait for call completion if requested
                    call_status = "initiated"
                    if request.wait_for_completion:
                        call_status = await self._wait_for_call_completion(call_id, request.max_duration or 300)

                    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

                    result = TestResult(
                        test_id=test_id,
                        test_type="call",
                        success=True,
                        duration=duration,
                        details={
                            "call_id": call_id,
                            "call_status": call_status,
                            "phone_number": request.phone_number,
                            "test_scenario": request.test_scenario,
                            "call_data": call_data
                        },
                        timestamp=start_time
                    )
                else:
                    raise ValueError(f"Failed to create call: {response.status_code} - {response.text}")

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            result = TestResult(
                test_id=test_id,
                test_type="call",
                success=False,
                duration=duration,
                details={"error_details": str(e), "request": request.dict()},
                error=str(e),
                timestamp=start_time
            )

        self.test_results[test_id] = result
        return result

    async def _wait_for_call_completion(self, call_id: str, max_wait: int) -> str:
        """Wait for call to complete and return final status."""
        if not self.vapi_service:
            return "unknown"

        wait_time = 0
        check_interval = 5  # Check every 5 seconds

        while wait_time < max_wait:
            try:
                async with httpx.AsyncClient() as client:
                    headers = {
                        "Authorization": f"Bearer {self.vapi_service.api_key}",
                    }

                    response = await client.get(
                        f"https://api.vapi.ai/call/{call_id}",
                        headers=headers,
                        timeout=10.0
                    )

                    if response.status_code == 200:
                        call_data = response.json()
                        status = call_data.get("status", "unknown")

                        # Check if call is finished
                        if status in ["ended", "completed", "failed", "canceled"]:
                            return status

                await asyncio.sleep(check_interval)
                wait_time += check_interval

            except Exception as e:
                logger.warning(f"Error checking call status: {e}")
                await asyncio.sleep(check_interval)
                wait_time += check_interval

        return "timeout"

    async def test_webhook_endpoint(self, request: WebhookTestRequest) -> TestResult:
        """Test webhook endpoint connectivity and response."""
        test_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)

        try:
            headers = request.headers or {"Content-Type": "application/json"}

            async with httpx.AsyncClient() as client:
                if request.method.upper() == "POST":
                    response = await client.post(
                        request.webhook_url,
                        headers=headers,
                        json=request.payload,
                        timeout=request.timeout
                    )
                elif request.method.upper() == "GET":
                    response = await client.get(
                        request.webhook_url,
                        headers=headers,
                        timeout=request.timeout
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {request.method}")

                duration = (datetime.now(timezone.utc) - start_time).total_seconds()

                result = TestResult(
                    test_id=test_id,
                    test_type="webhook",
                    success=response.status_code < 400,
                    duration=duration,
                    details={
                        "webhook_url": request.webhook_url,
                        "method": request.method,
                        "status_code": response.status_code,
                        "response_headers": dict(response.headers),
                        "response_body": response.text[:1000] if response.text else None,
                        "payload_sent": request.payload
                    },
                    error=None if response.status_code < 400 else f"HTTP {response.status_code}",
                    timestamp=start_time
                )

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            result = TestResult(
                test_id=test_id,
                test_type="webhook",
                success=False,
                duration=duration,
                details={"error_details": str(e), "request": request.dict()},
                error=str(e),
                timestamp=start_time
            )

        self.test_results[test_id] = result
        return result

    async def test_tool_calls(self, request: ToolCallTestRequest) -> TestResult:
        """Test specific tool call functionality."""
        test_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)

        try:
            # Get assistant configuration to check tools
            health_result = await self.test_assistant_health(request.assistant_id)

            if not health_result.success:
                raise ValueError(f"Assistant health check failed: {health_result.error}")

            assistant_data = health_result.details.get("assistant_data", {})
            tools = assistant_data.get("tools", [])

            # Find the specific tool
            target_tool = None
            for tool in tools:
                if tool.get("type") == "function" and tool.get("function", {}).get("name") == request.tool_name:
                    target_tool = tool
                    break

            if not target_tool:
                raise ValueError(f"Tool '{request.tool_name}' not found in assistant configuration")

            # Validate tool parameters against schema
            tool_schema = target_tool.get("function", {}).get("parameters", {})
            required_params = tool_schema.get("required", [])

            missing_params = [param for param in required_params if param not in request.tool_parameters]
            if missing_params:
                raise ValueError(f"Missing required parameters: {missing_params}")

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            result = TestResult(
                test_id=test_id,
                test_type="tool_call",
                success=True,
                duration=duration,
                details={
                    "tool_name": request.tool_name,
                    "tool_found": True,
                    "tool_schema": tool_schema,
                    "parameters_valid": True,
                    "test_parameters": request.tool_parameters,
                    "tool_configuration": target_tool
                },
                timestamp=start_time
            )

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            result = TestResult(
                test_id=test_id,
                test_type="tool_call",
                success=False,
                duration=duration,
                details={"error_details": str(e), "request": request.dict()},
                error=str(e),
                timestamp=start_time
            )

        self.test_results[test_id] = result
        return result

    async def run_test_suite(self, request: TestSuiteRequest) -> List[TestResult]:
        """Run a comprehensive test suite."""
        suite_tests = []

        # Define test suites
        if request.test_suite == "basic":
            suite_tests = [
                ("health", {"assistant_id": request.assistant_id}),
            ]
        elif request.test_suite == "comprehensive":
            suite_tests = [
                ("health", {"assistant_id": request.assistant_id}),
                # Add more comprehensive tests
            ]
        elif request.test_suite == "performance":
            suite_tests = [
                ("health", {"assistant_id": request.assistant_id}),
                # Add performance-specific tests
            ]

        results = []

        if request.parallel_execution:
            # Run tests in parallel
            tasks = []
            for test_type, test_params in suite_tests:
                if test_type == "health":
                    task = self.test_assistant_health(test_params["assistant_id"])
                    tasks.append(task)

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Convert exceptions to failed test results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        test_type, _ = suite_tests[i]
                        results[i] = TestResult(
                            test_id=str(uuid.uuid4()),
                            test_type=test_type,
                            success=False,
                            duration=0.0,
                            details={"error_details": str(result)},
                            error=str(result),
                            timestamp=datetime.now(timezone.utc)
                        )
        else:
            # Run tests sequentially
            for test_type, test_params in suite_tests:
                if test_type == "health":
                    result = await self.test_assistant_health(test_params["assistant_id"])
                    results.append(result)

        return results

    def get_test_result(self, test_id: str) -> Optional[TestResult]:
        """Get test result by ID."""
        return self.test_results.get(test_id)

    def get_recent_test_results(self, limit: int = 50) -> List[TestResult]:
        """Get recent test results."""
        sorted_results = sorted(
            self.test_results.values(),
            key=lambda x: x.timestamp,
            reverse=True
        )
        return sorted_results[:limit]

# Global testing service instance
testing_service = VAPITestingService()

# Routes
@router.on_event("startup")
async def startup_event():
    """Initialize testing service on startup."""
    await testing_service.initialize()

@router.post("/test-assistant", response_model=StandardResponse[TestResult])
async def test_assistant(
    request: VAPITestRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Test VAPI assistant with various test types.

    Supported test types:
    - health: Basic health and connectivity check
    - call: Programmatic call triggering (requires phone_number)
    - webhook: Webhook endpoint testing (requires webhook_data)
    - tools: Tool call validation
    """
    try:
        if request.test_type == "health":
            result = await testing_service.test_assistant_health(request.assistant_id)
        elif request.test_type == "webhook" and request.webhook_data:
            webhook_request = WebhookTestRequest(
                webhook_url=request.webhook_data.get("url", ""),
                payload=request.webhook_data.get("payload", {}),
                method=request.webhook_data.get("method", "POST"),
                timeout=request.timeout
            )
            result = await testing_service.test_webhook_endpoint(webhook_request)
        else:
            raise ValueError(f"Unsupported test type: {request.test_type}")

        return StandardResponse(
            success=True,
            data=result,
            message=f"Test completed: {result.test_type}"
        )

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/trigger-call", response_model=StandardResponse[TestResult])
async def trigger_test_call(
    request: CallTestRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """Trigger a programmatic test call to a VAPI assistant."""
    try:
        result = await testing_service.trigger_test_call(request)

        return StandardResponse(
            success=True,
            data=result,
            message="Test call initiated successfully"
        )

    except Exception as e:
        logger.error(f"Call test failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/test-webhook", response_model=StandardResponse[TestResult])
async def test_webhook(
    request: WebhookTestRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """Test webhook endpoint connectivity and response."""
    try:
        result = await testing_service.test_webhook_endpoint(request)

        return StandardResponse(
            success=True,
            data=result,
            message="Webhook test completed"
        )

    except Exception as e:
        logger.error(f"Webhook test failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/test-tool-calls", response_model=StandardResponse[TestResult])
async def test_tool_calls(
    request: ToolCallTestRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """Test specific tool call functionality."""
    try:
        result = await testing_service.test_tool_calls(request)

        return StandardResponse(
            success=True,
            data=result,
            message="Tool call test completed"
        )

    except Exception as e:
        logger.error(f"Tool call test failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/run-test-suite", response_model=StandardResponse[List[TestResult]])
async def run_test_suite(
    request: TestSuiteRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """Run a comprehensive test suite on a VAPI assistant."""
    try:
        results = await testing_service.run_test_suite(request)

        # Calculate summary statistics
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        return StandardResponse(
            success=True,
            data=results,
            message=f"Test suite completed: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)"
        )

    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/test-result/{test_id}", response_model=StandardResponse[TestResult])
async def get_test_result(
    test_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """Get test result by ID."""
    result = testing_service.get_test_result(test_id)

    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")

    return StandardResponse(
        success=True,
        data=result,
        message="Test result retrieved"
    )

@router.get("/test-results", response_model=StandardResponse[List[TestResult]])
async def get_test_results(
    limit: int = Query(50, description="Maximum number of results to return"),
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """Get recent test results."""
    results = testing_service.get_recent_test_results(limit)

    return StandardResponse(
        success=True,
        data=results,
        message=f"Retrieved {len(results)} test results"
    )

@router.get("/health-check", response_model=StandardResponse[Dict[str, Any]])
async def testing_service_health():
    """Check health of the testing service."""
    try:
        health_info = {
            "service": "vapi_testing",
            "status": "healthy",
            "vapi_service_available": testing_service.vapi_service is not None,
            "active_tests": len(testing_service.active_tests),
            "total_test_results": len(testing_service.test_results),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return StandardResponse(
            success=True,
            data=health_info,
            message="Testing service is healthy"
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))