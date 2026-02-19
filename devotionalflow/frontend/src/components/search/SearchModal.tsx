/**
 * SearchModal Component
 * Full-screen search modal for devotionals
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, X, Clock, TrendingUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api';
import { useQuery } from '@tanstack/react-query';

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface SearchResult {
  id: string;
  title: string;
  excerpt: string;
  categories: string[];
}

export function SearchModal({ isOpen, onClose }: SearchModalProps) {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  // Load recent searches from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('recent_searches');
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to parse recent searches:', e);
      }
    }
  }, []);

  // Search devotionals
  const { data: results, isLoading } = useQuery({
    queryKey: ['search', searchQuery],
    queryFn: async () => {
      if (!searchQuery || searchQuery.trim().length < 2) return [];

      const response = await apiClient.getDevotionals({
        search: searchQuery,
        status: 'published',
        page: 1,
        limit: 10
      });

      return response.items as SearchResult[];
    },
    enabled: searchQuery.trim().length >= 2
  });

  const handleSearch = (query: string) => {
    setSearchQuery(query);

    // Save to recent searches
    if (query.trim() && !recentSearches.includes(query)) {
      const updated = [query, ...recentSearches].slice(0, 5);
      setRecentSearches(updated);
      localStorage.setItem('recent_searches', JSON.stringify(updated));
    }
  };

  const handleSelectResult = (devotionalId: string) => {
    navigate(`/devotional/${devotionalId}`);
    onClose();
  };

  const handleClearRecent = () => {
    setRecentSearches([]);
    localStorage.removeItem('recent_searches');
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-background"
      >
        {/* Search Header */}
        <div className="sticky top-0 bg-background border-b border-border">
          <div className="container mx-auto px-4 py-3">
            <div className="flex items-center gap-3">
              {/* Search Input */}
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  placeholder="Search devotionals..."
                  className="w-full pl-10 pr-4 py-3 bg-secondary/10 rounded-full border-0 focus:outline-none focus:ring-2 focus:ring-secondary"
                  autoFocus
                />
              </div>

              {/* Close Button */}
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="shrink-0"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>

        {/* Search Content */}
        <div className="container mx-auto px-4 py-6">
          {/* Search Results */}
          {searchQuery.trim().length >= 2 && (
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-muted-foreground">
                Search Results {results && `(${results.length})`}
              </h3>

              {isLoading ? (
                <div className="py-8 text-center text-muted-foreground">
                  Searching...
                </div>
              ) : results && results.length > 0 ? (
                <div className="space-y-3">
                  {results.map((result) => (
                    <motion.div
                      key={result.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-4 bg-card rounded-xl border border-border hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => handleSelectResult(result.id)}
                    >
                      <h4 className="font-serif font-bold text-foreground mb-2 line-clamp-2">
                        {result.title}
                      </h4>
                      <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                        {result.excerpt}
                      </p>
                      {result.categories && result.categories.length > 0 && (
                        <div className="flex gap-2">
                          {result.categories.slice(0, 2).map((cat) => (
                            <span
                              key={cat}
                              className="px-2 py-1 rounded-full bg-secondary/10 text-secondary text-xs"
                            >
                              {cat}
                            </span>
                          ))}
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center text-muted-foreground">
                  No results found
                </div>
              )}
            </div>
          )}

          {/* Recent Searches */}
          {searchQuery.trim().length < 2 && recentSearches.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  Recent Searches
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearRecent}
                  className="text-xs"
                >
                  Clear
                </Button>
              </div>

              <div className="space-y-2">
                {recentSearches.map((search, index) => (
                  <div
                    key={index}
                    className="p-3 bg-secondary/5 rounded-lg cursor-pointer hover:bg-secondary/10 transition-colors"
                    onClick={() => handleSearch(search)}
                  >
                    <p className="text-sm text-foreground">{search}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Popular Categories */}
          {searchQuery.trim().length < 2 && (
            <div className="space-y-4 mt-8">
              <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Popular Topics
              </h3>

              <div className="flex flex-wrap gap-2">
                {['faith', 'prayer', 'hope', 'love', 'wisdom', 'courage', 'peace', 'gratitude'].map((topic) => (
                  <button
                    key={topic}
                    className="px-4 py-2 rounded-full bg-secondary/10 text-secondary text-sm font-medium hover:bg-secondary/20 transition-colors"
                    onClick={() => {
                      navigate(`/feed?category=${topic}`);
                      onClose();
                    }}
                  >
                    {topic}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
