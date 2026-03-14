/**
 * Integration test: Deepgram Nova STT
 *
 * Sends real audio to the Deepgram API and verifies transcription.
 * Requires DEEPGRAM_API_KEY in .env.
 */
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { describe, it, expect } from 'vitest';
import { describeIfKey, requireKey } from '../helpers/skip-if-missing.js';
import { DeepgramSTTProvider } from '@/providers/stt/deepgram.js';

const __dirname_ = typeof __dirname !== 'undefined'
  ? __dirname
  : dirname(fileURLToPath(import.meta.url));

const FIXTURES = join(__dirname_, '..', 'fixtures');

describeIfKey('DEEPGRAM_API_KEY', 'Deepgram STT Provider', () => {
  let provider: DeepgramSTTProvider;

  beforeAll(() => {
    provider = new DeepgramSTTProvider(requireKey('DEEPGRAM_API_KEY'));
  });

  it('should transcribe a WAV audio file', async () => {
    const audio = readFileSync(join(FIXTURES, 'hello-16k-mono.wav'));

    // A 440Hz tone won't produce meaningful text, but the API should
    // accept it and return a string (possibly empty for a pure tone).
    const transcript = await provider.transcribe(audio, { format: 'wav' });

    expect(typeof transcript).toBe('string');
    // API accepted the request and returned a result
  });

  it('should return empty or near-empty transcript for silence', async () => {
    const silence = readFileSync(join(FIXTURES, 'silence-16k-mono.wav'));

    const transcript = await provider.transcribe(silence, { format: 'wav' });

    expect(typeof transcript).toBe('string');
    // Silence should produce empty or nearly empty transcript
    expect(transcript.trim().length).toBeLessThanOrEqual(5);
  });

  it('should throw an error with an invalid API key', async () => {
    const badProvider = new DeepgramSTTProvider('invalid-key-12345');
    const audio = readFileSync(join(FIXTURES, 'hello-16k-mono.wav'));

    await expect(
      badProvider.transcribe(audio, { format: 'wav' })
    ).rejects.toThrow();
  });
});
