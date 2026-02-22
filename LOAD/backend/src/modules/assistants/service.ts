import { prisma } from '../../database/client.js';
import type { CreateAssistantInput, UpdateAssistantInput, ListAssistantsInput } from './schemas.js';

export async function createAssistant(input: CreateAssistantInput, organizationId: string) {
  return prisma.assistant.create({
    data: {
      organizationId,
      name: input.name,
      model: input.model as object,
      voice: input.voice as object,
      transcriber: input.transcriber as object,
      firstMessage: input.firstMessage,
      endCallMessage: input.endCallMessage,
      endCallPhrases: input.endCallPhrases,
      metadata: input.metadata as object | undefined,
    },
  });
}

export async function listAssistants(query: ListAssistantsInput, organizationId: string) {
  const skip = (query.page - 1) * query.limit;
  const [data, total] = await Promise.all([
    prisma.assistant.findMany({
      where: { organizationId },
      orderBy: { createdAt: 'desc' },
      skip,
      take: query.limit,
    }),
    prisma.assistant.count({ where: { organizationId } }),
  ]);

  return {
    data,
    meta: { total, page: query.page, limit: query.limit },
  };
}

export async function getAssistant(id: string, organizationId: string) {
  const assistant = await prisma.assistant.findFirst({
    where: { id, organizationId },
  });
  if (!assistant) {
    throw Object.assign(new Error('Assistant not found'), { statusCode: 404 });
  }
  return assistant;
}

export async function updateAssistant(
  id: string,
  input: UpdateAssistantInput,
  organizationId: string
) {
  await getAssistant(id, organizationId);

  return prisma.assistant.update({
    where: { id },
    data: {
      ...(input.name !== undefined && { name: input.name }),
      ...(input.model !== undefined && { model: input.model as object }),
      ...(input.voice !== undefined && { voice: input.voice as object }),
      ...(input.transcriber !== undefined && { transcriber: input.transcriber as object }),
      ...(input.firstMessage !== undefined && { firstMessage: input.firstMessage }),
      ...(input.endCallMessage !== undefined && { endCallMessage: input.endCallMessage }),
      ...(input.endCallPhrases !== undefined && { endCallPhrases: input.endCallPhrases }),
      ...(input.metadata !== undefined && { metadata: input.metadata as object }),
    },
  });
}

export async function deleteAssistant(id: string, organizationId: string) {
  await getAssistant(id, organizationId);
  await prisma.assistant.delete({ where: { id } });
}
