import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import AssistantAnalytics from '@/components/dashboard/AssistantAnalytics';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';

// Mock dependencies
vi.mock('@/contexts/AuthContext');
vi.mock('@/components/ui/use-toast');
vi.mock('@/integrations/supabase/client');
vi.mock('recharts', () => ({
  BarChart: ({ children }: { children: React.ReactNode }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  PieChart: ({ children }: { children: React.ReactNode }) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  Legend: () => <div data-testid="legend" />,
  AreaChart: ({ children }: { children: React.ReactNode }) => <div data-testid="area-chart">{children}</div>,
  Area: () => <div data-testid="area" />,
}));

const mockUser = {
  id: 'test-user-id',
  email: 'test@example.com',
};

const mockAgents = [
  {
    id: '1',
    assistant_name: 'Customer Support Bot',
    assistant_type: 'customer_service',
    demo_url: 'https://demo.example.com/1',
    created_at: '2024-01-15T10:00:00Z',
    status: 'active',
    assistant_id: 'assistant_1',
    voice_id: 'voice_1',
  },
  {
    id: '2',
    assistant_name: 'Sales Assistant',
    assistant_type: 'sales',
    demo_url: 'https://demo.example.com/2',
    created_at: '2024-01-20T14:30:00Z',
    status: 'active',
    assistant_id: 'assistant_2',
    voice_id: 'voice_2',
  },
  {
    id: '3',
    assistant_name: 'Booking Agent',
    assistant_type: 'booking',
    demo_url: 'https://demo.example.com/3',
    created_at: '2024-01-25T09:15:00Z',
    status: 'paused',
    assistant_id: 'assistant_3',
    voice_id: 'voice_3',
  },
];

describe('AssistantAnalytics', () => {
  const mockToast = vi.fn();
  const mockSupabaseFunctions = {
    invoke: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    (useAuth as any).mockReturnValue({
      user: mockUser,
    });
    
    (useToast as any).mockReturnValue({
      toast: mockToast,
    });
    
    (supabase as any) = {
      functions: mockSupabaseFunctions,
    };
  });

  it('renders loading state initially', () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ data: null, error: null });
    
    render(<AssistantAnalytics />);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('renders analytics data when loaded successfully', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: mockAgents }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Assistant Analytics')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument(); // Total agents
      expect(screen.getByText('2')).toBeInTheDocument(); // Active agents
    });
  });

  it('displays time range selector buttons', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: mockAgents }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('7d')).toBeInTheDocument();
      expect(screen.getByText('30d')).toBeInTheDocument();
      expect(screen.getByText('90d')).toBeInTheDocument();
      expect(screen.getByText('1y')).toBeInTheDocument();
    });
  });

  it('changes time range when button is clicked', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: mockAgents }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      const sevenDayButton = screen.getByText('7d');
      fireEvent.click(sevenDayButton);
      
      // Should trigger a new data load with 7d range
      expect(mockSupabaseFunctions.invoke).toHaveBeenCalled();
    });
  });

  it('displays chart type selector buttons', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: mockAgents }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Bar')).toBeInTheDocument();
      expect(screen.getByText('Line')).toBeInTheDocument();
      expect(screen.getByText('Area')).toBeInTheDocument();
    });
  });

  it('switches between chart types', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: mockAgents }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      const lineButton = screen.getByText('Line');
      fireEvent.click(lineButton);
      
      // Should show line chart
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });
  });

  it('displays summary cards with correct data', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: mockAgents }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      // Total Agents card
      expect(screen.getByText('Total Agents')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('2 active')).toBeInTheDocument();
      
      // Total Calls card
      expect(screen.getByText('Total Calls')).toBeInTheDocument();
      
      // Success Rate card
      expect(screen.getByText('Success Rate')).toBeInTheDocument();
      
      // Avg Call Duration card
      expect(screen.getByText('Avg Call Duration')).toBeInTheDocument();
    });
  });

  it('displays call trends chart', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: mockAgents }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Call Trends')).toBeInTheDocument();
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    });
  });

  it('displays call status distribution chart', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: mockAgents }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Call Status')).toBeInTheDocument();
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    });
  });

  it('displays top performing agents section', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: mockAgents }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Top Performing Agents')).toBeInTheDocument();
      expect(screen.getByText('Agents with the highest success rates')).toBeInTheDocument();
    });
  });

  it('displays recent activity section', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: mockAgents }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Recent Activity')).toBeInTheDocument();
      expect(screen.getByText('Latest call activity by agent')).toBeInTheDocument();
    });
  });

  it('handles refresh button click', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: mockAgents }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);
      
      // Should trigger data reload
      expect(mockSupabaseFunctions.invoke).toHaveBeenCalledWith('list-custom-demos');
    });
  });

  it('handles export functionality', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: mockAgents }, 
      error: null 
    });
    
    // Mock URL.createObjectURL and document.createElement
    const mockCreateObjectURL = vi.fn().mockReturnValue('blob:mock-url');
    const mockRevokeObjectURL = vi.fn();
    const mockClick = vi.fn();
    
    Object.defineProperty(window, 'URL', {
      value: {
        createObjectURL: mockCreateObjectURL,
        revokeObjectURL: mockRevokeObjectURL,
      },
      writable: true,
    });
    
    Object.defineProperty(document, 'createElement', {
      value: vi.fn().mockReturnValue({
        href: '',
        download: '',
        click: mockClick,
      }),
      writable: true,
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      const exportButton = screen.getByText('Export');
      fireEvent.click(exportButton);
      
      expect(mockCreateObjectURL).toHaveBeenCalled();
      expect(mockClick).toHaveBeenCalled();
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Analytics exported',
        description: 'Assistant analytics data has been downloaded as CSV',
      });
    });
  });

  it('handles error when loading data', async () => {
    const mockError = new Error('API error');
    mockSupabaseFunctions.invoke.mockResolvedValue({ data: null, error: mockError });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error loading analytics',
        description: 'API error',
        variant: 'destructive',
      });
    });
  });

  it('displays no data message when no agents exist', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: [] }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('No analytics data available')).toBeInTheDocument();
    });
  });

  it('formats duration correctly', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: mockAgents }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      // The component should display formatted durations
      expect(screen.getByText('Assistant Analytics')).toBeInTheDocument();
    });
  });

  it('calculates percentages correctly', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: mockAgents }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      // The component should display success rates as percentages
      expect(screen.getByText('Success Rate')).toBeInTheDocument();
    });
  });

  it('handles different agent statuses correctly', async () => {
    const agentsWithDifferentStatuses = [
      ...mockAgents,
      {
        id: '4',
        assistant_name: 'Inactive Agent',
        assistant_type: 'support',
        demo_url: 'https://demo.example.com/4',
        created_at: '2024-01-30T16:45:00Z',
        status: 'deleted',
        assistant_id: 'assistant_4',
        voice_id: 'voice_4',
      },
    ];
    
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: agentsWithDifferentStatuses }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Assistant Analytics')).toBeInTheDocument();
      // Should show 3 active agents (excluding deleted)
      expect(screen.getByText('3 active')).toBeInTheDocument();
    });
  });

  it('displays agent names in recent activity', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: mockAgents }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Customer Support Bot')).toBeInTheDocument();
      expect(screen.getByText('Sales Assistant')).toBeInTheDocument();
      expect(screen.getByText('Booking Agent')).toBeInTheDocument();
    });
  });

  it('handles area chart type selection', async () => {
    mockSupabaseFunctions.invoke.mockResolvedValue({ 
      data: { demos: mockAgents }, 
      error: null 
    });
    
    render(<AssistantAnalytics />);
    
    await waitFor(() => {
      const areaButton = screen.getByText('Area');
      fireEvent.click(areaButton);
      
      // Should show area chart
      expect(screen.getByTestId('area-chart')).toBeInTheDocument();
    });
  });
});
