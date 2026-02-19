/**
 * Shared Audio Processing Service for Real-Time Voice Chat
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
   */
  async initialize(): Promise<AudioContext> {
    if (!this.audioContext) {
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

    this.writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    this.writeString(view, 8, 'WAVE');
    this.writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    this.writeString(view, 36, 'data');
    view.setUint32(40, samples.length * 2, true);

    const offset = 44;
    for (let i = 0; i < samples.length; i++) {
      const sample = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(offset + i * 2, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
    }

    return new Blob([buffer], { type: 'audio/wav' });
  }

  private writeString(view: DataView, offset: number, string: string): void {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  /**
   * Process audio buffer and convert to base64 WAV
   */
  async processAudioBuffer(audioBuffer: AudioBuffer): Promise<ProcessedAudio> {
    const pcmData = audioBuffer.getChannelData(0);
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
   * Get microphone stream with optimal settings for voice chat
   */
  async getMicrophoneStream(): Promise<MediaStream> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1
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

    const source = audioContext.createMediaStreamSource(stream);
    const processorBufferSize = 4096;
    const targetSamplesPerChunk = Math.floor((audioContext.sampleRate * chunkDurationMs) / 1000);

    const processor = audioContext.createScriptProcessor(processorBufferSize, 1, 1);

    let accumulatedData: Float32Array[] = [];
    let accumulatedSamples = 0;

    processor.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0);
      accumulatedData.push(new Float32Array(inputData));
      accumulatedSamples += inputData.length;

      if (accumulatedSamples >= targetSamplesPerChunk) {
        const merged = new Float32Array(accumulatedSamples);
        let offset = 0;
        for (const chunk of accumulatedData) {
          merged.set(chunk, offset);
          offset += chunk.length;
        }

        const resampled = this.resamplePCM(merged, audioContext.sampleRate, 16000);
        onAudioData(resampled, 16000);

        accumulatedData = [];
        accumulatedSamples = 0;
      }
    };

    source.connect(processor);
    processor.connect(audioContext.destination);
    this.scriptProcessor = processor;

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
  async cleanup(): Promise<void> {
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
