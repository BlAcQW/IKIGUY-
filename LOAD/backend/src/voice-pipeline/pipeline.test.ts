import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createSession, getSession } from './session.js';
import { processPipelineTurn, type PipelineConfig } from './pipeline.js';
import type { CallSession } from './session.js';

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
});
