import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { templateManagementService, AutomationTemplate } from '@/services/TemplateManagementService';
import {
  ArrowLeft,
  FileText,
  Sparkles,
  Users,
  TrendingUp,
  Phone,
  Mail,
  Calendar,
  DollarSign,
  Settings,
  HeadphonesIcon,
  Loader2
} from 'lucide-react';

// Using AutomationTemplate interface from TemplateManagementService
export type CampaignTemplate = AutomationTemplate;

const categoryIcons = {
  // Unified template categories
  sales: TrendingUp,
  marketing: Sparkles,
  support: HeadphonesIcon,
  survey: FileText,
  follow_up: Mail,
  retention: Users,
  scheduling: Calendar,
  // Database template categories
  helpdesk: HeadphonesIcon,
  customer_service: HeadphonesIcon,
  appointment_booking: Calendar,
  lead_generation: TrendingUp,
  provider_locator: Users,
  claims_processing: FileText
};

const difficultyColors = {
  beginner: 'bg-green-100 text-green-800 border-green-200',
  intermediate: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  advanced: 'bg-red-100 text-red-800 border-red-200'
};

const SelectTemplate: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedTemplate, setSelectedTemplate] = useState<CampaignTemplate | null>(null);
  const [templates, setTemplates] = useState<CampaignTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        setLoading(true);
        setError(null);
        // Fetch templates for campaign page (Generic industry)
        const fetchedTemplates = await templateManagementService.getTemplatesForCampaignPage();
        setTemplates(fetchedTemplates);
      } catch (err) {
        console.error('Error fetching templates:', err);
        setError('Failed to load templates. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchTemplates();
  }, []);

  const categories = ['all', ...Array.from(new Set(templates.map(t => t.category || 'general')))];

  const filteredTemplates = selectedCategory === 'all'
    ? templates
    : templates.filter(t => (t.category || 'general') === selectedCategory);

  const handleTemplateSelect = (template: CampaignTemplate) => {
    setSelectedTemplate(template);
  };

  const handleUseTemplate = () => {
    if (selectedTemplate) {
      // Navigate to campaign creation with template data
      navigate('/campaigns/create', { 
        state: { selectedTemplate } 
      });
    }
  };

  const handleSkipTemplate = () => {
    // Navigate to campaign creation without template
    navigate('/campaigns/create');
  };

  const getCategoryIcon = (category: string) => {
    const IconComponent = categoryIcons[category as keyof typeof categoryIcons] || Settings;
    return <IconComponent className="h-5 w-5" />;
  };

  return (
    <div className="flex min-h-screen bg-background">
      <DashboardSidebar />

      <div className="flex-1 overflow-auto">
        <div className="container mx-auto p-6 pb-12 max-w-7xl">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate('/campaigns')}
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <h1 className="text-3xl font-bold text-foreground mb-2">Choose a Template</h1>
                <p className="text-gray-600">
                  Start with a proven template or create a custom campaign from scratch
                </p>
              </div>
            </div>
            
            <Button 
              variant="outline" 
              onClick={handleSkipTemplate}
              className="gap-2"
            >
              <Settings className="h-4 w-4" />
              Create Custom
            </Button>
          </div>

          {/* Category Filter */}
          <div className="flex gap-2 mb-6 overflow-x-auto">
            {categories.map(category => (
              <Button
                key={category}
                variant={selectedCategory === category ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedCategory(category)}
                className="gap-2 whitespace-nowrap"
              >
                {category !== 'all' && getCategoryIcon(category)}
                {category === 'all' ? 'All Templates' : category}
              </Button>
            ))}
          </div>

          {/* Loading State */}
          {loading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
              <span className="ml-2 text-lg">Loading templates...</span>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="text-center py-12">
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={() => window.location.reload()}>
                Try Again
              </Button>
            </div>
          )}

          {/* Templates Grid */}
          {!loading && !error && (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {filteredTemplates.map((template) => (
              <Card 
                key={template.id} 
                className={`cursor-pointer transition-all hover:shadow-lg ${
                  selectedTemplate?.id === template.id 
                    ? 'ring-2 ring-primary border-primary' 
                    : ''
                }`}
                onClick={() => handleTemplateSelect(template)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getCategoryIcon(template.category || 'general')}
                      <Badge variant="outline">{template.category || 'general'}</Badge>
                    </div>
                    <Badge className={difficultyColors[template.difficulty]}>
                      {template.difficulty}
                    </Badge>
                  </div>
                  
                  <CardTitle className="text-lg">{template.template_name}</CardTitle>
                  <CardDescription className="text-sm">
                    {template.description}
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div>
                    <p className="text-sm font-medium mb-2">Key Features:</p>
                    <div className="flex flex-wrap gap-1">
                      {template.features.slice(0, 3).map((feature, index) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {feature}
                        </Badge>
                      ))}
                      {template.features.length > 3 && (
                        <Badge variant="secondary" className="text-xs">
                          +{template.features.length - 3} more
                        </Badge>
                      )}
                    </div>
                  </div>

                  <div className="text-sm text-gray-600">
                    <strong>Company:</strong> {template.company_name}
                  </div>

                  {selectedTemplate?.id === template.id && (
                    <div className="pt-2 border-t">
                      <p className="text-sm">
                        <strong>System Prompt:</strong> {template.system_prompt.slice(0, 200)}...
                      </p>
                      <p className="text-sm mt-2">
                        <strong>Integrations:</strong> {template.integrations.map(i => i.name).join(', ')}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
            </div>
          )}

          {/* Action Buttons */}
          {selectedTemplate && (
            <div className="fixed bottom-6 right-6 flex gap-3">
              <Button 
                variant="outline" 
                onClick={() => setSelectedTemplate(null)}
              >
                Deselect
              </Button>
              <Button onClick={handleUseTemplate} className="gap-2">
                <FileText className="h-4 w-4" />
                Use This Template
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SelectTemplate;