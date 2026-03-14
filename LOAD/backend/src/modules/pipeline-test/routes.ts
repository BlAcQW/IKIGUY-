/**
 * Pipeline test endpoints — TTS, STT, and voice loop testing.
 *
 * POST /api/tts  — Synthesize text to audio (returns audio/wav)
 * POST /api/stt  — Transcribe uploaded audio (returns JSON transcript)
 */

import { FastifyInstance } from 'fastify';
import { authMiddleware } from '../../middleware/auth.js';
import { createSTTProvider, createTTSProvider } from '../../providers/registry.js';
import { prisma } from '../../database/client.js';

// ---------------------------------------------------------------------------
// WAV header helper
// ---------------------------------------------------------------------------

/**
 * Wrap raw PCM data in a WAV header (16-bit, mono).
 */
function wrapPcmAsWav(pcm: Buffer, sampleRate: number): Buffer {
  const header = Buffer.alloc(44);
  const dataSize = pcm.length;
  const fileSize = 36 + dataSize;

  header.write('RIFF', 0);
  header.writeUInt32LE(fileSize, 4);
  header.write('WAVE', 8);
  header.write('fmt ', 12);
  header.writeUInt32LE(16, 16);           // Sub-chunk size (16 for PCM)
  header.writeUInt16LE(1, 20);            // Audio format (1 = PCM)
  header.writeUInt16LE(1, 22);            // Mono
  header.writeUInt32LE(sampleRate, 24);   // Sample rate
  header.writeUInt32LE(sampleRate * 2, 28); // Byte rate (mono 16-bit)
  header.writeUInt16LE(2, 32);            // Block align
  header.writeUInt16LE(16, 34);           // Bits per sample
  header.write('data', 36);
  header.writeUInt32LE(dataSize, 40);

  return Buffer.concat([header, pcm]);
}

/**
 * Resolve the org-level API key override for a provider name.
 */
async function getOrgKeyOverride(
  organizationId: string,
  providerName: string,
): Promise<string | undefined> {
  try {
    const settings = await prisma.organization.findUnique({
      where: { id: organizationId },
      select: { settings: true },
    });

    const s = settings?.settings as Record<string, unknown> | null;
    const creds = s?.providerCredentials as Record<string, string | undefined> | undefined;
    if (!creds) return undefined;

    const keyMap: Record<string, string> = {
      openai: 'openaiApiKey',
      deepgram: 'deepgramApiKey',
      elevenlabs: 'elevenLabsApiKey',
      cartesia: 'cartesiaApiKey',
    };

    return creds[keyMap[providerName] ?? ''] ?? undefined;
  } catch {
    return undefined;
  }
}

// ---------------------------------------------------------------------------
// TTS sample rates by provider
// ---------------------------------------------------------------------------

const TTS_SAMPLE_RATES: Record<string, number> = {
  openai: 24_000,
  elevenlabs: 16_000,
  deepgram: 16_000,
  cartesia: 16_000,
};

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export async function pipelineTestRoutes(app: FastifyInstance): Promise<void> {
  /**
   * POST /api/tts
   *
   * Synthesize text to speech. Returns audio/wav.
   *
   * Body: { text: string, provider?: string, voiceId?: string, speed?: number }
   */
  app.post('/api/tts', {
    preHandler: [authMiddleware],
  }, async (request, reply) => {
    const { text, provider, voiceId, speed } = request.body as {
      text?: string;
      provider?: string;
      voiceId?: string;
      speed?: number;
    };

    if (!text || text.trim().length === 0) {
      return reply.status(400).send({
        success: false,
        error: { code: 'VALIDATION_ERROR', message: 'text is required', statusCode: 400 },
      });
    }

    const providerName = provider ?? 'deepgram';

    try {
      const orgKey = await getOrgKeyOverride(request.organizationId!, providerName);
      const ttsProvider = createTTSProvider(providerName, orgKey);

      const pcmBuffer = await ttsProvider.synthesize(text, {
        voiceId: voiceId ?? undefined,
        speed: speed ?? 1.0,
      });

      const sampleRate = TTS_SAMPLE_RATES[providerName] ?? 16_000;
      const wavBuffer = wrapPcmAsWav(pcmBuffer, sampleRate);

      return reply
        .header('Content-Type', 'audio/wav')
        .header('Content-Length', wavBuffer.length)
        .send(wavBuffer);
    } catch (err) {
      const statusCode = (err as { status?: number; statusCode?: number }).status
        ?? (err as { statusCode?: number }).statusCode ?? 500;
      const message = err instanceof Error ? err.message : 'TTS synthesis failed';
      return reply.status(statusCode).send({
        success: false,
        error: { code: 'TTS_ERROR', message, statusCode },
      });
    }
  });

  /**
   * POST /api/stt
   *
   * Transcribe uploaded audio file. Expects multipart/form-data with field "file".
   *
   * Returns: { success: true, data: { text: string } }
   */
  app.post('/api/stt', {
    preHandler: [authMiddleware],
  }, async (request, reply) => {
    let audioBuffer: Buffer | null = null;
    let audioFormat = 'webm';
    let providerName = 'deepgram';

    try {
      const parts = request.parts();

      for await (const part of parts) {
        if (part.type === 'field') {
          if (part.fieldname === 'provider') {
            providerName = part.value as string;
          }
          if (part.fieldname === 'format') {
            audioFormat = part.value as string;
          }
        } else if (part.type === 'file' && part.fieldname === 'file') {
          // Detect format from filename if not explicitly provided
          const filename = part.filename ?? '';
          if (filename.endsWith('.wav')) audioFormat = 'wav';
          else if (filename.endsWith('.webm')) audioFormat = 'webm';
          else if (filename.endsWith('.mp3')) audioFormat = 'mp3';
          else if (filename.endsWith('.ogg')) audioFormat = 'ogg';

          const chunks: Buffer[] = [];
          for await (const chunk of part.file) {
            chunks.push(chunk);
          }
          audioBuffer = Buffer.concat(chunks);
        }
      }
    } catch (err) {
      return reply.status(400).send({
        success: false,
        error: {
          code: 'PARSE_ERROR',
          message: 'Failed to parse multipart form data. Use multipart/form-data with a "file" field.',
          statusCode: 400,
        },
      });
    }

    if (!audioBuffer || audioBuffer.length === 0) {
      return reply.status(400).send({
        success: false,
        error: { code: 'VALIDATION_ERROR', message: 'Audio file is required (field name: "file")', statusCode: 400 },
      });
    }

    try {
      const orgKey = await getOrgKeyOverride(request.organizationId!, providerName);
      const sttProvider = createSTTProvider(providerName, orgKey);

      const text = await sttProvider.transcribe(audioBuffer, {
        format: audioFormat,
      });

      return reply.send({
        success: true,
        data: { text },
      });
    } catch (err) {
      const statusCode = (err as { status?: number; statusCode?: number }).status
        ?? (err as { statusCode?: number }).statusCode ?? 500;
      const message = err instanceof Error ? err.message : 'STT transcription failed';
      return reply.status(statusCode).send({
        success: false,
        error: { code: 'STT_ERROR', message, statusCode },
      });
    }
  });
}
