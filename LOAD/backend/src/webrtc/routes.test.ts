import { describe, it, expect, vi, beforeEach } from 'vitest';

// ── Mocks — must use factory functions, not top-level references ──

vi.mock('../database/client.js', () => ({
  prisma: {
    assistant: { findFirst: vi.fn(), findUnique: vi.fn() },
    tool: { findMany: vi.fn().mockResolvedValue([]) },
    $connect: vi.fn(),
    $disconnect: vi.fn(),
  },
  connectDatabase: vi.fn(),
  disconnectDatabase: vi.fn(),
}));

vi.mock('../config/index.js', () => ({
  config: {
    NODE_ENV: 'test',
    PORT: 3000,
    DATABASE_URL: 'postgresql://test:test@localhost:5432/test_db',
    REDIS_URL: 'redis://localhost:6379',
    JWT_SECRET: 'test-secret-key-minimum-16-chars',
    JWT_EXPIRES_IN: '15m',
    JWT_REFRESH_EXPIRES_IN: '7d',
    FRONTEND_URL: 'http://localhost:5173',
    API_URL: 'http://localhost:3000',
    WEBHOOK_SECRET: 'test-webhook-secret',
    ASTERISK_ARI_APP: 'load',
    STUN_SERVERS: 'stun:stun.l.google.com:19302',
  },
}));

vi.mock('../modules/calls/service.js', () => ({
  createCall: vi.fn().mockResolvedValue({ id: 'call-123' }),
  updateCallStatus: vi.fn(),
  endCall: vi.fn(),
  failCall: vi.fn(),
}));

vi.mock('../voice-pipeline/session.js', () => ({
  createSession: vi.fn().mockResolvedValue({ id: 'sess-123' }),
  getSession: vi.fn().mockResolvedValue({ id: 'sess-123', conversationHistory: [] }),
  endSession: vi.fn(),
  addMessage: vi.fn(),
  initializeSessionStore: vi.fn(),
}));

vi.mock('../providers/registry.js', () => ({
  buildPipelineFromAssistant: vi.fn().mockReturnValue({
    stt: { name: 'mock-stt', transcribe: vi.fn() },
    llm: { name: 'mock-llm', chat: vi.fn() },
    tts: { name: 'mock-tts', synthesize: vi.fn() },
  }),
}));

vi.mock('../modules/webhooks/delivery.js', () => ({
  fireWebhookEvent: vi.fn().mockResolvedValue(undefined),
  createWebhookWorker: vi.fn(),
  closeWebhookQueue: vi.fn(),
}));

vi.mock('../modules/campaigns/engine.js', () => ({
  createCampaignQueues: vi.fn(),
  setCallBridge: vi.fn(),
  closeCampaignQueues: vi.fn(),
}));

vi.mock('../voice-pipeline/squad-transfer.js', () => ({
  resolveTransfer: vi.fn(),
  executeTransfer: vi.fn(),
}));

vi.mock('@discordjs/opus', () => {
  class MockOpusEncoder {
    constructor(_rate: number, _channels: number) {}
    decode(_input: Buffer): Buffer { return Buffer.alloc(1920); }
    encode(_input: Buffer): Buffer { return Buffer.alloc(80); }
  }
  return { default: { OpusEncoder: MockOpusEncoder }, OpusEncoder: MockOpusEncoder };
});

vi.mock('../telephony/audio-resample.js', () => ({
  downsample: vi.fn((input: Buffer) => Buffer.alloc(Math.floor(input.length / 3))),
  upsample: vi.fn((input: Buffer) => Buffer.alloc(input.length * 2)),
  resample: vi.fn((input: Buffer) => Buffer.from(input)),
}));

// Mock werift
vi.mock('werift', () => ({
  RTCPeerConnection: vi.fn().mockImplementation(() => ({
    setRemoteDescription: vi.fn(),
    createAnswer: vi.fn().mockResolvedValue({ sdp: 'answer-sdp' }),
    setLocalDescription: vi.fn(),
    createDataChannel: vi.fn().mockReturnValue({
      readyState: 'open',
      send: vi.fn(),
      onopen: null,
    }),
    addTransceiver: vi.fn().mockReturnValue({
      sender: { sendRtp: vi.fn() },
      onTrack: { subscribe: vi.fn() },
    }),
    addIceCandidate: vi.fn(),
    close: vi.fn(),
    localDescription: { sdp: 'answer-sdp' },
    connectionStateChange: { subscribe: vi.fn() },
  })),
  RTCSessionDescription: vi.fn().mockImplementation((sdp: string, type: string) => ({ sdp, type })),
  RTCIceCandidate: vi.fn().mockImplementation((data: object) => data),
  MediaStreamTrack: vi.fn(),
  RtpPacket: vi.fn(),
}));

// Mock auth middleware
vi.mock('../middleware/auth.js', () => ({
  authMiddleware: vi.fn().mockImplementation(async (request: any) => {
    request.userId = 'user-1';
    request.organizationId = 'org-1';
    request.userRole = 'OWNER';
  }),
}));

vi.mock('../middleware/rate-limit.js', () => ({
  registerRateLimit: vi.fn(),
}));

// Import after mocks
import { buildApp } from '../index.js';
import { prisma } from '../database/client.js';

describe('WebRTC Routes', () => {
  let app: Awaited<ReturnType<typeof buildApp>>;

  beforeEach(async () => {
    vi.clearAllMocks();
    app = await buildApp();
  });

  describe('POST /api/calls/webrtc/offer', () => {
    it('should return 400 for invalid body', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/calls/webrtc/offer',
        headers: { authorization: 'Bearer test-token' },
        payload: { assistantId: 'not-a-uuid' },
      });

      expect(response.statusCode).toBe(400);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(false);
    });

    it('should return 404 when assistant not found', async () => {
      (prisma.assistant.findFirst as any).mockResolvedValue(null);

      const response = await app.inject({
        method: 'POST',
        url: '/api/calls/webrtc/offer',
        headers: { authorization: 'Bearer test-token' },
        payload: {
          assistantId: '00000000-0000-0000-0000-000000000001',
          sdpOffer: 'v=0\r\no=- 0 0 IN IP4 0.0.0.0\r\n',
        },
      });

      expect(response.statusCode).toBe(404);
    });

    it('should return SDP answer on success', async () => {
      const mockAssistant = {
        id: '00000000-0000-0000-0000-000000000001',
        name: 'Test Assistant',
        organizationId: 'org-1',
        model: { provider: 'openai', model: 'gpt-4' },
        voice: { provider: 'openai', voiceId: 'alloy' },
        transcriber: { provider: 'openai', model: 'whisper-1' },
        firstMessage: null,
        endCallPhrases: [],
        metadata: null,
      };
      (prisma.assistant.findFirst as any).mockResolvedValue(mockAssistant);

      const response = await app.inject({
        method: 'POST',
        url: '/api/calls/webrtc/offer',
        headers: { authorization: 'Bearer test-token' },
        payload: {
          assistantId: '00000000-0000-0000-0000-000000000001',
          sdpOffer: 'v=0\r\no=- 0 0 IN IP4 0.0.0.0\r\n',
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(true);
      expect(body.data.callId).toBe('call-123');
      expect(body.data.sessionId).toBe('sess-123');
      expect(body.data.sdpAnswer).toBe('answer-sdp');
    });
  });

  describe('POST /api/calls/webrtc/ice', () => {
    it('should return 400 for invalid body', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/calls/webrtc/ice',
        headers: { authorization: 'Bearer test-token' },
        payload: { callId: 'bad-id' },
      });

      expect(response.statusCode).toBe(400);
    });

    it('should return 404 when handler not found', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/calls/webrtc/ice',
        headers: { authorization: 'Bearer test-token' },
        payload: {
          callId: '00000000-0000-0000-0000-000000000099',
          candidate: { candidate: 'candidate:123', sdpMid: '0', sdpMLineIndex: 0 },
        },
      });

      expect(response.statusCode).toBe(404);
    });
  });

  describe('POST /api/calls/webrtc/:callId/end', () => {
    it('should return 404 when handler not found', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/calls/webrtc/00000000-0000-0000-0000-000000000099/end',
        headers: { authorization: 'Bearer test-token' },
      });

      expect(response.statusCode).toBe(404);
    });
  });
});
