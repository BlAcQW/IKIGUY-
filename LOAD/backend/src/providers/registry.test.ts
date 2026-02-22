import { describe, it, expect, vi, beforeEach } from 'vitest';

// ---------------------------------------------------------------------------
// Mocks — must be declared before importing the module under test
// ---------------------------------------------------------------------------

vi.mock('../config/index.js', () => ({
  config: {
    OPENAI_API_KEY: 'test-key',
    DEEPGRAM_API_KEY: 'test-deepgram-key',
    ELEVENLABS_API_KEY: 'test-elevenlabs-key',
  },
}));

vi.mock('./stt/openai.js', () => ({
  OpenAISTTProvider: vi.fn().mockImplementation(() => ({
    name: 'openai-whisper',
    transcribe: vi.fn(),
  })),
}));

vi.mock('./stt/deepgram.js', () => ({
  DeepgramSTTProvider: vi.fn().mockImplementation(() => ({
    name: 'deepgram-nova',
    transcribe: vi.fn(),
  })),
}));

vi.mock('./tts/openai.js', () => ({
  OpenAITTSProvider: vi.fn().mockImplementation(() => ({
    name: 'openai-tts',
    synthesize: vi.fn(),
  })),
}));

vi.mock('./tts/elevenlabs.js', () => ({
  ElevenLabsTTSProvider: vi.fn().mockImplementation(() => ({
    name: 'elevenlabs',
    synthesize: vi.fn(),
  })),
}));

vi.mock('./llm/openai.js', () => ({
  OpenAILLMProvider: vi.fn().mockImplementation(() => ({
    name: 'openai-gpt',
    chat: vi.fn(),
    chatStream: async function* () {},
  })),
}));

import {
  createSTTProvider,
  createTTSProvider,
  createLLMProvider,
  buildPipelineFromAssistant,
} from './registry.js';

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('createSTTProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns OpenAI provider', () => {
    const provider = createSTTProvider('openai');

    expect(provider.name).toBe('openai-whisper');
  });

  it('returns Deepgram provider', () => {
    const provider = createSTTProvider('deepgram');

    expect(provider.name).toBe('deepgram-nova');
  });

  it('throws on unknown provider', () => {
    expect(() => createSTTProvider('unknown')).toThrow('Unknown STT provider: unknown');
  });
});

describe('createTTSProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns OpenAI provider', () => {
    const provider = createTTSProvider('openai');

    expect(provider.name).toBe('openai-tts');
  });

  it('returns ElevenLabs provider', () => {
    const provider = createTTSProvider('elevenlabs');

    expect(provider.name).toBe('elevenlabs');
  });

  it('throws on unknown provider', () => {
    expect(() => createTTSProvider('unknown')).toThrow('Unknown TTS provider: unknown');
  });
});

describe('createLLMProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns OpenAI provider', () => {
    const provider = createLLMProvider('openai');

    expect(provider.name).toBe('openai-gpt');
  });

  it('throws on unknown provider', () => {
    expect(() => createLLMProvider('unknown')).toThrow('Unknown LLM provider: unknown');
  });
});

describe('buildPipelineFromAssistant', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('builds pipeline with correct providers', () => {
    const assistant = {
      model: { provider: 'openai', model: 'gpt-4' },
      voice: { provider: 'elevenlabs', voiceId: 'rachel' },
      transcriber: { provider: 'deepgram', model: 'nova-2' },
    };

    const pipeline = buildPipelineFromAssistant(assistant);

    expect(pipeline.stt.name).toBe('deepgram-nova');
    expect(pipeline.llm.name).toBe('openai-gpt');
    expect(pipeline.tts.name).toBe('elevenlabs');
  });

  it('defaults to OpenAI when no provider specified', () => {
    const assistant = {
      model: {},
      voice: {},
      transcriber: {},
    };

    const pipeline = buildPipelineFromAssistant(assistant);

    expect(pipeline.stt.name).toBe('openai-whisper');
    expect(pipeline.llm.name).toBe('openai-gpt');
    expect(pipeline.tts.name).toBe('openai-tts');
  });

  it('defaults to OpenAI when JSONB fields are null', () => {
    const assistant = {
      model: null as unknown,
      voice: null as unknown,
      transcriber: null as unknown,
    };

    const pipeline = buildPipelineFromAssistant(assistant);

    expect(pipeline.stt.name).toBe('openai-whisper');
    expect(pipeline.llm.name).toBe('openai-gpt');
    expect(pipeline.tts.name).toBe('openai-tts');
  });

  it('returns a PipelineConfig with stt, llm, and tts properties', () => {
    const assistant = {
      model: { provider: 'openai' },
      voice: { provider: 'openai' },
      transcriber: { provider: 'openai' },
    };

    const pipeline = buildPipelineFromAssistant(assistant);

    expect(pipeline).toHaveProperty('stt');
    expect(pipeline).toHaveProperty('llm');
    expect(pipeline).toHaveProperty('tts');
  });
});
