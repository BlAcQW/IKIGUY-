import type { TTSProvider, TTSOptions } from './types.js';

const DEFAULT_VOICE_ID = '21m00Tcm4TlvDq8ikWAM'; // Rachel

export class ElevenLabsTTSProvider implements TTSProvider {
  readonly name = 'elevenlabs';
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async synthesize(text: string, options?: TTSOptions): Promise<Buffer> {
    const voiceId = options?.voiceId ?? DEFAULT_VOICE_ID;
    const model = options?.model ?? 'eleven_turbo_v2_5';

    const params = new URLSearchParams({ output_format: 'pcm_16000' });
    const url = `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}?${params.toString()}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'xi-api-key': this.apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        model_id: model,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`ElevenLabs TTS request failed (${response.status}): ${errorText}`);
    }

    const arrayBuffer = await response.arrayBuffer();
    return Buffer.from(arrayBuffer);
  }
}
