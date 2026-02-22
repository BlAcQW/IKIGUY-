import { FastifyInstance } from 'fastify';
import { registerSchema, loginSchema, createApiKeySchema } from './schemas.js';
import { registerUser, loginUser, createApiKey, listApiKeys, revokeApiKey } from './service.js';
import { authMiddleware } from '../../middleware/auth.js';

export async function authRoutes(app: FastifyInstance): Promise<void> {
  // Public routes
  app.post('/api/auth/register', async (request, reply) => {
    const body = registerSchema.parse(request.body);
    const result = await registerUser(body);
    const token = app.jwt.sign(
      { userId: result.user.id, organizationId: result.organization.id, role: result.user.role },
      { expiresIn: process.env.JWT_EXPIRES_IN ?? '15m' }
    );
    return reply.status(201).send({
      success: true,
      data: { ...result, token },
    });
  });

  app.post('/api/auth/login', async (request, reply) => {
    const body = loginSchema.parse(request.body);
    const result = await loginUser(body);
    const token = app.jwt.sign(
      { userId: result.user.id, organizationId: result.organization.id, role: result.user.role },
      { expiresIn: process.env.JWT_EXPIRES_IN ?? '15m' }
    );
    return reply.send({
      success: true,
      data: { ...result, token },
    });
  });

  app.get('/api/auth/me', { preHandler: [authMiddleware] }, async (request) => {
    return {
      success: true,
      data: {
        userId: request.userId,
        organizationId: request.organizationId,
        role: request.userRole,
      },
    };
  });

  // API Key routes (authenticated)
  app.post('/api/api-keys', { preHandler: [authMiddleware] }, async (request, reply) => {
    const body = createApiKeySchema.parse(request.body);
    const result = await createApiKey(body, request.userId!, request.organizationId!);
    return reply.status(201).send({ success: true, data: result });
  });

  app.get('/api/api-keys', { preHandler: [authMiddleware] }, async (request) => {
    const keys = await listApiKeys(request.organizationId!);
    return { success: true, data: keys };
  });

  app.delete('/api/api-keys/:id', { preHandler: [authMiddleware] }, async (request, reply) => {
    const { id } = request.params as { id: string };
    await revokeApiKey(id, request.organizationId!);
    return reply.status(204).send();
  });
}
