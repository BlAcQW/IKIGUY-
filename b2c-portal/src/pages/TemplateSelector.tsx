import React, { useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import TemplateSelectionPage, { type CampaignTemplate } from '@/pages/TemplateSelection';
import { AutomationDeploymentWizard } from '@/components/campaigns/AutomationDeploymentWizard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, Sparkles, Target, Zap } from 'lucide-react';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


interface TemplateSelectorProps {
  mode?: 'campaign' | 'automation';
}

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

const TemplateSelector: React.FC<TemplateSelectorProps> = ({ mode }) => {
  const navigate = useNavigate();
  const { industry } = useParams();
  const [searchParams] = useSearchParams();
  const currentMode = mode || searchParams.get('mode') || 'automation';
  const [showTemplateSelection, setShowTemplateSelection] = useState(true);
  const [showDeploymentWizard, setShowDeploymentWizard] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<CampaignTemplate | null>(null);

  const handleCreateCampaign = async (config: AutomationDeploymentConfig): Promise<CampaignCreationResult> => {
    // Handle campaign creation from AutomationDeploymentWizard
    console.log('Campaign created:', config);
    return {
      success: true,
      campaignId: 'new-campaign-id',
      demoUrl: config.demoSettings?.demoUrl
    };
  };

  const handleBack = () => {
    if (currentMode === 'campaign') {
      navigate('/campaigns');
    } else {
      navigate('/automations');
    }
  };

  const handleTemplateSelectionClose = () => {
    setShowTemplateSelection(false);
    handleBack();
  };

  const handleTemplateSelected = (template: CampaignTemplate) => {
    setSelectedTemplate(template);
    setShowTemplateSelection(false);
    setShowDeploymentWizard(true);
  };

  const handleDeploymentWizardClose = () => {
    setShowDeploymentWizard(false);
    handleBack();
  };

  const getPageTitle = () => {
    if (industry) {
      const industryName = industry.replace('_', ' ').replace('-', ' ');
      return `${industryName.charAt(0).toUpperCase() + industryName.slice(1)} Templates`;
    }
    return currentMode === 'campaign' ? 'Campaign Templates' : 'Automation Templates';
  };

  const getPageDescription = () => {
    if (industry) {
      const industryName = industry.replace('_', ' ').replace('-', ' ');
      return `Browse ${industryName} templates for your ${currentMode}`;
    }
    return currentMode === 'campaign'
      ? 'Select a template to create your campaign'
      : 'Select a template to create your automation workflow';
  };

  const getIcon = () => {
    return currentMode === 'campaign' ? <Target className="h-6 w-6" /> : <Zap className="h-6 w-6" />;
  };

  // Since we're now using a page instead of a modal, redirect to the page
  React.useEffect(() => {
    if (showTemplateSelection) {
      navigate(`/campaigns/templates${industry ? `/${industry}` : ''}`);
    }
  }, [showTemplateSelection, industry, navigate]);

  return (
    <>
      {/* Deployment Configuration Wizard */}
      {selectedTemplate && (
        <AutomationDeploymentWizard
          isOpen={showDeploymentWizard}
          onClose={handleDeploymentWizardClose}
          template={selectedTemplate}
          onCreateCampaign={handleCreateCampaign}
          apiBaseUrl={API_BASE_URL}
        />
      )}
    </>
  );
};

export default TemplateSelector;