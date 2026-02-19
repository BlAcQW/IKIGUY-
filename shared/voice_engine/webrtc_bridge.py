"""WebRTC softphone bridge for Demo 18.

Provides a FastAPI router that accepts an SDP offer from a client
softphone and responds with an SDP answer. Audio frames can then
be routed into the existing voice pipeline.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration

router = APIRouter()


class Offer(BaseModel):
    """Represents an SDP offer from the softphone."""

    sdp: str
    type: str = "offer"


class Answer(BaseModel):
    """Represents an SDP answer to return to the softphone."""

    sdp: str
    type: str = "answer"


@router.post("/webrtc/offer", response_model=Answer)
async def webrtc_offer(offer: Offer) -> Answer:
    """Generate an SDP answer for a given offer.

    Args:
        offer (Offer): The SDP offer from the client.

    Returns:
        Answer: The SDP answer to complete the handshake.
    """

    pc = RTCPeerConnection(configuration=RTCConfiguration(iceServers=[]))
    await pc.setRemoteDescription(RTCSessionDescription(sdp=offer.sdp, type=offer.type))
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    sdp = pc.localDescription.sdp
    await pc.close()
    return Answer(sdp=sdp, type="answer")
