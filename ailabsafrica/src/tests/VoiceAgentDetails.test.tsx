import { render, screen, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import VoiceAgentDetails from '@/pages/VoiceAgentDetails';
import { AuthProvider } from '@/contexts/AuthContext';

// Mock data
const mockAgent = {
  id: 'test-agent-id',
  name: 'Test Voice Agent',
  description: 'A test voice agent for testing purposes',
  status: 'active',
  vapi_assistant_id: 'vapi-assistant-123',
  created_at: '2025-01-21T10:00:00.000Z',
  updated_at: '2025-01-21T10:00:00.000Z',
  user_id: 'test-user-id'
};

const mockCalls = [
  {
    id: 'call-1',
    vapi_call_id: 'vapi-call-123',
    voice_agent_id: 'test-agent-id',
    user_id: 'test-user-id',
    status: 'completed',
    start_time: '2025-01-21T10:00:00.000Z',
    end_time: '2025-01-21T10:05:00.000Z',
    duration_minutes: 5,
    total_cost: 0.25,
    communication_medium: 'phone',
    transcript: 'AI: Hello, how can I help you today? User: I need assistance with my order.',
    summary: 'Customer requested assistance with their order.',
    created_at: '2025-01-21T10:00:00.000Z'
  }
];

const mockAnalytics = {
  total_calls: 1,
  total_duration: 5,
  total_cost: 0.25,
  success_rate: 100,
  average_duration: 5,
  calls_by_status: [{ status: 'completed', count: 1 }],
  calls_by_medium: [{ medium: 'phone', count: 1 }],
  daily_calls: [{ date: '1/21/2025', count: 1 }],
  cost_trend: [{ date: '1/21/2025', cost: 0.25 }]
};

// Mock Supabase
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          single: vi.fn(() => Promise.resolve({ data: mockAgent })),
          order: vi.fn(() => Promise.resolve({ data: mockCalls }))
        }))
      }))
    }))
  }
}));

// Mock useAuth hook
const mockUser = {
  id: 'test-user-id',
  email: 'test@example.com'
};

vi.mock('@/contexts/AuthContext', async () => {
  const actual = await vi.importActual('@/contexts/AuthContext');
  return {
    ...actual,
    useAuth: () => ({
      user: mockUser,
      loading: false
    })
  };
});

// Mock useToast
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

// Mock recharts
vi.mock('recharts', () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
  PieChart: ({ children }: { children: React.ReactNode }) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />
}));

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/voice-agents/:id" element={component} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('VoiceAgentDetails', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    renderWithProviders(<VoiceAgentDetails />);
    
    expect(screen.getByText('Loading agent details...')).toBeInTheDocument();
  });

  it('renders agent details after loading', async () => {
    renderWithProviders(<VoiceAgentDetails />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Voice Agent')).toBeInTheDocument();
    });
    
    expect(screen.getByText('A test voice agent for testing purposes')).toBeInTheDocument();
    expect(screen.getByText('active')).toBeInTheDocument();
  });

  it('renders analytics overview cards', async () => {
    renderWithProviders(<VoiceAgentDetails />);
    
    await waitFor(() => {
      expect(screen.getByText('Total Calls')).toBeInTheDocument();
      expect(screen.getByText('Total Duration')).toBeInTheDocument();
      expect(screen.getByText('Total Cost')).toBeInTheDocument();
      expect(screen.getByText('Success Rate')).toBeInTheDocument();
    });
  });

  it('renders tabs for different sections', async () => {
    renderWithProviders(<VoiceAgentDetails />);
    
    await waitFor(() => {
      expect(screen.getByText('Analytics')).toBeInTheDocument();
      expect(screen.getByText('Call History')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });
  });

  it('renders back button', async () => {
    renderWithProviders(<VoiceAgentDetails />);
    
    await waitFor(() => {
      expect(screen.getByText('Back to Voice Agents')).toBeInTheDocument();
    });
  });

  it('renders call history table', async () => {
    renderWithProviders(<VoiceAgentDetails />);
    
    await waitFor(() => {
      expect(screen.getByText('Call History')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Start Time')).toBeInTheDocument();
      expect(screen.getByText('Duration')).toBeInTheDocument();
      expect(screen.getByText('Cost')).toBeInTheDocument();
      expect(screen.getByText('Medium')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });
  });

  it('shows completed call in the table', async () => {
    renderWithProviders(<VoiceAgentDetails />);
    
    await waitFor(() => {
      expect(screen.getByText('completed')).toBeInTheDocument();
      expect(screen.getByText('phone')).toBeInTheDocument();
    });
  });

  it('renders agent configuration in settings tab', async () => {
    renderWithProviders(<VoiceAgentDetails />);
    
    await waitFor(() => {
      expect(screen.getByText('Agent Configuration')).toBeInTheDocument();
      expect(screen.getByText('Vapi Assistant ID')).toBeInTheDocument();
      expect(screen.getByText('vapi-assistant-123')).toBeInTheDocument();
    });
  });
});
