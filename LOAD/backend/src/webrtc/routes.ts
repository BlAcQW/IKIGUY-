import { FastifyInstance } from 'fastify';
import { prisma } from '../database/client.js';
import { authMiddleware } from '../middleware/auth.js';
import { buildPipelineFromAssistant } from '../providers/registry.js';
import { createCall, updateCallStatus } from '../modules/calls/service.js';
import { createSession } from '../voice-pipeline/session.js';
import { fireWebhookEvent } from '../modules/webhooks/delivery.js';
import { WebRTCCallHandler } from './handler.js';
import { webrtcOfferSchema, webrtcIceCandidateSchema } from './schemas.js';

/** Active WebRTC call handlers keyed by callId. */
const activeHandlers = new Map<string, WebRTCCallHandler>();

/** Maximum time (ms) a handler can stay in the map without being cleaned up. */
const HANDLER_TTL_MS = 30 * 60 * 1000; // 30 minutes

/** Periodic sweep interval. */
const SWEEP_INTERVAL_MS = 60 * 1000; // 1 minute

let sweepTimer: ReturnType<typeof setInterval> | null = null;

/**
 * Start a periodic sweep that removes stale handlers.
 * Handlers track their creation time; if they exceed the TTL, they are closed and removed.
 */
function startHandlerSweep(): void {
  if (sweepTimer) return;
  sweepTimer = setInterval(() => {
    const now = Date.now();
    for (const [callId, handler] of activeHandlers) {
      if (now - handler.createdAt > HANDLER_TTL_MS) {
        console.warn(`[WebRTC] Evicting stale handler for call ${callId} (TTL exceeded)`);
        handler.close().catch(() => {});
        activeHandlers.delete(callId);
      }
    }
  }, SWEEP_INTERVAL_MS);
  // Don't block process exit
  if (sweepTimer && typeof sweepTimer === 'object' && 'unref' in sweepTimer) {
    sweepTimer.unref();
  }
}

export async function webrtcRoutes(app: FastifyInstance): Promise<void> {
  startHandlerSweep();
  /**
   * POST /api/calls/webrtc/offer
   * Exchange SDP offer/answer to establish a WebRTC peer connection.
   */
  app.post('/api/calls/webrtc/offer', {
    preHandler: [authMiddleware],
  }, async (request, reply) => {
    const parsed = webrtcOfferSchema.safeParse(request.body);
    if (!parsed.success) {
      return reply.status(400).send({
        success: false,
        error: { code: 'VALIDATION_ERROR', message: parsed.error.message, statusCode: 400 },
      });
    }

    const { assistantId, sdpOffer } = parsed.data;
    const organizationId = request.organizationId!;

    // Verify assistant belongs to org
    const assistant = await prisma.assistant.findFirst({
      where: { id: assistantId, organizationId },
    });
    if (!assistant) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Assistant not found', statusCode: 404 },
      });
    }

    // Build voice pipeline
    let pipeline;
    try {
      pipeline = buildPipelineFromAssistant(assistant);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to initialize voice providers';
      const isKeyMissing = message.includes('API_KEY is required') || message.includes('API key');
      const statusCode = isKeyMissing ? 503 : 500;
      const code = isKeyMissing ? 'PROVIDER_NOT_CONFIGURED' : 'PIPELINE_ERROR';
      return reply.status(statusCode).send({
        success: false,
        error: { code, message, statusCode },
      });
    }

    // Create call record
    const call = await createCall({
      organizationId,
      assistantId: assistant.id,
      type: 'WEB',
    });
    await updateCallStatus(call.id, 'IN_PROGRESS');

    // Create session
    const modelConfig = assistant.model as { systemPrompt?: string };
    const session = await createSession({
      callId: call.id,
      assistantId: assistant.id,
      organizationId,
      systemPrompt: modelConfig.systemPrompt,
    });

    // Instantiate handler
    const handler = new WebRTCCallHandler({
      organizationId,
      assistantId: assistant.id,
      callId: call.id,
      sessionId: session.id,
      pipeline,
      assistant: {
        id: assistant.id,
        name: assistant.name,
        model: assistant.model,
        voice: assistant.voice,
        transcriber: assistant.transcriber,
        firstMessage: assistant.firstMessage,
        endCallPhrases: assistant.endCallPhrases,
        metadata: assistant.metadata,
      },
    });

    // Perform SDP exchange
    const sdpAnswer = await handler.handleOffer(sdpOffer);

    // Auto-remove handler from map when it self-closes (disconnect, end-call phrase, etc.)
    handler.onClose(() => {
      activeHandlers.delete(call.id);
    });

    // Store handler
    activeHandlers.set(call.id, handler);

    // Fire webhook
    fireWebhookEvent(organizationId, 'call.started', {
      callId: call.id,
      type: 'WEB',
      assistantId: assistant.id,
    }).catch(() => {});

    return reply.send({
      success: true,
      data: {
        callId: call.id,
        sessionId: session.id,
        sdpAnswer,
      },
    });
  });

  /**
   * POST /api/calls/webrtc/ice
   * Add a trickle ICE candidate to an active call.
   */
  app.post('/api/calls/webrtc/ice', {
    preHandler: [authMiddleware],
  }, async (request, reply) => {
    const parsed = webrtcIceCandidateSchema.safeParse(request.body);
    if (!parsed.success) {
      return reply.status(400).send({
        success: false,
        error: { code: 'VALIDATION_ERROR', message: parsed.error.message, statusCode: 400 },
      });
    }

    const { callId, candidate } = parsed.data;
    const handler = activeHandlers.get(callId);
    if (!handler) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Call not found or already ended', statusCode: 404 },
      });
    }

    if (handler.organizationId !== request.organizationId) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Call not found or already ended', statusCode: 404 },
      });
    }

    await handler.addIceCandidate(candidate);

    return reply.send({ success: true, data: null });
  });

  /**
   * POST /api/calls/webrtc/:callId/end
   * End an active WebRTC call.
   */
  app.post<{ Params: { callId: string } }>('/api/calls/webrtc/:callId/end', {
    preHandler: [authMiddleware],
  }, async (request, reply) => {
    const { callId } = request.params;
    const handler = activeHandlers.get(callId);
    if (!handler) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Call not found or already ended', statusCode: 404 },
      });
    }

    if (handler.organizationId !== request.organizationId) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Call not found or already ended', statusCode: 404 },
      });
    }

    await handler.close();
    activeHandlers.delete(callId);

    return reply.send({ success: true, data: null });
  });
}

/**
 * Get an active handler (for testing).
 */
export function getActiveHandler(callId: string): WebRTCCallHandler | undefined {
  return activeHandlers.get(callId);
}

/**
 * Remove an active handler (for testing/cleanup).
 */
export function removeActiveHandler(callId: string): void {
  activeHandlers.delete(callId);
}
