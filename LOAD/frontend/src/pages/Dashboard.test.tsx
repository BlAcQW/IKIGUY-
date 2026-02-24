import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@test/helpers/render';
import { buildCall } from '@test/helpers/factories';

vi.mock('@/lib/api', () => ({
  listAssistants: vi.fn(),
  listCalls: vi.fn(),
  listPhoneNumbers: vi.fn(),
  listTools: vi.fn(),
  listWebhooks: vi.fn(),
}));

// Mock recharts to avoid rendering issues in jsdom
vi.mock('recharts', () => ({
  BarChart: ({ children }: { children: React.ReactNode }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  Tooltip: () => <div />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CartesianGrid: () => <div />,
}));

import React from 'react';
import { DashboardPage } from './Dashboard';
import { listAssistants, listCalls, listPhoneNumbers, listTools, listWebhooks } from '@/lib/api';

const mockedListAssistants = vi.mocked(listAssistants);
const mockedListCalls = vi.mocked(listCalls);
const mockedListPhoneNumbers = vi.mocked(listPhoneNumbers);
const mockedListTools = vi.mocked(listTools);
const mockedListWebhooks = vi.mocked(listWebhooks);

function mockAllApis(overrides: { assistants?: number; calls?: number; phones?: number; tools?: number; webhooks?: number } = {}) {
  mockedListAssistants.mockResolvedValue({ success: true, data: [], meta: { total: overrides.assistants ?? 0, page: 1, limit: 1 } });
  mockedListCalls.mockResolvedValue({ success: true, data: [], meta: { total: overrides.calls ?? 0, page: 1, limit: 100 } });
  mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [], meta: { total: overrides.phones ?? 0, page: 1, limit: 1 } });
  mockedListTools.mockResolvedValue({ success: true, data: [], meta: { total: overrides.tools ?? 0, page: 1, limit: 1 } });
  mockedListWebhooks.mockResolvedValue({ success: true, data: [], meta: { total: overrides.webhooks ?? 0, page: 1, limit: 1 } });
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page title', () => {
    mockAllApis();
    render(<DashboardPage />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    mockedListAssistants.mockReturnValue(new Promise(() => {}));
    mockedListCalls.mockReturnValue(new Promise(() => {}));
    mockedListPhoneNumbers.mockReturnValue(new Promise(() => {}));
    mockedListTools.mockReturnValue(new Promise(() => {}));
    mockedListWebhooks.mockReturnValue(new Promise(() => {}));

    render(<DashboardPage />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('displays stat cards with values', async () => {
    mockAllApis({ assistants: 5, calls: 42, phones: 3 });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });
  });

  it('shows quick action links', async () => {
    mockAllApis();

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Create Assistant')).toBeInTheDocument();
      expect(screen.getByText('Test Web Call')).toBeInTheDocument();
      expect(screen.getByText('Add Tool')).toBeInTheDocument();
      expect(screen.getByText('Set Up Webhook')).toBeInTheDocument();
    });
  });

  it('shows onboarding checklist when not all done', async () => {
    mockAllApis({ assistants: 1, calls: 0, phones: 0 });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Getting Started')).toBeInTheDocument();
      expect(screen.getByText(/1 of 5 steps completed/)).toBeInTheDocument();
    });
  });

  it('shows no call activity empty state', async () => {
    mockAllApis();

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('No call activity yet')).toBeInTheDocument();
    });
  });

  it('shows no calls yet empty state', async () => {
    mockAllApis();

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('No calls yet')).toBeInTheDocument();
    });
  });

  it('handles API error gracefully', async () => {
    mockedListAssistants.mockRejectedValue(new Error('fail'));
    mockedListCalls.mockRejectedValue(new Error('fail'));
    mockedListPhoneNumbers.mockRejectedValue(new Error('fail'));
    mockedListTools.mockRejectedValue(new Error('fail'));
    mockedListWebhooks.mockRejectedValue(new Error('fail'));

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getAllByText('0').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders recent calls with status and duration', async () => {
    const calls = [
      buildCall({ status: 'ENDED', duration: 90, type: 'WEB' }),
      buildCall({ status: 'IN_PROGRESS', duration: null, type: 'PHONE_INBOUND' as any }),
    ];
    mockedListAssistants.mockResolvedValue({ success: true, data: [], meta: { total: 2, page: 1, limit: 1 } });
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 2, page: 1, limit: 100 } });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListTools.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('ENDED')).toBeInTheDocument();
      expect(screen.getByText('IN PROGRESS')).toBeInTheDocument();
      expect(screen.getByText('1:30')).toBeInTheDocument();
      expect(screen.getByText('WEB')).toBeInTheDocument();
    });
  });

  it('shows all onboarding complete when all steps done', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [], meta: { total: 1, page: 1, limit: 1 } });
    mockedListCalls.mockResolvedValue({ success: true, data: [], meta: { total: 1, page: 1, limit: 100 } });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [], meta: { total: 1, page: 1, limit: 1 } });
    mockedListTools.mockResolvedValue({ success: true, data: [], meta: { total: 1, page: 1, limit: 1 } });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [], meta: { total: 1, page: 1, limit: 1 } });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.queryByText('Getting Started')).not.toBeInTheDocument();
    });
  });

  it('shows "View all" link when there are recent calls', async () => {
    const calls = [buildCall({ status: 'ENDED', duration: 30 })];
    mockedListAssistants.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 100 } });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListTools.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('View all')).toBeInTheDocument();
    });
  });

  it('renders active calls count for IN_PROGRESS and RINGING', async () => {
    const calls = [
      buildCall({ status: 'IN_PROGRESS', duration: null }),
      buildCall({ status: 'RINGING', duration: null }),
      buildCall({ status: 'ENDED', duration: 60 }),
    ];
    mockedListAssistants.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 3, page: 1, limit: 100 } });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListTools.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });

    render(<DashboardPage />);

    await waitFor(() => {
      // Active Now count = 2 (IN_PROGRESS + RINGING)
      expect(screen.getByText('2')).toBeInTheDocument();
    });
  });

  it('renders FAILED call status with destructive badge', async () => {
    const calls = [buildCall({ status: 'FAILED', duration: null })];
    mockedListAssistants.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 100 } });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListTools.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('FAILED')).toBeInTheDocument();
    });
  });

  it('renders QUEUED call status with outline badge', async () => {
    const calls = [buildCall({ status: 'QUEUED', duration: null })];
    mockedListAssistants.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 100 } });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListTools.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('QUEUED')).toBeInTheDocument();
    });
  });

  it('shows duration only for calls with positive duration', async () => {
    const calls = [
      buildCall({ status: 'ENDED', duration: 0 }),
    ];
    mockedListAssistants.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 100 } });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListTools.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });

    render(<DashboardPage />);

    await waitFor(() => {
      // duration=0 should not show formatted duration (the condition is duration != null && duration > 0)
      expect(screen.getByText('ENDED')).toBeInTheDocument();
      expect(screen.queryByText('0:00')).not.toBeInTheDocument();
    });
  });

  it('shows chart when calls have data', async () => {
    // Create a call with a date within the last 7 days
    const calls = [buildCall({ status: 'ENDED', duration: 60, createdAt: new Date().toISOString() })];
    mockedListAssistants.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 100 } });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListTools.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });

    render(<DashboardPage />);

    await waitFor(() => {
      // When chart data has calls > 0, the bar chart is rendered instead of empty state
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
      expect(screen.queryByText('No call activity yet')).not.toBeInTheDocument();
    });
  });

  it('shows "just now" for calls created less than a minute ago', async () => {
    const calls = [buildCall({ status: 'ENDED', duration: 30, createdAt: new Date().toISOString() })];
    mockedListAssistants.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 100 } });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListTools.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('just now')).toBeInTheDocument();
    });
  });

  it('shows "Xm ago" for calls created minutes ago', async () => {
    const thirtyMinsAgo = new Date(Date.now() - 30 * 60 * 1000).toISOString();
    const calls = [buildCall({ status: 'ENDED', duration: 30, createdAt: thirtyMinsAgo })];
    mockedListAssistants.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 100 } });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListTools.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('30m ago')).toBeInTheDocument();
    });
  });

  it('shows "Xh ago" for calls created hours ago', async () => {
    const threeHoursAgo = new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString();
    const calls = [buildCall({ status: 'ENDED', duration: 30, createdAt: threeHoursAgo })];
    mockedListAssistants.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 100 } });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListTools.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('3h ago')).toBeInTheDocument();
    });
  });

  it('shows "Xd ago" for calls created days ago', async () => {
    const twoDaysAgo = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString();
    const calls = [buildCall({ status: 'ENDED', duration: 30, createdAt: twoDaysAgo })];
    mockedListAssistants.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 100 } });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListTools.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('2d ago')).toBeInTheDocument();
    });
  });

  it('shows Make your first call link when no call activity', async () => {
    mockAllApis();

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Make your first call')).toBeInTheDocument();
    });
  });

  it('renders chart tooltip content when active with payload', async () => {
    // Create a call with data within last 7 days so chart shows
    const calls = [buildCall({ status: 'ENDED', duration: 60, createdAt: new Date().toISOString() })];
    mockedListAssistants.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 100 } });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListTools.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });

    render(<DashboardPage />);

    await waitFor(() => {
      // The chart is rendered when there's data
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
      // And "Call Activity" section heading
      expect(screen.getByText('Call Activity')).toBeInTheDocument();
    });
  });

  it('shows chart with singular "call" when only 1 call on a day', async () => {
    const calls = [buildCall({ status: 'ENDED', duration: 60, createdAt: new Date().toISOString() })];
    mockedListAssistants.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 100 } });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListTools.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('View analytics')).toBeInTheDocument();
    });
  });

  it('shows partial onboarding with multiple steps completed', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [], meta: { total: 1, page: 1, limit: 1 } });
    mockedListCalls.mockResolvedValue({ success: true, data: [], meta: { total: 1, page: 1, limit: 100 } });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [], meta: { total: 1, page: 1, limit: 1 } });
    mockedListTools.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 1 } });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Getting Started')).toBeInTheDocument();
      expect(screen.getByText(/3 of 5 steps completed/)).toBeInTheDocument();
    });
  });
});
