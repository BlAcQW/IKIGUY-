"""
Asterisk Manager Interface (AMI) Client
Handles low-level AMI operations for SIP peer management

IMPORTANT: This client uses a persistent connection pool to avoid memory leaks.
Do NOT create new Manager instances for each operation.
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import weakref

logger = logging.getLogger(__name__)

# Try to import panoramisk
try:
    from panoramisk import Manager
    PANORAMISK_AVAILABLE = True
except ImportError:
    logger.warning("panoramisk not installed - AMI operations will be simulated")
    PANORAMISK_AVAILABLE = False
    Manager = None


class AsteriskAMIClient:
    """
    Client for Asterisk Manager Interface operations
    Provides async methods for SIP peer management

    Uses a persistent connection to avoid memory leaks from creating
    new connections for each operation.
    """

    def __init__(self):
        """Initialize AMI client with environment configuration"""
        self.host = os.getenv('ASTERISK_AMI_HOST', '127.0.0.1')
        self.port = int(os.getenv('ASTERISK_AMI_PORT', 5038))
        self.username = os.getenv('ASTERISK_AMI_USER', 'kasaai')
        self.secret = os.getenv('ASTERISK_AMI_SECRET')

        if not self.secret:
            logger.warning("ASTERISK_AMI_SECRET not set - using simulation mode")
            self.simulation_mode = True
        else:
            self.simulation_mode = not PANORAMISK_AVAILABLE

        # Persistent connection - reused across operations
        self._manager: Optional['Manager'] = None
        self._manager_lock = asyncio.Lock()
        self._connected = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 3

        # Cache for status to reduce AMI calls
        self._status_cache: Optional[Dict[str, Any]] = None
        self._status_cache_time: Optional[datetime] = None
        self._status_cache_ttl = 5  # seconds

        logger.info(f"AMI Client initialized (simulation={self.simulation_mode})")

    async def _get_manager(self) -> Optional['Manager']:
        """
        Get or create a persistent AMI manager connection.

        This method reuses the same connection across multiple operations
        to prevent memory leaks from creating new connections.

        Returns:
            Manager instance or None if simulation mode
        """
        if self.simulation_mode:
            return None

        async with self._manager_lock:
            # Check if we have a valid connection
            if self._manager is not None and self._connected:
                return self._manager

            # Clean up old manager if exists
            if self._manager is not None:
                try:
                    self._manager.close()
                except Exception:
                    pass
                self._manager = None
                self._connected = False

            # Create new connection
            try:
                self._manager = Manager(
                    host=self.host,
                    port=self.port,
                    username=self.username,
                    secret=self.secret,
                    ping_delay=30,  # Reduce ping frequency to avoid spam
                    reconnect_timeout=5
                )
                await self._manager.connect()
                self._connected = True
                self._reconnect_attempts = 0
                logger.info(f"Connected to AMI at {self.host}:{self.port}")
                return self._manager
            except Exception as e:
                self._reconnect_attempts += 1
                logger.error(f"Failed to connect to AMI (attempt {self._reconnect_attempts}): {e}")
                self._manager = None
                self._connected = False
                raise

    async def _connect(self) -> Optional['Manager']:
        """
        Deprecated: Use _get_manager() instead for persistent connections.
        Kept for backwards compatibility but now returns the shared manager.

        Returns:
            Manager instance or None if simulation mode
        """
        return await self._get_manager()

    async def close(self):
        """
        Close the persistent AMI connection.
        Call this when shutting down the application.
        """
        async with self._manager_lock:
            if self._manager is not None:
                try:
                    self._manager.close()
                    logger.info("AMI connection closed")
                except Exception as e:
                    logger.error(f"Error closing AMI connection: {e}")
                finally:
                    self._manager = None
                    self._connected = False

    def _mark_disconnected(self):
        """Mark the connection as disconnected so it will be recreated."""
        self._connected = False

    async def test_connection(self) -> bool:
        """
        Test AMI connection

        Returns:
            bool: True if connection successful
        """
        if self.simulation_mode:
            logger.info("Simulating successful connection test")
            return True

        try:
            manager = await self._get_manager()
            # Don't close - we're using persistent connection
            return manager is not None and self._connected
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            self._mark_disconnected()
            return False

    async def get_version(self) -> Optional[str]:
        """
        Get Asterisk version

        Returns:
            Version string or None
        """
        if self.simulation_mode:
            return "Asterisk 20.0.0 (Simulated)"

        try:
            manager = await self._get_manager()
            if not manager:
                return None
            response = await manager.send_action({'Action': 'CoreShowChannels'})
            version = response.get('CoreVersion', 'Unknown') if isinstance(response, dict) else 'Unknown'
            # Don't close - persistent connection
            return version
        except Exception as e:
            logger.error(f"Failed to get version: {e}")
            self._mark_disconnected()
            return None

    async def create_sip_peer(
        self,
        number: str,
        sip_username: str,
        sip_password: str,
        webhook_url: str,
        context: str = "kasaai-virtual"
    ) -> bool:
        """
        Create SIP peer in Asterisk

        Creates PJSIP endpoint, auth, and AOR sections by writing to config file
        Stores webhook URL in AstDB

        Args:
            number: Phone number (E.164 format)
            sip_username: SIP username for authentication
            sip_password: SIP password for authentication
            webhook_url: Webhook URL for incoming calls
            context: Asterisk dialplan context

        Returns:
            bool: True if successful
        """
        if self.simulation_mode:
            logger.info(f"[SIMULATION] Creating SIP peer for {number}")
            logger.info(f"  Username: {sip_username}")
            logger.info(f"  Context: {context}")
            logger.info(f"  Webhook: {webhook_url}")
            await asyncio.sleep(0.1)  # Simulate network delay
            return True

        try:
            # Write PJSIP configuration to file
            config_path = "/opt/kasaai/asterisk/config/pjsip_kasaai.conf"
            self._write_pjsip_peer_config(config_path, number, sip_username, sip_password, context)

            # Get persistent AMI connection
            manager = await self._get_manager()
            if not manager:
                logger.error("Failed to get AMI manager connection")
                return False

            # Store webhook in AstDB
            await manager.send_action({
                'Action': 'DBPut',
                'Family': 'kasaai',
                'Key': f'webhook/{number}',
                'Val': webhook_url
            })

            # Reload PJSIP
            await manager.send_action({'Action': 'PJSIPReload'})

            # Don't close - persistent connection

            logger.info(f"Created SIP peer for {number}")
            return True

        except Exception as e:
            logger.error(f"Failed to create SIP peer: {e}")
            logger.exception(e)
            self._mark_disconnected()
            return False

    def _write_pjsip_peer_config(
        self,
        config_path: str,
        number: str,
        sip_username: str,
        sip_password: str,
        context: str
    ):
        """
        Write PJSIP peer configuration to file

        Creates endpoint, auth, and AOR sections for a SIP peer

        Args:
            config_path: Path to pjsip_kasaai.conf
            number: Phone number
            sip_username: SIP username
            sip_password: SIP password
            context: Dialplan context
        """
        config_template = f"""
; SIP Peer for {number}
; Created: {datetime.now().isoformat()}

[{sip_username}]
type=endpoint
context={context}
disallow=all
allow=ulaw
allow=alaw
allow=opus
auth={sip_username}-auth
aors={sip_username}-aor
direct_media=no
ice_support=yes
force_rport=yes
rewrite_contact=yes
rtp_symmetric=yes

[{sip_username}-auth]
type=auth
auth_type=userpass
password={sip_password}
username={sip_username}

[{sip_username}-aor]
type=aor
max_contacts=5
qualify_frequency=60
remove_existing=yes

"""
        try:
            # Read existing content
            try:
                with open(config_path, 'r') as f:
                    existing_content = f.read()
            except FileNotFoundError:
                existing_content = "; Kasa AI Dynamic SIP Peers\n; Auto-generated by Asterisk REST API\n\n"

            # Check if peer already exists
            if f"[{sip_username}]" in existing_content:
                logger.warning(f"SIP peer {sip_username} already exists, overwriting")
                # Remove existing peer configuration
                lines = existing_content.split('\n')
                new_lines = []
                skip = False
                for line in lines:
                    if line.strip().startswith(f"; SIP Peer for {number}"):
                        skip = True
                    elif skip and line.strip() == "":
                        # Empty line marks end of section
                        skip = False
                        continue
                    elif not skip:
                        new_lines.append(line)
                existing_content = '\n'.join(new_lines)

            # Append new peer configuration
            with open(config_path, 'w') as f:
                f.write(existing_content)
                f.write(config_template)

            logger.info(f"Wrote PJSIP configuration for {sip_username}")

        except Exception as e:
            logger.error(f"Failed to write PJSIP configuration: {e}")
            raise

    async def _create_pjsip_endpoint(
        self,
        manager: 'Manager',
        sip_username: str,
        context: str
    ):
        """Create PJSIP endpoint section"""
        await manager.send_action({
            'Action': 'UpdateConfig',
            'SrcFilename': 'pjsip_kasaai.conf',
            'DstFilename': 'pjsip_kasaai.conf',
            'Action-000000': 'NewCat',
            'Cat-000000': sip_username,
            'Action-000001': 'Append',
            'Cat-000001': sip_username,
            'Var-000001': 'type',
            'Value-000001': 'endpoint',
            'Action-000002': 'Append',
            'Cat-000002': sip_username,
            'Var-000002': 'context',
            'Value-000002': context,
            'Action-000003': 'Append',
            'Cat-000003': sip_username,
            'Var-000003': 'auth',
            'Value-000003': f'{sip_username}-auth',
            'Action-000004': 'Append',
            'Cat-000004': sip_username,
            'Var-000004': 'aors',
            'Value-000004': f'{sip_username}-aor',
            'Action-000005': 'Append',
            'Cat-000005': sip_username,
            'Var-000005': 'allow',
            'Value-000005': 'ulaw,alaw,gsm,g722',
            'Action-000006': 'Append',
            'Cat-000006': sip_username,
            'Var-000006': 'direct_media',
            'Value-000006': 'no'
        })

    async def _create_pjsip_auth(
        self,
        manager: 'Manager',
        sip_username: str,
        sip_password: str
    ):
        """Create PJSIP auth section"""
        await manager.send_action({
            'Action': 'UpdateConfig',
            'SrcFilename': 'pjsip_kasaai.conf',
            'DstFilename': 'pjsip_kasaai.conf',
            'Action-000000': 'NewCat',
            'Cat-000000': f'{sip_username}-auth',
            'Action-000001': 'Append',
            'Cat-000001': f'{sip_username}-auth',
            'Var-000001': 'type',
            'Value-000001': 'auth',
            'Action-000002': 'Append',
            'Cat-000002': f'{sip_username}-auth',
            'Var-000002': 'auth_type',
            'Value-000002': 'userpass',
            'Action-000003': 'Append',
            'Cat-000003': f'{sip_username}-auth',
            'Var-000003': 'username',
            'Value-000003': sip_username,
            'Action-000004': 'Append',
            'Cat-000004': f'{sip_username}-auth',
            'Var-000004': 'password',
            'Value-000004': sip_password
        })

    async def _create_pjsip_aor(self, manager: 'Manager', sip_username: str):
        """Create PJSIP AOR section"""
        await manager.send_action({
            'Action': 'UpdateConfig',
            'SrcFilename': 'pjsip_kasaai.conf',
            'DstFilename': 'pjsip_kasaai.conf',
            'Action-000000': 'NewCat',
            'Cat-000000': f'{sip_username}-aor',
            'Action-000001': 'Append',
            'Cat-000001': f'{sip_username}-aor',
            'Var-000001': 'type',
            'Value-000001': 'aor',
            'Action-000002': 'Append',
            'Cat-000002': f'{sip_username}-aor',
            'Var-000002': 'max_contacts',
            'Value-000002': '1',
            'Action-000003': 'Append',
            'Cat-000003': f'{sip_username}-aor',
            'Var-000003': 'remove_existing',
            'Value-000003': 'yes'
        })

    async def delete_sip_peer(self, number: str, sip_username: str) -> bool:
        """
        Delete SIP peer from Asterisk

        Args:
            number: Phone number
            sip_username: SIP username to remove

        Returns:
            bool: True if successful
        """
        if self.simulation_mode:
            logger.info(f"[SIMULATION] Deleting SIP peer {sip_username} for {number}")
            await asyncio.sleep(0.1)
            return True

        try:
            manager = await self._get_manager()
            if not manager:
                logger.error("Failed to get AMI manager connection")
                return False

            # Remove endpoint
            await manager.send_action({
                'Action': 'UpdateConfig',
                'SrcFilename': 'pjsip_kasaai.conf',
                'DstFilename': 'pjsip_kasaai.conf',
                'Action-000000': 'DelCat',
                'Cat-000000': sip_username
            })

            # Remove auth
            await manager.send_action({
                'Action': 'UpdateConfig',
                'SrcFilename': 'pjsip_kasaai.conf',
                'DstFilename': 'pjsip_kasaai.conf',
                'Action-000000': 'DelCat',
                'Cat-000000': f'{sip_username}-auth'
            })

            # Remove AOR
            await manager.send_action({
                'Action': 'UpdateConfig',
                'SrcFilename': 'pjsip_kasaai.conf',
                'DstFilename': 'pjsip_kasaai.conf',
                'Action-000000': 'DelCat',
                'Cat-000000': f'{sip_username}-aor'
            })

            # Remove webhook from AstDB
            await manager.send_action({
                'Action': 'DBDel',
                'Family': 'kasaai',
                'Key': f'webhook/{number}'
            })

            # Reload PJSIP
            await manager.send_action({'Action': 'PJSIPReload'})

            # Don't close - persistent connection

            logger.info(f"Deleted SIP peer for {number}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete SIP peer: {e}")
            self._mark_disconnected()
            return False

    async def get_sip_peer(self, sip_username: str) -> Optional[Dict[str, Any]]:
        """
        Get SIP peer information

        Args:
            sip_username: SIP username to query

        Returns:
            Dict with peer information or None
        """
        if self.simulation_mode:
            logger.info(f"[SIMULATION] Getting SIP peer {sip_username}")
            return {
                "username": sip_username,
                "status": "active",
                "registered": True,
                "contact": f"sip:{sip_username}@192.168.1.100:5060"
            }

        try:
            manager = await self._get_manager()
            if not manager:
                return None
            response = await manager.send_action({
                'Action': 'PJSIPShowEndpoint',
                'Endpoint': sip_username
            })
            # Don't close - persistent connection
            return response
        except Exception as e:
            logger.error(f"Failed to get SIP peer: {e}")
            self._mark_disconnected()
            return None

    async def list_sip_peers(self) -> List[str]:
        """
        List all SIP peers managed by Kasa AI

        Returns:
            List of SIP usernames
        """
        if self.simulation_mode:
            logger.info("[SIMULATION] Listing SIP peers")
            return ["kasaai_demo_001", "kasaai_demo_002"]

        try:
            manager = await self._get_manager()
            if not manager:
                return []
            response = await manager.send_action({'Action': 'PJSIPShowEndpoints'})
            # Don't close - persistent connection

            # Parse response to extract kasaai peers
            peers = []
            # TODO: Parse actual response format
            return peers

        except Exception as e:
            logger.error(f"Failed to list SIP peers: {e}")
            self._mark_disconnected()
            return []

    async def set_webhook_url(self, number: str, webhook_url: str) -> bool:
        """
        Set webhook URL for a phone number in AstDB

        Args:
            number: Phone number
            webhook_url: Webhook URL to store

        Returns:
            bool: True if successful
        """
        if self.simulation_mode:
            logger.info(f"[SIMULATION] Setting webhook for {number}: {webhook_url}")
            await asyncio.sleep(0.1)
            return True

        try:
            manager = await self._get_manager()
            if not manager:
                return False
            await manager.send_action({
                'Action': 'DBPut',
                'Family': 'kasaai',
                'Key': f'webhook/{number}',
                'Val': webhook_url
            })
            # Don't close - persistent connection
            logger.info(f"Set webhook URL for {number}")
            return True

        except Exception as e:
            logger.error(f"Failed to set webhook URL: {e}")
            self._mark_disconnected()
            return False

    async def get_asterisk_status(self) -> Dict[str, Any]:
        """
        Get Asterisk server status

        Uses caching to avoid excessive AMI calls (WebSocket polls every 5 seconds).

        Returns:
            Dict with status information
        """
        if self.simulation_mode:
            return {
                "status": "running",
                "uptime": "10 days, 5 hours",
                "active_channels": 3,
                "active_calls": 1,
                "sip_peers": 15,
                "simulation": True
            }

        # Check cache first to avoid excessive AMI calls
        now = datetime.utcnow()
        if (self._status_cache is not None and
            self._status_cache_time is not None and
            (now - self._status_cache_time).total_seconds() < self._status_cache_ttl):
            return self._status_cache

        try:
            manager = await self._get_manager()
            if not manager:
                return {
                    "status": "error",
                    "error": "No AMI connection",
                    "simulation": False
                }

            # Get core status
            core_status_response = await manager.send_action({'Action': 'CoreStatus'})

            # Panoramisk returns a list of responses, get the first one
            core_status = core_status_response[0] if isinstance(core_status_response, list) else core_status_response

            # Get active channels
            channels_response = await manager.send_action({'Action': 'CoreShowChannels'})
            channels = channels_response[0] if isinstance(channels_response, list) else channels_response

            # Don't close - persistent connection

            result = {
                "status": "running",
                "uptime": core_status.get('CoreUptime', 'Unknown') if isinstance(core_status, dict) else 'Unknown',
                "active_channels": int(channels.get('ListItems', 0)) if isinstance(channels, dict) else 0,
                "active_calls": int(channels.get('ListItems', 0)) // 2 if isinstance(channels, dict) else 0,
                "simulation": False
            }

            # Update cache
            self._status_cache = result
            self._status_cache_time = now

            return result

        except Exception as e:
            logger.error(f"Failed to get Asterisk status: {e}")
            self._mark_disconnected()
            return {
                "status": "error",
                "error": str(e),
                "simulation": False
            }

    async def reload_pjsip(self) -> bool:
        """
        Reload PJSIP configuration

        Returns:
            bool: True if successful
        """
        if self.simulation_mode:
            logger.info("[SIMULATION] Reloading PJSIP")
            await asyncio.sleep(0.1)
            return True

        try:
            manager = await self._get_manager()
            if not manager:
                return False
            await manager.send_action({'Action': 'PJSIPReload'})
            # Don't close - persistent connection
            logger.info("Reloaded PJSIP configuration")
            return True

        except Exception as e:
            logger.error(f"Failed to reload PJSIP: {e}")
            self._mark_disconnected()
            return False

    async def originate_call(
        self,
        destination: str,
        trunk: str = "ant-cellular",
        context: str = "from-internal",
        exten: str = "s",
        priority: int = 1,
        caller_id: str = "0308249843",
        timeout: int = 60000,
        variables: Optional[Dict[str, str]] = None,
        application: Optional[str] = None,
        data: Optional[str] = None,
        async_originate: bool = True
    ) -> Dict[str, Any]:
        """
        Originate an outbound call through Asterisk.

        This can be used to place calls via a SIP trunk (e.g., Ant Cellular)
        and optionally route to an application like AGI for voice AI.

        Args:
            destination: Phone number to call
            trunk: SIP trunk to use (default: ant-cellular)
            context: Dialplan context to use after call is answered
            exten: Extension to dial after answer
            priority: Dialplan priority
            caller_id: Caller ID to display
            timeout: Call timeout in milliseconds (default 60000 = 60 seconds)
            variables: Channel variables to set
            application: Asterisk application to run (alternative to context/exten)
            data: Data for the application
            async_originate: If True, return immediately without waiting for answer

        Returns:
            Dict with success status and call details
        """
        if self.simulation_mode:
            logger.info(f"[SIMULATION] Originating call to {destination} via {trunk}")
            await asyncio.sleep(0.1)
            return {
                "success": True,
                "message": "Call originated (simulated)",
                "destination": destination,
                "action_id": f"sim_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }

        try:
            manager = await self._get_manager()
            if not manager:
                return {
                    "success": False,
                    "error": "No AMI connection available"
                }

            # Build channel string for PJSIP
            channel = f"PJSIP/{destination}@{trunk}"

            # Build originate action
            action = {
                'Action': 'Originate',
                'Channel': channel,
                'CallerID': f'"{caller_id}" <{caller_id}>',
                'Timeout': str(timeout),
                'Async': 'true' if async_originate else 'false'
            }

            # Either use application or context/exten
            if application:
                action['Application'] = application
                if data:
                    action['Data'] = data
            else:
                action['Context'] = context
                action['Exten'] = exten
                action['Priority'] = str(priority)

            # Add channel variables
            if variables:
                for key, value in variables.items():
                    action[f'Variable'] = f'{key}={value}'

            logger.info(f"Originating call: {channel} -> {application or context}/{exten}")

            response = await manager.send_action(action)

            # Parse response
            result_response = response[0] if isinstance(response, list) else response

            if isinstance(result_response, dict):
                response_str = result_response.get('Response', '')
                message = result_response.get('Message', '')
                action_id = result_response.get('ActionID', '')
            else:
                response_str = str(result_response)
                message = ''
                action_id = ''

            success = 'Success' in response_str or 'Originate successfully' in str(result_response)

            result = {
                "success": success,
                "message": message or ("Call originated" if success else "Failed to originate"),
                "destination": destination,
                "channel": channel,
                "action_id": action_id,
                "response": str(result_response)[:500]  # Truncate for logging
            }

            if success:
                logger.info(f"✅ Call originated to {destination}")
            else:
                logger.error(f"❌ Failed to originate call to {destination}: {result_response}")

            return result

        except Exception as e:
            logger.error(f"Failed to originate call: {e}")
            self._mark_disconnected()
            return {
                "success": False,
                "error": str(e),
                "destination": destination
            }

    async def hangup_channel(self, channel: str, cause: int = 16) -> bool:
        """
        Hangup a channel.

        Args:
            channel: Channel name to hangup
            cause: Hangup cause code (default 16 = Normal clearing)

        Returns:
            bool: True if successful
        """
        if self.simulation_mode:
            logger.info(f"[SIMULATION] Hanging up channel {channel}")
            return True

        try:
            manager = await self._get_manager()
            if not manager:
                return False

            await manager.send_action({
                'Action': 'Hangup',
                'Channel': channel,
                'Cause': str(cause)
            })

            logger.info(f"Hangup sent to channel {channel}")
            return True

        except Exception as e:
            logger.error(f"Failed to hangup channel: {e}")
            self._mark_disconnected()
            return False

    async def get_active_channels(self) -> List[Dict[str, Any]]:
        """
        Get list of active channels.

        Returns:
            List of channel information dicts
        """
        if self.simulation_mode:
            return []

        try:
            manager = await self._get_manager()
            if not manager:
                return []

            response = await manager.send_action({'Action': 'CoreShowChannels'})

            channels = []
            if isinstance(response, list):
                for item in response:
                    if isinstance(item, dict) and item.get('Event') == 'CoreShowChannel':
                        channels.append({
                            'channel': item.get('Channel'),
                            'state': item.get('ChannelState'),
                            'application': item.get('Application'),
                            'duration': item.get('Duration'),
                            'caller_id': item.get('CallerIDNum')
                        })

            return channels

        except Exception as e:
            logger.error(f"Failed to get active channels: {e}")
            self._mark_disconnected()
            return []
