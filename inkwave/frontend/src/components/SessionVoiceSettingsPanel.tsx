/**
 * SessionVoiceSettingsPanel Component
 *
 * Panel for managing per-session voice settings (TTS, ASR, LLM).
 * These settings temporarily override user defaults for the current session.
 */

import React, { useState, useEffect, useRef } from 'react';
import { api } from '../lib/api';
import {
  Settings2,
  Volume2,
  Mic2,
  Brain,
  RotateCcw,
  X,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from 'lucide-react';
import toast from 'react-hot-toast';

interface EffectiveSettings {
  tts: {
    provider: string;
    voice: string | null;
    speed: number;
    pitch: number;
    source: string;
  };
  asr: {
    provider: string;
    language: string;
    task: string;
    source: string;
  };
  llm: {
    model: string;
    temperature: number;
    max_tokens: number;
    source: string;
  };
  session_id: string;
  has_overrides: boolean;
}

interface SessionVoiceSettingsPanelProps {
  sessionId: string;
  onSettingsChange?: (settings: EffectiveSettings) => void;
  className?: string;
}

// Available providers/models
const TTS_PROVIDERS = [
  { id: 'styletts2', name: 'StyleTTS2' },
  { id: 'kokoro', name: 'Kokoro' },
  { id: 'f5tts', name: 'F5-TTS' },
  { id: 'melotts', name: 'MeloTTS' },
  { id: 'zonos', name: 'Zonos' },
];

const ASR_PROVIDERS = [
  { id: 'faster_whisper_large', name: 'Whisper Large' },
  { id: 'faster_whisper_medium', name: 'Whisper Medium' },
  { id: 'faster_whisper_small', name: 'Whisper Small' },
  { id: 'deepgram', name: 'Deepgram' },
];

const LLM_MODELS = [
  { id: 'gemini-2.0-flash-exp', name: 'Gemini 2.0 Flash' },
  { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro' },
  { id: 'gpt-4o', name: 'GPT-4o' },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini' },
  { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet' },
  { id: 'llama3.2', name: 'Llama 3.2 (Local)' },
];

const LANGUAGES = [
  { id: 'en', name: 'English' },
  { id: 'es', name: 'Spanish' },
  { id: 'fr', name: 'French' },
  { id: 'de', name: 'German' },
  { id: 'zh', name: 'Chinese' },
];

export const SessionVoiceSettingsPanel: React.FC<SessionVoiceSettingsPanelProps> = ({
  sessionId,
  onSettingsChange,
  className = '',
}) => {
  const [open, setOpen] = useState(false);
  const [settings, setSettings] = useState<EffectiveSettings | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [expandedSection, setExpandedSection] = useState<string | null>('tts');
  const panelRef = useRef<HTMLDivElement>(null);

  // Local form state for pending changes
  const [localSettings, setLocalSettings] = useState<{
    tts_provider?: string;
    tts_voice?: string;
    tts_speed?: number;
    tts_pitch?: number;
    asr_provider?: string;
    asr_language?: string;
    llm_model?: string;
    llm_temperature?: number;
    llm_max_tokens?: number;
  }>({});

  // Close panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  // Load settings when panel opens
  useEffect(() => {
    if (open && sessionId) {
      loadSettings();
    }
  }, [open, sessionId]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await api.reading.getSessionVoiceSettings(sessionId);
      setSettings(response.data);
      // Reset local changes
      setLocalSettings({});
    } catch (error: any) {
      console.error('Failed to load session voice settings:', error);
      toast.error('Failed to load voice settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (Object.keys(localSettings).length === 0) {
      toast.success('No changes to save');
      return;
    }

    try {
      setSaving(true);
      await api.reading.updateSessionVoiceSettings(sessionId, localSettings);
      toast.success('Session voice settings updated');

      // Reload to get fresh data
      const response = await api.reading.getSessionVoiceSettings(sessionId);
      setSettings(response.data);
      setLocalSettings({});

      if (onSettingsChange) {
        onSettingsChange(response.data);
      }
    } catch (error: any) {
      console.error('Failed to save session voice settings:', error);
      toast.error(error.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    try {
      setSaving(true);
      await api.reading.clearSessionVoiceSettings(sessionId);
      toast.success('Session settings reset to user defaults');

      // Reload settings
      const response = await api.reading.getSessionVoiceSettings(sessionId);
      setSettings(response.data);
      setLocalSettings({});

      if (onSettingsChange) {
        onSettingsChange(response.data);
      }
    } catch (error: any) {
      console.error('Failed to reset session voice settings:', error);
      toast.error('Failed to reset settings');
    } finally {
      setSaving(false);
    }
  };

  const updateLocalSetting = (key: string, value: any) => {
    setLocalSettings((prev) => ({ ...prev, [key]: value }));
  };

  const getSourceBadge = (source: string) => {
    const colors: Record<string, string> = {
      session: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
      user: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      org: 'bg-green-500/20 text-green-400 border-green-500/30',
      system: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    };
    return (
      <span className={`text-[10px] px-1.5 py-0.5 rounded border ${colors[source] || colors.system}`}>
        {source}
      </span>
    );
  };

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const hasChanges = Object.keys(localSettings).length > 0;

  return (
    <div className="relative" ref={panelRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setOpen(!open)}
        className={`relative p-2 rounded-full text-gray-300 hover:text-white hover:bg-gray-800 transition-all ${className}`}
        title="Session Voice Settings"
      >
        <Settings2 className="h-5 w-5" />
        {settings?.has_overrides && (
          <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-purple-500 rounded-full" />
        )}
      </button>

      {/* Settings Panel */}
      {open && (
        <div className="absolute right-0 bottom-full mb-2 w-96 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl z-50 overflow-hidden max-h-[70vh] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-700 bg-gray-800/50">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-400" />
              <span className="font-semibold text-sm text-white">Session Settings</span>
              {settings?.has_overrides && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-400 border border-purple-500/30">
                  Custom
                </span>
              )}
            </div>
            <button
              onClick={() => setOpen(false)}
              className="p-1 text-gray-500 hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500" />
              </div>
            ) : settings ? (
              <>
                {/* TTS Section */}
                <div className="border border-gray-700 rounded-lg overflow-hidden">
                  <button
                    onClick={() => toggleSection('tts')}
                    className="w-full flex items-center justify-between p-3 bg-gray-800/50 hover:bg-gray-800"
                  >
                    <div className="flex items-center gap-2">
                      <Volume2 className="h-4 w-4 text-green-400" />
                      <span className="text-sm font-medium text-white">Text-to-Speech</span>
                      {getSourceBadge(settings.tts.source)}
                    </div>
                    {expandedSection === 'tts' ? (
                      <ChevronUp className="h-4 w-4 text-gray-400" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                  {expandedSection === 'tts' && (
                    <div className="p-3 space-y-3 bg-gray-900/50">
                      {/* Provider */}
                      <div>
                        <label className="text-xs text-gray-400 mb-1 block">Provider</label>
                        <select
                          value={localSettings.tts_provider ?? settings.tts.provider}
                          onChange={(e) => updateLocalSetting('tts_provider', e.target.value)}
                          className="w-full h-8 px-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-purple-500"
                        >
                          {TTS_PROVIDERS.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      {/* Speed */}
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-gray-400">Speed</span>
                          <span className="text-white">
                            {(localSettings.tts_speed ?? settings.tts.speed).toFixed(2)}x
                          </span>
                        </div>
                        <input
                          type="range"
                          min={0.5}
                          max={2}
                          step={0.05}
                          value={localSettings.tts_speed ?? settings.tts.speed}
                          onChange={(e) => updateLocalSetting('tts_speed', parseFloat(e.target.value))}
                          className="w-full h-1.5 bg-gray-700 rounded appearance-none cursor-pointer accent-purple-500"
                        />
                      </div>
                      {/* Pitch */}
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-gray-400">Pitch</span>
                          <span className="text-white">
                            {(localSettings.tts_pitch ?? settings.tts.pitch).toFixed(1)}
                          </span>
                        </div>
                        <input
                          type="range"
                          min={-1}
                          max={1}
                          step={0.1}
                          value={localSettings.tts_pitch ?? settings.tts.pitch}
                          onChange={(e) => updateLocalSetting('tts_pitch', parseFloat(e.target.value))}
                          className="w-full h-1.5 bg-gray-700 rounded appearance-none cursor-pointer accent-purple-500"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* ASR Section */}
                <div className="border border-gray-700 rounded-lg overflow-hidden">
                  <button
                    onClick={() => toggleSection('asr')}
                    className="w-full flex items-center justify-between p-3 bg-gray-800/50 hover:bg-gray-800"
                  >
                    <div className="flex items-center gap-2">
                      <Mic2 className="h-4 w-4 text-blue-400" />
                      <span className="text-sm font-medium text-white">Speech Recognition</span>
                      {getSourceBadge(settings.asr.source)}
                    </div>
                    {expandedSection === 'asr' ? (
                      <ChevronUp className="h-4 w-4 text-gray-400" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                  {expandedSection === 'asr' && (
                    <div className="p-3 space-y-3 bg-gray-900/50">
                      {/* Provider */}
                      <div>
                        <label className="text-xs text-gray-400 mb-1 block">Provider</label>
                        <select
                          value={localSettings.asr_provider ?? settings.asr.provider}
                          onChange={(e) => updateLocalSetting('asr_provider', e.target.value)}
                          className="w-full h-8 px-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-purple-500"
                        >
                          {ASR_PROVIDERS.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      {/* Language */}
                      <div>
                        <label className="text-xs text-gray-400 mb-1 block">Language</label>
                        <select
                          value={localSettings.asr_language ?? settings.asr.language}
                          onChange={(e) => updateLocalSetting('asr_language', e.target.value)}
                          className="w-full h-8 px-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-purple-500"
                        >
                          {LANGUAGES.map((l) => (
                            <option key={l.id} value={l.id}>
                              {l.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  )}
                </div>

                {/* LLM Section */}
                <div className="border border-gray-700 rounded-lg overflow-hidden">
                  <button
                    onClick={() => toggleSection('llm')}
                    className="w-full flex items-center justify-between p-3 bg-gray-800/50 hover:bg-gray-800"
                  >
                    <div className="flex items-center gap-2">
                      <Brain className="h-4 w-4 text-pink-400" />
                      <span className="text-sm font-medium text-white">AI Model</span>
                      {getSourceBadge(settings.llm.source)}
                    </div>
                    {expandedSection === 'llm' ? (
                      <ChevronUp className="h-4 w-4 text-gray-400" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                  {expandedSection === 'llm' && (
                    <div className="p-3 space-y-3 bg-gray-900/50">
                      {/* Model */}
                      <div>
                        <label className="text-xs text-gray-400 mb-1 block">Model</label>
                        <select
                          value={localSettings.llm_model ?? settings.llm.model}
                          onChange={(e) => updateLocalSetting('llm_model', e.target.value)}
                          className="w-full h-8 px-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-purple-500"
                        >
                          {LLM_MODELS.map((m) => (
                            <option key={m.id} value={m.id}>
                              {m.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      {/* Temperature */}
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-gray-400">Temperature</span>
                          <span className="text-white">
                            {(localSettings.llm_temperature ?? settings.llm.temperature).toFixed(2)}
                          </span>
                        </div>
                        <input
                          type="range"
                          min={0}
                          max={2}
                          step={0.1}
                          value={localSettings.llm_temperature ?? settings.llm.temperature}
                          onChange={(e) => updateLocalSetting('llm_temperature', parseFloat(e.target.value))}
                          className="w-full h-1.5 bg-gray-700 rounded appearance-none cursor-pointer accent-purple-500"
                        />
                        <div className="flex justify-between text-[10px] text-gray-500 mt-0.5">
                          <span>Precise</span>
                          <span>Creative</span>
                        </div>
                      </div>
                      {/* Max Tokens */}
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-gray-400">Max Response Length</span>
                          <span className="text-white">
                            {localSettings.llm_max_tokens ?? settings.llm.max_tokens}
                          </span>
                        </div>
                        <input
                          type="range"
                          min={500}
                          max={8000}
                          step={500}
                          value={localSettings.llm_max_tokens ?? settings.llm.max_tokens}
                          onChange={(e) => updateLocalSetting('llm_max_tokens', parseInt(e.target.value))}
                          className="w-full h-1.5 bg-gray-700 rounded appearance-none cursor-pointer accent-purple-500"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Info text */}
                <p className="text-[10px] text-gray-500 px-1 pt-2">
                  These settings apply only to this reading session and won't change your permanent preferences.
                </p>
              </>
            ) : (
              <div className="text-center py-8 text-gray-400">
                Failed to load settings
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between gap-2 p-3 border-t border-gray-700 bg-gray-800/50">
            <button
              onClick={handleReset}
              disabled={saving || !settings?.has_overrides}
              className="flex items-center gap-1 px-3 py-1.5 text-xs text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <RotateCcw className="h-3 w-3" />
              Reset to Defaults
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !hasChanges}
              className="flex items-center gap-1 px-4 py-1.5 text-xs bg-purple-600 hover:bg-purple-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white" />
                  Saving...
                </>
              ) : (
                'Apply Changes'
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SessionVoiceSettingsPanel;
