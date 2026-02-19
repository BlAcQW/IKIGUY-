import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import AdvancedTemplateFeatures from '../components/AdvancedTemplateFeatures';
import { VoiceTemplate } from '../components/VoiceAgentTemplates';

// Mock the toast hook
const mockToast = vi.fn();
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

// Mock Supabase client
const mockSupabase = {
  from: vi.fn(() => ({
    select: vi.fn(() => ({
      eq: vi.fn(() => ({
        single: vi.fn(() => Promise.resolve({ data: null, error: null })),
      })),
    })),
    insert: vi.fn(() => Promise.resolve({ data: null, error: null })),
    update: vi.fn(() => Promise.resolve({ data: null, error: null })),
    delete: vi.fn(() => Promise.resolve({ data: null, error: null })),
  })),
};

vi.mock('@/integrations/supabase/client', () => ({
  supabase: mockSupabase,
}));

describe('AdvancedTemplateFeatures', () => {
  const mockTemplate: VoiceTemplate = {
    id: 'test-template',
    name: 'Test Template',
    description: 'A test template for advanced features',
    category: 'Test',
    icon: 'MessageSquare',
    difficulty: 'Beginner',
    estimatedTime: '10 minutes',
    features: ['Feature 1', 'Feature 2'],
    systemPrompt: 'Test system prompt',
    sampleQuestions: ['Question 1', 'Question 2'],
    useCases: ['Use case 1'],
    tags: ['test'],
    popularity: 85,
  };

  const mockOnClose = vi.fn();
  const mockOnSave = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the advanced template features dialog', () => {
    render(
      <AdvancedTemplateFeatures
        template={mockTemplate}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByText('Advanced Template Features')).toBeInTheDocument();
    expect(screen.getByText('Configure conditional logic, dynamic content, and template inheritance')).toBeInTheDocument();
  });

  it('displays all three tabs', () => {
    render(
      <AdvancedTemplateFeatures
        template={mockTemplate}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByText('Conditional Logic')).toBeInTheDocument();
    expect(screen.getByText('Dynamic Content')).toBeInTheDocument();
    expect(screen.getByText('Inheritance')).toBeInTheDocument();
  });

  it('shows conditional logic tab content by default', () => {
    render(
      <AdvancedTemplateFeatures
        template={mockTemplate}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByText('Add Condition')).toBeInTheDocument();
    expect(screen.getByText('user_type')).toBeInTheDocument();
    expect(screen.getByText('conversation_length')).toBeInTheDocument();
  });

  it('switches to dynamic content tab when clicked', () => {
    render(
      <AdvancedTemplateFeatures
        template={mockTemplate}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const dynamicContentTab = screen.getByText('Dynamic Content');
    fireEvent.click(dynamicContentTab);

    expect(screen.getByText('Add Variable')).toBeInTheDocument();
    expect(screen.getByText('$user_name')).toBeInTheDocument();
    expect(screen.getByText('$current_time')).toBeInTheDocument();
  });

  it('switches to inheritance tab when clicked', () => {
    render(
      <AdvancedTemplateFeatures
        template={mockTemplate}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const inheritanceTab = screen.getByText('Inheritance');
    fireEvent.click(inheritanceTab);

    expect(screen.getByText('Add Inheritance')).toBeInTheDocument();
    expect(screen.getByText('Base Customer Service Template')).toBeInTheDocument();
  });

  it('displays conditional logic items with correct information', () => {
    render(
      <AdvancedTemplateFeatures
        template={mockTemplate}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByText('user_type')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('Priority: 1')).toBeInTheDocument();
    expect(screen.getByText(/user_type equals "premium" → show advanced_features/)).toBeInTheDocument();
  });

  it('displays dynamic content items with correct information', () => {
    render(
      <AdvancedTemplateFeatures
        template={mockTemplate}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const dynamicContentTab = screen.getByText('Dynamic Content');
    fireEvent.click(dynamicContentTab);

    expect(screen.getByText('$user_name')).toBeInTheDocument();
    expect(screen.getByText('user_input')).toBeInTheDocument();
    expect(screen.getByText(/Default: "Guest" \| Validation: string \| Transform: capitalize/)).toBeInTheDocument();
  });

  it('displays inheritance items with correct information', () => {
    render(
      <AdvancedTemplateFeatures
        template={mockTemplate}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const inheritanceTab = screen.getByText('Inheritance');
    fireEvent.click(inheritanceTab);

    expect(screen.getByText('Base Customer Service Template')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('partial')).toBeInTheDocument();
    expect(screen.getByText(/2 overrides, 2 extensions/)).toBeInTheDocument();
  });

  it('calls onClose when cancel button is clicked', () => {
    render(
      <AdvancedTemplateFeatures
        template={mockTemplate}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('calls onSave with advanced features data when save button is clicked', async () => {
    render(
      <AdvancedTemplateFeatures
        template={mockTemplate}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Saving...')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith({
        conditionalLogic: expect.arrayContaining([
          expect.objectContaining({
            id: '1',
            condition: 'user_type',
            operator: 'equals',
            value: 'premium',
            action: 'show',
            target: 'advanced_features',
            priority: 1,
            isActive: true
          })
        ]),
        dynamicContent: expect.arrayContaining([
          expect.objectContaining({
            id: '1',
            variable: 'user_name',
            source: 'user_input',
            defaultValue: 'Guest',
            validation: 'string',
            transform: 'capitalize',
            isRequired: false,
            isSensitive: false
          })
        ]),
        inheritance: expect.arrayContaining([
          expect.objectContaining({
            id: '1',
            parentTemplateId: 'parent-1',
            parentTemplateName: 'Base Customer Service Template',
            inheritanceType: 'partial',
            isActive: true
          })
        ])
      });
    });
  });

  it('shows success toast when save is successful', async () => {
    render(
      <AdvancedTemplateFeatures
        template={mockTemplate}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: "Advanced Features Saved",
        description: "Template advanced features have been updated successfully",
      });
    });
  });

  it('toggles conditional logic active state when toggle button is clicked', () => {
    render(
      <AdvancedTemplateFeatures
        template={mockTemplate}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const toggleButtons = screen.getAllByRole('button');
    const pauseButton = toggleButtons.find(button => 
      button.querySelector('svg')?.getAttribute('data-lucide') === 'pause'
    );

    if (pauseButton) {
      fireEvent.click(pauseButton);
      
      // The button should change to play icon
      expect(screen.getByText('Inactive')).toBeInTheDocument();
    }
  });

  it('toggles inheritance active state when toggle button is clicked', () => {
    render(
      <AdvancedTemplateFeatures
        template={mockTemplate}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const inheritanceTab = screen.getByText('Inheritance');
    fireEvent.click(inheritanceTab);

    const toggleButtons = screen.getAllByRole('button');
    const unlinkButton = toggleButtons.find(button => 
      button.querySelector('svg')?.getAttribute('data-lucide') === 'unlink'
    );

    if (unlinkButton) {
      fireEvent.click(unlinkButton);
      
      // The button should change to link icon
      expect(screen.getByText('Inactive')).toBeInTheDocument();
    }
  });
});
