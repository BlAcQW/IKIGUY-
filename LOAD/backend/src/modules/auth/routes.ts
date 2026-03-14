import { FastifyInstance } from 'fastify';
import { registerSchema, loginSchema, createApiKeySchema, refreshTokenSchema, updateProfileSchema } from './schemas.js';
import {
  registerUser, loginUser, createApiKey, listApiKeys, revokeApiKey,
  createRefreshToken, rotateRefreshToken, revokeAllRefreshTokens,
  updateProfile, getOrganization, updateOrganization, listOrgMembers, removeOrgMember,
} from './service.js';
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
    const refreshToken = await createRefreshToken(result.user.id, result.organization.id);
    return reply.status(201).send({
      success: true,
      data: { ...result, token, refreshToken },
    });
  });

  app.post('/api/auth/login', async (request, reply) => {
    const body = loginSchema.parse(request.body);
    const result = await loginUser(body);
    const token = app.jwt.sign(
      { userId: result.user.id, organizationId: result.organization.id, role: result.user.role },
      { expiresIn: process.env.JWT_EXPIRES_IN ?? '15m' }
    );
    const refreshToken = await createRefreshToken(result.user.id, result.organization.id);
    return reply.send({
      success: true,
      data: { ...result, token, refreshToken },
    });
  });

  app.post('/api/auth/refresh', async (request, reply) => {
    const body = refreshTokenSchema.parse(request.body);
    const result = await rotateRefreshToken(body.refreshToken);
    const token = app.jwt.sign(
      { userId: result.user.id, organizationId: result.organization.id, role: result.user.role },
      { expiresIn: process.env.JWT_EXPIRES_IN ?? '15m' }
    );
    return reply.send({
      success: true,
      data: {
        user: result.user,
        organization: result.organization,
        token,
        refreshToken: result.refreshToken,
      },
    });
  });

  app.post('/api/auth/logout', { preHandler: [authMiddleware] }, async (request, reply) => {
    await revokeAllRefreshTokens(request.userId!);
    return reply.send({ success: true, data: null });
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

  // Profile management
  app.patch('/api/auth/me', { preHandler: [authMiddleware] }, async (request) => {
    const body = updateProfileSchema.parse(request.body);
    const user = await updateProfile(request.userId!, body);
    return { success: true, data: user };
  });

  // Organization management
  app.get('/api/organizations/me', { preHandler: [authMiddleware] }, async (request) => {
    const org = await getOrganization(request.organizationId!);
    return { success: true, data: org };
  });

  app.patch('/api/organizations/me', { preHandler: [authMiddleware] }, async (request) => {
    const { name } = request.body as { name: string };
    if (!name || typeof name !== 'string' || name.trim().length === 0) {
      return { success: false, error: { code: 'VALIDATION_ERROR', message: 'Name is required', statusCode: 400 } };
    }
    const org = await updateOrganization(request.organizationId!, name.trim(), request.userRole!);
    return { success: true, data: org };
  });

  app.get('/api/organizations/me/members', { preHandler: [authMiddleware] }, async (request) => {
    const members = await listOrgMembers(request.organizationId!);
    return { success: true, data: members };
  });

  app.delete('/api/organizations/me/members/:userId', { preHandler: [authMiddleware] }, async (request, reply) => {
    const { userId } = request.params as { userId: string };
    await removeOrgMember(request.organizationId!, userId, request.userRole!);
    return reply.status(204).send();
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
