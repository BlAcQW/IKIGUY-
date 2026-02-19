"""
MCP Tools for Automation Configuration Management and Health Checking.

This module provides tools for checking and managing automation configurations,
including health checks for deployed VAPI and N8N components using platform IDs.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote_plus

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import httpx

logger = logging.getLogger(__name__)


class AutomationHealthChecker:
    """Health checker for deployed automations using VAPI and N8N platform IDs."""

    def __init__(self, mongodb_url: str = None):
        """Initialize with MongoDB connection."""
        if not mongodb_url:
            # Default connection from environment
            username = 'admin'
            password = 'aawwER4444%'
            encoded_password = quote_plus(password)
            mongodb_url = f'mongodb://{username}:{encoded_password}@127.0.0.1:27017/kasaai_core?authSource=admin'

        self.mongodb_url = mongodb_url
        self.sync_client = MongoClient(mongodb_url)
        self.db = self.sync_client['kasaai_core']

    def close(self):
        """Close database connections."""
        if self.sync_client:
            self.sync_client.close()

    def get_deployed_configs(self) -> List[Dict[str, Any]]:
        """Get all deployed automation configurations."""
        try:
            deployed_configs = list(self.db.automation_configs.find(
                {'status': 'deployed'},
                {
                    '_id': 1,
                    'automation_name': 1,
                    'automationName': 1,  # Alternative field name
                    'config': 1,
                    'deployment_info': 1,
                    'vapiAgent': 1,  # Direct field
                    'n8nWorkflow': 1,  # Direct field
                    'created_at': 1,
                    'deployed_at': 1,
                    'updated_at': 1
                }
            ))

            return deployed_configs
        except Exception as e:
            logger.error(f"Failed to get deployed configs: {e}")
            return []

    def extract_platform_ids(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Extract VAPI and N8N IDs from various possible locations in config."""
        platform_ids = {
            'vapi_assistant_id': None,
            'n8n_workflow_id': None,
            'phone_number_id': None,
            'webhook_urls': {}
        }

        # Check deployment_info first (most reliable)
        deployment_info = config.get('deployment_info', {})
        if deployment_info:
            platform_ids['vapi_assistant_id'] = deployment_info.get('vapi_assistant_id')
            platform_ids['n8n_workflow_id'] = deployment_info.get('n8n_workflow_id')
            platform_ids['webhook_urls'] = deployment_info.get('webhook_urls', {})

        # Check config structure
        config_data = config.get('config', {})
        if config_data:
            # Check nested config structure
            if 'vapi' in config_data:
                vapi_data = config_data['vapi']
                if isinstance(vapi_data, dict):
                    platform_ids['vapi_assistant_id'] = platform_ids['vapi_assistant_id'] or vapi_data.get('assistantId')
                    platform_ids['phone_number_id'] = vapi_data.get('phoneNumberId')

            if 'n8n' in config_data:
                n8n_data = config_data['n8n']
                if isinstance(n8n_data, dict):
                    platform_ids['n8n_workflow_id'] = platform_ids['n8n_workflow_id'] or n8n_data.get('workflowId')

            # Check userConfig structure
            if 'userConfig' in config_data:
                user_config = config_data['userConfig']
                if user_config and 'vapiAgent' in user_config:
                    vapi_agent = user_config['vapiAgent']
                    platform_ids['vapi_assistant_id'] = platform_ids['vapi_assistant_id'] or vapi_agent.get('assistantId')
                    platform_ids['phone_number_id'] = vapi_agent.get('phoneNumberId')

                if user_config and 'n8nWorkflow' in user_config:
                    n8n_workflow = user_config['n8nWorkflow']
                    platform_ids['n8n_workflow_id'] = platform_ids['n8n_workflow_id'] or n8n_workflow.get('workflowId')
                    if not platform_ids['webhook_urls'] and 'webhookUrl' in n8n_workflow:
                        platform_ids['webhook_urls']['main'] = n8n_workflow['webhookUrl']

        # Check direct fields (alternative schema)
        if 'vapiAgent' in config:
            vapi_agent = config['vapiAgent']
            if isinstance(vapi_agent, dict):
                platform_ids['vapi_assistant_id'] = platform_ids['vapi_assistant_id'] or vapi_agent.get('assistantId')
                platform_ids['phone_number_id'] = vapi_agent.get('phoneNumberId')

        if 'n8nWorkflow' in config:
            n8n_workflow = config['n8nWorkflow']
            if isinstance(n8n_workflow, dict):
                platform_ids['n8n_workflow_id'] = platform_ids['n8n_workflow_id'] or n8n_workflow.get('workflowId')
                if not platform_ids['webhook_urls'] and 'webhookUrl' in n8n_workflow:
                    platform_ids['webhook_urls']['main'] = n8n_workflow['webhookUrl']

        return platform_ids

    async def check_vapi_health(self, assistant_id: str) -> Dict[str, Any]:
        """Check VAPI assistant health using the platform ID."""
        if not assistant_id or assistant_id == '':
            return {
                'status': 'not_configured',
                'error': 'No VAPI assistant ID found',
                'assistant_id': assistant_id
            }

        try:
            # Mock VAPI health check - replace with actual VAPI API call
            # This would typically call the VAPI API to verify the assistant exists and is accessible
            async with httpx.AsyncClient() as client:
                # Example API call structure (adjust based on actual VAPI API)
                # response = await client.get(f"https://api.vapi.ai/assistants/{assistant_id}")

                # For now, return a mock response based on assistant ID pattern
                if assistant_id.endswith('-demo'):
                    return {
                        'status': 'healthy',
                        'assistant_id': assistant_id,
                        'assistant_name': assistant_id.replace('-demo', '').replace('-', ' ').title(),
                        'last_checked': datetime.now(timezone.utc).isoformat(),
                        'mock': True  # Remove when using real API
                    }
                else:
                    return {
                        'status': 'unknown',
                        'assistant_id': assistant_id,
                        'error': 'Assistant status unknown - requires real VAPI API integration',
                        'last_checked': datetime.now(timezone.utc).isoformat(),
                        'mock': True  # Remove when using real API
                    }

        except Exception as e:
            return {
                'status': 'error',
                'assistant_id': assistant_id,
                'error': f'Health check failed: {str(e)}',
                'last_checked': datetime.now(timezone.utc).isoformat()
            }

    async def check_n8n_health(self, workflow_id: str, webhook_urls: Dict[str, str] = None) -> Dict[str, Any]:
        """Check N8N workflow health using the platform ID."""
        if not workflow_id or workflow_id == '':
            return {
                'status': 'not_configured',
                'error': 'No N8N workflow ID found',
                'workflow_id': workflow_id
            }

        try:
            # Mock N8N health check - replace with actual N8N API call
            # This would typically call the N8N API to verify the workflow exists and is active
            webhook_status = {}

            if webhook_urls:
                async with httpx.AsyncClient() as client:
                    for name, url in webhook_urls.items():
                        try:
                            # Test webhook accessibility (GET request to check if endpoint exists)
                            response = await client.get(url, timeout=5.0)
                            # 405 Method Not Allowed is expected for POST webhooks
                            if response.status_code in [200, 405]:
                                webhook_status[name] = 'accessible'
                            else:
                                webhook_status[name] = f'error_{response.status_code}'
                        except Exception as e:
                            webhook_status[name] = f'error: {str(e)}'

            # Mock workflow status based on ID pattern
            if workflow_id.endswith('-demo'):
                return {
                    'status': 'healthy',
                    'workflow_id': workflow_id,
                    'workflow_name': workflow_id.replace('-demo', '').replace('-', ' ').title(),
                    'active': True,
                    'webhook_status': webhook_status,
                    'last_checked': datetime.now(timezone.utc).isoformat(),
                    'mock': True  # Remove when using real API
                }
            else:
                return {
                    'status': 'unknown',
                    'workflow_id': workflow_id,
                    'error': 'Workflow status unknown - requires real N8N API integration',
                    'webhook_status': webhook_status,
                    'last_checked': datetime.now(timezone.utc).isoformat(),
                    'mock': True  # Remove when using real API
                }

        except Exception as e:
            return {
                'status': 'error',
                'workflow_id': workflow_id,
                'error': f'Health check failed: {str(e)}',
                'last_checked': datetime.now(timezone.utc).isoformat()
            }

    async def check_automation_health(self, config_id: str) -> Dict[str, Any]:
        """Check complete health of a deployed automation."""
        try:
            # Get config from database - handle both string and ObjectId
            from bson import ObjectId

            # Try with string first, then ObjectId
            config = self.db.automation_configs.find_one({'_id': config_id})
            if not config and len(config_id) == 24:
                try:
                    config = self.db.automation_configs.find_one({'_id': ObjectId(config_id)})
                except:
                    pass

            if not config:
                return {
                    'config_id': config_id,
                    'status': 'not_found',
                    'error': 'Configuration not found'
                }

            # Extract automation name
            automation_name = (
                config.get('automation_name') or
                config.get('automationName') or
                f"Config {config_id[:8]}"
            )

            # Extract platform IDs
            platform_ids = self.extract_platform_ids(config)

            # Check VAPI health
            vapi_health = await self.check_vapi_health(platform_ids['vapi_assistant_id'])

            # Check N8N health
            n8n_health = await self.check_n8n_health(
                platform_ids['n8n_workflow_id'],
                platform_ids['webhook_urls']
            )

            # Determine overall health
            overall_status = 'healthy'
            if vapi_health['status'] in ['error', 'not_configured'] or n8n_health['status'] in ['error', 'not_configured']:
                overall_status = 'unhealthy'
            elif vapi_health['status'] == 'unknown' or n8n_health['status'] == 'unknown':
                overall_status = 'unknown'

            return {
                'config_id': config_id,
                'automation_name': automation_name,
                'overall_status': overall_status,
                'components': {
                    'vapi': vapi_health,
                    'n8n': n8n_health
                },
                'platform_ids': platform_ids,
                'last_checked': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            return {
                'config_id': config_id,
                'status': 'error',
                'error': f'Health check failed: {str(e)}',
                'last_checked': datetime.now(timezone.utc).isoformat()
            }

    async def check_all_deployed_health(self) -> Dict[str, Any]:
        """Check health of all deployed automations."""
        deployed_configs = self.get_deployed_configs()

        health_results = []
        summary = {
            'total_deployed': len(deployed_configs),
            'healthy': 0,
            'unhealthy': 0,
            'unknown': 0,
            'errors': 0
        }

        for config in deployed_configs:
            config_id = str(config['_id'])
            health_result = await self.check_automation_health(config_id)
            health_results.append(health_result)

            # Update summary
            status = health_result.get('overall_status', 'error')
            if status == 'healthy':
                summary['healthy'] += 1
            elif status == 'unhealthy':
                summary['unhealthy'] += 1
            elif status == 'unknown':
                summary['unknown'] += 1
            else:
                summary['errors'] += 1

        return {
            'summary': summary,
            'results': health_results,
            'checked_at': datetime.now(timezone.utc).isoformat()
        }

    def update_config_with_platform_ids(self, config_id: str, vapi_id: str = None, n8n_id: str = None, webhook_urls: Dict[str, str] = None):
        """Update a configuration with platform IDs in deployment_info."""
        try:
            update_data = {}

            # Prepare deployment_info update
            deployment_info_updates = {}
            if vapi_id:
                deployment_info_updates['vapi_assistant_id'] = vapi_id
            if n8n_id:
                deployment_info_updates['n8n_workflow_id'] = n8n_id
            if webhook_urls:
                deployment_info_updates['webhook_urls'] = webhook_urls

            if deployment_info_updates:
                # Use $set with dot notation to update nested fields
                for key, value in deployment_info_updates.items():
                    update_data[f'deployment_info.{key}'] = value

                # Update timestamp
                update_data['updated_at'] = datetime.now(timezone.utc)

                result = self.db.automation_configs.update_one(
                    {'_id': config_id},
                    {'$set': update_data}
                )

                if result.matched_count > 0:
                    logger.info(f"Updated config {config_id} with platform IDs")
                    return True
                else:
                    logger.warning(f"Config {config_id} not found for update")
                    return False

            return True

        except Exception as e:
            logger.error(f"Failed to update config {config_id} with platform IDs: {e}")
            return False


# Utility functions for direct use
async def check_deployed_automations():
    """Check all deployed automations and return health report."""
    checker = AutomationHealthChecker()
    try:
        return await checker.check_all_deployed_health()
    finally:
        checker.close()


async def check_single_automation(config_id: str):
    """Check health of a single automation."""
    checker = AutomationHealthChecker()
    try:
        return await checker.check_automation_health(config_id)
    finally:
        checker.close()


def get_automation_configs_summary():
    """Get summary of all automation configurations."""
    checker = AutomationHealthChecker()
    try:
        deployed_configs = checker.get_deployed_configs()

        summary = {
            'total_deployed': len(deployed_configs),
            'configs_with_vapi_ids': 0,
            'configs_with_n8n_ids': 0,
            'configs_with_both_ids': 0,
            'configs_missing_ids': 0
        }

        config_details = []

        for config in deployed_configs:
            config_id = str(config['_id'])
            automation_name = (
                config.get('automation_name') or
                config.get('automationName') or
                f"Config {config_id[:8]}"
            )

            platform_ids = checker.extract_platform_ids(config)

            has_vapi = bool(platform_ids['vapi_assistant_id'])
            has_n8n = bool(platform_ids['n8n_workflow_id'])

            if has_vapi:
                summary['configs_with_vapi_ids'] += 1
            if has_n8n:
                summary['configs_with_n8n_ids'] += 1
            if has_vapi and has_n8n:
                summary['configs_with_both_ids'] += 1
            if not has_vapi and not has_n8n:
                summary['configs_missing_ids'] += 1

            config_details.append({
                'config_id': config_id,
                'automation_name': automation_name,
                'vapi_assistant_id': platform_ids['vapi_assistant_id'],
                'n8n_workflow_id': platform_ids['n8n_workflow_id'],
                'has_webhook_urls': bool(platform_ids['webhook_urls']),
                'deployed_at': config.get('deployed_at'),
                'updated_at': config.get('updated_at')
            })

        return {
            'summary': summary,
            'configs': config_details
        }

    finally:
        checker.close()


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def main():
        print("=== AUTOMATION HEALTH CHECK REPORT ===")

        # Get summary
        summary = get_automation_configs_summary()
        print(f"Total deployed: {summary['summary']['total_deployed']}")
        print(f"With VAPI IDs: {summary['summary']['configs_with_vapi_ids']}")
        print(f"With N8N IDs: {summary['summary']['configs_with_n8n_ids']}")
        print(f"With both IDs: {summary['summary']['configs_with_both_ids']}")
        print()

        # Check health of all deployed
        health_report = await check_deployed_automations()
        print("=== HEALTH CHECK RESULTS ===")
        print(f"Healthy: {health_report['summary']['healthy']}")
        print(f"Unhealthy: {health_report['summary']['unhealthy']}")
        print(f"Unknown: {health_report['summary']['unknown']}")

        for result in health_report['results']:
            name = result.get('automation_name', f"Config {result['config_id'][:8]}")
            status = result.get('overall_status', result.get('status', 'unknown'))
            print(f"\n{name} ({result['config_id'][:8]}): {status}")
            if 'components' in result:
                print(f"  VAPI: {result['components']['vapi']['status']} - {result['components']['vapi'].get('assistant_id', 'N/A')}")
                print(f"  N8N: {result['components']['n8n']['status']} - {result['components']['n8n'].get('workflow_id', 'N/A')}")
            if result.get('error'):
                print(f"  Error: {result['error']}")

    asyncio.run(main())