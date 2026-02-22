import { prisma } from '../../database/client.js';
import type { CallStatus, CallType } from '@prisma/client';

export interface CreateCallInput {
  organizationId: string;
  assistantId: string;
  type: CallType;
  customerNumber?: string;
  phoneNumberId?: string;
}

export async function createCall(input: CreateCallInput) {
  return prisma.call.create({
    data: {
      organizationId: input.organizationId,
      assistantId: input.assistantId,
      type: input.type,
      status: 'QUEUED',
      customerNumber: input.customerNumber ?? null,
      phoneNumberId: input.phoneNumberId ?? null,
    },
  });
}

export async function updateCallStatus(id: string, status: CallStatus) {
  const data: Record<string, unknown> = { status };
  if (status === 'IN_PROGRESS') {
    data.startedAt = new Date();
  }
  return prisma.call.update({ where: { id }, data });
}

export async function endCall(
  id: string,
  transcript: { role: string; content: string }[],
  endReason?: string
) {
  const call = await prisma.call.findUnique({ where: { id } });
  if (!call) {
    throw Object.assign(new Error('Call not found'), { statusCode: 404 });
  }

  const endedAt = new Date();
  const duration = call.startedAt
    ? Math.round((endedAt.getTime() - call.startedAt.getTime()) / 1000)
    : 0;

  return prisma.call.update({
    where: { id },
    data: {
      status: 'ENDED',
      endedAt,
      duration,
      endReason: endReason ?? 'completed',
      transcript: transcript as object,
    },
  });
}

export async function failCall(id: string, reason: string) {
  return prisma.call.update({
    where: { id },
    data: {
      status: 'FAILED',
      endedAt: new Date(),
      endReason: reason,
    },
  });
}

export async function getCall(id: string, organizationId: string) {
  const call = await prisma.call.findFirst({
    where: { id, organizationId },
  });
  if (!call) {
    throw Object.assign(new Error('Call not found'), { statusCode: 404 });
  }
  return call;
}

export async function listCalls(
  organizationId: string,
  query: { page: number; limit: number; status?: string; assistantId?: string }
) {
  const skip = (query.page - 1) * query.limit;
  const where = {
    organizationId,
    ...(query.status && { status: query.status as CallStatus }),
    ...(query.assistantId && { assistantId: query.assistantId }),
  };

  const [data, total] = await Promise.all([
    prisma.call.findMany({
      where,
      orderBy: { createdAt: 'desc' },
      skip,
      take: query.limit,
    }),
    prisma.call.count({ where }),
  ]);

  return { data, meta: { total, page: query.page, limit: query.limit } };
}
