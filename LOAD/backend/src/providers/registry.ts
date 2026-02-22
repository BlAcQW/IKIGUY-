import { config } from '../config/index.js';
import type { STTProvider } from './stt/types.js';
import type { TTSProvider } from './tts/types.js';
import type { LLMProvider } from './llm/types.js';
import type { PipelineConfig } from '../voice-pipeline/pipeline.js';
import { OpenAISTTProvider } from './stt/openai.js';
import { DeepgramSTTProvider } from './stt/deepgram.js';
import { OpenAITTSProvider } from './tts/openai.js';
import { ElevenLabsTTSProvider } from './tts/elevenlabs.js';
import { OpenAILLMProvider } from './llm/openai.js';

export function createSTTProvider(provider: string): STTProvider {
  switch (provider) {
    case 'openai': {
      if (!config.OPENAI_API_KEY) {
        throw new Error('OPENAI_API_KEY is required for OpenAI STT provider');
      }
      return new OpenAISTTProvider(config.OPENAI_API_KEY);
    }
    case 'deepgram': {
      if (!config.DEEPGRAM_API_KEY) {
        throw new Error('DEEPGRAM_API_KEY is required for Deepgram STT provider');
      }
      return new DeepgramSTTProvider(config.DEEPGRAM_API_KEY);
    }
    default:
      throw new Error(`Unknown STT provider: ${provider}`);
  }
}

export function createTTSProvider(provider: string): TTSProvider {
  switch (provider) {
    case 'openai': {
      if (!config.OPENAI_API_KEY) {
        throw new Error('OPENAI_API_KEY is required for OpenAI TTS provider');
      }
      return new OpenAITTSProvider(config.OPENAI_API_KEY);
    }
    case 'elevenlabs': {
      if (!config.ELEVENLABS_API_KEY) {
        throw new Error('ELEVENLABS_API_KEY is required for ElevenLabs TTS provider');
      }
      return new ElevenLabsTTSProvider(config.ELEVENLABS_API_KEY);
    }
    default:
      throw new Error(`Unknown TTS provider: ${provider}`);
  }
}

export function createLLMProvider(provider: string): LLMProvider {
  switch (provider) {
    case 'openai': {
      if (!config.OPENAI_API_KEY) {
        throw new Error('OPENAI_API_KEY is required for OpenAI LLM provider');
      }
      return new OpenAILLMProvider(config.OPENAI_API_KEY);
    }
    default:
      throw new Error(`Unknown LLM provider: ${provider}`);
  }
}

export function buildPipelineFromAssistant(assistant: {
  model: unknown;
  voice: unknown;
  transcriber: unknown;
}): PipelineConfig {
  const llmProviderName = (assistant.model as { provider?: string })?.provider ?? 'openai';
  const ttsProviderName = (assistant.voice as { provider?: string })?.provider ?? 'openai';
  const sttProviderName = (assistant.transcriber as { provider?: string })?.provider ?? 'openai';

  const stt = createSTTProvider(sttProviderName);
  const llm = createLLMProvider(llmProviderName);
  const tts = createTTSProvider(ttsProviderName);

  return { stt, llm, tts };
}
