import { FastifyInstance } from 'fastify';
import { authMiddleware } from '../../middleware/auth.js';
import { prisma } from '../../database/client.js';
import { z } from 'zod';
import { startCampaign, pauseCampaign, resumeCampaign } from './engine.js';

const createCampaignSchema = z.object({
  name: z.string().min(1),
  assistantId: z.string().uuid(),
  phoneNumberId: z.string().uuid(),
  contacts: z
    .array(
      z.object({
        name: z.string(),
        number: z.string(),
        metadata: z.record(z.unknown()).optional(),
      })
    )
    .default([]),
  schedule: z
    .object({
      startTime: z.string().optional(),
      endTime: z.string().optional(),
      timezone: z.string().optional(),
      maxConcurrent: z.number().optional(),
      delayBetweenCalls: z.number().min(0).max(300).optional(),
      maxRetries: z.number().int().min(0).max(5).optional(),
    })
    .optional(),
});

const updateCampaignSchema = createCampaignSchema.partial();

export async function campaignRoutes(app: FastifyInstance): Promise<void> {
  app.addHook('preHandler', authMiddleware);

  app.post('/api/campaigns', async (request, reply) => {
    const body = createCampaignSchema.parse(request.body);
    const campaign = await prisma.campaign.create({
      data: {
        organizationId: request.organizationId!,
        name: body.name,
        assistantId: body.assistantId,
        phoneNumberId: body.phoneNumberId,
        contacts: body.contacts as object[],
        schedule: body.schedule as object | undefined,
      },
    });
    return reply.status(201).send({ success: true, data: campaign });
  });

  app.get('/api/campaigns', async (request) => {
    const campaigns = await prisma.campaign.findMany({
      where: { organizationId: request.organizationId! },
      orderBy: { createdAt: 'desc' },
    });
    return { success: true, data: campaigns };
  });

  app.get('/api/campaigns/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const campaign = await prisma.campaign.findFirst({
      where: { id, organizationId: request.organizationId! },
    });
    if (!campaign) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Campaign not found', statusCode: 404 },
      });
    }
    return { success: true, data: campaign };
  });

  app.patch('/api/campaigns/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const body = updateCampaignSchema.parse(request.body);
    const existing = await prisma.campaign.findFirst({
      where: { id, organizationId: request.organizationId! },
    });
    if (!existing) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Campaign not found', statusCode: 404 },
      });
    }
    const updated = await prisma.campaign.update({ where: { id }, data: body as any });
    return { success: true, data: updated };
  });

  app.post('/api/campaigns/:id/start', async (request, reply) => {
    const { id } = request.params as { id: string };
    const campaign = await prisma.campaign.findFirst({
      where: { id, organizationId: request.organizationId! },
    });
    if (!campaign) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Campaign not found', statusCode: 404 },
      });
    }
    await startCampaign(id, request.organizationId!);
    const updated = await prisma.campaign.findUnique({ where: { id } });
    return { success: true, data: updated };
  });

  app.post('/api/campaigns/:id/pause', async (request, reply) => {
    const { id } = request.params as { id: string };
    const campaign = await prisma.campaign.findFirst({
      where: { id, organizationId: request.organizationId! },
    });
    if (!campaign) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Campaign not found', statusCode: 404 },
      });
    }
    await pauseCampaign(id, request.organizationId!);
    const updated = await prisma.campaign.findUnique({ where: { id } });
    return { success: true, data: updated };
  });

  app.post('/api/campaigns/:id/resume', async (request, reply) => {
    const { id } = request.params as { id: string };
    const campaign = await prisma.campaign.findFirst({
      where: { id, organizationId: request.organizationId! },
    });
    if (!campaign) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Campaign not found', statusCode: 404 },
      });
    }
    await resumeCampaign(id, request.organizationId!);
    const updated = await prisma.campaign.findUnique({ where: { id } });
    return { success: true, data: updated };
  });

  app.delete('/api/campaigns/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const existing = await prisma.campaign.findFirst({
      where: { id, organizationId: request.organizationId! },
    });
    if (!existing) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Campaign not found', statusCode: 404 },
      });
    }
    await prisma.campaign.delete({ where: { id } });
    return reply.status(204).send();
  });
}
