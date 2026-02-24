import { describe, it, expect, vi, beforeEach } from 'vitest';
import { WebRTCCallHandler } from './handler.js';

// ── Mocks ──

vi.mock('../database/client.js', () => ({
  prisma: {
    assistant: { findUnique: vi.fn(), findFirst: vi.fn() },
    tool: { findMany: vi.fn().mockResolvedValue([]) },
  },
}));

vi.mock('../config/index.js', () => ({
  config: {
    STUN_SERVERS: 'stun:stun.l.google.com:19302',
    TURN_URL: undefined,
    TURN_USERNAME: undefined,
    TURN_CREDENTIAL: undefined,
  },
}));

const mockCreateSession = vi.fn();
const mockGetSession = vi.fn();
const mockEndSession = vi.fn();
const mockAddMessage = vi.fn();
vi.mock('../voice-pipeline/session.js', () => ({
  createSession: (...args: unknown[]) => mockCreateSession(...args),
  getSession: (...args: unknown[]) => mockGetSession(...args),
  endSession: (...args: unknown[]) => mockEndSession(...args),
  addMessage: (...args: unknown[]) => mockAddMessage(...args),
}));

const mockProcessPipelineTurn = vi.fn();
vi.mock('../voice-pipeline/pipeline.js', () => ({
  processPipelineTurn: (...args: unknown[]) => mockProcessPipelineTurn(...args),
}));

vi.mock('../modules/calls/service.js', () => ({
  createCall: vi.fn().mockResolvedValue({ id: 'call-1' }),
  updateCallStatus: vi.fn(),
  endCall: vi.fn(),
  failCall: vi.fn(),
}));

vi.mock('../modules/webhooks/delivery.js', () => ({
  fireWebhookEvent: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('../providers/registry.js', () => ({
  buildPipelineFromAssistant: vi.fn().mockReturnValue({
    stt: { name: 'mock-stt', transcribe: vi.fn() },
    llm: { name: 'mock-llm', chat: vi.fn() },
    tts: { name: 'mock-tts', synthesize: vi.fn() },
  }),
}));

vi.mock('../voice-pipeline/squad-transfer.js', () => ({
  resolveTransfer: vi.fn(),
  executeTransfer: vi.fn(),
}));

// Mock @discordjs/opus
vi.mock('@discordjs/opus', () => {
  class MockOpusEncoder {
    constructor(_rate: number, _channels: number) {}
    decode(_input: Buffer): Buffer {
      return Buffer.alloc(1920); // 960 samples * 2 bytes
    }
    encode(_input: Buffer): Buffer {
      return Buffer.alloc(80);
    }
  }
  return { default: { OpusEncoder: MockOpusEncoder }, OpusEncoder: MockOpusEncoder };
});

vi.mock('../telephony/audio-resample.js', () => ({
  downsample: vi.fn((input: Buffer) => Buffer.alloc(Math.floor(input.length / 3))),
  upsample: vi.fn((input: Buffer) => Buffer.alloc(input.length * 2)),
}));

// Mock werift
const mockSetRemoteDescription = vi.fn();
const mockCreateAnswer = vi.fn().mockResolvedValue({ sdp: 'mock-answer-sdp' });
const mockSetLocalDescription = vi.fn();
const mockCreateDataChannel = vi.fn().mockReturnValue({
  readyState: 'open',
  send: vi.fn(),
  onopen: null,
  onmessage: null,
});
const mockAddTransceiver = vi.fn().mockReturnValue({
  sender: { sendRtp: vi.fn() },
  onTrack: { subscribe: vi.fn() },
});
const mockAddIceCandidate = vi.fn();
const mockClose = vi.fn();

vi.mock('werift', () => ({
  RTCPeerConnection: vi.fn().mockImplementation(() => ({
    setRemoteDescription: mockSetRemoteDescription,
    createAnswer: mockCreateAnswer,
    setLocalDescription: mockSetLocalDescription,
    createDataChannel: mockCreateDataChannel,
    addTransceiver: mockAddTransceiver,
    addIceCandidate: mockAddIceCandidate,
    close: mockClose,
    localDescription: { sdp: 'mock-answer-sdp' },
    connectionStateChange: { subscribe: vi.fn() },
  })),
  RTCSessionDescription: vi.fn().mockImplementation((sdp: string, type: string) => ({ sdp, type })),
  RTCIceCandidate: vi.fn().mockImplementation((data: object) => data),
  useSdesRTPStreamID: vi.fn(),
}));

function buildHandlerParams(overrides: Partial<ConstructorParameters<typeof WebRTCCallHandler>[0]> = {}) {
  return {
    organizationId: 'org-1',
    assistantId: 'ast-1',
    callId: 'call-1',
    sessionId: 'sess-1',
    pipeline: {
      stt: { name: 'mock-stt', transcribe: vi.fn() },
      llm: { name: 'mock-llm', chat: vi.fn() },
      tts: { name: 'mock-tts', synthesize: vi.fn() },
    },
    assistant: {
      id: 'ast-1',
      name: 'Test Assistant',
      model: { provider: 'openai', model: 'gpt-4' },
      voice: { provider: 'openai', voiceId: 'alloy' },
      transcriber: { provider: 'openai', model: 'whisper-1' },
      firstMessage: null,
      endCallPhrases: [],
      metadata: null,
    },
    ...overrides,
  };
}

describe('WebRTCCallHandler', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetSession.mockResolvedValue({
      id: 'sess-1',
      callId: 'call-1',
      assistantId: 'ast-1',
      organizationId: 'org-1',
      conversationHistory: [],
      status: 'active',
      startedAt: new Date(),
      metadata: {},
    });
  });

  describe('constructor', () => {
    it('should create a handler with correct properties', () => {
      const handler = new WebRTCCallHandler(buildHandlerParams());
      expect(handler.callId).toBe('call-1');
      expect(handler.sessionId).toBe('sess-1');
    });
  });

  describe('handleOffer', () => {
    it('should create a peer connection and return SDP answer', async () => {
      const handler = new WebRTCCallHandler(buildHandlerParams());
      const answer = await handler.handleOffer('mock-offer-sdp');

      expect(answer).toBe('mock-answer-sdp');
      expect(mockCreateDataChannel).toHaveBeenCalledWith('control');
      expect(mockAddTransceiver).toHaveBeenCalledWith('audio', { direction: 'sendrecv' });
      expect(mockSetRemoteDescription).toHaveBeenCalled();
      expect(mockCreateAnswer).toHaveBeenCalled();
      expect(mockSetLocalDescription).toHaveBeenCalled();
    });

    it('should subscribe to incoming RTP via onTrack', async () => {
      const handler = new WebRTCCallHandler(buildHandlerParams());
      await handler.handleOffer('mock-offer-sdp');

      const transceiver = mockAddTransceiver.mock.results[0].value;
      expect(transceiver.onTrack.subscribe).toHaveBeenCalled();
    });
  });

  describe('addIceCandidate', () => {
    it('should forward candidate to peer connection', async () => {
      const handler = new WebRTCCallHandler(buildHandlerParams());
      await handler.handleOffer('mock-offer-sdp');

      await handler.addIceCandidate({
        candidate: 'candidate:123',
        sdpMid: '0',
        sdpMLineIndex: 0,
      });

      expect(mockAddIceCandidate).toHaveBeenCalled();
    });
  });

  describe('close', () => {
    it('should end session and close peer connection', async () => {
      const handler = new WebRTCCallHandler(buildHandlerParams());
      await handler.handleOffer('mock-offer-sdp');
      await handler.close();

      expect(mockEndSession).toHaveBeenCalledWith('sess-1');
      expect(mockClose).toHaveBeenCalled();
    });

    it('should be idempotent', async () => {
      const handler = new WebRTCCallHandler(buildHandlerParams());
      await handler.handleOffer('mock-offer-sdp');
      await handler.close();
      await handler.close();

      // endSession should only be called once
      expect(mockEndSession).toHaveBeenCalledTimes(1);
    });
  });
});
