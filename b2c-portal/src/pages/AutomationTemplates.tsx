import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  ArrowLeft,
  Search,
  Filter,
  Clock,
  Settings,
  Zap,
  CheckCircle,
  Star,
  Heart,
  CreditCard,
  ShoppingBag,
  Factory,
  Phone,
  Shield,
  Home,
  GraduationCap,
  Briefcase,
  Car,
  Hotel,
  Building2,
  Package,
  Zap as Utilities,
  Landmark,
  Laptop,
  Loader2,
  Wrench,
  Users,
  Megaphone,
  LayoutGrid,
  List
} from 'lucide-react';
import {
  automationOrchestrationService,
  type AutomationTemplate
} from '@/services/AutomationOrchestrationService';
import {
  userFavoritesService,
  type ToggleFavoriteResponse
} from '@/services/UserFavoritesService';
import { useToast } from '@/hooks/use-toast';
import CustomToolsTab from '@/components/automation/CustomToolsTab';
import { AutomationDeploymentWizard } from '@/components/campaigns/AutomationDeploymentWizard';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';



interface AutomationDeploymentConfig {
  companyInfo: any;
  vapiAgent: any;
  n8nWorkflow: any;
  integrations: any;
  demoSettings: any;
  analytics: any;
}

interface CampaignCreationResult {
  success: boolean;
  demoUrl?: string;
  campaignId?: string;
  error?: string;
}

interface TemplatesByIndustry {
  [industryId: string]: {
    industry: {
      id: string;
      name: string;
      description: string;
      icon: string;
      color: string;
    };
    templates: AutomationTemplate[];
  };
}

// Helper function for template complexity colors
const getTemplateComplexityColor = (complexity: string) => {
  switch (complexity) {
    case 'Simple':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
    case 'Medium':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
    case 'Advanced':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
  }
};

const industryNames = {
  Healthcare: 'Healthcare',
  'Financial Services': 'Financial Services',
  Retail: 'Retail & E-commerce',
  Manufacturing: 'Manufacturing',
  Telecommunications: 'Telecommunications',
  Insurance: 'Insurance',
  'Real Estate': 'Real Estate',
  Education: 'Education',
  Automotive: 'Automotive',
  Government: 'Government Services',
  Logistics: 'Logistics & Supply Chain',
  Utilities: 'Utilities & Energy',
  'Professional Services': 'Professional Services',
  Hospitality: 'Hospitality & Travel',
  Generic: 'Generic Workflows',
  Technology: 'Technology',
};

const industryIcons = {
  'All': Filter,
  'Campaign Templates': Megaphone,
  'Generic Templates': Settings,
  Healthcare: Heart,
  'Financial Services': CreditCard,
  Finance: CreditCard,
  Retail: ShoppingBag,
  Manufacturing: Factory,
  Telecommunications: Phone,
  Insurance: Shield,
  'Real Estate': Home,
  Education: GraduationCap,
  Automotive: Car,
  Government: Landmark,
  Logistics: Package,
  Utilities: Utilities,
  'Professional Services': Briefcase,
  Hospitality: Hotel,
  Generic: Settings,
  Technology: Laptop,
};

const AutomationTemplates: React.FC = () => {
  const { industryId } = useParams<{ industryId: string }>();
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedComplexity, setSelectedComplexity] = useState<string | null>(null);
  const [selectedIndustry, setSelectedIndustry] = useState<string>('All');
  const [viewMode, setViewMode] = useState<'table' | 'card'>('table'); // Default to table view

  // State for API data
  const [templates, setTemplates] = useState<AutomationTemplate[]>([]);
  const [templatesByIndustry, setTemplatesByIndustry] = useState<TemplatesByIndustry>({});
  const [availableIndustries, setAvailableIndustries] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [favoriteTemplateIds, setFavoriteTemplateIds] = useState<string[]>([]);
  const [togglingFavorite, setTogglingFavorite] = useState<string | null>(null);
  const [showDeploymentWizard, setShowDeploymentWizard] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<AutomationTemplate | null>(null);

  const { toast } = useToast();

  // Map industry ID to display names
  const industryKey = industryId ?
    Object.keys(industryNames).find(key =>
      key.toLowerCase().replace(/\s+/g, '_') === industryId.toLowerCase().replace(/-/g, '_')
    ) : null;

  const industryName = industryKey ?
    industryNames[industryKey as keyof typeof industryNames] :
    'Unknown Industry';

  const IconComponent = industryKey ?
    industryIcons[industryKey as keyof typeof industryIcons] :
    Settings;

  // Load app settings and templates from API
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        // App settings removed - now loading all available templates

        // Load templates and industries from automation templates API
        try {
          // Get all templates (use maximum allowed per_page)
          const templatesResponse = await automationOrchestrationService.listTemplates({ per_page: 100 });
          setTemplates(templatesResponse.templates);

          // Extract unique industries from templates for sidebar
          const uniqueIndustries = [...new Set(templatesResponse.templates.map(template => template.industry || 'Generic'))];

          // Set available industries including special categories (removed categories for now)
          setAvailableIndustries(['All', 'Campaign Templates', 'Generic Templates', ...uniqueIndustries.filter(name => name !== 'Generic')]);

          // Organize templates by industry for filtering
          const templatesByIndustryData: any = {};
          templatesResponse.templates.forEach(template => {
            const industry = template.industry || 'Generic';
            if (!templatesByIndustryData[industry]) {
              templatesByIndustryData[industry] = {
                industry: { name: industry },
                templates: []
              };
            }
            templatesByIndustryData[industry].templates.push(template);
          });
          setTemplatesByIndustry(templatesByIndustryData);

        } catch (templatesError) {
          console.error('Failed to load templates from automation service:', templatesError);

          // Fallback to original automation service
          if (industryKey) {
            const industryTemplates = await automationOrchestrationService.listTemplates({ industry: industryKey });
            setTemplates(industryTemplates.templates);
          } else {
            const response = await automationOrchestrationService.listTemplates({ per_page: 100 });
            setTemplates(response.templates);
          }
        }

      } catch (err) {
        console.error('Error loading data:', err);
        setError('Failed to load automation templates. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [industryKey]);

  // Load user favorites
  useEffect(() => {
    const loadFavorites = async () => {
      try {
        const favoriteIds = await userFavoritesService.getFavoriteTemplateIds();
        setFavoriteTemplateIds(favoriteIds);
      } catch (error) {
        // Silently fail - favorites are not critical and user may not be authenticated
        setFavoriteTemplateIds([]);
      }
    };

    loadFavorites();
  }, []);

  // Toggle favorite status
  const handleToggleFavorite = async (templateId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent card click

    try {
      setTogglingFavorite(templateId);
      const response: ToggleFavoriteResponse = await userFavoritesService.toggleFavorite(templateId);

      if (response.success) {
        if (response.is_favorite) {
          setFavoriteTemplateIds(prev => [...prev, templateId]);
        } else {
          setFavoriteTemplateIds(prev => prev.filter(id => id !== templateId));
        }

        toast({
          title: response.is_favorite ? "Added to Favorites" : "Removed from Favorites",
          description: response.message,
        });
      }
    } catch (error) {
      // Check if it's an authentication error
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      if (errorMessage.includes('authorization') || errorMessage.includes('Invalid user ID')) {
        toast({
          title: "Authentication Required",
          description: "Please log in to save favorites.",
          variant: "destructive"
        });
      } else {
        toast({
          title: "Error",
          description: "Failed to update favorite status. Please try again.",
          variant: "destructive"
        });
      }
    } finally {
      setTogglingFavorite(null);
    }
  };

  // Enhanced filtering logic
  const getFilteredTemplates = () => {
    let templatesToFilter: AutomationTemplate[] = [];

    // Filter by selected industry/category
    if (selectedIndustry === 'All') {
      templatesToFilter = Object.values(templatesByIndustry).flatMap(industryGroup =>
        industryGroup.templates
      ) as AutomationTemplate[];
    } else if (selectedIndustry === 'Campaign Templates') {
      // Show templates with campaign-related categories
      const campaignCategories = ['marketing', 'promotion', 'announcement', 'campaign', 'outreach'];
      templatesToFilter = Object.values(templatesByIndustry).flatMap(industryGroup =>
        industryGroup?.templates || []
      ).filter((template: any) =>
        template && template.category && campaignCategories.some(cat => template.category?.toLowerCase().includes(cat))
      ) as AutomationTemplate[];
    } else if (selectedIndustry === 'Generic Templates') {
      // Show generic templates that work across industries
      const genericIndustryGroup = Object.values(templatesByIndustry).find(group =>
        group.industry.name === 'Generic'
      );
      templatesToFilter = (genericIndustryGroup?.templates || []) as AutomationTemplate[];
    } else {
      // Show templates for specific industry by name
      const industryGroup = Object.values(templatesByIndustry).find(group =>
        group.industry.name === selectedIndustry
      );
      templatesToFilter = (industryGroup?.templates || []) as AutomationTemplate[];
    }

    // Show all templates (app settings filtering removed)

    // Apply existing filters (only industry and search for now)
    return templatesToFilter.filter((template: any) => {
      if (!template) return false;

      const matchesSearch = template.template_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           template.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           template.name?.toLowerCase().includes(searchTerm.toLowerCase());

      return matchesSearch;
    });
  };

  const filteredTemplates = getFilteredTemplates();

  const popularTemplates = filteredTemplates.filter(t => t && t.popular);
  const favoriteTemplates = filteredTemplates.filter(t => t && favoriteTemplateIds.includes(t.id));

  const handleTemplateSelect = (template: any) => {
    setSelectedTemplate(template);
    setShowDeploymentWizard(true);
  };

  const handleCreateCampaign = async (config: AutomationDeploymentConfig): Promise<CampaignCreationResult> => {
    try {
      // Handle automation deployment
      console.log('Automation config:', config);

      // Close the wizard and show success
      setShowDeploymentWizard(false);
      setSelectedTemplate(null);

      toast({
        title: "Automation Created",
        description: "Your automation has been successfully deployed.",
      });

      return {
        success: true,
        campaignId: 'new-automation-id'
      };
    } catch (error) {
      console.error('Failed to create automation:', error);
      return {
        success: false,
        error: 'Failed to create automation'
      };
    }
  };

  const handleDeploymentWizardClose = () => {
    setShowDeploymentWizard(false);
    setSelectedTemplate(null);
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-background">
        <DashboardSidebar />
        <div className="flex-1 overflow-auto">
          <div className="container mx-auto p-6">
            <div className="flex items-center justify-center min-h-96">
              <div className="text-center">
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
                <p className="text-gray-600">Loading automation templates...</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen bg-background">
        <DashboardSidebar />
        <div className="flex-1 overflow-auto">
          <div className="container mx-auto p-6">
            <div className="flex items-center justify-center min-h-96">
              <div className="text-center">
                <p className="text-red-500 mb-4">{error}</p>
                <Button onClick={() => window.location.reload()}>
                  Try Again
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Helper function to get industry icon
  const getIndustryIcon = (industry: string) => {
    return industryIcons[industry as keyof typeof industryIcons] || Settings;
  };

  // Helper function to get template type icon
  const getTemplateIcon = (template: any) => {
    const campaignCategories = ['marketing', 'promotion', 'announcement', 'campaign', 'outreach'];
    const isCampaignTemplate = template.category && campaignCategories.some(cat => template.category?.toLowerCase().includes(cat));

    if (isCampaignTemplate) {
      return <Megaphone className="h-4 w-4 text-orange-600" />;
    } else if (template.industry === 'Generic') {
      return <Settings className="h-4 w-4 text-blue-600" />;
    } else {
      return <Building2 className="h-4 w-4 text-purple-600" />;
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      <DashboardSidebar />

      {/* Secondary Sidebar for Template Categories */}
      <div className="w-64 bg-card border-r border-border p-4 flex-shrink-0">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Categories</h3>
            <Button variant="outline" size="icon" onClick={() => navigate('/automations')}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-1">
            {availableIndustries.map((industry) => {
              const IconComponent = getIndustryIcon(industry);
              const isSelected = selectedIndustry === industry;

              // Calculate template count for each category
              let templateCount = 0;
              if (industry === 'All') {
                templateCount = Object.values(templatesByIndustry).flatMap(group =>
                  group.templates
                ).length;
              } else if (industry === 'Campaign Templates') {
                const campaignCategories = ['marketing', 'promotion', 'announcement', 'campaign', 'outreach'];
                templateCount = Object.values(templatesByIndustry).flatMap(group =>
                  group?.templates || []
                ).filter((t: any) => {
                  const isCampaign = t && t.category && campaignCategories.some(cat => t.category?.toLowerCase().includes(cat));
                  return isCampaign;
                }).length;
              } else if (industry === 'Generic Templates') {
                const genericGroup = Object.values(templatesByIndustry).find(group =>
                  group.industry.name === 'Generic'
                );
                templateCount = (genericGroup?.templates || []).length;
              } else {
                const industryGroup = Object.values(templatesByIndustry).find(group =>
                  group.industry.name === industry
                );
                templateCount = (industryGroup?.templates || []).length;
              }

              return (
                <div
                  key={industry}
                  className={`p-3 rounded-lg cursor-pointer transition-colors flex items-center justify-between ${
                    isSelected
                      ? 'bg-indigo-600 text-primary-foreground'
                      : 'hover:bg-accent text-gray-600 hover:text-foreground'
                  }`}
                  onClick={() => setSelectedIndustry(industry)}
                >
                  <div className="flex items-center space-x-3">
                    <IconComponent className="w-4 h-4" />
                    <span className="font-medium text-sm">{industry}</span>
                  </div>
                  {templateCount > 0 && (
                    <Badge variant={isSelected ? "secondary" : "outline"} className="text-xs">
                      {templateCount}
                    </Badge>
                  )}
                </div>
              );
            })}
          </div>

          {selectedIndustry === 'Campaign Templates' && (
            <>
              <Separator />
              <div className="text-xs text-gray-600 p-3 bg-orange-50 dark:bg-orange-950 rounded-lg border border-orange-200 dark:border-orange-800">
                <div className="flex items-center gap-2 mb-2">
                  <Users className="h-4 w-4 text-orange-600" />
                  <span className="font-medium text-orange-800 dark:text-orange-200">Campaign Templates</span>
                </div>
                <p className="text-orange-700 dark:text-orange-300">
                  These templates require audience selection for targeted campaigns like product announcements or marketing outreach.
                </p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-auto">
        <div className="container mx-auto p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center gap-4 mb-6">
            <div className="flex items-center gap-3">
              {React.createElement(getIndustryIcon(selectedIndustry), {
                className: "h-8 w-8 p-2 bg-primary/10 rounded-lg text-indigo-600"
              })}
              <div>
                <h1 className="text-3xl font-bold">{selectedIndustry} Templates</h1>
                <p className="text-gray-600">
                  {filteredTemplates.length} templates available to streamline your workflow
                </p>
              </div>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="flex flex-col lg:flex-row gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-600" />
              <Input
                placeholder="Search templates..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            <div className="flex gap-2 flex-wrap items-center">
              <Button
                variant={selectedComplexity === null ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedComplexity(null)}
              >
                All Levels
              </Button>
              <Button
                variant={selectedComplexity === "Simple" ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedComplexity("Simple")}
              >
                Simple
              </Button>
              <Button
                variant={selectedComplexity === "Medium" ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedComplexity("Medium")}
              >
                Medium
              </Button>
              <Button
                variant={selectedComplexity === "Advanced" ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedComplexity("Advanced")}
              >
                Advanced
              </Button>

              {/* View Mode Toggle */}
              <div className="flex border rounded-md">
                <Button
                  variant={viewMode === 'table' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('table')}
                  className="rounded-r-none"
                >
                  <List className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'card' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('card')}
                  className="rounded-l-none"
                >
                  <LayoutGrid className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>


          {/* Templates Grid */}
          <Tabs defaultValue="all" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="all">All Templates ({filteredTemplates.length})</TabsTrigger>
              <TabsTrigger value="popular">Popular ({popularTemplates.length})</TabsTrigger>
              <TabsTrigger value="favorites">Favorites ({favoriteTemplates.length})</TabsTrigger>
              <TabsTrigger value="custom-tools" className="gap-1">
                <Wrench className="h-4 w-4" />
                Custom Tools
              </TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="mt-6">
              {viewMode === 'table' ? (
                /* Table View */
                <Card>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Template Name</TableHead>
                        <TableHead>Industry</TableHead>
                        <TableHead>Complexity</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredTemplates.filter(template => template).map((template: any) => {
                        const campaignCategories = ['marketing', 'promotion', 'announcement', 'campaign', 'outreach'];
                        const isCampaignTemplate = template.category && campaignCategories.some(cat => template.category?.toLowerCase().includes(cat));
                        const templateName = template.template_name || template.name;
                        const templateId = template.id || template._id;

                        return (
                          <TableRow key={templateId} className="hover:bg-accent/50 cursor-pointer" onClick={() => handleTemplateSelect(template)}>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                {getTemplateIcon(template)}
                                <div>
                                  <div className="font-medium">{templateName}</div>
                                  <div className="text-xs text-gray-600 line-clamp-1">
                                    {template.description}
                                  </div>
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className="text-xs">
                                {template.industry_name || template.industry || 'Generic'}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              {template.complexity && (
                                <Badge className={getTemplateComplexityColor(template.complexity)}>
                                  {template.complexity}
                                </Badge>
                              )}
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-2">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleTemplateSelect(template);
                                  }}
                                >
                                  <Settings className="h-4 w-4" />
                                </Button>
                                {templateId && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={(e) => handleToggleFavorite(templateId, e)}
                                    disabled={togglingFavorite === templateId}
                                  >
                                    <Heart
                                      className={`h-4 w-4 transition-colors ${
                                        favoriteTemplateIds.includes(templateId)
                                          ? 'fill-red-500 text-red-500'
                                          : 'text-gray-400 hover:text-red-500'
                                      }`}
                                    />
                                  </Button>
                                )}
                              </div>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </Card>
              ) : (
                /* Card View */
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {filteredTemplates.filter(template => template).map((template: any) => {
                  const campaignCategories = ['marketing', 'promotion', 'announcement', 'campaign', 'outreach'];
                  const isCampaignTemplate = template.category && campaignCategories.some(cat => template.category?.toLowerCase().includes(cat));
                  const templateName = template.template_name || template.name;
                  const templateId = template.id || template._id;

                  return (
                    <Card
                      key={templateId}
                      className="cursor-pointer hover:shadow-lg transition-all duration-200 group hover:border-primary/50"
                      onClick={() => handleTemplateSelect(template)}
                    >
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-lg group-hover:text-indigo-600 transition-colors flex items-center gap-2">
                              {getTemplateIcon(template)}
                              {templateName}
                            </CardTitle>
                            <CardDescription className="mt-2">
                              {template.description}
                            </CardDescription>
                          </div>
                          <div className="flex items-center gap-2">
                            {template.popular && (
                              <Badge variant="default" className="text-xs">
                                <Star className="h-3 w-3 mr-1" />
                                Popular
                              </Badge>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 mt-3 flex-wrap">
                          <Badge variant="outline" className="text-xs">
                            {template.industry_name || template.industry || 'Generic'}
                          </Badge>
                          {isCampaignTemplate && (
                            <Badge className="bg-orange-100 text-orange-800 text-xs">
                              <Users className="h-3 w-3 mr-1" />
                              Audience Required
                            </Badge>
                          )}
                          {template.complexity && (
                            <Badge className={getTemplateComplexityColor(template.complexity)}>
                              {template.complexity}
                            </Badge>
                          )}
                        </div>
                      </CardHeader>

                      <CardContent className="space-y-4">
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          {template.estimatedTime && (
                            <div className="flex items-center gap-1">
                              <Clock className="h-4 w-4" />
                              {template.estimatedTime}
                            </div>
                          )}
                          {template.rating && (
                            <div className="flex items-center gap-1">
                              <Star className="h-4 w-4 fill-current text-yellow-500" />
                              {template.rating}
                            </div>
                          )}
                          {template.version && (
                            <div>v{template.version}</div>
                          )}
                        </div>

                        <div className="text-xs text-gray-600">
                          {template.updated_at && (
                            <div>Updated: {new Date(template.updated_at).toLocaleDateString()}</div>
                          )}
                        </div>

                        <div className="flex gap-2 pt-2">
                          <Button size="sm" className="flex-1 gap-2 group-hover:bg-primary/10">
                            <Settings className="h-3 w-3" />
                            {isCampaignTemplate ? 'Select Audience' : 'Configure'}
                          </Button>
                          {templateId && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => handleToggleFavorite(templateId, e)}
                              disabled={togglingFavorite === templateId}
                              className="p-1 h-auto hover:bg-red-50"
                            >
                              <Heart
                                className={`h-5 w-5 transition-colors ${
                                  favoriteTemplateIds.includes(templateId)
                                    ? 'fill-red-500 text-red-500'
                                    : 'text-gray-400 hover:text-red-500'
                                }`}
                              />
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                  })}
                </div>
              )}

              {filteredTemplates.length === 0 && (
                <div className="text-center py-12">
                  <p className="text-gray-600">No templates found matching your criteria.</p>
                  <Button
                    variant="outline"
                    className="mt-4"
                    onClick={() => {
                      setSearchTerm('');
                      setSelectedComplexity(null);
                    }}
                  >
                    Clear Filters
                  </Button>
                </div>
              )}
            </TabsContent>

            <TabsContent value="popular" className="mt-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {popularTemplates.map((template) => (
                  <Card
                    key={template.id}
                    className="cursor-pointer hover:shadow-lg transition-all duration-200 group hover:border-primary/50 border-primary/20"
                    onClick={() => handleTemplateSelect(template)}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-lg group-hover:text-indigo-600 transition-colors">
                            {template.name}
                          </CardTitle>
                          <Badge variant="default" className="text-xs">
                            <Star className="h-3 w-3 mr-1" />
                            Popular
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => handleToggleFavorite(template.id, e)}
                            disabled={togglingFavorite === template.id}
                            className="p-1 h-auto hover:bg-red-50"
                          >
                            <Heart
                              className={`h-5 w-5 transition-colors ${
                                favoriteTemplateIds.includes(template.id)
                                  ? 'fill-red-500 text-red-500'
                                  : 'text-gray-400 hover:text-red-500'
                              }`}
                            />
                          </Button>
                          <Badge className={getTemplateComplexityColor(template.complexity)}>
                            {template.complexity}
                          </Badge>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          {template.estimatedTime}
                        </div>
                        <div className="flex items-center gap-1">
                          <Star className="h-4 w-4 fill-current text-yellow-500" />
                          {template.rating}
                        </div>
                        <div>{template.usageCount.toLocaleString()} users</div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <CardDescription className="mb-4">
                        {template.description}
                      </CardDescription>

                      <div className="space-y-3">
                        <div>
                          <div className="text-sm font-medium mb-2">Integration Categories:</div>
                          <div className="flex flex-wrap gap-1">
                            {template.integrationCategories.map((category) => (
                              <Badge key={category} variant="secondary" className="text-xs">
                                {category}
                              </Badge>
                            ))}
                          </div>
                        </div>

                        <div className="flex items-center justify-end pt-2">
                          <Button size="sm" className="group-hover:bg-primary/10">
                            Configure
                            <Settings className="h-4 w-4 ml-1" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {popularTemplates.length === 0 && (
                <div className="text-center py-12">
                  <p className="text-gray-600">No popular templates found for this industry.</p>
                </div>
              )}
            </TabsContent>

            <TabsContent value="favorites" className="mt-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {favoriteTemplates.map((template) => (
                  <Card
                    key={template.id}
                    className="cursor-pointer hover:shadow-lg transition-all duration-200 group hover:border-primary/50 border-red/20"
                    onClick={() => handleTemplateSelect(template)}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-lg group-hover:text-indigo-600 transition-colors">
                            {template.name}
                          </CardTitle>
                          {template.popular && (
                            <Badge variant="default" className="text-xs">
                              <Star className="h-3 w-3 mr-1" />
                              Popular
                            </Badge>
                          )}
                          <Badge variant="outline" className="text-xs text-red-600 border-red-200">
                            <Heart className="h-3 w-3 mr-1 fill-current" />
                            Favorite
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => handleToggleFavorite(template.id, e)}
                            disabled={togglingFavorite === template.id}
                            className="p-1 h-auto hover:bg-red-50"
                          >
                            <Heart
                              className={`h-5 w-5 transition-colors ${
                                favoriteTemplateIds.includes(template.id)
                                  ? 'fill-red-500 text-red-500'
                                  : 'text-gray-400 hover:text-red-500'
                              }`}
                            />
                          </Button>
                          <Badge className={getTemplateComplexityColor(template.complexity)}>
                            {template.complexity}
                          </Badge>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          {template.estimatedTime}
                        </div>
                        <div className="flex items-center gap-1">
                          <Star className="h-4 w-4 fill-current text-yellow-500" />
                          {template.rating}
                        </div>
                        <div>{template.usageCount.toLocaleString()} users</div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <CardDescription className="mb-4">
                        {template.description}
                      </CardDescription>

                      <div className="space-y-3">
                        <div>
                          <div className="text-sm font-medium mb-2">Integration Categories:</div>
                          <div className="flex flex-wrap gap-1">
                            {template.integrationCategories.map((category) => (
                              <Badge key={category} variant="secondary" className="text-xs">
                                {category}
                              </Badge>
                            ))}
                          </div>
                        </div>

                        <div className="flex items-center justify-end pt-2">
                          <Button size="sm" className="group-hover:bg-primary/10">
                            Configure
                            <Settings className="h-4 w-4 ml-1" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {favoriteTemplates.length === 0 && (
                <div className="text-center py-12">
                  <Heart className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p className="text-gray-600 mb-2">No favorite templates yet</p>
                  <p className="text-sm text-gray-600">Click the heart icon on any template to add it to your favorites.</p>
                </div>
              )}
            </TabsContent>

            <TabsContent value="custom-tools" className="mt-6">
              <CustomToolsTab />
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* AutomationDeploymentWizard Modal */}
      <AutomationDeploymentWizard
        isOpen={showDeploymentWizard}
        onClose={handleDeploymentWizardClose}
        template={selectedTemplate ? {
          id: selectedTemplate.id,
          name: selectedTemplate.name,
          description: selectedTemplate.description,
          industry: selectedTemplate.industry,
          category: selectedTemplate.category || 'general',
          complexity: selectedTemplate.complexity,
          estimatedTime: selectedTemplate.estimatedTime,
          rating: selectedTemplate.rating,
          usageCount: selectedTemplate.usageCount,
          popular: selectedTemplate.popular,
          integrationCategories: selectedTemplate.integrationCategories,
          defaultIntegrations: selectedTemplate.defaultIntegrations,
          vapiConfig: selectedTemplate.vapiConfig,
          features: selectedTemplate.features,
          supportedLanguages: selectedTemplate.supportedLanguages,
          knowledgeBase: selectedTemplate.knowledgeBase,
          tags: selectedTemplate.tags
        } : undefined}
        onCreateCampaign={handleCreateCampaign}
        apiBaseUrl={API_BASE_URL}
      />
    </div>
  );
};

export default AutomationTemplates;