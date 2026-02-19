import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import VoiceAgents from '@/pages/VoiceAgents';
import { AuthProvider } from '@/contexts/AuthContext';

// Mock Supabase with simplified structure
const mockSupabaseData = [
  {
    id: 'test-import-id',
    assistant_name: 'Test Imported Assistant',
    assistant_type: 'external',
    assistant_id: 'b601e2aa-c4e4-4d93-ae52-2389bb0d1042',
    demo_url: 'https://example.com/demo',
    created_at: '2025-01-21T10:00:00.000Z',
    status: 'active',
    external: true,
    user_id: 'test-user-id'
  },
  {
    id: 'test-created-id',
    assistant_name: 'Test Created Assistant',
    assistant_type: 'sales_cold_call',
    assistant_id: 'created-assistant-id',
    demo_url: 'https://example.com/demo2',
    created_at: '2025-01-21T09:00:00.000Z',
    status: 'active',
    external: false,
    user_id: 'test-user-id'
  }
];

vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          or: vi.fn(() => ({
            order: vi.fn(() => Promise.resolve({ data: mockSupabaseData }))
          }))
        }))
      }))
    })),
    functions: {
      invoke: vi.fn(() => Promise.resolve({
        data: {
          success: true,
          assistant: {
            id: 'b601e2aa-c4e4-4d93-ae52-2389bb0d1042',
            name: 'Test Imported Assistant',
            type: 'external',
            voice: { name: 'test-voice' },
            metadata: {}
          }
        }
      }))
    }
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
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate
  };
});

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {component}
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('VoiceAgents Import Display', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display imported assistants alongside created assistants', async () => {
    renderWithProviders(<VoiceAgents />);

    // Wait for the data to load
    await waitFor(() => {
      expect(screen.getByText('Test Imported Assistant')).toBeInTheDocument();
      expect(screen.getByText('Test Created Assistant')).toBeInTheDocument();
    });

    // Check that imported assistant has external badge
    expect(screen.getByText('External')).toBeInTheDocument();
  });

  it('should show import dialog when import button is clicked', async () => {
    renderWithProviders(<VoiceAgents />);

    // Wait for the page to load
    await waitFor(() => {
      expect(screen.getByText('Import Agent')).toBeInTheDocument();
    });

    // Click import button
    const importButton = screen.getByText('Import Agent');
    fireEvent.click(importButton);

    // Check that import dialog appears
    await waitFor(() => {
      expect(screen.getByText('Import Assistant from Vapi')).toBeInTheDocument();
    });
  });

  it('should handle import process correctly', async () => {
    renderWithProviders(<VoiceAgents />);

    // Wait for the page to load
    await waitFor(() => {
      expect(screen.getByText('Import Agent')).toBeInTheDocument();
    });

    // Click import button
    const importButton = screen.getByText('Import Agent');
    fireEvent.click(importButton);

    // Wait for dialog to appear
    await waitFor(() => {
      expect(screen.getByText('Import Assistant from Vapi')).toBeInTheDocument();
    });

    // Find and fill the assistant ID input
    const assistantIdInput = screen.getByPlaceholderText('Enter Vapi Assistant ID');
    fireEvent.change(assistantIdInput, {
      target: { value: 'b601e2aa-c4e4-4d93-ae52-2389bb0d1042' }
    });

    // Find and fill the custom URL input (optional)
    const urlInput = screen.getByPlaceholderText('https://your-website.com/assistant (optional)');
    fireEvent.change(urlInput, {
      target: { value: 'https://example.com/custom-demo' }
    });

    // Click import button in dialog
    const dialogImportButton = screen.getByText('Import Assistant');
    fireEvent.click(dialogImportButton);

    // Verify that the import function was called
    await waitFor(() => {
      const { supabase } = require('@/integrations/supabase/client');
      expect(supabase.functions.invoke).toHaveBeenCalledWith('fetch-assistant-details', {
        body: {
          assistant_id: 'b601e2aa-c4e4-4d93-ae52-2389bb0d1042',
          custom_url: 'https://example.com/custom-demo'
        }
      });
    });
  });

  it('should display correct assistant types for imported vs created assistants', async () => {
    renderWithProviders(<VoiceAgents />);

    // Wait for the data to load
    await waitFor(() => {
      expect(screen.getByText('Test Imported Assistant')).toBeInTheDocument();
      expect(screen.getByText('Test Created Assistant')).toBeInTheDocument();
    });

    // Check that imported assistant shows as external
    expect(screen.getByText('external')).toBeInTheDocument();
    
    // Check that created assistant shows correct type
    expect(screen.getByText('sales cold call')).toBeInTheDocument();
  });

  it('should handle search and filtering correctly', async () => {
    renderWithProviders(<VoiceAgents />);

    // Wait for the page to load
    await waitFor(() => {
      expect(screen.getByText('Test Imported Assistant')).toBeInTheDocument();
    });

    // Find search input
    const searchInput = screen.getByPlaceholderText('Search by name...');
    fireEvent.change(searchInput, { target: { value: 'Imported' } });

    // Should still show the imported assistant
    expect(screen.getByText('Test Imported Assistant')).toBeInTheDocument();

    // Search for something that doesn't exist
    fireEvent.change(searchInput, { target: { value: 'NonExistent' } });

    // Should not show any assistants
    await waitFor(() => {
      expect(screen.queryByText('Test Imported Assistant')).not.toBeInTheDocument();
    });
  });

  it('should handle filter by type correctly', async () => {
    renderWithProviders(<VoiceAgents />);

    // Wait for the page to load
    await waitFor(() => {
      expect(screen.getByText('Test Imported Assistant')).toBeInTheDocument();
      expect(screen.getByText('Test Created Assistant')).toBeInTheDocument();
    });

    // Find filter dropdown
    const filterDropdown = screen.getByText('All Types');
    fireEvent.click(filterDropdown);

    // Select external filter
    const externalOption = screen.getByText('external');
    fireEvent.click(externalOption);

    // Should only show external assistants
    expect(screen.getByText('Test Imported Assistant')).toBeInTheDocument();
    expect(screen.queryByText('Test Created Assistant')).not.toBeInTheDocument();
  });
});
