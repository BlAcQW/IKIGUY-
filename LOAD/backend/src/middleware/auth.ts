import { FastifyReply, FastifyRequest } from 'fastify';
import { prisma } from '../database/client.js';
import bcrypt from 'bcryptjs';

declare module 'fastify' {
  interface FastifyRequest {
    userId?: string;
    organizationId?: string;
    userRole?: string;
  }
}

export async function authMiddleware(
  request: FastifyRequest,
  reply: FastifyReply
): Promise<void> {
  const authHeader = request.headers.authorization;
  if (!authHeader) {
    reply.status(401).send({
      success: false,
      error: { code: 'UNAUTHORIZED', message: 'Missing authorization header', statusCode: 401 },
    });
    return;
  }

  // API Key auth: "Bearer load_..."
  if (authHeader.startsWith('Bearer load_')) {
    const apiKey = authHeader.slice(7); // Remove "Bearer "
    await authenticateApiKey(request, reply, apiKey);
    return;
  }

  // JWT auth: "Bearer <jwt>"
  if (authHeader.startsWith('Bearer ')) {
    const token = authHeader.slice(7);
    await authenticateJwt(request, reply, token);
    return;
  }

  reply.status(401).send({
    success: false,
    error: { code: 'UNAUTHORIZED', message: 'Invalid authorization format', statusCode: 401 },
  });
}

async function authenticateJwt(
  request: FastifyRequest,
  reply: FastifyReply,
  _token: string
): Promise<void> {
  try {
    const decoded = await request.jwtVerify<{
      userId: string;
      organizationId: string;
      role: string;
    }>();
    request.userId = decoded.userId;
    request.organizationId = decoded.organizationId;
    request.userRole = decoded.role;
  } catch {
    reply.status(401).send({
      success: false,
      error: { code: 'UNAUTHORIZED', message: 'Invalid or expired token', statusCode: 401 },
    });
  }
}

async function authenticateApiKey(
  request: FastifyRequest,
  reply: FastifyReply,
  apiKey: string
): Promise<void> {
  const prefix = apiKey.slice(0, 13); // "load_" + 8 chars

  const apiKeys = await prisma.apiKey.findMany({
    where: { prefix },
    include: { createdBy: true },
  });

  for (const record of apiKeys) {
    const isMatch = await bcrypt.compare(apiKey, record.keyHash);
    if (isMatch) {
      if (record.expiresAt && record.expiresAt < new Date()) {
        reply.status(401).send({
          success: false,
          error: { code: 'UNAUTHORIZED', message: 'API key has expired', statusCode: 401 },
        });
        return;
      }

      // Update last used timestamp (fire and forget)
      prisma.apiKey.update({
        where: { id: record.id },
        data: { lastUsedAt: new Date() },
      }).catch(() => {});

      request.userId = record.createdById;
      request.organizationId = record.organizationId;
      request.userRole = record.createdBy.role;
      return;
    }
  }

  reply.status(401).send({
    success: false,
    error: { code: 'UNAUTHORIZED', message: 'Invalid API key', statusCode: 401 },
  });
}
