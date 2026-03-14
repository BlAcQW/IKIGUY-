import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@test/helpers/render';
import { buildAnalyticsSummary, buildTimeSeriesPoint } from '@test/helpers/factories';

vi.mock('@/lib/api', () => ({
  getCallAnalytics: vi.fn(),
  getAnalyticsSummary: vi.fn(),
  listAssistants: vi.fn(),
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
  PieChart: ({ children }: { children: React.ReactNode }) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div />,
  Cell: () => <div />,
  Legend: () => <div />,
}));

import React from 'react';
import { AnalyticsPage } from './Analytics';
import { getCallAnalytics, getAnalyticsSummary, listAssistants } from '@/lib/api';

const mockedGetCallAnalytics = vi.mocked(getCallAnalytics);
const mockedGetAnalyticsSummary = vi.mocked(getAnalyticsSummary);
const mockedListAssistants = vi.mocked(listAssistants);

describe('AnalyticsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedListAssistants.mockResolvedValue({ success: true, data: [] });
  });

  it('renders page title', () => {
    mockedGetCallAnalytics.mockReturnValue(new Promise(() => {}));
    mockedGetAnalyticsSummary.mockReturnValue(new Promise(() => {}));
    render(<AnalyticsPage />);
    expect(screen.getByText('Analytics')).toBeInTheDocument();
  });

  it('shows empty state when no data', async () => {
    mockedGetCallAnalytics.mockResolvedValue({ success: true, data: [] });
    mockedGetAnalyticsSummary.mockResolvedValue({ success: true, data: buildAnalyticsSummary({ totalCalls: 0 }) });

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('No analytics data')).toBeInTheDocument();
    });
  });

  it('shows summary cards with values', async () => {
    const summary = buildAnalyticsSummary({ totalCalls: 100, successRate: 85, failedCalls: 15, avgDuration: 120, totalMinutes: 200 });
    mockedGetCallAnalytics.mockResolvedValue({ success: true, data: [buildTimeSeriesPoint()] });
    mockedGetAnalyticsSummary.mockResolvedValue({ success: true, data: summary });

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument();
      expect(screen.getByText('200')).toBeInTheDocument();
    });
  });

  it('renders range filter buttons', () => {
    mockedGetCallAnalytics.mockReturnValue(new Promise(() => {}));
    mockedGetAnalyticsSummary.mockReturnValue(new Promise(() => {}));
    render(<AnalyticsPage />);
    expect(screen.getByText('7 days')).toBeInTheDocument();
    expect(screen.getByText('30 days')).toBeInTheDocument();
    expect(screen.getByText('90 days')).toBeInTheDocument();
  });

  it('handles API error gracefully', async () => {
    mockedGetCallAnalytics.mockRejectedValue(new Error('fail'));
    mockedGetAnalyticsSummary.mockRejectedValue(new Error('fail'));

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('Analytics')).toBeInTheDocument();
    });
  });

  it('shows duration less than 60 seconds', async () => {
    const summary = buildAnalyticsSummary({ totalCalls: 10, avgDuration: 45 });
    mockedGetCallAnalytics.mockResolvedValue({ success: true, data: [buildTimeSeriesPoint()] });
    mockedGetAnalyticsSummary.mockResolvedValue({ success: true, data: summary });

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('45s')).toBeInTheDocument();
    });
  });

  it('renders By Call Type section with data', async () => {
    const summary = buildAnalyticsSummary({
      totalCalls: 50,
      byType: [{ type: 'WEB', count: 30 }, { type: 'INBOUND', count: 20 }],
    });
    mockedGetCallAnalytics.mockResolvedValue({ success: true, data: [buildTimeSeriesPoint()] });
    mockedGetAnalyticsSummary.mockResolvedValue({ success: true, data: summary });

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('By Call Type')).toBeInTheDocument();
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    });
  });

  it('shows "No data" when byType is empty', async () => {
    const summary = buildAnalyticsSummary({
      totalCalls: 50,
      byType: [],
      byAssistant: [],
    });
    mockedGetCallAnalytics.mockResolvedValue({ success: true, data: [buildTimeSeriesPoint()] });
    mockedGetAnalyticsSummary.mockResolvedValue({ success: true, data: summary });

    render(<AnalyticsPage />);

    await waitFor(() => {
      const noDataElements = screen.getAllByText('No data');
      expect(noDataElements.length).toBeGreaterThanOrEqual(2);
    });
  });

  it('renders By Assistant section with data', async () => {
    const summary = buildAnalyticsSummary({
      totalCalls: 50,
      byAssistant: [
        { assistantId: 'a1', assistantName: 'Sales Bot', count: 30 },
        { assistantId: 'a2', assistantName: 'Support Bot', count: 20 },
      ],
    });
    mockedGetCallAnalytics.mockResolvedValue({ success: true, data: [buildTimeSeriesPoint()] });
    mockedGetAnalyticsSummary.mockResolvedValue({ success: true, data: summary });

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('By Assistant')).toBeInTheDocument();
      expect(screen.getByText('Sales Bot')).toBeInTheDocument();
      expect(screen.getByText('30 calls')).toBeInTheDocument();
      expect(screen.getByText('Support Bot')).toBeInTheDocument();
      expect(screen.getByText('20 calls')).toBeInTheDocument();
    });
  });

  it('changes range when clicking 30 days button', async () => {
    const summary = buildAnalyticsSummary({ totalCalls: 0 });
    mockedGetCallAnalytics.mockResolvedValue({ success: true, data: [] });
    mockedGetAnalyticsSummary.mockResolvedValue({ success: true, data: summary });

    const { user } = render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('No analytics data')).toBeInTheDocument();
    });

    // Click "30 days"
    await user.click(screen.getByText('30 days'));

    await waitFor(() => {
      // getCallAnalytics should have been called again with new range
      expect(mockedGetCallAnalytics).toHaveBeenCalledTimes(2);
    });
  });

  it('changes range when clicking 90 days button', async () => {
    const summary = buildAnalyticsSummary({ totalCalls: 0 });
    mockedGetCallAnalytics.mockResolvedValue({ success: true, data: [] });
    mockedGetAnalyticsSummary.mockResolvedValue({ success: true, data: summary });

    const { user } = render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('No analytics data')).toBeInTheDocument();
    });

    await user.click(screen.getByText('90 days'));

    await waitFor(() => {
      expect(mockedGetCallAnalytics).toHaveBeenCalledTimes(2);
    });
  });

  it('shows "No data for selected period" when chartData is empty but summary has calls', async () => {
    const summary = buildAnalyticsSummary({ totalCalls: 10 });
    mockedGetCallAnalytics.mockResolvedValue({ success: true, data: [] });
    mockedGetAnalyticsSummary.mockResolvedValue({ success: true, data: summary });

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('No data for selected period')).toBeInTheDocument();
    });
  });

  it('shows Call Volume heading when data is present', async () => {
    const summary = buildAnalyticsSummary({ totalCalls: 10 });
    mockedGetCallAnalytics.mockResolvedValue({ success: true, data: [buildTimeSeriesPoint()] });
    mockedGetAnalyticsSummary.mockResolvedValue({ success: true, data: summary });

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('Call Volume')).toBeInTheDocument();
    });
  });

  it('renders summary card labels', async () => {
    const summary = buildAnalyticsSummary({ totalCalls: 10, successRate: 90, failedCalls: 1, avgDuration: 30, totalMinutes: 5 });
    mockedGetCallAnalytics.mockResolvedValue({ success: true, data: [buildTimeSeriesPoint()] });
    mockedGetAnalyticsSummary.mockResolvedValue({ success: true, data: summary });

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('Total Calls')).toBeInTheDocument();
      expect(screen.getByText('Success Rate')).toBeInTheDocument();
      expect(screen.getByText('Failed Calls')).toBeInTheDocument();
      expect(screen.getByText('Avg Duration')).toBeInTheDocument();
      expect(screen.getByText('Total Minutes')).toBeInTheDocument();
    });
  });

  it('shows null summary as empty state', async () => {
    mockedGetCallAnalytics.mockResolvedValue({ success: true, data: [] });
    mockedGetAnalyticsSummary.mockResolvedValue({ success: true, data: null as any });

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('No analytics data')).toBeInTheDocument();
    });
  });

  it('renders assistant filter', () => {
    mockedGetCallAnalytics.mockReturnValue(new Promise(() => {}));
    mockedGetAnalyticsSummary.mockReturnValue(new Promise(() => {}));
    render(<AnalyticsPage />);
    // The assistant filter Select component should be rendered
    expect(screen.getByText('All Assistants')).toBeInTheDocument();
  });

  it('shows loading state with skeletons', () => {
    mockedGetCallAnalytics.mockReturnValue(new Promise(() => {}));
    mockedGetAnalyticsSummary.mockReturnValue(new Promise(() => {}));
    render(<AnalyticsPage />);
    // During loading, the summary cards should not be visible
    expect(screen.queryByText('Total Calls')).not.toBeInTheDocument();
  });

  it('shows duration in formatted string', async () => {
    const summary = buildAnalyticsSummary({ totalCalls: 50, avgDuration: 90 });
    mockedGetCallAnalytics.mockResolvedValue({ success: true, data: [buildTimeSeriesPoint()] });
    mockedGetAnalyticsSummary.mockResolvedValue({ success: true, data: summary });

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('1m 30s')).toBeInTheDocument();
    });
  });
});
