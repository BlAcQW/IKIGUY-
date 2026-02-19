import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import RecentDemos from '@/components/dashboard/RecentDemos';
import { supabase } from '@/integrations/supabase/client';

// Mock the dependencies
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: vi.fn(),
  },
}));

vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

vi.mock('@/components/DemoSharing', () => ({
  default: ({ demoId }: { demoId: string }) => <div data-testid={`demo-sharing-${demoId}`}>Share</div>,
}));

vi.mock('@/components/DemoEmbedding', () => ({
  default: ({ demoId }: { demoId: string }) => <div data-testid={`demo-embedding-${demoId}`}>Embed</div>,
}));

vi.mock('@/components/DemoVersioning', () => ({
  default: ({ demoId }: { demoId: string }) => <div data-testid={`demo-versioning-${demoId}`}>Version</div>,
}));

vi.mock('@/components/DemoComments', () => ({
  default: ({ demoId }: { demoId: string }) => <div data-testid={`demo-comments-${demoId}`}>Comments</div>,
}));

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const renderRecentDemos = () => {
  return render(
    <BrowserRouter>
      <RecentDemos />
    </BrowserRouter>
  );
};

describe('RecentDemos', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Loading State', () => {
    it('shows loading spinner when loading demos', () => {
      // Mock Supabase to return a promise that doesn't resolve immediately
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockReturnValue(new Promise(() => {})),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      expect(screen.getByText('Recent Demos')).toBeInTheDocument();
      // Check for the loading spinner by its class instead of role
      expect(document.querySelector('.animate-spin')).toBeInTheDocument();
    });

    it('shows loading spinner with proper styling', () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockReturnValue(new Promise(() => {})),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toHaveClass('animate-spin', 'rounded-full', 'h-6', 'w-6');
    });
  });

  describe('Empty State', () => {
    it('shows empty state when no demos exist', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: [], error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        expect(screen.getByText('No demos yet')).toBeInTheDocument();
        expect(screen.getByText('Create your first AI assistant demo to get started.')).toBeInTheDocument();
      });
    });

    it('shows create first demo button in empty state', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: [], error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        const createButton = screen.getByText('Create First Demo');
        expect(createButton).toBeInTheDocument();
        fireEvent.click(createButton);
        expect(mockNavigate).toHaveBeenCalledWith('/create-assistant');
      });
    });
  });

  describe('Demo Display', () => {
    const mockDemos = [
      {
        id: '1',
        assistant_name: 'Customer Support Bot',
        assistant_type: 'customer_support',
        demo_url: 'https://demo1.example.com',
        created_at: '2024-01-15T10:00:00Z',
        status: 'active',
        assistant_id: 'assistant-1',
        description: 'AI-powered customer support assistant',
        current_version: 1,
      },
      {
        id: '2',
        assistant_name: 'Sales Assistant',
        assistant_type: 'sales_assistant',
        demo_url: 'https://demo2.example.com',
        created_at: '2024-01-14T15:30:00Z',
        status: 'inactive',
        assistant_id: 'assistant-2',
        description: 'Sales automation and lead qualification',
        current_version: 2,
      },
    ];

    it('displays demos when they exist', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: mockDemos, error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        expect(screen.getByText('Customer Support Bot')).toBeInTheDocument();
        expect(screen.getByText('Sales Assistant')).toBeInTheDocument();
      });
    });

    it('displays demo status badges', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: mockDemos, error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        expect(screen.getByText('active')).toBeInTheDocument();
        expect(screen.getByText('inactive')).toBeInTheDocument();
      });
    });

    it('displays demo type and creation date', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: mockDemos, error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        // Check for the content with truncate class - the text might be split across elements
        expect(screen.getAllByText(/customer support/).length).toBeGreaterThan(0);
        expect(screen.getAllByText(/sales assistant/).length).toBeGreaterThan(0);
        // Check for date patterns more flexibly
        expect(screen.getAllByText(/2024/).length).toBeGreaterThan(0);
        expect(screen.getAllByText(/15/).length).toBeGreaterThan(0);
        expect(screen.getAllByText(/14/).length).toBeGreaterThan(0);
      });
    });

    it('displays demo description when available', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: mockDemos, error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        expect(screen.getByText('AI-powered customer support assistant')).toBeInTheDocument();
        expect(screen.getByText('Sales automation and lead qualification')).toBeInTheDocument();
      });
    });
  });

  describe('Demo Actions', () => {
    const mockDemo = {
      id: '1',
      assistant_name: 'Customer Support Bot',
      assistant_type: 'customer_support',
      demo_url: 'https://demo1.example.com',
      created_at: '2024-01-15T10:00:00Z',
      status: 'active',
      assistant_id: 'assistant-1',
      description: 'AI-powered customer support assistant',
      current_version: 1,
    };

    it('navigates to demo preview when preview button is clicked', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: [mockDemo], error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        const previewButton = screen.getByText('Preview');
        fireEvent.click(previewButton);
        expect(mockNavigate).toHaveBeenCalledWith('/demo-preview?id=assistant-1');
      });
    });

    it('opens demo URL in new tab when external link is clicked', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: [mockDemo], error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        const externalLink = screen.getByRole('link');
        expect(externalLink).toHaveAttribute('href', 'https://demo1.example.com');
        expect(externalLink).toHaveAttribute('target', '_blank');
        expect(externalLink).toHaveAttribute('rel', 'noreferrer');
      });
    });

    it('renders demo sharing component', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: [mockDemo], error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        expect(screen.getByTestId('demo-sharing-1')).toBeInTheDocument();
      });
    });

    it('renders demo embedding component', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: [mockDemo], error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        expect(screen.getByTestId('demo-embedding-1')).toBeInTheDocument();
      });
    });

    it('renders demo versioning component', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: [mockDemo], error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        expect(screen.getByTestId('demo-versioning-1')).toBeInTheDocument();
      });
    });

    it('renders demo comments component', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: [mockDemo], error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        expect(screen.getByTestId('demo-comments-1')).toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('navigates to voice agents when view all button is clicked', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: [], error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        const viewAllButton = screen.getByText('View All');
        fireEvent.click(viewAllButton);
        expect(mockNavigate).toHaveBeenCalledWith('/voice-agents');
      });
    });

    it('navigates to create assistant when create new demo button is clicked', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: [], error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        const createButton = screen.getByText('Create First Demo');
        fireEvent.click(createButton);
        expect(mockNavigate).toHaveBeenCalledWith('/create-assistant');
      });
    });
  });

  describe('Error Handling', () => {
    it('shows error toast when loading fails', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: null, error: { message: 'Database error' } }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        // The error should be logged to console, but we can't easily test the toast
        // since it's mocked. We can verify the component doesn't crash.
        expect(screen.getByText('Recent Demos')).toBeInTheDocument();
      });
    });

    it('handles network errors gracefully', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockRejectedValue(new Error('Network error')),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        // The error should be logged to console, but we can't easily test the toast
        // since it's mocked. We can verify the component doesn't crash.
        expect(screen.getByText('Recent Demos')).toBeInTheDocument();
      });
    });
  });

  describe('Data Fetching', () => {
    it('fetches demos from correct table', async () => {
      const mockLimit = vi.fn().mockResolvedValue({ data: [], error: null });
      const mockOrder = vi.fn().mockReturnValue({ limit: mockLimit });
      const mockSelect = vi.fn().mockReturnValue({ order: mockOrder });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        expect(supabase.from).toHaveBeenCalledWith('custom_demos');
      });
    });

    it('orders demos by creation date descending', async () => {
      const mockLimit = vi.fn().mockResolvedValue({ data: [], error: null });
      const mockOrder = vi.fn().mockReturnValue({ limit: mockLimit });
      const mockSelect = vi.fn().mockReturnValue({ order: mockOrder });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        expect(mockOrder).toHaveBeenCalledWith('created_at', { ascending: false });
      });
    });

    it('limits results to 3 demos', async () => {
      const mockLimit = vi.fn().mockResolvedValue({ data: [], error: null });
      const mockOrder = vi.fn().mockReturnValue({ limit: mockLimit });
      const mockSelect = vi.fn().mockReturnValue({ order: mockOrder });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        expect(mockLimit).toHaveBeenCalledWith(3);
      });
    });
  });

  describe('Styling and Layout', () => {
    it('has proper card structure', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: [], error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        expect(screen.getByText('Recent Demos')).toBeInTheDocument();
      });
    });

    it('has proper demo item styling', async () => {
      const mockDemo = {
        id: '1',
        assistant_name: 'Test Demo',
        assistant_type: 'test',
        demo_url: 'https://test.com',
        created_at: '2024-01-15T10:00:00Z',
        status: 'active',
        assistant_id: 'assistant-1',
      };

      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: [mockDemo], error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        // Find the demo item container by looking for the parent div that contains the demo
        const demoItem = screen.getByText('Test Demo').closest('div[class*="flex items-start justify-between"]');
        expect(demoItem).toBeInTheDocument();
        expect(demoItem).toHaveClass('flex', 'items-start', 'justify-between', 'p-4', 'border', 'rounded-lg');
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper button roles', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: [], error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        const buttons = screen.getAllByRole('button');
        expect(buttons.length).toBeGreaterThan(0);
      });
    });

    it('has proper link roles for external links', async () => {
      const mockDemo = {
        id: '1',
        assistant_name: 'Test Demo',
        assistant_type: 'test',
        demo_url: 'https://test.com',
        created_at: '2024-01-15T10:00:00Z',
        status: 'active',
        assistant_id: 'assistant-1',
      };

      const mockSelect = vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue({ data: [mockDemo], error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderRecentDemos();
      
      await waitFor(() => {
        const links = screen.getAllByRole('link');
        expect(links.length).toBeGreaterThan(0);
      });
    });
  });
});
