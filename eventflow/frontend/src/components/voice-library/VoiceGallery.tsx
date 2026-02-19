/**
 * VoiceGallery Component
 *
 * Complete voice browsing interface with search, filters, and voice cards.
 * Integrates VoiceFilters, VoiceCard, and useVoiceLibrary hook.
 *
 * Usage:
 * ```tsx
 * import { VoiceGallery } from '@/components/voice-library/VoiceGallery';
 *
 * <VoiceGallery
 *   onVoiceSelect={(voice) => handleSelect(voice)}
 *   showFilters={true}
 *   layout="grid"
 * />
 * ```
 */

import React, { useState, useEffect } from 'react';
import { useVoiceLibrary } from '@/hooks/useVoiceLibrary';
import { VoiceCard } from './VoiceCard';
import { VoiceFilters } from './VoiceFilters';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2, LayoutGrid, List, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Voice {
  voice_id: string;
  name: string;
  description?: string;
  characteristics?: any;
  metadata?: any;
  stats?: any;
  files?: any;
  access?: any;
  owner?: any;
}

interface VoiceFiltersData {
  search?: string;
  gender?: string;
  language?: string;
  accent?: string;
  dialect?: string;
  categories?: string[];
  tags?: string[];
  featured?: boolean;
  verified?: boolean;
  visibility?: string;
  minRating?: number;
}

interface VoiceGalleryProps {
  onVoiceSelect?: (voice: Voice) => void;
  selectedVoiceId?: string;
  showFilters?: boolean;
  showStats?: boolean;
  showActions?: boolean;
  defaultLayout?: 'grid' | 'list';
  defaultFilters?: VoiceFiltersData;
  pageSize?: number;
  className?: string;
}

export const VoiceGallery: React.FC<VoiceGalleryProps> = ({
  onVoiceSelect,
  selectedVoiceId,
  showFilters = true,
  showStats = true,
  showActions = true,
  defaultLayout = 'grid',
  defaultFilters = {},
  pageSize = 20,
  className = '',
}) => {
  const { fetchVoices, addToFavorites, removeFromFavorites, getFavorites } = useVoiceLibrary();

  const [voices, setVoices] = useState<Voice[]>([]);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [filters, setFilters] = useState<VoiceFiltersData>(defaultFilters);
  const [layout, setLayout] = useState<'grid' | 'list'>(defaultLayout);
  const [sortBy, setSortBy] = useState<string>('created_at');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadVoices();
  }, [filters, sortBy, page]);

  useEffect(() => {
    loadFavorites();
  }, []);

  const loadVoices = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await fetchVoices(filters, page * pageSize, pageSize);

      if (data && data.voices) {
        setVoices(data.voices);
        setTotal(data.total || 0);
        setHasMore((page + 1) * pageSize < (data.total || 0));
      }
    } catch (err: any) {
      console.error('Failed to load voices:', err);
      setError(err.message || 'Failed to load voices');
    } finally {
      setLoading(false);
    }
  };

  const loadFavorites = async () => {
    try {
      const favoritesData = await getFavorites();
      if (favoritesData && favoritesData.voices) {
        const favoriteIds = new Set(favoritesData.voices.map((v: Voice) => v.voice_id));
        setFavorites(favoriteIds);
      }
    } catch (err) {
      console.error('Failed to load favorites:', err);
    }
  };

  const handleFilterChange = (newFilters: VoiceFiltersData) => {
    setFilters(newFilters);
    setPage(0); // Reset to first page
  };

  const handleFavorite = async (voiceId: string, isFavorite: boolean) => {
    try {
      if (isFavorite) {
        await addToFavorites(voiceId);
        setFavorites(prev => new Set([...prev, voiceId]));
      } else {
        await removeFromFavorites(voiceId);
        setFavorites(prev => {
          const newSet = new Set(prev);
          newSet.delete(voiceId);
          return newSet;
        });
      }
    } catch (err) {
      console.error('Failed to toggle favorite:', err);
      throw err;
    }
  };

  const handleSortChange = (value: string) => {
    setSortBy(value);
    setPage(0);
  };

  const handlePrevPage = () => {
    if (page > 0) {
      setPage(page - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleNextPage = () => {
    if (hasMore) {
      setPage(page + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Voice Library</h2>
          <p className="text-sm text-muted-foreground">
            {loading ? 'Loading...' : `${total} voice${total !== 1 ? 's' : ''} available`}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Sort dropdown */}
          <Select value={sortBy} onValueChange={handleSortChange}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="created_at">Newest First</SelectItem>
              <SelectItem value="name">Name (A-Z)</SelectItem>
              <SelectItem value="stats.rating">Highest Rated</SelectItem>
              <SelectItem value="stats.uses">Most Used</SelectItem>
              <SelectItem value="stats.favorites">Most Favorited</SelectItem>
            </SelectContent>
          </Select>

          {/* Layout toggle */}
          <div className="flex items-center gap-1 border rounded-md p-1">
            <Button
              variant={layout === 'grid' ? 'secondary' : 'ghost'}
              size="icon"
              className="h-8 w-8"
              onClick={() => setLayout('grid')}
              title="Grid view"
            >
              <LayoutGrid className="h-4 w-4" />
            </Button>
            <Button
              variant={layout === 'list' ? 'secondary' : 'ghost'}
              size="icon"
              className="h-8 w-8"
              onClick={() => setLayout('list')}
              title="List view"
            >
              <List className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <VoiceFilters
          filters={filters}
          onChange={handleFilterChange}
          showSearch={true}
          compact={true}
        />
      )}

      {/* Error state */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-2 text-muted-foreground">Loading voices...</span>
        </div>
      )}

      {/* Empty state */}
      {!loading && voices.length === 0 && (
        <div className="text-center py-12">
          <p className="text-lg text-muted-foreground">No voices found</p>
          <p className="text-sm text-muted-foreground mt-1">
            Try adjusting your filters or search terms
          </p>
        </div>
      )}

      {/* Voice gallery */}
      {!loading && voices.length > 0 && (
        <>
          <div
            className={cn(
              layout === 'grid'
                ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4'
                : 'flex flex-col gap-3'
            )}
          >
            {voices.map((voice) => (
              <VoiceCard
                key={voice.voice_id}
                voice={voice}
                onSelect={onVoiceSelect}
                onFavorite={handleFavorite}
                isFavorite={favorites.has(voice.voice_id)}
                isSelected={voice.voice_id === selectedVoiceId}
                showActions={showActions}
                showStats={showStats}
                compact={layout === 'list'}
              />
            ))}
          </div>

          {/* Pagination */}
          {(page > 0 || hasMore) && (
            <div className="flex items-center justify-between pt-4">
              <div className="text-sm text-muted-foreground">
                Showing {page * pageSize + 1} - {Math.min((page + 1) * pageSize, total)} of {total}
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  onClick={handlePrevPage}
                  disabled={page === 0 || loading}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  onClick={handleNextPage}
                  disabled={!hasMore || loading}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default VoiceGallery;
