import OpenAI, { toFile } from 'openai';
import type { STTProvider, STTOptions } from './types.js';

export class OpenAISTTProvider implements STTProvider {
  readonly name = 'openai-whisper';
  private client: OpenAI;

  constructor(apiKey: string) {
    this.client = new OpenAI({ apiKey });
  }

  async transcribe(audioBuffer: Buffer, options?: STTOptions): Promise<string> {
    const format = options?.format ?? 'webm';
    const mimeTypes: Record<string, string> = {
      webm: 'audio/webm',
      wav: 'audio/wav',
      mp3: 'audio/mpeg',
      ogg: 'audio/ogg',
      mp4: 'audio/mp4',
    };
    const mime = mimeTypes[format] ?? `audio/${format}`;
    const file = await toFile(audioBuffer, `audio.${format}`, { type: mime });
    const response = await this.client.audio.transcriptions.create({
      model: options?.model ?? 'whisper-1',
      file,
      language: options?.language ?? 'en',
    });
    return response.text;
  }
}
