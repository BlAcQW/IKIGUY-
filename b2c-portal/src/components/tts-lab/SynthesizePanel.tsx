/**
 * Synthesize Panel Component
 *
 * Basic TTS synthesis interface for all providers.
 */

import React, { useState, useEffect } from 'react';
import { TTSProvider } from '../../config/tts-providers';
import { SynthesisProgress } from './SynthesisProgress';
import { ExportFormatModal } from './ExportFormatModal';
import { SSMLEditor } from './SSMLEditor';

interface CostEstimate {
  estimated_cost: number;
  character_count: number;
  provider_id: string;
}

interface SynthesizePanelProps {
  provider: TTSProvider;
  onSynthesize: (params: {
    text: string;
    language?: string;
    speaker?: string | number;
    speed?: number;
  }) => Promise<Blob | null>;
  isLoading: boolean;
  error: string | null;
  getLanguages: () => Promise<string[]>;
  getSpeakers: (language?: string) => Promise<string[]>;
  estimateCost: (text: string, voiceCloning?: boolean) => Promise<CostEstimate | null>;
}

export const SynthesizePanel: React.FC<SynthesizePanelProps> = ({
  provider,
  onSynthesize,
  isLoading,
  error,
  getLanguages,
  getSpeakers,
  estimateCost,
}) => {
  const [text, setText] = useState('');
  const [language, setLanguage] = useState('en');
  const [speaker, setSpeaker] = useState<string | number>(0);
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(0.0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [availableLanguages, setAvailableLanguages] = useState<string[]>([]);
  const [availableSpeakers, setAvailableSpeakers] = useState<string[]>([]);
  const [referenceVoice, setReferenceVoice] = useState('nana_aba');

  // Export modal state
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);

  // SSML mode state
  const [isSSMLMode, setIsSSMLMode] = useState(false);

  // Cost estimation state
  const [costEstimate, setCostEstimate] = useState<CostEstimate | null>(null);
  const [isEstimatingCost, setIsEstimatingCost] = useState(false);

  // Voice preview state
  const [isPlayingPreview, setIsPlayingPreview] = useState(false);
  const [previewAudio, setPreviewAudio] = useState<HTMLAudioElement | null>(null);

  // Progress tracking state
  const [synthesisProgress, setSynthesisProgress] = useState(0);
  const [synthesisStage, setSynthesisStage] = useState('');

  // Voice-cloning providers require reference audio
  const isVoiceCloningProvider = ['coqui_xtts', 'f5tts', 'styletts2'].includes(provider.id);

  // Text templates for common use cases
  const textTemplates = [
    {
      name: 'Welcome Message',
      text: 'Welcome to our service! We\'re glad to have you here. How can we assist you today?',
      category: 'Customer Service'
    },
    {
      name: 'Appointment Reminder',
      text: 'This is a friendly reminder about your appointment tomorrow at 2:00 PM. Please arrive 10 minutes early. Call us if you need to reschedule.',
      category: 'Healthcare'
    },
    {
      name: 'Order Confirmation',
      text: 'Thank you for your order! Your order number is 12345 and will be delivered within 3-5 business days. You will receive a tracking number via email shortly.',
      category: 'E-commerce'
    },
    {
      name: 'Payment Reminder',
      text: 'This is a gentle reminder that your payment of $50 is due on the 15th of this month. Please make your payment to avoid any late fees.',
      category: 'Finance'
    },
    {
      name: 'Service Update',
      text: 'We wanted to inform you about an important update to our service. Our system will undergo maintenance tonight from 11 PM to 2 AM. Thank you for your patience.',
      category: 'IT/Tech'
    },
    {
      name: 'Marketing Promotion',
      text: 'Exciting news! Get 20% off your next purchase with code SAVE20. This limited-time offer expires in 7 days. Shop now and save!',
      category: 'Marketing'
    },
    {
      name: 'Survey Request',
      text: 'We value your feedback! Please take a moment to complete our short customer satisfaction survey. Your input helps us improve our services.',
      category: 'Feedback'
    },
    {
      name: 'Password Reset',
      text: 'We received a request to reset your password. Click the link in your email to create a new password. If you didn\'t request this, please ignore this message.',
      category: 'Security'
    },
    {
      name: 'Event Invitation',
      text: 'You\'re invited to our annual conference on December 15th! Join us for networking, workshops, and keynote speakers. Register now to secure your spot.',
      category: 'Events'
    },
    {
      name: 'Delivery Notification',
      text: 'Your package has been delivered! It was left at your front door. If you have any questions, please contact our support team.',
      category: 'Logistics'
    },
    {
      name: 'Emergency Alert',
      text: 'This is an important safety alert. Please stay indoors and follow official instructions. Check our website for updates.',
      category: 'Emergency'
    },
    {
      name: 'Birthday Greeting',
      text: 'Happy Birthday! Wishing you a wonderful day filled with joy and celebration. Enjoy your special day!',
      category: 'Greetings'
    },
  ];

  // Available Ghanaian reference voices
  const referenceVoices = [
    { id: 'nana_aba', name: 'Nana Aba (Female)', description: 'Professional female voice' },
    { id: 'juliet_bawuah', name: 'Juliet Bawuah (Female)', description: 'Female voice' },
    { id: 'adom_okyere', name: 'Adom Okyere (Male)', description: 'Male voice' },
    { id: 'archbishop_1', name: 'Archbishop 1 (Male)', description: 'Male voice' },
    { id: 'archbishop_2', name: 'Archbishop 2 (Male)', description: 'Male voice' },
    { id: 'nana_aba_24bit', name: 'Nana Aba HQ (Female)', description: 'High-quality 24-bit female voice' },
  ];

  // Reset fields when provider changes
  useEffect(() => {
    // Clear audio when switching providers
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    // Reset to default values
    setSpeed(1.0);
    setPitch(0.0);
    setReferenceVoice('nana_aba');
    // Clear cost estimate
    setCostEstimate(null);
  }, [provider.id]);

  // Debounced cost estimation - update when text or provider changes
  useEffect(() => {
    // Clear cost estimate if text is empty
    if (!text || text.trim().length === 0) {
      setCostEstimate(null);
      return;
    }

    setIsEstimatingCost(true);

    // Debounce cost estimation (wait 500ms after user stops typing)
    const timer = setTimeout(async () => {
      try {
        const estimate = await estimateCost(text, isVoiceCloningProvider);
        setCostEstimate(estimate);
      } catch (err) {
        console.error('Cost estimation failed:', err);
        setCostEstimate(null);
      } finally {
        setIsEstimatingCost(false);
      }
    }, 500);

    return () => {
      clearTimeout(timer);
      setIsEstimatingCost(false);
    };
  }, [text, provider.id, estimateCost, isVoiceCloningProvider]);

  useEffect(() => {
    // Load available languages
    const loadLanguages = async () => {
      const langs = await getLanguages();
      setAvailableLanguages(langs);
      if (langs.length > 0) {
        setLanguage(langs[0]);
      }
    };
    loadLanguages();
  }, [provider.id, getLanguages]);

  useEffect(() => {
    // Load available speakers when language changes
    if (provider.capabilities.multiSpeaker) {
      const loadSpeakers = async () => {
        const speakers = await getSpeakers(language);
        setAvailableSpeakers(speakers);
        if (speakers.length > 0) {
          setSpeaker(0);
        }
      };
      loadSpeakers();
    }
  }, [language, provider.id, provider.capabilities.multiSpeaker, getSpeakers]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+Enter or Cmd+Enter: Trigger synthesis
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (text.trim() && !isLoading) {
          handleSynthesize();
        }
      }
      // Escape: Clear text or stop audio playback
      else if (e.key === 'Escape') {
        e.preventDefault();
        if (audioUrl) {
          // Stop and clear audio if playing
          if (audioUrl) {
            URL.revokeObjectURL(audioUrl);
            setAudioUrl(null);
          }
        } else if (text) {
          // Clear text if no audio is playing
          setText('');
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [text, isLoading, audioUrl]);

  const handleSynthesize = async () => {
    if (!text.trim()) {
      return;
    }

    // Clear previous audio
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }

    // Reset progress
    setSynthesisProgress(0);
    setSynthesisStage('Starting...');

    const params: any = {
      text,
      onProgress: (progress: number, stage: string) => {
        setSynthesisProgress(progress);
        setSynthesisStage(stage);
      }
    };
    if (provider.capabilities.multiLanguage) {
      params.language = language;
    }
    // For voice-cloning providers, use reference voice as speaker
    if (isVoiceCloningProvider) {
      params.speaker = referenceVoice;
    } else if (provider.capabilities.multiSpeaker) {
      params.speaker = speaker;
    }
    if (provider.capabilities.speedControl) {
      params.speed = speed;
    }
    if (provider.capabilities.pitchControl) {
      params.pitch = pitch;
    }

    const resultBlob = await onSynthesize(params);
    if (resultBlob) {
      const url = URL.createObjectURL(resultBlob);
      setAudioUrl(url);
      setAudioBlob(resultBlob);
      // Reset progress after completion
      setSynthesisProgress(0);
      setSynthesisStage('');
    } else {
      // Reset progress on error
      setSynthesisProgress(0);
      setSynthesisStage('');
    }
  };

  const handleDownload = () => {
    if (!audioUrl) return;

    const a = document.createElement('a');
    a.href = audioUrl;
    a.download = `tts_${provider.id}_${Date.now()}.wav`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handlePlayPreview = async (voiceId: string) => {
    try {
      // Stop any currently playing preview
      if (previewAudio) {
        previewAudio.pause();
        previewAudio.currentTime = 0;
      }

      setIsPlayingPreview(true);

      // Create preview URL
      const previewUrl = `/api/tts/voices/${voiceId}/preview`;

      // Create new audio element
      const audio = new Audio(previewUrl);

      audio.onended = () => {
        setIsPlayingPreview(false);
        setPreviewAudio(null);
      };

      audio.onerror = () => {
        setIsPlayingPreview(false);
        setPreviewAudio(null);
        console.error('Error playing voice preview');
      };

      setPreviewAudio(audio);
      await audio.play();
    } catch (err) {
      console.error('Error playing preview:', err);
      setIsPlayingPreview(false);
      setPreviewAudio(null);
    }
  };

  /**
   * Handle text template selection.
   */
  const handleTemplateSelect = (templateText: string) => {
    setText(templateText);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Text Input */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-3">
            <label className="block text-sm font-medium text-gray-700">
              Text to Synthesize
            </label>
            {/* SSML Mode Toggle */}
            {provider.capabilities.ssmlSupport && (
              <button
                onClick={() => setIsSSMLMode(!isSSMLMode)}
                className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                  isSSMLMode
                    ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                title="Toggle SSML mode for advanced prosody control"
              >
                {isSSMLMode ? '📝 SSML Mode' : '🔤 Plain Text'}
              </button>
            )}
          </div>
          {/* Text Template Selector */}
          {!isSSMLMode && (
            <div className="flex items-center space-x-2">
              <label className="text-xs text-gray-600">Quick Templates:</label>
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    handleTemplateSelect(e.target.value);
                    e.target.value = ''; // Reset dropdown
                  }
                }}
                className="text-xs px-2 py-1 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-700"
              >
                <option value="">Select template...</option>
                {textTemplates.map((template, index) => (
                  <option key={index} value={template.text}>
                    {template.name} ({template.category})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Render SSML Editor or Plain Text Editor */}
        {isSSMLMode ? (
          <SSMLEditor
            value={text}
            onChange={setText}
            placeholder="Enter SSML markup... e.g., <speak>Hello <emphasis level='strong'>world</emphasis>!</speak>"
          />
        ) : (
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Enter text to convert to speech or select a template above..."
            className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none text-gray-900 placeholder:text-gray-400"
          />
        )}
        <div className="mt-2 flex items-center justify-between text-sm">
          <div className="flex flex-col space-y-1">
            <p className="text-gray-500">
              {text.length} characters
            </p>
            {/* Keyboard Shortcuts Hint */}
            <div className="flex items-center space-x-3 text-xs text-gray-400">
              <span className="flex items-center space-x-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-gray-600 font-mono">Ctrl</kbd>
                <span>+</span>
                <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-gray-600 font-mono">Enter</kbd>
                <span>to synthesize</span>
              </span>
              <span>•</span>
              <span className="flex items-center space-x-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-gray-600 font-mono">Esc</kbd>
                <span>to clear</span>
              </span>
            </div>
          </div>
          {/* Cost Estimation Display */}
          {isEstimatingCost && (
            <p className="text-gray-400 italic">
              Estimating cost...
            </p>
          )}
          {costEstimate && !isEstimatingCost && (
            <div className="flex items-center space-x-2">
              {costEstimate.estimated_cost > 0.10 ? (
                <span className="text-amber-600 font-medium flex items-center">
                  ⚠️ High cost: ${costEstimate.estimated_cost.toFixed(4)}
                </span>
              ) : (
                <span className="text-green-600 font-medium">
                  💰 Est. cost: ${costEstimate.estimated_cost.toFixed(4)}
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Reference Voice Selection (for voice-cloning providers) */}
      {isVoiceCloningProvider && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-2 mb-3">
            <span className="text-blue-600 text-xl">ℹ️</span>
            <div>
              <h4 className="font-medium text-blue-900 text-sm">
                Voice Cloning Provider
              </h4>
              <p className="text-xs text-blue-700 mt-1">
                This provider clones the selected reference voice to speak your text.
                Choose from our Ghanaian voice library below.
              </p>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reference Voice
            </label>
            <div className="space-y-2">
              {referenceVoices.map((voice) => (
                <div
                  key={voice.id}
                  className={`flex items-center justify-between p-3 rounded-lg border-2 cursor-pointer transition-all ${
                    referenceVoice === voice.id
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                  onClick={() => setReferenceVoice(voice.id)}
                >
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 text-sm">
                      {voice.name}
                    </div>
                    <div className="text-xs text-gray-600">
                      {voice.description}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handlePlayPreview(voice.id);
                    }}
                    disabled={isPlayingPreview}
                    className="ml-3 px-3 py-1.5 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-xs font-medium transition-colors flex items-center space-x-1"
                  >
                    {isPlayingPreview ? (
                      <>
                        <span className="inline-block animate-pulse">⏸️</span>
                        <span>Playing...</span>
                      </>
                    ) : (
                      <>
                        <span>▶️</span>
                        <span>Preview</span>
                      </>
                    )}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Settings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Language Selection */}
        {provider.capabilities.multiLanguage && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Language
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900"
            >
              {availableLanguages.map((lang) => (
                <option key={lang} value={lang}>
                  {lang.toUpperCase()}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Speaker Selection */}
        {provider.capabilities.multiSpeaker && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Speaker
            </label>
            <select
              value={speaker}
              onChange={(e) => setSpeaker(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900"
            >
              {availableSpeakers.length > 0 ? (
                availableSpeakers.map((spk, idx) => (
                  <option key={idx} value={idx}>
                    {spk || `Speaker ${idx}`}
                  </option>
                ))
              ) : (
                Array.from({ length: 5 }, (_, i) => (
                  <option key={i} value={i}>
                    Speaker {i}
                  </option>
                ))
              )}
            </select>
          </div>
        )}

        {/* Speed Control */}
        {provider.capabilities.speedControl && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Speed: {speed.toFixed(1)}x
            </label>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={speed}
              onChange={(e) => setSpeed(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0.5x</span>
              <span>1.0x</span>
              <span>2.0x</span>
            </div>
          </div>
        )}

        {/* Pitch Control */}
        {provider.capabilities.pitchControl && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Pitch: {pitch > 0 ? '+' : ''}{pitch.toFixed(1)}
            </label>
            <input
              type="range"
              min="-0.5"
              max="0.5"
              step="0.1"
              value={pitch}
              onChange={(e) => setPitch(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>-0.5</span>
              <span>0.0</span>
              <span>+0.5</span>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-4">
        <button
          onClick={handleSynthesize}
          disabled={isLoading || !text.trim()}
          className={`
            flex-1 px-6 py-3 rounded-lg font-medium text-white
            ${
              isLoading || !text.trim()
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800'
            }
            transition-colors duration-200
          `}
        >
          {isLoading ? 'Synthesizing...' : 'Synthesize Speech'}
        </button>
      </div>

      {/* Progress Bar (shown during synthesis) */}
      {isLoading && synthesisProgress > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <SynthesisProgress progress={synthesisProgress} stage={synthesisStage} />
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <span className="text-red-600 mr-2">⚠️</span>
            <div>
              <h4 className="font-medium text-red-900">Synthesis Error</h4>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Audio Player */}
      {audioUrl && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-green-900">✓ Synthesis Complete</h4>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleDownload}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
              >
                Download WAV
              </button>
              <button
                onClick={() => setIsExportModalOpen(true)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium"
              >
                Export As...
              </button>
            </div>
          </div>
          <audio controls src={audioUrl} className="w-full" />
        </div>
      )}

      {/* Export Format Modal */}
      <ExportFormatModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        audioBlob={audioBlob}
        filename={`tts_${provider.id}_${Date.now()}`}
      />
    </div>
  );
};
