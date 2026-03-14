import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@test/helpers/render';
import { buildCall } from '@test/helpers/factories';

vi.mock('@/lib/api', () => ({
  listCalls: vi.fn(),
  getCall: vi.fn(),
}));

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { CallsPage } from './Calls';
import { listCalls, getCall } from '@/lib/api';

const mockedListCalls = vi.mocked(listCalls);
const mockedGetCall = vi.mocked(getCall);

describe('CallsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page title', () => {
    mockedListCalls.mockReturnValue(new Promise(() => {}));
    render(<CallsPage />);
    expect(screen.getByText('Call History')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    mockedListCalls.mockReturnValue(new Promise(() => {}));
    render(<CallsPage />);
    // Skeleton placeholders are rendered (no table yet)
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('shows empty state when no calls', async () => {
    mockedListCalls.mockResolvedValue({ success: true, data: [], meta: { total: 0, page: 1, limit: 20 } });

    render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('No calls yet')).toBeInTheDocument();
    });
  });

  it('renders table with calls data', async () => {
    const calls = [
      buildCall({ id: 'call-001-test-test', type: 'WEB', status: 'ENDED', duration: 120 }),
      buildCall({ id: 'call-002-test-test', type: 'INBOUND', status: 'FAILED', duration: null }),
    ];
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 2, page: 1, limit: 20 } });

    render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('call-001...')).toBeInTheDocument();
      expect(screen.getByText('call-002...')).toBeInTheDocument();
    });
  });

  it('formats duration correctly', async () => {
    const calls = [buildCall({ id: 'test-call-fmt-test', duration: 90 })];
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 20 } });

    render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('1:30')).toBeInTheDocument();
    });
  });

  it('shows -- for null duration', async () => {
    const calls = [buildCall({ id: 'test-null-dur-test', duration: null })];
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 20 } });

    render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('--')).toBeInTheDocument();
    });
  });

  it('expands row on click to show details', async () => {
    const call = buildCall({ id: 'expand-call-test1', endReason: 'user-hangup', cost: '0.0500' });
    mockedListCalls.mockResolvedValue({ success: true, data: [call], meta: { total: 1, page: 1, limit: 20 } });
    mockedGetCall.mockResolvedValue({ success: true, data: call });

    const { user } = render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('expand-c...')).toBeInTheDocument();
    });

    await user.click(screen.getByText('expand-c...'));

    await waitFor(() => {
      expect(mockedGetCall).toHaveBeenCalledWith('expand-call-test1');
      expect(screen.getByText('user-hangup')).toBeInTheDocument();
      expect(screen.getByText('$0.0500')).toBeInTheDocument();
    });
  });

  it('shows status badges', async () => {
    const calls = [buildCall({ id: 'status-badge-test', status: 'IN_PROGRESS' })];
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 20 } });

    render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('IN PROGRESS')).toBeInTheDocument();
    });
  });

  it('shows pagination controls when total exceeds limit', async () => {
    const calls = Array.from({ length: 20 }, (_, i) =>
      buildCall({ id: `pag-call-${String(i).padStart(4, '0')}-test`, status: 'ENDED' }),
    );
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 45, page: 1, limit: 20 } });

    render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 3 (45 total)')).toBeInTheDocument();
      expect(screen.getByText('Previous')).toBeInTheDocument();
      expect(screen.getByText('Next')).toBeInTheDocument();
    });
  });

  it('disables Previous button on first page', async () => {
    const calls = [buildCall({ id: 'pag-prev-disabled', status: 'ENDED' })];
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 45, page: 1, limit: 20 } });

    render(<CallsPage />);

    await waitFor(() => {
      const prevBtn = screen.getByText('Previous').closest('button');
      expect(prevBtn).toBeDisabled();
    });
  });

  it('navigates to next page when Next is clicked', async () => {
    const calls = [buildCall({ id: 'pag-next-click1', status: 'ENDED' })];
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 45, page: 1, limit: 20 } });

    const { user } = render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('Next')).toBeInTheDocument();
    });

    // Reset to track second call
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 45, page: 2, limit: 20 } });

    await user.click(screen.getByText('Next'));

    await waitFor(() => {
      // listCalls should be called with page=2
      expect(mockedListCalls).toHaveBeenCalledWith(2, 20);
    });
  });

  it('collapses expanded row when clicking again', async () => {
    const call = buildCall({ id: 'collapse-call01', endReason: 'user-hangup', cost: '0.0500' });
    mockedListCalls.mockResolvedValue({ success: true, data: [call], meta: { total: 1, page: 1, limit: 20 } });
    mockedGetCall.mockResolvedValue({ success: true, data: call });

    const { user } = render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('collapse...')).toBeInTheDocument();
    });

    // Expand
    await user.click(screen.getByText('collapse...'));
    await waitFor(() => {
      expect(screen.getByText('user-hangup')).toBeInTheDocument();
    });

    // Collapse
    await user.click(screen.getByText('collapse...'));
    await waitFor(() => {
      expect(screen.queryByText('user-hangup')).not.toBeInTheDocument();
    });
  });

  it('shows FAILED status with destructive badge', async () => {
    const calls = [buildCall({ id: 'fail-badge-test', status: 'FAILED' })];
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 20 } });

    render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('FAILED')).toBeInTheDocument();
    });
  });

  it('shows QUEUED status with outline badge', async () => {
    const calls = [buildCall({ id: 'queued-badge-01', status: 'QUEUED' })];
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 20 } });

    render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('QUEUED')).toBeInTheDocument();
    });
  });

  it('shows RINGING status with outline badge', async () => {
    const calls = [buildCall({ id: 'ring-badge-test', status: 'RINGING' })];
    mockedListCalls.mockResolvedValue({ success: true, data: calls, meta: { total: 1, page: 1, limit: 20 } });

    render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('RINGING')).toBeInTheDocument();
    });
  });

  it('shows expanded row with recording link', async () => {
    const call = buildCall({
      id: 'rec-call-test01',
      endReason: 'completed',
      recordingUrl: 'https://example.com/recording.mp3',
    });
    mockedListCalls.mockResolvedValue({ success: true, data: [call], meta: { total: 1, page: 1, limit: 20 } });
    mockedGetCall.mockResolvedValue({ success: true, data: call });

    const { user } = render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('rec-call...')).toBeInTheDocument();
    });

    await user.click(screen.getByText('rec-call...'));

    await waitFor(() => {
      expect(screen.getByText('Listen')).toBeInTheDocument();
    });
  });

  it('shows expanded row with transcript text', async () => {
    const call = buildCall({
      id: 'trans-call-test',
      transcript: 'Hello, how can I help?',
    });
    mockedListCalls.mockResolvedValue({ success: true, data: [call], meta: { total: 1, page: 1, limit: 20 } });
    mockedGetCall.mockResolvedValue({ success: true, data: call });

    const { user } = render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('trans-ca...')).toBeInTheDocument();
    });

    await user.click(screen.getByText('trans-ca...'));

    await waitFor(() => {
      expect(screen.getByText('Hello, how can I help?')).toBeInTheDocument();
    });
  });

  it('shows expanded row with transcript as JSON object', async () => {
    const call = buildCall({
      id: 'json-trans-test',
      transcript: { role: 'assistant', content: 'hi' } as any,
    });
    mockedListCalls.mockResolvedValue({ success: true, data: [call], meta: { total: 1, page: 1, limit: 20 } });
    mockedGetCall.mockResolvedValue({ success: true, data: call });

    const { user } = render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('json-tra...')).toBeInTheDocument();
    });

    await user.click(screen.getByText('json-tra...'));

    await waitFor(() => {
      expect(screen.getByText(/assistant/)).toBeInTheDocument();
    });
  });

  it('shows -- for cost when cost is null', async () => {
    const call = buildCall({
      id: 'nocost-call-01',
      cost: null as any,
      endReason: 'timeout',
    });
    mockedListCalls.mockResolvedValue({ success: true, data: [call], meta: { total: 1, page: 1, limit: 20 } });
    mockedGetCall.mockResolvedValue({ success: true, data: call });

    const { user } = render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('nocost-c...')).toBeInTheDocument();
    });

    await user.click(screen.getByText('nocost-c...'));

    await waitFor(() => {
      expect(screen.getByText('timeout')).toBeInTheDocument();
      // Cost should show '--' for null
      const costElements = screen.getAllByText('--');
      expect(costElements.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows load error toast when listCalls fails', async () => {
    mockedListCalls.mockRejectedValue(new Error('Load error'));

    const { toast } = await import('sonner');
    render(<CallsPage />);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to load calls', expect.objectContaining({ description: 'Load error' }));
    });
  });

  it('shows -- for null endReason in expanded row', async () => {
    const call = buildCall({
      id: 'no-reason-test',
      endReason: null,
      cost: '1.2345',
    });
    mockedListCalls.mockResolvedValue({ success: true, data: [call], meta: { total: 1, page: 1, limit: 20 } });
    mockedGetCall.mockResolvedValue({ success: true, data: call });

    const { user } = render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('no-reaso...')).toBeInTheDocument();
    });

    await user.click(screen.getByText('no-reaso...'));

    await waitFor(() => {
      expect(screen.getByText('$1.2345')).toBeInTheDocument();
      // endReason should show '--'
      const dashes = screen.getAllByText('--');
      expect(dashes.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows no expanded row when expandedData is null', async () => {
    const call = buildCall({ id: 'no-expand-data' });
    mockedListCalls.mockResolvedValue({ success: true, data: [call], meta: { total: 1, page: 1, limit: 20 } });

    render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('no-expan...')).toBeInTheDocument();
    });

    // Without clicking to expand, no detail row is shown
    expect(screen.queryByText('End Reason')).not.toBeInTheDocument();
  });

  it('handles getCall error when expanding', async () => {
    const call = buildCall({ id: 'err-expand-test' });
    mockedListCalls.mockResolvedValue({ success: true, data: [call], meta: { total: 1, page: 1, limit: 20 } });
    mockedGetCall.mockRejectedValue(new Error('Network error'));

    const { toast } = await import('sonner');
    const { user } = render(<CallsPage />);

    await waitFor(() => {
      expect(screen.getByText('err-expa...')).toBeInTheDocument();
    });

    await user.click(screen.getByText('err-expa...'));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to load call details', expect.any(Object));
    });
  });
});
