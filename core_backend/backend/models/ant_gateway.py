"""
ANT Cellular Gateway Models

Supports various GSM/cellular gateway devices:
- GoIP (Hybertone/DBL Technology)
- Dinstar
- Yeastar
- OpenVox
- Synway
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class GatewayType(str, Enum):
    """Supported gateway types"""
    GOIP = "goip"
    DINSTAR = "dinstar"
    YEASTAR = "yeastar"
    OPENVOX = "openvox"
    SYNWAY = "synway"
    GENERIC = "generic"


class GatewayStatus(str, Enum):
    """Gateway connection status"""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    UNKNOWN = "unknown"


class SIMStatus(str, Enum):
    """SIM card registration status"""
    REGISTERED = "registered"
    NOT_REGISTERED = "not_registered"
    SEARCHING = "searching"
    DENIED = "denied"
    UNKNOWN = "unknown"


class SIMCard(BaseModel):
    """SIM card information"""
    slot: int = Field(..., description="SIM slot number (1-N)")
    phone_number: Optional[str] = Field(None, description="Phone number on SIM")
    imsi: Optional[str] = Field(None, description="IMSI number")
    iccid: Optional[str] = Field(None, description="ICC-ID")
    network_provider: Optional[str] = Field(None, description="Network operator name")
    status: SIMStatus = Field(default=SIMStatus.UNKNOWN, description="Registration status")
    signal_strength: int = Field(default=0, description="Signal strength 0-100")
    network_type: Optional[str] = Field(None, description="2G/3G/4G")

    class Config:
        use_enum_values = True


class GatewayCredentials(BaseModel):
    """Gateway authentication credentials"""
    username: str = Field(default="admin", description="Admin username")
    password: str = Field(..., description="Admin password")
    api_key: Optional[str] = Field(None, description="API key if supported")


class ANTGateway(BaseModel):
    """ANT Cellular Gateway model"""
    gateway_id: str = Field(..., description="Unique gateway identifier")
    name: str = Field(..., description="Friendly name for gateway")
    gateway_type: GatewayType = Field(..., description="Type of gateway device")

    # Connection details
    ip_address: str = Field(..., description="Gateway IP address")
    port: int = Field(default=80, description="HTTP API port")
    https: bool = Field(default=False, description="Use HTTPS")

    # Authentication
    credentials: GatewayCredentials = Field(..., description="Admin credentials")

    # SIM cards
    sim_cards: List[SIMCard] = Field(default_factory=list, description="List of SIM cards")
    total_sim_slots: int = Field(default=1, description="Total SIM slots available")

    # Status
    status: GatewayStatus = Field(default=GatewayStatus.OFFLINE, description="Connection status")
    last_seen: Optional[datetime] = Field(None, description="Last successful ping")

    # Asterisk integration
    asterisk_sip_server: str = Field(
        default="asterisk.ailabsafrica.com",
        description="Asterisk SIP server"
    )
    asterisk_sip_port: int = Field(default=5060, description="SIP port")

    # Metadata
    firmware_version: Optional[str] = Field(None, description="Gateway firmware version")
    hardware_version: Optional[str] = Field(None, description="Hardware version")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class GatewayCreateRequest(BaseModel):
    """Request to add new gateway"""
    name: str = Field(..., description="Gateway name", min_length=1)
    gateway_type: GatewayType
    ip_address: str = Field(..., description="IP address or hostname")
    port: int = Field(default=80, ge=1, le=65535)
    https: bool = Field(default=False)
    username: str = Field(default="admin")
    password: str = Field(..., min_length=1)
    api_key: Optional[str] = None
    total_sim_slots: int = Field(default=1, ge=1, le=32)

    class Config:
        use_enum_values = True


class GatewayUpdateRequest(BaseModel):
    """Request to update gateway"""
    name: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    https: Optional[bool] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None

    class Config:
        use_enum_values = True


class GatewayStatusResponse(BaseModel):
    """Gateway status response"""
    success: bool
    gateway_id: str
    name: str
    status: GatewayStatus
    sim_cards: List[SIMCard]
    online_sims: int
    registered_numbers: int
    last_seen: Optional[datetime]
    error: Optional[str] = None

    class Config:
        use_enum_values = True


class GatewayListResponse(BaseModel):
    """List of gateways response"""
    success: bool
    gateways: List[ANTGateway]
    total_gateways: int
    online_gateways: int
    total_sims: int
    registered_sims: int

    class Config:
        use_enum_values = True
