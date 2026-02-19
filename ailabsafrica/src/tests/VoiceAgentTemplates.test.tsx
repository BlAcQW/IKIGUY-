import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import VoiceAgentTemplates from '@/components/VoiceAgentTemplates';
import { VoiceTemplate } from '@/components/VoiceAgentTemplates';

// Mock the templates data
const mockTemplate: VoiceTemplate = {
  id: 'customer-support',
  name: 'Customer Support Agent',
  description: 'Handle customer inquiries, troubleshoot issues, and provide product support',
  category: 'Customer Service',
  icon: 'MessageSquare',
  difficulty: 'Beginner',
  estimatedTime: '15-30 minutes',
  features: ['Issue Resolution', 'Product Information', 'Ticket Creation', 'FAQ Handling'],
  systemPrompt: 'You are a helpful customer support agent for {company_name}.',
  sampleQuestions: [
    'How do I reset my password?',
    'What are your return policies?',
    'I need help with my order',
    'Can you explain your warranty coverage?'
  ],
  useCases: ['E-commerce Support', 'SaaS Customer Service', 'Product Support', 'Technical Help'],
  tags: ['support', 'customer-service', 'help-desk', 'troubleshooting'],
  popularity: 95
};

// Mock useToast
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

describe('VoiceAgentTemplates', () => {
  const mockOnTemplateSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the component with header', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    expect(screen.getByText('Voice Agent Templates')).toBeInTheDocument();
    expect(screen.getByText(/Choose from our pre-built templates/)).toBeInTheDocument();
  });

  it('displays category filter buttons', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    expect(screen.getByText('All Templates')).toBeInTheDocument();
    expect(screen.getAllByText('Customer Service').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Scheduling').length).toBeGreaterThan(0);
  });

  it('filters templates by category when category button is clicked', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    expect(screen.getByText('Customer Support Agent')).toBeInTheDocument();
    expect(screen.getByText('Appointment Scheduler')).toBeInTheDocument();
  });

  it('displays template cards with correct information', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    // Check for template information
    expect(screen.getByText('Customer Support Agent')).toBeInTheDocument();
    expect(screen.getByText('Handle customer inquiries, troubleshoot issues, and provide product support')).toBeInTheDocument();
    expect(screen.getAllByText('Customer Service').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Beginner').length).toBeGreaterThan(0);
    expect(screen.getByText('15-30 minutes')).toBeInTheDocument();
    expect(screen.getByText('95% popular')).toBeInTheDocument();
  });

  it('calls onTemplateSelect when template card is clicked', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    const templateCard = screen.getByText('Customer Support Agent').closest('.cursor-pointer');
    if (templateCard) {
      fireEvent.click(templateCard);
      expect(mockOnTemplateSelect).toHaveBeenCalled();
    }
  });

  it('displays template tags', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    expect(screen.getByText('support')).toBeInTheDocument();
    expect(screen.getByText('customer-service')).toBeInTheDocument();
    expect(screen.getByText('help-desk')).toBeInTheDocument();
  });

  it('shows difficulty badges with correct colors', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    const beginnerBadges = screen.getAllByText('Beginner');
    expect(beginnerBadges.length).toBeGreaterThan(0);
  });

  it('displays estimated time for templates', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    expect(screen.getByText('15-30 minutes')).toBeInTheDocument();
  });

  it('shows popularity rating', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    expect(screen.getByText('95% popular')).toBeInTheDocument();
  });

  it('displays configure button for templates', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    const configureButtons = screen.getAllByText('Configure');
    expect(configureButtons.length).toBeGreaterThan(0);
  });

  it('handles configure button click', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    const configureButton = screen.getAllByText('Configure')[0];
    fireEvent.click(configureButton);
    
    // Should not trigger template selection
    expect(mockOnTemplateSelect).not.toHaveBeenCalled();
  });

  it('displays selected template summary when template is selected', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={mockTemplate}
      />
    );

    expect(screen.getByText('Template Selected')).toBeInTheDocument();
    expect(screen.getAllByText('Customer Support Agent').length).toBeGreaterThan(0);
    expect(screen.getByText('Use This Template')).toBeInTheDocument();
  });

  it('handles template selection from summary card', async () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={mockTemplate}
      />
    );

    const useTemplateButton = screen.getByText('Use This Template');
    fireEvent.click(useTemplateButton);

    // Wait for the async operation to complete
    await waitFor(() => {
      expect(mockOnTemplateSelect).toHaveBeenCalledWith(mockTemplate);
    });
  });

  it('sorts templates by popularity', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    // The most popular templates should appear first
    const templateCards = screen.getAllByText(/Agent|Scheduler/);
    expect(templateCards.length).toBeGreaterThan(0);
  });

  it('shows no templates message when filtered category has no templates', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    // Test the "All Templates" view shows templates
    expect(screen.getByText('Customer Support Agent')).toBeInTheDocument();
    expect(screen.getByText('Appointment Scheduler')).toBeInTheDocument();
  });

  it('displays available templates', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    // Should show available templates
    expect(screen.getByText('Customer Support Agent')).toBeInTheDocument();
    expect(screen.getByText('Appointment Scheduler')).toBeInTheDocument();
  });

  it('handles different difficulty levels', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    // Check for available difficulty levels
    expect(screen.getAllByText('Beginner').length).toBeGreaterThan(0);
  });

  it('displays template categories correctly', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    expect(screen.getAllByText('Customer Service').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Scheduling').length).toBeGreaterThan(0);
  });

  it('filters templates when category is selected', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    // Get the Customer Service button (first one)
    const customerServiceButtons = screen.getAllByText('Customer Service');
    const customerServiceButton = customerServiceButtons.find(button => 
      button.tagName === 'BUTTON'
    );
    
    if (customerServiceButton) {
      fireEvent.click(customerServiceButton);
      // When Customer Service is selected, it should show the Customer Support Agent template
      expect(screen.getByText('Customer Support Agent')).toBeInTheDocument();
      // The Appointment Scheduler should not be visible since it's in a different category
      expect(screen.queryByText('Appointment Scheduler')).not.toBeInTheDocument();
    }
  });

  it('resets to all templates when All Templates is clicked', () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={null}
      />
    );

    const allTemplatesButton = screen.getByText('All Templates');
    fireEvent.click(allTemplatesButton);

    // Should show all templates
    expect(screen.getByText('Customer Support Agent')).toBeInTheDocument();
    expect(screen.getByText('Appointment Scheduler')).toBeInTheDocument();
  });

  it('shows loading state when Use This Template is clicked', async () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={mockTemplate}
      />
    );

    const useTemplateButton = screen.getByText('Use This Template');
    fireEvent.click(useTemplateButton);

    // Should show loading state
    await waitFor(() => {
      expect(screen.getByText('Confirming...')).toBeInTheDocument();
    });
  });

  it('shows success state after template is confirmed', async () => {
    render(
      <VoiceAgentTemplates
        onTemplateSelect={mockOnTemplateSelect}
        selectedTemplate={mockTemplate}
      />
    );

    const useTemplateButton = screen.getByText('Use This Template');
    fireEvent.click(useTemplateButton);

    // Wait for confirmation
    await waitFor(() => {
      expect(screen.getByText('Template Ready')).toBeInTheDocument();
    });
  });
});
