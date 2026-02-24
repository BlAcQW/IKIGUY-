import type { TTSProvider, TTSOptions } from './types.js';

const DEFAULT_VOICE = 'aura-asteria-en';

export class DeepgramTTSProvider implements TTSProvider {
  readonly name = 'deepgram';
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async synthesize(text: string, options?: TTSOptions): Promise<Buffer> {
    const model = options?.voiceId ?? DEFAULT_VOICE;

    const url = new URL('https://api.deepgram.com/v1/speak');
    url.searchParams.set('model', model);
    url.searchParams.set('encoding', 'linear16');
    url.searchParams.set('sample_rate', '16000');

    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        Authorization: `Token ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Deepgram TTS request failed (${response.status}): ${errorText}`);
    }

    const arrayBuffer = await response.arrayBuffer();
    return Buffer.from(arrayBuffer);
  }
}
