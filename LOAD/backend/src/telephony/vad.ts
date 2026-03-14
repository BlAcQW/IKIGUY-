/**
 * Energy-based Voice Activity Detection (VAD).
 *
 * Detects speech presence in PCM 16-bit LE audio by computing RMS energy
 * per chunk and comparing against a dB threshold. Tracks silence duration
 * after speech to determine when a speaker has finished talking.
 *
 * Used by the call-bridge to detect end-of-speech before sending audio
 * to the voice pipeline.
 */

/** Configuration options for the SimpleVAD detector. */
export interface VADOptions {
  /**
   * Duration of consecutive silence (in ms) after speech that triggers
   * a `speechComplete` signal. Defaults to 800ms.
   */
  silenceThresholdMs: number;

  /**
   * Minimum dB level to consider a chunk as speech.
   * Typical range: -45 (very sensitive) to -25 (less sensitive).
   * Defaults to -35 dB.
   */
  speechThresholdDb: number;

  /** Sample rate of the incoming audio in Hz. Defaults to 16000. */
  sampleRate: number;
}

/** Result returned by `processChunk` for each audio chunk. */
export interface VADResult {
  /** Whether the current chunk contains speech energy above the threshold. */
  isSpeech: boolean;

  /**
   * Whether speech has completed — i.e. speech was detected previously
   * and silence has persisted for at least `silenceThresholdMs`.
   */
  speechComplete: boolean;
}

const DEFAULT_OPTIONS: VADOptions = {
  silenceThresholdMs: 800,
  speechThresholdDb: -35,
  sampleRate: 16000,
};

/**
 * Simple energy-based Voice Activity Detector.
 *
 * Processes PCM 16-bit LE audio chunks and detects when a speaker
 * has finished talking based on silence duration after speech.
 *
 * @example
 * ```ts
 * const vad = new SimpleVAD({ silenceThresholdMs: 1000 });
 *
 * ws.on('message', (audioChunk: Buffer) => {
 *   const { isSpeech, speechComplete } = vad.processChunk(audioChunk);
 *   if (speechComplete) {
 *     // Speaker finished — send accumulated audio to pipeline
 *     vad.reset();
 *   }
 * });
 * ```
 */
export class SimpleVAD {
  private readonly options: VADOptions;
  private speechDetected: boolean;
  private silenceDurationMs: number;

  constructor(options?: Partial<VADOptions>) {
    this.options = { ...DEFAULT_OPTIONS, ...options };
    this.speechDetected = false;
    this.silenceDurationMs = 0;
  }

  /**
   * Process a single PCM 16-bit LE audio chunk.
   *
   * Computes the RMS energy of the chunk, converts to dB, and updates
   * internal speech/silence tracking state.
   *
   * @param chunk - Buffer containing PCM 16-bit LE audio samples.
   * @returns VADResult indicating speech presence and completion.
   */
  processChunk(chunk: Buffer): VADResult {
    const energyDb = computeEnergyDb(chunk);
    const isSpeech = energyDb > this.options.speechThresholdDb;
    const chunkDurationMs = computeChunkDurationMs(
      chunk,
      this.options.sampleRate,
    );

    if (isSpeech) {
      // Speech detected — reset silence counter, mark speech as started
      return this.handleSpeechChunk();
    }

    // Silence chunk
    return this.handleSilenceChunk(chunkDurationMs);
  }

  /**
   * Reset all internal state.
   * Call this after handling a `speechComplete` event to begin
   * detecting the next utterance.
   */
  reset(): void {
    this.speechDetected = false;
    this.silenceDurationMs = 0;
  }

  /** Handle a chunk that contains speech energy. */
  private handleSpeechChunk(): VADResult {
    this.speechDetected = true;
    this.silenceDurationMs = 0;
    return { isSpeech: true, speechComplete: false };
  }

  /** Handle a chunk that falls below the speech energy threshold. */
  private handleSilenceChunk(chunkDurationMs: number): VADResult {
    if (!this.speechDetected) {
      // No speech has been detected yet — nothing to complete
      return { isSpeech: false, speechComplete: false };
    }

    const updatedSilenceDuration = this.silenceDurationMs + chunkDurationMs;
    this.silenceDurationMs = updatedSilenceDuration;

    const speechComplete =
      updatedSilenceDuration >= this.options.silenceThresholdMs;

    return { isSpeech: false, speechComplete };
  }
}

/**
 * Compute the RMS energy of a PCM 16-bit LE audio buffer in decibels.
 *
 * @param chunk - Buffer of PCM 16-bit little-endian samples.
 * @returns Energy level in dB (relative to full scale). Returns -Infinity
 *          for silent/empty buffers.
 */
function computeEnergyDb(chunk: Buffer): number {
  const sampleCount = Math.floor(chunk.length / 2);
  if (sampleCount === 0) {
    return -Infinity;
  }

  let sumOfSquares = 0;
  for (let i = 0; i < sampleCount; i++) {
    const sample = chunk.readInt16LE(i * 2);
    sumOfSquares += sample * sample;
  }

  const rms = Math.sqrt(sumOfSquares / sampleCount);
  if (rms === 0) {
    return -Infinity;
  }

  return 20 * Math.log10(rms / 32768);
}

/**
 * Compute the duration of a PCM 16-bit LE audio chunk in milliseconds.
 *
 * @param chunk - Buffer of PCM 16-bit little-endian samples.
 * @param sampleRate - Sample rate in Hz.
 * @returns Duration in milliseconds.
 */
function computeChunkDurationMs(chunk: Buffer, sampleRate: number): number {
  const sampleCount = Math.floor(chunk.length / 2);
  return (sampleCount / sampleRate) * 1000;
}
