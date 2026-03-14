import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { WebSocket } from 'ws';
import { createPrismaMock, type PrismaMock } from '../../tests/helpers/prisma-mock.js';
import { buildAssistant } from '../../tests/helpers/factories.js';

let prismaMock: PrismaMock;

// Mock dependencies
vi.mock('../database/client.js', () => ({
  get prisma() {
    return prismaMock;
  },
}));

vi.mock('./mulaw-codec.js', () => ({
  decodeTwilioAudio: vi.fn((buf: Buffer) => Buffer.alloc(buf.length * 4)), // simulate 4x expansion
  encodeTwilioAudio: vi.fn((buf: Buffer) => Buffer.alloc(Math.floor(buf.length / 6))), // simulate 24k->8k mulaw
}));

vi.mock('./vad.js', () => ({
  SimpleVAD: vi.fn().mockImplementation(() => ({
    processChunk: vi.fn().mockReturnValue({ isSpeech: false, speechComplete: false }),
    reset: vi.fn(),
  })),
}));

vi.mock('../voice-pipeline/pipeline.js', () => ({
  processPipelineTurn: vi.fn(),
}));

vi.mock('../voice-pipeline/session.js', () => ({
  getSession: vi.fn(),
  endSession: vi.fn(),
  addMessage: vi.fn(),
  createSession: vi.fn(),
}));

vi.mock('../modules/calls/service.js', () => ({
  endCall: vi.fn(),
  failCall: vi.fn(),
  createCall: vi.fn(),
  updateCallStatus: vi.fn(),
}));

vi.mock('../providers/registry.js', () => ({
  buildPipelineFromAssistant: vi.fn().mockReturnValue({
    stt: { transcribe: vi.fn() },
    llm: { chat: vi.fn() },
    tts: { synthesize: vi.fn().mockResolvedValue(Buffer.alloc(480)) },
  }),
}));

vi.mock('../modules/webhooks/delivery.js', () => ({
  fireWebhookEvent: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('../voice-pipeline/squad-transfer.js', () => ({
  resolveTransfer: vi.fn(),
  executeTransfer: vi.fn(),
}));

vi.mock('../voice-pipeline/pipeline-helpers.js', () => ({
  extractAssistantConfig: vi.fn().mockReturnValue({
    modelConfig: { model: 'gpt-4' },
    voiceConfig: { voiceId: 'alloy' },
    transcriberConfig: { model: 'whisper-1' },
  }),
  loadToolsForPipeline: vi.fn().mockResolvedValue(undefined),
}));

import { handleTwilioMediaStream, activeStreams, type TwilioStreamState } from './twilio-stream.js';
import { endCall, failCall } from '../modules/calls/service.js';
import { getSession, endSession, addMessage } from '../voice-pipeline/session.js';
import { fireWebhookEvent } from '../modules/webhooks/delivery.js';
import { processPipelineTurn } from '../voice-pipeline/pipeline.js';
import { decodeTwilioAudio, encodeTwilioAudio } from './mulaw-codec.js';
import { SimpleVAD } from './vad.js';

// ---------------------------------------------------------------------------
// Mock WebSocket
// ---------------------------------------------------------------------------

function createMockSocket(): WebSocket {
  const handlers: Record<string, ((...args: unknown[]) => void)[]> = {};
  const socket = {
    readyState: WebSocket.OPEN,
    on: vi.fn((event: string, handler: (...args: unknown[]) => void) => {
      handlers[event] = handlers[event] ?? [];
      handlers[event].push(handler);
    }),
    send: vi.fn(),
    close: vi.fn(),
    // Helper to trigger events
    __emit: (event: string, ...args: unknown[]) => {
      for (const handler of handlers[event] ?? []) {
        handler(...args);
      }
    },
  } as unknown as WebSocket & { __emit: (event: string, ...args: unknown[]) => void };
  return socket;
}

describe('twilio-stream', () => {
  let socket: WebSocket & { __emit: (event: string, ...args: unknown[]) => void };

  beforeEach(() => {
    vi.clearAllMocks();
    prismaMock = createPrismaMock();
    activeStreams.clear();
    socket = createMockSocket();
  });

  afterEach(() => {
    activeStreams.clear();
  });

  describe('handleTwilioMediaStream', () => {
    it('registers message, close, and error handlers', () => {
      handleTwilioMediaStream(socket);
      expect(socket.on).toHaveBeenCalledWith('message', expect.any(Function));
      expect(socket.on).toHaveBeenCalledWith('close', expect.any(Function));
      expect(socket.on).toHaveBeenCalledWith('error', expect.any(Function));
    });
  });

  describe('message dispatch', () => {
    it('handles connected event without error', async () => {
      handleTwilioMediaStream(socket);
      // Should not throw
      await socket.__emit('message', JSON.stringify({
        event: 'connected',
        streamSid: 'MZ_test',
      }));
    });

    it('ignores unknown event types', async () => {
      handleTwilioMediaStream(socket);
      await socket.__emit('message', JSON.stringify({
        event: 'unknown_event',
      }));
      // No error, no state change
      expect(activeStreams.size).toBe(0);
    });

    it('handles invalid JSON gracefully', async () => {
      handleTwilioMediaStream(socket);
      await socket.__emit('message', 'not-json');
      // Should not throw
      expect(activeStreams.size).toBe(0);
    });
  });

  describe('onStart', () => {
    it('extracts custom parameters and builds state', async () => {
      const assistant = buildAssistant({
        id: 'asst-1',
        organizationId: 'org-1',
        firstMessage: null,
      });
      prismaMock.assistant.findFirst.mockResolvedValue(assistant);

      handleTwilioMediaStream(socket);
      await socket.__emit('message', JSON.stringify({
        event: 'start',
        start: {
          streamSid: 'MZ_stream1',
          accountSid: 'AC_test',
          callSid: 'CA_test',
          customParameters: {
            callId: 'call-1',
            sessionId: 'session-1',
            assistantId: 'asst-1',
            organizationId: 'org-1',
          },
        },
      }));

      // Allow async to settle
      await new Promise((r) => setTimeout(r, 10));

      expect(activeStreams.has(socket)).toBe(true);
      const state = activeStreams.get(socket)!;
      expect(state.callId).toBe('call-1');
      expect(state.sessionId).toBe('session-1');
      expect(state.assistantId).toBe('asst-1');
      expect(state.organizationId).toBe('org-1');
      expect(state.streamSid).toBe('MZ_stream1');
    });

    it('closes socket when custom parameters are missing', async () => {
      handleTwilioMediaStream(socket);
      await socket.__emit('message', JSON.stringify({
        event: 'start',
        start: {
          streamSid: 'MZ_no_params',
          accountSid: 'AC_test',
          callSid: 'CA_test',
          customParameters: {},
        },
      }));

      await new Promise((r) => setTimeout(r, 10));

      expect(socket.close).toHaveBeenCalledWith(1008, 'Missing required parameters');
      expect(activeStreams.has(socket)).toBe(false);
    });

    it('sends first message if configured', async () => {
      const assistant = buildAssistant({
        id: 'asst-1',
        organizationId: 'org-1',
        firstMessage: 'Welcome!',
        voice: { provider: 'openai', voiceId: 'alloy', speed: 1.0 },
      });
      prismaMock.assistant.findFirst.mockResolvedValue(assistant);

      handleTwilioMediaStream(socket);
      await socket.__emit('message', JSON.stringify({
        event: 'start',
        start: {
          streamSid: 'MZ_first_msg',
          accountSid: 'AC_test',
          callSid: 'CA_test',
          customParameters: {
            callId: 'call-1',
            sessionId: 'session-1',
            assistantId: 'asst-1',
            organizationId: 'org-1',
          },
        },
      }));

      await new Promise((r) => setTimeout(r, 50));

      expect(addMessage).toHaveBeenCalledWith('session-1', {
        role: 'assistant',
        content: 'Welcome!',
      });
      // Should have sent clear + media + mark events
      expect(socket.send).toHaveBeenCalled();
    });
  });

  describe('onMedia', () => {
    let state: TwilioStreamState;

    beforeEach(() => {
      const mockVad = new SimpleVAD();
      state = {
        streamSid: 'MZ_test',
        callId: 'call-1',
        sessionId: 'session-1',
        assistantId: 'asst-1',
        organizationId: 'org-1',
        pipeline: {
          stt: { transcribe: vi.fn() },
          llm: { chat: vi.fn() },
          tts: { synthesize: vi.fn().mockResolvedValue(Buffer.alloc(480)) },
        } as unknown as PipelineConfig,
        vad: mockVad,
        audioChunks: [],
        processing: false,
      };
      activeStreams.set(socket, state);
    });

    it('decodes base64 mu-law payload', async () => {
      handleTwilioMediaStream(socket);
      const payload = Buffer.alloc(100).toString('base64');
      await socket.__emit('message', JSON.stringify({
        event: 'media',
        media: { track: 'inbound', chunk: '1', timestamp: '0', payload },
      }));

      await new Promise((r) => setTimeout(r, 10));
      expect(decodeTwilioAudio).toHaveBeenCalled();
    });

    it('drops audio when processing is true', async () => {
      state.processing = true;
      handleTwilioMediaStream(socket);

      const payload = Buffer.alloc(100).toString('base64');
      await socket.__emit('message', JSON.stringify({
        event: 'media',
        media: { track: 'inbound', chunk: '1', timestamp: '0', payload },
      }));

      await new Promise((r) => setTimeout(r, 10));
      // decodeTwilioAudio should NOT be called
      expect(decodeTwilioAudio).not.toHaveBeenCalled();
    });

    it('accumulates audio chunks when VAD detects speech', async () => {
      (state.vad.processChunk as any).mockReturnValue({ isSpeech: true, speechComplete: false });
      handleTwilioMediaStream(socket);

      const payload = Buffer.alloc(100).toString('base64');
      await socket.__emit('message', JSON.stringify({
        event: 'media',
        media: { track: 'inbound', chunk: '1', timestamp: '0', payload },
      }));

      await new Promise((r) => setTimeout(r, 10));
      expect(state.audioChunks.length).toBe(1);
    });

    it('triggers pipeline turn on speechComplete', async () => {
      (state.vad.processChunk as any).mockReturnValue({ isSpeech: false, speechComplete: true });
      state.audioChunks = [Buffer.alloc(200)]; // Pre-fill some audio

      const assistant = buildAssistant({ id: 'asst-1' });
      prismaMock.assistant.findUnique.mockResolvedValue(assistant);
      (processPipelineTurn as any).mockResolvedValue({
        userText: 'hello',
        assistantText: 'hi there',
        audioBuffer: Buffer.alloc(480),
        toolCallsExecuted: [],
        endCallRequested: false,
      });

      handleTwilioMediaStream(socket);

      const payload = Buffer.alloc(100).toString('base64');
      await socket.__emit('message', JSON.stringify({
        event: 'media',
        media: { track: 'inbound', chunk: '1', timestamp: '0', payload },
      }));

      await new Promise((r) => setTimeout(r, 100));

      expect(processPipelineTurn).toHaveBeenCalled();
      expect(encodeTwilioAudio).toHaveBeenCalled();
    });
  });

  describe('onStop', () => {
    it('ends session and call, fires webhook', async () => {
      const state: TwilioStreamState = {
        streamSid: 'MZ_stop',
        callId: 'call-stop',
        sessionId: 'session-stop',
        assistantId: 'asst-1',
        organizationId: 'org-1',
        pipeline: {} as PipelineConfig,
        vad: new SimpleVAD(),
        audioChunks: [],
        processing: false,
      };
      activeStreams.set(socket, state);

      (getSession as any).mockResolvedValue({
        conversationHistory: [
          { role: 'system', content: 'You are helpful' },
          { role: 'assistant', content: 'Hello!' },
          { role: 'user', content: 'Hi' },
        ],
        startedAt: new Date(Date.now() - 60_000),
      });
      (endCall as any).mockResolvedValue({});
      (endSession as any).mockResolvedValue(undefined);

      handleTwilioMediaStream(socket);
      await socket.__emit('message', JSON.stringify({ event: 'stop' }));

      await new Promise((r) => setTimeout(r, 50));

      expect(endSession).toHaveBeenCalledWith('session-stop');
      expect(endCall).toHaveBeenCalledWith('call-stop', expect.any(Array), 'hangup');
      expect(fireWebhookEvent).toHaveBeenCalledWith('org-1', 'call.ended', expect.objectContaining({
        callId: 'call-stop',
        endReason: 'hangup',
      }));
      expect(activeStreams.has(socket)).toBe(false);
    });

    it('cleans up on close event', async () => {
      const state: TwilioStreamState = {
        streamSid: 'MZ_close',
        callId: 'call-close',
        sessionId: 'session-close',
        assistantId: 'asst-1',
        organizationId: 'org-1',
        pipeline: {} as PipelineConfig,
        vad: new SimpleVAD(),
        audioChunks: [],
        processing: false,
      };
      activeStreams.set(socket, state);

      (getSession as any).mockResolvedValue({
        conversationHistory: [],
        startedAt: new Date(),
      });
      (endCall as any).mockResolvedValue({});
      (endSession as any).mockResolvedValue(undefined);

      handleTwilioMediaStream(socket);
      await socket.__emit('close');

      await new Promise((r) => setTimeout(r, 50));

      expect(endSession).toHaveBeenCalledWith('session-close');
      expect(activeStreams.has(socket)).toBe(false);
    });
  });

  describe('error handling', () => {
    it('fails call and cleans up on WebSocket error', async () => {
      const state: TwilioStreamState = {
        streamSid: 'MZ_error',
        callId: 'call-error',
        sessionId: 'session-error',
        assistantId: 'asst-1',
        organizationId: 'org-1',
        pipeline: {} as PipelineConfig,
        vad: new SimpleVAD(),
        audioChunks: [],
        processing: false,
      };
      activeStreams.set(socket, state);

      (failCall as any).mockResolvedValue({});
      (endSession as any).mockResolvedValue(undefined);

      handleTwilioMediaStream(socket);
      await socket.__emit('error', new Error('Connection reset'));

      await new Promise((r) => setTimeout(r, 50));

      expect(failCall).toHaveBeenCalledWith('call-error', 'websocket_error');
      expect(endSession).toHaveBeenCalledWith('session-error');
      expect(activeStreams.has(socket)).toBe(false);
    });
  });
});
