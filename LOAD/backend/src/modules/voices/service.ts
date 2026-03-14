import { config } from '../../config/index.js';

export interface CustomVoice {
  voiceId: string;
  name: string;
  provider: string;
  category: string;
  labels: Record<string, string>;
  previewUrl?: string;
}

/**
 * List all voices from ElevenLabs (built-in + custom clones).
 */
export async function listElevenLabsVoices(): Promise<CustomVoice[]> {
  if (!config.ELEVENLABS_API_KEY) {
    throw Object.assign(new Error('ELEVENLABS_API_KEY is required'), { statusCode: 503 });
  }

  const response = await fetch('https://api.elevenlabs.io/v1/voices', {
    headers: { 'xi-api-key': config.ELEVENLABS_API_KEY },
  });

  if (!response.ok) {
    const text = await response.text();
    throw Object.assign(
      new Error(`ElevenLabs API error (${response.status}): ${text}`),
      { statusCode: response.status >= 500 ? 502 : response.status },
    );
  }

  const data = await response.json() as {
    voices: Array<{
      voice_id: string;
      name: string;
      category: string;
      labels: Record<string, string>;
      preview_url?: string;
    }>;
  };

  return data.voices.map((v) => ({
    voiceId: v.voice_id,
    name: v.name,
    provider: 'elevenlabs',
    category: v.category,
    labels: v.labels ?? {},
    previewUrl: v.preview_url,
  }));
}

/**
 * Clone a voice using ElevenLabs Instant Voice Cloning.
 * Accepts a buffer of audio data + name.
 */
export async function cloneVoice(
  name: string,
  description: string,
  audioBuffer: Buffer,
  audioFilename: string,
): Promise<CustomVoice> {
  if (!config.ELEVENLABS_API_KEY) {
    throw Object.assign(new Error('ELEVENLABS_API_KEY is required'), { statusCode: 503 });
  }

  const formData = new FormData();
  formData.append('name', name);
  formData.append('description', description || `Custom voice clone: ${name}`);
  formData.append('labels', JSON.stringify({ source: 'load-platform' }));
  formData.append('remove_background_noise', 'true');

  // Create a Blob from the buffer for FormData
  const blob = new Blob([new Uint8Array(audioBuffer)], { type: 'audio/mpeg' });
  formData.append('files', blob, audioFilename);

  const response = await fetch('https://api.elevenlabs.io/v1/voices/add', {
    method: 'POST',
    headers: {
      'xi-api-key': config.ELEVENLABS_API_KEY,
    },
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw Object.assign(
      new Error(`Voice cloning failed (${response.status}): ${text}`),
      { statusCode: response.status >= 500 ? 502 : 400 },
    );
  }

  const data = await response.json() as { voice_id: string };

  return {
    voiceId: data.voice_id,
    name,
    provider: 'elevenlabs',
    category: 'cloned',
    labels: { source: 'load-platform' },
  };
}

/**
 * Delete a cloned voice from ElevenLabs.
 */
export async function deleteClonedVoice(voiceId: string): Promise<void> {
  if (!config.ELEVENLABS_API_KEY) {
    throw Object.assign(new Error('ELEVENLABS_API_KEY is required'), { statusCode: 503 });
  }

  const response = await fetch(`https://api.elevenlabs.io/v1/voices/${voiceId}`, {
    method: 'DELETE',
    headers: { 'xi-api-key': config.ELEVENLABS_API_KEY },
  });

  if (!response.ok) {
    const text = await response.text();
    throw Object.assign(
      new Error(`Failed to delete voice (${response.status}): ${text}`),
      { statusCode: response.status >= 500 ? 502 : response.status },
    );
  }
}

/**
 * Generate a short TTS preview of a voice.
 */
export async function previewVoice(
  provider: string,
  voiceId: string,
  text = 'Hello! This is a preview of how I sound.',
): Promise<Buffer> {
  if (provider === 'elevenlabs') {
    if (!config.ELEVENLABS_API_KEY) {
      throw Object.assign(new Error('ELEVENLABS_API_KEY is required'), { statusCode: 503 });
    }

    const response = await fetch(
      `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}?output_format=mp3_44100_128`,
      {
        method: 'POST',
        headers: {
          'xi-api-key': config.ELEVENLABS_API_KEY,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text, model_id: 'eleven_monolingual_v1' }),
      },
    );

    if (!response.ok) {
      const errorText = await response.text();
      throw Object.assign(
        new Error(`Voice preview failed (${response.status}): ${errorText}`),
        { statusCode: 502 },
      );
    }

    return Buffer.from(await response.arrayBuffer());
  }

  if (provider === 'deepgram') {
    if (!config.DEEPGRAM_API_KEY) {
      throw Object.assign(new Error('DEEPGRAM_API_KEY is required'), { statusCode: 503 });
    }

    const url = new URL('https://api.deepgram.com/v1/speak');
    url.searchParams.set('model', voiceId);
    url.searchParams.set('encoding', 'mp3');

    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        Authorization: `Token ${config.DEEPGRAM_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw Object.assign(
        new Error(`Deepgram preview failed (${response.status}): ${errorText}`),
        { statusCode: 502 },
      );
    }

    return Buffer.from(await response.arrayBuffer());
  }

  if (provider === 'cartesia') {
    if (!config.CARTESIA_API_KEY) {
      throw Object.assign(new Error('CARTESIA_API_KEY is required'), { statusCode: 503 });
    }

    const response = await fetch('https://api.cartesia.ai/tts/bytes', {
      method: 'POST',
      headers: {
        'X-API-Key': config.CARTESIA_API_KEY,
        'Cartesia-Version': '2024-06-10',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model_id: 'sonic-2',
        transcript: text,
        voice: { mode: 'id', id: voiceId },
        output_format: { container: 'mp3', encoding: 'mp3', sample_rate: 44100 },
        language: 'en',
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw Object.assign(
        new Error(`Cartesia preview failed (${response.status}): ${errorText}`),
        { statusCode: 502 },
      );
    }

    return Buffer.from(await response.arrayBuffer());
  }

  throw Object.assign(new Error(`Preview not supported for provider: ${provider}`), { statusCode: 400 });
}
