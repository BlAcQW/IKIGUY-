import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createSession, getSession } from './session.js';
import { processPipelineTurn, type PipelineConfig } from './pipeline.js';
import type { CallSession } from './session.js';
import type { LLMChatResult } from '../providers/llm/types.js';
import type { ToolExecutionResult } from './tool-executor.js';

vi.mock('./tool-executor.js', () => ({
  executeTool: vi.fn(),
}));

import { executeTool } from './tool-executor.js';
const mockExecuteTool = vi.mocked(executeTool);

function createMockPipeline(): PipelineConfig {
  return {
    stt: {
      name: 'mock-stt',
      transcribe: vi.fn().mockResolvedValue('Hello from user'),
    },
    llm: {
      name: 'mock-llm',
      chat: vi.fn().mockResolvedValue('Hello from assistant'),
      chatStream: vi.fn(),
    },
    tts: {
      name: 'mock-tts',
      synthesize: vi.fn().mockResolvedValue(Buffer.from('fake-audio')),
    },
  };
}

describe('processPipelineTurn', () => {
  let session: CallSession;
  let pipeline: PipelineConfig;

  beforeEach(async () => {
    session = await createSession({
      callId: 'call-1',
      assistantId: 'ast-1',
      organizationId: 'org-1',
      systemPrompt: 'You are helpful',
    });
    pipeline = createMockPipeline();
    mockExecuteTool.mockReset();
  });

  it('processes audio through STT -> LLM -> TTS', async () => {
    const audioInput = Buffer.from('raw-audio');

    const result = await processPipelineTurn(session.id, audioInput, pipeline);

    expect(result.userText).toBe('Hello from user');
    expect(result.assistantText).toBe('Hello from assistant');
    expect(Buffer.isBuffer(result.audioBuffer)).toBe(true);
  });

  it('calls STT with audio input', async () => {
    const audioInput = Buffer.from('audio-data');

    await processPipelineTurn(session.id, audioInput, pipeline);

    expect(pipeline.stt.transcribe).toHaveBeenCalledWith(audioInput, {
      model: undefined,
      language: undefined,
    });
  });

  it('calls LLM with conversation history including user message', async () => {
    await processPipelineTurn(session.id, Buffer.from('audio'), pipeline);

    const llmCall = vi.mocked(pipeline.llm.chat).mock.calls[0];
    const messages = llmCall[0];

    // Should contain system prompt + user message
    expect(messages[0]).toEqual({ role: 'system', content: 'You are helpful' });
    expect(messages[1]).toEqual({ role: 'user', content: 'Hello from user' });
  });

  it('calls TTS with assistant response', async () => {
    await processPipelineTurn(session.id, Buffer.from('audio'), pipeline);

    expect(pipeline.tts.synthesize).toHaveBeenCalledWith('Hello from assistant', {
      voiceId: undefined,
      speed: undefined,
    });
  });

  it('adds both user and assistant messages to session history', async () => {
    await processPipelineTurn(session.id, Buffer.from('audio'), pipeline);

    const updated = await getSession(session.id);
    expect(updated?.conversationHistory).toHaveLength(3); // system + user + assistant
    expect(updated?.conversationHistory[1]).toEqual({ role: 'user', content: 'Hello from user' });
    expect(updated?.conversationHistory[2]).toEqual({ role: 'assistant', content: 'Hello from assistant' });
  });

  it('passes pipeline options when provided', async () => {
    await processPipelineTurn(session.id, Buffer.from('audio'), pipeline, {
      sttModel: 'whisper-1',
      sttLanguage: 'fr',
      llmModel: 'gpt-4-turbo',
      llmTemperature: 0.3,
      llmMaxTokens: 2000,
      ttsVoiceId: 'nova',
      ttsSpeed: 1.5,
    });

    expect(pipeline.stt.transcribe).toHaveBeenCalledWith(expect.anything(), {
      model: 'whisper-1',
      language: 'fr',
    });
    expect(pipeline.llm.chat).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({
      model: 'gpt-4-turbo',
      temperature: 0.3,
      maxTokens: 2000,
    }));
    expect(pipeline.tts.synthesize).toHaveBeenCalledWith(expect.anything(), {
      voiceId: 'nova',
      speed: 1.5,
    });
  });

  it('throws when session not found', async () => {
    await expect(
      processPipelineTurn('nonexistent', Buffer.from('audio'), pipeline)
    ).rejects.toThrow('Session nonexistent not found');
  });

  it('handles multiple turns with accumulating history', async () => {
    await processPipelineTurn(session.id, Buffer.from('audio1'), pipeline);

    // Second turn
    vi.mocked(pipeline.stt.transcribe).mockResolvedValue('Second message');
    vi.mocked(pipeline.llm.chat).mockResolvedValue('Second response');

    await processPipelineTurn(session.id, Buffer.from('audio2'), pipeline);

    const updated = await getSession(session.id);
    // system + user1 + assistant1 + user2 + assistant2
    expect(updated?.conversationHistory).toHaveLength(5);
  });

  it('returns tool call metadata', async () => {
    const result = await processPipelineTurn(session.id, Buffer.from('audio'), pipeline);

    expect(result.toolCallsExecuted).toEqual([]);
    expect(result.endCallRequested).toBe(false);
    expect(result.transferRequest).toBeUndefined();
  });

  describe('tool execution', () => {
    const functionTool = {
      id: 'tool-1',
      type: 'FUNCTION' as const,
      name: 'check_availability',
      function: { name: 'check_availability', description: 'Check availability', parameters: {} },
      serverUrl: 'https://example.com/hook',
      serverSecret: null,
    };

    const transferTool = {
      id: 'tool-2',
      type: 'TRANSFER_CALL' as const,
      name: 'transfer_to_sales',
      description: 'Transfer to sales',
      metadata: { targetAssistantId: 'ast-sales' },
      serverUrl: null,
      serverSecret: null,
    };

    const endCallTool = {
      id: 'tool-3',
      type: 'END_CALL' as const,
      name: 'end_call',
      description: 'End the call',
      serverUrl: null,
      serverSecret: null,
    };

    it('executes a single tool call and returns final text', async () => {
      const llmChat = vi.mocked(pipeline.llm.chat);
      // First call: LLM returns tool call
      llmChat.mockResolvedValueOnce({
        content: null,
        toolCalls: [{ id: 'tc-1', name: 'check_availability', arguments: '{"date":"2026-01-01"}' }],
      } satisfies LLMChatResult);
      // Second call: LLM returns text after tool result
      llmChat.mockResolvedValueOnce({
        content: 'The date is available!',
        toolCalls: [],
      } satisfies LLMChatResult);

      mockExecuteTool.mockResolvedValueOnce({ success: true, output: 'available' });

      const result = await processPipelineTurn(session.id, Buffer.from('audio'), pipeline, {
        tools: [functionTool],
      });

      expect(result.assistantText).toBe('The date is available!');
      expect(result.toolCallsExecuted).toHaveLength(1);
      expect(result.toolCallsExecuted[0].name).toBe('check_availability');
      expect(result.toolCallsExecuted[0].result.success).toBe(true);
      expect(mockExecuteTool).toHaveBeenCalledOnce();
    });

    it('executes multiple tool calls in one turn', async () => {
      const llmChat = vi.mocked(pipeline.llm.chat);
      llmChat.mockResolvedValueOnce({
        content: null,
        toolCalls: [
          { id: 'tc-1', name: 'check_availability', arguments: '{"date":"2026-01-01"}' },
          { id: 'tc-2', name: 'check_availability', arguments: '{"date":"2026-01-02"}' },
        ],
      } satisfies LLMChatResult);
      llmChat.mockResolvedValueOnce({
        content: 'Both dates are available.',
        toolCalls: [],
      } satisfies LLMChatResult);

      mockExecuteTool
        .mockResolvedValueOnce({ success: true, output: 'available' })
        .mockResolvedValueOnce({ success: true, output: 'available' });

      const result = await processPipelineTurn(session.id, Buffer.from('audio'), pipeline, {
        tools: [functionTool],
      });

      expect(result.assistantText).toBe('Both dates are available.');
      expect(result.toolCallsExecuted).toHaveLength(2);
      expect(mockExecuteTool).toHaveBeenCalledTimes(2);
    });

    it('handles tool chaining across 2 iterations', async () => {
      const llmChat = vi.mocked(pipeline.llm.chat);
      // Iteration 1: LLM returns tool call
      llmChat.mockResolvedValueOnce({
        content: null,
        toolCalls: [{ id: 'tc-1', name: 'check_availability', arguments: '{"date":"2026-01-01"}' }],
      } satisfies LLMChatResult);
      // Iteration 2: LLM returns another tool call based on first result
      llmChat.mockResolvedValueOnce({
        content: null,
        toolCalls: [{ id: 'tc-2', name: 'check_availability', arguments: '{"date":"2026-01-02"}' }],
      } satisfies LLMChatResult);
      // Iteration 3: LLM returns final text
      llmChat.mockResolvedValueOnce({
        content: 'I found availability on Jan 2.',
        toolCalls: [],
      } satisfies LLMChatResult);

      mockExecuteTool
        .mockResolvedValueOnce({ success: true, output: 'not available' })
        .mockResolvedValueOnce({ success: true, output: 'available' });

      const result = await processPipelineTurn(session.id, Buffer.from('audio'), pipeline, {
        tools: [functionTool],
      });

      expect(result.assistantText).toBe('I found availability on Jan 2.');
      expect(result.toolCallsExecuted).toHaveLength(2);
      expect(llmChat).toHaveBeenCalledTimes(3);
    });

    it('stops at MAX_TOOL_ITERATIONS (5) when LLM keeps returning tool calls', async () => {
      const llmChat = vi.mocked(pipeline.llm.chat);
      // All 5 iterations return tool calls — never returns text
      for (let i = 0; i < 5; i++) {
        llmChat.mockResolvedValueOnce({
          content: null,
          toolCalls: [{ id: `tc-${i}`, name: 'check_availability', arguments: '{}' }],
        } satisfies LLMChatResult);
      }

      mockExecuteTool.mockResolvedValue({ success: true, output: 'looping' });

      const result = await processPipelineTurn(session.id, Buffer.from('audio'), pipeline, {
        tools: [functionTool],
      });

      expect(result.toolCallsExecuted).toHaveLength(5);
      expect(result.assistantText).toBe('');
      expect(llmChat).toHaveBeenCalledTimes(5);
    });

    it('handles transfer_call signal — stops loop and sets transferRequest', async () => {
      const llmChat = vi.mocked(pipeline.llm.chat);
      llmChat.mockResolvedValueOnce({
        content: null,
        toolCalls: [{ id: 'tc-1', name: 'transfer_to_sales', arguments: '{"reason":"needs sales"}' }],
      } satisfies LLMChatResult);
      // Final LLM call for farewell message
      llmChat.mockResolvedValueOnce({
        content: 'Let me transfer you to our sales team.',
        toolCalls: [],
      } satisfies LLMChatResult);

      mockExecuteTool.mockResolvedValueOnce({
        success: true,
        output: 'Transferring call to assistant. Reason: needs sales',
        signal: 'transfer_call',
        targetAssistantId: 'ast-sales',
      });

      const result = await processPipelineTurn(session.id, Buffer.from('audio'), pipeline, {
        tools: [transferTool],
      });

      expect(result.transferRequest).toEqual({ targetAssistantId: 'ast-sales' });
      expect(result.assistantText).toBe('Let me transfer you to our sales team.');
      expect(result.endCallRequested).toBe(false);
    });

    it('handles end_call signal — stops loop and sets endCallRequested', async () => {
      const llmChat = vi.mocked(pipeline.llm.chat);
      llmChat.mockResolvedValueOnce({
        content: null,
        toolCalls: [{ id: 'tc-1', name: 'end_call', arguments: '{"reason":"resolved"}' }],
      } satisfies LLMChatResult);
      // Final LLM call for goodbye
      llmChat.mockResolvedValueOnce({
        content: 'Goodbye! Have a great day.',
        toolCalls: [],
      } satisfies LLMChatResult);

      mockExecuteTool.mockResolvedValueOnce({
        success: true,
        output: 'Ending call. Reason: resolved',
        signal: 'end_call',
      });

      const result = await processPipelineTurn(session.id, Buffer.from('audio'), pipeline, {
        tools: [endCallTool],
      });

      expect(result.endCallRequested).toBe(true);
      expect(result.assistantText).toBe('Goodbye! Have a great day.');
      expect(result.transferRequest).toBeUndefined();
    });

    it('handles tool not found — records failure and continues', async () => {
      const llmChat = vi.mocked(pipeline.llm.chat);
      llmChat.mockResolvedValueOnce({
        content: null,
        toolCalls: [{ id: 'tc-1', name: 'nonexistent_tool', arguments: '{}' }],
      } satisfies LLMChatResult);
      llmChat.mockResolvedValueOnce({
        content: 'Sorry, I could not complete that action.',
        toolCalls: [],
      } satisfies LLMChatResult);

      const result = await processPipelineTurn(session.id, Buffer.from('audio'), pipeline, {
        tools: [functionTool],
      });

      expect(result.toolCallsExecuted).toHaveLength(1);
      expect(result.toolCallsExecuted[0].result.success).toBe(false);
      expect(result.toolCallsExecuted[0].result.output).toContain('not found');
      // executeTool should NOT be called for unknown tool
      expect(mockExecuteTool).not.toHaveBeenCalled();
      expect(result.assistantText).toBe('Sorry, I could not complete that action.');
    });

    it('handles tool execution failure — records error and continues', async () => {
      const llmChat = vi.mocked(pipeline.llm.chat);
      llmChat.mockResolvedValueOnce({
        content: null,
        toolCalls: [{ id: 'tc-1', name: 'check_availability', arguments: '{}' }],
      } satisfies LLMChatResult);
      llmChat.mockResolvedValueOnce({
        content: 'The service is currently unavailable.',
        toolCalls: [],
      } satisfies LLMChatResult);

      mockExecuteTool.mockResolvedValueOnce({
        success: false,
        output: 'Tool execution failed: Connection refused',
      });

      const result = await processPipelineTurn(session.id, Buffer.from('audio'), pipeline, {
        tools: [functionTool],
      });

      expect(result.toolCallsExecuted).toHaveLength(1);
      expect(result.toolCallsExecuted[0].result.success).toBe(false);
      expect(result.toolCallsExecuted[0].result.output).toContain('Connection refused');
      expect(result.assistantText).toBe('The service is currently unavailable.');
    });

    it('skips tool loop when no tools are provided', async () => {
      const result = await processPipelineTurn(session.id, Buffer.from('audio'), pipeline);

      expect(result.assistantText).toBe('Hello from assistant');
      expect(result.toolCallsExecuted).toEqual([]);
      expect(mockExecuteTool).not.toHaveBeenCalled();
    });
  });
});
