import { FastifyInstance } from 'fastify';
import { authMiddleware } from '../../middleware/auth.js';
import {
  listElevenLabsVoices,
  cloneVoice,
  deleteClonedVoice,
  previewVoice,
} from './service.js';

export async function voiceRoutes(app: FastifyInstance): Promise<void> {
  /**
   * GET /api/voices
   * List all available voices (ElevenLabs library + clones).
   */
  app.get('/api/voices', {
    preHandler: [authMiddleware],
  }, async (_request, reply) => {
    try {
      const voices = await listElevenLabsVoices();
      return reply.send({ success: true, data: voices });
    } catch (err) {
      const statusCode = (err as { statusCode?: number }).statusCode ?? 500;
      const message = err instanceof Error ? err.message : 'Failed to list voices';
      return reply.status(statusCode).send({
        success: false,
        error: { code: 'VOICE_LIST_ERROR', message, statusCode },
      });
    }
  });

  /**
   * POST /api/voices/clone
   * Clone a voice from an uploaded audio file.
   * Expects multipart/form-data with fields: name, description, file (audio).
   */
  app.post('/api/voices/clone', {
    preHandler: [authMiddleware],
  }, async (request, reply) => {
    try {
      const parts = request.parts();
      let name = '';
      let description = '';
      let audioBuffer: Buffer | null = null;
      let audioFilename = 'voice.mp3';

      for await (const part of parts) {
        if (part.type === 'field') {
          if (part.fieldname === 'name') name = part.value as string;
          if (part.fieldname === 'description') description = part.value as string;
        } else if (part.type === 'file' && part.fieldname === 'file') {
          audioFilename = part.filename ?? 'voice.mp3';
          const chunks: Buffer[] = [];
          for await (const chunk of part.file) {
            chunks.push(chunk);
          }
          audioBuffer = Buffer.concat(chunks);
        }
      }

      if (!name) {
        return reply.status(400).send({
          success: false,
          error: { code: 'VALIDATION_ERROR', message: 'Voice name is required', statusCode: 400 },
        });
      }

      if (!audioBuffer || audioBuffer.length === 0) {
        return reply.status(400).send({
          success: false,
          error: { code: 'VALIDATION_ERROR', message: 'Audio file is required', statusCode: 400 },
        });
      }

      const voice = await cloneVoice(name, description, audioBuffer, audioFilename);

      return reply.status(201).send({ success: true, data: voice });
    } catch (err) {
      const statusCode = (err as { statusCode?: number }).statusCode ?? 500;
      const message = err instanceof Error ? err.message : 'Voice cloning failed';
      return reply.status(statusCode).send({
        success: false,
        error: { code: 'CLONE_ERROR', message, statusCode },
      });
    }
  });

  /**
   * DELETE /api/voices/:voiceId
   * Delete a cloned voice.
   */
  app.delete<{ Params: { voiceId: string } }>('/api/voices/:voiceId', {
    preHandler: [authMiddleware],
  }, async (request, reply) => {
    try {
      await deleteClonedVoice(request.params.voiceId);
      return reply.send({ success: true, data: null });
    } catch (err) {
      const statusCode = (err as { statusCode?: number }).statusCode ?? 500;
      const message = err instanceof Error ? err.message : 'Failed to delete voice';
      return reply.status(statusCode).send({
        success: false,
        error: { code: 'DELETE_ERROR', message, statusCode },
      });
    }
  });

  /**
   * POST /api/voices/preview
   * Generate a short audio preview of a voice. Returns audio/mpeg.
   */
  app.post('/api/voices/preview', {
    preHandler: [authMiddleware],
  }, async (request, reply) => {
    const { provider, voiceId, text } = request.body as {
      provider: string;
      voiceId: string;
      text?: string;
    };

    if (!provider || !voiceId) {
      return reply.status(400).send({
        success: false,
        error: { code: 'VALIDATION_ERROR', message: 'provider and voiceId are required', statusCode: 400 },
      });
    }

    try {
      const audioBuffer = await previewVoice(provider, voiceId, text);
      return reply
        .header('Content-Type', 'audio/mpeg')
        .header('Content-Length', audioBuffer.length)
        .send(audioBuffer);
    } catch (err) {
      const statusCode = (err as { statusCode?: number }).statusCode ?? 500;
      const message = err instanceof Error ? err.message : 'Preview failed';
      return reply.status(statusCode).send({
        success: false,
        error: { code: 'PREVIEW_ERROR', message, statusCode },
      });
    }
  });
}
