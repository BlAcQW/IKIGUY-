import { describe, it, expect, vi } from 'vitest';
import { ZodError, ZodIssueCode } from 'zod';
import { Prisma } from '@prisma/client';
import { errorHandler } from './error-handler.js';
import type { FastifyError, FastifyReply, FastifyRequest } from 'fastify';

function createMockReply() {
  const reply = {
    status: vi.fn().mockReturnThis(),
    send: vi.fn().mockReturnThis(),
  };
  return reply as unknown as FastifyReply;
}

function createMockRequest() {
  return {} as FastifyRequest;
}

describe('errorHandler', () => {
  it('handles ZodError as 400 VALIDATION_ERROR', () => {
    const zodError = new ZodError([
      {
        code: ZodIssueCode.invalid_type,
        expected: 'string',
        received: 'undefined',
        path: ['email'],
        message: 'Required',
      },
    ]);

    const reply = createMockReply();
    errorHandler(zodError as unknown as FastifyError, createMockRequest(), reply);

    expect(reply.status).toHaveBeenCalledWith(400);
    expect(reply.send).toHaveBeenCalledWith({
      success: false,
      error: {
        code: 'VALIDATION_ERROR',
        message: expect.stringContaining('email'),
        statusCode: 400,
      },
    });
  });

  it('handles Prisma P2002 as 409 DUPLICATE_ENTRY', () => {
    const prismaError = new Prisma.PrismaClientKnownRequestError('Unique constraint', {
      code: 'P2002',
      clientVersion: '5.0.0',
    });

    const reply = createMockReply();
    errorHandler(prismaError as unknown as FastifyError, createMockRequest(), reply);

    expect(reply.status).toHaveBeenCalledWith(409);
    expect(reply.send).toHaveBeenCalledWith({
      success: false,
      error: {
        code: 'DUPLICATE_ENTRY',
        message: 'A record with this value already exists',
        statusCode: 409,
      },
    });
  });

  it('handles Prisma P2025 as 404 NOT_FOUND', () => {
    const prismaError = new Prisma.PrismaClientKnownRequestError('Record not found', {
      code: 'P2025',
      clientVersion: '5.0.0',
    });

    const reply = createMockReply();
    errorHandler(prismaError as unknown as FastifyError, createMockRequest(), reply);

    expect(reply.status).toHaveBeenCalledWith(404);
    expect(reply.send).toHaveBeenCalledWith({
      success: false,
      error: {
        code: 'NOT_FOUND',
        message: 'Record not found',
        statusCode: 404,
      },
    });
  });

  it('handles error with statusCode property', () => {
    const error = Object.assign(new Error('Unauthorized'), { statusCode: 401 }) as FastifyError;

    const reply = createMockReply();
    errorHandler(error, createMockRequest(), reply);

    expect(reply.status).toHaveBeenCalledWith(401);
    expect(reply.send).toHaveBeenCalledWith({
      success: false,
      error: {
        code: 'REQUEST_ERROR',
        message: 'Unauthorized',
        statusCode: 401,
      },
    });
  });

  it('returns 500 for unknown errors', () => {
    const error = new Error('Something broke') as FastifyError;

    const reply = createMockReply();
    errorHandler(error, createMockRequest(), reply);

    expect(reply.status).toHaveBeenCalledWith(500);
    expect(reply.send).toHaveBeenCalledWith({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: 'An unexpected error occurred',
        statusCode: 500,
      },
    });
  });

  it('returns consistent error envelope structure', () => {
    const error = new Error('Test') as FastifyError;

    const reply = createMockReply();
    errorHandler(error, createMockRequest(), reply);

    const sent = vi.mocked(reply.send).mock.calls[0][0];
    expect(sent).toHaveProperty('success', false);
    expect(sent.error).toHaveProperty('code');
    expect(sent.error).toHaveProperty('message');
    expect(sent.error).toHaveProperty('statusCode');
  });
});
