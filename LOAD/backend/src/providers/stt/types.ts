export interface STTOptions {
  model?: string;
  language?: string;
}

export interface STTStream {
  write(chunk: Buffer): void;
  end(): Promise<string>;
  destroy(): void;
}

export interface STTProvider {
  readonly name: string;
  transcribe(audioBuffer: Buffer, options?: STTOptions): Promise<string>;
}
