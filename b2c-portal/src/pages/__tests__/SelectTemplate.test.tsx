import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import SelectTemplate from '../SelectTemplate';

const MockedSelectTemplate = () => (
  <BrowserRouter>
    <SelectTemplate />
  </BrowserRouter>
);

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useSearchParams: () => [new URLSearchParams(), vi.fn()]
  };
});

describe('SelectTemplate', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  test('renders helpdesk template with correct properties', () => {
    render(<MockedSelectTemplate />);

    expect(screen.getByText('Customer Support Helpdesk')).toBeInTheDocument();
    expect(screen.getByText('Provide automated customer support and resolve common inquiries')).toBeInTheDocument();
    expect(screen.getAllByText('Support')).toHaveLength(2); // Filter button and badge
    expect(screen.getAllByText('intermediate').length).toBeGreaterThan(0); // Multiple templates have intermediate difficulty
  });

  test('displays helpdesk template features', () => {
    render(<MockedSelectTemplate />);

    expect(screen.getByText('Issue categorization')).toBeInTheDocument();
    expect(screen.getByText('Ticket creation')).toBeInTheDocument();
    expect(screen.getByText('Knowledge base integration')).toBeInTheDocument();
  });

  test('shows Support category filter', () => {
    render(<MockedSelectTemplate />);

    expect(screen.getByRole('button', { name: /support/i })).toBeInTheDocument();
  });

  test('filters templates by Support category', () => {
    render(<MockedSelectTemplate />);

    const supportButton = screen.getByRole('button', { name: /support/i });
    fireEvent.click(supportButton);

    expect(screen.getByText('Customer Support Helpdesk')).toBeInTheDocument();
    expect(screen.queryByText('Lead Nurturing Campaign')).not.toBeInTheDocument();
  });

  test('selects helpdesk template and shows additional details', () => {
    render(<MockedSelectTemplate />);

    const helpdeskCard = screen.getByText('Customer Support Helpdesk').closest('[role="button"]') ||
                        screen.getByText('Customer Support Helpdesk').closest('div')?.parentElement;

    if (helpdeskCard) {
      fireEvent.click(helpdeskCard);

      expect(screen.getByText('Efficiently handle customer support requests and resolve issues')).toBeInTheDocument();
      expect(screen.getByText('Automated calls to help customers with common issues and create support tickets')).toBeInTheDocument();
    }
  });

  test('navigates to campaign creation with helpdesk template', () => {
    render(<MockedSelectTemplate />);

    const helpdeskCard = screen.getByText('Customer Support Helpdesk').closest('[role="button"]') ||
                        screen.getByText('Customer Support Helpdesk').closest('div')?.parentElement;

    if (helpdeskCard) {
      fireEvent.click(helpdeskCard);

      const useTemplateButton = screen.getByRole('button', { name: /use this template/i });
      fireEvent.click(useTemplateButton);

      expect(mockNavigate).toHaveBeenCalledWith('/campaigns/create', {
        state: {
          selectedTemplate: expect.objectContaining({
            id: 'helpdesk-support',
            name: 'Customer Support Helpdesk',
            category: 'Support'
          })
        }
      });
    }
  });
});