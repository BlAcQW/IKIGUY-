/**
 * Integration test: Cartesia Sonic TTS
 *
 * Sends real text to Cartesia API and verifies audio output.
 * Requires CARTESIA_API_KEY in .env.
 */
import { describe, it, expect } from 'vitest';
import { describeIfKey, requireKey } from '../helpers/skip-if-missing.js';
import { assertValidPcmAudio, getPcmStats } from '../helpers/audio-validators.js';
import { CartesiaTTSProvider } from '@/providers/tts/cartesia.js';

describeIfKey('CARTESIA_API_KEY', 'Cartesia Sonic TTS Provider', () => {
  let provider: CartesiaTTSProvider;

  beforeAll(() => {
    provider = new CartesiaTTSProvider(requireKey('CARTESIA_API_KEY'));
  });

  it('should synthesize text to valid PCM audio', async () => {
    const audio = await provider.synthesize('Hello, this is a test of the Cartesia text to speech system.');

    assertValidPcmAudio(audio, { minBytes: 1000 });

    const stats = getPcmStats(audio);
    expect(stats.durationMs).toBeGreaterThan(500);
  });

  it('should synthesize short text', async () => {
    const audio = await provider.synthesize('Hi.');

    assertValidPcmAudio(audio);
  });

  it('should throw an error with an invalid API key', async () => {
    const badProvider = new CartesiaTTSProvider('invalid-key-12345');

    await expect(
      badProvider.synthesize('Hello')
    ).rejects.toThrow();
  });
});
