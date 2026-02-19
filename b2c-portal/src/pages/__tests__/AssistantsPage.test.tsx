import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import Assistants from '../Assistants';
import { vi } from 'vitest';
import { supabase } from '@/integrations/supabase/client';
import { assistantApi } from '@/lib/core-api';

const mockToast = vi.fn();

vi.mock('@/components/dashboard/DashboardSidebar', () => ({ DashboardSidebar: () => <div>Sidebar</div> }));
vi.mock('@/components/assistants/AssistantBuilderDialog', () => ({ AssistantBuilderDialog: ({ children }: any) => <div>{children}</div> }));
vi.mock('@/components/assistants/TestSandboxDialog', () => ({ default: ({ children }: any) => <div>{children}</div> }));
vi.mock('@/components/ProtectedRoute', () => ({ ProtectedRoute: ({ children }: any) => <>{children}</> }));
vi.mock('@/hooks/use-toast', () => ({ useToast: () => ({ toast: mockToast }) }));

vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    auth: {
      getUser: vi.fn()
    }
  }
}));

vi.mock('@/lib/core-api', () => ({
  assistantApi: {
    list: vi.fn()
  }
}));

describe('AssistantsPage', () => {
  beforeEach(() => {
    mockToast.mockReset();
    (supabase.auth.getUser as any).mockReset();
    (assistantApi.list as any).mockReset();
  });

  it('renders assistants on success', async () => {
    (supabase.auth.getUser as any).mockResolvedValue({ data: { user: { id: 'u1' } } });
    (assistantApi.list as any).mockResolvedValue([{ id: 'a1', name: 'Assistant One', channel: 'voice', status: 'active', stats: {} }]);

    render(<Assistants />);

    await waitFor(() => expect(screen.getByText('Assistant One')).toBeInTheDocument());
  });

  it('shows message when no assistants found', async () => {
    (supabase.auth.getUser as any).mockResolvedValue({ data: { user: { id: 'u1' } } });
    (assistantApi.list as any).mockResolvedValue([]);

    render(<Assistants />);

    await waitFor(() => expect(screen.getByText('No assistants found')).toBeInTheDocument());
  });

  it('shows toast on load error', async () => {
    (supabase.auth.getUser as any).mockResolvedValue({ data: { user: { id: 'u1' } } });
    (assistantApi.list as any).mockRejectedValue(new Error('fail'));

    render(<Assistants />);

    await waitFor(() => expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({ title: 'Error loading assistants' })));
  });
});
