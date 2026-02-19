/**
 * Tests for the category property undefined fix
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AutomationDeploymentWizard } from '@/components/campaigns/AutomationDeploymentWizard';

// Mock the required dependencies
const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: mockToast })
}));

// Mock other services and components
vi.mock('@/services/AutomationOrchestrationService');
vi.mock('@/components/shared/SystemPromptGenerator');
vi.mock('@/components/automation/CustomToolsTab');
vi.mock('@/components/automation/IndustryConfigHandler');
vi.mock('@/components/analytics/AutomationAnalyticsDashboard');
vi.mock('@/components/automation/CustomToolsSelector');

describe('Category Property Undefined Fix', () => {
  it('should handle template with undefined category property', () => {
    // Template with missing category property
    const templateWithoutCategory = {
      id: 'test-template',
      name: 'Test Template',
      description: 'Test template without category',
      industry: 'Test Industry',
      // category is intentionally undefined
      complexity: 'Medium',
      estimatedTime: '30 minutes',
      rating: 4.5,
      usageCount: 0,
      popular: false,
      isEnhanced: true,
      integrationCategories: [],
      defaultIntegrations: [],
      vapiConfig: null,
      n8nConfig: null,
      features: [],
      supportedLanguages: ['en'],
      knowledgeBase: [],
      tags: []
    };

    // This should not throw an error
    expect(() => {
      render(
        <AutomationDeploymentWizard
          template={templateWithoutCategory}
          isOpen={true}
          onClose={() => {}}
          onDeploy={() => {}}
        />
      );
    }).not.toThrow();
  });

  it('should display "general" as default category when category is undefined', () => {
    const templateWithoutCategory = {
      id: 'test-template',
      name: 'Test Template',
      description: 'Test template without category',
      industry: 'Test Industry',
      // category is intentionally undefined
      complexity: 'Medium',
      estimatedTime: '30 minutes',
      rating: 4.5,
      usageCount: 0,
      popular: false,
      isEnhanced: true,
      integrationCategories: [],
      defaultIntegrations: [],
      vapiConfig: null,
      n8nConfig: null,
      features: [],
      supportedLanguages: ['en'],
      knowledgeBase: [],
      tags: []
    };

    render(
      <AutomationDeploymentWizard
        template={templateWithoutCategory}
        isOpen={true}
        onClose={() => {}}
        onDeploy={() => {}}
      />
    );

    // Should find "general" as the fallback category
    expect(screen.getByText('general')).toBeInTheDocument();
  });

  it('should handle template with valid category property', () => {
    const templateWithCategory = {
      id: 'test-template',
      name: 'Test Template',
      description: 'Test template with category',
      industry: 'Test Industry',
      category: 'sales',
      complexity: 'Medium',
      estimatedTime: '30 minutes',
      rating: 4.5,
      usageCount: 0,
      popular: false,
      isEnhanced: true,
      integrationCategories: [],
      defaultIntegrations: [],
      vapiConfig: null,
      n8nConfig: null,
      features: [],
      supportedLanguages: ['en'],
      knowledgeBase: [],
      tags: []
    };

    render(
      <AutomationDeploymentWizard
        template={templateWithCategory}
        isOpen={true}
        onClose={() => {}}
        onDeploy={() => {}}
      />
    );

    // Should find the actual category
    expect(screen.getByText('sales')).toBeInTheDocument();
  });
});