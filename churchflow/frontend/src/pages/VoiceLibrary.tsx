/**
 * Voice Library Page
 *
 * Voice settings configuration for TTS providers with full controls.
 * Uses ComprehensiveTTSSelector for provider selection, voice/language
 * selection, speed, pitch, and preview functionality.
 */

import { useState, useEffect } from 'react';
import { Volume2, Save, RotateCcw, AlertCircle } from 'lucide-react';
import { API_BASE_URL } from '../config/api-config';
import ConfirmDialog from '../components/ConfirmDialog';
import { ComprehensiveTTSSelector } from '../../../../shared/frontend/components/voice-settings/ComprehensiveTTSSelector';
import { useComprehensiveTTS } from '../../../../shared/frontend/hooks/useComprehensiveTTS';
import { getAuthHeaders } from '../lib/auth-utils';

interface VoiceSettings {
  tts_provider_id: string;
  voice_id: string | null;
  language: string;
  speed: number;
  pitch: number;
}

export default function VoiceLibrary() {
  // Settings state
  const [settings, setSettings] = useState<VoiceSettings>({
    tts_provider_id: 'f5tts',
    voice_id: null,
    language: 'en',
    speed: 1.0,
    pitch: 0.0,
  });

  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewAudio, setPreviewAudio] = useState<HTMLAudioElement | null>(null);
  const [showResetDialog, setShowResetDialog] = useState(false);

  // Use comprehensive TTS hook for provider data
  const {
    providers: ttsProviders,
    loading: loadingProviders,
    error: providersError,
  } = useComprehensiveTTS(API_BASE_URL, undefined, {
    onlineOnly: false,
    autoFetch: true,
    endpointPath: '/api/tts/providers',
    skipWalletBalance: true,
    getAuthHeaders,
  });

  // Load saved settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/api/v1/voice-library/settings`, {
        headers: {
          ...headers,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSettings({
          tts_provider_id: data.tts_provider_id || 'f5tts',
          voice_id: data.voice_id || null,
          language: data.language || 'en',
          speed: data.speed || 1.0,
          pitch: data.pitch || 0.0,
        });
      }
    } catch (err: any) {
      console.error('Failed to load voice settings:', err);
      // Use defaults if load fails
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!isDirty) return;

    setIsSaving(true);
    setError(null);

    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/api/v1/voice-library/settings`, {
        method: 'PUT',
        headers: {
          ...headers,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (response.ok) {
        setIsDirty(false);
        alert('Voice settings saved successfully!');
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to save settings');
      }
    } catch (err: any) {
      console.error('Failed to save voice settings:', err);
      setError(err.message || 'Failed to save voice settings');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    loadSettings();
    setIsDirty(false);
    setShowResetDialog(false);
  };

  const updateSettings = (updates: Partial<VoiceSettings>) => {
    setSettings((prev) => ({ ...prev, ...updates }));
    setIsDirty(true);
  };

  // Handle voice preview
  const handlePreviewVoice = async (previewText: string) => {
    if (!settings.tts_provider_id) {
      alert('Please select a TTS provider first');
      return;
    }

    // Stop any currently playing audio
    if (previewAudio) {
      previewAudio.pause();
      previewAudio.currentTime = 0;
    }

    setPreviewLoading(true);

    try {
      const synthesisRequest = {
        provider_id: settings.tts_provider_id,
        text: previewText,
        language: settings.language || 'en',
        voice_id: settings.voice_id || undefined,
        speed: settings.speed || 1.0,
        pitch: settings.pitch || 0.0,
        output_format: 'wav',
      };

      const headers = await getAuthHeaders();

      const response = await fetch(`${API_BASE_URL}/api/tts/synthesize`, {
        method: 'POST',
        headers: {
          ...headers,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(synthesisRequest),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || 'TTS synthesis failed');
      }

      const data = await response.json();

      if (data.audio_base64) {
        const audioBlob = await fetch(`data:audio/wav;base64,${data.audio_base64}`).then((r) =>
          r.blob()
        );
        const audioUrl = URL.createObjectURL(audioBlob);

        const audio = new Audio(audioUrl);
        setPreviewAudio(audio);

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
        };

        await audio.play();
      } else {
        throw new Error('No audio data returned from TTS service');
      }
    } catch (err: any) {
      console.error('TTS preview failed:', err);
      alert(err.message || 'Preview failed');
    } finally {
      setPreviewLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Volume2 className="w-8 h-8 text-purple-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Voice Library</h1>
              <p className="text-gray-600">Configure your voice preferences for text-to-speech</p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowResetDialog(true)}
              disabled={!isDirty || isSaving}
              className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              <RotateCcw className="h-4 w-4" />
              <span>Reset</span>
            </button>
            <button
              onClick={handleSave}
              disabled={!isDirty || isSaving}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              <Save className="h-4 w-4" />
              <span>{isSaving ? 'Saving...' : 'Save Changes'}</span>
            </button>
          </div>
        </div>

        {/* Unsaved Changes Warning */}
        {isDirty && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-yellow-600" />
            <p className="text-yellow-700 text-sm">You have unsaved changes</p>
          </div>
        )}

        {/* Error Message */}
        {(error || providersError) && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <p className="text-red-700 text-sm">{error || providersError}</p>
          </div>
        )}

        {/* Main Content */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Text-to-Speech Settings</h2>
          <p className="text-gray-600 text-sm mb-6">
            Choose your preferred TTS provider, voice, and audio settings
          </p>

          {/* Comprehensive TTS Selector */}
          <ComprehensiveTTSSelector
            providers={ttsProviders}
            selectedProviderId={settings.tts_provider_id}
            onSelectProvider={(providerId) => updateSettings({ tts_provider_id: providerId })}
            selectedVoice={settings.voice_id || undefined}
            onSelectVoice={(voice) => updateSettings({ voice_id: voice })}
            selectedLanguage={settings.language}
            onSelectLanguage={(language) => updateSettings({ language })}
            speed={settings.speed}
            onSpeedChange={(speed) => updateSettings({ speed })}
            pitch={settings.pitch}
            onPitchChange={(pitch) => updateSettings({ pitch })}
            showAdvanced={true}
            showOnlineOnly={false}
            isLoading={isLoading || loadingProviders}
            onPreview={handlePreviewVoice}
            previewLoading={previewLoading}
          />
        </div>

        {/* Provider Stats */}
        {!loadingProviders && ttsProviders.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Provider Statistics</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <p className="text-3xl font-bold text-purple-600">{ttsProviders.length}</p>
                <p className="text-sm text-gray-600">Total Providers</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <p className="text-3xl font-bold text-green-600">
                  {ttsProviders.filter((p) => p.status === 'online').length}
                </p>
                <p className="text-sm text-gray-600">Online</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <p className="text-3xl font-bold text-red-600">
                  {ttsProviders.filter((p) => p.status === 'offline').length}
                </p>
                <p className="text-sm text-gray-600">Offline</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Reset Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showResetDialog}
        onClose={() => setShowResetDialog(false)}
        onConfirm={handleReset}
        title="Reset Changes"
        message="Are you sure you want to reset your changes? All unsaved modifications will be lost."
        confirmText="Reset Changes"
        cancelText="Keep Editing"
        variant="warning"
      />
    </div>
  );
}
