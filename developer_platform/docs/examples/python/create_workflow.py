"""
Create an n8n Workflow

This example demonstrates how to create an n8n workflow for automation.
"""

import os
import requests
from typing import Dict, List, Optional


# Configuration
API_KEY = os.getenv("KASAAI_API_KEY", "your_api_key_here")
BASE_URL = "https://developer.ailabsafrica.com"


def create_workflow(
    name: str,
    description: Optional[str] = None,
    nodes: Optional[List[Dict]] = None,
    connections: Optional[Dict] = None,
    active: bool = False
) -> Dict:
    """
    Create a new n8n workflow.

    Args:
        name: Workflow name
        description: Optional workflow description
        nodes: List of workflow nodes
        connections: Node connections configuration
        active: Whether to activate the workflow immediately

    Returns:
        Dict: Created workflow object

    Raises:
        requests.HTTPError: If the API request fails
    """
    endpoint = f"{BASE_URL}/api/v1/n8n/workflows"

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "name": name,
        "active": active
    }

    if description:
        payload["description"] = description
    if nodes:
        payload["nodes"] = nodes
    if connections:
        payload["connections"] = connections

    response = requests.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()


def create_simple_webhook_workflow(
    name: str,
    webhook_path: str = "webhook"
) -> Dict:
    """
    Create a simple workflow with a webhook trigger.

    Args:
        name: Workflow name
        webhook_path: Path for the webhook endpoint

    Returns:
        Dict: Created workflow object
    """
    nodes = [
        {
            "id": "webhook",
            "name": "Webhook",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 1,
            "position": [250, 300],
            "parameters": {
                "path": webhook_path,
                "httpMethod": "POST",
                "responseMode": "onReceived",
                "responseData": "allEntries"
            }
        },
        {
            "id": "set",
            "name": "Process Data",
            "type": "n8n-nodes-base.set",
            "typeVersion": 1,
            "position": [450, 300],
            "parameters": {
                "values": {
                    "string": [
                        {
                            "name": "status",
                            "value": "processed"
                        },
                        {
                            "name": "message",
                            "value": "Data received and processed"
                        }
                    ]
                }
            }
        }
    ]

    connections = {
        "Webhook": {
            "main": [
                [
                    {
                        "node": "Process Data",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        }
    }

    return create_workflow(
        name=name,
        description="Simple webhook workflow that processes incoming data",
        nodes=nodes,
        connections=connections,
        active=True
    )


def create_call_notification_workflow(name: str, slack_webhook: str) -> Dict:
    """
    Create a workflow that sends Slack notifications for completed calls.

    Args:
        name: Workflow name
        slack_webhook: Slack webhook URL

    Returns:
        Dict: Created workflow object
    """
    nodes = [
        {
            "id": "webhook",
            "name": "Call Webhook",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 1,
            "position": [250, 300],
            "parameters": {
                "path": "call-completed",
                "httpMethod": "POST"
            }
        },
        {
            "id": "slack",
            "name": "Send to Slack",
            "type": "n8n-nodes-base.slack",
            "typeVersion": 1,
            "position": [450, 300],
            "parameters": {
                "webhookUrl": slack_webhook,
                "text": "Call completed: {{$json.call_id}}",
                "otherOptions": {
                    "mrkdwn": True
                }
            }
        }
    ]

    connections = {
        "Call Webhook": {
            "main": [
                [
                    {
                        "node": "Send to Slack",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        }
    }

    return create_workflow(
        name=name,
        description="Sends Slack notification when a call is completed",
        nodes=nodes,
        connections=connections,
        active=True
    )


def main():
    """Main function to demonstrate workflow creation."""
    try:
        # Example 1: Create a simple webhook workflow
        print("Creating simple webhook workflow...")
        workflow1 = create_simple_webhook_workflow(
            name="Simple Data Processor",
            webhook_path="process-data"
        )

        print("✅ Workflow 1 created successfully!")
        print(f"   ID: {workflow1['id']}")
        print(f"   Name: {workflow1['name']}")
        print(f"   Active: {workflow1['active']}")
        print()

        # Example 2: Create a call notification workflow
        slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        if slack_webhook:
            print("Creating call notification workflow...")
            workflow2 = create_call_notification_workflow(
                name="Call Completion Notifier",
                slack_webhook=slack_webhook
            )

            print("✅ Workflow 2 created successfully!")
            print(f"   ID: {workflow2['id']}")
            print(f"   Name: {workflow2['name']}")
            print(f"   Active: {workflow2['active']}")
        else:
            print("⚠️  Skipping Slack workflow (SLACK_WEBHOOK_URL not set)")

    except requests.HTTPError as e:
        print(f"❌ Error creating workflow: {e}")
        if hasattr(e.response, 'json'):
            print(f"   Details: {e.response.json()}")
        exit(1)


if __name__ == "__main__":
    main()
