import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { VoiceTemplate } from './VoiceAgentTemplates';
import { CustomTemplate } from './TemplateCustomization';
import { 
  BarChart3,
  LineChart,
  PieChart,
  TrendingUp,
  TrendingDown,
  Users,
  Clock,
  Star,
  Eye,
  Download,
  Filter,
  Calendar,
  Target,
  Award,
  Activity,
  Loader2,
  RefreshCw,
  FileText,
  Share2,
  Zap,
  CheckCircle,
  AlertCircle,
  ArrowUp,
  ArrowDown,
  Minus
} from 'lucide-react';

interface AnalyticsData {
  templateId: string;
  templateName: string;
  usageCount: number;
  successRate: number;
  averageResponseTime: number;
  totalConversations: number;
  uniqueUsers: number;
  averageSessionDuration: number;
  conversionRate: number;
  satisfactionScore: number;
  errorRate: number;
  lastUsed: string;
  createdAt: string;
  category: string;
  difficulty: string;
  isPublic: boolean;
  isFavorite: boolean;
  tags: string[];
  features: string[];
}

interface AnalyticsFilters {
  dateRange: '7d' | '30d' | '90d' | '1y' | 'all';
  category: string;
  difficulty: string;
  sortBy: 'usage' | 'success' | 'popularity' | 'recent' | 'name';
  sortOrder: 'asc' | 'desc';
  showPublic: boolean;
  showFavorites: boolean;
}

interface TemplateAnalyticsProps {
  templates: (VoiceTemplate | CustomTemplate)[];
  onClose: () => void;
}

const TemplateAnalytics: React.FC<TemplateAnalyticsProps> = ({ templates, onClose }) => {
  const [isOpen, setIsOpen] = useState(true);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<AnalyticsFilters>({
    dateRange: '30d',
    category: 'all',
    difficulty: 'all',
    sortBy: 'usage',
    sortOrder: 'desc',
    showPublic: true,
    showFavorites: false
  });
  const [selectedTemplate, setSelectedTemplate] = useState<AnalyticsData | null>(null);
  const [detailedView, setDetailedView] = useState(false);
  const { toast } = useToast();

  // Generate mock analytics data for demonstration
  useEffect(() => {
    generateAnalyticsData();
  }, [templates]);

  const generateAnalyticsData = () => {
    const mockData: AnalyticsData[] = templates.map((template, index) => ({
      templateId: template.id,
      templateName: template.name,
      usageCount: Math.floor(Math.random() * 1000) + 50,
      successRate: Math.random() * 30 + 70, // 70-100%
      averageResponseTime: Math.random() * 3000 + 500, // 500-3500ms
      totalConversations: Math.floor(Math.random() * 5000) + 100,
      uniqueUsers: Math.floor(Math.random() * 500) + 20,
      averageSessionDuration: Math.random() * 600 + 120, // 2-12 minutes
      conversionRate: Math.random() * 25 + 5, // 5-30%
      satisfactionScore: Math.random() * 2 + 3, // 3-5 stars
      errorRate: Math.random() * 15 + 1, // 1-16%
      lastUsed: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      createdAt: template.createdAt || new Date().toISOString(),
      category: template.category,
      difficulty: template.difficulty,
      isPublic: 'isPublic' in template ? template.isPublic : false,
      isFavorite: 'isFavorite' in template ? template.isFavorite : false,
      tags: template.tags,
      features: template.features
    }));

    setAnalyticsData(mockData);
  };

  const filteredData = analyticsData.filter(item => {
    if (filters.category !== 'all' && item.category !== filters.category) return false;
    if (filters.difficulty !== 'all' && item.difficulty !== filters.difficulty) return false;
    if (filters.showPublic && !item.isPublic) return false;
    if (filters.showFavorites && !item.isFavorite) return false;
    return true;
  });

  const sortedData = [...filteredData].sort((a, b) => {
    let comparison = 0;
    switch (filters.sortBy) {
      case 'usage':
        comparison = a.usageCount - b.usageCount;
        break;
      case 'success':
        comparison = a.successRate - b.successRate;
        break;
      case 'popularity':
        comparison = a.totalConversations - b.totalConversations;
        break;
      case 'recent':
        comparison = new Date(a.lastUsed).getTime() - new Date(b.lastUsed).getTime();
        break;
      case 'name':
        comparison = a.templateName.localeCompare(b.templateName);
        break;
    }
    return filters.sortOrder === 'asc' ? comparison : -comparison;
  });

  const getTrendIcon = (current: number, previous: number) => {
    if (current > previous) return <ArrowUp className="h-4 w-4 text-green-500" />;
    if (current < previous) return <ArrowDown className="h-4 w-4 text-red-500" />;
    return <Minus className="h-4 w-4 text-gray-500" />;
  };

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 90) return 'text-green-600';
    if (rate >= 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Beginner': return 'bg-green-100 text-green-800';
      case 'Intermediate': return 'bg-yellow-100 text-yellow-800';
      case 'Advanced': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const exportAnalytics = () => {
    const csvContent = [
      ['Template Name', 'Usage Count', 'Success Rate', 'Response Time', 'Conversations', 'Users', 'Category', 'Difficulty'],
      ...sortedData.map(item => [
        item.templateName,
        item.usageCount.toString(),
        `${item.successRate.toFixed(1)}%`,
        `${item.averageResponseTime.toFixed(0)}ms`,
        item.totalConversations.toString(),
        item.uniqueUsers.toString(),
        item.category,
        item.difficulty
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `template-analytics-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    toast({
      title: "Analytics Exported",
      description: "Template analytics data has been exported to CSV",
    });
  };

  const refreshAnalytics = async () => {
    setLoading(true);
    try {
      // Simulate API call to refresh analytics
      await new Promise(resolve => setTimeout(resolve, 2000));
      generateAnalyticsData();
      toast({
        title: "Analytics Refreshed",
        description: "Template analytics data has been updated",
      });
    } catch (error) {
      toast({
        title: "Refresh Failed",
        description: "Failed to refresh analytics data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const renderOverview = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Usage</CardTitle>
          <Users className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {sortedData.reduce((sum, item) => sum + item.usageCount, 0).toLocaleString()}
          </div>
          <p className="text-xs text-muted-foreground">
            +12% from last month
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Average Success Rate</CardTitle>
          <Target className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {(sortedData.reduce((sum, item) => sum + item.successRate, 0) / sortedData.length).toFixed(1)}%
          </div>
          <p className="text-xs text-muted-foreground">
            +2.1% from last month
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Templates</CardTitle>
          <Zap className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {sortedData.filter(item => item.usageCount > 0).length}
          </div>
          <p className="text-xs text-muted-foreground">
            {sortedData.length} total templates
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {(sortedData.reduce((sum, item) => sum + item.averageResponseTime, 0) / sortedData.length).toFixed(0)}ms
          </div>
          <p className="text-xs text-muted-foreground">
            -5% from last month
          </p>
        </CardContent>
      </Card>
    </div>
  );

  const renderTemplateList = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Template Performance</h3>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={refreshAnalytics} disabled={loading}>
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </Button>
          <Button variant="outline" size="sm" onClick={exportAnalytics}>
            <Download className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="space-y-2">
        {sortedData.map((item) => (
          <Card key={item.templateId} className="cursor-pointer hover:bg-muted/50 transition-colors">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium">{item.templateName}</h4>
                      <Badge className={getDifficultyColor(item.difficulty)}>
                        {item.difficulty}
                      </Badge>
                      <Badge variant="outline">{item.category}</Badge>
                      {item.isPublic && <Badge variant="secondary">Public</Badge>}
                      {item.isFavorite && <Star className="h-4 w-4 text-yellow-500 fill-current" />}
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {item.tags.slice(0, 3).join(', ')}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-6">
                  <div className="text-center">
                    <div className="text-sm font-medium">{item.usageCount.toLocaleString()}</div>
                    <div className="text-xs text-muted-foreground">Usage</div>
                  </div>
                  <div className="text-center">
                    <div className={`text-sm font-medium ${getSuccessRateColor(item.successRate)}`}>
                      {item.successRate.toFixed(1)}%
                    </div>
                    <div className="text-xs text-muted-foreground">Success</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm font-medium">{item.averageResponseTime.toFixed(0)}ms</div>
                    <div className="text-xs text-muted-foreground">Response</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm font-medium">{item.totalConversations.toLocaleString()}</div>
                    <div className="text-xs text-muted-foreground">Conversations</div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSelectedTemplate(item);
                      setDetailedView(true);
                    }}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderDetailedView = () => {
    if (!selectedTemplate) return null;

    return (
      <Dialog open={detailedView} onOpenChange={setDetailedView}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Template Analytics: {selectedTemplate.templateName}</DialogTitle>
            <DialogDescription>
              Detailed performance metrics and insights
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold">{selectedTemplate.usageCount.toLocaleString()}</div>
                  <div className="text-sm text-muted-foreground">Total Usage</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className={`text-2xl font-bold ${getSuccessRateColor(selectedTemplate.successRate)}`}>
                    {selectedTemplate.successRate.toFixed(1)}%
                  </div>
                  <div className="text-sm text-muted-foreground">Success Rate</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold">{selectedTemplate.averageResponseTime.toFixed(0)}ms</div>
                  <div className="text-sm text-muted-foreground">Avg Response Time</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold">{selectedTemplate.totalConversations.toLocaleString()}</div>
                  <div className="text-sm text-muted-foreground">Conversations</div>
                </CardContent>
              </Card>
            </div>

            {/* Additional Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>User Engagement</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between">
                    <span>Unique Users</span>
                    <span className="font-medium">{selectedTemplate.uniqueUsers.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Avg Session Duration</span>
                    <span className="font-medium">{Math.floor(selectedTemplate.averageSessionDuration / 60)}m {selectedTemplate.averageSessionDuration % 60}s</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Conversion Rate</span>
                    <span className="font-medium">{selectedTemplate.conversionRate.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Satisfaction Score</span>
                    <span className="font-medium">{selectedTemplate.satisfactionScore.toFixed(1)}/5</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Performance Metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between">
                    <span>Error Rate</span>
                    <span className="font-medium text-red-600">{selectedTemplate.errorRate.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Last Used</span>
                    <span className="font-medium">{new Date(selectedTemplate.lastUsed).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Created</span>
                    <span className="font-medium">{new Date(selectedTemplate.createdAt).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Category</span>
                    <span className="font-medium">{selectedTemplate.category}</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Tags and Features */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Tags</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {selectedTemplate.tags.map((tag, index) => (
                      <Badge key={index} variant="outline">#{tag}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Features</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {selectedTemplate.features.map((feature, index) => (
                      <Badge key={index} variant="secondary">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        {feature}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Template Analytics</DialogTitle>
          <DialogDescription>
            Track template usage, success rates, and performance metrics
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="templates">Templates</TabsTrigger>
            <TabsTrigger value="filters">Filters</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {renderOverview()}
            {renderTemplateList()}
          </TabsContent>

          <TabsContent value="templates" className="space-y-6">
            {renderTemplateList()}
          </TabsContent>

          <TabsContent value="filters" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Analytics Filters</CardTitle>
                <CardDescription>
                  Customize the analytics view with filters and sorting options
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="date-range">Date Range</Label>
                    <Select
                      value={filters.dateRange}
                      onValueChange={(value) => setFilters(prev => ({ ...prev, dateRange: value as any }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="7d">Last 7 days</SelectItem>
                        <SelectItem value="30d">Last 30 days</SelectItem>
                        <SelectItem value="90d">Last 90 days</SelectItem>
                        <SelectItem value="1y">Last year</SelectItem>
                        <SelectItem value="all">All time</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="category">Category</Label>
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
                        <SelectItem value="Scheduling">Scheduling</SelectItem>
                        <SelectItem value="Research">Research</SelectItem>
                        <SelectItem value="Insurance">Insurance</SelectItem>
                        <SelectItem value="Real Estate">Real Estate</SelectItem>
                        <SelectItem value="Healthcare">Healthcare</SelectItem>
                        <SelectItem value="Banking">Banking</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="difficulty">Difficulty</Label>
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
                    <Label htmlFor="sort-by">Sort By</Label>
                    <Select
                      value={filters.sortBy}
                      onValueChange={(value) => setFilters(prev => ({ ...prev, sortBy: value as any }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="usage">Usage Count</SelectItem>
                        <SelectItem value="success">Success Rate</SelectItem>
                        <SelectItem value="popularity">Popularity</SelectItem>
                        <SelectItem value="recent">Recently Used</SelectItem>
                        <SelectItem value="name">Name</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex gap-4">
                  <Button
                    variant="outline"
                    onClick={() => setFilters({
                      dateRange: '30d',
                      category: 'all',
                      difficulty: 'all',
                      sortBy: 'usage',
                      sortOrder: 'desc',
                      showPublic: true,
                      showFavorites: false
                    })}
                  >
                    Reset Filters
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {renderDetailedView()}

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => setIsOpen(false)}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TemplateAnalytics;
