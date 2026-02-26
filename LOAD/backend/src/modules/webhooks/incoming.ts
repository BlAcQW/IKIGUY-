import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import { verifyWebhookSignature } from '../../middleware/webhook-signature.js';

const incomingWebhookSchema = z.object({
  event: z.string().min(1),
  timestamp: z.string().datetime().optional(),
  data: z.record(z.unknown()).optional(),
});

export async function incomingWebhookRoutes(app: FastifyInstance): Promise<void> {
  app.post(
    '/api/webhooks/incoming',
    { preHandler: verifyWebhookSignature },
    async (request, reply) => {
      const body = incomingWebhookSchema.parse(request.body);

      request.log.info({ event: body.event }, 'Incoming webhook received');

      return reply.send({
        success: true,
        data: { received: true, event: body.event },
      });
    },
  );
}
