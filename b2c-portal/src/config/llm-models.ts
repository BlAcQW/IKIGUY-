/**
 * LLM Model Configuration
 *
 * Defines all available LLM models, including fine-tuned models for Ghanaian languages.
 */

export interface LLMCapabilities {
  streaming: boolean;
  functionCalling: boolean;
  multiLanguage: boolean;
  culturalContext: boolean;
  codeGeneration?: boolean;
  reasoning?: boolean;
  vision?: boolean;
}

export interface LLMModel {
  id: string;
  name: string;
  baseModel: string;
  endpoint: string;
  status: 'online' | 'offline' | 'building' | 'training';
  languages: number;
  languageList?: string[];
  capabilities: LLMCapabilities;
  description: string;
  icon?: string;
  modelSize?: string;
  contextWindow: number;
  maxTokens?: number;
  cost?: {
    input: number; // per 1K tokens
    output: number; // per 1K tokens
  };
  fineTuned?: boolean;
  trainingData?: string;
}

export const LLM_MODELS: Record<string, LLMModel> = {
  // Google Gemini Models (Cloud API - Default)
  'gemini-2.5-flash': {
    id: 'gemini-2.5-flash',
    name: 'Gemini 2.5 Flash ⚡',
    baseModel: 'Google Gemini 2.5',
    endpoint: 'https://generativelanguage.googleapis.com/v1beta/models',
    status: 'online',
    languages: 100,
    languageList: ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'tw', 'ak', 'ar', 'zh', 'ja', 'ko', 'hi', 'ru', 'tr'],
    capabilities: {
      streaming: true,
      functionCalling: true,
      multiLanguage: true,
      culturalContext: true,
      codeGeneration: true,
      reasoning: true,
      vision: false,
    },
    description: '🌐 Google\'s fastest LLM with 1M token context. Excellent for real-time chat, code generation, and multilingual conversations. Default model for KasaAI.',
    icon: '⚡',
    modelSize: 'Cloud API',
    contextWindow: 1048576, // 1M tokens
    maxTokens: 8192,
    cost: {
      input: 0.000075, // $0.075 per 1M tokens
      output: 0.0003,   // $0.30 per 1M tokens
    },
    fineTuned: false,
  },
  'gemini-2.0-flash-exp': {
    id: 'gemini-2.0-flash-exp',
    name: 'Gemini 2.0 Flash (Experimental)',
    baseModel: 'Google Gemini 2.0',
    endpoint: 'https://generativelanguage.googleapis.com/v1beta/models',
    status: 'online',
    languages: 100,
    languageList: ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'tw', 'ak', 'ar', 'zh', 'ja', 'ko', 'hi', 'ru', 'tr'],
    capabilities: {
      streaming: true,
      functionCalling: true,
      multiLanguage: true,
      culturalContext: true,
      codeGeneration: true,
      reasoning: true,
      vision: false,
    },
    description: '🧪 Experimental Gemini 2.0 with latest features. Free tier available for testing. Great for development and experimentation.',
    icon: '🧪',
    modelSize: 'Cloud API',
    contextWindow: 1048576,
    maxTokens: 8192,
    cost: {
      input: 0.0,  // Free tier
      output: 0.0,
    },
    fineTuned: false,
  },

  // Fine-tuned Ghanaian Models (Local)
  kasaai_llama_twi: {
    id: 'kasaai_llama_twi',
    name: 'KasaAI Llama 3.2 Twi',
    baseModel: 'meta-llama/Llama-3.2-3B-Instruct',
    endpoint: 'https://ollama.ailabsafrica.com',
    status: 'training',
    languages: 2,
    languageList: ['en', 'tw'],
    capabilities: {
      streaming: true,
      functionCalling: true,
      multiLanguage: true,
      culturalContext: true,
      codeGeneration: false,
      reasoning: true,
      vision: false,
    },
    description: 'Llama 3.2 3B fine-tuned on Twi language and Ghanaian cultural context. Optimized for conversations, proverbs, and local knowledge.',
    icon: '🇬🇭',
    modelSize: '3B',
    contextWindow: 128000,
    maxTokens: 4096,
    cost: {
      input: 0.001,
      output: 0.002,
    },
    fineTuned: true,
    trainingData: 'Twi proverbs, Ghanaian cultural knowledge, local conversations (1,500+ samples)',
  },
  kasaai_aya_ghana: {
    id: 'kasaai_aya_ghana',
    name: 'KasaAI Aya-23 Ghana',
    baseModel: 'CohereForAI/aya-23-8B',
    endpoint: 'https://ollama.ailabsafrica.com',
    status: 'training',
    languages: 5,
    languageList: ['en', 'tw', 'ak', 'gaa', 'ee'],
    capabilities: {
      streaming: true,
      functionCalling: true,
      multiLanguage: true,
      culturalContext: true,
      codeGeneration: false,
      reasoning: true,
      vision: false,
    },
    description: 'Aya-23 8B fine-tuned on Ghanaian languages (Twi, Akan, Ga, Ewe). Best for multilingual Ghanaian conversations.',
    icon: '🌍',
    modelSize: '8B',
    contextWindow: 8192,
    maxTokens: 4096,
    cost: {
      input: 0.002,
      output: 0.004,
    },
    fineTuned: true,
    trainingData: 'Multi-language Ghanaian dataset (Twi, Akan, Ga, Ewe) with cultural knowledge',
  },
  kasaai_mistral_ghana: {
    id: 'kasaai_mistral_ghana',
    name: 'KasaAI Mistral 7B Ghana',
    baseModel: 'mistralai/Mistral-7B-Instruct-v0.3',
    endpoint: 'https://ollama.ailabsafrica.com',
    status: 'building',
    languages: 2,
    languageList: ['en', 'tw'],
    capabilities: {
      streaming: true,
      functionCalling: true,
      multiLanguage: true,
      culturalContext: true,
      codeGeneration: true,
      reasoning: true,
      vision: false,
    },
    description: 'Mistral 7B fine-tuned for Ghanaian context. High-quality reasoning with cultural awareness.',
    icon: '💫',
    modelSize: '7B',
    contextWindow: 32768,
    maxTokens: 4096,
    cost: {
      input: 0.0015,
      output: 0.003,
    },
    fineTuned: true,
    trainingData: 'Ghanaian cultural knowledge with advanced reasoning tasks',
  },

  // Base Models (for comparison/fallback)
  llama_32_3b: {
    id: 'llama_32_3b',
    name: 'Llama 3.2 3B (Base)',
    baseModel: 'meta-llama/Llama-3.2-3B-Instruct',
    endpoint: 'https://ollama.ailabsafrica.com',
    status: 'online',
    languages: 8,
    languageList: ['en', 'es', 'fr', 'de', 'it', 'pt', 'hi', 'th'],
    capabilities: {
      streaming: true,
      functionCalling: true,
      multiLanguage: true,
      culturalContext: false,
      codeGeneration: true,
      reasoning: true,
      vision: false,
    },
    description: 'Base Llama 3.2 3B model. Fast and efficient for general-purpose tasks.',
    icon: '🦙',
    modelSize: '3B',
    contextWindow: 128000,
    maxTokens: 4096,
    cost: {
      input: 0.001,
      output: 0.002,
    },
    fineTuned: false,
  },
  aya_23_8b: {
    id: 'aya_23_8b',
    name: 'Aya-23 8B (Base)',
    baseModel: 'CohereForAI/aya-23-8B',
    endpoint: 'https://ollama.ailabsafrica.com',
    status: 'online',
    languages: 23,
    languageList: [
      'en', 'ar', 'zh', 'cs', 'nl', 'fr', 'de', 'el', 'he', 'hi',
      'id', 'it', 'ja', 'ko', 'pl', 'pt', 'ro', 'ru', 'es', 'tr',
      'uk', 'vi', 'yo',
    ],
    capabilities: {
      streaming: true,
      functionCalling: true,
      multiLanguage: true,
      culturalContext: false,
      codeGeneration: false,
      reasoning: true,
      vision: false,
    },
    description: 'Base Aya-23 8B model. Excellent multilingual performance across 23 languages.',
    icon: '🌐',
    modelSize: '8B',
    contextWindow: 8192,
    maxTokens: 4096,
    cost: {
      input: 0.002,
      output: 0.004,
    },
    fineTuned: false,
  },
  mistral_7b: {
    id: 'mistral_7b',
    name: 'Mistral 7B (Base)',
    baseModel: 'mistralai/Mistral-7B-Instruct-v0.3',
    endpoint: 'https://ollama.ailabsafrica.com',
    status: 'online',
    languages: 5,
    languageList: ['en', 'es', 'fr', 'de', 'it'],
    capabilities: {
      streaming: true,
      functionCalling: true,
      multiLanguage: true,
      culturalContext: false,
      codeGeneration: true,
      reasoning: true,
      vision: false,
    },
    description: 'Base Mistral 7B model. High-quality reasoning and code generation.',
    icon: '🌬️',
    modelSize: '7B',
    contextWindow: 32768,
    maxTokens: 4096,
    cost: {
      input: 0.0015,
      output: 0.003,
    },
    fineTuned: false,
  },

  // Specialized Models
  llama_32_vision: {
    id: 'llama_32_vision',
    name: 'Llama 3.2 11B Vision',
    baseModel: 'meta-llama/Llama-3.2-11B-Vision-Instruct',
    endpoint: 'https://ollama.ailabsafrica.com',
    status: 'building',
    languages: 8,
    languageList: ['en', 'es', 'fr', 'de', 'it', 'pt', 'hi', 'th'],
    capabilities: {
      streaming: true,
      functionCalling: true,
      multiLanguage: true,
      culturalContext: false,
      codeGeneration: false,
      reasoning: true,
      vision: true,
    },
    description: 'Llama 3.2 with vision capabilities. Analyze images and generate descriptions.',
    icon: '👁️',
    modelSize: '11B',
    contextWindow: 128000,
    maxTokens: 4096,
    cost: {
      input: 0.003,
      output: 0.006,
    },
    fineTuned: false,
  },
  deepseek_coder: {
    id: 'deepseek_coder',
    name: 'DeepSeek Coder 6.7B',
    baseModel: 'deepseek-ai/deepseek-coder-6.7b-instruct',
    endpoint: 'https://ollama.ailabsafrica.com',
    status: 'building',
    languages: 1,
    languageList: ['en'],
    capabilities: {
      streaming: true,
      functionCalling: true,
      multiLanguage: false,
      culturalContext: false,
      codeGeneration: true,
      reasoning: true,
      vision: false,
    },
    description: 'Specialized for code generation and programming tasks. Supports 80+ programming languages.',
    icon: '💻',
    modelSize: '6.7B',
    contextWindow: 16384,
    maxTokens: 4096,
    cost: {
      input: 0.001,
      output: 0.002,
    },
    fineTuned: false,
  },
};

/**
 * Get LLM models by status
 */
export const getLLMModelsByStatus = (status: 'online' | 'offline' | 'building' | 'training') => {
  return Object.values(LLM_MODELS).filter(model => model.status === status);
};

/**
 * Get LLM models with specific capability
 */
export const getLLMModelsByCapability = (capability: keyof LLMCapabilities) => {
  return Object.values(LLM_MODELS).filter(
    model => model.capabilities[capability] === true
  );
};

/**
 * Get fine-tuned Ghanaian models
 */
export const getGhanaianModels = () => {
  return Object.values(LLM_MODELS).filter(model => model.fineTuned === true);
};

/**
 * Get models by context window size
 */
export const getLLMModelsByContextSize = (minContext: number) => {
  return Object.values(LLM_MODELS).filter(model => model.contextWindow >= minContext);
};

/**
 * Get culturally-aware models
 */
export const getCulturalModels = () => {
  return getLLMModelsByCapability('culturalContext');
};
