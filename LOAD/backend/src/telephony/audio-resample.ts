/**
 * Audio resampling utilities for PCM 16-bit LE audio.
 *
 * Provides pure functions for converting audio between sample rates using
 * linear interpolation. Common use case: downsampling 24kHz TTS output
 * to 16kHz for Asterisk ExternalMedia (slin16 format).
 *
 * All functions are pure — input buffers are never mutated.
 */

/**
 * Resample PCM 16-bit LE audio from one sample rate to another
 * using linear interpolation.
 *
 * Works for both upsampling and downsampling. Produces a new Buffer
 * without modifying the input.
 *
 * @param input - Source buffer containing PCM 16-bit LE audio samples.
 * @param fromRate - Sample rate of the input audio in Hz (e.g. 24000).
 * @param toRate - Desired output sample rate in Hz (e.g. 16000).
 * @returns A new Buffer containing the resampled PCM 16-bit LE audio.
 * @throws {Error} If sample rates are not positive integers or input is empty.
 *
 * @example
 * ```ts
 * // Downsample 24kHz TTS output to 16kHz for Asterisk
 * const asteriskAudio = resample(ttsOutput, 24000, 16000);
 * ```
 */
export function resample(
  input: Buffer,
  fromRate: number,
  toRate: number,
): Buffer {
  validateRates(fromRate, toRate);

  const inputSampleCount = Math.floor(input.length / 2);
  if (inputSampleCount === 0) {
    return Buffer.alloc(0);
  }

  // Same rate — return a copy (never return the original to preserve immutability)
  if (fromRate === toRate) {
    return Buffer.from(input);
  }

  const ratio = fromRate / toRate;
  const outputSampleCount = Math.floor(inputSampleCount / ratio);
  const output = Buffer.alloc(outputSampleCount * 2);

  for (let i = 0; i < outputSampleCount; i++) {
    const srcPosition = i * ratio;
    const srcIndex = Math.floor(srcPosition);
    const fraction = srcPosition - srcIndex;

    const sample = interpolateSample(input, inputSampleCount, srcIndex, fraction);
    output.writeInt16LE(sample, i * 2);
  }

  return output;
}

/**
 * Downsample PCM 16-bit LE audio from a higher sample rate to a lower one.
 *
 * Convenience wrapper around {@link resample} for the common case of
 * converting TTS output (typically 24kHz) to a telephony format (16kHz or 8kHz).
 *
 * @param input - Source buffer containing PCM 16-bit LE audio samples.
 * @param fromRate - Sample rate of the input audio in Hz. Must be >= toRate.
 * @param toRate - Desired output sample rate in Hz. Must be <= fromRate.
 * @returns A new Buffer containing the downsampled PCM 16-bit LE audio.
 * @throws {Error} If toRate > fromRate.
 *
 * @example
 * ```ts
 * // 24kHz OpenAI TTS → 16kHz Asterisk slin16
 * const slin16 = downsample(ttsBuffer, 24000, 16000);
 * ```
 */
export function downsample(
  input: Buffer,
  fromRate: number,
  toRate: number,
): Buffer {
  if (toRate > fromRate) {
    throw new Error(
      `downsample requires toRate (${toRate}) <= fromRate (${fromRate}). ` +
        'Use upsample() for increasing sample rate.',
    );
  }
  return resample(input, fromRate, toRate);
}

/**
 * Upsample PCM 16-bit LE audio from a lower sample rate to a higher one.
 *
 * Convenience wrapper around {@link resample} for the case of increasing
 * the sample rate (e.g. upsampling 8kHz telephony audio to 16kHz for STT).
 *
 * @param input - Source buffer containing PCM 16-bit LE audio samples.
 * @param fromRate - Sample rate of the input audio in Hz. Must be <= toRate.
 * @param toRate - Desired output sample rate in Hz. Must be >= fromRate.
 * @returns A new Buffer containing the upsampled PCM 16-bit LE audio.
 * @throws {Error} If fromRate > toRate.
 *
 * @example
 * ```ts
 * // 8kHz telephony → 16kHz for STT engine
 * const wideband = upsample(narrowbandBuffer, 8000, 16000);
 * ```
 */
export function upsample(
  input: Buffer,
  fromRate: number,
  toRate: number,
): Buffer {
  if (fromRate > toRate) {
    throw new Error(
      `upsample requires fromRate (${fromRate}) <= toRate (${toRate}). ` +
        'Use downsample() for decreasing sample rate.',
    );
  }
  return resample(input, fromRate, toRate);
}

/**
 * Validate that sample rates are positive integers.
 *
 * @param fromRate - Source sample rate.
 * @param toRate - Target sample rate.
 * @throws {Error} If either rate is not a positive integer.
 */
function validateRates(fromRate: number, toRate: number): void {
  if (!Number.isInteger(fromRate) || fromRate <= 0) {
    throw new Error(`fromRate must be a positive integer, got ${fromRate}`);
  }
  if (!Number.isInteger(toRate) || toRate <= 0) {
    throw new Error(`toRate must be a positive integer, got ${toRate}`);
  }
}

/**
 * Perform linear interpolation between two adjacent samples.
 *
 * @param input - Source buffer of PCM 16-bit LE samples.
 * @param sampleCount - Total number of samples in the input buffer.
 * @param index - Integer index of the left sample.
 * @param fraction - Fractional distance to the next sample (0.0 to 1.0).
 * @returns The interpolated sample value, clamped to int16 range.
 */
function interpolateSample(
  input: Buffer,
  sampleCount: number,
  index: number,
  fraction: number,
): number {
  const currentSample = input.readInt16LE(index * 2);

  // If we're at or beyond the last sample, no interpolation needed
  if (index + 1 >= sampleCount) {
    return currentSample;
  }

  const nextSample = input.readInt16LE((index + 1) * 2);
  const interpolated = currentSample + fraction * (nextSample - currentSample);

  // Clamp to 16-bit signed integer range
  return Math.max(-32768, Math.min(32767, Math.round(interpolated)));
}
