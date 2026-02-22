/**
 * WebSocket audio stream handler.
 * Manages bidirectional audio streaming for web-based calls.
 * Full implementation in Phase 2.
 */

export interface AudioStreamConfig {
  sampleRate: number;
  channels: number;
  bitDepth: number;
}

export const DEFAULT_INPUT_CONFIG: AudioStreamConfig = {
  sampleRate: 16000,
  channels: 1,
  bitDepth: 16,
};

export const DEFAULT_OUTPUT_CONFIG: AudioStreamConfig = {
  sampleRate: 24000,
  channels: 1,
  bitDepth: 16,
};

export class AudioBuffer {
  private chunks: Buffer[] = [];

  append(chunk: Buffer): void {
    this.chunks = [...this.chunks, chunk];
  }

  flush(): Buffer {
    const combined = Buffer.concat(this.chunks);
    this.chunks = [];
    return combined;
  }

  get size(): number {
    return this.chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  }

  clear(): void {
    this.chunks = [];
  }
}
