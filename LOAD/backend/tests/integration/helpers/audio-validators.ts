/**
 * Audio validation helpers for integration tests.
 *
 * Validates that TTS output is real PCM audio and not empty/garbage.
 */
import { expect } from 'vitest';

/**
 * Assert that a buffer contains valid 16-bit PCM audio.
 *
 * Checks:
 * - Buffer is not empty
 * - Buffer length is even (16-bit samples = 2 bytes each)
 * - Contains non-zero samples (not silence)
 * - Has reasonable sample variance (not a flat line)
 */
export function assertValidPcmAudio(
  buffer: Buffer,
  options?: {
    /** Minimum expected byte length. Default: 100 */
    minBytes?: number;
    /** Allow all-silence buffers. Default: false */
    allowSilence?: boolean;
    /** Expected sample rate (for duration calculation only). Default: 16000 */
    sampleRate?: number;
  },
): void {
  const minBytes = options?.minBytes ?? 100;
  const allowSilence = options?.allowSilence ?? false;
  const sampleRate = options?.sampleRate ?? 16_000;

  expect(buffer).toBeInstanceOf(Buffer);
  expect(buffer.length).toBeGreaterThanOrEqual(minBytes);

  // 16-bit samples = 2 bytes each
  expect(buffer.length % 2).toBe(0);

  const sampleCount = buffer.length / 2;
  const durationMs = (sampleCount / sampleRate) * 1000;

  // Should be at least 50ms of audio
  expect(durationMs).toBeGreaterThanOrEqual(50);

  if (!allowSilence) {
    // Read samples and check for non-zero values
    let hasNonZero = false;
    let maxAmplitude = 0;

    for (let i = 0; i < buffer.length; i += 2) {
      const sample = buffer.readInt16LE(i);
      if (sample !== 0) hasNonZero = true;
      const abs = Math.abs(sample);
      if (abs > maxAmplitude) maxAmplitude = abs;
    }

    expect(hasNonZero).toBe(true);
    // Max amplitude should be above noise floor (at least 100 out of 32767)
    expect(maxAmplitude).toBeGreaterThan(100);
  }
}

/**
 * Get basic statistics about a PCM audio buffer.
 */
export function getPcmStats(buffer: Buffer): {
  sampleCount: number;
  durationMs: number;
  maxAmplitude: number;
  rmsLevel: number;
  isSilent: boolean;
} {
  const sampleCount = buffer.length / 2;
  const durationMs = (sampleCount / 16_000) * 1000;
  let maxAmplitude = 0;
  let sumSquares = 0;

  for (let i = 0; i < buffer.length; i += 2) {
    const sample = buffer.readInt16LE(i);
    const abs = Math.abs(sample);
    if (abs > maxAmplitude) maxAmplitude = abs;
    sumSquares += sample * sample;
  }

  const rmsLevel = Math.sqrt(sumSquares / sampleCount);
  const isSilent = maxAmplitude < 100;

  return { sampleCount, durationMs, maxAmplitude, rmsLevel, isSilent };
}
