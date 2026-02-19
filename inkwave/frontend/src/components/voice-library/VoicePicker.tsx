/**
 * VoicePicker Component
 *
 * Reusable voice selection component for all KasaAI apps.
 * Allows users to browse and select voices from the centralized voice library.
 *
 * Usage:
 * ```tsx
 * import { VoicePicker } from '@/components/voice-library/VoicePicker';
 *
 * <VoicePicker
 *   value={selectedVoiceId}
 *   onChange={(voiceId) => setSelectedVoiceId(voiceId)}
 *   filters={{ language: 'en', gender: 'female' }}
 * />
 * ```
 */

import React, { useState, useEffect } from 'react';
import { useVoiceLibrary } from '@/hooks/useVoiceLibrary';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Volume2, Star, Loader2 } from 'lucide-react';

interface Voice {
  voice_id: string;
  name: string;
  description?: string;
  characteristics?: {
    gender?: string;
    language?: string;
    accent?: string;
    dialect?: string;
  };
  metadata?: {
    featured?: boolean;
    tags?: string[];
  };
  stats?: {
    rating?: {
      average?: number;
    };
    uses?: number;
  };
}

interface VoicePickerProps {
  value?: string;
  onChange?: (voiceId: string, voice?: Voice) => void;
  filters?: {
    gender?: string;
    language?: string;
    accent?: string;
    categories?: string[];
    featured?: boolean;
  };
  placeholder?: string;
  showPreview?: boolean;
  className?: string;
}

export const VoicePicker: React.FC<VoicePickerProps> = ({
  value,
  onChange,
  filters = {},
  placeholder = 'Select a voice',
  showPreview = true,
  className = '',
}) => {
  const { fetchVoices } = useVoiceLibrary();
  const [voices, setVoices] = useState<Voice[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedVoice, setSelectedVoice] = useState<Voice | null>(null);
  const [previewPlaying, setPreviewPlaying] = useState(false);

  useEffect(() => {
    loadVoices();
  }, [JSON.stringify(filters)]);

  useEffect(() => {
    if (value && voices.length > 0) {
      const voice = voices.find(v => v.voice_id === value);
      setSelectedVoice(voice || null);
    }
  }, [value, voices]);

  const loadVoices = async () => {
    try {
      setLoading(true);
      const data = await fetchVoices(filters, 0, 100);
      if (data && data.voices) {
        setVoices(data.voices);
      }
    } catch (error) {
      console.error('Failed to load voices:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceSelect = (voiceId: string) => {
    const voice = voices.find(v => v.voice_id === voiceId);
    setSelectedVoice(voice || null);
    onChange?.(voiceId, voice);
  };

  const handlePreview = async (e: React.MouseEvent) => {
    e.stopPropagation();

    if (!selectedVoice?.files?.preview?.url) {
      console.warn('No preview available for this voice');
      return;
    }

    try {
      setPreviewPlaying(true);
      const audio = new Audio(selectedVoice.files.preview.url);

      audio.onended = () => setPreviewPlaying(false);
      audio.onerror = () => {
        setPreviewPlaying(false);
        console.error('Failed to play preview');
      };

      await audio.play();
    } catch (error) {
      console.error('Error playing preview:', error);
      setPreviewPlaying(false);
    }
  };

  const groupVoicesByLanguage = () => {
    const grouped: Record<string, Voice[]> = {};

    voices.forEach(voice => {
      const lang = voice.characteristics?.language || 'other';
      if (!grouped[lang]) {
        grouped[lang] = [];
      }
      grouped[lang].push(voice);
    });

    return grouped;
  };

  const getLanguageName = (code: string): string => {
    const languages: Record<string, string> = {
      'en': 'English',
      'tw': 'Twi',
      'ak': 'Akan',
      'es': 'Spanish',
      'fr': 'French',
      'de': 'German',
      'other': 'Other Languages'
    };
    return languages[code] || code.toUpperCase();
  };

  const groupedVoices = groupVoicesByLanguage();

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Select value={value} onValueChange={handleVoiceSelect} disabled={loading}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder={loading ? 'Loading voices...' : placeholder}>
            {selectedVoice && (
              <div className="flex items-center gap-2">
                <span className="font-medium">{selectedVoice.name}</span>
                {selectedVoice.metadata?.featured && (
                  <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                )}
                {selectedVoice.characteristics?.gender && (
                  <Badge variant="outline" className="text-xs">
                    {selectedVoice.characteristics.gender}
                  </Badge>
                )}
              </div>
            )}
          </SelectValue>
        </SelectTrigger>

        <SelectContent className="max-h-[400px]">
          {loading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="ml-2 text-sm text-muted-foreground">Loading voices...</span>
            </div>
          ) : Object.keys(groupedVoices).length === 0 ? (
            <div className="py-4 text-center text-sm text-muted-foreground">
              No voices available
            </div>
          ) : (
            Object.entries(groupedVoices).map(([langCode, langVoices]) => (
              <SelectGroup key={langCode}>
                <SelectLabel className="font-semibold">
                  {getLanguageName(langCode)}
                </SelectLabel>
                {langVoices.map((voice) => (
                  <SelectItem key={voice.voice_id} value={voice.voice_id}>
                    <div className="flex items-center gap-2">
                      <span>{voice.name}</span>

                      {voice.metadata?.featured && (
                        <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                      )}

                      {voice.characteristics?.gender && (
                        <Badge variant="outline" className="text-xs">
                          {voice.characteristics.gender}
                        </Badge>
                      )}

                      {voice.characteristics?.accent && (
                        <Badge variant="secondary" className="text-xs">
                          {voice.characteristics.accent}
                        </Badge>
                      )}

                      {voice.stats?.rating?.average && voice.stats.rating.average > 0 && (
                        <span className="text-xs text-muted-foreground">
                          ⭐ {voice.stats.rating.average.toFixed(1)}
                        </span>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectGroup>
            ))
          )}
        </SelectContent>
      </Select>

      {showPreview && selectedVoice && (
        <Button
          variant="outline"
          size="icon"
          onClick={handlePreview}
          disabled={previewPlaying || !selectedVoice.files?.preview?.url}
          title="Preview voice"
        >
          {previewPlaying ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Volume2 className="h-4 w-4" />
          )}
        </Button>
      )}
    </div>
  );
};

export default VoicePicker;
