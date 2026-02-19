import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import Discussions from '../Discussions';
import { apiClient } from '@/lib/api';

// Mock the API client
vi.mock('@/lib/api', () => ({
  apiClient: {
    client: {
      get: vi.fn(),
    },
  },
}));

// Mock useAuth
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 'test-user', name: 'Test User' },
  }),
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe('Discussions Page', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = createTestQueryClient();
    vi.clearAllMocks();
  });

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Discussions />
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  it('renders the discussions page', () => {
    (apiClient.client.get as any).mockResolvedValue({
      data: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
    });

    renderComponent();
    expect(screen.getByText('Group Discussions')).toBeInTheDocument();
  });

  it('displays loading state', () => {
    (apiClient.client.get as any).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    renderComponent();
    expect(screen.getByText(/loading discussions/i)).toBeInTheDocument();
  });

  it('displays discussions when loaded', async () => {
    const mockDiscussions = {
      items: [
        {
          id: '1',
          title: 'Test Discussion',
          description: 'Test description',
          author_name: 'Test Author',
          participants_count: 5,
          messages_count: 10,
          last_activity_at: new Date().toISOString(),
          created_at: new Date().toISOString(),
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };

    (apiClient.client.get as any).mockResolvedValue({
      data: mockDiscussions,
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Test Discussion')).toBeInTheDocument();
    });
  });

  it('displays empty state when no discussions', async () => {
    (apiClient.client.get as any).mockResolvedValue({
      data: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText(/no discussions yet/i)).toBeInTheDocument();
    });
  });
});

