/**
 * Reference Audio List Component
 * 
 * Displays and manages reference audio files for zero-shot TTS providers.
 */

import React, { useState, useEffect } from 'react';
import { Music, Trash2, Play, Pause, Clock, Upload, Loader2, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import axios from 'axios';
import { ReferenceAudioUpload } from './ReferenceAudioUpload';

interface ReferenceAudio {
  reference_audio_id: string;
  name: string;
  description?: string;
  audio_url: string;
  file_size_bytes: number;
  duration_seconds?: number;
  compatible_providers: string[];
  created_at: string;
  voice_id?: string;
}

interface ReferenceAudioListProps {
  apiBaseUrl: string;
  getAuthHeaders?: () => Promise<Record<string, string>>;
  onSelect?: (audio: ReferenceAudio) => void;
  selectedId?: string;
  showUpload?: boolean;
  className?: string;
}

export const ReferenceAudioList: React.FC<ReferenceAudioListProps> = ({
  apiBaseUrl,
  getAuthHeaders,
  onSelect,
  selectedId,
  showUpload = true,
  className = '',
}) => {
  const [referenceAudios, setReferenceAudios] = useState<ReferenceAudio[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [audioElements, setAudioElements] = useState<Map<string, HTMLAudioElement>>(new Map());
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadReferenceAudios = async () => {
    try {
      setLoading(true);
      const headers: Record<string, string> = {};
      if (getAuthHeaders) {
        const authHeaders = await getAuthHeaders();
        Object.assign(headers, authHeaders);
      }
      
      const response = await axios.get(
        `${apiBaseUrl}/reference-audio/`,
        { headers }
      );
      // Ensure reference_audio is always an array and handle different response formats
      const referenceAudioData = response.data?.reference_audio;
      const audioList = Array.isArray(referenceAudioData)
        ? referenceAudioData
        : (Array.isArray(response.data) ? response.data : []);

      // Ensure each audio's compatible_providers is always an array
      // Reason: Backend may return null, undefined, string, or array - normalize to always be an array
      const normalizedAudioList = audioList
        .filter((audio: any) => audio != null)
        .map((audio: any) => ({
          ...audio,
          compatible_providers: Array.isArray(audio?.compatible_providers)
            ? audio.compatible_providers
            : (audio?.compatible_providers ? [audio.compatible_providers] : [])
        }));

      setReferenceAudios(normalizedAudioList);
    } catch (error: any) {
      console.error('Failed to load reference audio:', error);
      toast.error('Failed to load reference audio files');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReferenceAudios();
  }, []);

  const handlePlay = async (audio: ReferenceAudio) => {
    try {
      // Stop any currently playing audio
      audioElements.forEach((element, id) => {
        if (id !== audio.reference_audio_id) {
          element.pause();
          element.currentTime = 0;
        }
      });

      if (playingId === audio.reference_audio_id) {
        // Pause if already playing
        const element = audioElements.get(audio.reference_audio_id);
        if (element) {
          element.pause();
          setPlayingId(null);
        }
      } else {
        // Play new audio
        const audioUrl = audio.audio_url.startsWith('http') 
          ? audio.audio_url 
          : `${apiBaseUrl}${audio.audio_url}`;

        let element = audioElements.get(audio.reference_audio_id);
        if (!element) {
          element = new Audio(audioUrl);
          setAudioElements(prev => new Map(prev).set(audio.reference_audio_id, element!));
          
          element.onended = () => setPlayingId(null);
          element.onerror = () => {
            toast.error('Failed to play audio');
            setPlayingId(null);
          };
        }

        await element.play();
        setPlayingId(audio.reference_audio_id);
      }
    } catch (error) {
      console.error('Error playing audio:', error);
      toast.error('Failed to play audio');
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!confirm('Are you sure you want to delete this reference audio?')) {
      return;
    }

    try {
      setDeletingId(id);
      const headers: Record<string, string> = {};
      if (getAuthHeaders) {
        const authHeaders = await getAuthHeaders();
        Object.assign(headers, authHeaders);
      }
      
      await axios.delete(
        `${apiBaseUrl}/reference-audio/${id}`,
        { headers }
      );
      
      // Stop audio if playing
      const element = audioElements.get(id);
      if (element) {
        element.pause();
        element.src = '';
      }
      audioElements.delete(id);
      setAudioElements(new Map(audioElements));

      if (playingId === id) {
        setPlayingId(null);
      }

      toast.success('Reference audio deleted');
      loadReferenceAudios();
    } catch (error: any) {
      console.error('Failed to delete reference audio:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete reference audio');
    } finally {
      setDeletingId(null);
    }
  };

  const handleUploadSuccess = () => {
    setShowUploadModal(false);
    loadReferenceAudios();
  };

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return 'Unknown';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      audioElements.forEach(element => {
        element.pause();
        element.src = '';
      });
    };
  }, []);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white mb-1">Reference Audio Library</h3>
          <p className="text-sm text-gray-400">
            Upload reference audio for zero-shot TTS providers (StyleTTS2, Coqui XTTS, OpenVoice, F5-TTS)
          </p>
        </div>
        {showUpload && (
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white font-medium rounded-lg transition-colors"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Audio</span>
          </button>
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <ReferenceAudioUpload
              apiBaseUrl={apiBaseUrl}
              getAuthHeaders={getAuthHeaders}
              onUploadSuccess={handleUploadSuccess}
              onClose={() => setShowUploadModal(false)}
            />
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
        </div>
      )}

      {/* Empty State */}
      {!loading && referenceAudios.length === 0 && (
        <div className="text-center py-12 bg-gray-800/50 border border-gray-700 rounded-xl">
          <Music className="w-12 h-12 text-gray-500 mx-auto mb-4" />
          <p className="text-gray-400 mb-2">No reference audio uploaded yet</p>
          <p className="text-sm text-gray-500 mb-4">
            Upload reference audio files to use with zero-shot TTS providers
          </p>
          {showUpload && (
            <button
              onClick={() => setShowUploadModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white font-medium rounded-lg transition-colors"
            >
              <Upload className="w-4 h-4" />
              <span>Upload Your First Audio</span>
            </button>
          )}
        </div>
      )}

      {/* Reference Audio Grid */}
      {!loading && referenceAudios.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {referenceAudios.map((audio) => (
            <div
              key={audio.reference_audio_id}
              onClick={() => onSelect?.(audio)}
              className={`relative p-4 bg-gray-800/50 border rounded-xl cursor-pointer transition-all ${
                selectedId === audio.reference_audio_id
                  ? 'border-purple-500 ring-2 ring-purple-500/30'
                  : 'border-gray-700 hover:border-gray-600'
              }`}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold text-white truncate mb-1">{audio.name}</h4>
                  {audio.description && (
                    <p className="text-sm text-gray-400 line-clamp-2">{audio.description}</p>
                  )}
                </div>
                <button
                  onClick={(e) => handleDelete(audio.reference_audio_id, e)}
                  disabled={deletingId === audio.reference_audio_id}
                  className="ml-2 p-1.5 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50"
                  title="Delete"
                >
                  {deletingId === audio.reference_audio_id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                </button>
              </div>

              {/* Metadata */}
              <div className="flex items-center gap-4 text-sm text-gray-400 mb-3">
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  <span>{formatDuration(audio.duration_seconds)}</span>
                </div>
                <span>{formatFileSize(audio.file_size_bytes)}</span>
              </div>

              {/* Compatible Providers */}
              {audio.compatible_providers && Array.isArray(audio.compatible_providers) && audio.compatible_providers.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-3">
                  {audio.compatible_providers.slice(0, 3).map((provider) => (
                    <span
                      key={provider}
                      className="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-400 rounded"
                    >
                      {provider}
                    </span>
                  ))}
                  {audio.compatible_providers.length > 3 && (
                    <span className="px-2 py-0.5 text-xs bg-gray-700 text-gray-400 rounded">
                      +{audio.compatible_providers.length - 3}
                    </span>
                  )}
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center gap-2 pt-3 border-t border-gray-700">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handlePlay(audio);
                  }}
                  className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors text-sm"
                >
                  {playingId === audio.reference_audio_id ? (
                    <>
                      <Pause className="w-3 h-3" />
                      <span>Pause</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-3 h-3" />
                      <span>Play</span>
                    </>
                  )}
                </button>
                {audio.voice_id && (
                  <span className="text-xs text-gray-500">
                    Linked to voice library
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
