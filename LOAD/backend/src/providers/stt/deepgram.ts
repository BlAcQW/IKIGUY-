import type { STTProvider, STTOptions } from './types.js';

interface DeepgramResponse {
  results: {
    channels: Array<{
      alternatives: Array<{
        transcript: string;
      }>;
    }>;
  };
}

export class DeepgramSTTProvider implements STTProvider {
  readonly name = 'deepgram-nova';
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async transcribe(audioBuffer: Buffer, options?: STTOptions): Promise<string> {
    const model = options?.model ?? 'nova-2';
    const language = options?.language ?? 'en';
    const format = options?.format ?? 'wav';

    // Map audio format to MIME type — Deepgram auto-detects but correct
    // Content-Type avoids transcription failures for non-WAV formats.
    const mimeMap: Record<string, string> = {
      wav: 'audio/wav',
      webm: 'audio/webm',
      mp3: 'audio/mpeg',
      ogg: 'audio/ogg',
    };
    const contentType = mimeMap[format] ?? 'audio/wav';

    const params = new URLSearchParams({ model, language });
    const url = `https://api.deepgram.com/v1/listen?${params.toString()}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Token ${this.apiKey}`,
        'Content-Type': contentType,
      },
      body: audioBuffer.buffer.slice(
        audioBuffer.byteOffset,
        audioBuffer.byteOffset + audioBuffer.byteLength,
      ) as BodyInit,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Deepgram STT request failed (${response.status}): ${errorText}`);
    }

    const data = (await response.json()) as DeepgramResponse;
    const transcript = data.results?.channels?.[0]?.alternatives?.[0]?.transcript ?? '';

    return transcript;
  }
}
