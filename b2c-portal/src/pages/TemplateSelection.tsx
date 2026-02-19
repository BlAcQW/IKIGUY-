/**
 * Template Selection Page
 * Full page for searching and selecting automation templates
 * Converted from modal component to standalone page
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Search,
  Filter,
  Star,
  Clock,
  AlertCircle,
  CheckCircle,
  Loader2,
  FileText,
  Sparkles,
  ArrowLeft
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  automationTemplatesService,
  type AutomationTemplate as DatabaseTemplate
} from '@/services/AutomationTemplatesService';

// Template interface for the page
export interface CampaignTemplate {
  id: string;
  name: string;
  description: string;
  industry: string;
  category?: string;
  complexity?: string;
  estimatedTime?: string;
  rating?: number;
  usageCount?: number;
  popular?: boolean;
  isEnhanced?: boolean;
  integrationCategories?: string[];
  defaultIntegrations?: string[];
  vapiConfig?: any;
  n8nConfig?: any;
  features?: string[];
  supportedLanguages?: string[];
  knowledgeBase?: any[];
  tags?: string[];
}

// Adapter function to convert database template to campaign template
const adaptDatabaseTemplate = (dbTemplate: DatabaseTemplate): CampaignTemplate => {
  return {
    id: dbTemplate.id,
    name: dbTemplate.name,
    description: dbTemplate.description,
    industry: dbTemplate.industry,
    category: dbTemplate.category || 'general',
    complexity: dbTemplate.complexity || 'Medium',
    estimatedTime: dbTemplate.estimatedTime || '30 minutes',
    rating: dbTemplate.rating || 4.5,
    usageCount: dbTemplate.usageCount || 0,
    popular: dbTemplate.popular || false,
    isEnhanced: true,
    integrationCategories: dbTemplate.integrationCategories || [],
    defaultIntegrations: dbTemplate.defaultIntegrations || [],
    vapiConfig: dbTemplate.vapiConfig,
    n8nConfig: null, // DatabaseTemplate doesn't have n8nConfig
    features: dbTemplate.features || [],
    supportedLanguages: dbTemplate.supportedLanguages || ['en'],
    knowledgeBase: dbTemplate.knowledgeBase || [],
    tags: dbTemplate.tags || []
  };
};

interface TemplateSelectionPageProps {
  onTemplateSelected?: (template: CampaignTemplate) => void;
}

const TemplateSelectionPage: React.FC<TemplateSelectionPageProps> = ({
  onTemplateSelected
}) => {
  const navigate = useNavigate();
  const { industry } = useParams();
  const [searchParams] = useSearchParams();
  const [templates, setTemplates] = useState<CampaignTemplate[]>([]);
  const [filteredTemplates, setFilteredTemplates] = useState<CampaignTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<CampaignTemplate | null>(null);
  const [templatesLoading, setTemplatesLoading] = useState(true);
  const [templatesError, setTemplatesError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedIndustry, setSelectedIndustry] = useState<string>(industry || 'all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const { toast } = useToast();

  // Load templates from API
  useEffect(() => {
    const loadTemplates = async () => {
      try {
        setTemplatesLoading(true);
        setTemplatesError(null);

        let response;
        if (industry) {
          response = await automationTemplatesService.getTemplatesByIndustry(industry);
          const adaptedTemplates = response.map(adaptDatabaseTemplate);
          setTemplates(adaptedTemplates);
        } else {
          response = await automationTemplatesService.listTemplates();
          const adaptedTemplates = response.templates.map(adaptDatabaseTemplate);
          setTemplates(adaptedTemplates);
        }
      } catch (error) {
        console.error('Error loading templates:', error);
        setTemplatesError('Failed to load automation templates. Please try again.');
      } finally {
        setTemplatesLoading(false);
      }
    };

    loadTemplates();
  }, [industry]);

  // Filter templates based on search and filters
  useEffect(() => {
    let filtered = templates;

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(template =>
        template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        template.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        template.industry.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (template.category || '').toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Industry filter
    if (selectedIndustry !== 'all') {
      filtered = filtered.filter(template =>
        template.industry.toLowerCase() === selectedIndustry.toLowerCase()
      );
    }

    // Category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(template =>
        (template.category || 'general').toLowerCase() === selectedCategory.toLowerCase()
      );
    }

    setFilteredTemplates(filtered);
  }, [templates, searchTerm, selectedIndustry, selectedCategory]);

  const handleTemplateSelect = (template: CampaignTemplate) => {
    setSelectedTemplate(template);
  };

  const handleConfirmSelection = (template?: CampaignTemplate) => {
    const templateToUse = template || selectedTemplate;
    if (templateToUse) {
      if (onTemplateSelected) {
        onTemplateSelected(templateToUse);
      }
      // Navigate to deployment configuration with the selected template
      navigate('/campaigns/deploy', {
        state: { selectedTemplate: templateToUse }
      });
    } else {
      toast({
        title: "No Template Selected",
        description: "Please select a template to continue.",
        variant: "destructive"
      });
    }
  };

  const handleBack = () => {
    navigate('/campaigns');
  };

  const getUniqueIndustries = () => {
    const industries = [...new Set(templates.map(t => t.industry))];
    return industries.sort();
  };

  const getUniqueCategories = () => {
    const categories = [...new Set(templates.map(t => t.category || 'general'))];
    return categories.sort();
  };

  return (
    <div className="flex min-h-screen bg-background">
      <DashboardSidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="border-b bg-background p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleBack}
                className="gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </Button>

              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <FileText className="h-5 w-5 text-indigo-600" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold">Select Automation Template</h1>
                  <p className="text-gray-600">
                    Choose a template to configure your automation campaign
                  </p>
                </div>
              </div>
            </div>

            {selectedTemplate && (
              <Badge variant="default" className="flex items-center gap-1">
                <CheckCircle className="h-3 w-3" />
                Selected: {selectedTemplate.name}
              </Badge>
            )}
          </div>
        </div>

        {/* Search and Filters */}
        <div className="p-6 border-b">
          <div className="flex gap-4">
            <div className="flex-1">
              <Label htmlFor="search">Search Templates</Label>
              <div className="relative mt-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-600" />
                <Input
                  id="search"
                  placeholder="Search by name, description, industry..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <div className="w-48">
              <Label htmlFor="industry">Industry</Label>
              <select
                id="industry"
                value={selectedIndustry}
                onChange={(e) => setSelectedIndustry(e.target.value)}
                className="w-full mt-1 p-2 border rounded-md"
              >
                <option value="all">All Industries</option>
                {getUniqueIndustries().map(industry => (
                  <option key={industry} value={industry}>{industry}</option>
                ))}
              </select>
            </div>

            <div className="w-48">
              <Label htmlFor="category">Category</Label>
              <select
                id="category"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full mt-1 p-2 border rounded-md"
              >
                <option value="all">All Categories</option>
                {getUniqueCategories().map(category => (
                  <option key={category} value={category}>
                    {category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Templates List */}
        <div className="flex-1 overflow-y-auto p-6">
          {templatesLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin mr-2" />
              <span>Loading templates...</span>
            </div>
          )}

          {templatesError && (
            <div className="text-center py-12">
              <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Failed to load templates</h3>
              <p className="text-gray-600">{templatesError}</p>
            </div>
          )}

          {!templatesLoading && !templatesError && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">
                  {filteredTemplates.length} template{filteredTemplates.length !== 1 ? 's' : ''} found
                </h3>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                {filteredTemplates.map((template) => (
                  <Card
                    key={template.id}
                    className={`transition-all duration-200 ${
                      selectedTemplate?.id === template.id
                        ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                        : 'hover:border-primary/50'
                    }`}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-lg">{template.name}</CardTitle>
                          {template.popular && (
                            <Badge variant="default" className="text-xs">
                              <Star className="h-3 w-3 mr-1" />
                              Popular
                            </Badge>
                          )}
                        </div>
                        <Badge variant="outline">{template.complexity}</Badge>
                      </div>
                      <CardDescription className="text-sm">{template.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            {template.estimatedTime}
                          </div>
                          <div className="flex items-center gap-1">
                            <Star className="h-4 w-4 fill-current text-yellow-500" />
                            {template.rating}
                          </div>
                        </div>
                        <div>
                          <div className="text-sm font-medium mb-1">Industry:</div>
                          <Badge variant="secondary" className="text-xs">{template.industry}</Badge>
                        </div>
                        <div>
                          <div className="text-sm font-medium mb-1">Category:</div>
                          <Badge variant="outline" className="text-xs">
                            {(template.category || 'general').replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </Badge>
                        </div>
                        <div>
                          <div className="text-sm font-medium mb-1">Features:</div>
                          <div className="flex flex-wrap gap-1">
                            {template.features?.slice(0, 3).map((feature) => (
                              <Badge key={feature} variant="outline" className="text-xs">
                                {feature}
                              </Badge>
                            ))}
                            {template.features && template.features.length > 3 && (
                              <Badge variant="outline" className="text-xs">
                                +{template.features.length - 3} more
                              </Badge>
                            )}
                          </div>
                        </div>

                        {/* Select Button */}
                        <div className="pt-4 border-t">
                          <Button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleConfirmSelection(template);
                            }}
                            variant={selectedTemplate?.id === template.id ? "default" : "outline"}
                            className="w-full flex items-center gap-2"
                          >
                            {selectedTemplate?.id === template.id ? (
                              <>
                                <CheckCircle className="h-4 w-4" />
                                Selected - Configure Now
                              </>
                            ) : (
                              <>
                                <Sparkles className="h-4 w-4" />
                                Select Template
                              </>
                            )}
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {filteredTemplates.length === 0 && (
                <div className="text-center py-12">
                  <Search className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No templates found</h3>
                  <p className="text-gray-600">Try adjusting your search criteria or filters.</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t p-6 bg-background">
          <div className="flex justify-between">
            <Button variant="outline" onClick={handleBack}>
              Cancel
            </Button>

            <Button
              onClick={handleConfirmSelection}
              disabled={!selectedTemplate}
              className="flex items-center gap-2"
            >
              <Sparkles className="h-4 w-4" />
              Configure Selected Template
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TemplateSelectionPage;