import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { VoiceTemplate } from './VoiceAgentTemplates';
import { CustomTemplate } from './TemplateCustomization';
import { 
  Store,
  Star,
  Heart,
  Download,
  Eye,
  MessageSquare,
  Filter,
  Search,
  TrendingUp,
  Award,
  Users,
  Clock,
  Calendar,
  Tag,
  Hash,
  Globe,
  Zap,
  CheckCircle,
  AlertCircle,
  Loader2,
  RefreshCw,
  ExternalLink,
  Settings,
  Shield,
  Bookmark,
  Share2,
  ThumbsUp,
  ThumbsDown,
  Edit3,
  Trash2,
  Plus,
  Minus,
  ArrowUp,
  ArrowDown,
  MoreHorizontal,
  Grid3X3,
  List,
  SortAsc,
  SortDesc,
  Filter as FilterIcon,
  X,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface MarketplaceTemplate {
  id: string;
  templateId: string;
  name: string;
  description: string;
  author: {
    id: string;
    name: string;
    avatar: string;
    verified: boolean;
    reputation: number;
  };
  category: string;
  difficulty: string;
  tags: string[];
  features: string[];
  rating: number;
  reviewCount: number;
  downloadCount: number;
  viewCount: number;
  favoriteCount: number;
  price: number;
  isFree: boolean;
  isPremium: boolean;
  isVerified: boolean;
  isFeatured: boolean;
  isTrending: boolean;
  lastUpdated: string;
  createdAt: string;
  version: string;
  compatibility: string[];
  requirements: string[];
  preview: {
    image: string;
    demo: string;
    screenshots: string[];
  };
  stats: {
    successRate: number;
    averageResponseTime: number;
    totalConversations: number;
    uniqueUsers: number;
  };
  reviews: MarketplaceReview[];
}

interface MarketplaceReview {
  id: string;
  userId: string;
  userName: string;
  userAvatar: string;
  rating: number;
  review: string;
  helpful: number;
  notHelpful: number;
  createdAt: string;
  isVerified: boolean;
  tags: string[];
}

interface MarketplaceFilters {
  search: string;
  category: string;
  difficulty: string;
  price: 'all' | 'free' | 'paid';
  rating: number;
  sortBy: 'popular' | 'rating' | 'newest' | 'downloads' | 'trending';
  sortOrder: 'asc' | 'desc';
  tags: string[];
  features: string[];
  compatibility: string[];
}

interface TemplateMarketplaceProps {
  onClose: () => void;
  onSelectTemplate?: (template: MarketplaceTemplate) => void;
}

const TemplateMarketplace: React.FC<TemplateMarketplaceProps> = ({ onClose, onSelectTemplate }) => {
  const [isOpen, setIsOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('browse');
  const [templates, setTemplates] = useState<MarketplaceTemplate[]>([]);
  const [filteredTemplates, setFilteredTemplates] = useState<MarketplaceTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<MarketplaceTemplate | null>(null);
  const [filters, setFilters] = useState<MarketplaceFilters>({
    search: '',
    category: 'all',
    difficulty: 'all',
    price: 'all',
    rating: 0,
    sortBy: 'popular',
    sortOrder: 'desc',
    tags: [],
    features: [],
    compatibility: []
  });
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(false);
  const [showReviewDialog, setShowReviewDialog] = useState(false);
  const [reviewForm, setReviewForm] = useState({
    rating: 5,
    review: '',
    tags: [] as string[]
  });
  const { toast } = useToast();

  // Generate mock marketplace data
  useEffect(() => {
    generateMockData();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [templates, filters]);

  const generateMockData = () => {
    const mockTemplates: MarketplaceTemplate[] = [
      {
        id: '1',
        templateId: 'template-1',
        name: 'Advanced Customer Service Bot',
        description: 'A comprehensive customer service assistant with multi-language support, sentiment analysis, and escalation handling.',
        author: {
          id: 'user-1',
          name: 'Sarah Johnson',
          avatar: '/avatars/sarah.jpg',
          verified: true,
          reputation: 95
        },
        category: 'Customer Service',
        difficulty: 'Advanced',
        tags: ['customer-service', 'multi-language', 'sentiment-analysis', 'escalation'],
        features: ['Multi-language Support', 'Sentiment Analysis', 'Escalation Handling', 'Knowledge Base Integration'],
        rating: 4.8,
        reviewCount: 127,
        downloadCount: 2341,
        viewCount: 15678,
        favoriteCount: 892,
        price: 0,
        isFree: true,
        isPremium: false,
        isVerified: true,
        isFeatured: true,
        isTrending: true,
        lastUpdated: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        createdAt: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        version: '2.1.0',
        compatibility: ['Vapi', 'OpenAI', 'Anthropic'],
        requirements: ['Vapi Account', 'OpenAI API Key'],
        preview: {
          image: '/templates/customer-service-bot.jpg',
          demo: 'https://demo.example.com/customer-service-bot',
          screenshots: ['/screenshots/cs-1.jpg', '/screenshots/cs-2.jpg', '/screenshots/cs-3.jpg']
        },
        stats: {
          successRate: 94.2,
          averageResponseTime: 1.8,
          totalConversations: 45678,
          uniqueUsers: 1234
        },
        reviews: [
          {
            id: 'review-1',
            userId: 'user-2',
            userName: 'Mike Chen',
            userAvatar: '/avatars/mike.jpg',
            rating: 5,
            review: 'Excellent template! The multi-language support works perfectly and the sentiment analysis is spot on.',
            helpful: 23,
            notHelpful: 1,
            createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
            isVerified: true,
            tags: ['helpful', 'detailed', 'verified']
          }
        ]
      },
      {
        id: '2',
        templateId: 'template-2',
        name: 'Sales Lead Qualification Pro',
        description: 'Professional sales qualification template with BANT methodology, lead scoring, and CRM integration.',
        author: {
          id: 'user-2',
          name: 'Alex Rodriguez',
          avatar: '/avatars/alex.jpg',
          verified: true,
          reputation: 87
        },
        category: 'Sales',
        difficulty: 'Intermediate',
        tags: ['sales', 'lead-qualification', 'bant', 'crm-integration'],
        features: ['BANT Methodology', 'Lead Scoring', 'CRM Integration', 'Follow-up Automation'],
        rating: 4.6,
        reviewCount: 89,
        downloadCount: 1567,
        viewCount: 8923,
        favoriteCount: 456,
        price: 29.99,
        isFree: false,
        isPremium: true,
        isVerified: true,
        isFeatured: false,
        isTrending: true,
        lastUpdated: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        createdAt: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString(),
        version: '1.5.2',
        compatibility: ['Vapi', 'Salesforce', 'HubSpot'],
        requirements: ['Vapi Account', 'Salesforce/HubSpot Integration'],
        preview: {
          image: '/templates/sales-lead-qual.jpg',
          demo: 'https://demo.example.com/sales-lead-qual',
          screenshots: ['/screenshots/sales-1.jpg', '/screenshots/sales-2.jpg']
        },
        stats: {
          successRate: 91.5,
          averageResponseTime: 2.1,
          totalConversations: 23456,
          uniqueUsers: 789
        },
        reviews: []
      },
      {
        id: '3',
        templateId: 'template-3',
        name: 'Healthcare Appointment Scheduler',
        description: 'Medical appointment scheduling with insurance verification, patient intake, and calendar integration.',
        author: {
          id: 'user-3',
          name: 'Dr. Emily Brown',
          avatar: '/avatars/emily.jpg',
          verified: true,
          reputation: 92
        },
        category: 'Healthcare',
        difficulty: 'Advanced',
        tags: ['healthcare', 'appointments', 'insurance', 'patient-intake'],
        features: ['Insurance Verification', 'Patient Intake', 'Calendar Integration', 'HIPAA Compliant'],
        rating: 4.9,
        reviewCount: 203,
        downloadCount: 3456,
        viewCount: 23456,
        favoriteCount: 1234,
        price: 49.99,
        isFree: false,
        isPremium: true,
        isVerified: true,
        isFeatured: true,
        isTrending: false,
        lastUpdated: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        createdAt: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
        version: '3.0.1',
        compatibility: ['Vapi', 'Practice Management Systems'],
        requirements: ['Vapi Account', 'HIPAA Compliance'],
        preview: {
          image: '/templates/healthcare-scheduler.jpg',
          demo: 'https://demo.example.com/healthcare-scheduler',
          screenshots: ['/screenshots/health-1.jpg', '/screenshots/health-2.jpg', '/screenshots/health-3.jpg']
        },
        stats: {
          successRate: 96.8,
          averageResponseTime: 1.5,
          totalConversations: 67890,
          uniqueUsers: 2345
        },
        reviews: []
      }
    ];

    setTemplates(mockTemplates);
  };

  const applyFilters = () => {
    let filtered = [...templates];

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(template =>
        template.name.toLowerCase().includes(searchLower) ||
        template.description.toLowerCase().includes(searchLower) ||
        template.tags.some(tag => tag.toLowerCase().includes(searchLower))
      );
    }

    // Category filter
    if (filters.category !== 'all') {
      filtered = filtered.filter(template => template.category === filters.category);
    }

    // Difficulty filter
    if (filters.difficulty !== 'all') {
      filtered = filtered.filter(template => template.difficulty === filters.difficulty);
    }

    // Price filter
    if (filters.price === 'free') {
      filtered = filtered.filter(template => template.isFree);
    } else if (filters.price === 'paid') {
      filtered = filtered.filter(template => !template.isFree);
    }

    // Rating filter
    if (filters.rating > 0) {
      filtered = filtered.filter(template => template.rating >= filters.rating);
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      switch (filters.sortBy) {
        case 'popular':
          comparison = a.downloadCount - b.downloadCount;
          break;
        case 'rating':
          comparison = a.rating - b.rating;
          break;
        case 'newest':
          comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
          break;
        case 'downloads':
          comparison = a.downloadCount - b.downloadCount;
          break;
        case 'trending':
          comparison = a.viewCount - b.viewCount;
          break;
      }
      return filters.sortOrder === 'asc' ? comparison : -comparison;
    });

    setFilteredTemplates(filtered);
  };

  const handleDownload = async (template: MarketplaceTemplate) => {
    setLoading(true);
    try {
      // Simulate download process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      toast({
        title: "Template Downloaded",
        description: `${template.name} has been added to your templates`,
      });

      if (onSelectTemplate) {
        onSelectTemplate(template);
      }
    } catch (error) {
      toast({
        title: "Download Failed",
        description: "Failed to download template. Please try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async () => {
    if (!selectedTemplate || !reviewForm.review.trim()) {
      toast({
        title: "Review Required",
        description: "Please provide a review before submitting",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    try {
      // Simulate review submission
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      toast({
        title: "Review Submitted",
        description: "Thank you for your review!",
      });

      setShowReviewDialog(false);
      setReviewForm({ rating: 5, review: '', tags: [] });
    } catch (error) {
      toast({
        title: "Review Failed",
        description: "Failed to submit review. Please try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const renderTemplateCard = (template: MarketplaceTemplate) => (
    <Card key={template.id} className="hover:shadow-lg transition-all duration-200 cursor-pointer">
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-lg font-semibold">{template.name}</h3>
              {template.isVerified && <Badge className="bg-blue-100 text-blue-800">Verified</Badge>}
              {template.isFeatured && <Badge className="bg-yellow-100 text-yellow-800">Featured</Badge>}
              {template.isTrending && <Badge className="bg-red-100 text-red-800">Trending</Badge>}
            </div>
            <p className="text-sm text-muted-foreground mb-3">{template.description}</p>
            
            <div className="flex items-center gap-4 mb-3">
              <div className="flex items-center gap-1">
                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                <span className="text-sm font-medium">{template.rating}</span>
                <span className="text-sm text-muted-foreground">({template.reviewCount})</span>
              </div>
              <div className="flex items-center gap-1">
                <Download className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">{template.downloadCount.toLocaleString()}</span>
              </div>
              <div className="flex items-center gap-1">
                <Eye className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">{template.viewCount.toLocaleString()}</span>
              </div>
            </div>

            <div className="flex flex-wrap gap-1 mb-3">
              <Badge variant="outline">{template.category}</Badge>
              <Badge variant="outline">{template.difficulty}</Badge>
              {template.isFree ? (
                <Badge className="bg-green-100 text-green-800">Free</Badge>
              ) : (
                <Badge className="bg-purple-100 text-purple-800">${template.price}</Badge>
              )}
            </div>

            <div className="flex flex-wrap gap-1">
              {template.tags.slice(0, 3).map((tag, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  #{tag}
                </Badge>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setSelectedTemplate(template);
              }}
            >
              <Eye className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handleDownload(template);
              }}
              disabled={loading}
            >
              <Download className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setSelectedTemplate(template);
                setShowReviewDialog(true);
              }}
            >
              <MessageSquare className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="flex items-center justify-between pt-3 border-t">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center">
              <span className="text-xs font-medium">{template.author.name.charAt(0)}</span>
            </div>
            <span className="text-sm font-medium">{template.author.name}</span>
            {template.author.verified && <Badge className="bg-green-100 text-green-800 text-xs">Verified</Badge>}
          </div>
          <span className="text-xs text-muted-foreground">
            Updated {new Date(template.lastUpdated).toLocaleDateString()}
          </span>
        </div>
      </CardContent>
    </Card>
  );

  const renderBrowseTab = () => (
    <div className="space-y-6">
      {/* Header with search and filters */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 flex-1">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search templates..."
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
              className="pl-10"
            />
          </div>
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2"
          >
            <FilterIcon className="h-4 w-4" />
            Filters
            {showFilters ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant={viewMode === 'grid' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('grid')}
          >
            <Grid3X3 className="h-4 w-4" />
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

      {/* Filters */}
      {showFilters && (
        <Card>
          <CardContent className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <Label>Category</Label>
                <Select
                  value={filters.category}
                  onValueChange={(value) => setFilters(prev => ({ ...prev, category: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Categories</SelectItem>
                    <SelectItem value="Customer Service">Customer Service</SelectItem>
                    <SelectItem value="Sales">Sales</SelectItem>
                    <SelectItem value="Healthcare">Healthcare</SelectItem>
                    <SelectItem value="Scheduling">Scheduling</SelectItem>
                    <SelectItem value="Research">Research</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Difficulty</Label>
                <Select
                  value={filters.difficulty}
                  onValueChange={(value) => setFilters(prev => ({ ...prev, difficulty: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Difficulties</SelectItem>
                    <SelectItem value="Beginner">Beginner</SelectItem>
                    <SelectItem value="Intermediate">Intermediate</SelectItem>
                    <SelectItem value="Advanced">Advanced</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Price</Label>
                <Select
                  value={filters.price}
                  onValueChange={(value) => setFilters(prev => ({ ...prev, price: value as any }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Prices</SelectItem>
                    <SelectItem value="free">Free</SelectItem>
                    <SelectItem value="paid">Paid</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Sort By</Label>
                <Select
                  value={filters.sortBy}
                  onValueChange={(value) => setFilters(prev => ({ ...prev, sortBy: value as any }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="popular">Most Popular</SelectItem>
                    <SelectItem value="rating">Highest Rated</SelectItem>
                    <SelectItem value="newest">Newest</SelectItem>
                    <SelectItem value="downloads">Most Downloaded</SelectItem>
                    <SelectItem value="trending">Trending</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Templates Grid/List */}
      <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'}>
        {filteredTemplates.map(renderTemplateCard)}
      </div>

      {filteredTemplates.length === 0 && (
        <div className="text-center py-12">
          <Store className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No templates found</h3>
          <p className="text-muted-foreground">Try adjusting your filters or search terms</p>
        </div>
      )}
    </div>
  );

  const renderTemplateDetails = () => {
    if (!selectedTemplate) return null;

    return (
      <Dialog open={!!selectedTemplate} onOpenChange={() => setSelectedTemplate(null)}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedTemplate.name}</DialogTitle>
            <DialogDescription>
              {selectedTemplate.description}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* Template Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold mb-2">Template Details</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Category:</span>
                    <span>{selectedTemplate.category}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Difficulty:</span>
                    <span>{selectedTemplate.difficulty}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Version:</span>
                    <span>{selectedTemplate.version}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Last Updated:</span>
                    <span>{new Date(selectedTemplate.lastUpdated).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Downloads:</span>
                    <span>{selectedTemplate.downloadCount.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Rating:</span>
                    <span>⭐ {selectedTemplate.rating} ({selectedTemplate.reviewCount} reviews)</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Author</h3>
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center">
                    <span className="font-medium">{selectedTemplate.author.name.charAt(0)}</span>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{selectedTemplate.author.name}</span>
                      {selectedTemplate.author.verified && <Badge className="bg-green-100 text-green-800">Verified</Badge>}
                    </div>
                    <p className="text-sm text-muted-foreground">Reputation: {selectedTemplate.author.reputation}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Features */}
            <div>
              <h3 className="font-semibold mb-2">Features</h3>
              <div className="flex flex-wrap gap-2">
                {selectedTemplate.features.map((feature, index) => (
                  <Badge key={index} variant="secondary">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    {feature}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Tags */}
            <div>
              <h3 className="font-semibold mb-2">Tags</h3>
              <div className="flex flex-wrap gap-2">
                {selectedTemplate.tags.map((tag, index) => (
                  <Badge key={index} variant="outline">
                    #{tag}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Stats */}
            <div>
              <h3 className="font-semibold mb-2">Performance Stats</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{selectedTemplate.stats.successRate}%</div>
                  <div className="text-sm text-muted-foreground">Success Rate</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">{selectedTemplate.stats.averageResponseTime}s</div>
                  <div className="text-sm text-muted-foreground">Avg Response</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">{selectedTemplate.stats.totalConversations.toLocaleString()}</div>
                  <div className="text-sm text-muted-foreground">Conversations</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">{selectedTemplate.stats.uniqueUsers.toLocaleString()}</div>
                  <div className="text-sm text-muted-foreground">Users</div>
                </div>
              </div>
            </div>

            {/* Reviews */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">Reviews ({selectedTemplate.reviewCount})</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowReviewDialog(true)}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Write Review
                </Button>
              </div>

              <div className="space-y-4">
                {selectedTemplate.reviews.map((review) => (
                  <Card key={review.id}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                            <span className="text-sm font-medium">{review.userName.charAt(0)}</span>
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{review.userName}</span>
                              {review.isVerified && <Badge className="bg-green-100 text-green-800 text-xs">Verified</Badge>}
                            </div>
                            <div className="flex items-center gap-1">
                              {[...Array(5)].map((_, i) => (
                                <Star
                                  key={i}
                                  className={`h-3 w-3 ${i < review.rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
                                />
                              ))}
                            </div>
                          </div>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {new Date(review.createdAt).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-sm mb-2">{review.review}</p>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>Helpful ({review.helpful})</span>
                        <span>Not Helpful ({review.notHelpful})</span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setShowReviewDialog(true)}
              >
                <MessageSquare className="h-4 w-4 mr-2" />
                Write Review
              </Button>
              <Button
                onClick={() => handleDownload(selectedTemplate)}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Downloading...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-2" />
                    Download Template
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    );
  };

  const renderReviewDialog = () => (
    <Dialog open={showReviewDialog} onOpenChange={setShowReviewDialog}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Write a Review</DialogTitle>
          <DialogDescription>
            Share your experience with this template
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <Label>Rating</Label>
            <div className="flex items-center gap-1 mt-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <Star
                  key={star}
                  className={`h-6 w-6 cursor-pointer ${
                    star <= reviewForm.rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
                  }`}
                  onClick={() => setReviewForm(prev => ({ ...prev, rating: star }))}
                />
              ))}
            </div>
          </div>

          <div>
            <Label>Review</Label>
            <Textarea
              placeholder="Share your experience with this template..."
              value={reviewForm.review}
              onChange={(e) => setReviewForm(prev => ({ ...prev, review: e.target.value }))}
              rows={4}
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => setShowReviewDialog(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleReview}
              disabled={loading || !reviewForm.review.trim()}
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Submitting...
                </>
              ) : (
                'Submit Review'
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Store className="h-5 w-5" />
            Template Marketplace
          </DialogTitle>
          <DialogDescription>
            Discover and download community-created templates
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="browse">Browse</TabsTrigger>
            <TabsTrigger value="trending">Trending</TabsTrigger>
            <TabsTrigger value="featured">Featured</TabsTrigger>
          </TabsList>

          <TabsContent value="browse" className="space-y-6">
            {renderBrowseTab()}
          </TabsContent>

          <TabsContent value="trending" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {templates.filter(t => t.isTrending).map(renderTemplateCard)}
            </div>
          </TabsContent>

          <TabsContent value="featured" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {templates.filter(t => t.isFeatured).map(renderTemplateCard)}
            </div>
          </TabsContent>
        </Tabs>

        {renderTemplateDetails()}
        {renderReviewDialog()}

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => setIsOpen(false)}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TemplateMarketplace;
