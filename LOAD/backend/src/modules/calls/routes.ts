import { FastifyInstance } from 'fastify';
import { authMiddleware } from '../../middleware/auth.js';
import { listCallsSchema, createOutboundCallSchema } from './schemas.js';
import { listCalls, getCall, endCall } from './service.js';

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
  app.post('/api/calls', async (request, reply) => {
    const body = createOutboundCallSchema.parse(request.body);
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
