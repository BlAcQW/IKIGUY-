import { FastifyError, FastifyReply, FastifyRequest } from 'fastify';
import { ZodError } from 'zod';
import { Prisma } from '@prisma/client';

interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    statusCode: number;
  };
}

export function errorHandler(
  error: FastifyError,
  _request: FastifyRequest,
  reply: FastifyReply
): void {
  const response: ApiError = {
    success: false,
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred',
      statusCode: 500,
    },
  };

  if (error instanceof ZodError) {
    response.error = {
      code: 'VALIDATION_ERROR',
      message: error.errors.map((e) => `${e.path.join('.')}: ${e.message}`).join(', '),
      statusCode: 400,
    };
  } else if (error instanceof Prisma.PrismaClientKnownRequestError) {
    if (error.code === 'P2002') {
      response.error = {
        code: 'DUPLICATE_ENTRY',
        message: 'A record with this value already exists',
        statusCode: 409,
      };
    } else if (error.code === 'P2025') {
      response.error = {
        code: 'NOT_FOUND',
        message: 'Record not found',
        statusCode: 404,
      };
    }
  } else if (error.statusCode) {
    response.error = {
      code: error.code ?? 'REQUEST_ERROR',
      message: error.message,
      statusCode: error.statusCode,
    };
  }

  if (response.error.statusCode >= 500) {
    _request.log.error({ err: error }, 'Server error');
  } else if (process.env.NODE_ENV === 'development') {
    _request.log.debug({ err: error }, 'Request error');
  }

  reply.status(response.error.statusCode).send(response);
}
