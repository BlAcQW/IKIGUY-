#!/usr/bin/env python3
"""
RunPod API Client

This script provides functions to interact with the RunPod API to:
- Query pod status and connection details
- Auto-discover current SSH connection parameters
- Update configuration when pod details change

Usage:
    # Get pod info
    python runpod_api_client.py --pod-id jzfmzviw26huka-644113c7 info

    # Get SSH connection details
    python runpod_api_client.py --pod-id jzfmzviw26huka-644113c7 ssh-details

    # Update environment file with latest connection details
    python runpod_api_client.py --pod-id jzfmzviw26huka-644113c7 update-env
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict, Optional, Tuple
from pathlib import Path


class RunPodAPIClient:
    """Client for interacting with RunPod GraphQL API"""

    API_ENDPOINT = "https://api.runpod.io/graphql"

    def __init__(self, api_key: str):
        """
        Initialize RunPod API client.

        Args:
            api_key: RunPod API key from https://www.runpod.io/console/user/settings
        """
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Execute a GraphQL query.

        Args:
            query: GraphQL query string
            variables: Optional query variables

        Returns:
            API response as dictionary

        Raises:
            Exception: If API request fails
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = requests.post(
                self.API_ENDPOINT,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"RunPod API request failed: {e}")

    def get_pod_info(self, pod_id: str) -> Dict:
        """
        Get detailed information about a pod.

        Args:
            pod_id: RunPod pod identifier

        Returns:
            Dictionary containing pod information
        """
        query = """
        query GetPod($podId: String!) {
            pod(input: {podId: $podId}) {
                id
                name
                desiredStatus
                runtime {
                    ports {
                        ip
                        publicPort
                        privatePort
                        type
                    }
                    uptimeInSeconds
                }
                machine {
                    gpuCount
                }
            }
        }
        """
        variables = {"podId": pod_id}
        response = self.query(query, variables)

        if "errors" in response:
            raise Exception(f"API error: {response['errors']}")

        return response.get("data", {}).get("pod", {})

    def get_ssh_connection_details(self, pod_id: str) -> Tuple[str, int]:
        """
        Extract SSH connection details from pod info.

        Args:
            pod_id: RunPod pod identifier

        Returns:
            Tuple of (host_ip, ssh_port)

        Raises:
            Exception: If SSH port not found or pod is not running
        """
        pod_info = self.get_pod_info(pod_id)

        if not pod_info or not pod_info.get("runtime"):
            raise Exception(f"Pod {pod_id} is not running or not found")

        ports = pod_info["runtime"].get("ports", [])

        # Find the SSH port (private port 22)
        for port in ports:
            if port.get("privatePort") == 22:
                return (port["ip"], port["publicPort"])

        raise Exception("SSH port (22) not found in pod configuration")

    def get_proxy_ssh_command(self, pod_id: str, ssh_key_path: str = "~/.ssh/id_ed25519") -> str:
        """
        Generate the proxied SSH command for connecting to the pod.

        Args:
            pod_id: RunPod pod identifier
            ssh_key_path: Path to SSH private key

        Returns:
            SSH command string
        """
        return f"ssh {pod_id}@ssh.runpod.io -i {ssh_key_path}"

    def get_direct_ssh_command(self, pod_id: str, ssh_key_path: str = "~/.ssh/id_ed25519") -> str:
        """
        Generate the direct TCP SSH command for connecting to the pod.

        Args:
            pod_id: RunPod pod identifier
            ssh_key_path: Path to SSH private key

        Returns:
            SSH command string
        """
        host, port = self.get_ssh_connection_details(pod_id)
        return f"ssh root@{host} -p {port} -i {ssh_key_path}"


def load_api_key() -> Optional[str]:
    """
    Load RunPod API key from environment or .env file.

    Returns:
        API key string or None if not found
    """
    # Try environment variable first
    api_key = os.getenv("RUNPOD_API_KEY")
    if api_key:
        return api_key

    # Try loading from .env file
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("RUNPOD_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")

    return None


def update_env_file(pod_id: str):
    """
    Update .env file with latest connection details from API.

    Args:
        pod_id: RunPod pod identifier
    """
    api_key = load_api_key()
    if not api_key:
        print("ERROR: RUNPOD_API_KEY not found in environment or .env file", file=sys.stderr)
        sys.exit(1)

    client = RunPodAPIClient(api_key)

    try:
        host, port = client.get_ssh_connection_details(pod_id)
        print(f"✓ Found SSH connection: {host}:{port}")

        env_file = Path(__file__).parent.parent / ".env"
        if not env_file.exists():
            print(f"ERROR: .env file not found at {env_file}", file=sys.stderr)
            sys.exit(1)

        # Read current .env
        with open(env_file) as f:
            lines = f.readlines()

        # Update RUNPOD_DIRECT_HOST and RUNPOD_DIRECT_PORT
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("RUNPOD_DIRECT_HOST="):
                lines[i] = f"RUNPOD_DIRECT_HOST={host}\n"
                updated = True
            elif line.startswith("RUNPOD_DIRECT_PORT="):
                lines[i] = f"RUNPOD_DIRECT_PORT={port}\n"
                updated = True

        # Write back
        with open(env_file, "w") as f:
            f.writelines(lines)

        print(f"✓ Updated {env_file} with new connection details")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="RunPod API Client for querying pod information"
    )
    parser.add_argument(
        "--pod-id",
        required=True,
        help="RunPod pod identifier (e.g., jzfmzviw26huka-644113c7)"
    )
    parser.add_argument(
        "--api-key",
        help="RunPod API key (overrides environment/config)"
    )
    parser.add_argument(
        "command",
        choices=["info", "ssh-details", "update-env"],
        help="Command to execute"
    )

    args = parser.parse_args()

    # Load API key
    api_key = args.api_key or load_api_key()
    if not api_key:
        print(
            "ERROR: RunPod API key not found.\n"
            "Set RUNPOD_API_KEY environment variable or add it to .env file.\n"
            "Get your API key from: https://www.runpod.io/console/user/settings",
            file=sys.stderr
        )
        sys.exit(1)

    client = RunPodAPIClient(api_key)

    try:
        if args.command == "info":
            pod_info = client.get_pod_info(args.pod_id)
            print(json.dumps(pod_info, indent=2))

        elif args.command == "ssh-details":
            host, port = client.get_ssh_connection_details(args.pod_id)
            print(f"Direct SSH: ssh root@{host} -p {port} -i ~/.ssh/id_ed25519")
            print(f"Proxy SSH:  ssh {args.pod_id}@ssh.runpod.io -i ~/.ssh/id_ed25519")

        elif args.command == "update-env":
            update_env_file(args.pod_id)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
