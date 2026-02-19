/**
 * Export Format Modal Component
 *
 * Modal for exporting audio in different formats (MP3, OGG, FLAC, M4A).
 * Created: 2025-10-27
 * Sprint 4: Advanced Features (Phase 9)
 */

import React, { useState } from 'react';
import { useAudioConversion } from '../../hooks/useAudioConversion';

type AudioFormat = 'wav' | 'mp3' | 'ogg' | 'flac' | 'm4a';

interface ExportFormatModalProps {
  isOpen: boolean;
  onClose: () => void;
  audioBlob: Blob | null;
  filename?: string;
}

interface FormatOption {
  format: AudioFormat;
  name: string;
  description: string;
  icon: string;
  bitrates?: string[];
}

const formatOptions: FormatOption[] = [
  {
    format: 'wav',
    name: 'WAV (Lossless)',
    description: 'Uncompressed audio, highest quality, largest file size',
    icon: '🎵',
  },
  {
    format: 'mp3',
    name: 'MP3',
    description: 'Widely compatible, good quality, smaller file size',
    icon: '🎧',
    bitrates: ['128k', '192k', '256k', '320k'],
  },
  {
    format: 'ogg',
    name: 'OGG Vorbis',
    description: 'Open-source, good quality, smaller file size',
    icon: '🔊',
    bitrates: ['128k', '192k', '256k', '320k'],
  },
  {
    format: 'flac',
    name: 'FLAC (Lossless)',
    description: 'Lossless compression, smaller than WAV, perfect quality',
    icon: '💎',
  },
  {
    format: 'm4a',
    name: 'M4A/AAC',
    description: 'Apple/iTunes format, good quality and compatibility',
    icon: '🍎',
    bitrates: ['128k', '192k', '256k', '320k'],
  },
];

export const ExportFormatModal: React.FC<ExportFormatModalProps> = ({
  isOpen,
  onClose,
  audioBlob,
  filename = 'audio',
}) => {
  const [selectedFormat, setSelectedFormat] = useState<AudioFormat>('mp3');
  const [selectedBitrate, setSelectedBitrate] = useState('192k');
  const { convertAudio, isConverting, error } = useAudioConversion();

  if (!isOpen) return null;

  const handleExport = async () => {
    if (!audioBlob) {
      alert('No audio to export');
      return;
    }

    try {
      let exportBlob: Blob | null = audioBlob;

      // Convert if not WAV
      if (selectedFormat !== 'wav') {
        exportBlob = await convertAudio(
          audioBlob,
          'wav', // Assume source is WAV
          selectedFormat,
          selectedBitrate
        );
      }

      if (exportBlob) {
        // Download
        const url = URL.createObjectURL(exportBlob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filename}.${selectedFormat}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        // Close modal after successful export
        onClose();
      }
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const selectedFormatOption = formatOptions.find((f) => f.format === selectedFormat);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto m-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Export Audio</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Format Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Select Format
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {formatOptions.map((option) => (
                <button
                  key={option.format}
                  onClick={() => setSelectedFormat(option.format)}
                  className={`p-4 rounded-lg border-2 text-left transition-all ${
                    selectedFormat === option.format
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <span className="text-2xl">{option.icon}</span>
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{option.name}</div>
                      <div className="text-xs text-gray-600 mt-1">
                        {option.description}
                      </div>
                    </div>
                    {selectedFormat === option.format && (
                      <span className="text-indigo-600">✓</span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Bitrate Selection (for lossy formats) */}
          {selectedFormatOption?.bitrates && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Quality (Bitrate)
              </label>
              <div className="flex space-x-2">
                {selectedFormatOption.bitrates.map((bitrate) => (
                  <button
                    key={bitrate}
                    onClick={() => setSelectedBitrate(bitrate)}
                    className={`px-4 py-2 rounded-lg border-2 text-sm font-medium transition-all ${
                      selectedBitrate === bitrate
                        ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                        : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    {bitrate}
                  </button>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Higher bitrate = better quality but larger file size
              </p>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-2">
              <span className="text-blue-600">ℹ️</span>
              <div className="text-xs text-blue-700">
                <p className="font-medium mb-1">Format Guide:</p>
                <ul className="space-y-1">
                  <li>• <strong>WAV/FLAC</strong>: Best for archiving and editing</li>
                  <li>• <strong>MP3</strong>: Most compatible across all devices</li>
                  <li>• <strong>OGG</strong>: Better quality than MP3 at same bitrate</li>
                  <li>• <strong>M4A</strong>: Great for Apple devices and iTunes</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            disabled={isConverting}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            disabled={isConverting || !audioBlob}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isConverting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Converting...</span>
              </>
            ) : (
              <>
                <span>📥</span>
                <span>Export as {selectedFormat.toUpperCase()}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
