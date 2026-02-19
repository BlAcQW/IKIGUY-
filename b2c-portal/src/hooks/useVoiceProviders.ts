/**
 * Hook to fetch TTS, ASR, and LLM providers for voice settings
 */

import { useState, useEffect } from 'react';
import { TTSProviderInfo } from '@kasaai/shared-frontend/components/voice-settings/ComprehensiveTTSSelector';
import { ASRProvider } from '@kasaai/shared-frontend/components/voice-settings/ASRProviderSelector';
import { LLMModel } from '@kasaai/shared-frontend/components/voice-settings/LLMModelSelector';
import { ClonedVoice } from '@kasaai/shared-frontend/components/voice-settings/VoiceLibrarySelector';

export interface UseVoiceProvidersResult {
  ttsProviders: TTSProviderInfo[];
  asrProviders: ASRProvider[];
  llmModels: LLMModel[];
  clonedVoices: ClonedVoice[];
  isLoading: boolean;
  error: string | null;
}

export function useVoiceProviders(apiBaseUrl: string): UseVoiceProvidersResult {
  const [ttsProviders, setTtsProviders] = useState<TTSProviderInfo[]>([]);
  const [asrProviders, setAsrProviders] = useState<ASRProvider[]>([]);
  const [llmModels, setLlmModels] = useState<LLMModel[]>([]);
  const [clonedVoices, setClonedVoices] = useState<ClonedVoice[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProviders = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Fetch TTS providers - using same endpoint as inkwave
        const ttsResponse = await fetch(`${apiBaseUrl}/api/tts/providers`);
        if (ttsResponse.ok) {
          const ttsData = await ttsResponse.json();
          // Handle both array and object formats
          const providersArray = Array.isArray(ttsData.providers) 
            ? ttsData.providers 
            : Object.values(ttsData.providers || {});
          
          const providers = providersArray.map((p: any) => ({
            id: p.id || p.provider_id,
            name: p.name || p.display_name || p.id?.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
            description: p.description || `${p.id} TTS provider`,
            status: (p.status === 'online' ? 'online' : p.status === 'offline' ? 'offline' : 'degraded') as 'online' | 'offline' | 'degraded',
            deployment: p.deployment || 'cloud',
            endpoint: p.endpoint || '',
            icon: p.icon || '🔊',
            capabilities: {
              voice_cloning: p.capabilities?.voice_cloning || false,
              multi_language: p.capabilities?.multi_language || false,
              speed_control: p.capabilities?.speed_control !== false,
              pitch_control: p.capabilities?.pitch_control !== false,
              multi_speaker: p.capabilities?.multi_speaker || false,
              streaming: p.capabilities?.streaming || false,
            },
          }));
          setTtsProviders(providers);
        } else {
          console.warn('Failed to fetch TTS providers:', ttsResponse.status, ttsResponse.statusText);
        }

        // Fetch ASR providers - using same endpoint pattern
        const asrResponse = await fetch(`${apiBaseUrl}/api/asr/providers`);
        if (asrResponse.ok) {
          const asrData = await asrResponse.json();
          const providersArray = Array.isArray(asrData.providers) 
            ? asrData.providers 
            : Object.values(asrData.providers || {});
          
          const providers = providersArray.map((p: any) => ({
            id: p.id || p.provider_id,
            name: p.name || p.display_name || p.id?.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
            description: p.description || `${p.id} ASR provider`,
            status: (p.status === 'online' ? 'online' : p.status === 'offline' ? 'offline' : 'building') as 'online' | 'offline' | 'building',
            languages: Array.isArray(p.languages) ? p.languages : (p.languages ? [p.languages] : ['en']),
            icon: p.icon || '🎤',
            capabilities: {
              realtime: p.capabilities?.realtime || false,
              translation: p.capabilities?.translation || false,
              punctuation: p.capabilities?.punctuation !== false,
            },
          }));
          setAsrProviders(providers);
        } else {
          console.warn('Failed to fetch ASR providers:', asrResponse.status, asrResponse.statusText);
        }

        // Fetch LLM models - using same endpoint pattern
        const llmResponse = await fetch(`${apiBaseUrl}/api/llm/providers`);
        if (llmResponse.ok) {
          const llmData = await llmResponse.json();
          const models: LLMModel[] = [];
          
          // Handle both array and object formats
          const providersArray = Array.isArray(llmData.providers) 
            ? llmData.providers 
            : Object.values(llmData.providers || {});
          
          // Flatten providers into models
          providersArray.forEach((provider: any) => {
            if (provider.models && Array.isArray(provider.models)) {
              provider.models.forEach((model: any) => {
                models.push({
                  id: model.id || model.model_id,
                  name: model.name || model.display_name || model.id,
                  description: model.description || `${model.id} model`,
                  provider: provider.id || provider.provider_id,
                  contextWindow: model.context_window || model.max_tokens || 8000,
                  icon: model.icon || provider.icon || '🧠',
                  capabilities: {
                    functionCalling: model.capabilities?.function_calling || false,
                    streaming: model.capabilities?.streaming !== false,
                    multimodal: model.capabilities?.multimodal || false,
                    json: model.capabilities?.json || false,
                  },
                  pricing: model.pricing ? {
                    inputCostPer1M: model.pricing.input_cost_per_1m,
                    outputCostPer1M: model.pricing.output_cost_per_1m,
                  } : undefined,
                });
              });
            }
          });
          setLlmModels(models);
        } else {
          console.warn('Failed to fetch LLM providers:', llmResponse.status, llmResponse.statusText);
        }

        // Fetch cloned voices (if endpoint exists)
        try {
          const voicesResponse = await fetch(`${apiBaseUrl}/voice-library/voices`);
          if (voicesResponse.ok) {
            const voicesData = await voicesResponse.json();
            setClonedVoices(voicesData.voices || []);
          }
        } catch (e) {
          // Voice library endpoint might not exist, that's okay
          console.warn('Voice library endpoint not available:', e);
        }

      } catch (err) {
        console.error('Error fetching providers:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch providers');
      } finally {
        setIsLoading(false);
      }
    };

    if (apiBaseUrl) {
      fetchProviders();
    }
  }, [apiBaseUrl]);

  return {
    ttsProviders,
    asrProviders,
    llmModels,
    clonedVoices,
    isLoading,
    error,
  };
}

