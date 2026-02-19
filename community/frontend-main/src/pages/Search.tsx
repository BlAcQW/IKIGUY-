import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Search as SearchIcon,
  Globe,
  FileText,
  Users,
  Music,
  Filter,
  SortAsc,
  Calendar,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { apiClient } from '@/lib/api';

const API_BASE = 'https://language-community-api.ailabsafrica.com/api/v1';

interface SearchResult {
  id: string;
  type: 'language' | 'submission' | 'user' | 'community' | 'model' | 'dataset' | 'resource';
  title: string;
  subtitle?: string;
  description: string;
  metadata: any;
  created_at?: string;
  url: string;
}

const Search = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [filteredResults, setFilteredResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  const [sortBy, setSortBy] = useState('relevance');
  const [filters, setFilters] = useState({
    language: '',
    type: '',
    dateRange: ''
  });

  // Perform search when query or URL params change
  useEffect(() => {
    const searchQuery = searchParams.get('q');
    if (searchQuery) {
      setQuery(searchQuery);
      performSearch(searchQuery);
    }
  }, [searchParams]);

  // Filter and sort results when filters change
  useEffect(() => {
    let filtered = [...results];

    // Apply type filter (from active tab)
    if (activeTab !== 'all') {
      filtered = filtered.filter(result => result.type === activeTab);
    }

    // Apply additional filters
    if (filters.language) {
      filtered = filtered.filter(result =>
        result.metadata?.language?.toLowerCase().includes(filters.language.toLowerCase()) ||
        result.metadata?.language_code === filters.language
      );
    }

    if (filters.type) {
      filtered = filtered.filter(result =>
        result.metadata?.submission_type === filters.type ||
        result.metadata?.type === filters.type
      );
    }

    // Apply sorting
    switch (sortBy) {
      case 'newest':
        filtered.sort((a, b) => {
          const dateA = new Date(a.created_at || a.metadata?.created_at || '');
          const dateB = new Date(b.created_at || b.metadata?.created_at || '');
          return dateB.getTime() - dateA.getTime();
        });
        break;
      case 'oldest':
        filtered.sort((a, b) => {
          const dateA = new Date(a.created_at || a.metadata?.created_at || '');
          const dateB = new Date(b.created_at || b.metadata?.created_at || '');
          return dateA.getTime() - dateB.getTime();
        });
        break;
      case 'title':
        filtered.sort((a, b) => a.title.localeCompare(b.title));
        break;
      default: // relevance
        // Results are already in relevance order from search
        break;
    }

    setFilteredResults(filtered);
  }, [results, activeTab, filters, sortBy]);

  const performSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      // Use discovery search endpoint for comprehensive search
      const response = await fetch(
        `${API_BASE}/discovery/search?query=${encodeURIComponent(searchQuery)}&limit=50`
      );

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data = await response.json();
      const searchResults: SearchResult[] = [];

      // Process models
      if (data.models && data.models.length > 0) {
        data.models.forEach((model: any) => {
          searchResults.push({
            id: `model-${model.model_uuid}`,
            type: 'model',
            title: model.name,
            subtitle: model.model_type?.toUpperCase(),
            description: `${model.architecture} • v${model.version} • ${model.download_count || 0} downloads`,
            metadata: model,
            created_at: model.created_at,
            url: `/models/${model.model_uuid}`
          });
        });
      }

      // Process datasets
      if (data.datasets && data.datasets.length > 0) {
        data.datasets.forEach((dataset: any) => {
          searchResults.push({
            id: `dataset-${dataset.dataset_uuid}`,
            type: 'dataset',
            title: dataset.name,
            subtitle: dataset.source_type,
            description: `${dataset.languages?.join(', ') || 'Multiple languages'} • ${dataset.total_size_gb || 0} GB`,
            metadata: dataset,
            created_at: dataset.created_at,
            url: `/datasets/${dataset.dataset_uuid}`
          });
        });
      }

      // Process resources
      if (data.resources && data.resources.length > 0) {
        data.resources.forEach((resource: any) => {
          searchResults.push({
            id: `resource-${resource.link_uuid}`,
            type: 'resource',
            title: resource.title,
            subtitle: resource.platform,
            description: `${resource.resource_type} • ${resource.upvotes || 0} upvotes`,
            metadata: resource,
            created_at: resource.created_at,
            url: resource.url || '#'
          });
        });
      }

      // Also search languages
      const languages = await apiClient.searchLanguages(searchQuery, 20);
      languages.forEach((lang: any) => {
        searchResults.push({
          id: `lang-${lang.code}`,
          type: 'language',
          title: lang.name,
          subtitle: lang.native_name,
          description: `${lang.speakers?.toLocaleString() || 'Unknown'} speakers • ${lang.family || 'Unknown family'}`,
          metadata: {
            speakers: lang.speakers,
            family: lang.family,
            code: lang.code
          },
          url: `/languages/${lang.code}`
        });
      });

      setResults(searchResults);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      setSearchParams({ q: query.trim() });
      performSearch(query.trim());
    }
  };

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'language': return <Globe className="h-5 w-5 text-blue-500" />;
      case 'model': return <FileText className="h-5 w-5 text-purple-500" />;
      case 'dataset': return <Music className="h-5 w-5 text-green-500" />;
      case 'resource': return <FileText className="h-5 w-5 text-orange-500" />;
      case 'submission': return <FileText className="h-5 w-5 text-green-500" />;
      case 'user': return <Users className="h-5 w-5 text-purple-500" />;
      case 'community': return <Music className="h-5 w-5 text-orange-500" />;
      default: return <SearchIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getResultCounts = () => {
    const counts = {
      all: results.length,
      language: results.filter(r => r.type === 'language').length,
      model: results.filter(r => r.type === 'model').length,
      dataset: results.filter(r => r.type === 'dataset').length,
      resource: results.filter(r => r.type === 'resource').length,
      submission: results.filter(r => r.type === 'submission').length,
      user: results.filter(r => r.type === 'user').length,
      community: results.filter(r => r.type === 'community').length,
    };
    return counts;
  };

  const counts = getResultCounts();

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 py-8">
        {/* Search Header */}
        <div className="max-w-4xl mx-auto mb-8">
          <h1 className="text-3xl font-bold mb-6">Search Results</h1>

          {/* Search Form */}
          <form onSubmit={handleSearch} className="flex gap-3 mb-6">
            <div className="flex-1 relative">
              <SearchIcon className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search languages, models, datasets, resources..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button type="submit" disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Search'}
            </Button>
          </form>

          {/* Search Info */}
          {query && (
            <div className="flex items-center gap-4 text-sm text-muted-foreground mb-6">
              <span>
                {loading ? 'Searching...' : `${results.length} result${results.length !== 1 ? 's' : ''} for "${query}"`}
              </span>
              {!loading && results.length > 0 && (
                <div className="flex items-center gap-4">
                  <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger className="w-36">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="relevance">Relevance</SelectItem>
                      <SelectItem value="newest">Newest</SelectItem>
                      <SelectItem value="oldest">Oldest</SelectItem>
                      <SelectItem value="title">Title A-Z</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Results */}
        <div className="max-w-4xl mx-auto">
          {!query ? (
            <Card>
              <CardContent className="text-center py-12">
                <SearchIcon className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h2 className="text-xl font-semibold mb-2">Search AfriLang Community</h2>
                <p className="text-muted-foreground">
                  Find languages, ML models, datasets, and external resources
                </p>
              </CardContent>
            </Card>
          ) : loading ? (
            <Card>
              <CardContent className="text-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-4" />
                <p className="text-muted-foreground">Searching...</p>
              </CardContent>
            </Card>
          ) : results.length === 0 ? (
            <Card>
              <CardContent className="text-center py-12">
                <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h2 className="text-xl font-semibold mb-2">No results found</h2>
                <p className="text-muted-foreground mb-4">
                  No results found for "{query}". Try adjusting your search terms.
                </p>
                <div className="text-sm text-muted-foreground space-y-1">
                  <p>• Try different keywords</p>
                  <p>• Check your spelling</p>
                  <p>• Use broader search terms</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="all">All ({counts.all})</TabsTrigger>
                <TabsTrigger value="language">Languages ({counts.language})</TabsTrigger>
                <TabsTrigger value="model">Models ({counts.model})</TabsTrigger>
                <TabsTrigger value="dataset">Datasets ({counts.dataset})</TabsTrigger>
                <TabsTrigger value="resource">Resources ({counts.resource})</TabsTrigger>
              </TabsList>

              <TabsContent value={activeTab} className="mt-6">
                <div className="space-y-4">
                  {filteredResults.map((result) => (
                    <Card key={result.id} className="hover:shadow-md transition-shadow cursor-pointer">
                      <CardContent className="p-6">
                        <div className="flex items-start gap-4">
                          {getResultIcon(result.type)}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              <h3 className="font-semibold text-lg hover:text-primary transition-colors">
                                <a href={result.url}>{result.title}</a>
                              </h3>
                              <Badge variant="outline" className="text-xs">
                                {result.type}
                              </Badge>
                            </div>
                            {result.subtitle && (
                              <p className="text-sm text-muted-foreground mb-2">
                                {result.subtitle}
                              </p>
                            )}
                            <p className="text-sm text-muted-foreground mb-3">
                              {result.description}
                            </p>
                            <div className="flex items-center gap-4 text-xs text-muted-foreground">
                              <span className="text-primary font-medium">{result.url}</span>
                              {result.created_at && (
                                <span className="flex items-center gap-1">
                                  <Calendar className="h-3 w-3" />
                                  {new Date(result.created_at).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Search;