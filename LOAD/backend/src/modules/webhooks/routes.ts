import { FastifyInstance } from 'fastify';
import { authMiddleware } from '../../middleware/auth.js';
import { prisma } from '../../database/client.js';
import { z } from 'zod';
import crypto from 'node:crypto';

const createWebhookSchema = z.object({
  url: z.string().url(),
  events: z.array(z.string()).min(1),
  active: z.boolean().default(true),
});

const updateWebhookSchema = createWebhookSchema.partial();

export async function webhookRoutes(app: FastifyInstance): Promise<void> {
  app.addHook('preHandler', authMiddleware);

  app.post('/api/webhooks', async (request, reply) => {
    const body = createWebhookSchema.parse(request.body);
    const secret = crypto.randomBytes(32).toString('hex');
    const webhook = await prisma.webhook.create({
      data: {
        organizationId: request.organizationId!,
        url: body.url,
        events: body.events,
        secret,
        active: body.active,
      },
    });
    return reply.status(201).send({ success: true, data: webhook });
  });

  app.get('/api/webhooks', async (request) => {
    const webhooks = await prisma.webhook.findMany({
      where: { organizationId: request.organizationId! },
      orderBy: { createdAt: 'desc' },
    });
    return { success: true, data: webhooks };
  });

  app.get('/api/webhooks/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const webhook = await prisma.webhook.findFirst({
      where: { id, organizationId: request.organizationId! },
    });
    if (!webhook) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Webhook not found', statusCode: 404 },
      });
    }
    return { success: true, data: webhook };
  });

  app.get('/api/webhooks/:id/deliveries', async (request, reply) => {
    const { id } = request.params as { id: string };
    const query = request.query as { page?: string; limit?: string };
    const page = Math.max(1, parseInt(query.page ?? '1', 10) || 1);
    const limit = Math.min(100, Math.max(1, parseInt(query.limit ?? '20', 10) || 20));
    const skip = (page - 1) * limit;

    // Verify webhook belongs to this org
    const webhook = await prisma.webhook.findFirst({
      where: { id, organizationId: request.organizationId! },
    });
    if (!webhook) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Webhook not found', statusCode: 404 },
      });
    }

    const [deliveries, total] = await Promise.all([
      prisma.webhookDelivery.findMany({
        where: { webhookId: id },
        orderBy: { createdAt: 'desc' },
        skip,
        take: limit,
      }),
      prisma.webhookDelivery.count({ where: { webhookId: id } }),
    ]);

    return {
      success: true,
      data: deliveries,
      meta: { total, page, limit },
    };
  });

  app.patch('/api/webhooks/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const body = updateWebhookSchema.parse(request.body);
    const existing = await prisma.webhook.findFirst({
      where: { id, organizationId: request.organizationId! },
    });
    if (!existing) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Webhook not found', statusCode: 404 },
      });
    }
    const updated = await prisma.webhook.update({ where: { id }, data: body });
    return { success: true, data: updated };
  });

  app.delete('/api/webhooks/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const existing = await prisma.webhook.findFirst({
      where: { id, organizationId: request.organizationId! },
    });
    if (!existing) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Webhook not found', statusCode: 404 },
      });
    }
    await prisma.webhook.delete({ where: { id } });
    return reply.status(204).send();
  });
}
