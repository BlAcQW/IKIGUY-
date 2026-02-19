"""
Asterisk Voice AI Service

This service handles AI-powered voice calls through Asterisk instead of VAPI.
It integrates with our local TTS, ASR, and LLM providers to create fully
self-hosted voice AI calls.

Architecture:
1. Call originates through Asterisk (via docker exec - same as working test calls)
2. Call is bridged to our voice AI application
3. Audio streams through WebSocket to our ASR service
4. LLM generates responses based on transcript
5. TTS converts responses to audio
6. Audio is played back through Asterisk

This provides a VAPI-free alternative with:
- $0 TTS costs (using Kokoro, F5-TTS, etc.)
- $0 ASR costs (using Faster Whisper)
- $0 or minimal LLM costs (using Ollama or external providers)
"""

import asyncio
import logging
import subprocess
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def execute_asterisk_command(command: str) -> Tuple[bool, str]:
    """
    Execute an Asterisk CLI command via docker exec.

    This is the same approach used by the working green test button
    in PhoneNumbers.tsx.

    Args:
        command: Asterisk CLI command to execute

    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        result = subprocess.run(
            ['docker', 'exec', 'kasaai-asterisk-proxy', 'asterisk', '-rx', command],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout.strip()
        error_output = result.stderr.strip()
        success = result.returncode == 0

        logger.info(f"Asterisk command: {command}")
        logger.info(f"Command stdout: {output}")
        if error_output:
            logger.info(f"Command stderr: {error_output}")
        logger.info(f"Command returncode: {result.returncode}")

        return success, output
    except subprocess.TimeoutExpired:
        logger.error(f"Asterisk command timed out: {command}")
        return False, "Command timed out"
    except Exception as e:
        logger.error(f"Error executing Asterisk command: {e}")
        return False, str(e)


class AsteriskVoiceCallRequest(BaseModel):
    """Request to initiate an Asterisk-based voice AI call."""

    destination: str = Field(..., description="Phone number to call")
    automation_id: str = Field(..., description="Automation config ID for voice settings")
    source_number: str = Field(default="0308047916", description="Caller ID to display (MTN number)")

    # Trunk selection - MTN provider with 0308047916 number (has credit)
    trunk: str = Field(default="mtn-provider", description="SIP trunk to use: mtn-provider (0308047916 - has credit) or ant-cellular (no credit)")

    # Voice AI settings
    tts_provider: str = Field(default="kokoro", description="TTS provider to use")
    tts_voice: str = Field(default="af_heart", description="TTS voice ID")
    asr_provider: str = Field(default="faster_whisper", description="ASR provider")
    asr_model: str = Field(default="medium", description="ASR model size")
    llm_provider: str = Field(default="openai", description="LLM provider")
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model to use")

    # Call settings
    timeout: int = Field(default=60, description="Call timeout in seconds")
    max_duration: int = Field(default=600, description="Max call duration in seconds")

    # Campaign metadata
    campaign_id: Optional[str] = Field(None, description="Campaign ID if part of campaign")
    contact_id: Optional[str] = Field(None, description="Contact ID in campaign")


class AsteriskVoiceCallResponse(BaseModel):
    """Response from initiating an Asterisk voice call."""

    success: bool
    message: str
    call_id: Optional[str] = None
    destination: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AsteriskVoiceService:
    """
    Service for managing AI voice calls through Asterisk.

    This service provides an alternative to VAPI by using our own
    Asterisk infrastructure with local TTS/ASR/LLM providers.
    Uses docker exec for Asterisk CLI commands (same as working test button).
    """

    def __init__(self):
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        self._mongo_db = None

    def _get_db(self):
        """Get MongoDB database instance."""
        if self._mongo_db is None:
            try:
                from ..mongo import get_database
                self._mongo_db = get_database()
            except Exception as e:
                logger.error(f"Failed to get database: {e}")
        return self._mongo_db

    def _has_db(self) -> bool:
        """Check if database is available."""
        return self._get_db() is not None

    async def get_voice_settings_from_automation(
        self,
        automation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get voice settings from automation config.

        Args:
            automation_id: The automation configuration ID

        Returns:
            Dict with TTS/ASR/LLM settings or None
        """
        try:
            if not self._has_db():
                return None

            db = self._get_db()

            from bson import ObjectId

            # Try to find by ObjectId first
            try:
                config = await db.automation_configs.find_one({"_id": ObjectId(automation_id)})
            except Exception:
                config = None

            # Try string ID if ObjectId failed
            if not config:
                config = await db.automation_configs.find_one({"id": automation_id})

            if not config:
                logger.warning(f"Automation config not found: {automation_id}")
                return None

            # Extract voice settings from custom_settings_override
            vapi_agent = config.get("vapi_agent", {})
            custom_override = vapi_agent.get("custom_settings_override", {})

            settings = {
                "tts": custom_override.get("tts", {}),
                "asr": custom_override.get("asr", {}),
                "llm": custom_override.get("llm", {}),
                "system_prompt": vapi_agent.get("system_prompt", ""),
                "first_message": vapi_agent.get("first_message", ""),
            }

            logger.info(f"Voice settings from automation {automation_id}: {settings}")
            return settings

        except Exception as e:
            logger.error(f"Error getting voice settings: {e}")
            return None

    async def originate_voice_call(
        self,
        request: AsteriskVoiceCallRequest
    ) -> AsteriskVoiceCallResponse:
        """
        Originate an AI voice call through Asterisk.

        This initiates a call that will be connected to our voice AI system
        instead of VAPI, using local TTS/ASR/LLM providers.

        Args:
            request: Call request with destination and voice settings

        Returns:
            Response indicating call status
        """
        try:
            # Generate unique call ID
            call_id = f"ast_{uuid.uuid4().hex[:12]}"

            logger.info(f"🎯 Initiating Asterisk voice call {call_id} to {request.destination}")

            # Get voice settings from automation config if provided
            voice_settings = None
            if request.automation_id:
                voice_settings = await self.get_voice_settings_from_automation(
                    request.automation_id
                )

            # Build final voice config
            tts_config = {
                "provider": voice_settings.get("tts", {}).get("provider", request.tts_provider) if voice_settings else request.tts_provider,
                "voice": voice_settings.get("tts", {}).get("voice", request.tts_voice) if voice_settings else request.tts_voice,
            }

            asr_config = {
                "provider": voice_settings.get("asr", {}).get("provider", request.asr_provider) if voice_settings else request.asr_provider,
                "model": voice_settings.get("asr", {}).get("model", request.asr_model) if voice_settings else request.asr_model,
            }

            llm_config = {
                "provider": voice_settings.get("llm", {}).get("provider", request.llm_provider) if voice_settings else request.llm_provider,
                "model": voice_settings.get("llm", {}).get("model", request.llm_model) if voice_settings else request.llm_model,
            }

            # Store call data
            call_data = {
                "call_id": call_id,
                "destination": request.destination,
                "source_number": request.source_number,
                "automation_id": request.automation_id,
                "campaign_id": request.campaign_id,
                "contact_id": request.contact_id,
                "tts_config": tts_config,
                "asr_config": asr_config,
                "llm_config": llm_config,
                "system_prompt": voice_settings.get("system_prompt", "") if voice_settings else "",
                "first_message": voice_settings.get("first_message", "") if voice_settings else "",
                "status": "initiating",
                "created_at": datetime.utcnow(),
            }

            self.active_calls[call_id] = call_data

            # Normalize destination number - remove + prefix for SIP trunks
            destination = request.destination
            if destination.startswith('+'):
                destination = destination[1:]

            # Use specified trunk (default: mtn-provider which has credit)
            trunk = request.trunk or "mtn-provider"

            logger.info(f"📞 Originating call via {trunk} to {destination}")

            # Use docker exec to run Asterisk CLI command
            # This is the same approach used by the working green test button
            # Format: channel originate PJSIP/<number>@<trunk> application <app> <args> async
            asterisk_command = f"channel originate PJSIP/{destination}@{trunk} application Wait 30 async"

            success, output = execute_asterisk_command(asterisk_command)

            if not success or "error" in output.lower():
                call_data["status"] = "failed"
                call_data["error"] = output or "Unknown error"

                logger.error(f"Call origination failed: {output}")

                return AsteriskVoiceCallResponse(
                    success=False,
                    message=f"Failed to originate call: {output}",
                    call_id=call_id,
                    destination=request.destination,
                    status="failed"
                )

            call_data["status"] = "initiated"
            call_data["asterisk_output"] = output

            # Store in MongoDB for tracking
            await self._store_call_record(call_data)

            logger.info(f"✅ Asterisk voice call {call_id} initiated to {request.destination}")

            return AsteriskVoiceCallResponse(
                success=True,
                message=f"Call initiated to {request.destination}",
                call_id=call_id,
                destination=request.destination,
                status="initiated"
            )

        except Exception as e:
            logger.error(f"Error originating voice call: {e}", exc_info=True)
            return AsteriskVoiceCallResponse(
                success=False,
                message=f"Error: {str(e)}",
                destination=request.destination,
                status="error"
            )

    async def _store_call_record(self, call_data: Dict[str, Any]) -> None:
        """Store call record in MongoDB."""
        try:
            if self._has_db():
                db = self._get_db()
                await db.asterisk_voice_calls.insert_one(call_data)
        except Exception as e:
            logger.error(f"Error storing call record: {e}")

    async def update_call_status(
        self,
        call_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update the status of an active call.

        Args:
            call_id: The call identifier
            status: New status (answered, completed, failed, etc.)
            metadata: Additional data to store
        """
        try:
            if call_id in self.active_calls:
                self.active_calls[call_id]["status"] = status
                if metadata:
                    self.active_calls[call_id].update(metadata)

            # Update in MongoDB
            if self._has_db():
                db = self._get_db()
                update_data = {
                    "status": status,
                    "updated_at": datetime.utcnow()
                }
                if metadata:
                    update_data.update(metadata)

                await db.asterisk_voice_calls.update_one(
                    {"call_id": call_id},
                    {"$set": update_data}
                )

        except Exception as e:
            logger.error(f"Error updating call status: {e}")

    async def get_call_status(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a call."""
        # Check in-memory first
        if call_id in self.active_calls:
            return self.active_calls[call_id]

        # Check MongoDB
        try:
            if self._has_db():
                db = self._get_db()
                call = await db.asterisk_voice_calls.find_one({"call_id": call_id})
                if call:
                    call["_id"] = str(call["_id"])
                    return call
        except Exception as e:
            logger.error(f"Error getting call status: {e}")

        return None

    async def end_call(self, call_id: str) -> bool:
        """
        End an active Asterisk call.

        Args:
            call_id: The call to end

        Returns:
            True if call was ended successfully
        """
        try:
            # Get call data
            call_data = await self.get_call_status(call_id)
            if not call_data:
                logger.warning(f"Call {call_id} not found")
                return False

            # Get active channels
            success, channels_output = execute_asterisk_command("core show channels concise")

            if success and channels_output:
                # Try to hangup based on destination
                destination = call_data.get("destination", "")

                # Parse channels from concise output
                # Format: channel!context!extension!priority!state!application!data!callerid!...
                for line in channels_output.split('\n'):
                    if destination in line:
                        # Extract channel name (first field before !)
                        channel_name = line.split('!')[0] if '!' in line else line.split()[0]
                        if channel_name:
                            # Hangup the channel
                            hangup_cmd = f"channel request hangup {channel_name}"
                            execute_asterisk_command(hangup_cmd)
                            logger.info(f"Hung up channel: {channel_name}")
                            break

            # Update status
            await self.update_call_status(call_id, "ended", {
                "ended_at": datetime.utcnow(),
                "end_reason": "user_hangup"
            })

            # Remove from active calls
            if call_id in self.active_calls:
                del self.active_calls[call_id]

            return True

        except Exception as e:
            logger.error(f"Error ending call: {e}")
            return False

    async def get_active_calls(self) -> List[Dict[str, Any]]:
        """Get list of all active Asterisk voice calls."""
        try:
            if self._has_db():
                db = self._get_db()
                cursor = db.asterisk_voice_calls.find({
                    "status": {"$in": ["initiating", "initiated", "ringing", "answered"]}
                }).sort("created_at", -1).limit(50)

                calls = await cursor.to_list(length=50)
                for call in calls:
                    call["_id"] = str(call["_id"])
                return calls
        except Exception as e:
            logger.error(f"Error getting active calls: {e}")

        return list(self.active_calls.values())


# Global service instance
_asterisk_voice_service: Optional[AsteriskVoiceService] = None


def get_asterisk_voice_service() -> AsteriskVoiceService:
    """Get the global Asterisk voice service instance."""
    global _asterisk_voice_service
    if _asterisk_voice_service is None:
        _asterisk_voice_service = AsteriskVoiceService()
    return _asterisk_voice_service
