import OpenAI, { toFile } from 'openai';
import type { STTProvider, STTOptions } from './types.js';

export class OpenAISTTProvider implements STTProvider {
  readonly name = 'openai-whisper';
  private client: OpenAI;

  constructor(apiKey: string) {
    this.client = new OpenAI({ apiKey });
  }

  async transcribe(audioBuffer: Buffer, options?: STTOptions): Promise<string> {
    const file = await toFile(audioBuffer, 'audio.wav', { type: 'audio/wav' });
    const response = await this.client.audio.transcriptions.create({
      model: options?.model ?? 'whisper-1',
      file,
      language: options?.language ?? 'en',
    });
    return response.text;
  }
}
