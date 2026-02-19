/**
 * Template Management Component
 * Displays and manages automation templates for Campaign and Automation pages
 */

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Search,
  Plus,
  RefreshCw,
  Filter,
  Download,
  Upload,
  Settings,
} from 'lucide-react';
import TemplateCard from './TemplateCard';
import {
  AutomationTemplate,
  templateManagementService,
  TemplateUpdateRequest,
} from '../../services/TemplateManagementService';
import { useToast } from '@/hooks/use-toast';

interface TemplateManagementProps {
  pageType?: 'campaign' | 'automation' | 'all';
  showManagementActions?: boolean;
  onTemplateSelect?: (template: AutomationTemplate) => void;
  mode?: 'management' | 'selection';
  industry?: string;
}

const TemplateManagement: React.FC<TemplateManagementProps> = ({
  pageType = 'all',
  showManagementActions = true,
  onTemplateSelect,
  mode = 'management',
  industry,
}) => {
  const [templates, setTemplates] = useState<AutomationTemplate[]>([]);
  const [filteredTemplates, setFilteredTemplates] = useState<AutomationTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedIndustry, setSelectedIndustry] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const { toast } = useToast();

  // Load templates on component mount
  useEffect(() => {
    loadTemplates();
  }, [pageType]);

  // Filter templates when search/filter criteria change
  useEffect(() => {
    filterTemplates();
  }, [templates, searchTerm, selectedIndustry, selectedCategory]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      let templates: AutomationTemplate[];

      switch (pageType) {
        case 'campaign':
          templates = await templateManagementService.getTemplatesForCampaignPage();
          break;
        case 'automation':
          templates = await templateManagementService.getTemplatesForAutomationPage();
          break;
        default:
          templates = await templateManagementService.listTemplates();
      }

      setTemplates(templates);
    } catch (error) {
      console.error('Failed to load templates:', error);
      toast({
        title: "Error",
        description: "Failed to load templates. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const filterTemplates = () => {
    let filtered = templates;

    // Filter by industry prop if provided (from URL)
    if (industry) {
      const industryName = industry.replace('_', ' ').replace('-', ' ');
      filtered = filtered.filter(template =>
        template.industry.toLowerCase() === industryName.toLowerCase() ||
        template.industry.toLowerCase() === industry.toLowerCase()
      );
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(template =>
        template.template_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        template.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        template.company_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by industry selector
    if (selectedIndustry !== 'all') {
      filtered = filtered.filter(template => template.industry === selectedIndustry);
    }

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(template => (template.category || 'general') === selectedCategory);
    }

    setFilteredTemplates(filtered);
  };

  const handleEditTemplate = (template: AutomationTemplate) => {
    // In a real implementation, this would open an edit modal
    console.log('Edit template:', template);
    toast({
      title: "Edit Template",
      description: `Opening editor for ${template.template_name}`,
    });
  };

  const handleDeleteTemplate = async (templateId: string) => {
    try {
      await templateManagementService.deleteTemplate(templateId);
      await loadTemplates(); // Reload templates
      toast({
        title: "Template Deleted",
        description: "Template has been deleted successfully.",
      });
    } catch (error) {
      console.error('Failed to delete template:', error);
      toast({
        title: "Error",
        description: "Failed to delete template. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleDeployTemplate = (template: AutomationTemplate) => {
    // In a real implementation, this would start the deployment process
    console.log('Deploy template:', template);
    toast({
      title: "Deployment Started",
      description: `${template.template_name} deployment is in progress...`,
    });
  };

  const handlePopulateDefaults = async () => {
    try {
      setLoading(true);
      await templateManagementService.populateDefaultTemplates();
      await loadTemplates();
      toast({
        title: "Templates Populated",
        description: "Default templates have been added successfully.",
      });
    } catch (error) {
      console.error('Failed to populate templates:', error);
      toast({
        title: "Error",
        description: "Failed to populate default templates.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const getUniqueIndustries = () => {
    const industries = [...new Set(templates.map(t => t.industry))];
    return industries.sort();
  };

  const getUniqueCategories = () => {
    const categories = [...new Set(templates.map(t => t.category || 'general'))];
    return categories.sort();
  };

  const getPageTitle = () => {
    switch (pageType) {
      case 'campaign': return 'Campaign Templates';
      case 'automation': return 'Automation Templates';
      default: return 'All Templates';
    }
  };

  const getPageDescription = () => {
    switch (pageType) {
      case 'campaign': return 'Generic templates suitable for general campaigns';
      case 'automation': return 'Industry-specific automation templates';
      default: return 'Manage all automation templates';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{getPageTitle()}</h2>
          <p className="text-gray-600">{getPageDescription()}</p>
        </div>

        {showManagementActions && (
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={loadTemplates} disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="outline" onClick={handlePopulateDefaults}>
              <Download className="h-4 w-4 mr-2" />
              Populate Defaults
            </Button>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Template
            </Button>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search templates..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        <Select value={selectedIndustry} onValueChange={setSelectedIndustry}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="All Industries" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Industries</SelectItem>
            {getUniqueIndustries().map(industry => (
              <SelectItem key={industry} value={industry}>
                {industry}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {getUniqueCategories().map(category => (
              <SelectItem key={category} value={category}>
                {category.replace('_', ' ')}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Templates Grid */}
      <div className="space-y-4">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-64 bg-gray-200 animate-pulse rounded-lg" />
            ))}
          </div>
        ) : filteredTemplates.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 text-lg mb-2">No templates found</div>
            <p className="text-gray-600 mb-4">
              {templates.length === 0
                ? "No templates have been created yet."
                : "Try adjusting your search or filter criteria."
              }
            </p>
            {templates.length === 0 && showManagementActions && (
              <Button onClick={handlePopulateDefaults}>
                <Download className="h-4 w-4 mr-2" />
                Populate Default Templates
              </Button>
            )}
          </div>
        ) : (
          <>
            {/* Summary */}
            <div className="text-sm text-gray-600 mb-4">
              Showing {filteredTemplates.length} of {templates.length} templates
            </div>

            {/* Templates Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredTemplates.map(template => (
                <TemplateCard
                  key={template.id}
                  template={template}
                  onEdit={handleEditTemplate}
                  onDelete={handleDeleteTemplate}
                  onDeploy={handleDeployTemplate}
                  onSelect={onTemplateSelect}
                  showActions={showManagementActions}
                  mode={mode}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default TemplateManagement;