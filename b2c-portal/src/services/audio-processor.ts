/**
 * Audio Processing Service for Real-Time Voice Chat
 *
 * Provides utilities for:
 * - Converting browser audio to PCM/WAV format
 * - Streaming audio chunks efficiently
 * - Audio format detection and validation
 */

export interface AudioChunk {
  data: Float32Array;
  sampleRate: number;
  timestamp: number;
}

export interface ProcessedAudio {
  base64: string;
  format: 'wav' | 'pcm';
  sampleRate: number;
  channels: number;
  duration: number;
}

/**
 * Audio Processor for real-time voice chat
 */
export class AudioProcessor {
  private audioContext: AudioContext | null = null;
  private scriptProcessor: ScriptProcessorNode | null = null;
  private mediaStream: MediaStream | null = null;

  /**
   * Initialize audio context with optimal settings
   * Uses browser's native sample rate to avoid compatibility issues
   */
  async initialize(): Promise<AudioContext> {
    if (!this.audioContext) {
      // Don't specify sampleRate - let browser use hardware default
      // This avoids "different sample-rate" errors when connecting MediaStreamSource
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        latencyHint: 'interactive'
      });
      console.log(`[AudioProcessor] AudioContext initialized at ${this.audioContext.sampleRate}Hz`);
    }
    return this.audioContext;
  }

  /**
   * Convert Blob to base64 string
   */
  async blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = (reader.result as string).split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  /**
   * Convert Float32Array PCM data to WAV format
   */
  float32ToWav(samples: Float32Array, sampleRate: number = 16000): Blob {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    // WAV file header
    this.writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    this.writeString(view, 8, 'WAVE');
    this.writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true); // Subchunk1Size
    view.setUint16(20, 1, true); // AudioFormat (PCM)
    view.setUint16(22, 1, true); // NumChannels (mono)
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true); // ByteRate
    view.setUint16(32, 2, true); // BlockAlign
    view.setUint16(34, 16, true); // BitsPerSample
    this.writeString(view, 36, 'data');
    view.setUint32(40, samples.length * 2, true);

    // Convert float samples to 16-bit PCM
    const offset = 44;
    for (let i = 0; i < samples.length; i++) {
      const sample = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(offset + i * 2, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
    }

    return new Blob([buffer], { type: 'audio/wav' });
  }

  /**
   * Write string to DataView for WAV header
   */
  private writeString(view: DataView, offset: number, string: string): void {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  /**
   * Process audio buffer and convert to base64 WAV
   */
  async processAudioBuffer(audioBuffer: AudioBuffer): Promise<ProcessedAudio> {
    // Get PCM data from first channel
    const pcmData = audioBuffer.getChannelData(0);

    // Convert to WAV
    const wavBlob = this.float32ToWav(pcmData, audioBuffer.sampleRate);
    const base64 = await this.blobToBase64(wavBlob);

    return {
      base64,
      format: 'wav',
      sampleRate: audioBuffer.sampleRate,
      channels: audioBuffer.numberOfChannels,
      duration: audioBuffer.duration
    };
  }

  /**
   * Convert WebM Blob to WAV format
   * Decodes WebM audio and re-encodes as PCM WAV
   */
  async webmToWav(webmBlob: Blob): Promise<ProcessedAudio> {
    const audioContext = await this.initialize();

    // Read WebM blob as array buffer
    const arrayBuffer = await webmBlob.arrayBuffer();

    try {
      // Decode audio data - may fail for incomplete chunks
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

      // Process and return WAV
      return this.processAudioBuffer(audioBuffer);
    } catch (error) {
      // If decoding fails (incomplete chunk, invalid format, etc.), throw with context
      const errorMessage = error instanceof Error ? error.message : String(error);
      throw new Error(`Failed to decode WebM audio: ${errorMessage}. Chunk size: ${webmBlob.size} bytes`);
    }
  }

  /**
   * Resample audio to target sample rate
   */
  async resampleAudio(
    audioBuffer: AudioBuffer,
    targetSampleRate: number = 16000
  ): Promise<AudioBuffer> {
    const audioContext = await this.initialize();
    const offlineContext = new OfflineAudioContext(
      audioBuffer.numberOfChannels,
      audioBuffer.duration * targetSampleRate,
      targetSampleRate
    );

    const source = offlineContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(offlineContext.destination);
    source.start();

    return await offlineContext.startRendering();
  }

  /**
   * Get microphone stream with optimal settings for voice chat
   */
  async getMicrophoneStream(): Promise<MediaStream> {
    try {
      // Request microphone without sampleRate constraint
      // Let browser use native hardware rate to avoid compatibility issues
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1
          // Note: sampleRate removed - browser will use hardware default
        }
      });

      this.mediaStream = stream;
      console.log('[AudioProcessor] Microphone stream obtained');
      return stream;
    } catch (error) {
      console.error('[AudioProcessor] Failed to get microphone access:', error);
      throw new Error('Microphone access denied or not available');
    }
  }

  /**
   * Resample Float32Array PCM data to target sample rate
   */
  private resamplePCM(input: Float32Array, inputRate: number, outputRate: number): Float32Array {
    if (inputRate === outputRate) {
      return input;
    }

    const ratio = inputRate / outputRate;
    const outputLength = Math.floor(input.length / ratio);
    const output = new Float32Array(outputLength);

    for (let i = 0; i < outputLength; i++) {
      const srcIndex = i * ratio;
      const srcIndexFloor = Math.floor(srcIndex);
      const srcIndexCeil = Math.min(srcIndexFloor + 1, input.length - 1);
      const fraction = srcIndex - srcIndexFloor;

      // Linear interpolation
      output[i] = input[srcIndexFloor] * (1 - fraction) + input[srcIndexCeil] * fraction;
    }

    return output;
  }

  /**
   * Start streaming raw PCM audio from microphone
   * Returns a callback to stop streaming
   */
  async startPCMStreaming(
    onAudioData: (pcmData: Float32Array, sampleRate: number) => void,
    chunkDurationMs: number = 1000
  ): Promise<() => void> {
    const audioContext = await this.initialize();
    const stream = await this.getMicrophoneStream();

    console.log(`[AudioProcessor] Starting PCM capture at ${audioContext.sampleRate}Hz, will resample to 16kHz`);

    // Create audio source from microphone
    const source = audioContext.createMediaStreamSource(stream);

    // ScriptProcessor requires power-of-2 buffer sizes between 256-16384
    // Use 4096 samples and accumulate to reach desired chunk duration
    const processorBufferSize = 4096;
    const targetSamplesPerChunk = Math.floor((audioContext.sampleRate * chunkDurationMs) / 1000);

    console.log(`[AudioProcessor] Processor buffer: ${processorBufferSize}, target chunk: ${targetSamplesPerChunk} samples`);

    const processor = audioContext.createScriptProcessor(processorBufferSize, 1, 1);

    // Accumulate audio data until we reach target chunk size
    let accumulatedData: Float32Array[] = [];
    let accumulatedSamples = 0;

    processor.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0);

      // Clone and accumulate
      accumulatedData.push(new Float32Array(inputData));
      accumulatedSamples += inputData.length;

      // When we've accumulated enough for desired chunk duration
      if (accumulatedSamples >= targetSamplesPerChunk) {
        // Merge accumulated chunks
        const merged = new Float32Array(accumulatedSamples);
        let offset = 0;
        for (const chunk of accumulatedData) {
          merged.set(chunk, offset);
          offset += chunk.length;
        }

        // Resample to 16kHz for speech recognition (optimal)
        const resampled = this.resamplePCM(merged, audioContext.sampleRate, 16000);

        // Send resampled 16kHz data
        onAudioData(resampled, 16000);

        // Reset accumulator
        accumulatedData = [];
        accumulatedSamples = 0;
      }
    };

    // Connect audio graph
    source.connect(processor);
    processor.connect(audioContext.destination);

    this.scriptProcessor = processor;

    // Return cleanup function
    return () => {
      processor.disconnect();
      source.disconnect();
      this.stopStreams();
    };
  }

  /**
   * Stop all active audio streams
   */
  stopStreams(): void {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }

    if (this.scriptProcessor) {
      this.scriptProcessor.disconnect();
      this.scriptProcessor = null;
    }
  }

  /**
   * Clean up resources
   */
  async cleanup(): void {
    this.stopStreams();

    if (this.audioContext && this.audioContext.state !== 'closed') {
      await this.audioContext.close();
      this.audioContext = null;
    }
  }
}

// Global audio processor instance
let globalAudioProcessor: AudioProcessor | null = null;

/**
 * Get the global audio processor instance
 */
export function getAudioProcessor(): AudioProcessor {
  if (!globalAudioProcessor) {
    globalAudioProcessor = new AudioProcessor();
  }
  return globalAudioProcessor;
}

/**
 * Cleanup global audio processor
 */
export async function cleanupAudioProcessor(): Promise<void> {
  if (globalAudioProcessor) {
    await globalAudioProcessor.cleanup();
    globalAudioProcessor = null;
  }
}