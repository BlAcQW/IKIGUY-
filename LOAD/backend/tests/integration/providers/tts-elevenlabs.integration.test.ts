/**
 * Integration test: ElevenLabs TTS
 *
 * Sends real text to ElevenLabs API and verifies audio output.
 * Requires ELEVENLABS_API_KEY in .env.
 */
import { describe, it, expect } from 'vitest';
import { describeIfKey, requireKey } from '../helpers/skip-if-missing.js';
import { assertValidPcmAudio, getPcmStats } from '../helpers/audio-validators.js';
import { ElevenLabsTTSProvider } from '@/providers/tts/elevenlabs.js';

describeIfKey('ELEVENLABS_API_KEY', 'ElevenLabs TTS Provider', () => {
  let provider: ElevenLabsTTSProvider;

  beforeAll(() => {
    provider = new ElevenLabsTTSProvider(requireKey('ELEVENLABS_API_KEY'));
  });

  it('should synthesize text to valid PCM audio', async () => {
    const audio = await provider.synthesize('Hello, this is a test of the ElevenLabs text to speech system.');

    assertValidPcmAudio(audio, { minBytes: 1000 });

    const stats = getPcmStats(audio);
    // Should be at least 500ms of audio for this sentence
    expect(stats.durationMs).toBeGreaterThan(500);
  });

  it('should synthesize short text', async () => {
    const audio = await provider.synthesize('Hi.');

    assertValidPcmAudio(audio);
  });

  it('should throw an error with an invalid API key', async () => {
    const badProvider = new ElevenLabsTTSProvider('invalid-key-12345');

    await expect(
      badProvider.synthesize('Hello')
    ).rejects.toThrow();
  });
});
