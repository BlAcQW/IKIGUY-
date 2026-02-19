/**
 * Automation Deploy Page
 * Handles the deployment configuration step after template selection
 */

import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { AutomationDeploymentWizard } from '@/components/campaigns/AutomationDeploymentWizard';
import { type CampaignTemplate } from '@/pages/TemplateSelection';
import { type AutomationConfig } from '@/services/AutomationOrchestrationService';
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

const AutomationDeployPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const selectedTemplate = location.state?.selectedTemplate as CampaignTemplate;
  const existingConfig = location.state?.existingConfig as AutomationConfig;
  const isEditing = location.state?.isEditing as boolean;

  const [showWizard, setShowWizard] = useState(true);

  // If no template and not editing, redirect back to template selection
  React.useEffect(() => {
    if (!selectedTemplate && !existingConfig) {
      navigate('/automations/templates');
    }
  }, [selectedTemplate, existingConfig, navigate]);

  const handleCreateCampaign = async (config: AutomationDeploymentConfig): Promise<CampaignCreationResult> => {
    try {
      // Handle campaign creation logic here
      console.log('Creating campaign with config:', config);

      // For now, return a success response
      return {
        success: true,
        campaignId: 'new-campaign-id',
        demoUrl: config.demoSettings?.demoUrl
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to create campaign'
      };
    }
  };

  const handleWizardClose = () => {
    setShowWizard(false);
    navigate('/automations');
  };

  if (!selectedTemplate && !existingConfig) {
    return null; // Will redirect in useEffect
  }

  return (
    <div className="flex min-h-screen bg-background">
      <DashboardSidebar />

      <AutomationDeploymentWizard
        isOpen={showWizard}
        onClose={handleWizardClose}
        template={selectedTemplate}
        existingConfig={existingConfig}
        isEditing={isEditing}
        onCreateCampaign={handleCreateCampaign}
        apiBaseUrl={API_BASE_URL}
      />
    </div>
  );
};

export default AutomationDeployPage;