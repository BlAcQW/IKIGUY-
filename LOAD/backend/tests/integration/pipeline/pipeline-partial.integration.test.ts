/**
 * Partial pipeline integration test: Real STT + Mock LLM + Real TTS
 *
 * Proves the pipeline works with mixed real/mock providers.
 * Useful when only STT + TTS keys are available (no OpenAI for LLM).
 *
 * Tests Deepgram STT → mock LLM → Cartesia/ElevenLabs/Deepgram TTS.
 */
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { describeIfKeys, requireKey, hasValidKey } from '../helpers/skip-if-missing.js';
import { assertValidPcmAudio } from '../helpers/audio-validators.js';
import { DeepgramSTTProvider } from '@/providers/stt/deepgram.js';
import { CartesiaTTSProvider } from '@/providers/tts/cartesia.js';
import { ElevenLabsTTSProvider } from '@/providers/tts/elevenlabs.js';
import { DeepgramTTSProvider } from '@/providers/tts/deepgram.js';
import { processPipelineTurn } from '@/voice-pipeline/pipeline.js';
import { createSession, endSession } from '@/voice-pipeline/session.js';
import type { LLMProvider, Message, LLMChatResult } from '@/providers/llm/types.js';

const __dirname_ = typeof __dirname !== 'undefined'
  ? __dirname
  : dirname(fileURLToPath(import.meta.url));

const FIXTURES = join(__dirname_, '..', 'fixtures');

/**
 * Simple mock LLM that always returns a fixed response.
 * This isolates the STT and TTS integration from the LLM provider.
 */
class MockLLMProvider implements LLMProvider {
  readonly name = 'mock-llm';
  private response: string;

  constructor(response: string = 'I understand. How can I help you today?') {
    this.response = response;
  }

  async chat(_messages: Message[]): Promise<string | LLMChatResult> {
    return this.response;
  }

  async *chatStream(_messages: Message[]): AsyncIterable<string> {
    for (const word of this.response.split(' ')) {
      yield word + ' ';
    }
  }
}

describeIfKeys(['DEEPGRAM_API_KEY'], 'Partial Pipeline (Deepgram STT → Mock LLM → Real TTS)', () => {
  let sessionId: string;

  beforeAll(async () => {
    const session = await createSession({
      callId: 'integration-test-partial',
      assistantId: 'test-assistant',
      organizationId: 'test-org',
      systemPrompt: 'You are a test assistant.',
    });
    sessionId = session.id;
  });

  afterAll(async () => {
    if (sessionId) {
      await endSession(sessionId);
    }
  });

  it('should run Deepgram STT → Mock LLM → Deepgram TTS', async () => {
    const audio = readFileSync(join(FIXTURES, 'hello-16k-mono.wav'));

    const config = {
      stt: new DeepgramSTTProvider(requireKey('DEEPGRAM_API_KEY')),
      llm: new MockLLMProvider(),
      tts: new DeepgramTTSProvider(requireKey('DEEPGRAM_API_KEY')),
    };

    const result = await processPipelineTurn(sessionId, audio, config, {
      format: 'wav',
    });

    expect(typeof result.userText).toBe('string');
    expect(result.assistantText).toBe('I understand. How can I help you today?');
    assertValidPcmAudio(result.audioBuffer, { minBytes: 500 });
  });

  // Only run if Cartesia key is present
  if (hasValidKey('CARTESIA_API_KEY')) {
    it('should run Deepgram STT → Mock LLM → Cartesia TTS', async () => {
      // Create a fresh session for this test
      const session = await createSession({
        callId: 'integration-test-partial-cartesia',
        assistantId: 'test-assistant',
        organizationId: 'test-org',
      });

      try {
        const audio = readFileSync(join(FIXTURES, 'hello-16k-mono.wav'));

        const config = {
          stt: new DeepgramSTTProvider(requireKey('DEEPGRAM_API_KEY')),
          llm: new MockLLMProvider('Hello from the Cartesia pipeline test.'),
          tts: new CartesiaTTSProvider(requireKey('CARTESIA_API_KEY')),
        };

        const result = await processPipelineTurn(session.id, audio, config, {
          format: 'wav',
        });

        expect(result.assistantText).toBe('Hello from the Cartesia pipeline test.');
        assertValidPcmAudio(result.audioBuffer, { minBytes: 500 });
      } finally {
        await endSession(session.id);
      }
    });
  }

  // Only run if ElevenLabs key is present
  if (hasValidKey('ELEVENLABS_API_KEY')) {
    it('should run Deepgram STT → Mock LLM → ElevenLabs TTS', async () => {
      const session = await createSession({
        callId: 'integration-test-partial-elevenlabs',
        assistantId: 'test-assistant',
        organizationId: 'test-org',
      });

      try {
        const audio = readFileSync(join(FIXTURES, 'hello-16k-mono.wav'));

        const config = {
          stt: new DeepgramSTTProvider(requireKey('DEEPGRAM_API_KEY')),
          llm: new MockLLMProvider('Hello from the ElevenLabs pipeline test.'),
          tts: new ElevenLabsTTSProvider(requireKey('ELEVENLABS_API_KEY')),
        };

        const result = await processPipelineTurn(session.id, audio, config, {
          format: 'wav',
        });

        expect(result.assistantText).toBe('Hello from the ElevenLabs pipeline test.');
        assertValidPcmAudio(result.audioBuffer, { minBytes: 500 });
      } finally {
        await endSession(session.id);
      }
    });
  }
});
