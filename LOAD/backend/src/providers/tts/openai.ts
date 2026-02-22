import OpenAI from 'openai';
import type { TTSProvider, TTSOptions } from './types.js';

type OpenAIVoice = 'alloy' | 'echo' | 'fable' | 'onyx' | 'nova' | 'shimmer';

export class OpenAITTSProvider implements TTSProvider {
  readonly name = 'openai-tts';
  private client: OpenAI;

  constructor(apiKey: string) {
    this.client = new OpenAI({ apiKey });
  }

  async synthesize(text: string, options?: TTSOptions): Promise<Buffer> {
    const response = await this.client.audio.speech.create({
      model: options?.model ?? 'tts-1',
      voice: (options?.voiceId as OpenAIVoice) ?? 'alloy',
      input: text,
      speed: options?.speed ?? 1.0,
      response_format: 'pcm',
    });

    const arrayBuffer = await response.arrayBuffer();
    return Buffer.from(arrayBuffer);
  }
}
