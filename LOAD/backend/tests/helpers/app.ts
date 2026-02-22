import { FastifyInstance } from 'fastify';

export async function createTestApp(): Promise<FastifyInstance> {
  const { buildApp } = await import('../../src/index.js');
  const app = await buildApp();
  await app.ready();
  return app;
}

export function generateTestToken(
  app: FastifyInstance,
  payload?: { userId?: string; organizationId?: string; role?: string }
): string {
  return app.jwt.sign({
    userId: payload?.userId ?? 'test-user-id',
    organizationId: payload?.organizationId ?? 'test-org-id',
    role: payload?.role ?? 'OWNER',
  });
}
