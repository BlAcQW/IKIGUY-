import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import DemoAnalytics from '@/components/dashboard/DemoAnalytics';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';

// Mock dependencies
vi.mock('@/components/ui/use-toast');
vi.mock('@/integrations/supabase/client');

const mockToast = vi.fn();
const mockSupabase = {
  from: vi.fn(() => ({
    select: vi.fn(() => ({
      order: vi.fn(() => ({
        eq: vi.fn(() => ({
          gte: vi.fn(() => ({
            single: vi.fn()
          }))
        }))
      }))
    }))
  }))
};

describe('DemoAnalytics', () => {
  const mockAnalyticsData = [
    {
      id: 'demo-1',
      assistant_name: 'Test Assistant 1',
      assistant_type: 'sales_cold_call',
      total_views: 150,
      total_interactions: 45,
      total_conversions: 12,
      avg_session_duration: 180,
      last_analytics_update: '2024-01-15T10:00:00Z',
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      id: 'demo-2',
      assistant_name: 'Test Assistant 2',
      assistant_type: 'help_desk',
      total_views: 89,
      total_interactions: 23,
      total_conversions: 8,
      avg_session_duration: 120,
      last_analytics_update: '2024-01-14T15:30:00Z',
      created_at: '2024-01-02T00:00:00Z'
    }
  ];

  const mockEventData = [
    { date: '2024-01-15', views: 10, interactions: 3, conversions: 1, shares: 0, embeds: 0 },
    { date: '2024-01-16', views: 15, interactions: 5, conversions: 2, shares: 1, embeds: 0 }
  ];

  const mockSessionData = [
    { session_id: 'session-1', duration_seconds: 180, interaction_count: 5, started_at: '2024-01-15T10:00:00Z' },
    { session_id: 'session-2', duration_seconds: 120, interaction_count: 3, started_at: '2024-01-15T11:00:00Z' }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue({ toast: mockToast });
    (supabase as any) = mockSupabase;
  });

  it('renders loading state initially', () => {
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        order: vi.fn().mockResolvedValue({ data: null, error: null })
      })
    });

    render(<DemoAnalytics />);
    
    expect(screen.getByText('Demo Analytics')).toBeInTheDocument();
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders analytics data after loading', async () => {
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        order: vi.fn().mockResolvedValue({ data: mockAnalyticsData, error: null })
      })
    });

    render(<DemoAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Total Demos')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument(); // Total demos
      expect(screen.getByText('239')).toBeInTheDocument(); // Total views
      expect(screen.getByText('68')).toBeInTheDocument(); // Total interactions
      expect(screen.getByText('8.37%')).toBeInTheDocument(); // Conversion rate
    });
  });

  it('displays demo performance list', async () => {
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        order: vi.fn().mockResolvedValue({ data: mockAnalyticsData, error: null })
      })
    });

    render(<DemoAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Assistant 1')).toBeInTheDocument();
      expect(screen.getByText('Test Assistant 2')).toBeInTheDocument();
      expect(screen.getByText('sales cold call')).toBeInTheDocument();
      expect(screen.getByText('help desk')).toBeInTheDocument();
    });
  });

  it('handles time range selection', async () => {
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        order: vi.fn().mockResolvedValue({ data: mockAnalyticsData, error: null })
      })
    });

    render(<DemoAnalytics />);
    
    await waitFor(() => {
      const timeRangeSelect = screen.getByDisplayValue('Last 30 days');
      fireEvent.click(timeRangeSelect);
    });

    await waitFor(() => {
      expect(screen.getByText('Last 7 days')).toBeInTheDocument();
      expect(screen.getByText('Last 90 days')).toBeInTheDocument();
      expect(screen.getByText('Last year')).toBeInTheDocument();
    });
  });

  it('handles demo selection', async () => {
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        order: vi.fn().mockResolvedValue({ data: mockAnalyticsData, error: null })
      })
    });

    render(<DemoAnalytics />);
    
    await waitFor(() => {
      const demoSelect = screen.getByDisplayValue('All Demos');
      fireEvent.click(demoSelect);
    });

    await waitFor(() => {
      expect(screen.getByText('Test Assistant 1')).toBeInTheDocument();
      expect(screen.getByText('Test Assistant 2')).toBeInTheDocument();
    });
  });

  it('exports analytics data', async () => {
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        order: vi.fn().mockResolvedValue({ data: mockAnalyticsData, error: null })
      })
    });

    // Mock URL.createObjectURL and document.createElement
    const mockCreateObjectURL = vi.fn(() => 'blob:mock-url');
    const mockRevokeObjectURL = vi.fn();
    const mockCreateElement = vi.fn(() => ({
      href: '',
      download: '',
      click: vi.fn()
    }));
    const mockAppendChild = vi.fn();
    const mockRemoveChild = vi.fn();

    Object.defineProperty(global, 'URL', {
      value: {
        createObjectURL: mockCreateObjectURL,
        revokeObjectURL: mockRevokeObjectURL
      }
    });

    Object.defineProperty(document, 'createElement', {
      value: mockCreateElement
    });

    Object.defineProperty(document.body, 'appendChild', {
      value: mockAppendChild
    });

    Object.defineProperty(document.body, 'removeChild', {
      value: mockRemoveChild
    });

    render(<DemoAnalytics />);
    
    await waitFor(() => {
      const exportButton = screen.getByText('Export');
      fireEvent.click(exportButton);
    });

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Success',
        description: 'Analytics data exported successfully'
      });
    });
  });

  it('handles export error', async () => {
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        order: vi.fn().mockResolvedValue({ data: mockAnalyticsData, error: null })
      })
    });

    // Mock URL.createObjectURL to throw error
    Object.defineProperty(global, 'URL', {
      value: {
        createObjectURL: vi.fn(() => { throw new Error('Export failed'); }),
        revokeObjectURL: vi.fn()
      }
    });

    render(<DemoAnalytics />);
    
    await waitFor(() => {
      const exportButton = screen.getByText('Export');
      fireEvent.click(exportButton);
    });

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'Failed to export analytics data',
        variant: 'destructive'
      });
    });
  });

  it('displays detailed charts for selected demo', async () => {
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        order: vi.fn().mockResolvedValue({ data: mockAnalyticsData, error: null }),
        eq: vi.fn().mockReturnValue({
          gte: vi.fn().mockReturnValue({
            order: vi.fn().mockResolvedValue({ data: mockEventData, error: null })
          })
        })
      })
    });

    render(<DemoAnalytics />);
    
    await waitFor(() => {
      const demoSelect = screen.getByDisplayValue('All Demos');
      fireEvent.click(demoSelect);
    });

    await waitFor(() => {
      fireEvent.click(screen.getByText('Test Assistant 1'));
    });

    await waitFor(() => {
      expect(screen.getByText('Event Activity')).toBeInTheDocument();
      expect(screen.getByText('Session Duration Distribution')).toBeInTheDocument();
    });
  });

  it('formats duration correctly', async () => {
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        order: vi.fn().mockResolvedValue({ data: mockAnalyticsData, error: null })
      })
    });

    render(<DemoAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('3m 0s')).toBeInTheDocument(); // 180 seconds
      expect(screen.getByText('2m 0s')).toBeInTheDocument(); // 120 seconds
    });
  });

  it('handles loading error', async () => {
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        order: vi.fn().mockRejectedValue(new Error('Database error'))
      })
    });

    render(<DemoAnalytics />);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'Database error',
        variant: 'destructive'
      });
    });
  });

  it('calculates summary metrics correctly', async () => {
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        order: vi.fn().mockResolvedValue({ data: mockAnalyticsData, error: null })
      })
    });

    render(<DemoAnalytics />);
    
    await waitFor(() => {
      // Total views: 150 + 89 = 239
      expect(screen.getByText('239')).toBeInTheDocument();
      
      // Total interactions: 45 + 23 = 68
      expect(screen.getByText('68')).toBeInTheDocument();
      
      // Total conversions: 12 + 8 = 20
      // Conversion rate: (20 / 239) * 100 = 8.37%
      expect(screen.getByText('8.37%')).toBeInTheDocument();
    });
  });

  it('displays demo badges correctly', async () => {
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        order: vi.fn().mockResolvedValue({ data: mockAnalyticsData, error: null })
      })
    });

    render(<DemoAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('sales cold call')).toBeInTheDocument();
      expect(screen.getByText('help desk')).toBeInTheDocument();
    });
  });
});
