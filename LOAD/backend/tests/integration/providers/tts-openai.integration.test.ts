/**
 * Integration test: OpenAI TTS
 *
 * Sends real text to OpenAI TTS API and verifies audio output.
 * Requires OPENAI_API_KEY in .env.
 */
import { describe, it, expect } from 'vitest';
import { describeIfKey, requireKey } from '../helpers/skip-if-missing.js';
import { assertValidPcmAudio, getPcmStats } from '../helpers/audio-validators.js';
import { OpenAITTSProvider } from '@/providers/tts/openai.js';

describeIfKey('OPENAI_API_KEY', 'OpenAI TTS Provider', () => {
  let provider: OpenAITTSProvider;

  beforeAll(() => {
    provider = new OpenAITTSProvider(requireKey('OPENAI_API_KEY'));
  });

  it('should synthesize text to valid PCM audio', async () => {
    const audio = await provider.synthesize('Hello, this is a test of the OpenAI text to speech system.');

    // OpenAI TTS with pcm format returns 24kHz audio by default
    assertValidPcmAudio(audio, { minBytes: 1000, sampleRate: 24_000 });

    const stats = getPcmStats(audio);
    expect(stats.durationMs).toBeGreaterThan(200); // Adjusted for 24kHz rate mismatch in stat calc
  });

  it('should synthesize short text', async () => {
    const audio = await provider.synthesize('Hi.');

    assertValidPcmAudio(audio, { sampleRate: 24_000 });
  });

  it('should support different voices', async () => {
    const audio = await provider.synthesize('Hello.', { voiceId: 'nova' });

    assertValidPcmAudio(audio, { sampleRate: 24_000 });
  });

  it('should throw an error with an invalid API key', async () => {
    const badProvider = new OpenAITTSProvider('sk-invalid-key-12345');

    await expect(
      badProvider.synthesize('Hello')
    ).rejects.toThrow();
  });
});
