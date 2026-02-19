/**
 * Simple WebRTC client for audio sessions.
 *
 * Provides helpers to start and stop an audio-only WebRTC session by
 * negotiating SDP with the backend.
 */

let pc: RTCPeerConnection | null = null;
let localStream: MediaStream | null = null;

/**
 * Start a WebRTC session.
 *
 * Requests microphone access, builds an SDP offer and posts it to the backend
 * at `/webrtc/offer`. The SDP answer returned from the backend is then applied
 * to the peer connection.
 *
 * Returns:
 *   The active RTCPeerConnection instance.
 */
export async function startSession(): Promise<RTCPeerConnection> {
        if (pc) {
                return pc;
        }

        try {
                localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        } catch (err) {
                // Reason: provide clearer error for permission denials
                if (err instanceof DOMException && err.name === 'NotAllowedError') {
                        throw new Error('Microphone permission denied');
                }
                throw err;
        }

        pc = new RTCPeerConnection();
        localStream.getTracks().forEach(track => pc!.addTrack(track, localStream!));

        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        const response = await fetch('/webrtc/offer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/sdp' },
                body: offer.sdp ?? '',
        });

        if (!response.ok) {
                throw new Error(`Offer failed: ${response.status}`);
        }

        const answerSdp = await response.text();
        await pc.setRemoteDescription({ type: 'answer', sdp: answerSdp });

        return pc;
}

/**
 * Stop the active WebRTC session and release resources.
 */
export function stopSession(): void {
        localStream?.getTracks().forEach(track => track.stop());
        pc?.close();
        pc = null;
        localStream = null;
}

