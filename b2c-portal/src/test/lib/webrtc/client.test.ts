import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { startSession, stopSession } from '@/lib/webrtc/client';

describe('WebRTC client', () => {
        let trackStop: any;
        let pcMock: any;

        beforeEach(() => {
                trackStop = vi.fn();
                const mockStream = { getTracks: () => [{ stop: trackStop }] } as MediaStream;
                (navigator as any).mediaDevices = {
                        getUserMedia: vi.fn().mockResolvedValue(mockStream),
                };

                pcMock = {
                        addTrack: vi.fn(),
                        createOffer: vi.fn().mockResolvedValue({ type: 'offer', sdp: 'offer-sdp' }),
                        setLocalDescription: vi.fn().mockResolvedValue(undefined),
                        setRemoteDescription: vi.fn().mockResolvedValue(undefined),
                        close: vi.fn(),
                };
                (global as any).RTCPeerConnection = vi.fn(() => pcMock);

                (global as any).fetch = vi.fn().mockResolvedValue({
                        ok: true,
                        text: () => Promise.resolve('answer-sdp'),
                });
        });

        afterEach(() => {
                vi.clearAllMocks();
                stopSession();
        });

        it('starts and stops session successfully', async () => {
                const pc = await startSession();

                expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({ audio: true });
                expect(global.fetch).toHaveBeenCalledWith(
                        '/webrtc/offer',
                        expect.objectContaining({ method: 'POST', body: 'offer-sdp' }),
                );
                expect(pc.setRemoteDescription).toHaveBeenCalledWith({ type: 'answer', sdp: 'answer-sdp' });

                stopSession();
                expect(trackStop).toHaveBeenCalled();
                expect(pc.close).toHaveBeenCalled();
        });

        it('handles microphone permission errors', async () => {
                (navigator.mediaDevices.getUserMedia as any).mockRejectedValue(
                        new DOMException('', 'NotAllowedError'),
                );

                await expect(startSession()).rejects.toThrow('Microphone permission denied');
        });

        it('handles backend errors', async () => {
                (global as any).fetch = vi.fn().mockResolvedValue({ ok: false, status: 500 });

                await expect(startSession()).rejects.toThrow('Offer failed: 500');
        });
});

