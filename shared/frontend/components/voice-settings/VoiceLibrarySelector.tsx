/**
 * Voice Library Selector Component
 *
 * Elegant component for selecting favorite voices from the cloned voice library.
 * Features modern card-based grid layout, smooth animations, and dark mode support.
 * Part of @kasaai/shared-frontend library.
 */

import React, { useState, useMemo } from 'react';

export interface ClonedVoice {
  id: string;
  name: string;
  description?: string;
  language?: string;
  gender?: 'male' | 'female' | 'neutral';
  tags?: string[];
  previewUrl?: string;
  createdAt?: string;
  isFavorite?: boolean;
}

export interface VoiceLibrarySelectorProps {
  voices: ClonedVoice[];
  favoriteVoiceIds: string[];
  onToggleFavorite: (voiceId: string) => void;
  onPreviewVoice?: (voiceId: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  maxFavorites?: number;
  className?: string;
  variant?: 'light' | 'dark';
}

export const VoiceLibrarySelector: React.FC<VoiceLibrarySelectorProps> = ({
  voices,
  favoriteVoiceIds,
  onToggleFavorite,
  onPreviewVoice,
  isLoading = false,
  disabled = false,
  maxFavorites = 10,
  className = '',
  variant = 'light',
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterGender, setFilterGender] = useState<string>('all');
  const [filterLanguage, setFilterLanguage] = useState<string>('all');
  const [previewingId, setPreviewingId] = useState<string | null>(null);
  const [favoritingId, setFavoritingId] = useState<string | null>(null);

  // Theme classes based on variant
  const isDark = variant === 'dark';
  const themeClasses = {
    bg: isDark ? 'bg-gray-900' : 'bg-white',
    card: isDark ? 'bg-gray-800/50 border-gray-700 hover:border-gray-600' : 'bg-white border-gray-200 hover:border-gray-300',
    cardFavorite: isDark 
      ? 'bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-purple-500/30 ring-1 ring-purple-500/20' 
      : 'bg-gradient-to-br from-purple-50 to-pink-50 border-purple-300 ring-1 ring-purple-200',
    text: isDark ? 'text-gray-100' : 'text-gray-900',
    textSecondary: isDark ? 'text-gray-400' : 'text-gray-600',
    textMuted: isDark ? 'text-gray-500' : 'text-gray-500',
    input: isDark 
      ? 'bg-gray-800 border-gray-700 text-white placeholder-gray-500 focus:border-purple-500 focus:ring-purple-500/20' 
      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:ring-indigo-500/20',
    badge: isDark ? 'bg-gray-700/50 text-gray-300 border-gray-600' : 'bg-gray-100 text-gray-700 border-gray-200',
    badgeLanguage: isDark ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' : 'bg-blue-100 text-blue-700 border-blue-200',
    empty: isDark ? 'text-gray-500' : 'text-gray-400',
  };

  // Get unique languages from voices
  const languages = useMemo(() => {
    const langs = new Set(voices.map((v) => v.language).filter(Boolean));
    return Array.from(langs).sort();
  }, [voices]);

  // Filter voices based on search and filters
  const filteredVoices = useMemo(() => {
    return voices.filter((voice) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesName = voice.name.toLowerCase().includes(query);
        const matchesDescription = voice.description?.toLowerCase().includes(query);
        const matchesTags = voice.tags?.some((tag) => tag.toLowerCase().includes(query));
        if (!matchesName && !matchesDescription && !matchesTags) {
          return false;
        }
      }

      // Gender filter
      if (filterGender !== 'all' && voice.gender !== filterGender) {
        return false;
      }

      // Language filter
      if (filterLanguage !== 'all' && voice.language !== filterLanguage) {
        return false;
      }

      return true;
    });
  }, [voices, searchQuery, filterGender, filterLanguage]);

  const isFavorite = (voiceId: string) => favoriteVoiceIds.includes(voiceId);
  const canAddMoreFavorites = favoriteVoiceIds.length < maxFavorites;

  const handleToggleFavorite = async (voiceId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (disabled) return;

    const currentlyFavorite = isFavorite(voiceId);
    if (!currentlyFavorite && !canAddMoreFavorites) {
      // Show a more elegant toast-like message instead of alert
      return;
    }

    setFavoritingId(voiceId);
    try {
      await onToggleFavorite(voiceId);
    } finally {
      setTimeout(() => setFavoritingId(null), 300);
    }
  };

  const handlePreview = async (voiceId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (disabled || !onPreviewVoice) return;

    setPreviewingId(voiceId);
    try {
      await onPreviewVoice(voiceId);
    } finally {
      setTimeout(() => setPreviewingId(null), 1000);
    }
  };

  const getGenderIcon = (gender?: string) => {
    switch (gender) {
      case 'male':
        return '👨';
      case 'female':
        return '👩';
      case 'neutral':
        return '👤';
      default:
        return '🎤';
    }
  };

  const getLanguageFlag = (language?: string) => {
    // Simple mapping for common languages
    const flags: Record<string, string> = {
      en: '🇬🇧',
      es: '🇪🇸',
      fr: '🇫🇷',
      de: '🇩🇪',
      tw: '🇬🇭',
      yo: '🇳🇬',
      ak: '🇬🇭',
    };
    return flags[language?.toLowerCase() || ''] || '🌍';
  };

  // Loading skeleton
  if (isLoading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="flex items-center justify-between">
          <div>
            <div className={`h-6 w-48 ${isDark ? 'bg-gray-800' : 'bg-gray-200'} rounded-md animate-pulse mb-2`}></div>
            <div className={`h-4 w-32 ${isDark ? 'bg-gray-800' : 'bg-gray-200'} rounded-md animate-pulse`}></div>
          </div>
        </div>

        {/* Filter skeletons */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className={`h-10 ${isDark ? 'bg-gray-800' : 'bg-gray-200'} rounded-lg animate-pulse`}
            ></div>
          ))}
        </div>

        {/* Card skeletons */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className={`${themeClasses.card} rounded-xl p-5 border animate-pulse`}
            >
              <div className={`h-5 w-32 ${isDark ? 'bg-gray-700' : 'bg-gray-200'} rounded mb-3`}></div>
              <div className={`h-4 w-full ${isDark ? 'bg-gray-700' : 'bg-gray-200'} rounded mb-2`}></div>
              <div className={`h-4 w-3/4 ${isDark ? 'bg-gray-700' : 'bg-gray-200'} rounded`}></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className={`text-lg font-semibold ${themeClasses.text} mb-1`}>
            Voice Library
          </h3>
          <p className={`text-sm ${themeClasses.textMuted}`}>
            {favoriteVoiceIds.length} of {maxFavorites} favorites selected • {filteredVoices.length} {filteredVoices.length === 1 ? 'voice' : 'voices'} found
          </p>
        </div>
        {favoriteVoiceIds.length > 0 && (
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${isDark ? 'bg-purple-500/20 border border-purple-500/30' : 'bg-purple-100 border border-purple-200'}`}>
            <span className={`text-sm font-medium ${isDark ? 'text-purple-400' : 'text-purple-700'}`}>
              ⭐ {favoriteVoiceIds.length} Favorite{favoriteVoiceIds.length !== 1 ? 's' : ''}
            </span>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Search */}
        <div className="md:col-span-1 relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg
              className={`h-5 w-5 ${themeClasses.textMuted}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          <input
            type="text"
            placeholder="Search voices..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            disabled={disabled}
            className={`block w-full pl-10 pr-3 py-2.5 ${themeClasses.input} border rounded-lg shadow-sm transition-all focus:outline-none focus:ring-2 sm:text-sm`}
          />
        </div>

        {/* Gender Filter */}
        <div className="md:col-span-1">
          <select
            value={filterGender}
            onChange={(e) => setFilterGender(e.target.value)}
            disabled={disabled}
            className={`block w-full px-3 py-2.5 ${themeClasses.input} border rounded-lg shadow-sm transition-all focus:outline-none focus:ring-2 sm:text-sm`}
          >
            <option value="all">All Genders</option>
            <option value="male">👨 Male</option>
            <option value="female">👩 Female</option>
            <option value="neutral">👤 Neutral</option>
          </select>
        </div>

        {/* Language Filter */}
        <div className="md:col-span-1">
          <select
            value={filterLanguage}
            onChange={(e) => setFilterLanguage(e.target.value)}
            disabled={disabled}
            className={`block w-full px-3 py-2.5 ${themeClasses.input} border rounded-lg shadow-sm transition-all focus:outline-none focus:ring-2 sm:text-sm`}
          >
            <option value="all">All Languages</option>
            {languages.map((lang) => (
              <option key={lang} value={lang}>
                {getLanguageFlag(lang)} {lang}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Voice Grid */}
      {filteredVoices.length === 0 ? (
        <div className={`text-center py-16 rounded-xl border ${themeClasses.card}`}>
          <div className="text-6xl mb-4">🎭</div>
          <p className={`text-lg font-medium ${themeClasses.text} mb-2`}>
            No voices found
          </p>
          <p className={`text-sm ${themeClasses.textMuted}`}>
            {searchQuery || filterGender !== 'all' || filterLanguage !== 'all'
              ? 'Try adjusting your filters or search terms'
              : 'Clone voices in the Voice Lab to get started'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredVoices.map((voice) => {
            const favorite = isFavorite(voice.id);
            const isPreviewing = previewingId === voice.id;
            const isFavoriting = favoritingId === voice.id;

            return (
              <div
                key={voice.id}
                className={`group relative ${themeClasses.card} ${
                  favorite ? themeClasses.cardFavorite : ''
                } rounded-xl p-5 border transition-all duration-300 ${
                  disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:shadow-lg hover:scale-[1.02]'
                } ${favorite ? 'shadow-md' : ''}`}
                onClick={() => !disabled && handleToggleFavorite(voice.id, {} as React.MouseEvent)}
              >
                {/* Favorite indicator */}
                {favorite && (
                  <div className="absolute top-3 right-3">
                    <div className={`w-2 h-2 rounded-full ${isDark ? 'bg-purple-400' : 'bg-purple-500'} animate-pulse`}></div>
                  </div>
                )}

                {/* Voice Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <h4 className={`font-semibold text-lg ${themeClasses.text} mb-1 truncate`}>
                      {voice.name}
                    </h4>
                    {voice.description && (
                      <p className={`text-sm ${themeClasses.textSecondary} line-clamp-2`}>
                        {voice.description}
                      </p>
                    )}
                  </div>
                </div>

                {/* Badges */}
                <div className="flex flex-wrap gap-2 mb-4">
                  {voice.gender && (
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${themeClasses.badge}`}>
                      <span className="mr-1.5">{getGenderIcon(voice.gender)}</span>
                      {voice.gender.charAt(0).toUpperCase() + voice.gender.slice(1)}
                    </span>
                  )}
                  {voice.language && (
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${themeClasses.badgeLanguage}`}>
                      <span className="mr-1.5">{getLanguageFlag(voice.language)}</span>
                      {voice.language}
                    </span>
                  )}
                  {voice.tags && voice.tags.length > 0 && (
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${themeClasses.badge}`}>
                      {voice.tags.length} tag{voice.tags.length !== 1 ? 's' : ''}
                    </span>
                  )}
                </div>

                {/* Tags */}
                {voice.tags && voice.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {voice.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs ${isDark ? 'bg-gray-700/50 text-gray-300' : 'bg-gray-100 text-gray-600'}`}
                      >
                        #{tag}
                      </span>
                    ))}
                    {voice.tags.length > 3 && (
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs ${themeClasses.textMuted}`}>
                        +{voice.tags.length - 3}
                      </span>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center justify-between pt-3 border-t border-gray-700/50">
                  {/* Preview Button */}
                  {onPreviewVoice && voice.previewUrl && (
                    <button
                      onClick={(e) => handlePreview(voice.id, e)}
                      disabled={disabled || isPreviewing}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                        isDark
                          ? 'bg-gray-700/50 text-gray-300 hover:bg-gray-700 hover:text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      } disabled:opacity-50 disabled:cursor-not-allowed`}
                      title="Preview voice"
                    >
                      {isPreviewing ? (
                        <>
                          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                          <span>Playing...</span>
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" />
                          </svg>
                          <span>Preview</span>
                        </>
                      )}
                    </button>
                  )}

                  {/* Favorite Toggle */}
                  <button
                    onClick={(e) => handleToggleFavorite(voice.id, e)}
                    disabled={disabled || (!favorite && !canAddMoreFavorites) || isFavoriting}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                      favorite
                        ? isDark
                          ? 'bg-purple-500/20 text-purple-400 hover:bg-purple-500/30'
                          : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                        : isDark
                        ? 'bg-gray-700/50 text-gray-400 hover:bg-gray-700 hover:text-gray-300'
                        : 'bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-600'
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                    title={
                      favorite
                        ? 'Remove from favorites'
                        : canAddMoreFavorites
                        ? 'Add to favorites'
                        : `Maximum ${maxFavorites} favorites reached`
                    }
                  >
                    {isFavoriting ? (
                      <>
                        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                        <span>{favorite ? 'Removing...' : 'Adding...'}</span>
                      </>
                    ) : (
                      <>
                        <svg
                          className={`w-4 h-4 transition-transform ${favorite ? 'scale-110' : ''}`}
                          fill={favorite ? 'currentColor' : 'none'}
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                          />
                        </svg>
                        <span>{favorite ? 'Favorited' : 'Favorite'}</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Empty state for no voices at all */}
      {voices.length === 0 && !isLoading && (
        <div className={`text-center py-16 rounded-xl border ${themeClasses.card}`}>
          <div className="text-6xl mb-4">🎭</div>
          <p className={`text-lg font-medium ${themeClasses.text} mb-2`}>
            No voices available
          </p>
          <p className={`text-sm ${themeClasses.textMuted}`}>
            Clone voices in the Voice Lab to get started
          </p>
        </div>
      )}
    </div>
  );
};
