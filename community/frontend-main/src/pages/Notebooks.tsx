import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen, Plus, Search, Filter, TrendingUp, Star,
  Download, Eye, ThumbsUp, Calendar, User, Tag,
  FileCode, Upload, BookMarked, Grid, List, Loader2
} from 'lucide-react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { useBackendAuth } from '@/contexts/BackendAuthContext';

// Types based on backend models
interface NotebookUsageStats {
  downloads: number;
  views: number;
  forks: number;
  successful_runs: number;
  failed_runs: number;
  avg_execution_time?: number;
}

interface NotebookResponse {
  id: string;
  title: string;
  description: string;
  category: string;
  difficulty: string;
  language_codes: string[];
  tags: string[];
  is_public: boolean;
  license: string;
  author_name: string;
  current_version: string;
  file_size: number;
  upvotes: number;
  downvotes: number;
  rating: number;
  comment_count: number;
  usage_stats: NotebookUsageStats;
  created_at: string;
  updated_at: string;
  published_at?: string;
  user_vote?: 'upvote' | 'downvote';
  is_bookmarked: boolean;
  is_owner: boolean;
}

interface NotebookListResponse {
  notebooks: NotebookResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const API_BASE = 'https://language-community-api.ailabsafrica.com/api/v1';

const Notebooks: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useBackendAuth();

  // State management
  const [activeTab, setActiveTab] = useState('browse');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState('updated_at');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  // Data state
  const [notebooks, setNotebooks] = useState<NotebookResponse[]>([]);
  const [featuredNotebooks, setFeaturedNotebooks] = useState<NotebookResponse[]>([]);
  const [trendingNotebooks, setTrendingNotebooks] = useState<NotebookResponse[]>([]);
  const [myNotebooks, setMyNotebooks] = useState<NotebookResponse[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  // Loading states
  const [loading, setLoading] = useState(false);
  const [featuredLoading, setFeaturedLoading] = useState(false);
  const [trendingLoading, setTrendingLoading] = useState(false);
  const [myNotebooksLoading, setMyNotebooksLoading] = useState(false);

  // Categories from backend enum
  const categories = [
    { value: 'all', label: 'All Categories' },
    { value: 'data_acquisition', label: 'Data Acquisition' },
    { value: 'data_processing', label: 'Data Processing' },
    { value: 'asr_training', label: 'ASR Training' },
    { value: 'tts_training', label: 'TTS Training' },
    { value: 'llm_training', label: 'LLM Training' },
    { value: 'evaluation', label: 'Evaluation' },
    { value: 'deployment', label: 'Deployment' },
    { value: 'research', label: 'Research' },
    { value: 'tutorial', label: 'Tutorial' },
    { value: 'other', label: 'Other' }
  ];

  const difficulties = [
    { value: 'all', label: 'All Levels' },
    { value: 'beginner', label: 'Beginner' },
    { value: 'intermediate', label: 'Intermediate' },
    { value: 'advanced', label: 'Advanced' },
    { value: 'expert', label: 'Expert' }
  ];

  const sortOptions = [
    { value: 'updated_at', label: 'Recently Updated' },
    { value: 'created_at', label: 'Recently Created' },
    { value: 'rating', label: 'Highest Rated' },
    { value: 'upvotes', label: 'Most Upvoted' },
    { value: 'downloads', label: 'Most Downloaded' }
  ];

  // Load featured notebooks on mount
  useEffect(() => {
    loadFeaturedNotebooks();
    loadTrendingNotebooks();
  }, []);

  // Load notebooks when filters change
  useEffect(() => {
    if (activeTab === 'browse') {
      loadNotebooks();
    } else if (activeTab === 'my-notebooks' && user) {
      loadMyNotebooks();
    }
  }, [activeTab, searchQuery, categoryFilter, difficultyFilter, sortBy, page, user]);

  const loadNotebooks = async () => {
    try {
      setLoading(true);

      // Build query parameters
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        sort_by: sortBy,
        sort_order: 'desc'
      });

      if (searchQuery) params.append('query', searchQuery);
      if (categoryFilter !== 'all') params.append('category', categoryFilter);
      if (difficultyFilter !== 'all') params.append('difficulty', difficultyFilter);

      const response = await fetch(`${API_BASE}/notebooks/search?${params.toString()}`);

      if (!response.ok) {
        throw new Error('Failed to load notebooks');
      }

      const data: NotebookListResponse = await response.json();
      setNotebooks(data.notebooks);
      setTotalCount(data.total);
      setTotalPages(data.total_pages);
    } catch (error) {
      console.error('Error loading notebooks:', error);
      toast({
        title: 'Error',
        description: 'Failed to load notebooks. Please try again.',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const loadFeaturedNotebooks = async () => {
    try {
      setFeaturedLoading(true);
      const response = await fetch(`${API_BASE}/notebooks/featured/?page=1&page_size=6`);

      if (response.ok) {
        const data: NotebookListResponse = await response.json();
        setFeaturedNotebooks(data.notebooks);
      }
    } catch (error) {
      console.error('Error loading featured notebooks:', error);
    } finally {
      setFeaturedLoading(false);
    }
  };

  const loadTrendingNotebooks = async () => {
    try {
      setTrendingLoading(true);
      const response = await fetch(`${API_BASE}/notebooks/trending/?page=1&page_size=6`);

      if (response.ok) {
        const data: NotebookListResponse = await response.json();
        setTrendingNotebooks(data.notebooks);
      }
    } catch (error) {
      console.error('Error loading trending notebooks:', error);
    } finally {
      setTrendingLoading(false);
    }
  };

  const loadMyNotebooks = async () => {
    if (!user) return;

    try {
      setMyNotebooksLoading(true);
      const response = await fetch(`${API_BASE}/notebooks/my/notebooks?page=${page}&page_size=${pageSize}`, {
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      });

      if (response.ok) {
        const data: NotebookListResponse = await response.json();
        setMyNotebooks(data.notebooks);
        setTotalCount(data.total);
        setTotalPages(data.total_pages);
      }
    } catch (error) {
      console.error('Error loading my notebooks:', error);
      toast({
        title: 'Error',
        description: 'Failed to load your notebooks.',
        variant: 'destructive'
      });
    } finally {
      setMyNotebooksLoading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getDifficultyColor = (difficulty: string): string => {
    const colors: Record<string, string> = {
      beginner: 'bg-green-100 text-green-800',
      intermediate: 'bg-blue-100 text-blue-800',
      advanced: 'bg-orange-100 text-orange-800',
      expert: 'bg-red-100 text-red-800'
    };
    return colors[difficulty] || 'bg-gray-100 text-gray-800';
  };

  const NotebookCard: React.FC<{ notebook: NotebookResponse; compact?: boolean }> = ({ notebook, compact = false }) => (
    <Card
      className="hover:shadow-lg transition-shadow cursor-pointer group"
      onClick={() => navigate(`/notebooks/${notebook.id}`)}
    >
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg group-hover:text-primary transition-colors line-clamp-1">
              {notebook.title}
            </CardTitle>
            <CardDescription className="mt-1 line-clamp-2">
              {notebook.description}
            </CardDescription>
          </div>
          <Badge className={getDifficultyColor(notebook.difficulty)}>
            {notebook.difficulty}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-3">
          {/* Category and Tags */}
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline" className="capitalize">
              {notebook.category.replace(/_/g, ' ')}
            </Badge>
            {notebook.tags.slice(0, 3).map((tag, idx) => (
              <Badge key={idx} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
            {notebook.tags.length > 3 && (
              <Badge variant="secondary" className="text-xs">
                +{notebook.tags.length - 3}
              </Badge>
            )}
          </div>

          {/* Languages */}
          {notebook.language_codes.length > 0 && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Tag className="h-4 w-4" />
              <span className="line-clamp-1">
                {notebook.language_codes.join(', ')}
              </span>
            </div>
          )}

          {/* Stats */}
          {!compact && (
            <div className="grid grid-cols-2 gap-2 pt-2 border-t text-sm">
              <div className="flex items-center gap-2">
                <ThumbsUp className="h-4 w-4 text-muted-foreground" />
                <span>{notebook.upvotes}</span>
              </div>
              <div className="flex items-center gap-2">
                <Download className="h-4 w-4 text-muted-foreground" />
                <span>{notebook.usage_stats.downloads}</span>
              </div>
              <div className="flex items-center gap-2">
                <Eye className="h-4 w-4 text-muted-foreground" />
                <span>{notebook.usage_stats.views}</span>
              </div>
              <div className="flex items-center gap-2">
                <Star className="h-4 w-4 text-muted-foreground" />
                <span>{notebook.rating.toFixed(1)}</span>
              </div>
            </div>
          )}
        </div>
      </CardContent>

      <CardFooter className="flex items-center justify-between text-sm text-muted-foreground border-t pt-4">
        <div className="flex items-center gap-2">
          <User className="h-4 w-4" />
          <span className="line-clamp-1">{notebook.author_name}</span>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4" />
          <span>{formatDate(notebook.updated_at)}</span>
        </div>
      </CardFooter>
    </Card>
  );

  const NotebookListItem: React.FC<{ notebook: NotebookResponse }> = ({ notebook }) => (
    <Card
      className="hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => navigate(`/notebooks/${notebook.id}`)}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
            <FileCode className="h-6 w-6 text-primary" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h3 className="font-semibold text-base hover:text-primary transition-colors line-clamp-1">
                  {notebook.title}
                </h3>
                <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                  {notebook.description}
                </p>

                <div className="flex flex-wrap items-center gap-3 mt-3 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <User className="h-4 w-4" />
                    {notebook.author_name}
                  </div>
                  <div className="flex items-center gap-1">
                    <ThumbsUp className="h-4 w-4" />
                    {notebook.upvotes}
                  </div>
                  <div className="flex items-center gap-1">
                    <Download className="h-4 w-4" />
                    {notebook.usage_stats.downloads}
                  </div>
                  <div className="flex items-center gap-1">
                    <Star className="h-4 w-4" />
                    {notebook.rating.toFixed(1)}
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {formatDate(notebook.updated_at)}
                  </div>
                </div>
              </div>

              <Badge className={getDifficultyColor(notebook.difficulty)}>
                {notebook.difficulty}
              </Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const LoadingSkeleton = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[...Array(6)].map((_, i) => (
        <Card key={i}>
          <CardHeader>
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-full mt-2" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-20 w-full" />
          </CardContent>
        </Card>
      ))}
    </div>
  );

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold mb-2">Notebook Library</h1>
              <p className="text-lg text-muted-foreground">
                Discover and share Jupyter notebooks for African language processing
              </p>
            </div>
            {user && (
              <Button onClick={() => navigate('/notebooks/upload')} size="lg">
                <Upload className="mr-2 h-5 w-5" />
                Upload Notebook
              </Button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList>
            <TabsTrigger value="browse">
              <BookOpen className="mr-2 h-4 w-4" />
              Browse
            </TabsTrigger>
            <TabsTrigger value="featured">
              <Star className="mr-2 h-4 w-4" />
              Featured
            </TabsTrigger>
            <TabsTrigger value="trending">
              <TrendingUp className="mr-2 h-4 w-4" />
              Trending
            </TabsTrigger>
            {user && (
              <TabsTrigger value="my-notebooks">
                <BookMarked className="mr-2 h-4 w-4" />
                My Notebooks
              </TabsTrigger>
            )}
          </TabsList>

          {/* Browse Tab */}
          <TabsContent value="browse" className="space-y-6">
            {/* Search and Filters */}
            <Card>
              <CardContent className="pt-6">
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                  <div className="md:col-span-2">
                    <div className="relative">
                      <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Search notebooks..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                  </div>

                  <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                    <SelectTrigger>
                      <SelectValue placeholder="Category" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map(cat => (
                        <SelectItem key={cat.value} value={cat.value}>
                          {cat.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <Select value={difficultyFilter} onValueChange={setDifficultyFilter}>
                    <SelectTrigger>
                      <SelectValue placeholder="Difficulty" />
                    </SelectTrigger>
                    <SelectContent>
                      {difficulties.map(diff => (
                        <SelectItem key={diff.value} value={diff.value}>
                          {diff.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger>
                      <SelectValue placeholder="Sort by" />
                    </SelectTrigger>
                    <SelectContent>
                      {sortOptions.map(opt => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center justify-between mt-4 pt-4 border-t">
                  <p className="text-sm text-muted-foreground">
                    {totalCount} {totalCount === 1 ? 'notebook' : 'notebooks'} found
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant={viewMode === 'grid' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setViewMode('grid')}
                    >
                      <Grid className="h-4 w-4" />
                    </Button>
                    <Button
                      variant={viewMode === 'list' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setViewMode('list')}
                    >
                      <List className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Notebooks Grid/List */}
            {loading ? (
              <LoadingSkeleton />
            ) : notebooks.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <FileCode className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No notebooks found</h3>
                  <p className="text-muted-foreground">
                    Try adjusting your filters or search query
                  </p>
                </CardContent>
              </Card>
            ) : viewMode === 'grid' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {notebooks.map(notebook => (
                  <NotebookCard key={notebook.id} notebook={notebook} />
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {notebooks.map(notebook => (
                  <NotebookListItem key={notebook.id} notebook={notebook} />
                ))}
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2">
                <Button
                  variant="outline"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {page} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                </Button>
              </div>
            )}
          </TabsContent>

          {/* Featured Tab */}
          <TabsContent value="featured" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Featured Notebooks</CardTitle>
                <CardDescription>
                  High-quality notebooks curated by our community
                </CardDescription>
              </CardHeader>
            </Card>

            {featuredLoading ? (
              <LoadingSkeleton />
            ) : featuredNotebooks.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <Star className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">No featured notebooks yet</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {featuredNotebooks.map(notebook => (
                  <NotebookCard key={notebook.id} notebook={notebook} />
                ))}
              </div>
            )}
          </TabsContent>

          {/* Trending Tab */}
          <TabsContent value="trending" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Trending Notebooks</CardTitle>
                <CardDescription>
                  Most popular notebooks this week
                </CardDescription>
              </CardHeader>
            </Card>

            {trendingLoading ? (
              <LoadingSkeleton />
            ) : trendingNotebooks.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <TrendingUp className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">No trending notebooks yet</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {trendingNotebooks.map(notebook => (
                  <NotebookCard key={notebook.id} notebook={notebook} />
                ))}
              </div>
            )}
          </TabsContent>

          {/* My Notebooks Tab */}
          {user && (
            <TabsContent value="my-notebooks" className="space-y-6">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>My Notebooks</CardTitle>
                      <CardDescription>
                        Notebooks you've created and uploaded
                      </CardDescription>
                    </div>
                    <Button onClick={() => navigate('/notebooks/upload')}>
                      <Plus className="mr-2 h-4 w-4" />
                      Upload New
                    </Button>
                  </div>
                </CardHeader>
              </Card>

              {myNotebooksLoading ? (
                <LoadingSkeleton />
              ) : myNotebooks.length === 0 ? (
                <Card>
                  <CardContent className="py-12 text-center">
                    <FileCode className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No notebooks yet</h3>
                    <p className="text-muted-foreground mb-4">
                      Upload your first notebook to share with the community
                    </p>
                    <Button onClick={() => navigate('/notebooks/upload')}>
                      <Upload className="mr-2 h-4 w-4" />
                      Upload Notebook
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {myNotebooks.map(notebook => (
                    <NotebookCard key={notebook.id} notebook={notebook} />
                  ))}
                </div>
              )}
            </TabsContent>
          )}
        </Tabs>
      </main>

      <Footer />
    </div>
  );
};

export default Notebooks;
