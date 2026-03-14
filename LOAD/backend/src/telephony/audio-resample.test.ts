import { describe, it, expect } from 'vitest';
import { resample, downsample, upsample } from './audio-resample.js';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Create a PCM 16-bit LE buffer with incrementing sample values. */
function createTestBuffer(samples: number, startValue: number = 1000): Buffer {
  const buf = Buffer.alloc(samples * 2);
  for (let i = 0; i < samples; i++) {
    const value = Math.min(32767, startValue + i);
    buf.writeInt16LE(value, i * 2);
  }
  return buf;
}

// ---------------------------------------------------------------------------
// resample
// ---------------------------------------------------------------------------

describe('resample', () => {
  it('returns empty buffer for empty input', () => {
    const result = resample(Buffer.alloc(0), 24000, 16000);

    expect(result.length).toBe(0);
  });

  it('returns a copy for same rate', () => {
    const input = createTestBuffer(100);

    const result = resample(input, 16000, 16000);

    // Should be a different buffer reference (immutability)
    expect(result).not.toBe(input);
    // But same content
    expect(result.equals(input)).toBe(true);
  });

  it('downsamples 24kHz to 16kHz correctly', () => {
    const inputSamples = 2400; // 100ms at 24kHz
    const input = createTestBuffer(inputSamples);

    const result = resample(input, 24000, 16000);

    // Expected output samples: floor(2400 * 16000/24000) = floor(1600) = 1600
    const expectedOutputSamples = Math.floor(inputSamples * 16000 / 24000);
    expect(result.length / 2).toBe(expectedOutputSamples);
  });

  it('upsamples 16kHz to 24kHz correctly', () => {
    const inputSamples = 1600; // 100ms at 16kHz
    const input = createTestBuffer(inputSamples);

    const result = resample(input, 16000, 24000);

    // Expected output samples: floor(1600 * 24000/16000) = floor(2400) = 2400
    const expectedOutputSamples = Math.floor(inputSamples * 24000 / 16000);
    expect(result.length / 2).toBe(expectedOutputSamples);
  });

  it('throws on invalid rates - zero', () => {
    const input = createTestBuffer(100);

    expect(() => resample(input, 0, 16000)).toThrow('positive integer');
    expect(() => resample(input, 16000, 0)).toThrow('positive integer');
  });

  it('throws on invalid rates - negative', () => {
    const input = createTestBuffer(100);

    expect(() => resample(input, -8000, 16000)).toThrow('positive integer');
    expect(() => resample(input, 16000, -8000)).toThrow('positive integer');
  });

  it('throws on invalid rates - non-integer', () => {
    const input = createTestBuffer(100);

    expect(() => resample(input, 16000.5, 8000)).toThrow('positive integer');
    expect(() => resample(input, 16000, 8000.5)).toThrow('positive integer');
  });

  it('preserves audio characteristics', () => {
    const inputSamples = 2400;
    const amplitude = 5000;
    const input = Buffer.alloc(inputSamples * 2);
    for (let i = 0; i < inputSamples; i++) {
      input.writeInt16LE(amplitude, i * 2);
    }

    const result = resample(input, 24000, 16000);
    const outputSamples = result.length / 2;

    // First and last output samples should be close to the constant amplitude
    const firstSample = result.readInt16LE(0);
    const lastSample = result.readInt16LE((outputSamples - 1) * 2);

    expect(firstSample).toBe(amplitude);
    expect(lastSample).toBe(amplitude);
  });
});

// ---------------------------------------------------------------------------
// downsample
// ---------------------------------------------------------------------------

describe('downsample', () => {
  it('downsamples successfully when toRate < fromRate', () => {
    const input = createTestBuffer(2400);

    const result = downsample(input, 24000, 16000);

    expect(result.length / 2).toBe(Math.floor(2400 * 16000 / 24000));
  });

  it('throws if toRate > fromRate', () => {
    const input = createTestBuffer(100);

    expect(() => downsample(input, 16000, 24000)).toThrow(
      'downsample requires toRate'
    );
  });

  it('allows same rate (toRate === fromRate)', () => {
    const input = createTestBuffer(100);

    const result = downsample(input, 16000, 16000);

    expect(result.equals(input)).toBe(true);
    expect(result).not.toBe(input);
  });
});

// ---------------------------------------------------------------------------
// upsample
// ---------------------------------------------------------------------------

describe('upsample', () => {
  it('upsamples successfully when toRate > fromRate', () => {
    const input = createTestBuffer(1600);

    const result = upsample(input, 16000, 24000);

    expect(result.length / 2).toBe(Math.floor(1600 * 24000 / 16000));
  });

  it('throws if fromRate > toRate', () => {
    const input = createTestBuffer(100);

    expect(() => upsample(input, 24000, 16000)).toThrow(
      'upsample requires fromRate'
    );
  });

  it('allows same rate (fromRate === toRate)', () => {
    const input = createTestBuffer(100);

    const result = upsample(input, 16000, 16000);

    expect(result.equals(input)).toBe(true);
    expect(result).not.toBe(input);
  });
});
