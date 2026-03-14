import { describe, it, expect, beforeEach } from 'vitest';
import { SimpleVAD } from './vad.js';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Create a buffer of silent PCM 16-bit LE samples (all zeros). */
function createSilentBuffer(samples: number): Buffer {
  return Buffer.alloc(samples * 2); // 16-bit = 2 bytes per sample
}

/** Create a buffer of loud PCM 16-bit LE samples at the given amplitude. */
function createLoudBuffer(samples: number, amplitude: number = 10000): Buffer {
  const buf = Buffer.alloc(samples * 2);
  for (let i = 0; i < samples; i++) {
    buf.writeInt16LE(amplitude, i * 2);
  }
  return buf;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('SimpleVAD', () => {
  let vad: SimpleVAD;

  beforeEach(() => {
    vad = new SimpleVAD();
  });

  it('returns no speech for empty buffer', () => {
    const result = vad.processChunk(Buffer.alloc(0));

    expect(result.isSpeech).toBe(false);
    expect(result.speechComplete).toBe(false);
  });

  it('returns no speech for silent audio', () => {
    const silent = createSilentBuffer(1600); // 100ms at 16kHz

    const result = vad.processChunk(silent);

    expect(result.isSpeech).toBe(false);
    expect(result.speechComplete).toBe(false);
  });

  it('detects speech in loud audio', () => {
    const loud = createLoudBuffer(1600, 10000);

    const result = vad.processChunk(loud);

    expect(result.isSpeech).toBe(true);
    expect(result.speechComplete).toBe(false);
  });

  it('signals speechComplete after silence following speech', () => {
    const loud = createLoudBuffer(1600, 10000); // 100ms at 16kHz
    // 16000 samples at 16kHz = 1000ms of silence, exceeding 800ms threshold
    const silent = createSilentBuffer(16000);

    // First: detect speech
    const speechResult = vad.processChunk(loud);
    expect(speechResult.isSpeech).toBe(true);

    // Then: enough silence to trigger speechComplete
    const silenceResult = vad.processChunk(silent);
    expect(silenceResult.isSpeech).toBe(false);
    expect(silenceResult.speechComplete).toBe(true);
  });

  it('does not signal speechComplete if no speech was detected', () => {
    // Send only silence -- never any speech beforehand
    const silent = createSilentBuffer(16000); // 1000ms at 16kHz

    const result = vad.processChunk(silent);

    expect(result.isSpeech).toBe(false);
    expect(result.speechComplete).toBe(false);
  });

  it('reset clears state', () => {
    const loud = createLoudBuffer(1600, 10000);
    const silent = createSilentBuffer(8000); // 500ms -- not enough for speechComplete

    // Detect speech, accumulate some silence
    vad.processChunk(loud);
    vad.processChunk(silent);

    // Reset
    vad.reset();

    // After reset, silence should NOT trigger speechComplete because
    // there is no speech history
    const result = vad.processChunk(silent);
    expect(result.isSpeech).toBe(false);
    expect(result.speechComplete).toBe(false);
  });

  it('respects custom silenceThresholdMs', () => {
    // Use a very short silence threshold of 200ms
    const customVad = new SimpleVAD({ silenceThresholdMs: 200 });

    const loud = createLoudBuffer(1600, 10000); // 100ms at 16kHz
    // 3200 samples at 16kHz = 200ms of silence
    const shortSilent = createSilentBuffer(3200);

    customVad.processChunk(loud);
    const result = customVad.processChunk(shortSilent);

    expect(result.speechComplete).toBe(true);
  });

  it('respects custom speechThresholdDb', () => {
    // Use a very high threshold so that moderate amplitude is not considered speech.
    // amplitude=100 has RMS = 100, dB = 20*log10(100/32768) ~ -50.3 dB
    // With a threshold of -20 dB, amplitude=100 should not be speech.
    const strictVad = new SimpleVAD({ speechThresholdDb: -20 });

    const moderateLoud = createLoudBuffer(1600, 100);
    const result = strictVad.processChunk(moderateLoud);

    expect(result.isSpeech).toBe(false);
  });

  it('does not trigger speechComplete before enough silence accumulates', () => {
    const loud = createLoudBuffer(1600, 10000); // 100ms at 16kHz
    // 4800 samples at 16kHz = 300ms of silence -- below 800ms threshold
    const shortSilent = createSilentBuffer(4800);

    vad.processChunk(loud);
    const result = vad.processChunk(shortSilent);

    expect(result.isSpeech).toBe(false);
    expect(result.speechComplete).toBe(false);
  });

  it('accumulates silence across multiple chunks', () => {
    const loud = createLoudBuffer(1600, 10000); // 100ms at 16kHz
    // Each chunk: 4800 samples = 300ms of silence
    const silenceChunk = createSilentBuffer(4800);

    vad.processChunk(loud);

    // 300ms -- not enough
    const r1 = vad.processChunk(silenceChunk);
    expect(r1.speechComplete).toBe(false);

    // 600ms -- still not enough
    const r2 = vad.processChunk(silenceChunk);
    expect(r2.speechComplete).toBe(false);

    // 900ms -- exceeds 800ms threshold
    const r3 = vad.processChunk(silenceChunk);
    expect(r3.speechComplete).toBe(true);
  });
});
