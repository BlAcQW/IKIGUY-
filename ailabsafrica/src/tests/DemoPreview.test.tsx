import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import DemoPreview from '@/pages/DemoPreview';
import { AuthProvider } from '@/contexts/AuthContext';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/components/ui/use-toast';

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock Supabase client
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: vi.fn(),
  },
}));

// Mock useToast hook
vi.mock('@/components/ui/use-toast', () => ({
  useToast: vi.fn(),
}));

// Mock useDemoAnalytics hook
vi.mock('@/hooks/useDemoAnalytics', () => ({
  useDemoAnalytics: vi.fn(() => ({
    startSession: vi.fn(),
    trackInteraction: vi.fn(),
    trackShare: vi.fn(),
    trackEmbed: vi.fn(),
    trackComment: vi.fn(),
  })),
}));

const renderDemoPreview = (initialEntries = ['/demo-preview']) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <AuthProvider>
        <DemoPreview />
      </AuthProvider>
    </MemoryRouter>
  );
};

describe('DemoPreview Component', () => {
  const mockToast = vi.fn();
  const mockSupabaseFrom = vi.mocked(supabase.from);

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue({ toast: mockToast });
  });

  it('should show loading state initially', () => {
    renderDemoPreview();
    expect(screen.getByText('Loading demo...')).toBeInTheDocument();
  });

  it('should handle demo preview with HTML content', async () => {
    const htmlContent = '<html><head><title>Test Assistant - Demo</title></head><body>Test content</body></html>';
    const encodedHtml = encodeURIComponent(htmlContent);
    
    renderDemoPreview([`/demo-preview?html=${encodedHtml}`]);

    await waitFor(() => {
      expect(screen.getByText('Demo Preview: Test Assistant')).toBeInTheDocument();
    });
  });

  it('should handle demo preview with assistant ID', async () => {
    const mockDemoData = {
      id: '1',
      assistant_name: 'Test Assistant',
      assistant_type: 'customer_support',
      description: 'Test description',
      demo_url: 'https://demo.example.com',
      current_version: 1,
    };

    const mockSelect = vi.fn().mockReturnValue({
      eq: vi.fn().mockReturnValue({
        maybeSingle: vi.fn().mockResolvedValue({
          data: mockDemoData,
          error: null,
        }),
      }),
    });

    mockSupabaseFrom.mockReturnValue({
      select: mockSelect,
    } as any);

    // Mock fetch for demo URL
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: vi.fn().mockResolvedValue('<html><body>Demo content</body></html>'),
    });

    renderDemoPreview(['/demo-preview?id=assistant-123']);

    await waitFor(() => {
      expect(screen.getByText('Demo Preview: Test Assistant')).toBeInTheDocument();
    });
  });

  it('should handle missing demo data gracefully', async () => {
    const mockSelect = vi.fn().mockReturnValue({
      eq: vi.fn().mockReturnValue({
        maybeSingle: vi.fn().mockResolvedValue({
          data: null,
          error: null,
        }),
      }),
    });

    mockSupabaseFrom.mockReturnValue({
      select: mockSelect,
    } as any);

    renderDemoPreview(['/demo-preview?id=invalid-id']);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'No demo found',
        description: 'This assistant doesn\'t have a demo page yet',
        variant: 'destructive',
      });
    });
  });

  it('should handle database errors gracefully', async () => {
    const mockSelect = vi.fn().mockReturnValue({
      eq: vi.fn().mockReturnValue({
        maybeSingle: vi.fn().mockResolvedValue({
          data: null,
          error: { message: 'Database error' },
        }),
      }),
    });

    mockSupabaseFrom.mockReturnValue({
      select: mockSelect,
    } as any);

    renderDemoPreview(['/demo-preview?id=assistant-123']);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'Database error',
        variant: 'destructive',
      });
    });
  });

  it('should show demo not found when no content is available', async () => {
    renderDemoPreview(['/demo-preview']);

    await waitFor(() => {
      expect(screen.getByText('Demo Not Found')).toBeInTheDocument();
      expect(screen.getByText('The requested demo could not be loaded. It may have been deleted or the link is invalid.')).toBeInTheDocument();
    });
  });
});
