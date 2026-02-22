import { FastifyInstance } from 'fastify';
import { authMiddleware } from '../../middleware/auth.js';
import { prisma } from '../../database/client.js';
import { z } from 'zod';

const createSquadSchema = z.object({
  name: z.string().min(1),
  members: z.array(
    z.object({
      assistantId: z.string().uuid(),
      transferConditions: z.record(z.unknown()).optional(),
    })
  ),
  metadata: z.record(z.unknown()).optional(),
});

const updateSquadSchema = createSquadSchema.partial();

export async function squadRoutes(app: FastifyInstance): Promise<void> {
  app.addHook('preHandler', authMiddleware);

  app.post('/api/squads', async (request, reply) => {
    const body = createSquadSchema.parse(request.body);
    const squad = await prisma.squad.create({
      data: {
        organizationId: request.organizationId!,
        name: body.name,
        members: body.members as object[],
        metadata: body.metadata as object | undefined,
      },
    });
    return reply.status(201).send({ success: true, data: squad });
  });

  app.get('/api/squads', async (request) => {
    const squads = await prisma.squad.findMany({
      where: { organizationId: request.organizationId! },
      orderBy: { createdAt: 'desc' },
    });
    return { success: true, data: squads };
  });

  app.get('/api/squads/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const squad = await prisma.squad.findFirst({
      where: { id, organizationId: request.organizationId! },
    });
    if (!squad) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Squad not found', statusCode: 404 },
      });
    }
    return { success: true, data: squad };
  });

  app.patch('/api/squads/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const body = updateSquadSchema.parse(request.body);
    const existing = await prisma.squad.findFirst({
      where: { id, organizationId: request.organizationId! },
    });
    if (!existing) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Squad not found', statusCode: 404 },
      });
    }
    const updated = await prisma.squad.update({
      where: { id },
      data: {
        ...(body.name !== undefined && { name: body.name }),
        ...(body.members !== undefined && { members: body.members as object[] }),
        ...(body.metadata !== undefined && { metadata: body.metadata as object }),
      },
    });
    return { success: true, data: updated };
  });

  app.delete('/api/squads/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const existing = await prisma.squad.findFirst({
      where: { id, organizationId: request.organizationId! },
    });
    if (!existing) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Squad not found', statusCode: 404 },
      });
    }
    await prisma.squad.delete({ where: { id } });
    return reply.status(204).send();
  });
}
