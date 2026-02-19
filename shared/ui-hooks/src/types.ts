/**
 * Shared types for AI services hooks
 */

/**
 * AI provider types
 */
export type ProviderType = 'tts' | 'llm' | 'asr' | 'vision' | 'embedding' | 'multimodal';

/**
 * Provider status
 */
export type ProviderStatus = 'online' | 'offline' | 'degraded' | 'building' | 'maintenance';

/**
 * Provider capabilities
 */
export interface ProviderCapabilities {
  // Generic capabilities
  multiLanguage?: boolean;
  streaming?: boolean;
  realtime?: boolean;

  // TTS-specific
  voiceCloning?: boolean;
  speedControl?: boolean;
  pitchControl?: boolean;
  multiSpeaker?: boolean;
  emotionControl?: boolean;

  // LLM-specific
  functionCalling?: boolean;
  reasoning?: boolean;
  codeGeneration?: boolean;
  vision?: boolean;
  culturalContext?: boolean;

  // ASR-specific
  diarization?: boolean;
  timestamps?: boolean;
  wordLevelTimestamps?: boolean;
  punctuation?: boolean;

  // Custom capabilities
  [key: string]: boolean | undefined;
}

/**
 * AI Provider
 */
export interface AIProvider {
  id: string;
  name: string;
  provider_type: ProviderType;
  endpoint: string;
  status: ProviderStatus;
  capabilities: ProviderCapabilities;
  description: string;
  icon: string;
  languages: number;
  languageList: string[];
  metadata?: Record<string, any>;
  lastChecked?: string;
  responseTime?: number;
}

/**
 * Hook options
 */
export interface UseAIProviderOptions {
  /**
   * API base URL
   * @default process.env.VITE_API_URL || 'http://localhost:8000'
   */
  apiUrl?: string;

  /**
   * Auto-refresh interval in milliseconds
   * @default 60000 (1 minute)
   */
  refreshInterval?: number;

  /**
   * Enable auto-refresh
   * @default true
   */
  autoRefresh?: boolean;

  /**
   * Initial provider ID to select
   */
  initialProviderId?: string;

  /**
   * Callback when provider selection changes
   */
  onProviderChange?: (provider: AIProvider | null) => void;

  /**
   * Callback when providers are fetched
   */
  onProvidersLoaded?: (providers: Record<string, AIProvider>) => void;

  /**
   * Callback on error
   */
  onError?: (error: Error) => void;
}

/**
 * Return type for useAIProvider hook
 */
export interface UseAIProviderReturn {
  /**
   * Map of all providers by ID
   */
  providers: Record<string, AIProvider>;

  /**
   * Currently selected provider
   */
  selectedProvider: AIProvider | null;

  /**
   * Set the selected provider
   */
  setSelectedProvider: (provider: AIProvider | null) => void;

  /**
   * Select provider by ID
   */
  selectProviderById: (providerId: string) => void;

  /**
   * Loading state
   */
  loading: boolean;

  /**
   * Error state
   */
  error: Error | null;

  /**
   * Manually refresh providers
   */
  refetch: () => Promise<void>;

  /**
   * Get providers by status
   */
  getProvidersByStatus: (status: ProviderStatus) => AIProvider[];

  /**
   * Get providers by capability
   */
  getProvidersByCapability: (capability: string) => AIProvider[];

  /**
   * Get online providers
   */
  getOnlineProviders: () => AIProvider[];
}
