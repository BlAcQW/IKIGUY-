import { FastifyInstance } from 'fastify';
import { authMiddleware } from '../../middleware/auth.js';
import { prisma } from '../../database/client.js';
import { z } from 'zod';
import {
  TOOL_TEMPLATES,
  TOOL_TEMPLATE_CATEGORIES,
  getTemplatesByCategory,
  getTemplateByFunctionName,
  type ToolTemplate,
} from './templates/index.js';

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

const createFromTemplateSchema = z.object({
  templateName: z.string().min(1),
  serverUrl: z.string().url(),
  serverSecret: z.string().optional(),
});

const bulkCreateFromTemplatesSchema = z.object({
  category: z.string().min(1),
  serverUrl: z.string().url(),
  serverSecret: z.string().optional(),
  assistantId: z.string().uuid().optional(),
});

export async function toolRoutes(app: FastifyInstance): Promise<void> {
  app.addHook('preHandler', authMiddleware);

  // ─── Template endpoints (listed before :id routes) ───────────────

  app.get('/api/tools/templates', async () => {
    const grouped = getTemplatesByCategory();
    return {
      success: true,
      data: {
        categories: TOOL_TEMPLATE_CATEGORIES,
        templates: grouped,
      },
    };
  });

  app.post('/api/tools/from-template', async (request, reply) => {
    const body = createFromTemplateSchema.parse(request.body);
    const template = getTemplateByFunctionName(body.templateName);
    if (!template) {
      return reply.status(404).send({
        success: false,
        error: {
          code: 'TEMPLATE_NOT_FOUND',
          message: `Template "${body.templateName}" not found`,
          statusCode: 404,
        },
      });
    }

    const tool = await prisma.tool.create({
      data: {
        organizationId: request.organizationId!,
        name: template.name,
        type: template.type,
        description: template.description,
        function: template.function as object,
        serverUrl: body.serverUrl,
        serverSecret: body.serverSecret,
        metadata: { templateName: template.function.name, category: template.category },
      },
    });
    return reply.status(201).send({ success: true, data: tool });
  });

  app.post('/api/tools/from-templates/bulk', async (request, reply) => {
    const body = bulkCreateFromTemplatesSchema.parse(request.body);
    const grouped = getTemplatesByCategory();
    const templates = grouped[body.category as keyof typeof grouped];

    if (!templates || templates.length === 0) {
      return reply.status(404).send({
        success: false,
        error: {
          code: 'CATEGORY_NOT_FOUND',
          message: `No templates found for category "${body.category}"`,
          statusCode: 404,
        },
      });
    }

    const tools = await prisma.$transaction(
      templates.map((template: ToolTemplate) =>
        prisma.tool.create({
          data: {
            organizationId: request.organizationId!,
            name: template.name,
            type: template.type,
            description: template.description,
            function: template.function as object,
            serverUrl: body.serverUrl,
            serverSecret: body.serverSecret,
            metadata: { templateName: template.function.name, category: template.category },
          },
        }),
      ),
    );

    if (body.assistantId) {
      const assistant = await prisma.assistant.findFirst({
        where: { id: body.assistantId, organizationId: request.organizationId! },
      });
      if (assistant) {
        const modelConfig = (assistant.model ?? {}) as Record<string, unknown>;
        const existingToolIds = (modelConfig.toolIds as string[]) ?? [];
        const newToolIds = tools.map((t) => t.id);
        await prisma.assistant.update({
          where: { id: body.assistantId },
          data: {
            model: { ...modelConfig, toolIds: [...existingToolIds, ...newToolIds] },
          },
        });
      }
    }

    return reply.status(201).send({ success: true, data: tools });
  });

  // ─── Standard CRUD ───────────────────────────────────────────────

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
    const updated = await prisma.tool.update({
      where: { id },
      data: {
        ...(body.name !== undefined && { name: body.name }),
        ...(body.type !== undefined && { type: body.type }),
        ...(body.description !== undefined && { description: body.description }),
        ...(body.function !== undefined && { function: body.function as object }),
        ...(body.serverUrl !== undefined && { serverUrl: body.serverUrl }),
        ...(body.serverSecret !== undefined && { serverSecret: body.serverSecret }),
        ...(body.metadata !== undefined && { metadata: body.metadata as object }),
      },
    });
    return { success: true, data: updated };
  });

  app.post('/api/tools/:id/test', async (request, reply) => {
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
    if (!tool.serverUrl) {
      return reply.status(400).send({
        success: false,
        error: { code: 'NO_SERVER_URL', message: 'Tool has no server URL configured', statusCode: 400 },
      });
    }

    const testPayload = {
      type: 'tool_call',
      toolCallId: `test-${Date.now()}`,
      function: tool.function ?? { name: tool.name, parameters: {} },
      test: true,
    };

    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (tool.serverSecret) {
        const crypto = await import('crypto');
        const sig = crypto.createHmac('sha256', tool.serverSecret).update(JSON.stringify(testPayload)).digest('hex');
        headers['x-load-signature'] = sig;
      }

      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000);
      const res = await fetch(tool.serverUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(testPayload),
        signal: controller.signal,
      });
      clearTimeout(timeout);

      const responseText = await res.text();
      let responseBody: unknown;
      try { responseBody = JSON.parse(responseText); } catch { responseBody = responseText; }

      return {
        success: true,
        data: {
          status: res.status,
          statusText: res.statusText,
          body: responseBody,
          latencyMs: Date.now() - parseInt(testPayload.toolCallId.split('-')[1]),
        },
      };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      return reply.status(502).send({
        success: false,
        error: { code: 'TOOL_TEST_FAILED', message: `Failed to reach server: ${message}`, statusCode: 502 },
      });
    }
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
