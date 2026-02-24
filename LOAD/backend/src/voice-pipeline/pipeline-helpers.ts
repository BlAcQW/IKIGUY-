/**
 * Shared helpers for loading assistant config and tools for pipeline turns.
 *
 * Eliminates duplication across webrtc/handler.ts, websocket/handler.ts,
 * and telephony/call-bridge.ts.
 */

import { prisma } from '../database/client.js';

export interface AssistantPipelineConfig {
  modelConfig: {
    model?: string;
    temperature?: number;
    maxTokens?: number;
    toolIds?: string[];
  };
  voiceConfig: {
    voiceId?: string;
    speed?: number;
  };
  transcriberConfig: {
    model?: string;
    language?: string;
  };
}

export interface PipelineTool {
  id: string;
  type: 'FUNCTION' | 'TRANSFER_CALL' | 'END_CALL';
  name: string;
  description: string | null;
  function: { name: string; description?: string; parameters?: Record<string, unknown> } | null;
  serverUrl: string | null;
  serverSecret: string | null;
  metadata: Record<string, unknown> | null;
}

/**
 * Extract typed config objects from an assistant's JSONB fields.
 */
export function extractAssistantConfig(assistant: {
  model: unknown;
  voice: unknown;
  transcriber: unknown;
}): AssistantPipelineConfig {
  const modelConfig = (assistant.model ?? {}) as AssistantPipelineConfig['modelConfig'];
  const voiceConfig = (assistant.voice ?? {}) as AssistantPipelineConfig['voiceConfig'];
  const transcriberConfig = (assistant.transcriber ?? {}) as AssistantPipelineConfig['transcriberConfig'];
  return { modelConfig, voiceConfig, transcriberConfig };
}

/**
 * Load tools associated with an assistant and map them to the shape
 * expected by processPipelineTurn().
 */
export async function loadToolsForPipeline(
  toolIds: string[] | undefined,
  organizationId: string,
): Promise<PipelineTool[] | undefined> {
  if (!toolIds || toolIds.length === 0) return undefined;

  const tools = await prisma.tool.findMany({
    where: { id: { in: toolIds }, organizationId },
  });

  if (tools.length === 0) return undefined;

  return tools.map((t) => ({
    id: t.id,
    type: t.type as 'FUNCTION' | 'TRANSFER_CALL' | 'END_CALL',
    name: t.name,
    description: t.description,
    function: t.function as PipelineTool['function'],
    serverUrl: t.serverUrl,
    serverSecret: t.serverSecret,
    metadata: t.metadata as Record<string, unknown> | null,
  }));
}
