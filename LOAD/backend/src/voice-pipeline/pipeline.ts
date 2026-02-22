import type { STTProvider } from '../providers/stt/types.js';
import type { LLMProvider, LLMTool, LLMToolCall, Message } from '../providers/llm/types.js';
import type { TTSProvider } from '../providers/tts/types.js';
import { addMessage, getSession } from './session.js';
import { executeTool, type ToolExecutionResult } from './tool-executor.js';

export interface PipelineConfig {
  stt: STTProvider;
  llm: LLMProvider;
  tts: TTSProvider;
}

export interface PipelineResult {
  userText: string;
  assistantText: string;
  audioBuffer: Buffer;
  toolCallsExecuted: ToolCallRecord[];
  transferRequest?: { targetAssistantId: string };
  endCallRequested: boolean;
}

export interface ToolCallRecord {
  name: string;
  arguments: string;
  result: ToolExecutionResult;
}

interface ToolDefinition {
  id: string;
  type: 'FUNCTION' | 'TRANSFER_CALL' | 'END_CALL';
  name: string;
  description?: string | null;
  function?: { name: string; description?: string; parameters?: Record<string, unknown> } | null;
  serverUrl?: string | null;
  serverSecret?: string | null;
}

const MAX_TOOL_ITERATIONS = 5;

/**
 * Voice pipeline orchestrator: Audio → STT → LLM → TTS → Audio
 * Supports tool calling with iterative LLM-tool loop.
 */
export async function processPipelineTurn(
  sessionId: string,
  audioInput: Buffer,
  config: PipelineConfig,
  options?: {
    sttModel?: string;
    sttLanguage?: string;
    llmModel?: string;
    llmTemperature?: number;
    llmMaxTokens?: number;
    ttsVoiceId?: string;
    ttsSpeed?: number;
    tools?: ToolDefinition[];
  }
): Promise<PipelineResult> {
  const session = await getSession(sessionId);
  if (!session) {
    throw new Error(`Session ${sessionId} not found`);
  }

  // Step 1: STT — Transcribe audio to text
  const userText = await config.stt.transcribe(audioInput, {
    model: options?.sttModel,
    language: options?.sttLanguage,
  });

  // Add user message to conversation history
  await addMessage(sessionId, { role: 'user', content: userText });

  // Convert tools to LLM format
  const llmTools: LLMTool[] | undefined = options?.tools?.map(toolToLLMFormat);

  // Step 2: LLM with tool call loop
  const toolCallsExecuted: ToolCallRecord[] = [];
  let transferRequest: { targetAssistantId: string } | undefined;
  let endCallRequested = false;
  let assistantText = '';

  for (let iteration = 0; iteration < MAX_TOOL_ITERATIONS; iteration++) {
    const updatedSession = await getSession(sessionId);
    const result = await config.llm.chat(
      updatedSession?.conversationHistory ?? [],
      {
        model: options?.llmModel,
        temperature: options?.llmTemperature,
        maxTokens: options?.llmMaxTokens,
        tools: llmTools,
      }
    );

    // If the LLM returned a string (legacy) or result with no tool calls
    if (typeof result === 'string') {
      assistantText = result;
      break;
    }

    const { content, toolCalls } = result;

    if (!toolCalls || toolCalls.length === 0) {
      assistantText = content ?? '';
      break;
    }

    // Add assistant message with tool calls to history
    if (content) {
      await addMessage(sessionId, { role: 'assistant', content });
    }

    // Execute each tool call
    for (const toolCall of toolCalls) {
      const toolDef = options?.tools?.find((t) => {
        if (t.type === 'FUNCTION' && t.function?.name === toolCall.name) return true;
        if (t.type === 'TRANSFER_CALL' && t.name === toolCall.name) return true;
        if (t.type === 'END_CALL' && t.name === toolCall.name) return true;
        return false;
      });

      let execResult: ToolExecutionResult;

      if (toolDef) {
        execResult = await executeTool(toolDef, toolCall.arguments, sessionId);
      } else {
        execResult = { success: false, output: `Tool "${toolCall.name}" not found` };
      }

      toolCallsExecuted.push({
        name: toolCall.name,
        arguments: toolCall.arguments,
        result: execResult,
      });

      // Add tool result to conversation
      await addMessage(sessionId, {
        role: 'tool',
        content: typeof execResult.output === 'string' ? execResult.output : JSON.stringify(execResult.output),
        name: toolCall.id,
      });

      // Handle special tool signals
      if (execResult.signal === 'transfer_call' && execResult.targetAssistantId) {
        transferRequest = { targetAssistantId: execResult.targetAssistantId };
      }
      if (execResult.signal === 'end_call') {
        endCallRequested = true;
      }
    }

    // If we got a transfer or end-call signal, stop the loop
    if (transferRequest || endCallRequested) {
      // Do one final LLM call to get a response message
      const finalSession = await getSession(sessionId);
      const finalResult = await config.llm.chat(
        finalSession?.conversationHistory ?? [],
        {
          model: options?.llmModel,
          temperature: options?.llmTemperature,
          maxTokens: options?.llmMaxTokens,
        }
      );
      assistantText = typeof finalResult === 'string' ? finalResult : (finalResult.content ?? '');
      break;
    }
  }

  // Add assistant message to conversation history
  if (assistantText) {
    await addMessage(sessionId, { role: 'assistant', content: assistantText });
  }

  // Step 3: TTS — Convert response to audio
  const textToSynthesize = assistantText || 'I understand.';
  const audioBuffer = await config.tts.synthesize(textToSynthesize, {
    voiceId: options?.ttsVoiceId,
    speed: options?.ttsSpeed,
  });

  return { userText, assistantText, audioBuffer, toolCallsExecuted, transferRequest, endCallRequested };
}

function toolToLLMFormat(tool: ToolDefinition): LLMTool {
  if (tool.type === 'FUNCTION' && tool.function) {
    return {
      type: 'function',
      function: {
        name: tool.function.name,
        description: tool.function.description ?? tool.description ?? undefined,
        parameters: tool.function.parameters,
      },
    };
  }

  // TRANSFER_CALL and END_CALL are exposed as functions the LLM can invoke
  if (tool.type === 'TRANSFER_CALL') {
    return {
      type: 'function',
      function: {
        name: tool.name,
        description: tool.description ?? 'Transfer the call to another assistant',
        parameters: {
          type: 'object',
          properties: {
            reason: { type: 'string', description: 'Reason for transfer' },
          },
        },
      },
    };
  }

  // END_CALL
  return {
    type: 'function',
    function: {
      name: tool.name,
      description: tool.description ?? 'End the current call',
      parameters: {
        type: 'object',
        properties: {
          reason: { type: 'string', description: 'Reason for ending the call' },
        },
      },
    },
  };
}
