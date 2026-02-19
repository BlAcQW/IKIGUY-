"""
Automation Configuration Management API
CRUD operations for automation configurations
"""

from typing import List, Optional, Dict, Any, Optional as TypingOptional
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.exceptions import RequestValidationError
from bson import ObjectId
from datetime import datetime
import logging
from uuid import uuid4
from pydantic import ValidationError, BaseModel, Field
import subprocess
import os

from ..auth import get_current_user_mongo
from ..middleware.organization_context import (
    get_organization_context,
    get_user_organization_filter
)
from ..models.automation_config import (
    AutomationConfig,
    AutomationConfigCreate,
    AutomationConfigUpdate,
    AutomationConfigResponse,
    AutomationConfigList,
    AutomationStatus as AutomationStatusEnum,
    DeploymentResult,
    AutomationStatusResponse,
    DuplicateRequest
)
from ..models.campaign import (
    CampaignCreateRequest,
    CampaignStatusResponse,
    CampaignAnalyticsResponse,
    AutomationCampaign
)
from ..mongo import get_collection
from apps.shared.integration.n8n import N8NIntegration, N8NConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/automation-configs", tags=["automation-configs"])

# MongoDB collection
automation_configs_collection = get_collection("automation_configs")

# Initialize n8n integration
n8n_config = N8NConfig(
    base_url=os.getenv("N8N_API_URL", "https://automate.inspirecreations.it.com"),
    api_key=os.getenv("N8N_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MTBhMTUzMi04YmRkLTRkYjAtYjU1OS01ZTIxYTAzNjI4ODMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU2NDQxNjg4fQ.oAcaO5v0As8jl543StOB87l21jkURptt7bn9X6E7NcU")
)
n8n_integration = N8NIntegration(n8n_config)

def _convert_to_object_id(id_value: str) -> ObjectId:
    """
    Convert a string ID to MongoDB ObjectId.

    Args:
        id_value: String ID (ObjectId hex string)

    Returns:
        MongoDB ObjectId

    Raises:
        HTTPException: If the ID format is invalid
    """
    try:
        return ObjectId(id_value)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ID format: {id_value}. Expected MongoDB ObjectId hex string (24 characters)."
        )

def _to_response(doc: Dict[str, Any]) -> AutomationConfigResponse:
    """Convert MongoDB document to response model"""
    # Handle null _id case - should not happen with proper filtering
    if doc.get("_id") is None:
        raise ValueError(f"Document has null _id: {doc}")

    doc["id"] = str(doc["_id"])
    del doc["_id"]

    # Handle field name conversions from camelCase (database) to snake_case (response model)
    field_mappings = {
        "automationName": "automation_name",
        "companyInfo": "company_info",
        "vapiAgent": "vapi_agent",
        "n8nWorkflow": "n8n_workflow",
        "customTools": "custom_tools",
        "demoSettings": "demo_settings",
        "createdAt": "created_at",
        "updatedAt": "updated_at"
    }

    for camel_case, snake_case in field_mappings.items():
        if camel_case in doc and snake_case not in doc:
            doc[snake_case] = doc[camel_case]

    # Handle old automation config format that has different field structure
    if "automation_name" not in doc:
        doc["automation_name"] = doc.get("config", {}).get("automation_name", "Unnamed Automation")

    # Set defaults for missing required fields
    if doc.get("company_info") is None:
        from ..models.automation_config import CompanyInfo
        doc["company_info"] = {
            "name": "Unknown Company",
            "description": "No description available",
            "url": ""
        }

    if doc.get("vapi_agent") is None:
        from ..models.automation_config import VAPIAgent, VoiceSettings
        doc["vapi_agent"] = {
            "assistant_id": "",
            "phone_number_id": "",
            "system_prompt": "You are a helpful assistant",
            "voice_settings": {
                "voice_id": "jennifer",
                "model": "nova-2",
                "max_duration": 600
            },
            "tools": []
        }

    if doc.get("n8n_workflow") is None:
        from ..models.automation_config import N8NWorkflow, N8NEndpoints
        doc["n8n_workflow"] = {
            "workflow_id": "",
            "workflow_name": "Default Workflow",
            "webhook_url": "",
            "endpoints": {
                "calendar": "/calendar/availability",
                "tickets": "/tickets/create",
                "availability": "/availability/check",
                "escalation": "/escalation/route",
                "analytics": "/analytics/track"
            }
        }

    if doc.get("integrations") is None:
        from ..models.automation_config import Integrations
        doc["integrations"] = Integrations().dict()
    if doc.get("custom_tools") is None:
        from ..models.automation_config import CustomTools
        doc["custom_tools"] = CustomTools().dict()
    if doc.get("demo_settings") is None:
        from ..models.automation_config import DemoSettings
        doc["demo_settings"] = DemoSettings().dict()
    if doc.get("analytics") is None:
        from ..models.automation_config import Analytics
        doc["analytics"] = Analytics().dict()

    # Ensure config field has proper user_config structure for frontend compatibility
    if doc.get("config") is None:
        doc["config"] = {}

    # Ensure config has user_config structure that frontend expects
    if "user_config" not in doc["config"] or not doc["config"]["user_config"]:
        doc["config"]["user_config"] = {
            "automation_name": doc.get("automation_name", "Unnamed Automation"),
            "company_info": doc.get("company_info", {
                "name": "Unknown Company",
                "description": "No description available",
                "url": ""
            }),
            "vapi_agent": doc.get("vapi_agent", {}),
            "n8n_workflow": doc.get("n8n_workflow", {}),
            "integrations": doc.get("integrations", {}),
            "custom_tools": doc.get("custom_tools", {}),
            "demo_settings": doc.get("demo_settings", {})
        }

    # Ensure required datetime fields exist
    if "created_at" not in doc:
        doc["created_at"] = datetime.utcnow()

    if "updated_at" not in doc:
        doc["updated_at"] = datetime.utcnow()

    return AutomationConfigResponse(**doc)

def _prepare_for_storage(config: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
    """Prepare config for MongoDB storage"""
    now = datetime.utcnow()

    if "_id" in config:
        del config["_id"]
    if "id" in config:
        del config["id"]

    config["updatedAt"] = now
    config["updated_at"] = now  # Also add snake_case for response model compatibility
    if user_id:
        config["user_id"] = user_id

    return config

@router.post("/", response_model=AutomationConfigResponse)
async def create_automation_config(
    config: AutomationConfigCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context),
    request: Request = None
):
    """Create a new automation configuration"""
    try:
        user_id = current_user.get("id") or current_user.get("sub")

        # Convert to dict and prepare for storage
        config_dict = config.dict()
        config_dict["status"] = AutomationStatusEnum.DRAFT
        now = datetime.utcnow()
        config_dict["createdAt"] = now
        config_dict["created_at"] = now  # Also add snake_case for response model compatibility

        # Set organization_id from context
        if org_id:
            config_dict["organization_id"] = org_id

        # Set defaults for all optional fields
        if "company_info" not in config_dict or config_dict["company_info"] is None:
            from ..models.automation_config import CompanyInfo
            config_dict["company_info"] = {
                "name": "",
                "description": "",
                "url": ""
            }
            # Also set camelCase for database compatibility
            config_dict["companyInfo"] = config_dict["company_info"]

        if "vapi_agent" not in config_dict or config_dict["vapi_agent"] is None:
            from ..models.automation_config import VAPIAgent, VoiceSettings
            config_dict["vapi_agent"] = {
                "assistant_id": "",
                "phone_number_id": "",
                "system_prompt": "You are a helpful assistant",
                "voice_settings": {
                    "voice_id": "jennifer",
                    "model": "nova-2",
                    "max_duration": 600
                },
                "tools": []
            }
            # Also set camelCase for database compatibility
            config_dict["vapiAgent"] = {
                "assistantId": config_dict["vapi_agent"]["assistant_id"],
                "phoneNumberId": config_dict["vapi_agent"]["phone_number_id"],
                "systemPrompt": config_dict["vapi_agent"]["system_prompt"],
                "voiceSettings": {
                    "voiceId": config_dict["vapi_agent"]["voice_settings"]["voice_id"],
                    "model": config_dict["vapi_agent"]["voice_settings"]["model"],
                    "maxDuration": config_dict["vapi_agent"]["voice_settings"]["max_duration"]
                },
                "tools": config_dict["vapi_agent"]["tools"]
            }

        if "n8n_workflow" not in config_dict or config_dict["n8n_workflow"] is None:
            from ..models.automation_config import N8NWorkflow, N8NEndpoints
            config_dict["n8n_workflow"] = {
                "workflow_id": "",
                "workflow_name": "Default Workflow",
                "webhook_url": "",
                "endpoints": {
                    "calendar": "/calendar/availability",
                    "tickets": "/tickets/create",
                    "availability": "/availability/check",
                    "escalation": "/escalation/route",
                    "analytics": "/analytics/track"
                }
            }
            # Also set camelCase for database compatibility
            config_dict["n8nWorkflow"] = {
                "workflowId": config_dict["n8n_workflow"]["workflow_id"],
                "workflowName": config_dict["n8n_workflow"]["workflow_name"],
                "webhookUrl": config_dict["n8n_workflow"]["webhook_url"],
                "endpoints": config_dict["n8n_workflow"]["endpoints"]
            }

        if "integrations" not in config_dict or config_dict["integrations"] is None:
            from ..models.automation_config import Integrations
            config_dict["integrations"] = Integrations().dict()
        if "custom_tools" not in config_dict or config_dict["custom_tools"] is None:
            from ..models.automation_config import CustomTools
            config_dict["custom_tools"] = CustomTools().dict()
            config_dict["customTools"] = config_dict["custom_tools"]  # camelCase for database
        if "demo_settings" not in config_dict or config_dict["demo_settings"] is None:
            from ..models.automation_config import DemoSettings
            config_dict["demo_settings"] = DemoSettings().dict()
            config_dict["demoSettings"] = config_dict["demo_settings"]  # camelCase for database
        if "analytics" not in config_dict or config_dict["analytics"] is None:
            from ..models.automation_config import Analytics
            config_dict["analytics"] = Analytics().dict()

        config_dict = _prepare_for_storage(config_dict, user_id)

        # Insert into MongoDB (async)
        result = await automation_configs_collection.insert_one(config_dict)

        # Retrieve the created document (async)
        created_doc = await automation_configs_collection.find_one({"_id": result.inserted_id})

        logger.info(f"Created automation config: {config.automation_name} for user: {user_id}")
        return _to_response(created_doc)

    except Exception as e:
        logger.error(f"Error creating automation config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create automation config: {str(e)}")

@router.get("/")
async def list_automation_configs(
    status: Optional[AutomationStatusEnum] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: TypingOptional[Dict[str, Any]] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """List automation configurations with organization filtering"""
    try:
        # Build query with organization filtering
        org_filter = get_user_organization_filter(current_user, org_id)
        query = {**org_filter}

        if status:
            query["status"] = status

        # Add filter to exclude configs with null/invalid _id (data integrity issue)
        query["_id"] = {"$ne": None, "$exists": True}

        # Get total count
        total = await automation_configs_collection.count_documents(query)

        # Get configurations with pagination
        cursor = automation_configs_collection.find(query).sort("updatedAt", -1)
        if offset:
            cursor = cursor.skip(offset)
        if limit:
            cursor = cursor.limit(limit)

        # Convert cursor to list for async iteration
        docs = await cursor.to_list(length=limit)

        configs = []
        for doc in docs:
            try:
                response_doc = _to_response(doc)
                configs.append(response_doc.dict())
            except Exception as e:
                logger.warning(f"Error converting automation config {doc.get('_id')}: {str(e)}")
                continue

        return {"configs": configs, "total": total}

    except Exception as e:
        logger.error(f"Error listing automation configs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list automation configs: {str(e)}")

@router.get("/{config_id}", response_model=AutomationConfigResponse)
async def get_automation_config(
    config_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Get a specific automation configuration.

    Note: Users with universal_admin role can access any automation config.
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Convert string ID to ObjectId
        object_id = _convert_to_object_id(config_id)

        # Build query based on role and organization
        # Universal admins can access any config, regular users only their org's configs
        query = {"_id": object_id}
        if not is_universal_admin:
            # Apply organization filter
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        # Find the configuration (async)
        doc = await automation_configs_collection.find_one(query)

        if not doc:
            if is_universal_admin:
                raise HTTPException(status_code=404, detail="Automation config not found")
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Automation config not found or you don't have permission to access it"
                )

        # Log admin access
        if is_universal_admin and doc.get("user_id") != user_id:
            logger.warning(
                f"ADMIN ACCESS: User {user_id} (universal_admin) accessed automation config {config_id} "
                f"owned by {doc.get('user_id')}"
            )

        return _to_response(doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting automation config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get automation config: {str(e)}")

@router.put("/{config_id}", response_model=AutomationConfigResponse)
async def update_automation_config(
    config_id: str,
    update_data: AutomationConfigUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Update an automation configuration.

    Note: Users with universal_admin role can update any automation config.
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Convert string ID to ObjectId
        object_id = _convert_to_object_id(config_id)

        # Build query based on role and organization
        # Universal admins can update any config, regular users only their org's configs
        query = {"_id": object_id}
        if not is_universal_admin:
            # Apply organization filter
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        # Prepare update data
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        if not update_dict:
            raise HTTPException(status_code=400, detail="No update data provided")

        # Don't override user_id for universal admins (preserve original owner)
        if is_universal_admin:
            update_dict = _prepare_for_storage(update_dict, user_id=None)
        else:
            update_dict = _prepare_for_storage(update_dict, user_id)

        # Update the document (async)
        result = await automation_configs_collection.update_one(
            query,
            {"$set": update_dict}
        )

        if result.matched_count == 0:
            if is_universal_admin:
                raise HTTPException(status_code=404, detail="Automation config not found")
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Automation config not found or you don't have permission to update it"
                )

        # Get updated document (async)
        updated_doc = await automation_configs_collection.find_one({"_id": object_id})

        # Log admin action
        if is_universal_admin and updated_doc.get("user_id") != user_id:
            logger.warning(
                f"ADMIN ACTION: User {user_id} (universal_admin) updated automation config {config_id} "
                f"owned by {updated_doc.get('user_id')}"
            )

        logger.info(f"Updated automation config: {config_id}")
        return _to_response(updated_doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating automation config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update automation config: {str(e)}")


def _flatten_dict_to_dot_notation(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten a nested dictionary to dot notation for MongoDB $set operations.

    Example:
        {"vapi_agent": {"custom_settings_override": {"tts": {"provider": "kokoro"}}}}
        becomes:
        {"vapi_agent.custom_settings_override": {"tts": {"provider": "kokoro"}}}

    This preserves the final nested object (like custom_settings_override) instead of
    flattening it completely, which allows for proper merging behavior.

    Args:
        d: Dictionary to flatten
        parent_key: Current parent key path
        sep: Separator for keys

    Returns:
        Flattened dictionary with dot notation keys
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        # Only flatten one level deep for known nested structures
        # This allows custom_settings_override to be set as a whole object
        known_nested_keys = ['vapi_agent', 'vapiAgent', 'config', 'n8n_workflow', 'company_info']

        if isinstance(v, dict) and k in known_nested_keys:
            # Flatten this level but keep children as objects
            for sub_k, sub_v in v.items():
                items.append((f"{new_key}{sep}{sub_k}", sub_v))
        else:
            items.append((new_key, v))

    return dict(items)


@router.patch("/{config_id}", response_model=AutomationConfigResponse)
async def partial_update_automation_config(
    config_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Partial update of automation configuration.

    Supports nested updates like { vapi_agent: { custom_settings_override: {...} } }
    without overwriting other fields in vapi_agent.

    This is the preferred endpoint for updating conversation settings (TTS/ASR/LLM overrides).

    Args:
        config_id: Automation config ID (MongoDB ObjectId hex string)
        request: Request body with partial update data

    Returns:
        Updated automation configuration

    Example request body:
    ```json
    {
        "vapi_agent": {
            "custom_settings_override": {
                "tts": {"provider": "kokoro", "voice": "af_heart"},
                "asr": {"provider": "faster_whisper"},
                "llm": {"model": "gemini-2.5-flash"},
                "referenceVoice": null
            }
        }
    }
    ```
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Convert string ID to ObjectId
        object_id = _convert_to_object_id(config_id)

        # Build query based on role and organization
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        # Parse request body
        update_data = await request.json()

        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        # Flatten nested updates to dot notation for MongoDB $set
        # This ensures nested fields are merged rather than replaced
        flattened_update = _flatten_dict_to_dot_notation(update_data)

        # Add timestamp
        now = datetime.utcnow()
        flattened_update["updatedAt"] = now
        flattened_update["updated_at"] = now

        # Support both snake_case and camelCase for vapi_agent updates
        # If updating vapi_agent, also update vapiAgent for compatibility
        keys_to_add = {}
        for key, value in list(flattened_update.items()):
            if key.startswith("vapi_agent."):
                # Also set camelCase version
                camel_key = key.replace("vapi_agent.", "vapiAgent.")
                keys_to_add[camel_key] = value
            elif key.startswith("vapiAgent."):
                # Also set snake_case version
                snake_key = key.replace("vapiAgent.", "vapi_agent.")
                keys_to_add[snake_key] = value

        flattened_update.update(keys_to_add)

        logger.info(f"PATCH automation config {config_id}: {list(flattened_update.keys())}")

        # Update the document with $set
        result = await automation_configs_collection.update_one(
            query,
            {"$set": flattened_update}
        )

        if result.matched_count == 0:
            if is_universal_admin:
                raise HTTPException(status_code=404, detail="Automation config not found")
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Automation config not found or you don't have permission to update it"
                )

        # Get updated document
        updated_doc = await automation_configs_collection.find_one({"_id": object_id})

        # Log admin action
        if is_universal_admin and updated_doc.get("user_id") != user_id:
            logger.warning(
                f"ADMIN ACTION: User {user_id} (universal_admin) patched automation config {config_id} "
                f"owned by {updated_doc.get('user_id')}"
            )

        logger.info(f"Patched automation config: {config_id}")
        return _to_response(updated_doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error patching automation config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to patch automation config: {str(e)}")


@router.delete("/{config_id}")
async def delete_automation_config(
    config_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Delete an automation configuration and clean up associated resources.

    This will:
    1. Fetch the automation config
    2. Delete n8n workflow if workflow_id exists
    3. Delete VAPI assistant if assistant_id exists
    4. Delete from our database

    Note: Users with universal_admin role can delete any automation config.
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Convert string ID to ObjectId
        object_id = _convert_to_object_id(config_id)

        # Build query based on role and organization
        # Universal admins can delete any config, regular users only their org's configs
        query = {"_id": object_id}
        if not is_universal_admin:
            # Apply organization filter
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        # First, fetch the config to get n8n and VAPI IDs
        doc = await automation_configs_collection.find_one(query)

        if not doc:
            if is_universal_admin:
                raise HTTPException(status_code=404, detail="Automation config not found")
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Automation config not found or you don't have permission to delete it"
                )

        deletion_results = {
            "config_deleted": False,
            "n8n_deleted": False,
            "vapi_deleted": False,
            "errors": []
        }

        # Extract n8n workflow ID
        n8n_workflow_id = None
        if "n8n_workflow" in doc or "n8nWorkflow" in doc:
            n8n_data = doc.get("n8n_workflow") or doc.get("n8nWorkflow") or {}
            n8n_workflow_id = n8n_data.get("workflow_id") or n8n_data.get("workflowId")

        # Extract VAPI assistant ID
        vapi_assistant_id = None
        if "vapi_agent" in doc or "vapiAgent" in doc:
            vapi_data = doc.get("vapi_agent") or doc.get("vapiAgent") or {}
            vapi_assistant_id = vapi_data.get("assistant_id") or vapi_data.get("assistantId")

        # Delete n8n workflow if exists
        if n8n_workflow_id:
            try:
                logger.info(f"Attempting to delete n8n workflow: {n8n_workflow_id}")
                # Use n8n integration to delete workflow
                deletion_success = await n8n_integration.delete_workflow(n8n_workflow_id)

                if deletion_success:
                    deletion_results["n8n_deleted"] = True
                    logger.info(f"Successfully deleted n8n workflow: {n8n_workflow_id}")
                else:
                    logger.warning(f"Failed to delete n8n workflow {n8n_workflow_id}")
                    deletion_results["errors"].append(f"n8n: workflow deletion returned False")
            except Exception as e:
                logger.warning(f"Failed to delete n8n workflow {n8n_workflow_id}: {str(e)}")
                deletion_results["errors"].append(f"n8n: {str(e)}")

        # Delete VAPI assistant if exists
        if vapi_assistant_id:
            try:
                logger.info(f"Attempting to delete VAPI assistant: {vapi_assistant_id}")
                # Use VAPI CLI to delete assistant
                vapi_key = os.getenv("VAPI_API_KEY", "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2")
                vapi_cli = "/root/.nvm/versions/node/v20.19.5/lib/node_modules/@vapi-ai/cli/bin/vapi"

                result = subprocess.run(
                    [vapi_cli, "assistant", "delete", vapi_assistant_id],
                    env={**os.environ, "VAPI_API_KEY": vapi_key},
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    deletion_results["vapi_deleted"] = True
                    logger.info(f"Successfully deleted VAPI assistant: {vapi_assistant_id}")
                else:
                    logger.warning(f"Failed to delete VAPI assistant: {result.stderr}")
                    deletion_results["errors"].append(f"vapi: {result.stderr}")
            except subprocess.TimeoutExpired:
                logger.warning(f"Timeout deleting VAPI assistant {vapi_assistant_id}")
                deletion_results["errors"].append("vapi: timeout")
            except Exception as e:
                logger.warning(f"Failed to delete VAPI assistant {vapi_assistant_id}: {str(e)}")
                deletion_results["errors"].append(f"vapi: {str(e)}")

        # Finally, delete the document from our database
        # Use the same query we used earlier - respecting universal_admin permission
        result = await automation_configs_collection.delete_one(query)

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Automation config not found")

        deletion_results["config_deleted"] = True
        logger.info(f"Deleted automation config: {config_id}. Results: {deletion_results}")

        return {
            "message": "Automation config deleted successfully",
            "details": deletion_results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting automation config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete automation config: {str(e)}")

@router.post("/{config_id}/deploy", response_model=DeploymentResult)
async def deploy_automation(
    config_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """Deploy an automation configuration"""
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Convert string ID to ObjectId
        object_id = _convert_to_object_id(config_id)

        # Build query based on role and organization
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        # Get the configuration (async)
        doc = await automation_configs_collection.find_one(query)

        if not doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # TODO: Implement actual deployment logic here
        # This would involve:
        # 1. Creating N8N workflow
        # 2. Creating VAPI assistant
        # 3. Deploying demo page
        # 4. Setting up integrations

        # For now, simulate deployment
        demo_url = None
        if doc.get("demoSettings", {}).get("enableDemo"):
            demo_url = f"https://demo.ailabsafrica.com/{config_id}"

        # Update status to deployed (async)
        await automation_configs_collection.update_one(
            {"_id": object_id},
            {"$set": {
                "status": AutomationStatusEnum.DEPLOYED,
                "updatedAt": datetime.utcnow()
            }}
        )

        logger.info(f"Deployed automation config: {config_id}")

        return DeploymentResult(
            success=True,
            demoUrl=demo_url,
            workflowId=doc.get("n8nWorkflow", {}).get("workflowId"),
            assistantId=doc.get("vapiAgent", {}).get("assistantId")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deploying automation config {config_id}: {str(e)}")
        return DeploymentResult(
            success=False,
            error=f"Deployment failed: {str(e)}"
        )

@router.post("/{config_id}/stop", response_model=DeploymentResult)
async def stop_automation(
    config_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """Stop a deployed automation"""
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Convert string ID to ObjectId
        object_id = _convert_to_object_id(config_id)

        # Build query based on role and organization
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        # Get the configuration (async)
        doc = await automation_configs_collection.find_one(query)

        if not doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        if doc.get("status") != AutomationStatusEnum.DEPLOYED:
            raise HTTPException(status_code=400, detail="Automation is not currently deployed")

        # TODO: Implement actual stop logic here
        # This would involve:
        # 1. Deactivating N8N workflow
        # 2. Stopping VAPI assistant
        # 3. Removing demo page

        # Update status to stopped (async)
        await automation_configs_collection.update_one(
            {"_id": object_id},
            {"$set": {
                "status": AutomationStatusEnum.STOPPED,
                "updatedAt": datetime.utcnow()
            }}
        )

        logger.info(f"Stopped automation config: {config_id}")

        return DeploymentResult(success=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping automation config {config_id}: {str(e)}")
        return DeploymentResult(
            success=False,
            error=f"Stop failed: {str(e)}"
        )

@router.get("/{config_id}/status")
async def get_automation_status(
    config_id: str,
    current_user: TypingOptional[Dict[str, Any]] = None
):
    """Get automation status and metrics (public endpoint)"""
    try:
        # Handle case where config_id might be "None" string or other invalid values
        if config_id in ["None", "null", "undefined", ""] or not config_id or config_id.strip() == "":
            raise HTTPException(status_code=400, detail="Invalid automation config ID: cannot be None, null, or empty")

        # Convert string ID to ObjectId
        object_id = _convert_to_object_id(config_id)

        # Build query
        query = {"_id": object_id}
        if current_user:
            user_id = current_user.get("id") or current_user.get("sub")
            query["user_id"] = user_id

        # Get the configuration
        doc = await automation_configs_collection.find_one(query)

        if not doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Extract automation name from doc structure (handle both old and new formats)
        automation_name = doc.get("automation_name") or doc.get("config", {}).get("automation_name", "Unnamed Automation")

        # Build proper AutomationStatusResponse structure
        response = {
            "config_id": config_id,
            "status": doc.get("status", "draft"),
            "automation_name": automation_name,
            "deployment_info": doc.get("deployment_info", {}),
            "created_at": doc.get("created_at", doc.get("createdAt", datetime.utcnow())).isoformat() if isinstance(doc.get("created_at") or doc.get("createdAt"), datetime) else str(doc.get("created_at") or doc.get("createdAt", "")),
            "updated_at": doc.get("updated_at", doc.get("updatedAt", datetime.utcnow())).isoformat() if isinstance(doc.get("updated_at") or doc.get("updatedAt"), datetime) else str(doc.get("updated_at") or doc.get("updatedAt", "")),
        }

        # Add optional fields if they exist
        if doc.get("deployed_at") or doc.get("deployedAt"):
            deployed_at = doc.get("deployed_at") or doc.get("deployedAt")
            response["deployed_at"] = deployed_at.isoformat() if isinstance(deployed_at, datetime) else str(deployed_at)

        if doc.get("stopped_at") or doc.get("stoppedAt"):
            stopped_at = doc.get("stopped_at") or doc.get("stoppedAt")
            response["stopped_at"] = stopped_at.isoformat() if isinstance(stopped_at, datetime) else str(stopped_at)

        # Add metrics (TODO: Implement actual metrics collection from VAPI and N8N)
        # For now, return minimal metrics structure that frontend can use
        last_activity = doc.get("updated_at") or doc.get("updatedAt")
        response["metrics"] = {
            "uptime": "0 minutes",  # TODO: Calculate actual uptime
            "requests_handled": 0,  # TODO: Get from VAPI logs
            "avg_response_time": 0,  # TODO: Calculate from logs
            "errors": 0,  # TODO: Get from error tracking
            "last_activity": last_activity.isoformat() if isinstance(last_activity, datetime) else str(last_activity) if last_activity else None
        }

        # For backward compatibility with frontend's current usage
        response["callCount"] = 0  # TODO: Get from VAPI
        response["successRate"] = 0.0  # TODO: Calculate from logs
        response["lastActivity"] = last_activity.isoformat() if isinstance(last_activity, datetime) else str(last_activity) if last_activity else None

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting automation status {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get automation status: {str(e)}")

@router.post("/{config_id}/duplicate", response_model=AutomationConfigResponse)
async def duplicate_automation_config(
    config_id: str,
    duplicate_request: DuplicateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """Duplicate an automation configuration"""
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Convert string ID to ObjectId
        object_id = _convert_to_object_id(config_id)

        # Build query based on role and organization
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        # Get the original configuration (async)
        original_doc = await automation_configs_collection.find_one(query)

        if not original_doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Create duplicate
        duplicate_dict = original_doc.copy()
        del duplicate_dict["_id"]
        duplicate_dict["automationName"] = duplicate_request.newName
        duplicate_dict["status"] = AutomationStatusEnum.DRAFT
        duplicate_dict["createdAt"] = datetime.utcnow()

        # Clear deployment-specific data
        if "vapiAgent" in duplicate_dict:
            duplicate_dict["vapiAgent"]["assistantId"] = ""
            duplicate_dict["vapiAgent"]["phoneNumberId"] = ""
        if "n8nWorkflow" in duplicate_dict:
            duplicate_dict["n8nWorkflow"]["workflowId"] = ""
            duplicate_dict["n8nWorkflow"]["webhookUrl"] = ""
        if "demoSettings" in duplicate_dict:
            duplicate_dict["demoSettings"]["demoUrl"] = ""

        duplicate_dict = _prepare_for_storage(duplicate_dict, user_id)

        # Insert duplicate (async)
        result = await automation_configs_collection.insert_one(duplicate_dict)

        # Get created document (async)
        created_doc = await automation_configs_collection.find_one({"_id": result.inserted_id})

        logger.info(f"Duplicated automation config: {config_id} -> {duplicate_request.newName}")
        return _to_response(created_doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating automation config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to duplicate automation config: {str(e)}")


@router.get("/public/list")
async def list_automation_configs_public(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """List automation configurations publicly without authentication (for frontend)."""
    try:
        # Build filter query
        filter_query = {}
        if status:
            filter_query["status"] = status

        # Calculate skip for pagination
        skip = (page - 1) * per_page

        # Get total count for pagination (async)
        total = await automation_configs_collection.count_documents(filter_query)

        # Add filter to exclude configs with null/invalid _id (data integrity issue)
        filter_query["_id"] = {"$ne": None, "$exists": True}

        # Get configs from MongoDB with pagination (async)
        cursor = automation_configs_collection.find(filter_query).sort([("created_at", -1)]).skip(skip).limit(per_page)
        config_docs = await cursor.to_list(length=per_page)

        # Convert to response format
        configs = []
        for doc in config_docs:
            try:
                response_doc = _to_response(doc)
                configs.append(response_doc.dict())
            except Exception as e:
                logger.warning(f"Error converting automation config {doc.get('_id')}: {str(e)}")
                continue

        # Calculate pagination info
        pages = (total + per_page - 1) // per_page

        return {
            "configs": configs,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages
        }

    except Exception as e:
        logger.error(f"Error listing automation configs publicly: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list automation configs: {str(e)}")


@router.post("/import-vapi-assistant", response_model=AutomationConfigResponse)
async def import_vapi_assistant(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Import a VAPI assistant and create an automation config from it.

    Request body:
    {
        "assistant_id": "vapi-assistant-id",
        "automation_name": "Optional custom name"
    }
    """
    try:
        # Parse request body
        body = await request.json()
        assistant_id = body.get("assistant_id")
        automation_name = body.get("automation_name")

        if not assistant_id:
            raise HTTPException(status_code=400, detail="assistant_id is required")

        # Import VAPI service
        from ..services.vapi_service import vapi_service

        # Fetch assistant from VAPI
        logger.info(f"Fetching VAPI assistant: {assistant_id}")
        result = await vapi_service.get_assistant(assistant_id)

        if not result.get("success"):
            error_msg = result.get("error", "Failed to fetch assistant from VAPI")
            logger.error(f"VAPI assistant fetch failed: {error_msg}")
            raise HTTPException(status_code=404, detail=error_msg)

        assistant_data = result.get("assistant", {})
        assistant_name = assistant_data.get("name", "Imported Assistant")
        logger.info(f"Successfully fetched VAPI assistant: {assistant_name}")

        # Use sync service to extract comprehensive VAPI configuration
        from ..services.vapi_sync_service import get_sync_service
        import hashlib

        sync_service = get_sync_service(automation_configs_collection.database)

        # Extract complete VAPIAgent config using sync service
        vapi_agent = sync_service._extract_vapi_agent(assistant_data, assistant_id)
        vapi_agent_dict = vapi_agent.dict()

        # Compute config hash for sync tracking
        config_hash = sync_service._compute_config_hash(assistant_data)

        # Create automation config from assistant data
        user_id = current_user.get("id") or current_user.get("sub")

        config_dict = {
            "automation_name": automation_name or f"Imported: {assistant_name}",
            "company_info": {
                "name": assistant_data.get("metadata", {}).get("companyName", assistant_name),
                "description": f"Imported from VAPI assistant: {assistant_name}",
                "url": assistant_data.get("metadata", {}).get("websiteUrl", "")
            },
            "companyInfo": {  # camelCase for database
                "name": assistant_data.get("metadata", {}).get("companyName", assistant_name),
                "description": f"Imported from VAPI assistant: {assistant_name}",
                "url": assistant_data.get("metadata", {}).get("websiteUrl", "")
            },
            # Use comprehensive VAPI agent config extracted by sync service
            "vapi_agent": vapi_agent_dict,
            "vapiAgent": vapi_agent_dict,  # camelCase for database compatibility
            "n8n_workflow": {
                "workflow_id": "",
                "workflow_name": f"Workflow for {assistant_name}",
                "webhook_url": "",
                "endpoints": {
                    "calendar": "/calendar/availability",
                    "tickets": "/tickets/create",
                    "availability": "/availability/check",
                    "escalation": "/escalation/route",
                    "analytics": "/analytics/track"
                }
            },
            "n8nWorkflow": {  # camelCase for database
                "workflowId": "",
                "workflowName": f"Workflow for {assistant_name}",
                "webhookUrl": "",
                "endpoints": {
                    "calendar": "/calendar/availability",
                    "tickets": "/tickets/create",
                    "availability": "/availability/check",
                    "escalation": "/escalation/route",
                    "analytics": "/analytics/track"
                }
            },
            "integrations": {
                "calendly": {"enabled": False, "apiKey": ""},
                "supabase": {"enabled": False, "projectId": ""},
                "tavily": {"enabled": False, "apiKey": ""},
                "resend": {"enabled": False, "apiKey": ""},
                "vonage": {"enabled": False, "apiKey": ""}
            },
            "custom_tools": {
                "enabled": False,
                "selected_tools": [],
                "available_tools": []
            },
            "customTools": {  # camelCase for database
                "enabled": False,
                "selectedTools": [],
                "availableTools": []
            },
            "demo_settings": {
                "enable_demo": True,
                "demo_url": "",
                "html_template": ""
            },
            "demoSettings": {  # camelCase for database
                "enableDemo": True,
                "demoUrl": "",
                "htmlTemplate": ""
            },
            "analytics": {
                "enable_tracking": True,
                "webhook_url": "",
                "report_email": ""
            },
            "status": AutomationStatusEnum.DEPLOYED,  # Auto-deploy imported automations
            "assistant_id": assistant_id,  # Link to VAPI assistant for analytics
            "createdAt": datetime.utcnow(),
            "created_at": datetime.utcnow(),

            # VAPI Sync metadata
            "full_vapi_config": assistant_data,  # Store complete VAPI response
            "vapi_config_hash": config_hash,  # For change detection
            "vapi_sync_status": "synced",  # Synced on import
            "vapi_last_synced_at": datetime.utcnow()  # Synced now
        }

        # Set organization_id from context - CRITICAL for multi-org filtering
        # IMPORTANT: Ensure org_id is UUID format (organizations.id), not MongoDB _id
        if org_id:
            # Validate and normalize organization_id
            # Reason: Frontend might send MongoDB _id instead of UUID, need to look up correct UUID
            from ..services.organization_service import organization_service
            org = organization_service.get_organization(org_id)
            if org:
                # Use the UUID id field from organization
                config_dict["organization_id"] = org.id
                logger.info(f"✅ Using organization UUID: {org.id} for automation import")
            else:
                # org_id might be MongoDB _id, try to look up by _id
                from ..mongo import get_collection
                orgs_collection = get_collection("organizations")
                org_doc = await orgs_collection.find_one({"_id": org_id})
                if org_doc:
                    config_dict["organization_id"] = org_doc.get("id")
                    logger.warning(f"⚠️ Converted MongoDB _id to UUID: {org_id} -> {org_doc.get('id')}")
                else:
                    # Fallback to provided org_id
                    config_dict["organization_id"] = org_id
                    logger.warning(f"⚠️ Could not validate organization_id: {org_id}, using as-is")

        # Prepare for storage
        config_dict = _prepare_for_storage(config_dict, user_id)

        # Insert into MongoDB
        result = await automation_configs_collection.insert_one(config_dict)

        # Retrieve created document
        created_doc = await automation_configs_collection.find_one({"_id": result.inserted_id})

        logger.info(f"Successfully imported VAPI assistant {assistant_id} as automation config for user {user_id}")

        return _to_response(created_doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing VAPI assistant: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to import VAPI assistant: {str(e)}")


@router.post("/{config_id}/trigger-call")
async def trigger_test_call(
    config_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Trigger a test VAPI call for an automation.

    Request body (optional):
    {
        "customer_number": "+1234567890"  # Defaults to +12397783680
    }
    """
    try:
        # Parse request body
        body = await request.json() if request.headers.get("content-length") else {}
        customer_number = body.get("customer_number", "+12397783680")

        # Convert string ID to ObjectId
        object_id = _convert_to_object_id(config_id)

        # Get automation config
        doc = await automation_configs_collection.find_one({"_id": object_id})

        if not doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Get assistant_id from config
        assistant_id = doc.get("assistant_id")
        if not assistant_id:
            # Try to get from vapi_agent or vapiAgent
            vapi_data = doc.get("vapi_agent") or doc.get("vapiAgent") or {}
            assistant_id = vapi_data.get("assistant_id") or vapi_data.get("assistantId")

        if not assistant_id:
            raise HTTPException(
                status_code=400,
                detail="No VAPI assistant ID found for this automation"
            )

        # Check for custom settings override and apply to VAPI assistant
        vapi_agent = doc.get("vapi_agent") or doc.get("vapiAgent") or {}
        custom_override = vapi_agent.get("custom_settings_override")

        if custom_override:
            logger.info(f"Applying custom settings to VAPI assistant {assistant_id}")
            from ..services.vapi_assistant_builder import build_vapi_assistant_config
            import httpx

            # Build VAPI-compatible config with custom provider URLs
            vapi_config = build_vapi_assistant_config(vapi_agent, assistant_id)

            # Update VAPI assistant with custom settings
            update_payload = {}
            if "voice" in vapi_config:
                update_payload["voice"] = vapi_config["voice"]
            if "transcriber" in vapi_config:
                update_payload["transcriber"] = vapi_config["transcriber"]
            if "model" in vapi_config:
                update_payload["model"] = vapi_config["model"]
            if "metadata" in vapi_config:
                update_payload["metadata"] = vapi_config["metadata"]

            if update_payload:
                vapi_api_key = os.getenv("VAPI_API_KEY") or os.getenv("VAPI_PRIVATE_KEY")
                if vapi_api_key:
                    async with httpx.AsyncClient() as http_client:
                        resp = await http_client.patch(
                            f"https://api.vapi.ai/assistant/{assistant_id}",
                            headers={
                                "Authorization": f"Bearer {vapi_api_key}",
                                "Content-Type": "application/json"
                            },
                            json=update_payload,
                            timeout=30.0
                        )
                        if resp.status_code == 200:
                            logger.info(f"Applied custom settings: TTS={update_payload.get('voice', {}).get('provider')}, ASR={update_payload.get('transcriber', {}).get('provider')}, LLM={update_payload.get('model', {}).get('provider')}")
                        else:
                            logger.warning(f"Failed to apply custom settings: {resp.status_code} - {resp.text[:200]}")

        # Use VAPI service to trigger call
        from ..services.vapi_service import vapi_service

        # Phone number ID from environment or default
        phone_number_id = os.getenv("VAPI_US_PHONE_ID", "6c5af6e1-a2b7-41d6-ac04-4c9691bf73e4")

        logger.info(f"Triggering VAPI call for automation {config_id}, assistant {assistant_id}")

        result = await vapi_service.create_phone_call(
            phone_number_id=phone_number_id,
            customer_number=customer_number,
            assistant_id=assistant_id
        )

        if not result.get("success"):
            error_msg = result.get("error", "Failed to trigger call")
            logger.error(f"VAPI call trigger failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        call_data = result.get("call", {})

        return {
            "success": True,
            "call_id": call_data.get("id"),
            "status": call_data.get("status"),
            "customer_number": customer_number,
            "assistant_id": assistant_id,
            "message": f"Test call initiated to {customer_number}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering call for automation {config_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to trigger call: {str(e)}")


# ============================
# Campaign Management Endpoints
# ============================

@router.post("/{config_id}/campaigns", response_model=AutomationCampaign)
async def create_campaign(
    config_id: str,
    campaign_request: CampaignCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Create a new campaign linking an automation to an audience.

    This creates a campaign that will call all contacts in the specified audience
    using the automation's VAPI assistant configuration.
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Verify automation exists with organization filtering
        object_id = _convert_to_object_id(config_id)
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        automation_doc = await automation_configs_collection.find_one(query)

        if not automation_doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Get organization_id from automation (preferred) or from context
        # Reason: Campaign should inherit organization from its parent automation
        campaign_org_id = automation_doc.get("organization_id") or automation_doc.get("tenant_id") or org_id

        # Create campaign using service
        from ..services.campaign_execution_service import campaign_service

        campaign = await campaign_service.create_campaign(campaign_request, user_id, campaign_org_id)

        logger.info(f"Created campaign for automation {config_id} and audience {campaign_request.audience_id}")

        return campaign

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create campaign: {str(e)}")


@router.get("/{config_id}/campaigns")
async def list_campaigns(
    config_id: str,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    List all campaigns for an automation.

    Optionally filter by status (pending, running, paused, completed, failed).
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Verify automation exists with organization filtering
        object_id = _convert_to_object_id(config_id)
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        automation_doc = await automation_configs_collection.find_one(query)

        if not automation_doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Get campaigns from service
        from ..services.campaign_execution_service import campaign_service

        result = await campaign_service.list_campaigns(
            automation_id=config_id,
            status=status,
            limit=limit,
            offset=offset
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing campaigns: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list campaigns: {str(e)}")


@router.post("/{config_id}/campaigns/{campaign_id}/start")
async def start_campaign(
    config_id: str,
    campaign_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Start a campaign to begin calling contacts.

    This will initiate sequential calling through the audience contact list.
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Verify automation exists with organization filtering
        object_id = _convert_to_object_id(config_id)
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        automation_doc = await automation_configs_collection.find_one(query)

        if not automation_doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Start campaign using service
        from ..services.campaign_execution_service import campaign_service

        campaign = await campaign_service.start_campaign(campaign_id)

        logger.info(f"Started campaign {campaign_id} for automation {config_id}")

        return {
            "success": True,
            "campaign": campaign.dict(),
            "message": "Campaign started successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting campaign: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start campaign: {str(e)}")


@router.post("/{config_id}/campaigns/{campaign_id}/pause")
async def pause_campaign(
    config_id: str,
    campaign_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Pause a running campaign.

    This will stop making new calls but preserve progress for later resumption.
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Verify automation exists with organization filtering
        object_id = _convert_to_object_id(config_id)
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        automation_doc = await automation_configs_collection.find_one(query)

        if not automation_doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Pause campaign using service
        from ..services.campaign_execution_service import campaign_service

        campaign = await campaign_service.pause_campaign(campaign_id)

        logger.info(f"Paused campaign {campaign_id} for automation {config_id}")

        return {
            "success": True,
            "campaign": campaign.dict(),
            "message": "Campaign paused successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to pause campaign: {str(e)}")


@router.post("/{config_id}/campaigns/{campaign_id}/resume")
async def resume_campaign(
    config_id: str,
    campaign_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Resume a paused campaign.

    This will restart calling from where the campaign was paused.
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Verify automation exists with organization filtering
        object_id = _convert_to_object_id(config_id)
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        automation_doc = await automation_configs_collection.find_one(query)

        if not automation_doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Resume campaign using service
        from ..services.campaign_execution_service import campaign_service

        campaign = await campaign_service.resume_campaign(campaign_id)

        logger.info(f"Resumed campaign {campaign_id} for automation {config_id}")

        return {
            "success": True,
            "campaign": campaign.dict(),
            "message": "Campaign resumed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming campaign: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to resume campaign: {str(e)}")


@router.get("/{config_id}/campaigns/{campaign_id}/status", response_model=CampaignStatusResponse)
async def get_campaign_status(
    config_id: str,
    campaign_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Get real-time status and progress of a campaign.

    Returns current contact, next contact, progress metrics, and estimates.
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Verify automation exists with organization filtering
        object_id = _convert_to_object_id(config_id)
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        automation_doc = await automation_configs_collection.find_one(query)

        if not automation_doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Get campaign status from service
        from ..services.campaign_execution_service import campaign_service

        status = await campaign_service.get_campaign_status(campaign_id)

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get campaign status: {str(e)}")


@router.get("/{config_id}/campaigns/{campaign_id}/calls")
async def get_campaign_calls(
    config_id: str,
    campaign_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=500, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by call status"),
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Get paginated list of all calls made in a campaign.

    Returns call details including contact info, status, outcome, duration, cost, etc.
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Verify automation exists with organization filtering
        object_id = _convert_to_object_id(config_id)
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        automation_doc = await automation_configs_collection.find_one(query)

        if not automation_doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Get campaign calls from service
        from ..services.campaign_execution_service import campaign_service

        # IMPORTANT: Always use automation's organization_id for campaign calls filter
        # Reason: Campaign calls are associated with the automation's org, not the request header org
        # The header org_id might differ if user is viewing from a different org context
        organization_id = automation_doc.get("organization_id") or automation_doc.get("tenant_id")

        result = await campaign_service.get_campaign_calls(
            campaign_id=campaign_id,
            page=page,
            limit=limit,
            status_filter=status,
            organization_id=organization_id
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign calls: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get campaign calls: {str(e)}")


@router.get("/{config_id}/campaigns/{campaign_id}/analytics", response_model=CampaignAnalyticsResponse)
async def get_campaign_analytics(
    config_id: str,
    campaign_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Get comprehensive analytics for a campaign.

    Returns outcome distribution, objections, sentiment, cost metrics, and timeline data.
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Verify automation exists with organization filtering
        object_id = _convert_to_object_id(config_id)
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        automation_doc = await automation_configs_collection.find_one(query)

        if not automation_doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Get campaign analytics from service
        from ..services.campaign_execution_service import campaign_service

        analytics = await campaign_service.get_campaign_analytics(campaign_id)

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get campaign analytics: {str(e)}")


@router.put("/{config_id}/campaigns/{campaign_id}")
async def update_campaign(
    config_id: str,
    campaign_id: str,
    config: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Update campaign configuration settings.

    This allows editing campaign settings like:
    - call_delay_seconds
    - max_retries
    - retry_on_no_answer
    - max_concurrent_calls

    Note: Cannot edit automation_id or audience_id after creation.
    Campaign must be paused before editing.

    Args:
        config_id: Automation config ID
        campaign_id: Campaign ID to update
        config: Updated campaign configuration

    Returns:
        Updated campaign object
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Verify automation exists with organization filtering
        object_id = _convert_to_object_id(config_id)
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        automation_doc = await automation_configs_collection.find_one(query)

        if not automation_doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Update campaign using service
        from ..services.campaign_execution_service import campaign_service

        campaign = await campaign_service.update_campaign(campaign_id, config)

        logger.info(f"Updated campaign {campaign_id} for automation {config_id}")

        return {
            "success": True,
            "campaign": campaign.dict(),
            "message": "Campaign updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating campaign {campaign_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update campaign: {str(e)}")


@router.post("/{config_id}/campaigns/{campaign_id}/retry-missed")
async def retry_missed_calls(
    config_id: str,
    campaign_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Retry missed calls for a campaign.
    
    Missed calls are calls where status is 'failed' OR duration/cost are missing/zero.
    This will reset those calls to pending status so they can be retried when the campaign resumes.
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Verify automation exists with organization filtering
        object_id = _convert_to_object_id(config_id)
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        automation_doc = await automation_configs_collection.find_one(query)

        if not automation_doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Retry missed calls using service
        from ..services.campaign_execution_service import campaign_service

        result = await campaign_service.retry_missed_calls(campaign_id)

        logger.info(f"Retried {result.get('retry_count', 0)} missed calls for campaign {campaign_id}")

        return {
            "success": True,
            "retry_count": result.get("retry_count", 0),
            "message": result.get("message", "Missed calls queued for retry")
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying missed calls for campaign {campaign_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to retry missed calls: {str(e)}")


@router.delete("/{config_id}/campaigns/{campaign_id}")
async def delete_campaign(
    config_id: str,
    campaign_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Delete a campaign and all associated call records.

    This will:
    1. Verify automation ownership
    2. Stop the campaign if it's running
    3. Delete all campaign call records
    4. Delete the campaign itself

    Args:
        config_id: Automation config ID
        campaign_id: Campaign ID to delete

    Returns:
        Success message with deletion details
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Verify automation exists with organization filtering
        object_id = _convert_to_object_id(config_id)
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        automation_doc = await automation_configs_collection.find_one(query)

        if not automation_doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Delete campaign using service
        from ..services.campaign_execution_service import campaign_service

        success = await campaign_service.delete_campaign(campaign_id)

        if not success:
            raise HTTPException(status_code=404, detail="Campaign not found")

        logger.info(f"Deleted campaign {campaign_id} for automation {config_id} by user {user_id}")

        return {
            "success": True,
            "message": "Campaign deleted successfully",
            "campaign_id": campaign_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting campaign {campaign_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete campaign: {str(e)}")


# ============================
# Knowledge Base Management Endpoints
# ============================

class KnowledgeBaseLinked(BaseModel):
    """Response model for linked knowledge base"""
    collection_name: str

class KnowledgeBaseLinkRequest(BaseModel):
    """Request model for linking knowledge base to automation"""
    collection_name: str = Field(..., min_length=1, max_length=100, description="Knowledge base collection name to link")

@router.get("/{config_id}/knowledge-bases")
async def get_linked_knowledge_bases(
    config_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Get all knowledge bases linked to an automation.

    Returns list of linked collection names.
    Note: Users with universal_admin role can access any automation config.
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Convert string ID to ObjectId
        object_id = _convert_to_object_id(config_id)

        # Build query based on role and organization
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        # Get the automation config
        doc = await automation_configs_collection.find_one(query)

        if not doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Get knowledge_base_collections field (default to empty list)
        kb_collections = doc.get("knowledge_base_collections", [])

        return {
            "success": True,
            "knowledge_bases": kb_collections,
            "total": len(kb_collections)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting linked knowledge bases for {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get linked knowledge bases: {str(e)}")


@router.post("/{config_id}/knowledge-bases")
async def link_knowledge_base(
    config_id: str,
    request: KnowledgeBaseLinkRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Link a knowledge base collection to an automation.

    This will add the collection to the automation's knowledge_base_collections list.
    The linked knowledge bases can be used by the automation for RAG queries.
    Note: Users with universal_admin role can link knowledge bases to any automation config.
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Convert string ID to ObjectId
        object_id = _convert_to_object_id(config_id)

        # Build query based on role and organization
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        # Get the automation config
        doc = await automation_configs_collection.find_one(query)

        if not doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Get current knowledge_base_collections
        kb_collections = doc.get("knowledge_base_collections", [])

        # Check if already linked
        if request.collection_name in kb_collections:
            return {
                "success": True,
                "message": "Knowledge base already linked",
                "collection_name": request.collection_name
            }

        # Add the collection
        kb_collections.append(request.collection_name)

        # Update the automation config
        await automation_configs_collection.update_one(
            {"_id": object_id},
            {"$set": {
                "knowledge_base_collections": kb_collections,
                "updated_at": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }}
        )

        logger.info(f"Linked knowledge base {request.collection_name} to automation {config_id}")

        return {
            "success": True,
            "message": "Knowledge base linked successfully",
            "collection_name": request.collection_name
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking knowledge base to {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to link knowledge base: {str(e)}")


@router.delete("/{config_id}/knowledge-bases/{collection_name}")
async def unlink_knowledge_base(
    config_id: str,
    collection_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Unlink a knowledge base collection from an automation.

    This will remove the collection from the automation's knowledge_base_collections list.
    Note: Users with universal_admin role can unlink knowledge bases from any automation config.
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Convert string ID to ObjectId
        object_id = _convert_to_object_id(config_id)

        # Build query based on role and organization
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        # Get the automation config
        doc = await automation_configs_collection.find_one(query)

        if not doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Get current knowledge_base_collections
        kb_collections = doc.get("knowledge_base_collections", [])

        # Check if collection is linked
        if collection_name not in kb_collections:
            raise HTTPException(status_code=404, detail="Knowledge base not linked to this automation")

        # Remove the collection
        kb_collections.remove(collection_name)

        # Update the automation config
        await automation_configs_collection.update_one(
            {"_id": object_id},
            {"$set": {
                "knowledge_base_collections": kb_collections,
                "updated_at": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }}
        )

        logger.info(f"Unlinked knowledge base {collection_name} from automation {config_id}")

        return {
            "success": True,
            "message": "Knowledge base unlinked successfully",
            "collection_name": collection_name
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unlinking knowledge base from {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to unlink knowledge base: {str(e)}")


# ============================
# VAPI Sync Endpoints
# ============================

@router.post("/{config_id}/sync-from-vapi")
async def sync_from_vapi(
    config_id: str,
    force: bool = Query(False, description="Force sync even if config appears unchanged"),
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Sync automation config from VAPI assistant.

    This fetches the latest VAPI assistant configuration and updates the platform config,
    including all settings like Deepgram keywords, transcriber settings, messages, etc.

    Args:
        config_id: Automation config ID
        force: Force sync even if config appears unchanged

    Returns:
        Sync result with change details
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Convert string ID to ObjectId
        object_id = _convert_to_object_id(config_id)

        # Build query based on role and organization
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        # Verify automation exists
        doc = await automation_configs_collection.find_one(query)

        if not doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Get sync service
        from ..services.vapi_sync_service import get_sync_service
        sync_service = get_sync_service(automation_configs_collection.database)

        # Perform sync
        result = await sync_service.sync_config_from_vapi(config_id, force=force)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Sync failed"))

        logger.info(f"VAPI sync completed for automation {config_id} by user {user_id}")

        return {
            "success": True,
            "message": "Successfully synced from VAPI" if result.get("changed") else "Config already up-to-date",
            **result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing from VAPI for {config_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to sync from VAPI: {str(e)}")


@router.get("/{config_id}/sync-status")
async def get_sync_status(
    config_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Check VAPI synchronization status for an automation.

    Compares platform config with current VAPI config to determine if they're in sync.

    Args:
        config_id: Automation config ID

    Returns:
        Sync status details
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Convert string ID to ObjectId
        object_id = _convert_to_object_id(config_id)

        # Build query based on role and organization
        query = {"_id": object_id}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        # Verify automation exists
        doc = await automation_configs_collection.find_one(query)

        if not doc:
            raise HTTPException(status_code=404, detail="Automation config not found")

        # Get sync service
        from ..services.vapi_sync_service import get_sync_service
        sync_service = get_sync_service(automation_configs_collection.database)

        # Check sync status
        result = await sync_service.check_sync_status(config_id)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to check sync status"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking sync status for {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check sync status: {str(e)}")


@router.get("/analytics/overview")
async def get_analytics_overview(
    start_date: Optional[str] = Query(None, description="Start date for analytics period"),
    end_date: Optional[str] = Query(None, description="End date for analytics period"),
    current_user: Dict[str, Any] = Depends(get_current_user_mongo),
    org_id: Optional[str] = Depends(get_organization_context)
):
    """
    Get analytics overview for all automation configurations.

    Provides aggregated metrics including:
    - Total configurations and deployments
    - Success rates and performance metrics
    - Templates usage

    Args:
        start_date: Optional start date for metrics (ISO format)
        end_date: Optional end date for metrics (ISO format)

    Returns:
        Analytics overview data
    """
    try:
        from datetime import datetime, timedelta

        user_id = current_user.get("id") or current_user.get("sub")
        is_universal_admin = current_user.get("is_universal_admin", False)

        # Build query based on role and organization
        query = {}
        if not is_universal_admin:
            org_filter = get_user_organization_filter(current_user, org_id)
            query.update(org_filter)

        # Parse date range
        if not end_date:
            end_dt = datetime.now()
        else:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        if not start_date:
            start_dt = end_dt - timedelta(days=7)  # Default to 7 days
        else:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        # Get all configs for the user/organization
        configs_cursor = automation_configs_collection.find(query)
        all_configs = await configs_cursor.to_list(length=None)

        # Count total configurations
        total_configurations = len(all_configs)

        # Count deployed/active configurations
        active_deployments = sum(1 for config in all_configs
                                  if config.get("status") in ["deployed", "running", "active"])

        # Count configurations by template
        template_counts = {}
        for config in all_configs:
            template = config.get("template", "custom")
            template_counts[template] = template_counts.get(template, 0) + 1

        # Count deployments by status
        deployment_stats = {}
        for config in all_configs:
            status = config.get("status", "draft")
            deployment_stats[status] = deployment_stats.get(status, 0) + 1

        # Calculate overall success rate (based on configs with successful deployments)
        successful_configs = sum(1 for config in all_configs
                                if config.get("status") == "deployed")
        success_rate = (successful_configs / total_configurations) if total_configurations > 0 else 0

        # Get total templates count (unique templates)
        total_templates = len(template_counts)

        # Get call analytics from vapi_calls collection
        # Reason: Frontend expects total_calls, avg_sentiment, total_cost
        calls_collection = get_collection("vapi_calls")

        # Build calls query - filter by organization and date range
        calls_query = {}
        if not is_universal_admin:
            calls_query.update(org_filter)
        calls_query["created_at"] = {"$gte": start_dt, "$lte": end_dt}

        # Aggregate call metrics
        # Reason: Cost is stored in vonage_cost field, not cost field
        call_pipeline = [
            {"$match": calls_query},
            {"$group": {
                "_id": None,
                "total_calls": {"$sum": 1},
                "total_cost": {"$sum": {"$ifNull": ["$vonage_cost", 0]}},
                "avg_sentiment": {"$avg": {"$ifNull": ["$sentiment_score", 0]}}
            }}
        ]

        call_stats_cursor = calls_collection.aggregate(call_pipeline)
        call_stats_list = await call_stats_cursor.to_list(length=1)
        call_stats = call_stats_list[0] if call_stats_list else {
            "total_calls": 0,
            "total_cost": 0,
            "avg_sentiment": 0
        }

        return {
            "period": {
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat()
            },
            "templates": {
                "by_type": template_counts,
                "total_unique": total_templates
            },
            "configurations": {
                "by_status": deployment_stats,
                "total": total_configurations
            },
            "deployments": {
                "active": active_deployments,
                "inactive": total_configurations - active_deployments,
                "by_status": deployment_stats
            },
            "summary": {
                "total_templates": total_templates,
                "total_configurations": total_configurations,
                "active_deployments": active_deployments,
                "success_rate": round(success_rate * 100, 2)  # Convert to percentage
            },
            # Frontend-expected fields for UnifiedAutomationDashboard
            "total_automations": total_configurations,
            "deployed_automations": active_deployments,
            "success_rate": success_rate,  # 0-1 range (frontend multiplies by 100)
            "total_calls": call_stats.get("total_calls", 0),
            "avg_sentiment": call_stats.get("avg_sentiment", 0),
            "total_cost": call_stats.get("total_cost", 0),
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting analytics overview: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get analytics overview: {str(e)}")

