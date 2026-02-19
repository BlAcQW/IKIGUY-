/**
 * Voice Cloning Panel Component
 *
 * Interface for voice cloning with reference audio.
 */

import React, { useState, useEffect } from 'react';
import { TTSProvider, GHANAIAN_VOICES } from '../../config/tts-providers';
import { useClonedVoices, ClonedVoice } from '../../hooks/useClonedVoices';
import { API_BASE_URL } from '../../config/api-config';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { SynthesisProgress } from './SynthesisProgress';
import { ExportFormatModal } from './ExportFormatModal';

interface VoiceCloningPanelProps {
  provider: TTSProvider;
  onSynthesize: (params: {
    text: string;
    referenceAudio: File;
    language?: string;
    alpha?: number;
    beta?: number;
    diffusion_steps?: number;
    embedding_scale?: number;
    onProgress?: (progress: number, stage: string) => void;
  }) => Promise<Blob | null>;
  isLoading: boolean;
  error: string | null;
  getLanguages: () => Promise<string[]>;
}

export const VoiceCloningPanel: React.FC<VoiceCloningPanelProps> = ({
  provider,
  onSynthesize,
  isLoading,
  error,
  getLanguages,
}) => {
  const [text, setText] = useState('');
  const [language, setLanguage] = useState('en');
  const [referenceAudio, setReferenceAudio] = useState<File | null>(null);
  const [selectedGhanaianVoice, setSelectedGhanaianVoice] = useState<string | null>(null);
  const [selectedClonedVoice, setSelectedClonedVoice] = useState<ClonedVoice | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [availableLanguages, setAvailableLanguages] = useState<string[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [showVoiceSource, setShowVoiceSource] = useState<'library' | 'cloned' | 'upload' | 'record'>('cloned');
  const [previewAudio, setPreviewAudio] = useState<HTMLAudioElement | null>(null);
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);
  const [saveToLibrary, setSaveToLibrary] = useState(false);
  const [libraryVoiceName, setLibraryVoiceName] = useState('');
  const [saveSynthesizedToLibrary, setSaveSynthesizedToLibrary] = useState(false);
  const [synthesizedVoiceName, setSynthesizedVoiceName] = useState('');
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);

  // StyleTTS2 specific parameters
  const [alpha, setAlpha] = useState(0.3);  // Timbre control
  const [beta, setBeta] = useState(0.7);    // Prosody control
  const [diffusionSteps, setDiffusionSteps] = useState(5);
  const [embeddingScale, setEmbeddingScale] = useState(1.0);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Progress tracking state
  const [synthesisProgress, setSynthesisProgress] = useState(0);
  const [synthesisStage, setSynthesisStage] = useState('');

  // Use cloned voices hook
  const { voices: clonedVoices, isLoading: isLoadingVoices } = useClonedVoices();

  // Use voice recorder hook
  const {
    isRecording,
    isPlaying: isPlayingRecording,
    audioUrl: recordingUrl,
    audioBlob: recordingBlob,
    duration: recordingDuration,
    startRecording,
    stopRecording,
    playAudio: playRecording,
    stopPlayback: stopRecordingPlayback,
    clearRecording
  } = useVoiceRecorder();

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

  // Set reference audio when recording is complete
  useEffect(() => {
    if (recordingBlob && showVoiceSource === 'record') {
      const file = new File([recordingBlob], `recording_${Date.now()}.webm`, { type: recordingBlob.type });
      setReferenceAudio(file);
      setSelectedGhanaianVoice(null);
      setSelectedClonedVoice(null);
    }
  }, [recordingBlob, showVoiceSource]);

  // Cleanup preview audio on unmount
  useEffect(() => {
    return () => {
      if (previewAudio) {
        previewAudio.pause();
        previewAudio.src = '';
      }
    };
  }, [previewAudio]);

  const handlePreviewVoice = async (voiceId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent selecting the voice when clicking play

    const voice = GHANAIAN_VOICES.find((v) => v.id === voiceId);
    if (!voice) return;

    // If already playing this voice, stop it
    if (playingVoiceId === voiceId && previewAudio) {
      previewAudio.pause();
      previewAudio.currentTime = 0;
      setPlayingVoiceId(null);
      return;
    }

    // Stop any currently playing audio
    if (previewAudio) {
      previewAudio.pause();
      previewAudio.src = '';
    }

    try {
      // Fetch voice file from library-voices endpoint
      const response = await fetch(`${API_BASE_URL}/api/voice-lab/library-voices/${voiceId}/audio`);
      if (!response.ok) {
        throw new Error(`Failed to fetch voice: ${response.statusText}`);
      }
      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);

      // Create and play audio
      const audio = new Audio(audioUrl);
      audio.onended = () => {
        setPlayingVoiceId(null);
        URL.revokeObjectURL(audioUrl);
      };
      audio.onerror = (e) => {
        console.error('Audio playback error:', e);
        setPlayingVoiceId(null);
        URL.revokeObjectURL(audioUrl);
      };

      setPreviewAudio(audio);
      setPlayingVoiceId(voiceId);
      await audio.play();
    } catch (err) {
      console.error('Failed to preview voice:', err);
      alert(`Failed to preview voice: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setPlayingVoiceId(null);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setReferenceAudio(file);
      setSelectedGhanaianVoice(null);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('audio/')) {
      setReferenceAudio(file);
      setSelectedGhanaianVoice(null);
    }
  };

  const handleGhanaianVoiceSelect = async (voiceId: string) => {
    const voice = GHANAIAN_VOICES.find((v) => v.id === voiceId);
    if (!voice) return;

    setSelectedGhanaianVoice(voiceId);
    setSelectedClonedVoice(null);

    // Stop any playing preview
    if (previewAudio && playingVoiceId) {
      previewAudio.pause();
      previewAudio.currentTime = 0;
      setPlayingVoiceId(null);
    }

    // Fetch the voice file from library-voices endpoint
    // Reason: Need to convert the server-side voice file to a File object for the API
    try {
      const response = await fetch(`${API_BASE_URL}/api/voice-lab/library-voices/${voiceId}/audio`);
      if (!response.ok) {
        throw new Error(`Failed to fetch voice: ${response.statusText}`);
      }
      const blob = await response.blob();
      const file = new File([blob], `${voiceId}.wav`, { type: 'audio/wav' });
      setReferenceAudio(file);
      console.log('Library voice loaded successfully:', voice.name);
    } catch (err) {
      console.error('Failed to load library voice:', err);
      alert(`Failed to load voice: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleClonedVoiceSelect = async (voice: ClonedVoice) => {
    setSelectedClonedVoice(voice);
    setSelectedGhanaianVoice(null);

    // Fetch the cloned voice reference audio
    try {
      const response = await fetch(`${API_BASE_URL}/api/voice-lab/voices/cloned/${voice.voice_id}/audio`);
      if (!response.ok) {
        throw new Error(`Failed to fetch cloned voice: ${response.statusText}`);
      }
      const blob = await response.blob();
      const file = new File([blob], `${voice.name}.wav`, { type: 'audio/wav' });
      setReferenceAudio(file);
    } catch (err) {
      console.error('Failed to load cloned voice:', err);
    }
  };

  const handleSaveToLibrary = async () => {
    if (!recordingBlob || !libraryVoiceName.trim()) {
      alert('Please provide a name for the voice');
      return;
    }

    try {
      const formData = new FormData();
      const file = new File([recordingBlob], `${libraryVoiceName.replace(/\s+/g, '_')}.webm`, {
        type: recordingBlob.type
      });

      formData.append('audio', file);
      formData.append('voice_id', libraryVoiceName.toLowerCase().replace(/\s+/g, '_'));
      formData.append('name', libraryVoiceName);
      formData.append('gender', 'neutral');
      formData.append('accent', 'neutral');
      formData.append('language', language || 'en');
      formData.append('description', `Recorded voice: ${libraryVoiceName}`);
      formData.append('is_featured', 'false');

      const response = await fetch(`${API_BASE_URL}/api/voice-lab/library-voices/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Failed to save to library: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('Voice saved to library:', result);
      alert(`✅ Voice "${libraryVoiceName}" saved to library!`);

      // Reset the save to library state
      setSaveToLibrary(false);
      setLibraryVoiceName('');
    } catch (err) {
      console.error('Failed to save voice to library:', err);
      alert(`Failed to save voice: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleSynthesize = async () => {
    if (!text.trim() || !referenceAudio) {
      return;
    }

    // Save to library if option is checked
    if (saveToLibrary && showVoiceSource === 'record' && recordingBlob && libraryVoiceName.trim()) {
      await handleSaveToLibrary();
    }

    // Clear previous audio
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }

    // Reset progress
    setSynthesisProgress(0);
    setSynthesisStage('Starting...');

    const audioBlob = await onSynthesize({
      text,
      referenceAudio,
      language,
      // StyleTTS2 parameters (will be ignored by other providers)
      alpha,
      beta,
      diffusion_steps: diffusionSteps,
      embedding_scale: embeddingScale,
      // Progress callback
      onProgress: (progress: number, stage: string) => {
        setSynthesisProgress(progress);
        setSynthesisStage(stage);
      }
    });

    if (audioBlob) {
      const url = URL.createObjectURL(audioBlob);
      setAudioUrl(url);
      setAudioBlob(audioBlob);  // Save blob for export
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
    a.download = `tts_cloned_${Date.now()}.wav`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleSaveSynthesizedToLibrary = async () => {
    if (!audioUrl || !synthesizedVoiceName.trim()) {
      alert('Please provide a name for the voice');
      return;
    }

    try {
      // Fetch the blob from the audioUrl
      const response = await fetch(audioUrl);
      const blob = await response.blob();

      const formData = new FormData();
      const file = new File([blob], `${synthesizedVoiceName.replace(/\s+/g, '_')}.wav`, {
        type: 'audio/wav'
      });

      formData.append('audio', file);
      formData.append('voice_id', synthesizedVoiceName.toLowerCase().replace(/\s+/g, '_'));
      formData.append('name', synthesizedVoiceName);
      formData.append('gender', 'neutral');
      formData.append('accent', 'neutral');
      formData.append('language', language || 'en');
      formData.append('description', `Synthesized voice: ${synthesizedVoiceName}`);
      formData.append('is_featured', 'false');

      const uploadResponse = await fetch(`${API_BASE_URL}/api/voice-lab/library-voices/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error(`Failed to save to library: ${uploadResponse.statusText}`);
      }

      const result = await uploadResponse.json();
      console.log('Voice saved to library:', result);
      alert(`✅ Voice "${synthesizedVoiceName}" saved to library!`);

      // Reset the save to library state
      setSaveSynthesizedToLibrary(false);
      setSynthesizedVoiceName('');
    } catch (err) {
      console.error('Failed to save voice to library:', err);
      alert(`Failed to save voice: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Capability Check */}
      {!provider.capabilities.voiceCloning && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start">
            <span className="text-yellow-600 mr-2">⚠️</span>
            <div>
              <h4 className="font-medium text-yellow-900">Not Supported</h4>
              <p className="text-sm text-yellow-700 mt-1">
                {provider.name} does not support voice cloning. Please select a different provider.
              </p>
            </div>
          </div>
        </div>
      )}

      {provider.capabilities.voiceCloning && (
        <>
          {/* Text Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Text to Synthesize with Cloned Voice
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enter text to convert to speech with the reference voice..."
              className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
            />
            <p className="mt-1 text-sm text-gray-500">{text.length} characters</p>
          </div>

          {/* Language Selection */}
          {provider.capabilities.multiLanguage && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                {availableLanguages.map((lang) => (
                  <option key={lang} value={lang}>
                    {lang.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* StyleTTS2 Advanced Controls */}
          {provider.id === 'styletts2' && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center justify-between w-full text-left"
              >
                <div className="flex items-center">
                  <span className="text-sm font-medium text-purple-900">
                    🎨 Style & Emotion Controls
                  </span>
                  <span className="ml-2 text-xs text-purple-600 bg-purple-100 px-2 py-0.5 rounded">
                    Advanced
                  </span>
                </div>
                <svg
                  className={`w-5 h-5 text-purple-600 transition-transform ${showAdvanced ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {showAdvanced && (
                <div className="mt-4 space-y-4 pt-4 border-t border-purple-200">
                  {/* Alpha (Timbre) Control */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-gray-700">
                        Alpha (Timbre Control)
                      </label>
                      <span className="text-sm text-purple-600 font-mono">{alpha.toFixed(2)}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={alpha}
                      onChange={(e) => setAlpha(parseFloat(e.target.value))}
                      className="w-full h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                    />
                    <p className="text-xs text-gray-600 mt-1">
                      Higher values = more text-aligned timbre, Lower = more voice-like
                    </p>
                  </div>

                  {/* Beta (Prosody) Control */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-gray-700">
                        Beta (Prosody Control)
                      </label>
                      <span className="text-sm text-purple-600 font-mono">{beta.toFixed(2)}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={beta}
                      onChange={(e) => setBeta(parseFloat(e.target.value))}
                      className="w-full h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                    />
                    <p className="text-xs text-gray-600 mt-1">
                      Higher values = more text-aligned prosody, Lower = more emotional
                    </p>
                  </div>

                  {/* Diffusion Steps */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-gray-700">
                        Diffusion Steps
                      </label>
                      <span className="text-sm text-purple-600 font-mono">{diffusionSteps}</span>
                    </div>
                    <input
                      type="range"
                      min="3"
                      max="20"
                      step="1"
                      value={diffusionSteps}
                      onChange={(e) => setDiffusionSteps(parseInt(e.target.value))}
                      className="w-full h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                    />
                    <p className="text-xs text-gray-600 mt-1">
                      More steps = higher quality but slower (3-20)
                    </p>
                  </div>

                  {/* Embedding Scale */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-gray-700">
                        Embedding Scale
                      </label>
                      <span className="text-sm text-purple-600 font-mono">{embeddingScale.toFixed(2)}</span>
                    </div>
                    <input
                      type="range"
                      min="0.5"
                      max="2.0"
                      step="0.1"
                      value={embeddingScale}
                      onChange={(e) => setEmbeddingScale(parseFloat(e.target.value))}
                      className="w-full h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                    />
                    <p className="text-xs text-gray-600 mt-1">
                      Higher values = more emotional/expressive output
                    </p>
                  </div>

                  {/* Reset Button */}
                  <button
                    onClick={() => {
                      setAlpha(0.3);
                      setBeta(0.7);
                      setDiffusionSteps(5);
                      setEmbeddingScale(1.0);
                    }}
                    className="w-full px-3 py-2 text-sm text-purple-700 bg-purple-100 hover:bg-purple-200 rounded-lg transition-colors"
                  >
                    Reset to Defaults
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Voice Source Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reference Voice Source
            </label>
            <div className="flex space-x-2 mb-4">
              <button
                onClick={() => setShowVoiceSource('cloned')}
                className={`
                  px-4 py-2 rounded-lg text-sm font-medium transition-colors
                  ${showVoiceSource === 'cloned'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }
                `}
              >
                Cloned Voices ({clonedVoices.filter(v => v.status === 'completed' && v.provider === provider.id).length})
              </button>
              <button
                onClick={() => setShowVoiceSource('library')}
                className={`
                  px-4 py-2 rounded-lg text-sm font-medium transition-colors
                  ${showVoiceSource === 'library'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }
                `}
              >
                Library ({GHANAIAN_VOICES.length})
              </button>
              <button
                onClick={() => {
                  setShowVoiceSource('record');
                  // Clear any previous recording when switching to record mode
                  if (recordingBlob) {
                    clearRecording();
                  }
                }}
                className={`
                  px-4 py-2 rounded-lg text-sm font-medium transition-colors
                  ${showVoiceSource === 'record'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }
                `}
              >
                🎤 Record
              </button>
              <button
                onClick={() => setShowVoiceSource('upload')}
                className={`
                  px-4 py-2 rounded-lg text-sm font-medium transition-colors
                  ${showVoiceSource === 'upload'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }
                `}
              >
                Upload
              </button>
            </div>

            {/* Cloned Voices Gallery */}
            {showVoiceSource === 'cloned' && (
              <div>
                {isLoadingVoices ? (
                  <div className="text-center py-8 text-gray-500">
                    Loading cloned voices...
                  </div>
                ) : clonedVoices.filter(v => v.status === 'completed' && v.provider === provider.id).length === 0 ? (
                  <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-gray-600 mb-2">No cloned voices available for {provider.name}</p>
                    <p className="text-sm text-gray-500">Use the "Batch Clone" feature in Voice Studio to create cloned voices</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-3 max-h-96 overflow-y-auto">
                    {clonedVoices
                      .filter(v => v.status === 'completed' && v.provider === provider.id)
                      .map((voice) => (
                        <button
                          key={voice.voice_id}
                          onClick={() => handleClonedVoiceSelect(voice)}
                          className={`
                            p-4 rounded-lg border-2 text-left transition-all
                            ${
                              selectedClonedVoice?.voice_id === voice.voice_id
                                ? 'border-purple-500 bg-purple-50'
                                : 'border-gray-200 bg-white hover:border-purple-300'
                            }
                          `}
                        >
                          <div className="flex items-start justify-between">
                            <h4 className="font-medium text-gray-900">{voice.name}</h4>
                            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">✓</span>
                          </div>
                          <p className="text-xs text-gray-500 mt-1">{voice.description}</p>
                          <div className="flex items-center justify-between mt-2">
                            <span className="text-xs text-gray-400">{voice.gender}</span>
                            <span className="text-xs text-gray-400">{voice.accent}</span>
                          </div>
                        </button>
                      ))}
                  </div>
                )}
              </div>
            )}

            {/* Ghanaian Voices Library */}
            {showVoiceSource === 'library' && (
              <div className="grid grid-cols-2 gap-3">
                {GHANAIAN_VOICES.map((voice) => (
                  <button
                    key={voice.id}
                    onClick={() => handleGhanaianVoiceSelect(voice.id)}
                    className={`
                      p-4 rounded-lg border-2 text-left transition-all relative
                      ${
                        selectedGhanaianVoice === voice.id
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 bg-white hover:border-purple-300'
                      }
                    `}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{voice.name}</h4>
                        <p className="text-xs text-gray-500 mt-1">{voice.description}</p>
                        <p className="text-xs text-gray-400 mt-1">{voice.size}</p>
                      </div>
                      <button
                        onClick={(e) => handlePreviewVoice(voice.id, e)}
                        className={`
                          ml-2 p-2 rounded-full transition-all flex-shrink-0
                          ${
                            playingVoiceId === voice.id
                              ? 'bg-purple-600 text-white hover:bg-purple-700'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }
                        `}
                        title={playingVoiceId === voice.id ? 'Stop preview' : 'Preview voice'}
                      >
                        {playingVoiceId === voice.id ? (
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
                          </svg>
                        ) : (
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {/* Audio Recording */}
            {showVoiceSource === 'record' && (
              <div className="border-2 border-purple-200 rounded-lg p-6 bg-purple-50">
                <div className="space-y-4">
                  {/* Recording Controls */}
                  <div className="flex flex-col items-center space-y-4">
                    {!recordingBlob ? (
                      <>
                        <div className="text-5xl">{isRecording ? '🔴' : '🎤'}</div>
                        <button
                          onClick={isRecording ? stopRecording : startRecording}
                          className={`
                            px-6 py-3 rounded-lg font-medium transition-all
                            ${isRecording
                              ? 'bg-red-600 hover:bg-red-700 text-white'
                              : 'bg-purple-600 hover:bg-purple-700 text-white'
                            }
                          `}
                        >
                          {isRecording ? '⏹️ Stop Recording' : '🎤 Start Recording'}
                        </button>
                        {isRecording && (
                          <div className="text-sm text-gray-600 animate-pulse">
                            Recording... {recordingDuration.toFixed(1)}s
                          </div>
                        )}
                        <p className="text-xs text-gray-600 text-center max-w-md">
                          Record 5-30 seconds of clear speech for best voice cloning results.
                          Speak naturally and avoid background noise.
                        </p>
                      </>
                    ) : (
                      <>
                        <div className="text-5xl">✅</div>
                        <div className="text-center">
                          <p className="text-sm font-medium text-gray-900">Recording Complete</p>
                          <p className="text-xs text-gray-600 mt-1">
                            Duration: {recordingDuration.toFixed(1)}s
                          </p>
                        </div>

                        {/* Playback Controls */}
                        <div className="flex space-x-2">
                          <button
                            onClick={isPlayingRecording ? stopRecordingPlayback : playRecording}
                            className="px-4 py-2 bg-purple-100 hover:bg-purple-200 text-purple-700 rounded-lg text-sm font-medium transition-colors"
                          >
                            {isPlayingRecording ? '⏸️ Pause' : '▶️ Play'}
                          </button>
                          <button
                            onClick={clearRecording}
                            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
                          >
                            🗑️ Re-record
                          </button>
                        </div>

                        {/* Save to Library Option */}
                        <div className="w-full pt-4 border-t border-purple-200">
                          <label className="flex items-center space-x-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={saveToLibrary}
                              onChange={(e) => setSaveToLibrary(e.target.checked)}
                              className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                            />
                            <span className="text-sm font-medium text-gray-700">
                              Save this recording to voice library
                            </span>
                          </label>

                          {saveToLibrary && (
                            <input
                              type="text"
                              value={libraryVoiceName}
                              onChange={(e) => setLibraryVoiceName(e.target.value)}
                              placeholder="Enter voice name (e.g., My Voice, John's Voice)"
                              className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                            />
                          )}
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* File Upload */}
            {showVoiceSource === 'upload' && (
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`
                  border-2 border-dashed rounded-lg p-8 text-center transition-colors
                  ${
                    dragActive
                      ? 'border-purple-500 bg-purple-50'
                      : 'border-gray-300 bg-gray-50'
                  }
                `}
              >
                <input
                  type="file"
                  accept="audio/*"
                  onChange={handleFileChange}
                  className="hidden"
                  id="audio-upload"
                />
                <label htmlFor="audio-upload" className="cursor-pointer">
                  <div className="text-4xl mb-2">🎤</div>
                  <p className="text-sm text-gray-600">
                    {referenceAudio && !selectedGhanaianVoice && !selectedClonedVoice ? (
                      <span className="font-medium text-purple-600">
                        {referenceAudio.name}
                      </span>
                    ) : (
                      <>
                        Drop audio file here or{' '}
                        <span className="text-purple-600 font-medium">browse</span>
                      </>
                    )}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Supported: WAV, MP3, OGG (recommended: WAV, 5-30 seconds)
                  </p>
                </label>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-4">
            <button
              onClick={handleSynthesize}
              disabled={isLoading || !text.trim() || !referenceAudio}
              className={`
                flex-1 px-6 py-3 rounded-lg font-medium text-white
                ${
                  isLoading || !text.trim() || !referenceAudio
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-purple-600 hover:bg-purple-700 active:bg-purple-800'
                }
                transition-colors duration-200
              `}
            >
              {isLoading ? 'Cloning Voice...' : 'Clone Voice & Synthesize'}
            </button>
          </div>

          {/* Progress Bar (shown during synthesis) */}
          {isLoading && synthesisProgress > 0 && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <SynthesisProgress progress={synthesisProgress} stage={synthesisStage} />
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start">
                <span className="text-red-600 mr-2">⚠️</span>
                <div>
                  <h4 className="font-medium text-red-900">Voice Cloning Error</h4>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                  {error.includes('torchcodec') && (
                    <p className="text-xs text-red-600 mt-2">
                      Note: Voice cloning requires the torchcodec dependency to be installed.
                      This is a known issue and will be fixed in the next deployment.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Audio Player */}
          {audioUrl && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-purple-900">✓ Voice Cloning Complete</h4>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleDownload}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
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

              {/* Save to Library Option */}
              <div className="pt-4 border-t border-purple-200">
                <label className="flex items-center space-x-2 cursor-pointer mb-3">
                  <input
                    type="checkbox"
                    checked={saveSynthesizedToLibrary}
                    onChange={(e) => setSaveSynthesizedToLibrary(e.target.checked)}
                    className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                  />
                  <span className="text-sm font-medium text-gray-700">Save this synthesized voice to library</span>
                </label>

                {saveSynthesizedToLibrary && (
                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={synthesizedVoiceName}
                      onChange={(e) => setSynthesizedVoiceName(e.target.value)}
                      placeholder="Enter voice name (e.g., My Custom Voice)"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                    />
                    <button
                      onClick={handleSaveSynthesizedToLibrary}
                      disabled={!synthesizedVoiceName.trim()}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      💾 Save to Library
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* Export Format Modal */}
      <ExportFormatModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        audioBlob={audioBlob}
        filename={`tts_cloned_${Date.now()}`}
      />
    </div>
  );
};
