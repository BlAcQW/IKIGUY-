import { prisma } from '../../database/client.js';
import { createLLMProvider } from '../../providers/registry.js';
import type { Message } from '../../providers/llm/types.js';
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

export async function attachTool(assistantId: string, toolId: string, organizationId: string) {
  const assistant = await getAssistant(assistantId, organizationId);

  // Verify the tool exists and belongs to the same org
  const tool = await prisma.tool.findFirst({ where: { id: toolId, organizationId } });
  if (!tool) {
    throw Object.assign(new Error('Tool not found'), { statusCode: 404 });
  }

  const modelConfig = (assistant.model ?? {}) as Record<string, unknown>;
  const existingToolIds = (modelConfig.toolIds as string[]) ?? [];

  if (existingToolIds.includes(toolId)) {
    return assistant;
  }

  return prisma.assistant.update({
    where: { id: assistantId },
    data: {
      model: { ...modelConfig, toolIds: [...existingToolIds, toolId] },
    },
  });
}

export async function detachTool(assistantId: string, toolId: string, organizationId: string) {
  const assistant = await getAssistant(assistantId, organizationId);

  const modelConfig = (assistant.model ?? {}) as Record<string, unknown>;
  const existingToolIds = (modelConfig.toolIds as string[]) ?? [];

  return prisma.assistant.update({
    where: { id: assistantId },
    data: {
      model: { ...modelConfig, toolIds: existingToolIds.filter((id) => id !== toolId) },
    },
  });
}

export async function getAssistantTools(assistantId: string, organizationId: string) {
  const assistant = await getAssistant(assistantId, organizationId);
  const modelConfig = (assistant.model ?? {}) as Record<string, unknown>;
  const toolIds = (modelConfig.toolIds as string[]) ?? [];

  if (toolIds.length === 0) return [];

  return prisma.tool.findMany({
    where: { id: { in: toolIds }, organizationId },
  });
}

export async function chatWithAssistant(
  assistantId: string,
  organizationId: string,
  messages: Array<{ role: string; content: string }>
) {
  const assistant = await getAssistant(assistantId, organizationId);
  const modelConfig = (assistant.model ?? {}) as Record<string, unknown>;
  const providerName = (modelConfig.provider as string) ?? 'openai';
  const model = (modelConfig.model as string) ?? 'gpt-4o';
  const temperature = (modelConfig.temperature as number) ?? 0.7;
  const maxTokens = (modelConfig.maxTokens as number) ?? 1000;
  const systemPrompt = (modelConfig.systemPrompt as string) ?? '';

  const llm = createLLMProvider(providerName);

  const llmMessages: Message[] = [];
  if (systemPrompt) {
    llmMessages.push({ role: 'system', content: systemPrompt });
  }
  for (const msg of messages) {
    const role = msg.role === 'user' ? 'user' : 'assistant';
    llmMessages.push({ role, content: msg.content });
  }

  const result = await llm.chat(llmMessages, { model, temperature, maxTokens });
  const content = typeof result === 'string' ? result : result.content ?? '';

  return { message: content };
}
