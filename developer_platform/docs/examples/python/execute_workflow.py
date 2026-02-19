"""
Execute an n8n Workflow

This example demonstrates how to execute an n8n workflow.
"""

import os
import requests
import time
from typing import Dict, Any, Optional


# Configuration
API_KEY = os.getenv("KASAAI_API_KEY", "your_api_key_here")
BASE_URL = "https://developer.ailabsafrica.com"


def execute_workflow(
    workflow_id: str,
    data: Optional[Dict[str, Any]] = None
) -> Dict:
    """
    Execute an n8n workflow.

    Args:
        workflow_id: The workflow ID to execute
        data: Optional input data for the workflow

    Returns:
        Dict: Execution result with status and output

    Raises:
        requests.HTTPError: If the API request fails
    """
    endpoint = f"{BASE_URL}/api/v1/n8n/workflows/{workflow_id}/execute"

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {"data": data} if data else {}

    response = requests.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()


def get_execution_status(execution_id: str) -> Dict:
    """
    Get the status of a workflow execution.

    Args:
        execution_id: The execution ID

    Returns:
        Dict: Execution status object

    Raises:
        requests.HTTPError: If the API request fails
    """
    endpoint = f"{BASE_URL}/api/v1/n8n/executions/{execution_id}"

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()

    return response.json()


def list_executions(
    workflow_id: Optional[str] = None,
    limit: int = 10
) -> Dict:
    """
    List workflow executions.

    Args:
        workflow_id: Optional workflow ID to filter executions
        limit: Maximum number of executions to return

    Returns:
        Dict: List of execution objects

    Raises:
        requests.HTTPError: If the API request fails
    """
    endpoint = f"{BASE_URL}/api/v1/n8n/executions"

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    params = {"limit": limit}
    if workflow_id:
        params["workflow_id"] = workflow_id

    response = requests.get(endpoint, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def wait_for_execution(
    execution_id: str,
    max_wait: int = 60,
    check_interval: int = 2
) -> Dict:
    """
    Wait for a workflow execution to complete.

    Args:
        execution_id: The execution ID to monitor
        max_wait: Maximum seconds to wait (default: 60)
        check_interval: Seconds between checks (default: 2)

    Returns:
        Dict: Final execution status

    Raises:
        TimeoutError: If execution doesn't complete in time
    """
    start_time = time.time()

    while time.time() - start_time < max_wait:
        status = get_execution_status(execution_id)

        if status['finished']:
            return status

        if status.get('stoppedAt'):
            return status

        time.sleep(check_interval)

    raise TimeoutError(f"Execution {execution_id} did not complete in {max_wait} seconds")


def main():
    """Main function to demonstrate workflow execution."""
    workflow_id = os.getenv("WORKFLOW_ID")

    if not workflow_id:
        print("❌ Error: WORKFLOW_ID environment variable not set")
        print("   Set it with: export WORKFLOW_ID=your_workflow_id")
        exit(1)

    try:
        # Execute workflow with sample data
        print(f"🚀 Executing workflow: {workflow_id}")

        sample_data = {
            "customer_name": "John Doe",
            "email": "john@example.com",
            "message": "Hello from the API!"
        }

        execution = execute_workflow(
            workflow_id=workflow_id,
            data=sample_data
        )

        print("✅ Workflow execution started!")
        print(f"   Execution ID: {execution['id']}")
        print(f"   Status: {execution['status']}")
        print()

        # Wait for execution to complete
        print("⏳ Waiting for execution to complete...")
        final_status = wait_for_execution(execution['id'], max_wait=120)

        print("✅ Execution completed!")
        print(f"   Status: {final_status['status']}")
        print(f"   Finished: {final_status['finished']}")

        if 'data' in final_status:
            print(f"   Output: {final_status['data']}")

        # List recent executions for this workflow
        print(f"\n📋 Recent executions for workflow {workflow_id}:")
        executions = list_executions(workflow_id=workflow_id, limit=5)

        for exec_item in executions.get('executions', []):
            status_icon = "✅" if exec_item['finished'] else "⏳"
            print(f"{status_icon} {exec_item['id']} - {exec_item['status']} - {exec_item['startedAt']}")

    except TimeoutError as e:
        print(f"⏱️  {e}")
        exit(1)
    except requests.HTTPError as e:
        print(f"❌ Error executing workflow: {e}")
        if hasattr(e.response, 'json'):
            print(f"   Details: {e.response.json()}")
        exit(1)


if __name__ == "__main__":
    main()
