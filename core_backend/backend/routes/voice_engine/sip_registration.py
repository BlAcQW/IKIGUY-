"""
SIP Registration endpoints for generating QR codes and monitoring registration status.
"""

import logging
import secrets
import json
import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field
from apps.shared.services.qr_service import QRCodeService, QRCodeConfig
from ...mongo import get_database
import redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sip-registration", tags=["sip-registration"])

# Redis connection for provisioning configs
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


class SIPCredentials(BaseModel):
    """SIP credentials model"""
    username: str
    password: str
    domain: str = "asterisk.ailabsafrica.com"
    port: int = 5060
    transport: str = "UDP"
    display_name: Optional[str] = None


class SIPRegistrationQRRequest(BaseModel):
    """Request to generate SIP registration QR code"""
    phone_number: str = Field(..., description="Phone number associated with SIP account")
    sip_username: str = Field(..., description="SIP username")
    sip_password: str = Field(..., description="SIP password")
    display_name: Optional[str] = Field(None, description="Display name")
    domain: str = Field(default="asterisk.ailabsafrica.com", description="SIP domain")


class SIPRegistrationQRResponse(BaseModel):
    """Response containing SIP registration QR code"""
    qr_code_data_url: str = Field(..., description="Base64 data URL for QR code")
    sip_uri: str = Field(..., description="SIP URI (sip:username@domain)")
    provisioning_url: str = Field(..., description="Linphone provisioning URL")
    credentials: SIPCredentials
    instructions: str = Field(..., description="Setup instructions")


def generate_linphone_xml_config(credentials: SIPCredentials) -> str:
    """
    Generate Linphone XML provisioning configuration.

    Args:
        credentials: SIP credentials

    Returns:
        XML configuration string
    """
    xml_config = f'''<?xml version="1.0" encoding="UTF-8"?>
<config xmlns="http://www.linphone.org/xsds/lpconfig.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.linphone.org/xsds/lpconfig.xsd lpconfig.xsd">
  <section name="proxy_0">
    <entry name="reg_proxy">sip:{credentials.domain}</entry>
    <entry name="reg_identity">sip:{credentials.username}@{credentials.domain}</entry>
    <entry name="reg_expires">3600</entry>
    <entry name="reg_sendregister">1</entry>
    <entry name="publish">0</entry>
    <entry name="avpf">0</entry>
    <entry name="dial_escape_plus">0</entry>
    <entry name="quality_reporting_enabled">0</entry>
    <entry name="quality_reporting_interval">0</entry>
    <entry name="reg_route">&lt;sip:{credentials.domain}&gt;</entry>
    <entry name="nat_policy_ref">nat_policy_default_values</entry>
    <entry name="realm">{credentials.domain}</entry>
  </section>
  <section name="auth_info_0">
    <entry name="username">{credentials.username}</entry>
    <entry name="userid">{credentials.username}</entry>
    <entry name="passwd">{credentials.password}</entry>
    <entry name="realm">{credentials.domain}</entry>
    <entry name="domain">{credentials.domain}</entry>
  </section>
  <section name="sip">
    <entry name="default_proxy">0</entry>
    <entry name="guess_hostname">1</entry>
    <entry name="inc_timeout">60</entry>
    <entry name="use_info">0</entry>
    <entry name="register_only_when_network_is_up">1</entry>
  </section>
</config>'''
    return xml_config


@router.get("/provision/{token}")
async def get_linphone_provisioning(token: str):
    """
    Serve Linphone XML provisioning configuration.

    This endpoint is accessed when Linphone scans the QR code.

    Args:
        token: Provisioning token

    Returns:
        XML configuration file
    """
    # Retrieve credentials from Redis
    redis_key = f"sip_provisioning:{token}"
    credentials_json = redis_client.get(redis_key)

    if not credentials_json:
        raise HTTPException(status_code=404, detail="Provisioning config not found or expired")

    # Parse credentials
    credentials_dict = json.loads(credentials_json)
    credentials = SIPCredentials(**credentials_dict)

    # Generate XML config
    xml_config = generate_linphone_xml_config(credentials)

    return Response(
        content=xml_config,
        media_type="application/xml",
        headers={"Content-Disposition": "inline; filename=linphone-config.xml"}
    )


@router.post("/generate-qr", response_model=SIPRegistrationQRResponse)
async def generate_sip_registration_qr(request: SIPRegistrationQRRequest):
    """
    Generate QR code for SIP registration with Linphone.

    The QR code contains a provisioning URL that Linphone can scan to
    automatically download and configure the SIP account.

    Args:
        request: SIP registration request with credentials

    Returns:
        QR code data URL and setup information
    """
    try:
        # Create SIP credentials object
        credentials = SIPCredentials(
            username=request.sip_username,
            password=request.sip_password,
            domain=request.domain,
            display_name=request.display_name or f"KasaAI {request.phone_number}"
        )

        # Generate unique token for provisioning
        token = secrets.token_urlsafe(32)

        # Store credentials in Redis with 24-hour expiration
        redis_key = f"sip_provisioning:{token}"
        credentials_json = credentials.model_dump_json()
        redis_client.setex(redis_key, 86400, credentials_json)  # 24 hours

        # Generate provisioning URL
        provisioning_url = f"https://api.ailabsafrica.com/sip-registration/provision/{token}"

        # Generate SIP URI (standard format)
        sip_uri = f"sip:{credentials.username}@{credentials.domain}"

        # Generate QR code using shared service
        qr_service = QRCodeService()
        qr_config = QRCodeConfig(
            name=f"SIP Registration - {request.phone_number}",
            fill_color="#4F46E5",  # Indigo
            back_color="#FFFFFF",
            size=400,
            border=2
        )

        result = await qr_service.generate_qr_code(
            url=provisioning_url,
            config=qr_config
        )

        # Generate instructions
        instructions = f"""
Scan this QR code with Linphone app to auto-configure SIP registration:

1. Download Linphone from App Store/Play Store
2. Open Linphone → Tap menu → "Scan QR Code"
3. Scan this QR code
4. Linphone will automatically configure your account
5. Wait for "Registered" status (green indicator)

Manual Setup (if QR doesn't work):
- Username: {credentials.username}
- Password: {credentials.password}
- Domain: {credentials.domain}
- Transport: {credentials.transport}

Your number: {request.phone_number}
"""

        logger.info(f"Generated SIP registration QR code for {request.phone_number}")

        return SIPRegistrationQRResponse(
            qr_code_data_url=result.data_url,
            sip_uri=sip_uri,
            provisioning_url=provisioning_url,
            credentials=credentials,
            instructions=instructions.strip()
        )

    except Exception as e:
        logger.error(f"Error generating SIP registration QR code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{sip_username}")
async def get_sip_registration_status(sip_username: str):
    """
    Check SIP registration status for a given username.

    This endpoint checks if the SIP peer is registered with FreeSWITCH or Asterisk.

    Args:
        sip_username: SIP username to check

    Returns:
        Registration status information
    """
    try:
        # Try FreeSWITCH first (preferred)
        try:
            from apps.shared.freeswitch_api.client import FreeSWITCHAPIClient

            client = FreeSWITCHAPIClient(base_url="http://localhost:30040")

            # Check if peer is registered
            try:
                peer_info = await client.get_sip_peer_status(sip_username)
                registered = peer_info.get("registration_status") == "registered"
                status = peer_info.get("registration_status", "not_registered")
                ip_address = peer_info.get("ip_address")
                user_agent = peer_info.get("user_agent")
                last_registration = peer_info.get("last_registration")
                server = "freeswitch"
            except:
                # Peer not found or not registered
                registered = False
                status = "not_registered"
                ip_address = None
                user_agent = None
                last_registration = None
                server = "freeswitch"

        except ImportError:
            # FreeSWITCH client not available, try Asterisk (deprecated)
            logger.warning("FreeSWITCH client not available, trying Asterisk (deprecated)")
            from apps.shared.asterisk_api.client import AsteriskAPIClient

            client = AsteriskAPIClient(base_url="https://asterisk-api.ailabsafrica.com")

            # Check if peer is registered
            try:
                peer_info = await client.get_sip_peer_status(sip_username)
                registered = True
                status = "registered"
                ip_address = peer_info.get("ip_address")
                user_agent = peer_info.get("user_agent")
                last_registration = peer_info.get("last_registration")
                server = "asterisk"
            except:
                # Peer not found or not registered
                registered = False
                status = "not_registered"
                ip_address = None
                user_agent = None
                last_registration = None
                server = "asterisk"

        return {
            "success": True,
            "sip_username": sip_username,
            "status": status,
            "registered": registered,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "last_registration": last_registration,
            "server": server,
            "timestamp": None  # Will be filled with current time
        }

    except Exception as e:
        logger.error(f"Error checking SIP registration status: {e}")
        # Don't fail - return not registered status
        return {
            "success": True,
            "sip_username": sip_username,
            "status": "unknown",
            "registered": False,
            "error": str(e)
        }


@router.get("/ant-cellular/status")
async def get_ant_cellular_status(db = Depends(get_database)):
    """
    Get ANT cellular gateway registration status.

    This checks if any ANT cellular gateways are connected and their
    registration status with the mobile network.

    Returns:
        ANT cellular gateway status information
    """
    try:
        # Import service
        from apps.core_backend.backend.services.ant_gateway_service import ANTGatewayService

        # Get status from real service
        service = ANTGatewayService(db)
        result = await service.get_all_status()

        # Convert to response format expected by frontend
        gateways_list = []
        for gw in result.gateways:
            # Extract phone numbers from SIM cards
            phone_numbers = [
                sim.phone_number for sim in gw.sim_cards
                if sim.phone_number and sim.status == "registered"
            ]

            gateways_list.append({
                "gateway_id": gw.gateway_id,
                "name": gw.name,
                "status": gw.status,
                "sim_registered": any(sim.status == "registered" for sim in gw.sim_cards),
                "network_provider": gw.sim_cards[0].network_provider if gw.sim_cards else None,
                "signal_strength": gw.sim_cards[0].signal_strength if gw.sim_cards else 0,
                "phone_numbers": phone_numbers,
                "last_seen": gw.last_seen.isoformat() if gw.last_seen else None
            })

        # Add helpful message if no gateways configured
        message = None
        if result.total_gateways == 0:
            message = "No ANT cellular gateways configured. Add a gateway or use Linphone SIP registration."
        elif result.online_gateways == 0:
            message = "All configured gateways are offline. Check device connectivity."

        return {
            "success": True,
            "gateways": gateways_list,
            "total_gateways": result.total_gateways,
            "online_gateways": result.online_gateways,
            "registered_numbers": result.registered_sims,
            "message": message
        }

    except Exception as e:
        logger.error(f"Error getting ANT cellular status: {e}")
        return {
            "success": False,
            "error": str(e),
            "gateways": [],
            "total_gateways": 0,
            "online_gateways": 0,
            "registered_numbers": 0
        }
