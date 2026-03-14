/**
 * Integration test: Deepgram Aura TTS
 *
 * Sends real text to Deepgram TTS API and verifies audio output.
 * Requires DEEPGRAM_API_KEY in .env.
 */
import { describe, it, expect } from 'vitest';
import { describeIfKey, requireKey } from '../helpers/skip-if-missing.js';
import { assertValidPcmAudio, getPcmStats } from '../helpers/audio-validators.js';
import { DeepgramTTSProvider } from '@/providers/tts/deepgram.js';

describeIfKey('DEEPGRAM_API_KEY', 'Deepgram Aura TTS Provider', () => {
  let provider: DeepgramTTSProvider;

  beforeAll(() => {
    provider = new DeepgramTTSProvider(requireKey('DEEPGRAM_API_KEY'));
  });

  it('should synthesize text to valid PCM audio', async () => {
    const audio = await provider.synthesize('Hello, this is a test of the Deepgram text to speech system.');

    assertValidPcmAudio(audio, { minBytes: 1000 });

    const stats = getPcmStats(audio);
    expect(stats.durationMs).toBeGreaterThan(500);
  });

  it('should synthesize short text', async () => {
    const audio = await provider.synthesize('Hi.');

    assertValidPcmAudio(audio);
  });

  it('should throw an error with an invalid API key', async () => {
    const badProvider = new DeepgramTTSProvider('invalid-key-12345');

    await expect(
      badProvider.synthesize('Hello')
    ).rejects.toThrow();
  });
});
