import { FastifyInstance } from 'fastify';
import { authMiddleware } from '../../middleware/auth.js';
import { prisma } from '../../database/client.js';
import { z } from 'zod';

const createToolSchema = z.object({
  name: z.string().min(1),
  type: z.enum(['FUNCTION', 'TRANSFER_CALL', 'END_CALL']).default('FUNCTION'),
  description: z.string().optional(),
  function: z
    .object({
      name: z.string(),
      description: z.string().optional(),
      parameters: z.record(z.unknown()),
    })
    .optional(),
  serverUrl: z.string().url().optional(),
  serverSecret: z.string().optional(),
  metadata: z.record(z.unknown()).optional(),
});

const updateToolSchema = createToolSchema.partial();

export async function toolRoutes(app: FastifyInstance): Promise<void> {
  app.addHook('preHandler', authMiddleware);

  app.post('/api/tools', async (request, reply) => {
    const body = createToolSchema.parse(request.body);
    const tool = await prisma.tool.create({
      data: {
        organizationId: request.organizationId!,
        name: body.name,
        type: body.type,
        description: body.description,
        function: body.function as object | undefined,
        serverUrl: body.serverUrl,
        serverSecret: body.serverSecret,
        metadata: body.metadata as object | undefined,
      },
    });
    return reply.status(201).send({ success: true, data: tool });
  });

  app.get('/api/tools', async (request) => {
    const tools = await prisma.tool.findMany({
      where: { organizationId: request.organizationId! },
      orderBy: { createdAt: 'desc' },
    });
    return { success: true, data: tools };
  });

  app.get('/api/tools/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const tool = await prisma.tool.findFirst({
      where: { id, organizationId: request.organizationId! },
    });
    if (!tool) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Tool not found', statusCode: 404 },
      });
    }
    return { success: true, data: tool };
  });

  app.patch('/api/tools/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const body = updateToolSchema.parse(request.body);
    const existing = await prisma.tool.findFirst({
      where: { id, organizationId: request.organizationId! },
    });
    if (!existing) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Tool not found', statusCode: 404 },
      });
    }
    const updated = await prisma.tool.update({ where: { id }, data: body as any });
    return { success: true, data: updated };
  });

  app.delete('/api/tools/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const existing = await prisma.tool.findFirst({
      where: { id, organizationId: request.organizationId! },
    });
    if (!existing) {
      return reply.status(404).send({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Tool not found', statusCode: 404 },
      });
    }
    await prisma.tool.delete({ where: { id } });
    return reply.status(204).send();
  });
}
