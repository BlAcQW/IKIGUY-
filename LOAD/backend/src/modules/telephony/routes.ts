/**
 * Fastify route registration for Twilio telephony webhooks.
 *
 * These routes handle:
 * - Inbound calls (Twilio hits voiceUrl)
 * - Outbound call connection (callee answers)
 * - Call status callbacks
 * - Media Streams WebSocket for real-time audio
 *
 * Authentication: Twilio signature validation (NOT user auth).
 * Twilio calls these endpoints directly, so we verify the X-Twilio-Signature
 * header instead of requiring a JWT or API key.
 */

import type { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { config } from '../../config/index.js';
import { validateTwilioSignature } from '../../telephony/twilio.js';
import {
  inboundWebhookSchema,
  outboundConnectSchema,
  statusCallbackSchema,
} from './schemas.js';
import {
  handleInboundCall,
  handleOutboundConnect,
  handleStatusCallback,
} from './service.js';
import { handleTwilioMediaStream } from '../../telephony/twilio-stream.js';

// ---------------------------------------------------------------------------
// Twilio signature validation hook
// ---------------------------------------------------------------------------

/**
 * Verify that incoming requests are genuinely from Twilio.
 * Skips validation in development/test when Twilio is not configured.
 */
async function twilioSignatureHook(
  request: FastifyRequest,
  reply: FastifyReply,
): Promise<void> {
  // Skip validation in dev/test if Twilio is not configured
  if (
    (config.NODE_ENV === 'development' || config.NODE_ENV === 'test') &&
    !config.TWILIO_AUTH_TOKEN
  ) {
    return;
  }

  const signature = request.headers['x-twilio-signature'] as string | undefined;
  if (!signature) {
    reply.status(403).send({
      success: false,
      error: {
        code: 'FORBIDDEN',
        message: 'Missing Twilio signature',
        statusCode: 403,
      },
    });
    return;
  }

  // Build the full URL that Twilio signed
  const protocol = request.headers['x-forwarded-proto'] ?? 'http';
  const host = request.headers['host'] ?? `localhost:${config.PORT}`;
  const url = `${protocol}://${host}${request.url}`;

  const params = (request.body ?? {}) as Record<string, string>;
  const isValid = validateTwilioSignature(signature, url, params);

  if (!isValid) {
    reply.status(403).send({
      success: false,
      error: {
        code: 'FORBIDDEN',
        message: 'Invalid Twilio signature',
        statusCode: 403,
      },
    });
  }
}

// ---------------------------------------------------------------------------
// Route registration
// ---------------------------------------------------------------------------

export async function telephonyRoutes(app: FastifyInstance): Promise<void> {
  // Content-type helper for TwiML responses
  const sendTwiml = (reply: FastifyReply, twiml: string) => {
    return reply
      .header('Content-Type', 'application/xml')
      .send(twiml);
  };

  // --- Inbound call webhook ---
  app.post(
    '/api/telephony/inbound',
    { preHandler: twilioSignatureHook },
    async (request, reply) => {
      const input = inboundWebhookSchema.parse(request.body);
      const twiml = await handleInboundCall(input);
      return sendTwiml(reply, twiml);
    },
  );

  // --- Outbound call connect webhook ---
  app.post(
    '/api/telephony/outbound-connect',
    { preHandler: twilioSignatureHook },
    async (request, reply) => {
      const input = outboundConnectSchema.parse(request.body);
      const twiml = await handleOutboundConnect(input);
      return sendTwiml(reply, twiml);
    },
  );

  // --- Call status callback ---
  app.post(
    '/api/telephony/status',
    { preHandler: twilioSignatureHook },
    async (request, reply) => {
      const input = statusCallbackSchema.parse(request.body);
      await handleStatusCallback(input);
      return reply.status(204).send();
    },
  );

  // --- Media Streams WebSocket ---
  app.get(
    '/api/telephony/media-stream',
    { websocket: true },
    (socket) => {
      handleTwilioMediaStream(socket);
    },
  );
}
