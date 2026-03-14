import { config } from '../config/index.js';
import type { STTProvider } from './stt/types.js';
import type { TTSProvider } from './tts/types.js';
import type { LLMProvider } from './llm/types.js';
import type { PipelineConfig } from '../voice-pipeline/pipeline.js';
import { OpenAISTTProvider } from './stt/openai.js';
import { DeepgramSTTProvider } from './stt/deepgram.js';
import { OpenAITTSProvider } from './tts/openai.js';
import { ElevenLabsTTSProvider } from './tts/elevenlabs.js';
import { DeepgramTTSProvider } from './tts/deepgram.js';
import { CartesiaTTSProvider } from './tts/cartesia.js';
import { OpenAILLMProvider } from './llm/openai.js';
import { GoogleLLMProvider } from './llm/google.js';
import { AnthropicLLMProvider } from './llm/anthropic.js';

// ---------------------------------------------------------------------------
// Org-level credential overrides
// ---------------------------------------------------------------------------
// When an organization has configured provider API keys in their settings,
// those keys are passed here as `orgCredentials`.  The resolution order is:
//   1. Org-level credential (if provided)
//   2. Server-level environment variable
//   3. Throw an error

export interface OrgCredentials {
  openaiApiKey?: string;
  deepgramApiKey?: string;
  elevenLabsApiKey?: string;
  cartesiaApiKey?: string;
  googleAiApiKey?: string;
  anthropicApiKey?: string;
}

// ---------------------------------------------------------------------------
// Provider factories
// ---------------------------------------------------------------------------
// Each factory accepts an optional `apiKeyOverride` that takes precedence
// over the server env var, enabling org-specific credentials.

export function createSTTProvider(provider: string, apiKeyOverride?: string): STTProvider {
  switch (provider) {
    case 'openai': {
      const key = apiKeyOverride ?? config.OPENAI_API_KEY;
      if (!key) {
        throw new Error('OPENAI_API_KEY is required for OpenAI STT provider');
      }
      return new OpenAISTTProvider(key);
    }
    case 'deepgram': {
      const key = apiKeyOverride ?? config.DEEPGRAM_API_KEY;
      if (!key) {
        throw new Error('DEEPGRAM_API_KEY is required for Deepgram STT provider');
      }
      return new DeepgramSTTProvider(key);
    }
    default:
      throw new Error(`Unknown STT provider: ${provider}`);
  }
}

export function createTTSProvider(provider: string, apiKeyOverride?: string): TTSProvider {
  switch (provider) {
    case 'openai': {
      const key = apiKeyOverride ?? config.OPENAI_API_KEY;
      if (!key) {
        throw new Error('OPENAI_API_KEY is required for OpenAI TTS provider');
      }
      return new OpenAITTSProvider(key);
    }
    case 'elevenlabs': {
      const key = apiKeyOverride ?? config.ELEVENLABS_API_KEY;
      if (!key) {
        throw new Error('ELEVENLABS_API_KEY is required for ElevenLabs TTS provider');
      }
      return new ElevenLabsTTSProvider(key);
    }
    case 'deepgram': {
      const key = apiKeyOverride ?? config.DEEPGRAM_API_KEY;
      if (!key) {
        throw new Error('DEEPGRAM_API_KEY is required for Deepgram TTS provider');
      }
      return new DeepgramTTSProvider(key);
    }
    case 'cartesia': {
      const key = apiKeyOverride ?? config.CARTESIA_API_KEY;
      if (!key) {
        throw new Error('CARTESIA_API_KEY is required for Cartesia TTS provider');
      }
      return new CartesiaTTSProvider(key);
    }
    default:
      throw new Error(`Unknown TTS provider: ${provider}`);
  }
}

export function createLLMProvider(provider: string, apiKeyOverride?: string): LLMProvider {
  switch (provider) {
    case 'openai': {
      const key = apiKeyOverride ?? config.OPENAI_API_KEY;
      if (!key) {
        throw new Error('OPENAI_API_KEY is required for OpenAI LLM provider');
      }
      return new OpenAILLMProvider(key);
    }
    case 'google': {
      const key = apiKeyOverride ?? config.GOOGLE_AI_API_KEY;
      if (!key) {
        throw new Error('GOOGLE_AI_API_KEY is required for Google LLM provider. Add it in Settings > Provider Credentials or set the GOOGLE_AI_API_KEY environment variable.');
      }
      return new GoogleLLMProvider(key);
    }
    case 'anthropic': {
      const key = apiKeyOverride ?? config.ANTHROPIC_API_KEY;
      if (!key) {
        throw new Error('ANTHROPIC_API_KEY is required for Anthropic LLM provider. Add it in Settings > Provider Credentials or set the ANTHROPIC_API_KEY environment variable.');
      }
      return new AnthropicLLMProvider(key);
    }
    default:
      throw new Error(`Unknown LLM provider: ${provider}`);
  }
}

// ---------------------------------------------------------------------------
// Pipeline builder
// ---------------------------------------------------------------------------
// Resolves the correct API key for each provider in the pipeline.  When
// `orgCredentials` are provided (from the org's settings), they override
// server-level env vars so each org can bring their own keys.

/** Map a provider name to the matching org credential key. */
function resolveKey(
  providerName: string,
  orgCredentials?: OrgCredentials,
): string | undefined {
  if (!orgCredentials) return undefined;

  switch (providerName) {
    case 'openai':
      return orgCredentials.openaiApiKey;
    case 'deepgram':
      return orgCredentials.deepgramApiKey;
    case 'elevenlabs':
      return orgCredentials.elevenLabsApiKey;
    case 'cartesia':
      return orgCredentials.cartesiaApiKey;
    case 'google':
      return orgCredentials.googleAiApiKey;
    case 'anthropic':
      return orgCredentials.anthropicApiKey;
    default:
      return undefined;
  }
}

export function buildPipelineFromAssistant(
  assistant: { model: unknown; voice: unknown; transcriber: unknown },
  orgCredentials?: OrgCredentials,
): PipelineConfig {
  const llmProviderName = (assistant.model as { provider?: string })?.provider ?? 'openai';
  const ttsProviderName = (assistant.voice as { provider?: string })?.provider ?? 'openai';
  const sttProviderName = (assistant.transcriber as { provider?: string })?.provider ?? 'openai';

  // Resolve org-level keys for each provider
  const stt = createSTTProvider(sttProviderName, resolveKey(sttProviderName, orgCredentials));
  const llm = createLLMProvider(llmProviderName, resolveKey(llmProviderName, orgCredentials));
  const tts = createTTSProvider(ttsProviderName, resolveKey(ttsProviderName, orgCredentials));

  return { stt, llm, tts };
}
