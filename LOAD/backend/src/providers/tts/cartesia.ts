import type { TTSProvider, TTSOptions } from './types.js';

// Cartesia Sonic default voice — "Barbershop Man" (warm male voice)
const DEFAULT_VOICE_ID = 'a0e99841-438c-4a64-b679-ae501e7d6091';

export class CartesiaTTSProvider implements TTSProvider {
  readonly name = 'cartesia';
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async synthesize(text: string, options?: TTSOptions): Promise<Buffer> {
    const voiceId = options?.voiceId ?? DEFAULT_VOICE_ID;
    const speed = options?.speed ?? 1.0;

    const response = await fetch('https://api.cartesia.ai/tts/bytes', {
      method: 'POST',
      headers: {
        'X-API-Key': this.apiKey,
        'Cartesia-Version': '2024-06-10',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model_id: 'sonic-2',
        transcript: text,
        voice: {
          mode: 'id',
          id: voiceId,
        },
        output_format: {
          container: 'raw',
          encoding: 'pcm_s16le',
          sample_rate: 16000,
        },
        language: 'en',
        ...(speed !== 1.0 && {
          voice_controls: { speed: speed > 1 ? 'fast' : speed < 1 ? 'slow' : 'normal' },
        }),
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Cartesia TTS request failed (${response.status}): ${errorText}`);
    }

    const arrayBuffer = await response.arrayBuffer();
    return Buffer.from(arrayBuffer);
  }
}
