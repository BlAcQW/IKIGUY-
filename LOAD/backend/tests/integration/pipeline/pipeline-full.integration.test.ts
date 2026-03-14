/**
 * Full pipeline integration test: STT → LLM → TTS
 *
 * Runs real audio through the entire voice pipeline with real provider APIs.
 * Requires OPENAI_API_KEY (for LLM + STT + TTS).
 *
 * This is the gold standard test — if this passes, the pipeline works end-to-end.
 */
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { describeIfKey, requireKey } from '../helpers/skip-if-missing.js';
import { assertValidPcmAudio } from '../helpers/audio-validators.js';
import { OpenAISTTProvider } from '@/providers/stt/openai.js';
import { OpenAILLMProvider } from '@/providers/llm/openai.js';
import { OpenAITTSProvider } from '@/providers/tts/openai.js';
import { processPipelineTurn } from '@/voice-pipeline/pipeline.js';
import { createSession, endSession } from '@/voice-pipeline/session.js';

const __dirname_ = typeof __dirname !== 'undefined'
  ? __dirname
  : dirname(fileURLToPath(import.meta.url));

const FIXTURES = join(__dirname_, '..', 'fixtures');

describeIfKey('OPENAI_API_KEY', 'Full Pipeline (OpenAI STT → LLM → TTS)', () => {
  let sessionId: string;

  beforeAll(async () => {
    const session = await createSession({
      callId: 'integration-test-full',
      assistantId: 'test-assistant',
      organizationId: 'test-org',
      systemPrompt: 'You are a helpful assistant. Keep responses to one short sentence.',
    });
    sessionId = session.id;
  });

  afterAll(async () => {
    if (sessionId) {
      await endSession(sessionId);
    }
  });

  it('should process audio through the entire pipeline', async () => {
    const apiKey = requireKey('OPENAI_API_KEY');
    const audio = readFileSync(join(FIXTURES, 'hello-16k-mono.wav'));

    const config = {
      stt: new OpenAISTTProvider(apiKey),
      llm: new OpenAILLMProvider(apiKey),
      tts: new OpenAITTSProvider(apiKey),
    };

    const result = await processPipelineTurn(sessionId, audio, config, {
      llmModel: 'gpt-4o-mini',
      llmMaxTokens: 100,
      format: 'wav',
    });

    // STT produced some text (even if it's just noise transcription)
    expect(typeof result.userText).toBe('string');

    // LLM produced a response
    expect(typeof result.assistantText).toBe('string');
    expect(result.assistantText.length).toBeGreaterThan(0);

    // TTS produced valid audio
    assertValidPcmAudio(result.audioBuffer, { sampleRate: 24_000 });

    // No tool calls or special signals
    expect(result.toolCallsExecuted).toEqual([]);
    expect(result.endCallRequested).toBe(false);
    expect(result.transferRequest).toBeUndefined();
  });
});
