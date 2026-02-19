import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import CampaignTemplateSelector from '../CampaignTemplateSelector';

describe('Customer Reactivation Template', () => {
  const mockOnClose = vi.fn();
  const mockOnTemplateSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display customer reactivation template', () => {
    render(
      <CampaignTemplateSelector
        isOpen={true}
        onClose={mockOnClose}
        onTemplateSelect={mockOnTemplateSelect}
      />
    );

    expect(screen.getByText('Customer Reactivation Campaign')).toBeInTheDocument();
    expect(screen.getByText('AI-powered multi-channel campaign to reactivate dormant customers with personalized outreach')).toBeInTheDocument();
  });

  it('should show customer reactivation template in marketing category', () => {
    render(
      <CampaignTemplateSelector
        isOpen={true}
        onClose={mockOnClose}
        onTemplateSelect={mockOnTemplateSelect}
      />
    );

    // Click on Marketing category
    fireEvent.click(screen.getByRole('button', { name: /marketing/i }));

    // Should still show the customer reactivation template
    expect(screen.getByText('Customer Reactivation Campaign')).toBeInTheDocument();
  });

  it('should display n8n template ID when selected', () => {
    render(
      <CampaignTemplateSelector
        isOpen={true}
        onClose={mockOnClose}
        onTemplateSelect={mockOnTemplateSelect}
      />
    );

    // Click on the customer reactivation template
    fireEvent.click(screen.getByText('Customer Reactivation Campaign'));

    // Check if template details are shown
    expect(screen.getByText('Multi-channel sequencing (SMS, Email, Voice)')).toBeInTheDocument();
    expect(screen.getByText('AI-powered personalization')).toBeInTheDocument();
    expect(screen.getByText('Response sentiment analysis')).toBeInTheDocument();
  });

  it('should show correct difficulty and setup time', () => {
    render(
      <CampaignTemplateSelector
        isOpen={true}
        onClose={mockOnClose}
        onTemplateSelect={mockOnTemplateSelect}
      />
    );

    // Click on the customer reactivation template
    fireEvent.click(screen.getByText('Customer Reactivation Campaign'));

    // Check difficulty badge
    expect(screen.getByText('advanced')).toBeInTheDocument();

    // Check setup time
    expect(screen.getByText('⏱️ 30-40 minutes')).toBeInTheDocument();
  });

  it('should display expected integrations', () => {
    render(
      <CampaignTemplateSelector
        isOpen={true}
        onClose={mockOnClose}
        onTemplateSelect={mockOnTemplateSelect}
      />
    );

    // Click on the customer reactivation template
    fireEvent.click(screen.getByText('Customer Reactivation Campaign'));

    // Check for key integrations
    expect(screen.getByText('n8n')).toBeInTheDocument();
    expect(screen.getByText('openai')).toBeInTheDocument();
    expect(screen.getByText('twilio')).toBeInTheDocument();
  });

  it('should show conversion rate and expected responses', () => {
    render(
      <CampaignTemplateSelector
        isOpen={true}
        onClose={mockOnClose}
        onTemplateSelect={mockOnTemplateSelect}
      />
    );

    // Click on the customer reactivation template
    fireEvent.click(screen.getByText('Customer Reactivation Campaign'));

    // Check conversion rate
    expect(screen.getByText('📊 15-25% conversion')).toBeInTheDocument();

    // Check expected results section
    expect(screen.getByText('Response Rate: 45%')).toBeInTheDocument();
    expect(screen.getByText('Conversion: 15-25%')).toBeInTheDocument();
    expect(screen.getByText('Avg Duration: 4-6 minutes')).toBeInTheDocument();
  });

  it('should call onTemplateSelect when template is selected', () => {
    render(
      <CampaignTemplateSelector
        isOpen={true}
        onClose={mockOnClose}
        onTemplateSelect={mockOnTemplateSelect}
      />
    );

    // Click on the customer reactivation template
    fireEvent.click(screen.getByText('Customer Reactivation Campaign'));

    // Click "Use This Template" button
    fireEvent.click(screen.getByText('Use This Template'));

    expect(mockOnTemplateSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'customer_reactivation',
        name: 'Customer Reactivation Campaign',
        category: 'marketing',
        n8nTemplateId: 6213
      })
    );
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should display sample script', () => {
    render(
      <CampaignTemplateSelector
        isOpen={true}
        onClose={mockOnClose}
        onTemplateSelect={mockOnTemplateSelect}
      />
    );

    // Click on the customer reactivation template
    fireEvent.click(screen.getByText('Customer Reactivation Campaign'));

    // Check for sample script
    expect(screen.getByText('Sample Script')).toBeInTheDocument();
    expect(screen.getByText(/Hi \[Name\], we noticed you haven't used/)).toBeInTheDocument();
  });
});