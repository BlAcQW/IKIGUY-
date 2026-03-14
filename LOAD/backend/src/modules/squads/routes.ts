import { FastifyInstance } from 'fastify';
import { authMiddleware } from '../../middleware/auth.js';
import { createSquadSchema, updateSquadSchema, squadQuerySchema } from './schemas.js';
import { createSquad, listSquads, getSquad, updateSquad, deleteSquad } from './service.js';

export async function squadRoutes(app: FastifyInstance): Promise<void> {
  app.addHook('preHandler', authMiddleware);

  app.post('/api/squads', async (request, reply) => {
    const body = createSquadSchema.parse(request.body);
    const squad = await createSquad(body, request.organizationId!);
    return reply.status(201).send({ success: true, data: squad });
  });

  app.get('/api/squads', async (request) => {
    const query = squadQuerySchema.parse(request.query);
    const result = await listSquads(request.organizationId!, query.page, query.limit);
    return {
      success: true,
      data: result.squads,
      meta: { total: result.total, page: result.page, limit: result.limit },
    };
  });

  app.get('/api/squads/:id', async (request) => {
    const { id } = request.params as { id: string };
    const squad = await getSquad(id, request.organizationId!);
    return { success: true, data: squad };
  });

  app.patch('/api/squads/:id', async (request) => {
    const { id } = request.params as { id: string };
    const body = updateSquadSchema.parse(request.body);
    const updated = await updateSquad(id, body, request.organizationId!);
    return { success: true, data: updated };
  });

  app.delete('/api/squads/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    await deleteSquad(id, request.organizationId!);
    return reply.status(204).send();
  });
}
