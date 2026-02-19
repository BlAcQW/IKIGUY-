import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { NotebookGrid } from '@/components/notebooks/NotebookGrid';
import { NotebookFilters } from '@/components/notebooks/NotebookFilters';
import { Badge } from '@/components/ui/badge';
import {
  BookOpen,
  TrendingUp,
  Star,
  Upload,
  Filter,
  Grid,
  List
} from 'lucide-react';

// Mock data for development
const mockNotebooks = [
  {
    id: '1',
    title: 'Twi Data Acquisition Pipeline',
    description: 'Comprehensive data acquisition pipeline for Twi language using multiple sources including web scraping, API integration, and manual collection methods.',
    category: 'data_acquisition',
    difficulty: 'intermediate',
    language_codes: ['twi', 'aka'],
    tags: ['pipeline', 'web-scraping', 'api', 'data-collection'],
    author_name: 'Kwame Asante',
    current_version: '2.1.0',
    file_size: 1024 * 1024 * 2.5, // 2.5MB
    upvotes: 45,
    downvotes: 3,
    rating: 4.6,
    usage_stats: {
      downloads: 128,
      views: 542
    },
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-20T14:30:00Z',
    user_vote: null,
    is_bookmarked: false,
    is_owner: false
  },
  {
    id: '2',
    title: 'Enhanced Multi-Rate Data Processing',
    description: 'Advanced data processing techniques for handling multiple sample rates and audio formats in African language datasets.',
    category: 'data_processing',
    difficulty: 'advanced',
    language_codes: ['swa', 'yor', 'twi'],
    tags: ['audio-processing', 'multi-rate', 'preprocessing', 'optimization'],
    author_name: 'Amina Hassan',
    current_version: '1.3.2',
    file_size: 1024 * 1024 * 4.2, // 4.2MB
    upvotes: 62,
    downvotes: 1,
    rating: 4.8,
    usage_stats: {
      downloads: 189,
      views: 721
    },
    created_at: '2024-01-10T09:15:00Z',
    updated_at: '2024-01-22T16:45:00Z',
    user_vote: 'upvote',
    is_bookmarked: true,
    is_owner: false
  },
  {
    id: '3',
    title: 'Coqui TTS Training for African Languages',
    description: 'Step-by-step guide for training Coqui TTS models on African language datasets with specific optimizations and best practices.',
    category: 'tts_training',
    difficulty: 'expert',
    language_codes: ['yor', 'hau', 'ibo'],
    tags: ['coqui', 'tts', 'training', 'optimization', 'african-languages'],
    author_name: 'Joseph Okafor',
    current_version: '3.0.1',
    file_size: 1024 * 1024 * 6.8, // 6.8MB
    upvotes: 78,
    downvotes: 5,
    rating: 4.7,
    usage_stats: {
      downloads: 234,
      views: 891
    },
    created_at: '2024-01-05T11:30:00Z',
    updated_at: '2024-01-21T13:20:00Z',
    user_vote: null,
    is_bookmarked: false,
    is_owner: true
  }
];

const NotebooksPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [notebooks, setNotebooks] = useState(mockNotebooks);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  const [showFilters, setShowFilters] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const [filters, setFilters] = useState({
    query: searchParams.get('q') || '',
    category: searchParams.get('category') || '',
    difficulty: searchParams.get('difficulty') || '',
    language_codes: searchParams.get('languages')?.split(',').filter(Boolean) || [],
    tags: searchParams.get('tags')?.split(',').filter(Boolean) || [],
    sort_by: searchParams.get('sort') || 'updated_at',
    sort_order: searchParams.get('order') || 'desc'
  });

  const [pagination, setPagination] = useState({
    page: 1,
    total_pages: 1,
    total: mockNotebooks.length
  });

  // Update URL when filters change
  useEffect(() => {
    const params = new URLSearchParams();

    if (filters.query) params.set('q', filters.query);
    if (filters.category) params.set('category', filters.category);
    if (filters.difficulty) params.set('difficulty', filters.difficulty);
    if (filters.language_codes.length > 0) params.set('languages', filters.language_codes.join(','));
    if (filters.tags.length > 0) params.set('tags', filters.tags.join(','));
    if (filters.sort_by !== 'updated_at') params.set('sort', filters.sort_by);
    if (filters.sort_order !== 'desc') params.set('order', filters.sort_order);

    setSearchParams(params);
  }, [filters, setSearchParams]);

  // Filter notebooks based on current filters
  useEffect(() => {
    let filteredNotebooks = [...mockNotebooks];

    // Apply filters
    if (filters.query) {
      const query = filters.query.toLowerCase();
      filteredNotebooks = filteredNotebooks.filter(nb =>
        nb.title.toLowerCase().includes(query) ||
        nb.description.toLowerCase().includes(query) ||
        nb.author_name.toLowerCase().includes(query)
      );
    }

    if (filters.category) {
      filteredNotebooks = filteredNotebooks.filter(nb => nb.category === filters.category);
    }

    if (filters.difficulty) {
      filteredNotebooks = filteredNotebooks.filter(nb => nb.difficulty === filters.difficulty);
    }

    if (filters.language_codes.length > 0) {
      filteredNotebooks = filteredNotebooks.filter(nb =>
        nb.language_codes.some(code => filters.language_codes.includes(code))
      );
    }

    if (filters.tags.length > 0) {
      filteredNotebooks = filteredNotebooks.filter(nb =>
        nb.tags.some(tag => filters.tags.includes(tag))
      );
    }

    // Apply sorting
    filteredNotebooks.sort((a, b) => {
      const aValue = a[filters.sort_by as keyof typeof a] as number;
      const bValue = b[filters.sort_by as keyof typeof b] as number;

      if (filters.sort_order === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    setNotebooks(filteredNotebooks);
    setPagination(prev => ({
      ...prev,
      total: filteredNotebooks.length
    }));
  }, [filters]);

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    // Apply tab-specific filters
    switch (tab) {
      case 'featured':
        setFilters(prev => ({ ...prev, sort_by: 'rating', sort_order: 'desc' }));
        break;
      case 'trending':
        setFilters(prev => ({ ...prev, sort_by: 'upvotes', sort_order: 'desc' }));
        break;
      case 'recent':
        setFilters(prev => ({ ...prev, sort_by: 'created_at', sort_order: 'desc' }));
        break;
      default:
        break;
    }
  };

  const handleView = (id: string) => {
    // Navigate to notebook detail page
    console.log('View notebook:', id);
  };

  const handleDownload = (id: string) => {
    // Download notebook
    console.log('Download notebook:', id);
  };

  const handleVote = (id: string, voteType: 'upvote' | 'downvote') => {
    // Handle voting
    console.log('Vote on notebook:', id, voteType);
    setNotebooks(prev => prev.map(nb => {
      if (nb.id === id) {
        const currentVote = nb.user_vote;
        let newUpvotes = nb.upvotes;
        let newDownvotes = nb.downvotes;
        let newUserVote = voteType;

        // Handle vote changes
        if (currentVote === voteType) {
          // Remove vote
          newUserVote = null;
          if (voteType === 'upvote') newUpvotes--;
          else newDownvotes--;
        } else if (currentVote) {
          // Change vote
          if (currentVote === 'upvote') {
            newUpvotes--;
            newDownvotes++;
          } else {
            newDownvotes--;
            newUpvotes++;
          }
        } else {
          // New vote
          if (voteType === 'upvote') newUpvotes++;
          else newDownvotes++;
        }

        return {
          ...nb,
          upvotes: newUpvotes,
          downvotes: newDownvotes,
          user_vote: newUserVote as any
        };
      }
      return nb;
    }));
  };

  const availableLanguages = Array.from(
    new Set(mockNotebooks.flatMap(nb => nb.language_codes))
  ).sort();

  const availableTags = Array.from(
    new Set(mockNotebooks.flatMap(nb => nb.tags))
  ).sort();

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Notebook Library</h1>
          <p className="text-gray-600 mt-2">
            Discover and share Jupyter notebooks for African language processing
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="w-4 h-4 mr-2" />
            {showFilters ? 'Hide' : 'Show'} Filters
          </Button>
          <Button>
            <Upload className="w-4 h-4 mr-2" />
            Upload Notebook
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center gap-3">
            <BookOpen className="w-8 h-8 text-blue-600" />
            <div>
              <div className="text-2xl font-bold">{pagination.total}</div>
              <div className="text-sm text-gray-600">Total Notebooks</div>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center gap-3">
            <TrendingUp className="w-8 h-8 text-green-600" />
            <div>
              <div className="text-2xl font-bold">
                {mockNotebooks.reduce((sum, nb) => sum + nb.usage_stats.downloads, 0)}
              </div>
              <div className="text-sm text-gray-600">Total Downloads</div>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center gap-3">
            <Star className="w-8 h-8 text-yellow-600" />
            <div>
              <div className="text-2xl font-bold">
                {(mockNotebooks.reduce((sum, nb) => sum + nb.rating, 0) / mockNotebooks.length).toFixed(1)}
              </div>
              <div className="text-sm text-gray-600">Avg Rating</div>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center gap-3">
            <BookOpen className="w-8 h-8 text-purple-600" />
            <div>
              <div className="text-2xl font-bold">{availableLanguages.length}</div>
              <div className="text-sm text-gray-600">Languages</div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex gap-8">
        {/* Filters Sidebar */}
        {showFilters && (
          <div className="w-80 flex-shrink-0">
            <NotebookFilters
              filters={filters}
              onFiltersChange={setFilters}
              availableLanguages={availableLanguages}
              availableTags={availableTags}
            />
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1">
          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={handleTabChange} className="mb-6">
            <div className="flex items-center justify-between">
              <TabsList>
                <TabsTrigger value="all">All Notebooks</TabsTrigger>
                <TabsTrigger value="featured">Featured</TabsTrigger>
                <TabsTrigger value="trending">Trending</TabsTrigger>
                <TabsTrigger value="recent">Recent</TabsTrigger>
              </TabsList>
              <div className="flex gap-2">
                <Button
                  variant={viewMode === 'grid' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                >
                  <Grid className="w-4 h-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                >
                  <List className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <TabsContent value={activeTab} className="mt-6">
              {/* Active Filters */}
              {(filters.query || filters.category || filters.difficulty ||
                filters.language_codes.length > 0 || filters.tags.length > 0) && (
                <div className="flex flex-wrap gap-2 mb-6">
                  <span className="text-sm text-gray-600">Active filters:</span>
                  {filters.query && (
                    <Badge variant="secondary">
                      Query: "{filters.query}"
                    </Badge>
                  )}
                  {filters.category && (
                    <Badge variant="secondary">
                      Category: {filters.category.replace('_', ' ')}
                    </Badge>
                  )}
                  {filters.difficulty && (
                    <Badge variant="secondary">
                      Difficulty: {filters.difficulty}
                    </Badge>
                  )}
                  {filters.language_codes.map(lang => (
                    <Badge key={lang} variant="secondary">
                      Language: {lang.toUpperCase()}
                    </Badge>
                  ))}
                  {filters.tags.map(tag => (
                    <Badge key={tag} variant="secondary">
                      Tag: {tag}
                    </Badge>
                  ))}
                </div>
              )}

              {/* Notebook Grid */}
              <NotebookGrid
                notebooks={notebooks}
                loading={loading}
                pagination={pagination}
                onPageChange={(page) => setPagination(prev => ({ ...prev, page }))}
                onView={handleView}
                onDownload={handleDownload}
                onVote={handleVote}
              />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default NotebooksPage;