import { FastifyInstance } from 'fastify';
import { createAssistantSchema, updateAssistantSchema, listAssistantsSchema } from './schemas.js';
import {
  createAssistant,
  listAssistants,
  getAssistant,
  updateAssistant,
  deleteAssistant,
} from './service.js';
import { authMiddleware } from '../../middleware/auth.js';

export async function assistantRoutes(app: FastifyInstance): Promise<void> {
  app.addHook('preHandler', authMiddleware);

  app.post('/api/assistants', async (request, reply) => {
    const body = createAssistantSchema.parse(request.body);
    const assistant = await createAssistant(body, request.organizationId!);
    return reply.status(201).send({ success: true, data: assistant });
  });

  app.get('/api/assistants', async (request) => {
    const query = listAssistantsSchema.parse(request.query);
    const result = await listAssistants(query, request.organizationId!);
    return { success: true, data: result.data, meta: result.meta };
  });

  app.get('/api/assistants/:id', async (request) => {
    const { id } = request.params as { id: string };
    const assistant = await getAssistant(id, request.organizationId!);
    return { success: true, data: assistant };
  });

  app.patch('/api/assistants/:id', async (request) => {
    const { id } = request.params as { id: string };
    const body = updateAssistantSchema.parse(request.body);
    const assistant = await updateAssistant(id, body, request.organizationId!);
    return { success: true, data: assistant };
  });

  app.delete('/api/assistants/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    await deleteAssistant(id, request.organizationId!);
    return reply.status(204).send();
  });
}
