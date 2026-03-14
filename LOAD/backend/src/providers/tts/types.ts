export interface TTSOptions {
  voiceId?: string;
  speed?: number;
  model?: string;
}

export interface TTSProvider {
  readonly name: string;
  synthesize(text: string, options?: TTSOptions): Promise<Buffer>;
}
