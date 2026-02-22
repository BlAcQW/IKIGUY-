import { useEffect, useState, useCallback } from 'react';
import { getCallAnalytics, getAnalyticsSummary, listAssistants } from '../lib/api';
import type { TimeSeriesPoint, AnalyticsSummary, Assistant } from '../types';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell, Legend,
} from 'recharts';
import { PhoneCall, CheckCircle, XCircle, Clock, BarChart3, Timer } from 'lucide-react';

const RANGE_OPTIONS = [
  { value: '7d', label: '7 days' },
  { value: '30d', label: '30 days' },
  { value: '90d', label: '90 days' },
];

const PIE_COLORS = ['hsl(var(--chart-1))', 'hsl(var(--chart-2))', 'hsl(var(--chart-3))'];

function getDateRange(range: string): { from: string; to: string; groupBy: 'hour' | 'day' | 'week' } {
  const to = new Date();
  const from = new Date();
  let groupBy: 'hour' | 'day' | 'week' = 'day';
  switch (range) {
    case '7d': from.setDate(from.getDate() - 7); groupBy = 'day'; break;
    case '30d': from.setDate(from.getDate() - 30); groupBy = 'day'; break;
    case '90d': from.setDate(from.getDate() - 90); groupBy = 'week'; break;
  }
  return { from: from.toISOString(), to: to.toISOString(), groupBy };
}

function formatPeriod(iso: string, groupBy: string): string {
  const d = new Date(iso);
  if (groupBy === 'hour') return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric' });
  if (groupBy === 'week') return `Wk ${d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
}

function ChartTooltipContent({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-popover border border-border rounded-lg p-3 shadow-lg">
      <p className="text-xs font-medium text-foreground mb-1.5">{label}</p>
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center gap-2 text-xs">
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-muted-foreground">{entry.name}:</span>
          <span className="font-medium">{entry.value}</span>
        </div>
      ))}
    </div>
  );
}

export function AnalyticsPage() {
  const [range, setRange] = useState('7d');
  const [assistantId, setAssistantId] = useState<string>('all');
  const [assistants, setAssistants] = useState<Assistant[]>([]);
  const [timeSeries, setTimeSeries] = useState<TimeSeriesPoint[]>([]);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const { from, to, groupBy } = getDateRange(range);
      const filterAssistantId = assistantId !== 'all' ? assistantId : undefined;
      const [timeSeriesRes, summaryRes] = await Promise.all([
        getCallAnalytics({ from, to, groupBy, assistantId: filterAssistantId }),
        getAnalyticsSummary({ from, to, assistantId: filterAssistantId }),
      ]);
      setTimeSeries(timeSeriesRes.data);
      setSummary(summaryRes.data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoading(false);
    }
  }, [range, assistantId]);

  useEffect(() => { loadData(); }, [loadData]);

  useEffect(() => {
    listAssistants(1, 100)
      .then((res) => setAssistants(res.data))
      .catch((err) => console.error('Failed to load assistants:', err));
  }, []);

  const { groupBy } = getDateRange(range);
  const chartData = timeSeries.map((p) => ({ ...p, label: formatPeriod(p.period, groupBy) }));

  const summaryCards = summary
    ? [
        { label: 'Total Calls', value: summary.totalCalls, icon: PhoneCall, color: 'text-primary', bg: 'bg-primary/10' },
        { label: 'Success Rate', value: `${summary.successRate}%`, icon: CheckCircle, color: 'text-chart-2', bg: 'bg-chart-2/10' },
        { label: 'Failed Calls', value: summary.failedCalls, icon: XCircle, color: 'text-destructive', bg: 'bg-destructive/10' },
        { label: 'Avg Duration', value: formatDuration(summary.avgDuration), icon: Clock, color: 'text-chart-3', bg: 'bg-chart-3/10' },
        { label: 'Total Minutes', value: summary.totalMinutes, icon: Timer, color: 'text-chart-4', bg: 'bg-chart-4/10' },
      ]
    : [];

  return (
    <div className="animate-slide-up">
      <PageHeader title="Analytics" subtitle="Call volume, success rates, and performance metrics">
        <div className="flex gap-2 items-center">
          <Select value={assistantId} onValueChange={setAssistantId}>
            <SelectTrigger className="w-[170px] h-9 text-xs">
              <SelectValue placeholder="All assistants" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Assistants</SelectItem>
              {assistants.map((a) => (<SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>))}
            </SelectContent>
          </Select>
          <div className="flex gap-0.5 border rounded-lg p-0.5 bg-muted/30">
            {RANGE_OPTIONS.map((opt) => (
              <Button
                key={opt.value}
                variant={range === opt.value ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setRange(opt.value)}
                className={`h-7 text-[11px] px-3 font-medium ${range === opt.value ? '' : 'text-muted-foreground'}`}
              >
                {opt.label}
              </Button>
            ))}
          </div>
        </div>
      </PageHeader>

      {loading ? (
        <div className="space-y-4 stagger-children">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <Card key={i}><CardContent className="p-5"><Skeleton className="h-4 w-20 mb-3" /><Skeleton className="h-7 w-14" /></CardContent></Card>
            ))}
          </div>
          <Card><CardContent className="p-6"><Skeleton className="h-[280px] w-full" /></CardContent></Card>
        </div>
      ) : !summary || summary.totalCalls === 0 ? (
        <Card className="border-dashed"><CardContent className="py-16 text-center">
          <div className="w-14 h-14 rounded-2xl bg-muted/50 flex items-center justify-center mx-auto mb-4"><BarChart3 size={24} className="text-muted-foreground/40" /></div>
          <h2 className="text-base font-display font-semibold mb-1">No analytics data</h2>
          <p className="text-sm text-muted-foreground">Make some calls to see analytics data here.</p>
        </CardContent></Card>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mb-6 stagger-children">
            {summaryCards.map((card) => {
              const Icon = card.icon;
              return (
                <Card key={card.label} className="group transition-all duration-200 hover:border-border/80">
                  <CardContent className="p-5">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-[11px] text-muted-foreground uppercase tracking-wider font-medium">{card.label}</span>
                      <div className={`w-8 h-8 rounded-lg ${card.bg} flex items-center justify-center transition-transform group-hover:scale-110`}>
                        <Icon size={15} className={card.color} />
                      </div>
                    </div>
                    <div className="text-2xl font-display font-bold">{card.value}</div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <Card className="mb-6">
            <CardContent className="p-6">
              <h2 className="text-sm font-display font-semibold mb-4">Call Volume</h2>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.4} />
                    <XAxis dataKey="label" tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} axisLine={false} tickLine={false} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} axisLine={false} tickLine={false} />
                    <Tooltip content={<ChartTooltipContent />} cursor={{ fill: 'hsl(var(--muted))', opacity: 0.3 }} />
                    <Bar dataKey="completed" name="Completed" fill="hsl(var(--primary))" stackId="stack" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="failed" name="Failed" fill="hsl(var(--destructive))" stackId="stack" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[280px] flex items-center justify-center text-muted-foreground text-xs">
                  No data for selected period
                </div>
              )}
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardContent className="p-6">
                <h2 className="text-sm font-display font-semibold mb-4">By Call Type</h2>
                {summary.byType.length > 0 ? (
                  <ResponsiveContainer width="100%" height={240}>
                    <PieChart>
                      <Pie
                        data={summary.byType}
                        dataKey="count"
                        nameKey="type"
                        cx="50%"
                        cy="50%"
                        innerRadius={55}
                        outerRadius={85}
                        paddingAngle={3}
                        label={({ name, value }) => `${name} (${value})`}
                        labelLine={false}
                      >
                        {summary.byType.map((_, idx) => (
                          <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Legend wrapperStyle={{ fontSize: '11px' }} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[240px] flex items-center justify-center text-muted-foreground text-xs">No data</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <h2 className="text-sm font-display font-semibold mb-4">By Assistant</h2>
                {summary.byAssistant.length > 0 ? (
                  <div className="space-y-3">
                    {summary.byAssistant.map((item) => {
                      const maxCount = Math.max(...summary.byAssistant.map((a) => a.count));
                      const pct = maxCount > 0 ? (item.count / maxCount) * 100 : 0;
                      return (
                        <div key={item.assistantId}>
                          <div className="flex justify-between text-xs mb-1.5">
                            <span className="truncate font-medium">{item.assistantName}</span>
                            <span className="text-muted-foreground ml-2">{item.count} calls</span>
                          </div>
                          <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                            <div className="h-full bg-primary rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="h-[240px] flex items-center justify-center text-muted-foreground text-xs">No data</div>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
