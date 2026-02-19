"""
VAPI Sync Service

Handles synchronization between VAPI assistants and platform automation configs.
Ensures platform configs stay up-to-date with VAPI assistant changes.
"""

import logging
import hashlib
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models.automation_config import (
    VAPIAgent,
    VoiceSettings,
    TranscriberSettings,
    ModelSettings,
    SyncStatus
)

# Import shared VAPI service
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../shared'))
from integration.vapi import vapi_service

logger = logging.getLogger(__name__)


class VAPISyncService:
    """
    Service for synchronizing VAPI assistant configs with platform automation configs.

    This service ensures that updates made in VAPI (like Deepgram keywords) are
    reflected in the platform's MongoDB automation configs.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize VAPI sync service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.configs_collection = db.automation_configs
        self.vapi_service = vapi_service

    def _compute_config_hash(self, vapi_config: Dict[str, Any]) -> str:
        """
        Compute MD5 hash of VAPI config for change detection.

        Args:
            vapi_config: Complete VAPI assistant configuration

        Returns:
            MD5 hash string
        """
        # Remove dynamic fields that change frequently but aren't config changes
        config_copy = vapi_config.copy()
        for field in ['createdAt', 'updatedAt', 'orgId', 'id']:
            config_copy.pop(field, None)

        # Sort keys for consistent hashing
        config_json = json.dumps(config_copy, sort_keys=True)
        return hashlib.md5(config_json.encode()).hexdigest()

    def _extract_transcriber_settings(self, vapi_config: Dict[str, Any]) -> Optional[TranscriberSettings]:
        """
        Extract transcriber settings from VAPI config.

        Args:
            vapi_config: Complete VAPI assistant configuration

        Returns:
            TranscriberSettings object or None
        """
        transcriber_data = vapi_config.get('transcriber')
        if not transcriber_data:
            return None

        # Note: VAPI uses 'keyterm' (singular) not 'keyterms' (plural)
        # Check both for compatibility
        keyterms = transcriber_data.get('keyterm') or transcriber_data.get('keyterms', [])

        return TranscriberSettings(
            provider=transcriber_data.get('provider'),
            model=transcriber_data.get('model'),
            language=transcriber_data.get('language'),
            keywords=transcriber_data.get('keywords', []),
            keyterms=keyterms,
            endpointing=transcriber_data.get('endpointing'),
            smart_format=transcriber_data.get('smartFormat')
        )

    def _extract_model_settings(self, vapi_config: Dict[str, Any]) -> Optional[ModelSettings]:
        """
        Extract LLM model settings from VAPI config.

        Args:
            vapi_config: Complete VAPI assistant configuration

        Returns:
            ModelSettings object or None
        """
        model_data = vapi_config.get('model', {})
        if not model_data:
            return None

        return ModelSettings(
            provider=model_data.get('provider'),
            model=model_data.get('model'),
            temperature=model_data.get('temperature'),
            max_tokens=model_data.get('maxTokens'),
            top_p=model_data.get('topP'),
            frequency_penalty=model_data.get('frequencyPenalty'),
            presence_penalty=model_data.get('presencePenalty')
        )

    def _extract_voice_settings(self, vapi_config: Dict[str, Any]) -> VoiceSettings:
        """
        Extract voice settings from VAPI config.

        Args:
            vapi_config: Complete VAPI assistant configuration

        Returns:
            VoiceSettings object
        """
        voice_data = vapi_config.get('voice', {})

        return VoiceSettings(
            voice_id=voice_data.get('voiceId', 'alloy'),
            model=vapi_config.get('model', {}).get('model', 'gpt-4o-mini'),
            max_duration=vapi_config.get('maxDurationSeconds', 600),
            provider=voice_data.get('provider'),
            speed=voice_data.get('speed'),
            temperature=voice_data.get('temperature')
        )

    def _extract_tools(self, vapi_config: Dict[str, Any]) -> List[Any]:
        """
        Extract tools from VAPI config.

        Args:
            vapi_config: Complete VAPI assistant configuration

        Returns:
            List of tool IDs or tool objects
        """
        model_data = vapi_config.get('model', {})
        return model_data.get('tools', [])

    def _extract_vapi_agent(self, vapi_config: Dict[str, Any], assistant_id: str) -> VAPIAgent:
        """
        Extract complete VAPIAgent configuration from VAPI assistant response.

        Args:
            vapi_config: Complete VAPI assistant configuration
            assistant_id: VAPI assistant ID

        Returns:
            VAPIAgent object with all fields populated
        """
        # Extract system prompt from model messages
        messages = vapi_config.get('model', {}).get('messages', [])
        system_prompt = "You are a helpful assistant"
        if messages:
            for msg in messages:
                if msg.get('role') == 'system':
                    system_prompt = msg.get('content', system_prompt)
                    break

        return VAPIAgent(
            # Core identification
            assistant_id=assistant_id,
            assistant_name=vapi_config.get('name', 'Assistant'),
            phone_number_id="",  # Not in VAPI response

            # System configuration
            system_prompt=system_prompt,
            voice_settings=self._extract_voice_settings(vapi_config),
            tools=self._extract_tools(vapi_config),

            # Enhanced VAPI settings
            transcriber=self._extract_transcriber_settings(vapi_config),
            model_settings=self._extract_model_settings(vapi_config),

            # Messages and prompts
            first_message=vapi_config.get('firstMessage'),
            voicemail_message=vapi_config.get('voicemailMessage'),
            end_call_message=vapi_config.get('endCallMessage'),

            # Advanced settings
            server_messages=vapi_config.get('serverMessages', []),
            analysis_plan=vapi_config.get('analysisPlan'),
            artifact_plan=vapi_config.get('artifactPlan'),
            message_plan=vapi_config.get('messagePlan'),
            start_speaking_plan=vapi_config.get('startSpeakingPlan'),

            # Call behavior
            silence_timeout_seconds=vapi_config.get('silenceTimeoutSeconds'),
            max_duration_seconds=vapi_config.get('maxDurationSeconds'),
            background_denoising_enabled=vapi_config.get('backgroundDenoisingEnabled'),
            voicemail_detection=vapi_config.get('voicemailDetection'),

            # Features
            dial_keypad_function_enabled=vapi_config.get('dialKeypadFunctionEnabled'),
            end_call_function_enabled=vapi_config.get('endCallFunctionEnabled'),
            recording_enabled=vapi_config.get('recordingEnabled'),

            # Metadata
            metadata=vapi_config.get('metadata', {})
        )

    async def fetch_vapi_config(self, assistant_id: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Fetch complete assistant configuration from VAPI.

        Args:
            assistant_id: VAPI assistant ID

        Returns:
            Tuple of (success, config_dict, error_message)
        """
        try:
            result = await self.vapi_service.get_assistant(assistant_id)

            if not result.get("success"):
                error = result.get("error", "Unknown error fetching from VAPI")
                logger.error(f"Failed to fetch VAPI assistant {assistant_id}: {error}")
                return False, None, error

            assistant_data = result.get("assistant", {})
            logger.info(f"Successfully fetched VAPI config for assistant {assistant_id}")

            return True, assistant_data, None

        except Exception as e:
            error_msg = f"Exception fetching VAPI config: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    async def sync_config_from_vapi(
        self,
        config_id: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Sync automation config from VAPI assistant.

        This fetches the latest VAPI assistant config and updates the platform config.

        Args:
            config_id: Platform automation config ID
            force: Force sync even if config appears unchanged

        Returns:
            Dict with sync result details
        """
        try:
            from bson import ObjectId

            # Get automation config from MongoDB
            config_doc = await self.configs_collection.find_one({"_id": ObjectId(config_id)})
            if not config_doc:
                return {
                    "success": False,
                    "error": "Automation config not found"
                }

            # Get assistant_id from config
            assistant_id = config_doc.get('assistant_id')
            if not assistant_id:
                # Try alternative locations
                vapi_agent = config_doc.get('vapi_agent') or config_doc.get('vapiAgent', {})
                assistant_id = vapi_agent.get('assistant_id') or vapi_agent.get('assistantId')

            if not assistant_id:
                return {
                    "success": False,
                    "error": "No VAPI assistant ID found in automation config"
                }

            # Fetch latest config from VAPI
            success, vapi_config, error = await self.fetch_vapi_config(assistant_id)
            if not success:
                # Update sync status to ERROR
                await self.configs_collection.update_one(
                    {"_id": ObjectId(config_id)},
                    {"$set": {
                        "vapi_sync_status": SyncStatus.ERROR.value,
                        "updated_at": datetime.utcnow(),
                        "updatedAt": datetime.utcnow()
                    }}
                )
                return {
                    "success": False,
                    "error": error
                }

            # Compute config hash
            new_hash = self._compute_config_hash(vapi_config)
            old_hash = config_doc.get('vapi_config_hash')

            # Check if config changed (unless force sync)
            if not force and old_hash == new_hash:
                logger.info(f"VAPI config unchanged for automation {config_id}")
                return {
                    "success": True,
                    "changed": False,
                    "message": "VAPI config is already up-to-date"
                }

            # Extract VAPIAgent from VAPI config
            vapi_agent = self._extract_vapi_agent(vapi_config, assistant_id)
            vapi_agent_dict = vapi_agent.dict()
            
            # Preserve custom_settings_override if it exists in current config
            existing_custom_override = config_doc.get("vapi_agent", {}).get("custom_settings_override") or \
                                     config_doc.get("vapiAgent", {}).get("custom_settings_override") or \
                                     config_doc.get("vapi_agent", {}).get("customSettingsOverride") or \
                                     config_doc.get("vapiAgent", {}).get("customSettingsOverride")
            
            if existing_custom_override:
                # Preserve custom settings override when syncing from VAPI
                # This allows users to keep their custom TTS/ASR/LLM settings even when VAPI config changes
                vapi_agent_dict["custom_settings_override"] = existing_custom_override
                logger.info(f"Preserved custom_settings_override for automation {config_id}")

            # Prepare update document
            update_doc = {
                "vapi_agent": vapi_agent_dict,
                "vapiAgent": vapi_agent_dict,  # camelCase for database compatibility
                "full_vapi_config": vapi_config,
                "vapi_config_hash": new_hash,
                "vapi_sync_status": SyncStatus.SYNCED.value,
                "vapi_last_synced_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }

            # Update MongoDB
            await self.configs_collection.update_one(
                {"_id": ObjectId(config_id)},
                {"$set": update_doc}
            )

            logger.info(f"Successfully synced automation {config_id} from VAPI")

            # Extract key changes for summary
            changes_summary = []
            if old_hash != new_hash:
                # Check for transcriber keywords changes
                old_transcriber = config_doc.get('vapi_agent', {}).get('transcriber', {})
                new_transcriber = vapi_config.get('transcriber', {})

                old_keywords = old_transcriber.get('keywords', [])
                new_keywords = new_transcriber.get('keywords', [])

                if len(old_keywords) != len(new_keywords):
                    changes_summary.append(
                        f"Transcriber keywords: {len(old_keywords)} → {len(new_keywords)}"
                    )

                # Check for transcriber keyterms changes (VAPI uses 'keyterm' singular)
                old_keyterms = old_transcriber.get('keyterms', [])
                new_keyterms = new_transcriber.get('keyterm') or new_transcriber.get('keyterms', [])

                if len(old_keyterms) != len(new_keyterms):
                    changes_summary.append(
                        f"Transcriber keyterms: {len(old_keyterms)} → {len(new_keyterms)}"
                    )

            return {
                "success": True,
                "changed": True,
                "config_id": config_id,
                "assistant_id": assistant_id,
                "old_hash": old_hash,
                "new_hash": new_hash,
                "changes_summary": changes_summary,
                "synced_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error syncing config from VAPI: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    async def check_sync_status(self, config_id: str) -> Dict[str, Any]:
        """
        Check if automation config is in sync with VAPI.

        Args:
            config_id: Platform automation config ID

        Returns:
            Dict with sync status details
        """
        try:
            from bson import ObjectId

            config_doc = await self.configs_collection.find_one({"_id": ObjectId(config_id)})
            if not config_doc:
                return {
                    "success": False,
                    "error": "Automation config not found"
                }

            assistant_id = config_doc.get('assistant_id')
            if not assistant_id:
                vapi_agent = config_doc.get('vapi_agent') or config_doc.get('vapiAgent', {})
                assistant_id = vapi_agent.get('assistant_id') or vapi_agent.get('assistantId')

            if not assistant_id:
                return {
                    "success": False,
                    "error": "No VAPI assistant ID found"
                }

            # Fetch current VAPI config
            success, vapi_config, error = await self.fetch_vapi_config(assistant_id)
            if not success:
                return {
                    "success": True,
                    "sync_status": SyncStatus.ERROR.value,
                    "error": error,
                    "assistant_id": assistant_id
                }

            # Compute hashes
            vapi_hash = self._compute_config_hash(vapi_config)
            platform_hash = config_doc.get('vapi_config_hash')

            # Determine sync status
            if not platform_hash:
                sync_status = SyncStatus.NEVER_SYNCED
            elif vapi_hash == platform_hash:
                sync_status = SyncStatus.SYNCED
            else:
                sync_status = SyncStatus.OUT_OF_SYNC

            return {
                "success": True,
                "config_id": config_id,
                "assistant_id": assistant_id,
                "sync_status": sync_status.value,
                "last_synced_at": config_doc.get('vapi_last_synced_at'),
                "platform_hash": platform_hash,
                "vapi_hash": vapi_hash,
                "is_synced": vapi_hash == platform_hash
            }

        except Exception as e:
            logger.error(f"Error checking sync status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Global sync service instance (to be initialized with db)
_sync_service: Optional[VAPISyncService] = None

def get_sync_service(db: AsyncIOMotorDatabase) -> VAPISyncService:
    """
    Get or create VAPI sync service instance.

    Args:
        db: MongoDB database instance

    Returns:
        VAPISyncService instance
    """
    global _sync_service
    if _sync_service is None:
        _sync_service = VAPISyncService(db)
    return _sync_service
