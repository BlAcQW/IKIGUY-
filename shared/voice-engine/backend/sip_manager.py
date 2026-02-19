"""
SIP Manager for Kasaai Voice Engine
Manages both Asterisk and FreeSWITCH SIP servers
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List, Literal
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import aiohttp
import asyncio_mqtt
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SIPProvider(str, Enum):
    """Supported SIP server types"""
    ASTERISK = "asterisk"
    FREESWITCH = "freeswitch"


class SIPServerConfig(BaseModel):
    """Configuration for a SIP server"""
    provider: SIPProvider
    host: str = "localhost"
    port: int = 5060
    api_port: int = Field(default=5038, description="AMI port for Asterisk, ESL port for FreeSWITCH")
    api_username: str = ""
    api_password: str = ""
    context: str = "kasaai-default"
    enabled: bool = True
    priority: int = Field(default=1, description="Priority for server selection (lower is higher priority)")


class CallInfo(BaseModel):
    """Information about an active call"""
    call_id: str
    provider: SIPProvider
    from_number: str
    to_number: str
    direction: Literal["inbound", "outbound"]
    status: str
    start_time: datetime
    duration: Optional[int] = None
    assistant_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class SIPServerConnection:
    """Represents a connection to a SIP server"""
    config: SIPServerConfig
    connected: bool = False
    last_ping: Optional[datetime] = None
    active_calls: Dict[str, CallInfo] = None
    
    def __post_init__(self):
        if self.active_calls is None:
            self.active_calls = {}


class SIPManager:
    """
    Manages multiple SIP servers (Asterisk and FreeSWITCH)
    Provides unified interface for voice operations
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.servers: Dict[str, SIPServerConnection] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize SIP manager and connections"""
        logger.info("Initializing SIP Manager")
        
        # Create HTTP session
        self.session = aiohttp.ClientSession()
        
        # Load server configurations
        await self._load_server_configs()
        
        # Connect to servers
        for server_id, connection in self.servers.items():
            await self._connect_server(server_id)
        
        # Start monitoring
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_servers())
        
    async def shutdown(self):
        """Shutdown SIP manager and close connections"""
        logger.info("Shutting down SIP Manager")
        self._running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect from servers
        for server_id in self.servers:
            await self._disconnect_server(server_id)
        
        # Close HTTP session
        if self.session:
            await self.session.close()
    
    async def _load_server_configs(self):
        """Load SIP server configurations"""
        # Default Asterisk configuration
        asterisk_config = SIPServerConfig(
            provider=SIPProvider.ASTERISK,
            host=self.config.get("asterisk_host", "localhost"),
            port=self.config.get("asterisk_port", 5060),
            api_port=self.config.get("asterisk_ami_port", 5038),
            api_username=self.config.get("asterisk_ami_username", "admin"),
            api_password=self.config.get("asterisk_ami_password", "kasaai2024"),
            context="kasaai-internal",
            enabled=self.config.get("asterisk_enabled", True),
            priority=1
        )
        
        # Default FreeSWITCH configuration
        freeswitch_config = SIPServerConfig(
            provider=SIPProvider.FREESWITCH,
            host=self.config.get("freeswitch_host", "localhost"),
            port=self.config.get("freeswitch_port", 5080),
            api_port=self.config.get("freeswitch_esl_port", 8021),
            api_username=self.config.get("freeswitch_esl_username", ""),
            api_password=self.config.get("freeswitch_esl_password", "KasaaiFS2024"),
            context="kasaai",
            enabled=self.config.get("freeswitch_enabled", True),
            priority=2
        )
        
        # Add servers to manager
        if asterisk_config.enabled:
            self.servers["asterisk"] = SIPServerConnection(config=asterisk_config)
        
        if freeswitch_config.enabled:
            self.servers["freeswitch"] = SIPServerConnection(config=freeswitch_config)
    
    async def _connect_server(self, server_id: str) -> bool:
        """Connect to a SIP server"""
        connection = self.servers.get(server_id)
        if not connection:
            return False
        
        try:
            if connection.config.provider == SIPProvider.ASTERISK:
                connected = await self._connect_asterisk(connection)
            elif connection.config.provider == SIPProvider.FREESWITCH:
                connected = await self._connect_freeswitch(connection)
            else:
                connected = False
            
            connection.connected = connected
            connection.last_ping = datetime.utcnow() if connected else None
            
            if connected:
                logger.info(f"Connected to {server_id} ({connection.config.provider.value})")
            else:
                logger.warning(f"Failed to connect to {server_id}")
            
            return connected
            
        except Exception as e:
            logger.error(f"Error connecting to {server_id}: {e}")
            connection.connected = False
            return False
    
    async def _disconnect_server(self, server_id: str):
        """Disconnect from a SIP server"""
        connection = self.servers.get(server_id)
        if not connection:
            return
        
        try:
            if connection.config.provider == SIPProvider.ASTERISK:
                await self._disconnect_asterisk(connection)
            elif connection.config.provider == SIPProvider.FREESWITCH:
                await self._disconnect_freeswitch(connection)
            
            connection.connected = False
            logger.info(f"Disconnected from {server_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting from {server_id}: {e}")
    
    async def _connect_asterisk(self, connection: SIPServerConnection) -> bool:
        """Connect to Asterisk via AMI"""
        try:
            # Send login request to AMI
            url = f"http://{connection.config.host}:{connection.config.api_port}/rawman"
            data = {
                "Action": "Login",
                "Username": connection.config.api_username,
                "Secret": connection.config.api_password
            }
            
            async with self.session.post(url, data=data, timeout=5) as response:
                if response.status == 200:
                    text = await response.text()
                    return "Success" in text
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Asterisk AMI: {e}")
            return False
    
    async def _disconnect_asterisk(self, connection: SIPServerConnection):
        """Disconnect from Asterisk AMI"""
        try:
            url = f"http://{connection.config.host}:{connection.config.api_port}/rawman"
            data = {"Action": "Logoff"}
            
            async with self.session.post(url, data=data, timeout=5) as response:
                await response.text()
                
        except Exception as e:
            logger.error(f"Error disconnecting from Asterisk: {e}")
    
    async def _connect_freeswitch(self, connection: SIPServerConnection) -> bool:
        """Connect to FreeSWITCH via Event Socket"""
        try:
            # Test connection with a simple API call
            url = f"http://{connection.config.host}:{connection.config.api_port}/api/status"
            auth = aiohttp.BasicAuth("", connection.config.api_password)
            
            async with self.session.get(url, auth=auth, timeout=5) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Failed to connect to FreeSWITCH ESL: {e}")
            return False
    
    async def _disconnect_freeswitch(self, connection: SIPServerConnection):
        """Disconnect from FreeSWITCH"""
        # FreeSWITCH uses stateless HTTP API, no explicit disconnect needed
        pass
    
    async def _monitor_servers(self):
        """Monitor SIP servers health"""
        while self._running:
            try:
                for server_id, connection in self.servers.items():
                    if connection.config.enabled:
                        # Ping server
                        connected = await self._ping_server(server_id)
                        
                        # Update connection status
                        if connected != connection.connected:
                            if connected:
                                logger.info(f"Server {server_id} is back online")
                            else:
                                logger.warning(f"Server {server_id} is offline")
                            connection.connected = connected
                        
                        if connected:
                            connection.last_ping = datetime.utcnow()
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in server monitoring: {e}")
                await asyncio.sleep(30)
    
    async def _ping_server(self, server_id: str) -> bool:
        """Ping a SIP server to check if it's alive"""
        connection = self.servers.get(server_id)
        if not connection:
            return False
        
        try:
            if connection.config.provider == SIPProvider.ASTERISK:
                # Send Ping action to AMI
                url = f"http://{connection.config.host}:{connection.config.api_port}/rawman"
                data = {"Action": "Ping"}
                
                async with self.session.post(url, data=data, timeout=5) as response:
                    if response.status == 200:
                        text = await response.text()
                        return "Pong" in text
                        
            elif connection.config.provider == SIPProvider.FREESWITCH:
                # Check FreeSWITCH status
                url = f"http://{connection.config.host}:{connection.config.api_port}/api/status"
                auth = aiohttp.BasicAuth("", connection.config.api_password)
                
                async with self.session.get(url, auth=auth, timeout=5) as response:
                    return response.status == 200
            
            return False
            
        except Exception:
            return False
    
    async def get_active_server(self) -> Optional[str]:
        """Get the best available SIP server"""
        # Sort servers by priority and connection status
        available_servers = [
            (server_id, conn) for server_id, conn in self.servers.items()
            if conn.config.enabled and conn.connected
        ]
        
        if not available_servers:
            return None
        
        # Sort by priority (lower is better)
        available_servers.sort(key=lambda x: x[1].config.priority)
        
        return available_servers[0][0]
    
    async def make_call(
        self,
        to_number: str,
        from_number: Optional[str] = None,
        assistant_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Initiate an outbound call
        
        Returns:
            Call ID if successful, None otherwise
        """
        server_id = await self.get_active_server()
        if not server_id:
            logger.error("No available SIP servers for outbound call")
            return None
        
        connection = self.servers[server_id]
        call_id = f"{server_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{to_number[-4:]}"
        
        try:
            if connection.config.provider == SIPProvider.ASTERISK:
                success = await self._make_call_asterisk(
                    connection, call_id, to_number, from_number, assistant_id, metadata
                )
            elif connection.config.provider == SIPProvider.FREESWITCH:
                success = await self._make_call_freeswitch(
                    connection, call_id, to_number, from_number, assistant_id, metadata
                )
            else:
                success = False
            
            if success:
                # Track the call
                call_info = CallInfo(
                    call_id=call_id,
                    provider=connection.config.provider,
                    from_number=from_number or "kasaai",
                    to_number=to_number,
                    direction="outbound",
                    status="initiated",
                    start_time=datetime.utcnow(),
                    assistant_id=assistant_id,
                    metadata=metadata or {}
                )
                connection.active_calls[call_id] = call_info
                
                logger.info(f"Initiated outbound call {call_id} via {server_id}")
                return call_id
            else:
                logger.error(f"Failed to initiate call via {server_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error making call via {server_id}: {e}")
            return None
    
    async def _make_call_asterisk(
        self,
        connection: SIPServerConnection,
        call_id: str,
        to_number: str,
        from_number: Optional[str],
        assistant_id: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> bool:
        """Make a call using Asterisk"""
        try:
            url = f"http://{connection.config.host}:{connection.config.api_port}/rawman"
            data = {
                "Action": "Originate",
                "Channel": f"SIP/trunk-provider1/{to_number}",
                "Context": "kasaai-outbound-campaign",
                "Exten": to_number,
                "Priority": "1",
                "CallerID": from_number or "Kasaai",
                "Timeout": "30000",
                "Variable": f"CALL_ID={call_id}",
                "Async": "true"
            }
            
            if assistant_id:
                data["Variable"] += f",ASSISTANT_ID={assistant_id}"
            
            async with self.session.post(url, data=data, timeout=10) as response:
                if response.status == 200:
                    text = await response.text()
                    return "Success" in text
                return False
                
        except Exception as e:
            logger.error(f"Asterisk call failed: {e}")
            return False
    
    async def _make_call_freeswitch(
        self,
        connection: SIPServerConnection,
        call_id: str,
        to_number: str,
        from_number: Optional[str],
        assistant_id: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> bool:
        """Make a call using FreeSWITCH"""
        try:
            # Build originate command
            originate_string = (
                f"{{origination_uuid={call_id},"
                f"origination_caller_id_number={from_number or 'kasaai'},"
                f"kasaai_assistant_id={assistant_id or 'default'}"
                f"}}sofia/gateway/provider1/{to_number}"
            )
            
            url = f"http://{connection.config.host}:{connection.config.api_port}/api/originate"
            auth = aiohttp.BasicAuth("", connection.config.api_password)
            params = {
                "cmd": f"{originate_string} &lua(kasaai/outbound_handler.lua {call_id})"
            }
            
            async with self.session.get(url, params=params, auth=auth, timeout=10) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"FreeSWITCH call failed: {e}")
            return False
    
    async def hangup_call(self, call_id: str) -> bool:
        """Hang up an active call"""
        # Find which server has this call
        for server_id, connection in self.servers.items():
            if call_id in connection.active_calls:
                try:
                    if connection.config.provider == SIPProvider.ASTERISK:
                        success = await self._hangup_asterisk(connection, call_id)
                    elif connection.config.provider == SIPProvider.FREESWITCH:
                        success = await self._hangup_freeswitch(connection, call_id)
                    else:
                        success = False
                    
                    if success:
                        # Update call status
                        connection.active_calls[call_id].status = "terminated"
                        logger.info(f"Hung up call {call_id}")
                    
                    return success
                    
                except Exception as e:
                    logger.error(f"Error hanging up call {call_id}: {e}")
                    return False
        
        logger.warning(f"Call {call_id} not found in any server")
        return False
    
    async def _hangup_asterisk(self, connection: SIPServerConnection, call_id: str) -> bool:
        """Hang up a call in Asterisk"""
        try:
            url = f"http://{connection.config.host}:{connection.config.api_port}/rawman"
            data = {
                "Action": "Hangup",
                "Channel": call_id
            }
            
            async with self.session.post(url, data=data, timeout=5) as response:
                if response.status == 200:
                    text = await response.text()
                    return "Success" in text
                return False
                
        except Exception as e:
            logger.error(f"Asterisk hangup failed: {e}")
            return False
    
    async def _hangup_freeswitch(self, connection: SIPServerConnection, call_id: str) -> bool:
        """Hang up a call in FreeSWITCH"""
        try:
            url = f"http://{connection.config.host}:{connection.config.api_port}/api/uuid_kill"
            auth = aiohttp.BasicAuth("", connection.config.api_password)
            params = {"cmd": call_id}
            
            async with self.session.get(url, params=params, auth=auth, timeout=5) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"FreeSWITCH hangup failed: {e}")
            return False
    
    async def get_call_info(self, call_id: str) -> Optional[CallInfo]:
        """Get information about a call"""
        for connection in self.servers.values():
            if call_id in connection.active_calls:
                return connection.active_calls[call_id]
        return None
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Get status of all SIP servers"""
        status = {
            "servers": {},
            "total_active_calls": 0,
            "available_servers": 0
        }
        
        for server_id, connection in self.servers.items():
            server_status = {
                "provider": connection.config.provider.value,
                "host": connection.config.host,
                "port": connection.config.port,
                "connected": connection.connected,
                "enabled": connection.config.enabled,
                "priority": connection.config.priority,
                "active_calls": len(connection.active_calls),
                "last_ping": connection.last_ping.isoformat() if connection.last_ping else None
            }
            
            status["servers"][server_id] = server_status
            
            if connection.connected and connection.config.enabled:
                status["available_servers"] += 1
            
            status["total_active_calls"] += len(connection.active_calls)
        
        return status


# Global SIP manager instance
sip_manager = SIPManager()


async def initialize_sip_manager(config: Optional[Dict[str, Any]] = None):
    """Initialize the global SIP manager"""
    global sip_manager
    sip_manager = SIPManager(config)
    await sip_manager.initialize()
    return sip_manager


async def get_sip_manager() -> SIPManager:
    """Get the global SIP manager instance"""
    return sip_manager