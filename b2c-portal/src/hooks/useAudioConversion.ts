/**
 * Audio Conversion Hook
 *
 * Custom hook for converting audio between different formats.
 * Created: 2025-10-27
 * Sprint 4: Advanced Features (Phase 9)
 */

import { useState, useCallback } from 'react';
import { API_BASE_URL } from '../config/api-config';

type AudioFormat = 'wav' | 'mp3' | 'ogg' | 'flac' | 'm4a';

interface ConvertAudioRequest {
  audioBase64: string;
  sourceFormat: AudioFormat;
  targetFormat: AudioFormat;
  bitrate?: string;
}

interface UseAudioConversionReturn {
  convertAudio: (
    audioBlob: Blob,
    sourceFormat: AudioFormat,
    targetFormat: AudioFormat,
    bitrate?: string
  ) => Promise<Blob | null>;
  batchConvert: (
    audioBlob: Blob,
    sourceFormat: AudioFormat,
    targetFormats: AudioFormat[],
    bitrate?: string
  ) => Promise<Record<AudioFormat, Blob> | null>;
  isConverting: boolean;
  error: string | null;
}

export const useAudioConversion = (): UseAudioConversionReturn => {
  const [isConverting, setIsConverting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const convertAudio = useCallback(
    async (
      audioBlob: Blob,
      sourceFormat: AudioFormat,
      targetFormat: AudioFormat,
      bitrate: string = '192k'
    ): Promise<Blob | null> => {
      setIsConverting(true);
      setError(null);

      try {
        // Convert blob to base64
        const arrayBuffer = await audioBlob.arrayBuffer();
        const uint8Array = new Uint8Array(arrayBuffer);
        const binaryString = Array.from(uint8Array)
          .map((byte) => String.fromCharCode(byte))
          .join('');
        const audioBase64 = btoa(binaryString);

        // Call conversion API
        const response = await fetch(`${API_BASE_URL}/api/audio/convert`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            audio_base64: audioBase64,
            source_format: sourceFormat,
            target_format: targetFormat,
            bitrate: bitrate,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Conversion failed');
        }

        const data = await response.json();

        // Decode base64 to blob
        const convertedBinaryString = atob(data.audio_base64);
        const convertedBytes = new Uint8Array(convertedBinaryString.length);
        for (let i = 0; i < convertedBinaryString.length; i++) {
          convertedBytes[i] = convertedBinaryString.charCodeAt(i);
        }

        // Determine MIME type
        const mimeTypes: Record<AudioFormat, string> = {
          wav: 'audio/wav',
          mp3: 'audio/mpeg',
          ogg: 'audio/ogg',
          flac: 'audio/flac',
          m4a: 'audio/mp4',
        };

        return new Blob([convertedBytes], { type: mimeTypes[targetFormat] });
      } catch (err: any) {
        const errorMessage = err.message || 'Conversion failed';
        setError(errorMessage);
        console.error('Audio conversion error:', err);
        return null;
      } finally {
        setIsConverting(false);
      }
    },
    []
  );

  const batchConvert = useCallback(
    async (
      audioBlob: Blob,
      sourceFormat: AudioFormat,
      targetFormats: AudioFormat[],
      bitrate: string = '192k'
    ): Promise<Record<AudioFormat, Blob> | null> => {
      setIsConverting(true);
      setError(null);

      try {
        // Convert blob to base64
        const arrayBuffer = await audioBlob.arrayBuffer();
        const uint8Array = new Uint8Array(arrayBuffer);
        const binaryString = Array.from(uint8Array)
          .map((byte) => String.fromCharCode(byte))
          .join('');
        const audioBase64 = btoa(binaryString);

        // Call batch conversion API
        const response = await fetch(`${API_BASE_URL}/api/audio/convert/batch`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            audio_base64: audioBase64,
            source_format: sourceFormat,
            target_formats: targetFormats,
            bitrate: bitrate,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Batch conversion failed');
        }

        const data = await response.json();

        // Decode all formats to blobs
        const results: Record<AudioFormat, Blob> = {} as any;
        const mimeTypes: Record<AudioFormat, string> = {
          wav: 'audio/wav',
          mp3: 'audio/mpeg',
          ogg: 'audio/ogg',
          flac: 'audio/flac',
          m4a: 'audio/mp4',
        };

        for (const [format, base64Audio] of Object.entries(data.results)) {
          const convertedBinaryString = atob(base64Audio as string);
          const convertedBytes = new Uint8Array(convertedBinaryString.length);
          for (let i = 0; i < convertedBinaryString.length; i++) {
            convertedBytes[i] = convertedBinaryString.charCodeAt(i);
          }

          results[format as AudioFormat] = new Blob([convertedBytes], {
            type: mimeTypes[format as AudioFormat],
          });
        }

        return results;
      } catch (err: any) {
        const errorMessage = err.message || 'Batch conversion failed';
        setError(errorMessage);
        console.error('Batch conversion error:', err);
        return null;
      } finally {
        setIsConverting(false);
      }
    },
    []
  );

  return {
    convertAudio,
    batchConvert,
    isConverting,
    error,
  };
};
