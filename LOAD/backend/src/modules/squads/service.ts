import { prisma } from '../../database/client.js';
import type { CreateSquadInput, UpdateSquadInput } from './schemas.js';

export async function createSquad(input: CreateSquadInput, organizationId: string) {
  // Validate all assistant IDs belong to the organization
  const assistantIds = input.members.map((m) => m.assistantId);
  const uniqueIds = [...new Set(assistantIds)];
  if (uniqueIds.length !== assistantIds.length) {
    throw Object.assign(new Error('Duplicate assistant IDs in members'), { statusCode: 400 });
  }

  const assistants = await prisma.assistant.findMany({
    where: { id: { in: uniqueIds }, organizationId },
    select: { id: true },
  });
  if (assistants.length !== uniqueIds.length) {
    const foundIds = new Set(assistants.map((a) => a.id));
    const missing = uniqueIds.filter((id) => !foundIds.has(id));
    throw Object.assign(
      new Error(`Assistants not found: ${missing.join(', ')}`),
      { statusCode: 400 }
    );
  }

  const squad = await prisma.squad.create({
    data: {
      organizationId,
      name: input.name,
      members: input.members as object[],
      metadata: input.metadata as object | undefined,
    },
  });
  return squad;
}

export async function listSquads(organizationId: string, page: number, limit: number) {
  const [squads, total] = await Promise.all([
    prisma.squad.findMany({
      where: { organizationId },
      orderBy: { createdAt: 'desc' },
      skip: (page - 1) * limit,
      take: limit,
    }),
    prisma.squad.count({ where: { organizationId } }),
  ]);
  return { squads, total, page, limit };
}

export async function getSquad(id: string, organizationId: string) {
  const squad = await prisma.squad.findFirst({
    where: { id, organizationId },
  });
  if (!squad) {
    throw Object.assign(new Error('Squad not found'), { statusCode: 404 });
  }
  return squad;
}

export async function updateSquad(id: string, input: UpdateSquadInput, organizationId: string) {
  const existing = await prisma.squad.findFirst({
    where: { id, organizationId },
  });
  if (!existing) {
    throw Object.assign(new Error('Squad not found'), { statusCode: 404 });
  }

  // Validate assistant IDs if members are being updated
  if (input.members) {
    const assistantIds = input.members.map((m) => m.assistantId);
    const uniqueIds = [...new Set(assistantIds)];
    if (uniqueIds.length !== assistantIds.length) {
      throw Object.assign(new Error('Duplicate assistant IDs in members'), { statusCode: 400 });
    }

    const assistants = await prisma.assistant.findMany({
      where: { id: { in: uniqueIds }, organizationId },
      select: { id: true },
    });
    if (assistants.length !== uniqueIds.length) {
      const foundIds = new Set(assistants.map((a) => a.id));
      const missing = uniqueIds.filter((aid) => !foundIds.has(aid));
      throw Object.assign(
        new Error(`Assistants not found: ${missing.join(', ')}`),
        { statusCode: 400 }
      );
    }
  }

  const updated = await prisma.squad.update({
    where: { id },
    data: {
      ...(input.name !== undefined && { name: input.name }),
      ...(input.members !== undefined && { members: input.members as object[] }),
      ...(input.metadata !== undefined && { metadata: input.metadata as object }),
    },
  });
  return updated;
}

export async function deleteSquad(id: string, organizationId: string) {
  const existing = await prisma.squad.findFirst({
    where: { id, organizationId },
  });
  if (!existing) {
    throw Object.assign(new Error('Squad not found'), { statusCode: 404 });
  }

  await prisma.squad.delete({ where: { id } });
}
