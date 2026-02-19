import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import VoiceAgents from '@/pages/VoiceAgents';
import { useAuth } from '@/contexts/AuthContext';
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

// Mock AuthContext
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

// Mock Supabase client
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    functions: {
      invoke: vi.fn(),
    },
  },
}));

// Mock useToast hook
vi.mock('@/components/ui/use-toast', () => ({
  useToast: vi.fn(),
}));

const renderVoiceAgents = () => {
  return render(
    <BrowserRouter>
      <VoiceAgents />
    </BrowserRouter>
  );
};

describe('Preview Button Functionality', () => {
  const mockToast = vi.fn();
  const mockSupabaseInvoke = vi.mocked(supabase.functions.invoke);

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue({ toast: mockToast });
    (useAuth as any).mockReturnValue({
      user: { id: 'test-user-id', email: 'test@example.com' },
      loading: false,
    });
  });

  it('should navigate to demo preview when preview button is clicked', async () => {
    // Mock the list-custom-demos function response
    const mockDemo = {
      id: '1',
      assistant_name: 'Test Assistant',
      assistant_type: 'customer_support',
      assistant_id: 'assistant-123',
      demo_url: 'https://demo.example.com',
      created_at: '2024-01-15T10:00:00Z',
      status: 'active',
      voice_id: 'voice-123',
    };

    mockSupabaseInvoke.mockResolvedValue({
      data: { demos: [mockDemo] },
      error: null,
    });

    renderVoiceAgents();

    // Wait for the demo to load
    await waitFor(() => {
      expect(screen.getByText('Test Assistant')).toBeInTheDocument();
    });

    // Find and click the preview button
    const previewButton = screen.getByText('Preview Demo');
    fireEvent.click(previewButton);

    // Verify navigation was called with correct URL
    expect(mockNavigate).toHaveBeenCalledWith('/demo-preview?id=assistant-123');
  });

  it('should handle missing assistant_id gracefully', async () => {
    // Mock the list-custom-demos function response with missing assistant_id
    const mockDemo = {
      id: '1',
      assistant_name: 'Test Assistant',
      assistant_type: 'customer_support',
      assistant_id: undefined, // Missing assistant_id
      demo_url: 'https://demo.example.com',
      created_at: '2024-01-15T10:00:00Z',
      status: 'active',
      voice_id: 'voice-123',
    };

    mockSupabaseInvoke.mockResolvedValue({
      data: { demos: [mockDemo] },
      error: null,
    });

    renderVoiceAgents();

    // Wait for the demo to load
    await waitFor(() => {
      expect(screen.getByText('Test Assistant')).toBeInTheDocument();
    });

    // Find and click the preview button
    const previewButton = screen.getByText('Preview Demo');
    fireEvent.click(previewButton);

    // Verify navigation was called with undefined id
    expect(mockNavigate).toHaveBeenCalledWith('/demo-preview?id=undefined');
  });

  it('should handle API errors gracefully', async () => {
    // Mock API error
    mockSupabaseInvoke.mockResolvedValue({
      data: null,
      error: { message: 'API Error' },
    });

    renderVoiceAgents();

    // Wait for error toast
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Failed to load',
        description: 'API Error',
        variant: 'destructive',
      });
    });
  });
});
