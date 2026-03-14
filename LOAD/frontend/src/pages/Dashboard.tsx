import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listAssistants, listCalls, listPhoneNumbers, listTools, listWebhooks } from '../lib/api';
import type { Call } from '../types';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Bot,
  PhoneCall,
  Phone,
  Activity,
  Headphones,
  Wrench,
  ArrowRight,
  Check,
  Circle,
  Zap,
  Bell,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

interface DayData {
  date: string;
  calls: number;
}

interface OnboardingStep {
  label: string;
  description: string;
  done: boolean;
  path: string;
}

const STATUS_VARIANT: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  IN_PROGRESS: 'default',
  ENDED: 'secondary',
  FAILED: 'destructive',
  QUEUED: 'outline',
  RINGING: 'outline',
};

function buildCallChart(calls: Call[]): DayData[] {
  const days: Record<string, number> = {};
  const now = new Date();
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const key = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    days[key] = 0;
  }
  for (const call of calls) {
    const d = new Date(call.createdAt);
    const key = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    if (key in days) {
      days[key]++;
    }
  }
  return Object.entries(days).map(([date, count]) => ({ date, calls: count }));
}

function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === 0) return '--';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

function formatTimeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function ChartTooltipContent({ active, payload, label }: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-popover border border-border rounded-lg px-3 py-2 shadow-xl">
      <p className="text-[11px] text-muted-foreground">{label}</p>
      <p className="text-sm font-display font-semibold">{payload[0].value} call{payload[0].value !== 1 ? 's' : ''}</p>
    </div>
  );
}

const QUICK_ACTIONS = [
  { label: 'Create Assistant', desc: 'Build a new voice agent', icon: Bot, path: '/assistants', color: 'text-chart-2', bg: 'bg-chart-2/10' },
  { label: 'Test Web Call', desc: 'Talk to your AI live', icon: Headphones, path: '/web-call', color: 'text-primary', bg: 'bg-primary/10' },
  { label: 'Add Tool', desc: 'Extend capabilities', icon: Wrench, path: '/tools', color: 'text-chart-3', bg: 'bg-chart-3/10' },
  { label: 'Set Up Webhook', desc: 'Real-time events', icon: Bell, path: '/webhooks', color: 'text-chart-4', bg: 'bg-chart-4/10' },
];

export function DashboardPage() {
  const [stats, setStats] = useState({
    assistants: 0,
    calls: 0,
    activeCalls: 0,
    phoneNumbers: 0,
  });
  const [recentCalls, setRecentCalls] = useState<Call[]>([]);
  const [chartData, setChartData] = useState<DayData[]>([]);
  const [onboarding, setOnboarding] = useState<OnboardingStep[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const [assistantsRes, callsRes, phoneRes, toolsRes, webhooksRes] = await Promise.all([
          listAssistants(1, 1),
          listCalls(1, 100),
          listPhoneNumbers(1, 1),
          listTools(1, 1),
          listWebhooks(1, 1),
        ]);

        const assistantCount = assistantsRes.meta?.total ?? 0;
        const callCount = callsRes.meta?.total ?? 0;
        const phoneCount = phoneRes.meta?.total ?? 0;
        const toolCount = toolsRes.meta?.total ?? 0;
        const webhookCount = webhooksRes.meta?.total ?? 0;

        const activeCalls = callsRes.data.filter(
          (c) => c.status === 'IN_PROGRESS' || c.status === 'RINGING'
        ).length;

        setStats({
          assistants: assistantCount,
          calls: callCount,
          activeCalls,
          phoneNumbers: phoneCount,
        });

        setRecentCalls(callsRes.data.slice(0, 5));
        setChartData(buildCallChart(callsRes.data));

        setOnboarding([
          { label: 'Create an assistant', description: 'Set up your first AI voice agent', done: assistantCount > 0, path: '/assistants' },
          { label: 'Make a web call', description: 'Test your assistant from the browser', done: callCount > 0, path: '/web-call' },
          { label: 'Add a phone number', description: 'Enable real inbound/outbound calls', done: phoneCount > 0, path: '/phone-numbers' },
          { label: 'Create a tool', description: 'Extend your assistant with custom functions', done: toolCount > 0, path: '/tools' },
          { label: 'Set up a webhook', description: 'Get real-time event notifications', done: webhookCount > 0, path: '/webhooks' },
        ]);
      } catch {
        // Dashboard will show 0s
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  const completedSteps = onboarding.filter((s) => s.done).length;
  const allDone = completedSteps === onboarding.length && onboarding.length > 0;

  const statCards = [
    { label: 'Assistants', value: stats.assistants, icon: Bot, color: 'text-chart-2', bg: 'bg-chart-2/10' },
    { label: 'Total Calls', value: stats.calls, icon: PhoneCall, color: 'text-primary', bg: 'bg-primary/10' },
    { label: 'Active Now', value: stats.activeCalls, icon: Activity, color: 'text-chart-3', bg: 'bg-chart-3/10' },
    { label: 'Phone Numbers', value: stats.phoneNumbers, icon: Phone, color: 'text-chart-4', bg: 'bg-chart-4/10' },
  ];

  return (
    <div className="animate-slide-up">
      <PageHeader title="Dashboard" subtitle="Overview of your voice AI platform" />

      {loading ? (
        <div className="stagger-children space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i}>
                <CardContent className="p-6">
                  <Skeleton className="h-4 w-24 mb-4" />
                  <Skeleton className="h-9 w-20" />
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardContent className="p-6"><Skeleton className="h-[220px] w-full rounded-lg" /></CardContent>
            </Card>
            <Card>
              <CardContent className="p-6"><Skeleton className="h-[220px] w-full rounded-lg" /></CardContent>
            </Card>
          </div>
        </div>
      ) : (
        <div className="stagger-children space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {statCards.map((card) => {
              const Icon = card.icon;
              return (
                <Card key={card.label} className="group transition-all duration-200 hover:border-border/80">
                  <CardContent className="p-5">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{card.label}</span>
                      <div className={`p-2 rounded-lg ${card.bg} transition-transform duration-200 group-hover:scale-110`}>
                        <Icon size={15} className={card.color} />
                      </div>
                    </div>
                    <div className="text-3xl font-display font-bold tracking-tight">{card.value}</div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {QUICK_ACTIONS.map((action) => {
              const Icon = action.icon;
              return (
                <Link key={action.path} to={action.path}>
                  <Card className="group transition-all duration-200 hover:border-primary/20 cursor-pointer h-full">
                    <CardContent className="p-4 flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${action.bg} shrink-0`}>
                        <Icon size={16} className={action.color} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium group-hover:text-primary transition-colors">{action.label}</p>
                        <p className="text-[11px] text-muted-foreground mt-0.5">{action.desc}</p>
                      </div>
                      <ArrowRight size={13} className="text-muted-foreground/20 group-hover:text-primary/50 transition-colors mt-0.5 shrink-0" />
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>

          {/* Chart + Recent Calls */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-5">
                  <div>
                    <h2 className="text-sm font-display font-semibold">Call Activity</h2>
                    <p className="text-[11px] text-muted-foreground mt-0.5">Last 7 days</p>
                  </div>
                  <Link to="/analytics">
                    <Button variant="ghost" size="sm" className="text-xs text-muted-foreground hover:text-foreground gap-1 h-7">
                      View analytics <ArrowRight size={11} />
                    </Button>
                  </Link>
                </div>
                {chartData.some((d) => d.calls > 0) ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={chartData} barCategoryGap="20%">
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                      <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} axisLine={false} tickLine={false} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} axisLine={false} tickLine={false} width={28} />
                      <RechartsTooltip content={<ChartTooltipContent />} cursor={{ fill: 'hsl(var(--muted) / 0.3)', radius: 4 }} />
                      <Bar dataKey="calls" fill="hsl(var(--primary))" radius={[6, 6, 0, 0]} maxBarSize={44} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[220px] flex flex-col items-center justify-center text-muted-foreground gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-muted/50 flex items-center justify-center">
                      <Activity size={20} className="text-muted-foreground/40" />
                    </div>
                    <p className="text-sm">No call activity yet</p>
                    <Link to="/web-call"><Button variant="outline" size="sm" className="text-xs h-8">Make your first call</Button></Link>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Calls */}
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-5">
                  <h2 className="text-sm font-display font-semibold">Recent Calls</h2>
                  {recentCalls.length > 0 && (
                    <Link to="/calls" className="text-xs text-primary hover:underline underline-offset-4">View all</Link>
                  )}
                </div>
                {recentCalls.length > 0 ? (
                  <div className="space-y-3">
                    {recentCalls.map((call) => (
                      <div key={call.id} className="flex items-center justify-between gap-2 py-1">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-1.5">
                            <Badge variant={STATUS_VARIANT[call.status] ?? 'outline'} className="text-[10px] px-1.5 py-0 h-5">
                              {call.status.replace('_', ' ')}
                            </Badge>
                            <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-5 text-muted-foreground">
                              {call.type}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-[11px] text-muted-foreground font-mono">{call.id.slice(0, 8)}</span>
                            {call.duration != null && call.duration > 0 && (
                              <span className="text-[11px] text-muted-foreground">{formatDuration(call.duration)}</span>
                            )}
                          </div>
                        </div>
                        <span className="text-[11px] text-muted-foreground shrink-0">{formatTimeAgo(call.createdAt)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="h-[200px] flex flex-col items-center justify-center text-muted-foreground gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-muted/50 flex items-center justify-center">
                      <PhoneCall size={20} className="text-muted-foreground/40" />
                    </div>
                    <p className="text-sm">No calls yet</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Onboarding Checklist */}
          {!allDone && (
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-5">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Zap size={15} className="text-primary" />
                  </div>
                  <div className="flex-1">
                    <h2 className="text-sm font-display font-semibold">Getting Started</h2>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      {completedSteps} of {onboarding.length} steps completed
                    </p>
                  </div>
                  <div className="flex items-center gap-1">
                    {onboarding.map((step, i) => (
                      <div
                        key={i}
                        className={`w-2 h-2 rounded-full transition-colors ${step.done ? 'bg-primary' : 'bg-muted-foreground/15'}`}
                      />
                    ))}
                  </div>
                </div>
                <div className="space-y-1">
                  {onboarding.map((step) => (
                    <Link
                      key={step.path}
                      to={step.path}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group ${
                        step.done ? 'opacity-60' : 'hover:bg-muted/40'
                      }`}
                    >
                      {step.done ? (
                        <div className="w-6 h-6 rounded-full bg-primary/15 flex items-center justify-center shrink-0">
                          <Check size={12} className="text-primary" />
                        </div>
                      ) : (
                        <div className="w-6 h-6 rounded-full border border-border flex items-center justify-center shrink-0 group-hover:border-primary/30">
                          <Circle size={8} className="text-muted-foreground/30" />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm ${step.done ? 'line-through text-muted-foreground' : 'font-medium'}`}>{step.label}</p>
                        <p className="text-[11px] text-muted-foreground">{step.description}</p>
                      </div>
                      {!step.done && (
                        <ArrowRight size={13} className="text-muted-foreground/20 group-hover:text-primary/50 transition-colors shrink-0" />
                      )}
                    </Link>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
