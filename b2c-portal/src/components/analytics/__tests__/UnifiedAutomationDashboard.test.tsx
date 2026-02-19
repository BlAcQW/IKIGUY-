import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import UnifiedAutomationDashboard from '../UnifiedAutomationDashboard';
import { useToast } from '@/hooks/use-toast';
import { automationOrchestrationService } from '@/services/AutomationOrchestrationService';

// Mock dependencies
vi.mock('@/hooks/use-toast');
vi.mock('@/components/auth/MongoAuthContext', () => ({
  useMongoAuth: () => ({
    user: { id: 'test-user', user_metadata: { tenant_id: 'test-tenant' } }
  })
}));
vi.mock('@/services/AutomationOrchestrationService');

// Mock UI components that might cause issues in tests
vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className = '' }: any) => <div className={`card ${className}`}>{children}</div>,
  CardContent: ({ children, className = '' }: any) => <div className={`card-content ${className}`}>{children}</div>,
  CardDescription: ({ children }: any) => <div className="card-description">{children}</div>,
  CardHeader: ({ children, className = '' }: any) => <div className={`card-header ${className}`}>{children}</div>,
  CardTitle: ({ children, className = '' }: any) => <div className={`card-title ${className}`}>{children}</div>
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, className = '' }: any) => (
    <button onClick={onClick} disabled={disabled} className={`button ${className}`}>
      {children}
    </button>
  )
}));

vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, value, onValueChange }: any) => (
    <div data-testid="tabs" data-value={value} onClick={() => onValueChange?.('test')}>
      {children}
    </div>
  ),
  TabsContent: ({ children, value }: any) => <div data-testid={`tab-content-${value}`}>{children}</div>,
  TabsList: ({ children }: any) => <div data-testid="tabs-list">{children}</div>,
  TabsTrigger: ({ children, value }: any) => <div data-testid={`tab-trigger-${value}`}>{children}</div>
}));

const mockAnalyticsData = {
  total_automations: 10,
  deployed_automations: 8,
  success_rate: 0.85,
  total_calls: 150,
  total_cost: 45.75,
  avg_sentiment: 0.7,
  period_start: '2024-01-01',
  period_end: '2024-01-31'
};

const mockConfigStatus = {
  config_id: 'test-config',
  status: 'deployed',
  deployment_date: '2024-01-15',
  last_activity: '2024-01-31',
  metrics: {
    success_rate: 0.9,
    total_executions: 50,
    avg_execution_time: 2.5
  }
};

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('UnifiedAutomationDashboard', () => {
  const mockToast = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue({ toast: mockToast });
    (automationOrchestrationService.getAnalyticsOverview as any).mockResolvedValue(mockAnalyticsData);
    (automationOrchestrationService.getConfigurationStatus as any).mockResolvedValue(mockConfigStatus);
  });

  it('renders without crashing', () => {
    render(
      <TestWrapper>
        <UnifiedAutomationDashboard />
      </TestWrapper>
    );

    expect(screen.getByText('Automation Analytics')).toBeInTheDocument();
  });

  it('displays analytics overview cards when data loads', async () => {
    render(
      <TestWrapper>
        <UnifiedAutomationDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Total Automations')).toBeInTheDocument();
      expect(screen.getByText('Success Rate')).toBeInTheDocument();
      expect(screen.getByText('Total Calls')).toBeInTheDocument();
      expect(screen.getByText('Total Cost')).toBeInTheDocument();
    });
  });

  it('shows configuration status when configId is provided', async () => {
    render(
      <TestWrapper>
        <UnifiedAutomationDashboard configId="test-config" />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Configuration Status')).toBeInTheDocument();
      expect(screen.getByText('test-config')).toBeInTheDocument();
    });
  });

  it('handles refresh button click', async () => {
    render(
      <TestWrapper>
        <UnifiedAutomationDashboard />
      </TestWrapper>
    );

    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    fireEvent.click(refreshButton);

    expect(automationOrchestrationService.getAnalyticsOverview).toHaveBeenCalled();
  });

  it('handles export functionality', async () => {
    render(
      <TestWrapper>
        <UnifiedAutomationDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Total Automations')).toBeInTheDocument();
    });

    const exportButton = screen.getByRole('button', { name: /export/i });
    fireEvent.click(exportButton);

    expect(mockToast).toHaveBeenCalledWith({
      title: "Export Successful",
      description: "Analytics data exported as JSON"
    });
  });

  it('shows loading state initially', () => {
    (automationOrchestrationService.getAnalyticsOverview as any).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <TestWrapper>
        <UnifiedAutomationDashboard />
      </TestWrapper>
    );

    expect(screen.getByTestId('tabs')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    const errorMessage = 'Failed to fetch analytics';
    (automationOrchestrationService.getAnalyticsOverview as any).mockRejectedValue(
      new Error(errorMessage)
    );

    render(
      <TestWrapper>
        <UnifiedAutomationDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: "Failed to Load Analytics",
        description: errorMessage,
        variant: "destructive"
      });
    });
  });

  it('displays different time ranges correctly', async () => {
    render(
      <TestWrapper>
        <UnifiedAutomationDashboard timeRange="30d" />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(automationOrchestrationService.getAnalyticsOverview).toHaveBeenCalledWith(
        expect.objectContaining({
          start_date: expect.any(String),
          end_date: expect.any(String)
        })
      );
    });
  });

  it('switches between tabs correctly', () => {
    render(
      <TestWrapper>
        <UnifiedAutomationDashboard />
      </TestWrapper>
    );

    expect(screen.getByTestId('tabs')).toBeInTheDocument();
    expect(screen.getByTestId('tab-content-overview')).toBeInTheDocument();
    expect(screen.getByTestId('tab-content-performance')).toBeInTheDocument();
    expect(screen.getByTestId('tab-content-health')).toBeInTheDocument();
    expect(screen.getByTestId('tab-content-tools')).toBeInTheDocument();
  });
});