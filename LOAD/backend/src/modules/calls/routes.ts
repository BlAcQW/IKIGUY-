import { FastifyInstance } from 'fastify';
import { authMiddleware } from '../../middleware/auth.js';
import { prisma } from '../../database/client.js';
import { listCallsSchema, createOutboundCallSchema } from './schemas.js';
import { listCalls, getCall, endCall } from './service.js';
import { makeOutboundCallTwilio } from '../telephony/service.js';

export async function callRoutes(app: FastifyInstance): Promise<void> {
  app.addHook('preHandler', authMiddleware);

  app.get('/api/calls', async (request) => {
    const query = listCallsSchema.parse(request.query);
    const result = await listCalls(request.organizationId!, query);
    return { success: true, data: result.data, meta: result.meta };
  });

  app.get('/api/calls/:id', async (request) => {
    const { id } = request.params as { id: string };
    const call = await getCall(id, request.organizationId!);
    return { success: true, data: call };
  });

  // POST /api/calls — Initiate outbound call via telephony
  // Routes to Twilio Direct or Asterisk based on phone number provider.
  app.post('/api/calls', async (request, reply) => {
    const body = createOutboundCallSchema.parse(request.body);

    // Look up the phone number to determine the provider
    const phoneNumber = await prisma.phoneNumber.findFirst({
      where: { id: body.phoneNumberId, organizationId: request.organizationId! },
    });

    if (!phoneNumber) {
      return reply.status(404).send({
        success: false,
        error: {
          code: 'NOT_FOUND',
          message: 'Phone number not found',
          statusCode: 404,
        },
      });
    }

    // Twilio Direct path — use Twilio REST API + Media Streams
    if (phoneNumber.provider === 'TWILIO') {
      const result = await makeOutboundCallTwilio({
        organizationId: request.organizationId!,
        assistantId: body.assistantId,
        customerNumber: body.customerNumber,
        phoneNumberId: body.phoneNumberId,
        metadata: body.metadata,
      });
      return reply.status(201).send({ success: true, data: result });
    }

    // Asterisk path — GoIP / SIP_TRUNK providers
    const callBridge = (app as any).callBridge;
    if (!callBridge) {
      return reply.status(503).send({
        success: false,
        error: {
          code: 'TELEPHONY_UNAVAILABLE',
          message: 'Telephony is not configured. Set ASTERISK_ARI_URL to enable.',
          statusCode: 503,
        },
      });
    }

    const result = await callBridge.initiateOutbound({
      organizationId: request.organizationId!,
      assistantId: body.assistantId,
      customerNumber: body.customerNumber,
      phoneNumberId: body.phoneNumberId,
      metadata: body.metadata,
    });

    return reply.status(201).send({ success: true, data: result });
  });

  // POST /api/calls/:id/end — Force hangup
  app.post('/api/calls/:id/end', async (request) => {
    const { id } = request.params as { id: string };
    const call = await getCall(id, request.organizationId!);
    const ended = await endCall(call.id, [], 'force_hangup');
    return { success: true, data: ended };
  });
}
