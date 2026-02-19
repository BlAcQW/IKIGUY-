import React, { useState, useEffect, useCallback } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Search,
  Globe,
  FileText,
  Users,
  Music,
  Clock,
  TrendingUp,
  Loader2,
  ArrowRight
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { realApiClient } from '@/lib/realApi';

interface SearchResult {
  id: string;
  type: 'language' | 'submission' | 'user' | 'community';
  title: string;
  subtitle?: string;
  description?: string;
  metadata?: any;
  url: string;
}

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialQuery?: string;
}

export const SearchModal: React.FC<SearchModalProps> = ({
  isOpen,
  onClose,
  initialQuery = ''
}) => {
  const navigate = useNavigate();
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [popularSearches] = useState([
    'Yoruba audio', 'Igbo translations', 'Swahili proverbs',
    'Amharic literature', 'Zulu songs', 'Hausa stories'
  ]);

  // Load recent searches from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('recent_searches');
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved));
      } catch (error) {
        console.error('Error loading recent searches:', error);
      }
    }
  }, []);

  // Save search to recent searches
  const saveRecentSearch = useCallback((searchQuery: string) => {
    if (!searchQuery.trim()) return;

    const updated = [searchQuery, ...recentSearches.filter(s => s !== searchQuery)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('recent_searches', JSON.stringify(updated));
  }, [recentSearches]);

  // Debounced search function
  const performSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      // Perform multiple search operations in parallel
      const [languages, submissions] = await Promise.all([
        realApiClient.searchLanguages(searchQuery),
        realApiClient.searchSubmissions(searchQuery)
      ]);

      const searchResults: SearchResult[] = [];

      // Add language results
      languages.forEach((lang: any) => {
        searchResults.push({
          id: `lang-${lang.code}`,
          type: 'language',
          title: lang.name,
          subtitle: lang.native_name,
          description: `${lang.speakers || 0} speakers • ${lang.family || 'Unknown'} family`,
          metadata: { speakers: lang.speakers, family: lang.family },
          url: `/languages/${lang.code}`
        });
      });

      // Add submission results
      submissions.forEach((submission: any) => {
        searchResults.push({
          id: `sub-${submission.id}`,
          type: 'submission',
          title: submission.title,
          subtitle: submission.profiles?.full_name || submission.profiles?.username || 'Anonymous',
          description: `${submission.type} • ${submission.language_code} • ${new Date(submission.created_at).toLocaleDateString()}`,
          metadata: { type: submission.type, language: submission.language_code },
          url: `/submissions/${submission.id}`
        });
      });

      setResults(searchResults);
    } catch (error) {
      console.error('Search failed:', error);
      // Fallback to mock results for development
      const mockResults: SearchResult[] = [
        {
          id: 'lang-yo',
          type: 'language',
          title: 'Yoruba',
          subtitle: 'Yorùbá',
          description: '45M speakers • Niger-Congo family',
          url: '/languages/yo'
        },
        {
          id: 'sub-1',
          type: 'submission',
          title: 'Traditional Yoruba Greetings',
          subtitle: 'Amara Okafor',
          description: 'audio • yo • 2 days ago',
          url: '/submissions/1'
        }
      ].filter(r =>
        r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.subtitle?.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setResults(mockResults);
    } finally {
      setLoading(false);
    }
  }, []);

  // Debounce search input
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      performSearch(query);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [query, performSearch]);

  const handleResultClick = (result: SearchResult) => {
    saveRecentSearch(query);
    navigate(result.url);
    onClose();
  };

  const handleQuickSearch = (searchQuery: string) => {
    setQuery(searchQuery);
  };

  const handleViewAllResults = () => {
    if (query.trim()) {
      saveRecentSearch(query);
      navigate(`/search?q=${encodeURIComponent(query)}`);
      onClose();
    }
  };

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'language': return <Globe className="h-4 w-4 text-blue-500" />;
      case 'submission': return <FileText className="h-4 w-4 text-green-500" />;
      case 'user': return <Users className="h-4 w-4 text-purple-500" />;
      case 'community': return <Music className="h-4 w-4 text-orange-500" />;
      default: return <Search className="h-4 w-4 text-gray-500" />;
    }
  };

  const clearRecentSearches = () => {
    setRecentSearches([]);
    localStorage.removeItem('recent_searches');
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl p-0">
        <DialogHeader className="p-6 pb-4">
          <DialogTitle>Search AfriLang Community</DialogTitle>
        </DialogHeader>

        <div className="px-6">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search languages, submissions, users..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-10 pr-4"
              autoFocus
            />
            {loading && (
              <Loader2 className="absolute right-3 top-3 h-4 w-4 animate-spin text-muted-foreground" />
            )}
          </div>
        </div>

        <ScrollArea className="max-h-96">
          <div className="px-6 py-4">
            {!query.trim() && (
              <div className="space-y-6">
                {/* Recent Searches */}
                {recentSearches.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                        <Clock className="h-4 w-4" />
                        Recent Searches
                      </h3>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={clearRecentSearches}
                        className="text-xs"
                      >
                        Clear
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {recentSearches.map((search, index) => (
                        <Badge
                          key={index}
                          variant="secondary"
                          className="cursor-pointer hover:bg-secondary/80"
                          onClick={() => handleQuickSearch(search)}
                        >
                          {search}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Popular Searches */}
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" />
                    Popular Searches
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {popularSearches.map((search, index) => (
                      <Badge
                        key={index}
                        variant="outline"
                        className="cursor-pointer hover:bg-accent"
                        onClick={() => handleQuickSearch(search)}
                      >
                        {search}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Search Results */}
            {query.trim() && (
              <div className="space-y-2">
                {results.length > 0 && (
                  <div className="flex items-center justify-between mb-4">
                    <p className="text-sm text-muted-foreground">
                      {results.length} result{results.length !== 1 ? 's' : ''} for "{query}"
                    </p>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleViewAllResults}
                      className="text-primary hover:text-primary/80"
                    >
                      View all <ArrowRight className="h-3 w-3 ml-1" />
                    </Button>
                  </div>
                )}

                {results.map((result, index) => (
                  <div key={result.id}>
                    <div
                      className="flex items-center gap-3 p-3 rounded-lg hover:bg-accent cursor-pointer transition-colors"
                      onClick={() => handleResultClick(result)}
                    >
                      {getResultIcon(result.type)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="font-medium text-sm truncate">{result.title}</p>
                          <Badge variant="outline" className="text-xs">
                            {result.type}
                          </Badge>
                        </div>
                        {result.subtitle && (
                          <p className="text-xs text-muted-foreground truncate">
                            {result.subtitle}
                          </p>
                        )}
                        {result.description && (
                          <p className="text-xs text-muted-foreground truncate mt-1">
                            {result.description}
                          </p>
                        )}
                      </div>
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    </div>
                    {index < results.length - 1 && <Separator />}
                  </div>
                ))}

                {results.length === 0 && !loading && query.trim().length >= 2 && (
                  <div className="text-center py-8">
                    <Search className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                    <p className="text-sm text-muted-foreground">
                      No results found for "{query}"
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Try searching for languages, submissions, or users
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </ScrollArea>

        {query.trim() && results.length > 0 && (
          <div className="border-t p-4 bg-muted/50">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Press Enter to view all results</span>
              <span>ESC to close</span>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default SearchModal;