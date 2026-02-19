"""
SIP Telephony Adapter

This module provides the SIP telephony adapter implementation for Asterisk/FreeSWITCH.
Supports DTMF handling, IVR, call recording, conference, and transfer features.
"""

import asyncio
import logging
import socket
import threading
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from .base import BaseTelephonyAdapter
from ..models import CallContext, ProviderSettings
from ..interfaces import TelephonyEvent, TelephonyEventType


@dataclass
class SipCallInfo:
    """SIP call information"""
    call_id: str
    channel: str
    extension: str
    context: str
    priority: int
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    recording_path: Optional[str] = None
    dtmf_sequence: str = ""
    conference_id: Optional[str] = None


class SipAdapter(BaseTelephonyAdapter):
    """SIP telephony provider adapter for Asterisk/FreeSWITCH"""
    
    def __init__(self, settings: ProviderSettings):
        super().__init__(settings)
        self._connected = False
        self._ami_client = None
        self._agi_client = None
        self._sip_calls: Dict[str, SipCallInfo] = {}
        self._conferences: Dict[str, List[str]] = {}
        self._recordings: Dict[str, str] = {}
        
        # SIP-specific settings
        self.asterisk_host = settings.custom_settings.get('asterisk_host', 'localhost')
        self.asterisk_port = settings.custom_settings.get('asterisk_port', 5038)
        self.asterisk_username = settings.custom_settings.get('asterisk_username', 'admin')
        self.asterisk_password = settings.custom_settings.get('asterisk_password', '')
        self.asterisk_context = settings.custom_settings.get('asterisk_context', 'default')
        
        # FreeSWITCH settings (alternative)
        self.freeswitch_host = settings.custom_settings.get('freeswitch_host', 'localhost')
        self.freeswitch_port = settings.custom_settings.get('freeswitch_port', 8021)
        self.freeswitch_password = settings.custom_settings.get('freeswitch_password', 'ClueCon')
        
        # Feature flags
        self.enable_recording = settings.custom_settings.get('enable_recording', True)
        self.enable_conference = settings.custom_settings.get('enable_conference', True)
        self.enable_ivr = settings.custom_settings.get('enable_ivr', True)
        self.enable_dtmf = settings.custom_settings.get('enable_dtmf', True)
        
        # Recording settings
        self.recording_format = settings.custom_settings.get('recording_format', 'wav')
        self.recording_path = settings.custom_settings.get('recording_path', '/var/spool/asterisk/monitor')
        
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
    async def connect(self) -> bool:
        """Connect to SIP server (Asterisk/FreeSWITCH)"""
        try:
            # Try Asterisk first
            if await self._connect_asterisk():
                self.logger.info("Connected to Asterisk AMI")
                return True
            
            # Try FreeSWITCH if Asterisk fails
            if await self._connect_freeswitch():
                self.logger.info("Connected to FreeSWITCH")
                return True
                
            self.logger.error("Failed to connect to both Asterisk and FreeSWITCH")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to connect to SIP server: {e}")
            return False
    
    async def _connect_asterisk(self) -> bool:
        """Connect to Asterisk AMI"""
        try:
            # Create AMI client (simplified - in real implementation, use proper AMI library)
            self._ami_client = AsteriskAMIClient(
                host=self.asterisk_host,
                port=self.asterisk_port,
                username=self.asterisk_username,
                password=self.asterisk_password
            )
            
            await self._ami_client.connect()
            self._connected = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Asterisk: {e}")
            return False
    
    async def _connect_freeswitch(self) -> bool:
        """Connect to FreeSWITCH"""
        try:
            # Create FreeSWITCH client (simplified - in real implementation, use proper FS library)
            self._freeswitch_client = FreeSwitchClient(
                host=self.freeswitch_host,
                port=self.freeswitch_port,
                password=self.freeswitch_password
            )
            
            await self._freeswitch_client.connect()
            self._connected = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to FreeSWITCH: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from SIP server"""
        try:
            if self._ami_client:
                await self._ami_client.disconnect()
            if self._freeswitch_client:
                await self._freeswitch_client.disconnect()
            
            self._connected = False
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disconnect: {e}")
            return False
    
    async def is_connected(self) -> bool:
        """Check if connected to SIP server"""
        return self._connected
    
    async def _dial_impl(self, context: CallContext) -> str:
        """SIP-specific call initiation"""
        try:
            # Generate unique call ID
            call_id = f"sip_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(context.destination)}"
            
            # Create SIP call info
            sip_call = SipCallInfo(
                call_id=call_id,
                channel=f"SIP/{context.destination}",
                extension=context.destination,
                context=self.asterisk_context,
                priority=1,
                status="initiating",
                start_time=datetime.utcnow()
            )
            
            # Store call info
            self._sip_calls[call_id] = sip_call
            
            # Initiate call via AMI or FreeSWITCH
            if self._ami_client:
                await self._ami_client.originate_call(
                    channel=sip_call.channel,
                    context=sip_call.context,
                    extension=sip_call.extension,
                    priority=sip_call.priority,
                    call_id=call_id
                )
            elif self._freeswitch_client:
                await self._freeswitch_client.originate_call(
                    destination=context.destination,
                    call_id=call_id
                )
            
            # Update status
            sip_call.status = "initiated"
            self.logger.info(f"SIP call initiated: {call_id} to {context.destination}")
            
            return call_id
            
        except Exception as e:
            self.logger.error(f"Failed to initiate SIP call: {e}")
            raise
    
    async def _hangup_impl(self, call_id: str) -> bool:
        """SIP-specific call termination"""
        try:
            if call_id not in self._sip_calls:
                raise ValueError(f"SIP call {call_id} not found")
            
            sip_call = self._sip_calls[call_id]
            
            # Hangup call via AMI or FreeSWITCH
            if self._ami_client:
                await self._ami_client.hangup_call(sip_call.channel)
            elif self._freeswitch_client:
                await self._freeswitch_client.hangup_call(call_id)
            
            # Update call info
            sip_call.status = "ended"
            sip_call.end_time = datetime.utcnow()
            if sip_call.start_time and sip_call.end_time:
                sip_call.duration = int((sip_call.end_time - sip_call.start_time).total_seconds())
            
            self.logger.info(f"SIP call ended: {call_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to end SIP call {call_id}: {e}")
            return False
    
    async def _get_events_impl(self, call_id: str) -> List[TelephonyEvent]:
        """SIP-specific event retrieval"""
        events = []
        
        try:
            if call_id not in self._sip_calls:
                return events
            
            sip_call = self._sip_calls[call_id]
            
            # Get events from AMI or FreeSWITCH
            if self._ami_client:
                ami_events = await self._ami_client.get_call_events(call_id)
                events.extend(self._convert_ami_events(ami_events, call_id))
            elif self._freeswitch_client:
                fs_events = await self._freeswitch_client.get_call_events(call_id)
                events.extend(self._convert_fs_events(fs_events, call_id))
            
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to get SIP events for {call_id}: {e}")
            return events
    
    def _convert_ami_events(self, ami_events: List[Dict], call_id: str) -> List[TelephonyEvent]:
        """Convert Asterisk AMI events to TelephonyEvent objects"""
        events = []
        
        for ami_event in ami_events:
            event_type = ami_event.get('event')
            
            if event_type == 'Newchannel':
                events.append(TelephonyEvent(
                    event_type=TelephonyEventType.CALL_STARTED,
                    call_id=call_id,
                    timestamp=datetime.utcnow(),
                    data={
                        'channel': ami_event.get('channel'),
                        'caller_id': ami_event.get('callerid'),
                        'context': ami_event.get('context')
                    }
                ))
            elif event_type == 'Hangup':
                events.append(TelephonyEvent(
                    event_type=TelephonyEventType.CALL_ENDED,
                    call_id=call_id,
                    timestamp=datetime.utcnow(),
                    data={
                        'channel': ami_event.get('channel'),
                        'cause': ami_event.get('cause'),
                        'duration': ami_event.get('duration')
                    }
                ))
            elif event_type == 'DTMF':
                events.append(TelephonyEvent(
                    event_type=TelephonyEventType.DTMF_RECEIVED,
                    call_id=call_id,
                    timestamp=datetime.utcnow(),
                    data={
                        'digit': ami_event.get('digit'),
                        'channel': ami_event.get('channel')
                    }
                ))
        
        return events
    
    def _convert_fs_events(self, fs_events: List[Dict], call_id: str) -> List[TelephonyEvent]:
        """Convert FreeSWITCH events to TelephonyEvent objects"""
        events = []
        
        for fs_event in fs_events:
            event_type = fs_event.get('event_name')
            
            if event_type == 'CHANNEL_CREATE':
                events.append(TelephonyEvent(
                    event_type=TelephonyEventType.CALL_STARTED,
                    call_id=call_id,
                    timestamp=datetime.utcnow(),
                    data={
                        'uuid': fs_event.get('unique_id'),
                        'caller_id': fs_event.get('caller_id_number'),
                        'destination': fs_event.get('destination_number')
                    }
                ))
            elif event_type == 'CHANNEL_DESTROY':
                events.append(TelephonyEvent(
                    event_type=TelephonyEventType.CALL_ENDED,
                    call_id=call_id,
                    timestamp=datetime.utcnow(),
                    data={
                        'uuid': fs_event.get('unique_id'),
                        'hangup_cause': fs_event.get('hangup_cause'),
                        'duration': fs_event.get('variable_duration')
                    }
                ))
            elif event_type == 'DTMF':
                events.append(TelephonyEvent(
                    event_type=TelephonyEventType.DTMF_RECEIVED,
                    call_id=call_id,
                    timestamp=datetime.utcnow(),
                    data={
                        'digit': fs_event.get('dtmf_digit'),
                        'uuid': fs_event.get('unique_id')
                    }
                ))
        
        return events
    
    async def _get_costs_impl(self, call_id: str) -> Dict[str, float]:
        """SIP-specific cost calculation"""
        try:
            if call_id not in self._sip_calls:
                return {}
            
            sip_call = self._sip_calls[call_id]
            duration_minutes = (sip_call.duration or 0) / 60.0
            
            # SIP costs are typically very low (mostly infrastructure costs)
            cost_per_minute = await self._get_cost_per_minute()
            total_cost = duration_minutes * cost_per_minute
            
            return {
                'total_cost': total_cost,
                'cost_per_minute': cost_per_minute,
                'duration_minutes': duration_minutes,
                'infrastructure_cost': 0.001 * duration_minutes  # Minimal infrastructure cost
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate SIP costs for {call_id}: {e}")
            return {}
    
    async def _get_cost_per_minute(self) -> Optional[float]:
        """Get cost per minute for SIP"""
        return 0.005  # Very low cost for SIP
    
    async def _get_supported_regions(self) -> List[str]:
        """Get supported regions for SIP"""
        return ["US", "CA", "GB", "AU", "DE", "FR", "IT", "ES", "NL", "BE"]
    
    async def _get_supported_features(self) -> List[str]:
        """Get supported features for SIP"""
        features = [
            "voice_calls",
            "call_recording",
            "ivr",
            "conference",
            "transfer",
            "dtmf",
            "custom_dialplan"
        ]
        
        if self.enable_recording:
            features.append("recording")
        if self.enable_conference:
            features.append("conference")
        if self.enable_ivr:
            features.append("ivr")
        if self.enable_dtmf:
            features.append("dtmf")
        
        return features
    
    # SIP-specific methods
    
    async def start_recording(self, call_id: str) -> bool:
        """Start call recording"""
        try:
            if call_id not in self._sip_calls:
                raise ValueError(f"Call {call_id} not found")
            
            sip_call = self._sip_calls[call_id]
            recording_filename = f"{call_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{self.recording_format}"
            recording_path = f"{self.recording_path}/{recording_filename}"
            
            if self._ami_client:
                await self._ami_client.start_recording(sip_call.channel, recording_path)
            elif self._freeswitch_client:
                await self._freeswitch_client.start_recording(call_id, recording_path)
            
            sip_call.recording_path = recording_path
            self._recordings[call_id] = recording_path
            
            self.logger.info(f"Started recording for call {call_id}: {recording_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start recording for {call_id}: {e}")
            return False
    
    async def stop_recording(self, call_id: str) -> bool:
        """Stop call recording"""
        try:
            if call_id not in self._sip_calls:
                raise ValueError(f"Call {call_id} not found")
            
            sip_call = self._sip_calls[call_id]
            
            if self._ami_client:
                await self._ami_client.stop_recording(sip_call.channel)
            elif self._freeswitch_client:
                await self._freeswitch_client.stop_recording(call_id)
            
            self.logger.info(f"Stopped recording for call {call_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop recording for {call_id}: {e}")
            return False
    
    async def create_conference(self, name: str, pin: Optional[str] = None) -> str:
        """Create a conference room"""
        try:
            conference_id = f"conf_{name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            if self._ami_client:
                await self._ami_client.create_conference(conference_id, pin)
            elif self._freeswitch_client:
                await self._freeswitch_client.create_conference(conference_id, pin)
            
            self._conferences[conference_id] = []
            self.logger.info(f"Created conference: {conference_id}")
            
            return conference_id
            
        except Exception as e:
            self.logger.error(f"Failed to create conference: {e}")
            raise
    
    async def join_conference(self, call_id: str, conference_id: str) -> bool:
        """Join a call to a conference"""
        try:
            if call_id not in self._sip_calls:
                raise ValueError(f"Call {call_id} not found")
            
            if conference_id not in self._conferences:
                raise ValueError(f"Conference {conference_id} not found")
            
            sip_call = self._sip_calls[call_id]
            
            if self._ami_client:
                await self._ami_client.join_conference(sip_call.channel, conference_id)
            elif self._freeswitch_client:
                await self._freeswitch_client.join_conference(call_id, conference_id)
            
            self._conferences[conference_id].append(call_id)
            sip_call.conference_id = conference_id
            
            self.logger.info(f"Call {call_id} joined conference {conference_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to join conference: {e}")
            return False
    
    async def transfer_call(self, call_id: str, destination: str) -> bool:
        """Transfer a call to another destination"""
        try:
            if call_id not in self._sip_calls:
                raise ValueError(f"Call {call_id} not found")
            
            sip_call = self._sip_calls[call_id]
            
            if self._ami_client:
                await self._ami_client.transfer_call(sip_call.channel, destination)
            elif self._freeswitch_client:
                await self._freeswitch_client.transfer_call(call_id, destination)
            
            self.logger.info(f"Transferred call {call_id} to {destination}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to transfer call: {e}")
            return False
    
    async def send_dtmf(self, call_id: str, digits: str) -> bool:
        """Send DTMF digits to a call"""
        try:
            if call_id not in self._sip_calls:
                raise ValueError(f"Call {call_id} not found")
            
            sip_call = self._sip_calls[call_id]
            
            if self._ami_client:
                await self._ami_client.send_dtmf(sip_call.channel, digits)
            elif self._freeswitch_client:
                await self._freeswitch_client.send_dtmf(call_id, digits)
            
            self.logger.info(f"Sent DTMF {digits} to call {call_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send DTMF: {e}")
            return False


# Simplified client classes (in real implementation, use proper libraries)

class AsteriskAMIClient:
    """Simplified Asterisk AMI client"""
    
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connected = False
    
    async def connect(self):
        """Connect to Asterisk AMI"""
        # Simplified implementation
        self.connected = True
    
    async def disconnect(self):
        """Disconnect from Asterisk AMI"""
        self.connected = False
    
    async def originate_call(self, channel: str, context: str, extension: str, priority: int, call_id: str):
        """Originate a call via AMI"""
        # Simplified implementation
        pass
    
    async def hangup_call(self, channel: str):
        """Hangup a call via AMI"""
        # Simplified implementation
        pass
    
    async def get_call_events(self, call_id: str) -> List[Dict]:
        """Get call events from AMI"""
        # Simplified implementation
        return []
    
    async def start_recording(self, channel: str, path: str):
        """Start recording via AMI"""
        # Simplified implementation
        pass
    
    async def stop_recording(self, channel: str):
        """Stop recording via AMI"""
        # Simplified implementation
        pass
    
    async def create_conference(self, conference_id: str, pin: Optional[str]):
        """Create conference via AMI"""
        # Simplified implementation
        pass
    
    async def join_conference(self, channel: str, conference_id: str):
        """Join conference via AMI"""
        # Simplified implementation
        pass
    
    async def transfer_call(self, channel: str, destination: str):
        """Transfer call via AMI"""
        # Simplified implementation
        pass
    
    async def send_dtmf(self, channel: str, digits: str):
        """Send DTMF via AMI"""
        # Simplified implementation
        pass


class FreeSwitchClient:
    """Simplified FreeSWITCH client"""
    
    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password
        self.connected = False
    
    async def connect(self):
        """Connect to FreeSWITCH"""
        # Simplified implementation
        self.connected = True
    
    async def disconnect(self):
        """Disconnect from FreeSWITCH"""
        self.connected = False
    
    async def originate_call(self, destination: str, call_id: str):
        """Originate a call via FreeSWITCH"""
        # Simplified implementation
        pass
    
    async def hangup_call(self, call_id: str):
        """Hangup a call via FreeSWITCH"""
        # Simplified implementation
        pass
    
    async def get_call_events(self, call_id: str) -> List[Dict]:
        """Get call events from FreeSWITCH"""
        # Simplified implementation
        return []
    
    async def start_recording(self, call_id: str, path: str):
        """Start recording via FreeSWITCH"""
        # Simplified implementation
        pass
    
    async def stop_recording(self, call_id: str):
        """Stop recording via FreeSWITCH"""
        # Simplified implementation
        pass
    
    async def create_conference(self, conference_id: str, pin: Optional[str]):
        """Create conference via FreeSWITCH"""
        # Simplified implementation
        pass
    
    async def join_conference(self, call_id: str, conference_id: str):
        """Join conference via FreeSWITCH"""
        # Simplified implementation
        pass
    
    async def transfer_call(self, call_id: str, destination: str):
        """Transfer call via FreeSWITCH"""
        # Simplified implementation
        pass
    
    async def send_dtmf(self, call_id: str, digits: str):
        """Send DTMF via FreeSWITCH"""
        # Simplified implementation
        pass
