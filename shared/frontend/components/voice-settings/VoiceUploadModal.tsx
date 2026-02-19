/**
 * Voice Upload Modal Component
 *
 * Modal for uploading voice samples for cloning.
 * Part of @kasaai/shared-frontend library.
 */

import React, { useState } from 'react';

export interface VoiceUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadComplete?: (voiceId: string) => void;
  className?: string;
}

export const VoiceUploadModal: React.FC<VoiceUploadModalProps> = ({
  isOpen,
  onClose,
  onUploadComplete,
  className = '',
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [language, setLanguage] = useState('English');
  const [gender, setGender] = useState('');
  const [tags, setTags] = useState('');
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/x-m4a', 'audio/flac', 'audio/ogg'];
      if (!allowedTypes.includes(file.type) && !file.name.match(/\.(wav|mp3|m4a|flac|ogg)$/i)) {
        setError('Invalid file type. Please upload WAV, MP3, M4A, FLAC, or OGG files.');
        return;
      }

      // Validate file size (50MB max)
      if (file.size > 50 * 1024 * 1024) {
        setError('File too large. Maximum size is 50MB.');
        return;
      }

      setAudioFile(file);
      setError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      setError('Please enter a voice name');
      return;
    }

    if (!audioFile) {
      setError('Please select an audio file');
      return;
    }

    setIsUploading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const formData = new FormData();
      formData.append('name', name);
      formData.append('description', description);
      formData.append('language', language);
      formData.append('gender', gender);
      formData.append('tags', tags);
      formData.append('audio_file', audioFile);

      const response = await fetch('/api/v1/voice-library/voices/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      setSuccess(`Voice uploaded successfully! Processing: ${data.voice_id}`);

      // Reset form
      setName('');
      setDescription('');
      setLanguage('English');
      setGender('');
      setTags('');
      setAudioFile(null);

      // Call completion callback
      if (onUploadComplete) {
        onUploadComplete(data.voice_id);
      }

      // Close modal after 2 seconds
      setTimeout(() => {
        onClose();
        setSuccess('');
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Failed to upload voice');
    } finally {
      setIsUploading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className={`bg-white rounded-lg shadow-xl max-w-2xl w-full p-6 ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Upload Voice Sample</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
            disabled={isUploading}
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Voice Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Voice Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="e.g., Pastor John"
              required
              disabled={isUploading}
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="Warm and authoritative voice for sermons"
              rows={3}
              disabled={isUploading}
            />
          </div>

          {/* Language and Gender */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                disabled={isUploading}
              >
                <option value="English">English</option>
                <option value="Spanish">Spanish</option>
                <option value="French">French</option>
                <option value="German">German</option>
                <option value="Arabic">Arabic</option>
                <option value="Swahili">Swahili</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Gender
              </label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                disabled={isUploading}
              >
                <option value="">Select gender</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="neutral">Neutral</option>
              </select>
            </div>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tags (comma-separated)
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="sermon, authoritative, warm"
              disabled={isUploading}
            />
          </div>

          {/* Audio File */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Audio Sample * (10-60 seconds)
            </label>
            <input
              type="file"
              accept=".wav,.mp3,.m4a,.flac,.ogg,audio/*"
              onChange={handleFileChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              required
              disabled={isUploading}
            />
            <p className="text-xs text-gray-500 mt-1">
              Supported formats: WAV, MP3, M4A, FLAC, OGG (max 50MB)
            </p>
            {audioFile && (
              <p className="text-sm text-green-600 mt-1">
                ✓ Selected: {audioFile.name} ({(audioFile.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
          </div>

          {/* Requirements */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">Recording Tips:</h3>
            <ul className="text-xs text-blue-800 space-y-1 list-disc list-inside">
              <li>Use a quiet environment with minimal background noise</li>
              <li>Speak clearly and naturally</li>
              <li>Record 10-60 seconds of continuous speech</li>
              <li>Avoid music or sound effects in the recording</li>
            </ul>
          </div>

          {/* Error/Success Messages */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
              {error}
            </div>
          )}

          {success && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md text-sm">
              {success}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 justify-end pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
              disabled={isUploading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isUploading || !audioFile}
            >
              {isUploading ? 'Uploading...' : 'Upload Voice'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
