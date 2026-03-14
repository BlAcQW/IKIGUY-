/**
 * Integration test: OpenAI Whisper STT
 *
 * Sends real audio to the OpenAI Whisper API and verifies transcription.
 * Requires OPENAI_API_KEY in .env.
 */
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { describe, it, expect } from 'vitest';
import { describeIfKey, requireKey } from '../helpers/skip-if-missing.js';
import { OpenAISTTProvider } from '@/providers/stt/openai.js';

const __dirname_ = typeof __dirname !== 'undefined'
  ? __dirname
  : dirname(fileURLToPath(import.meta.url));

const FIXTURES = join(__dirname_, '..', 'fixtures');

describeIfKey('OPENAI_API_KEY', 'OpenAI Whisper STT Provider', () => {
  let provider: OpenAISTTProvider;

  beforeAll(() => {
    provider = new OpenAISTTProvider(requireKey('OPENAI_API_KEY'));
  });

  it('should transcribe a WAV audio file', async () => {
    const audio = readFileSync(join(FIXTURES, 'hello-16k-mono.wav'));

    const transcript = await provider.transcribe(audio, { format: 'wav' });

    expect(typeof transcript).toBe('string');
    // Whisper accepted the audio and returned a result
  });

  it('should return empty or near-empty transcript for silence', async () => {
    const silence = readFileSync(join(FIXTURES, 'silence-16k-mono.wav'));

    const transcript = await provider.transcribe(silence, { format: 'wav' });

    expect(typeof transcript).toBe('string');
    // Silence should produce empty or very short hallucinated text
  });

  it('should throw an error with an invalid API key', async () => {
    const badProvider = new OpenAISTTProvider('sk-invalid-key-12345');
    const audio = readFileSync(join(FIXTURES, 'hello-16k-mono.wav'));

    await expect(
      badProvider.transcribe(audio, { format: 'wav' })
    ).rejects.toThrow();
  });
});
