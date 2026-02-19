import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Analytics from '../Analytics';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';

// Mock all the analytics components
vi.mock('@/components/analytics/AnalyticsSidebar', () => ({
  default: ({ selectedView, onViewChange }: any) => (
    <div data-testid="analytics-sidebar">
      <button onClick={() => onViewChange('automation')}>Automation</button>
      <button onClick={() => onViewChange('deployment')}>Deployment</button>
      <button onClick={() => onViewChange('vapi')}>VAPI</button>
      <button onClick={() => onViewChange('health')}>Health</button>
      <button onClick={() => onViewChange('system')}>System</button>
      <div>Selected: {selectedView}</div>
    </div>
  )
}));

vi.mock('@/components/analytics/UnifiedAutomationDashboard', () => ({
  default: ({ timeRange }: any) => (
    <div data-testid="unified-automation-dashboard">
      Unified Dashboard - {timeRange}
    </div>
  )
}));

vi.mock('@/components/analytics/DeploymentAnalyticsDashboard', () => ({
  default: ({ tenantId }: any) => (
    <div data-testid="deployment-analytics-dashboard">
      Deployment Dashboard - {tenantId}
    </div>
  )
}));

vi.mock('@/components/analytics/RealTimeHealthMonitor', () => ({
  default: ({ automationId, showActivityLog, refreshInterval }: any) => (
    <div data-testid="realtime-health-monitor">
      Health Monitor - {automationId} - {showActivityLog ? 'with' : 'without'} activity log - {refreshInterval}ms
    </div>
  )
}));

vi.mock('@/components/voice-agent/VapiAnalyticsDashboard', () => ({
  default: ({ agentId, tenantId, apiBaseUrl }: any) => (
    <div data-testid="vapi-analytics-dashboard">
      VAPI Dashboard - {agentId} - {tenantId} - {apiBaseUrl}
    </div>
  )
}));

vi.mock('@/components/auth/MongoAuthContext');

// Mock UI components
vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: any) => <div className="card">{children}</div>,
  CardContent: ({ children }: any) => <div className="card-content">{children}</div>
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick }: any) => <button onClick={onClick}>{children}</button>
}));

const mockUser = {
  id: 'test-user-id',
  user_metadata: {
    tenant_id: 'test-tenant-id'
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
      <MemoryRouter initialEntries={['/analytics']}>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('Analytics Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useMongoAuth as any).mockReturnValue({
      user: mockUser,
      isLoading: false
    });
  });

  it('renders without crashing when user is authenticated', () => {
    render(
      <TestWrapper>
        <Analytics />
      </TestWrapper>
    );

    expect(screen.getByTestId('analytics-sidebar')).toBeInTheDocument();
  });

  it('shows loading state when auth is loading', () => {
    (useMongoAuth as any).mockReturnValue({
      user: null,
      isLoading: true
    });

    render(
      <TestWrapper>
        <Analytics />
      </TestWrapper>
    );

    expect(screen.getByText('Loading analytics...')).toBeInTheDocument();
  });

  it('displays automation view by default', () => {
    render(
      <TestWrapper>
        <Analytics />
      </TestWrapper>
    );

    expect(screen.getByTestId('unified-automation-dashboard')).toBeInTheDocument();
    expect(screen.getByText('Unified Dashboard - 7d')).toBeInTheDocument();
  });

  it('switches to deployment view when selected', () => {
    render(
      <TestWrapper>
        <Analytics />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Deployment'));

    expect(screen.getByTestId('deployment-analytics-dashboard')).toBeInTheDocument();
    expect(screen.getByText('Deployment Dashboard - test-tenant-id')).toBeInTheDocument();
  });

  it('switches to VAPI view when selected', () => {
    render(
      <TestWrapper>
        <Analytics />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('VAPI'));

    expect(screen.getByTestId('vapi-analytics-dashboard')).toBeInTheDocument();
    expect(screen.getByText(/VAPI Dashboard - default-automation - test-tenant-id - https:\/\/api\.ailabsafrica\.com/)).toBeInTheDocument();
  });

  it('switches to health monitoring view when selected', () => {
    render(
      <TestWrapper>
        <Analytics />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Health'));

    expect(screen.getByTestId('realtime-health-monitor')).toBeInTheDocument();
    expect(screen.getByText('Health Monitor - default-automation - with activity log - 30000ms')).toBeInTheDocument();
  });

  it('shows system health redirect when system view is selected', () => {
    render(
      <TestWrapper>
        <Analytics />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('System'));

    expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Open System Health Dashboard')).toBeInTheDocument();
  });

  it('uses fallback tenant ID when user metadata is missing', () => {
    (useMongoAuth as any).mockReturnValue({
      user: { id: 'test-user-id' }, // No user_metadata
      isLoading: false
    });

    render(
      <TestWrapper>
        <Analytics />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Deployment'));

    expect(screen.getByText('Deployment Dashboard - test-user-id')).toBeInTheDocument();
  });

  it('passes correct props to analytics components', () => {
    render(
      <TestWrapper>
        <Analytics />
      </TestWrapper>
    );

    // Test automation dashboard props
    expect(screen.getByText('Unified Dashboard - 7d')).toBeInTheDocument();

    // Switch to other views and test their props
    fireEvent.click(screen.getByText('Deployment'));
    expect(screen.getByText('Deployment Dashboard - test-tenant-id')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Health'));
    expect(screen.getByText('Health Monitor - default-automation - with activity log - 30000ms')).toBeInTheDocument();
  });

  it('maintains selected view state correctly', () => {
    render(
      <TestWrapper>
        <Analytics />
      </TestWrapper>
    );

    expect(screen.getByText('Selected: automation')).toBeInTheDocument();

    fireEvent.click(screen.getByText('VAPI'));
    expect(screen.getByText('Selected: vapi')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Health'));
    expect(screen.getByText('Selected: health')).toBeInTheDocument();
  });
});