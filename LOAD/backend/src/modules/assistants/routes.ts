import { FastifyInstance } from 'fastify';
import { createAssistantSchema, updateAssistantSchema, listAssistantsSchema } from './schemas.js';
import {
  createAssistant,
  listAssistants,
  getAssistant,
  updateAssistant,
  deleteAssistant,
  attachTool,
  detachTool,
  getAssistantTools,
  chatWithAssistant,
} from './service.js';
import { authMiddleware } from '../../middleware/auth.js';
import { z } from 'zod';

const attachToolSchema = z.object({
  toolId: z.string().uuid(),
});

const chatSchema = z.object({
  messages: z.array(z.object({
    role: z.string(),
    content: z.string(),
  })).min(1),
});

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

  // ─── Chat endpoint ─────────────────────────────────────────────

  app.post('/api/assistants/:id/chat', async (request, reply) => {
    const { id } = request.params as { id: string };
    const body = chatSchema.parse(request.body);
    try {
      const result = await chatWithAssistant(id, request.organizationId!, body.messages);
      return { success: true, data: result };
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Chat failed';
      const isKeyMissing = message.includes('API_KEY is required') || message.includes('API key');
      const statusCode = isKeyMissing ? 503 : 500;
      return reply.status(statusCode).send({
        success: false,
        error: { code: isKeyMissing ? 'PROVIDER_NOT_CONFIGURED' : 'CHAT_ERROR', message, statusCode },
      });
    }
  });

  // ─── Tool attachment endpoints ─────────────────────────────────

  app.get('/api/assistants/:id/tools', async (request) => {
    const { id } = request.params as { id: string };
    const tools = await getAssistantTools(id, request.organizationId!);
    return { success: true, data: tools };
  });

  app.post('/api/assistants/:id/tools', async (request) => {
    const { id } = request.params as { id: string };
    const body = attachToolSchema.parse(request.body);
    const assistant = await attachTool(id, body.toolId, request.organizationId!);
    return { success: true, data: assistant };
  });

  app.delete('/api/assistants/:id/tools/:toolId', async (request) => {
    const { id, toolId } = request.params as { id: string; toolId: string };
    const assistant = await detachTool(id, toolId, request.organizationId!);
    return { success: true, data: assistant };
  });
}
