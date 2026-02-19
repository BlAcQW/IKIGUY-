import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import AnalyticsSidebar, { type AnalyticsView } from '../AnalyticsSidebar';

// Mock UI components
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, className = '', variant }: any) => (
    <button onClick={onClick} className={`button ${className} ${variant}`} data-variant={variant}>
      {children}
    </button>
  )
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant = 'default', className = '' }: any) => (
    <span className={`badge ${className} ${variant}`} data-variant={variant}>
      {children}
    </span>
  )
}));

vi.mock('@/lib/utils', () => ({
  cn: (...classes: any[]) => classes.filter(Boolean).join(' ')
}));

// Mock window.open
const mockWindowOpen = vi.fn();
Object.defineProperty(window, 'open', {
  value: mockWindowOpen,
});

describe('AnalyticsSidebar', () => {
  const mockOnViewChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const defaultProps = {
    selectedView: 'automation' as AnalyticsView,
    onViewChange: mockOnViewChange
  };

  it('renders without crashing', () => {
    render(<AnalyticsSidebar {...defaultProps} />);

    expect(screen.getByText('Analytics')).toBeInTheDocument();
  });

  it('displays all sidebar navigation items', () => {
    render(<AnalyticsSidebar {...defaultProps} />);

    expect(screen.getByText('Automation Overview')).toBeInTheDocument();
    expect(screen.getByText('Deployment Metrics')).toBeInTheDocument();
    expect(screen.getByText('Voice & VAPI')).toBeInTheDocument();
    expect(screen.getByText('Health Monitoring')).toBeInTheDocument();
    expect(screen.getByText('System Health')).toBeInTheDocument();
  });

  it('highlights the selected view', () => {
    render(<AnalyticsSidebar {...defaultProps} />);

    const automationButton = screen.getByRole('button', { name: /automation overview/i });
    expect(automationButton).toHaveAttribute('data-variant', 'default');
  });

  it('shows non-selected views as ghost variant', () => {
    render(<AnalyticsSidebar {...defaultProps} />);

    const deploymentButton = screen.getByRole('button', { name: /deployment metrics/i });
    expect(deploymentButton).toHaveAttribute('data-variant', 'ghost');
  });

  it('calls onViewChange when a navigation item is clicked', () => {
    render(<AnalyticsSidebar {...defaultProps} />);

    const deploymentButton = screen.getByRole('button', { name: /deployment metrics/i });
    fireEvent.click(deploymentButton);

    expect(mockOnViewChange).toHaveBeenCalledWith('deployment');
  });

  it('displays the main badge for automation overview', () => {
    render(<AnalyticsSidebar {...defaultProps} />);

    expect(screen.getByText('Main')).toBeInTheDocument();
  });

  it('shows quick access links', () => {
    render(<AnalyticsSidebar {...defaultProps} />);

    expect(screen.getByText('Quick Access')).toBeInTheDocument();
    expect(screen.getByText('→ Call Logs')).toBeInTheDocument();
    expect(screen.getByText('→ System Health (Admin)')).toBeInTheDocument();
    expect(screen.getByText('→ Settings')).toBeInTheDocument();
  });

  it('opens call logs in new tab when quick access link is clicked', () => {
    render(<AnalyticsSidebar {...defaultProps} />);

    const callLogsLink = screen.getByText('→ Call Logs');
    fireEvent.click(callLogsLink);

    expect(mockWindowOpen).toHaveBeenCalledWith('/call-logs', '_blank');
  });

  it('opens admin system health in new tab when quick access link is clicked', () => {
    render(<AnalyticsSidebar {...defaultProps} />);

    const systemHealthLink = screen.getByText('→ System Health (Admin)');
    fireEvent.click(systemHealthLink);

    expect(mockWindowOpen).toHaveBeenCalledWith('/admin/system-health', '_blank');
  });

  it('opens settings in new tab when quick access link is clicked', () => {
    render(<AnalyticsSidebar {...defaultProps} />);

    const settingsLink = screen.getByText('→ Settings');
    fireEvent.click(settingsLink);

    expect(mockWindowOpen).toHaveBeenCalledWith('/settings', '_blank');
  });

  it('changes view when different navigation items are clicked', () => {
    render(<AnalyticsSidebar {...defaultProps} />);

    // Click on different views
    fireEvent.click(screen.getByRole('button', { name: /voice & vapi/i }));
    expect(mockOnViewChange).toHaveBeenCalledWith('vapi');

    fireEvent.click(screen.getByRole('button', { name: /health monitoring/i }));
    expect(mockOnViewChange).toHaveBeenCalledWith('health');

    fireEvent.click(screen.getByRole('button', { name: /system health/i }));
    expect(mockOnViewChange).toHaveBeenCalledWith('system');
  });

  it('applies custom className when provided', () => {
    const customClass = 'custom-sidebar-class';
    render(<AnalyticsSidebar {...defaultProps} className={customClass} />);

    const sidebar = screen.getByText('Analytics').closest('div')?.parentElement;
    expect(sidebar).toHaveClass(customClass);
  });

  it('shows descriptions for each navigation item', () => {
    render(<AnalyticsSidebar {...defaultProps} />);

    expect(screen.getByText('Unified automation analytics and monitoring')).toBeInTheDocument();
    expect(screen.getByText('Track deployment performance and trends')).toBeInTheDocument();
    expect(screen.getByText('Voice agent analytics and call metrics')).toBeInTheDocument();
    expect(screen.getByText('Real-time system health and component status')).toBeInTheDocument();
    expect(screen.getByText('Server resources and system performance')).toBeInTheDocument();
  });
});