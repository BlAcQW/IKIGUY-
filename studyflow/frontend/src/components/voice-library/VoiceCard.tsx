/**
 * VoiceCard Component
 *
 * Displays a single voice in a card format with preview, stats, and actions.
 * Used in voice galleries and browse interfaces across all KasaAI apps.
 *
 * Usage:
 * ```tsx
 * import { VoiceCard } from '@/components/voice-library/VoiceCard';
 *
 * <VoiceCard
 *   voice={voiceData}
 *   onSelect={(voice) => handleVoiceSelect(voice)}
 *   onFavorite={(voiceId) => handleFavorite(voiceId)}
 *   showActions={true}
 * />
 * ```
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Volume2,
  Star,
  Heart,
  Play,
  Pause,
  Loader2,
  Eye,
  TrendingUp,
  Globe,
  User,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Voice {
  voice_id: string;
  name: string;
  description?: string;
  characteristics?: {
    gender?: string;
    language?: string;
    accent?: string;
    dialect?: string;
    tone?: string;
    pace?: string;
  };
  metadata?: {
    featured?: boolean;
    verified?: boolean;
    tags?: string[];
    categories?: string[];
  };
  stats?: {
    views?: number;
    uses?: number;
    favorites?: number;
    rating?: {
      average?: number;
      count?: number;
    };
  };
  files?: {
    preview?: {
      url?: string;
    };
  };
  access?: {
    visibility?: string;
  };
  owner?: {
    user_id?: string;
  };
}

interface VoiceCardProps {
  voice: Voice;
  onSelect?: (voice: Voice) => void;
  onFavorite?: (voiceId: string, isFavorite: boolean) => void;
  onPreview?: (voice: Voice) => void;
  isFavorite?: boolean;
  isSelected?: boolean;
  showActions?: boolean;
  showStats?: boolean;
  compact?: boolean;
  className?: string;
}

export const VoiceCard: React.FC<VoiceCardProps> = ({
  voice,
  onSelect,
  onFavorite,
  onPreview,
  isFavorite = false,
  isSelected = false,
  showActions = true,
  showStats = true,
  compact = false,
  className = '',
}) => {
  const [previewPlaying, setPreviewPlaying] = useState(false);
  const [favoriteLoading, setFavoriteLoading] = useState(false);

  const handlePreview = async (e: React.MouseEvent) => {
    e.stopPropagation();

    if (onPreview) {
      onPreview(voice);
      return;
    }

    if (!voice.files?.preview?.url) {
      console.warn('No preview available');
      return;
    }

    try {
      setPreviewPlaying(true);
      const audio = new Audio(voice.files.preview.url);

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

  const handleFavorite = async (e: React.MouseEvent) => {
    e.stopPropagation();

    if (!onFavorite) return;

    try {
      setFavoriteLoading(true);
      await onFavorite(voice.voice_id, !isFavorite);
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    } finally {
      setFavoriteLoading(false);
    }
  };

  const handleSelect = () => {
    onSelect?.(voice);
  };

  const getLanguageName = (code?: string): string => {
    if (!code) return 'Unknown';
    const languages: Record<string, string> = {
      'en': 'English',
      'tw': 'Twi',
      'ak': 'Akan',
      'es': 'Spanish',
      'fr': 'French',
      'de': 'German',
    };
    return languages[code] || code.toUpperCase();
  };

  return (
    <Card
      className={cn(
        'relative cursor-pointer transition-all hover:shadow-lg',
        isSelected && 'ring-2 ring-primary',
        compact && 'max-w-sm',
        className
      )}
      onClick={handleSelect}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="flex items-center gap-2 text-lg">
              {voice.name}
              {voice.metadata?.featured && (
                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" title="Featured voice" />
              )}
              {voice.metadata?.verified && (
                <Badge variant="secondary" className="text-xs">
                  Verified
                </Badge>
              )}
            </CardTitle>

            {voice.description && !compact && (
              <CardDescription className="mt-1 line-clamp-2">
                {voice.description}
              </CardDescription>
            )}
          </div>

          {showActions && (
            <div className="flex items-center gap-1 ml-2">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={handlePreview}
                disabled={previewPlaying || !voice.files?.preview?.url}
                title="Preview voice"
              >
                {previewPlaying ? (
                  <Pause className="h-4 w-4" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
              </Button>

              {onFavorite && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={handleFavorite}
                  disabled={favoriteLoading}
                  title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
                >
                  {favoriteLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Heart
                      className={cn(
                        'h-4 w-4',
                        isFavorite && 'fill-red-500 text-red-500'
                      )}
                    />
                  )}
                </Button>
              )}
            </div>
          )}
        </div>
      </CardHeader>

      {!compact && (
        <>
          <CardContent className="pb-3">
            <div className="flex flex-wrap gap-2">
              {voice.characteristics?.gender && (
                <Badge variant="outline">
                  <User className="h-3 w-3 mr-1" />
                  {voice.characteristics.gender}
                </Badge>
              )}

              {voice.characteristics?.language && (
                <Badge variant="outline">
                  <Globe className="h-3 w-3 mr-1" />
                  {getLanguageName(voice.characteristics.language)}
                </Badge>
              )}

              {voice.characteristics?.accent && (
                <Badge variant="secondary">
                  {voice.characteristics.accent}
                </Badge>
              )}

              {voice.characteristics?.dialect && (
                <Badge variant="secondary">
                  {voice.characteristics.dialect}
                </Badge>
              )}

              {voice.characteristics?.tone && (
                <Badge variant="outline">{voice.characteristics.tone}</Badge>
              )}

              {voice.characteristics?.pace && (
                <Badge variant="outline">{voice.characteristics.pace}</Badge>
              )}
            </div>

            {voice.metadata?.tags && voice.metadata.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {voice.metadata.tags.slice(0, 3).map((tag, idx) => (
                  <Badge key={idx} variant="outline" className="text-xs">
                    {tag}
                  </Badge>
                ))}
                {voice.metadata.tags.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{voice.metadata.tags.length - 3}
                  </Badge>
                )}
              </div>
            )}
          </CardContent>

          {showStats && (
            <>
              <Separator />
              <CardFooter className="pt-3 pb-3">
                <div className="flex items-center justify-between w-full text-sm text-muted-foreground">
                  <div className="flex items-center gap-4">
                    {voice.stats?.rating?.average && voice.stats.rating.average > 0 && (
                      <div className="flex items-center gap-1" title="Average rating">
                        <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                        <span>{voice.stats.rating.average.toFixed(1)}</span>
                        {voice.stats.rating.count && (
                          <span className="text-xs">({voice.stats.rating.count})</span>
                        )}
                      </div>
                    )}

                    {voice.stats?.uses !== undefined && (
                      <div className="flex items-center gap-1" title="Total uses">
                        <TrendingUp className="h-3 w-3" />
                        <span>{voice.stats.uses.toLocaleString()}</span>
                      </div>
                    )}

                    {voice.stats?.favorites !== undefined && voice.stats.favorites > 0 && (
                      <div className="flex items-center gap-1" title="Favorites">
                        <Heart className="h-3 w-3" />
                        <span>{voice.stats.favorites}</span>
                      </div>
                    )}

                    {voice.stats?.views !== undefined && (
                      <div className="flex items-center gap-1" title="Views">
                        <Eye className="h-3 w-3" />
                        <span>{voice.stats.views.toLocaleString()}</span>
                      </div>
                    )}
                  </div>

                  {voice.access?.visibility && (
                    <Badge variant={voice.access.visibility === 'public' ? 'default' : 'secondary'}>
                      {voice.access.visibility}
                    </Badge>
                  )}
                </div>
              </CardFooter>
            </>
          )}
        </>
      )}
    </Card>
  );
};

export default VoiceCard;
