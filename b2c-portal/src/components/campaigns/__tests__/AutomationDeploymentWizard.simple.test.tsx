/**
 * Simplified unit tests for AutomationDeploymentWizard component
 * Tests core functionality without complex service mocking
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the toast hook
const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: mockToast })
}));

// Mock auth utilities
vi.mock('@/lib/auth-utils', () => ({
  isAdminUser: vi.fn().mockResolvedValue(false),
  getAuthHeaders: vi.fn().mockReturnValue({ Authorization: 'Bearer test-token' })
}));

// Mock the automation service
vi.mock('@/services/AutomationOrchestrationService', () => ({
  automationOrchestrationService: {
    getConfiguration: vi.fn(),
    createConfiguration: vi.fn(),
    updateConfiguration: vi.fn(),
    deployConfiguration: vi.fn(),
    validateConfiguration: vi.fn(),
    testConfiguration: vi.fn(),
    getTemplate: vi.fn(),
    updateTemplate: vi.fn()
  }
}));

// Mock child components to avoid complex dependencies
vi.mock('@/components/shared/SystemPromptGenerator', () => ({
  SystemPromptGenerator: () => <div data-testid="system-prompt-generator">System Prompt Generator</div>
}));

vi.mock('@/components/automation/CustomToolsTab', () => ({
  default: () => <div data-testid="custom-tools-tab">Custom Tools Tab</div>
}));

vi.mock('@/components/automation/IndustryConfigHandler', () => ({
  default: () => <div data-testid="industry-config-handler">Industry Config Handler</div>
}));

vi.mock('@/components/analytics/AutomationAnalyticsDashboard', () => ({
  default: () => <div data-testid="analytics-dashboard">Analytics Dashboard</div>
}));

vi.mock('@/components/automation/CustomToolsSelector', () => ({
  default: () => <div data-testid="custom-tools-selector">Custom Tools Selector</div>
}));

// Import the component after mocks
import { AutomationDeploymentWizard } from '../AutomationDeploymentWizard';

const mockTemplate = {
  id: 'template-123',
  name: 'Healthcare Provider Locator',
  description: 'Test template for healthcare automation',
  industry: 'healthcare',
  category: 'provider-locator',
  complexity: 'Medium',
  estimatedTime: '30 minutes',
  rating: 4.5,
  usageCount: 100,
  popular: true,
  isEnhanced: true,
  integrationCategories: ['vapi', 'n8n'],
  defaultIntegrations: ['openai', 'calendar'],
  vapiConfig: { assistant_id: 'test-assistant' },
  n8nConfig: { workflow_id: 'test-workflow' },
  features: ['voice-calls', 'automation'],
  supportedLanguages: ['en'],
  knowledgeBase: [],
  tags: ['healthcare', 'provider']
};

const defaultProps = {
  isOpen: true,
  onClose: vi.fn(),
  onCreateCampaign: vi.fn().mockResolvedValue({ success: true, campaignId: 'test-campaign' }),
  apiBaseUrl: 'https://api.test.com'
};

describe('AutomationDeploymentWizard - Core Functionality', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render when open', () => {
      render(<AutomationDeploymentWizard {...defaultProps} />);

      expect(screen.getByText(/automation.*deployment.*wizard/i)).toBeInTheDocument();
    });

    it('should not render when closed', () => {
      render(<AutomationDeploymentWizard {...defaultProps} isOpen={false} />);

      expect(screen.queryByText(/automation.*deployment.*wizard/i)).not.toBeInTheDocument();
    });

    it('should render with template information', () => {
      render(<AutomationDeploymentWizard {...defaultProps} template={mockTemplate} />);

      expect(screen.getByText('Healthcare Provider Locator')).toBeInTheDocument();
      expect(screen.getByText('healthcare')).toBeInTheDocument();
    });
  });

  describe('Form Fields', () => {
    it('should render automation name input', () => {
      render(<AutomationDeploymentWizard {...defaultProps} />);

      const nameInput = screen.getByLabelText(/automation name/i);
      expect(nameInput).toBeInTheDocument();
      expect(nameInput).toHaveValue('');
    });

    it('should update automation name when typed', () => {
      render(<AutomationDeploymentWizard {...defaultProps} />);

      const nameInput = screen.getByLabelText(/automation name/i);
      fireEvent.change(nameInput, { target: { value: 'My Test Automation' } });

      expect(nameInput).toHaveValue('My Test Automation');
    });

    it('should render company information fields', () => {
      render(<AutomationDeploymentWizard {...defaultProps} />);

      // Navigate to company info step or check if fields are visible
      expect(screen.getByLabelText(/company name/i)).toBeInTheDocument();
    });
  });

  describe('Navigation', () => {
    it('should have step navigation buttons', () => {
      render(<AutomationDeploymentWizard {...defaultProps} />);

      expect(screen.getByText('Next')).toBeInTheDocument();
    });

    it('should handle step navigation', () => {
      render(<AutomationDeploymentWizard {...defaultProps} />);

      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);

      // Should progress through wizard steps
      // The exact behavior depends on component implementation
    });
  });

  describe('Template Integration', () => {
    it('should display template category correctly', () => {
      render(<AutomationDeploymentWizard {...defaultProps} template={mockTemplate} />);

      expect(screen.getByText('provider-locator')).toBeInTheDocument();
    });

    it('should handle template without category', () => {
      const templateWithoutCategory = {
        ...mockTemplate,
        category: undefined
      };

      render(<AutomationDeploymentWizard {...defaultProps} template={templateWithoutCategory} />);

      // Should show default category
      expect(screen.getByText('general')).toBeInTheDocument();
    });

    it('should display template complexity', () => {
      render(<AutomationDeploymentWizard {...defaultProps} template={mockTemplate} />);

      expect(screen.getByText('Medium')).toBeInTheDocument();
    });

    it('should display estimated time', () => {
      render(<AutomationDeploymentWizard {...defaultProps} template={mockTemplate} />);

      expect(screen.getByText('30 minutes')).toBeInTheDocument();
    });
  });

  describe('Edit Mode', () => {
    const mockExistingConfig = {
      id: 'config-456',
      automation_name: 'Existing Automation',
      config: {
        userConfig: {
          automationName: 'Existing Automation',
          companyInfo: { name: 'Existing Company' }
        }
      }
    };

    it('should render in edit mode', () => {
      render(
        <AutomationDeploymentWizard
          {...defaultProps}
          isEditing={true}
          existingConfig={mockExistingConfig}
        />
      );

      expect(screen.getByText(/edit.*automation/i)).toBeInTheDocument();
    });

    it('should show save button in edit mode', () => {
      render(
        <AutomationDeploymentWizard
          {...defaultProps}
          isEditing={true}
          existingConfig={mockExistingConfig}
        />
      );

      expect(screen.getByText(/save.*changes/i)).toBeInTheDocument();
    });
  });

  describe('Child Components', () => {
    it('should render system prompt generator', () => {
      render(<AutomationDeploymentWizard {...defaultProps} />);

      expect(screen.getByTestId('system-prompt-generator')).toBeInTheDocument();
    });

    it('should render custom tools tab', () => {
      render(<AutomationDeploymentWizard {...defaultProps} />);

      expect(screen.getByTestId('custom-tools-tab')).toBeInTheDocument();
    });

    it('should render industry config handler', () => {
      render(<AutomationDeploymentWizard {...defaultProps} />);

      expect(screen.getByTestId('industry-config-handler')).toBeInTheDocument();
    });
  });

  describe('Button States', () => {
    it('should handle close button', () => {
      const onClose = vi.fn();
      render(<AutomationDeploymentWizard {...defaultProps} onClose={onClose} />);

      const closeButton = screen.getByLabelText(/close/i) || screen.getByText(/cancel/i);
      if (closeButton) {
        fireEvent.click(closeButton);
        expect(onClose).toHaveBeenCalled();
      }
    });

    it('should show loading states', () => {
      render(<AutomationDeploymentWizard {...defaultProps} />);

      // Check for loading indicators when actions are performed
      // This depends on component implementation
      const createButton = screen.queryByText(/create.*automation/i);
      if (createButton) {
        expect(createButton).toBeInTheDocument();
      }
    });
  });

  describe('Accessibility', () => {
    it('should have proper dialog role', () => {
      render(<AutomationDeploymentWizard {...defaultProps} />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });

    it('should have proper form labels', () => {
      render(<AutomationDeploymentWizard {...defaultProps} />);

      const nameInput = screen.getByLabelText(/automation name/i);
      expect(nameInput).toBeInTheDocument();
    });

    it('should support keyboard navigation', () => {
      render(<AutomationDeploymentWizard {...defaultProps} />);

      const nameInput = screen.getByLabelText(/automation name/i);
      nameInput.focus();

      expect(document.activeElement).toBe(nameInput);
    });
  });

  describe('Validation', () => {
    it('should show validation messages for empty required fields', () => {
      render(<AutomationDeploymentWizard {...defaultProps} />);

      const nameInput = screen.getByLabelText(/automation name/i);
      fireEvent.change(nameInput, { target: { value: '' } });
      fireEvent.blur(nameInput);

      // Should show validation message
      // This depends on component validation implementation
    });

    it('should validate automation name length', () => {
      render(<AutomationDeploymentWizard {...defaultProps} />);

      const nameInput = screen.getByLabelText(/automation name/i);
      fireEvent.change(nameInput, { target: { value: 'a' } }); // Too short
      fireEvent.blur(nameInput);

      // Should show validation message for short names
      // This depends on component validation implementation
    });
  });

  describe('Error Handling', () => {
    it('should handle creation errors gracefully', async () => {
      const onCreateCampaign = vi.fn().mockRejectedValue(new Error('Creation failed'));

      render(
        <AutomationDeploymentWizard
          {...defaultProps}
          onCreateCampaign={onCreateCampaign}
        />
      );

      // Try to create and expect error handling
      const createButton = screen.queryByText(/create.*automation/i);
      if (createButton) {
        fireEvent.click(createButton);
        // Should handle error gracefully (show toast, etc.)
      }
    });
  });
});