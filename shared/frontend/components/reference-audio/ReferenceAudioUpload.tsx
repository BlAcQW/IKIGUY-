/**
 * Reference Audio Upload Component
 * 
 * Allows users to upload reference audio files for zero-shot TTS providers
 * (StyleTTS2, Coqui XTTS, OpenVoice, F5-TTS) to use in audiobook narration.
 */

import React, { useState, useRef } from 'react';
import { Upload, X, Music, CheckCircle, AlertCircle, Loader2, Play, Pause } from 'lucide-react';
import toast from 'react-hot-toast';
import axios from 'axios';

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

interface ReferenceAudioUploadProps {
  apiBaseUrl: string;
  getAuthHeaders?: () => Promise<Record<string, string>>;
  onUploadSuccess?: (audio: ReferenceAudio) => void;
  onClose?: () => void;
  className?: string;
}

export const ReferenceAudioUpload: React.FC<ReferenceAudioUploadProps> = ({
  apiBaseUrl,
  getAuthHeaders,
  onUploadSuccess,
  onClose,
  className = '',
}) => {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);
  
  // Form fields
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [createVoice, setCreateVoice] = useState(true);
  const [gender, setGender] = useState<string>('neutral');
  const [language, setLanguage] = useState<string>('en');
  const [tags, setTags] = useState('');

  const fileInputRef = useRef<HTMLInputElement>(null);
  const previewAudioRef = useRef<HTMLAudioElement | null>(null);

  // Supported formats
  const ACCEPTED_FORMATS = ['.wav', '.mp3', '.ogg', '.flac', '.m4a'];
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

  const validateFile = (file: File): string | null => {
    // Check file type
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_FORMATS.includes(ext)) {
      return `Unsupported format. Please use: ${ACCEPTED_FORMATS.join(', ')}`;
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `File size exceeds ${MAX_FILE_SIZE / 1024 / 1024}MB limit`;
    }

    return null;
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const handleFileSelect = (file: File) => {
    const error = validateFile(file);
    if (error) {
      toast.error(error);
      return;
    }

    setAudioFile(file);
    
    // Auto-fill name if empty
    if (!name) {
      setName(file.name.replace(/\.[^/.]+$/, '')); // Remove extension
    }

    // Create preview URL
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);

    // Clean up previous audio element
    if (audioElement) {
      audioElement.pause();
      audioElement.src = '';
    }
  };

  const handleRemoveFile = () => {
    setAudioFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    if (audioElement) {
      audioElement.pause();
      audioElement.src = '';
      setAudioElement(null);
      setPlaying(false);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handlePlayPreview = async () => {
    if (!previewUrl) return;

    try {
      if (playing && audioElement) {
        audioElement.pause();
        setPlaying(false);
      } else {
        if (!previewAudioRef.current) {
          const audio = new Audio(previewUrl);
          previewAudioRef.current = audio;
          setAudioElement(audio);

          audio.onended = () => setPlaying(false);
          audio.onerror = () => {
            toast.error('Failed to play audio preview');
            setPlaying(false);
          };
        }

        await previewAudioRef.current.play();
        setPlaying(true);
      }
    } catch (error) {
      console.error('Error playing preview:', error);
      toast.error('Failed to play audio preview');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!audioFile) {
      toast.error('Please select an audio file');
      return;
    }

    if (!name.trim()) {
      toast.error('Please enter a name for the reference audio');
      return;
    }

    try {
      setUploading(true);
      toast.loading('Uploading reference audio...', { id: 'upload-ref-audio' });

      // Create FormData
      const formData = new FormData();
      formData.append('audio_file', audioFile);
      formData.append('name', name.trim());
      if (description.trim()) {
        formData.append('description', description.trim());
      }
      formData.append('create_voice', createVoice.toString());
      if (createVoice) {
        formData.append('gender', gender);
        formData.append('language', language);
        if (tags.trim()) {
          formData.append('tags', tags.trim());
        }
      }

      // Upload
      const headers: Record<string, string> = {};
      if (getAuthHeaders) {
        const authHeaders = await getAuthHeaders();
        Object.assign(headers, authHeaders);
      }
      
      const response = await axios.post(
        `${apiBaseUrl}/reference-audio/upload`,
        formData,
        {
          headers: {
            ...headers,
            'Content-Type': 'multipart/form-data',
          },
          timeout: 60000,
        }
      );
      const data = response.data;

      toast.success('Reference audio uploaded successfully!', { id: 'upload-ref-audio' });

      // Call success callback
      if (onUploadSuccess) {
        onUploadSuccess(data);
      }

      // Reset form
      handleRemoveFile();
      setName('');
      setDescription('');
      setTags('');
      setCreateVoice(true);
      setGender('neutral');
      setLanguage('en');

      // Close if callback provided
      if (onClose) {
        setTimeout(() => onClose(), 500);
      }

    } catch (error: any) {
      console.error('Upload error:', error);
      toast.error(
        error.response?.data?.detail || 'Failed to upload reference audio',
        { id: 'upload-ref-audio' }
      );
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
      if (previewAudioRef.current) {
        previewAudioRef.current.pause();
        previewAudioRef.current.src = '';
      }
    };
  }, [previewUrl]);

  return (
    <div className={`bg-gray-800/50 border border-gray-700 rounded-xl p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white mb-1">Upload Reference Audio</h3>
          <p className="text-sm text-gray-400">
            Upload audio for zero-shot TTS providers (StyleTTS2, Coqui XTTS, OpenVoice, F5-TTS)
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* File Drop Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !audioFile && fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
            dragging
              ? 'border-purple-500 bg-purple-500/10'
              : audioFile
              ? 'border-green-500 bg-green-500/10'
              : 'border-gray-600 hover:border-gray-500'
          } ${audioFile ? 'cursor-default' : ''}`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_FORMATS.join(',')}
            onChange={handleFileInputChange}
            className="hidden"
            disabled={uploading}
          />

          {audioFile ? (
            <div className="space-y-4">
              <div className="flex items-center justify-center gap-3">
                <Music className="w-10 h-10 text-green-400" />
                <div className="text-left">
                  <p className="text-white font-semibold">{audioFile.name}</p>
                  <p className="text-gray-400 text-sm">
                    {formatFileSize(audioFile.size)}
                    {audioFile.size > 0 && (
                      <span className="ml-2 text-gray-500">
                        ({((audioFile.size / MAX_FILE_SIZE) * 100).toFixed(0)}% of limit)
                      </span>
                    )}
                  </p>
                </div>
              </div>

              {/* Preview Controls */}
              {previewUrl && (
                <div className="flex items-center justify-center gap-3">
                  <button
                    type="button"
                    onClick={handlePlayPreview}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 border border-purple-500/30 rounded-lg text-purple-400 transition-colors"
                  >
                    {playing ? (
                      <>
                        <Pause className="w-4 h-4" />
                        <span>Pause Preview</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4" />
                        <span>Preview Audio</span>
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={handleRemoveFile}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-gray-300 transition-colors"
                    disabled={uploading}
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div>
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-white font-semibold mb-1">
                Drop your audio file here or click to browse
              </p>
              <p className="text-gray-400 text-sm">
                Supports WAV, MP3, OGG, FLAC, M4A (max {MAX_FILE_SIZE / 1024 / 1024}MB)
              </p>
            </div>
          )}
        </div>

        {/* Metadata Form */}
        {audioFile && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Name <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., My Narration Voice"
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                required
                disabled={uploading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description of this voice..."
                rows={3}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                disabled={uploading}
              />
            </div>

            {/* Voice Library Options */}
            <div className="border-t border-gray-700 pt-4">
              <label className="flex items-center gap-2 mb-4">
                <input
                  type="checkbox"
                  checked={createVoice}
                  onChange={(e) => setCreateVoice(e.target.checked)}
                  className="w-4 h-4 rounded bg-gray-700 border-gray-600 text-purple-500 focus:ring-purple-500"
                  disabled={uploading}
                />
                <span className="text-sm font-medium text-gray-300">
                  Create voice library entry
                </span>
              </label>

              {createVoice && (
                <div className="ml-6 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Gender
                      </label>
                      <select
                        value={gender}
                        onChange={(e) => setGender(e.target.value)}
                        className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={uploading}
                      >
                        <option value="neutral">Neutral</option>
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Language
                      </label>
                      <select
                        value={language}
                        onChange={(e) => setLanguage(e.target.value)}
                        className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={uploading}
                      >
                        <option value="en">English</option>
                        <option value="tw">Twi</option>
                        <option value="yo">Yoruba</option>
                        <option value="fr">French</option>
                        <option value="es">Spanish</option>
                        <option value="de">German</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Tags (comma-separated)
                    </label>
                    <input
                      type="text"
                      value={tags}
                      onChange={(e) => setTags(e.target.value)}
                      placeholder="e.g., narration, professional, audiobook"
                      className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                      disabled={uploading}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Submit Button */}
        {audioFile && (
          <div className="flex items-center gap-3 pt-4 border-t border-gray-700">
            <button
              type="submit"
              disabled={uploading || !name.trim()}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  <span>Upload Reference Audio</span>
                </>
              )}
            </button>
          </div>
        )}
      </form>
    </div>
  );
};
