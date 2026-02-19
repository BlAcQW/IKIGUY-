import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  DollarSign, 
  Activity,
  BarChart3,
  Calendar,
  Users
} from 'lucide-react';

interface UsageAnalyticsProps {
  userId: string;
}

interface AnalyticsData {
  totalSessions: number;
  totalMinutes: number;
  totalCost: number;
  averageSessionLength: number;
  sessionsToday: number;
  minutesToday: number;
  costToday: number;
  sessionsThisWeek: number;
  minutesThisWeek: number;
  costThisWeek: number;
  sessionsThisMonth: number;
  minutesThisMonth: number;
  costThisMonth: number;
  topAssistants: Array<{
    assistant_id: string;
    assistant_name: string;
    sessions: number;
    minutes: number;
    cost: number;
  }>;
  dailyUsage: Array<{
    date: string;
    sessions: number;
    minutes: number;
    cost: number;
  }>;
}

const UsageAnalytics = ({ userId }: UsageAnalyticsProps) => {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'today' | 'week' | 'month'>('week');

  useEffect(() => {
    if (userId) {
      loadAnalytics();
    }
  }, [userId, timeRange]);

  const loadAnalytics = async () => {
    if (!userId) return;
    
    setLoading(true);
    try {
      // Get current date ranges
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
      const monthAgo = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate());

      // Load all usage data
      const { data: usageData, error: usageError } = await supabase
        .from('usage_tracking')
        .select('*')
        .eq('user_id', userId)
        .eq('status', 'completed')
        .order('start_time', { ascending: false });

      if (usageError) {
        console.error('Error loading usage data:', usageError);
        return;
      }

      if (!usageData) return;

      // Calculate analytics
      const analytics: AnalyticsData = {
        totalSessions: usageData.length,
        totalMinutes: usageData.reduce((sum, record) => sum + (record.duration_minutes || 0), 0),
        totalCost: usageData.reduce((sum, record) => sum + (record.total_cost || 0), 0),
        averageSessionLength: usageData.length > 0 
          ? usageData.reduce((sum, record) => sum + (record.duration_minutes || 0), 0) / usageData.length 
          : 0,
        sessionsToday: usageData.filter(record => new Date(record.start_time) >= today).length,
        minutesToday: usageData
          .filter(record => new Date(record.start_time) >= today)
          .reduce((sum, record) => sum + (record.duration_minutes || 0), 0),
        costToday: usageData
          .filter(record => new Date(record.start_time) >= today)
          .reduce((sum, record) => sum + (record.total_cost || 0), 0),
        sessionsThisWeek: usageData.filter(record => new Date(record.start_time) >= weekAgo).length,
        minutesThisWeek: usageData
          .filter(record => new Date(record.start_time) >= weekAgo)
          .reduce((sum, record) => sum + (record.duration_minutes || 0), 0),
        costThisWeek: usageData
          .filter(record => new Date(record.start_time) >= weekAgo)
          .reduce((sum, record) => sum + (record.total_cost || 0), 0),
        sessionsThisMonth: usageData.filter(record => new Date(record.start_time) >= monthAgo).length,
        minutesThisMonth: usageData
          .filter(record => new Date(record.start_time) >= monthAgo)
          .reduce((sum, record) => sum + (record.duration_minutes || 0), 0),
        costThisMonth: usageData
          .filter(record => new Date(record.start_time) >= monthAgo)
          .reduce((sum, record) => sum + (record.total_cost || 0), 0),
        topAssistants: [],
        dailyUsage: []
      };

      // Calculate top assistants
      const assistantStats = new Map();
      usageData.forEach(record => {
        const assistantId = record.assistant_id;
        const assistantName = record.metadata?.assistant_name || 'Unknown Assistant';
        
        if (!assistantStats.has(assistantId)) {
          assistantStats.set(assistantId, {
            assistant_id: assistantId,
            assistant_name: assistantName,
            sessions: 0,
            minutes: 0,
            cost: 0
          });
        }
        
        const stats = assistantStats.get(assistantId);
        stats.sessions += 1;
        stats.minutes += record.duration_minutes || 0;
        stats.cost += record.total_cost || 0;
      });

      analytics.topAssistants = Array.from(assistantStats.values())
        .sort((a, b) => b.sessions - a.sessions)
        .slice(0, 5);

      // Calculate daily usage for the selected time range
      const startDate = timeRange === 'today' ? today : timeRange === 'week' ? weekAgo : monthAgo;
      const filteredData = usageData.filter(record => new Date(record.start_time) >= startDate);
      
      const dailyStats = new Map();
      filteredData.forEach(record => {
        const date = new Date(record.start_time).toISOString().split('T')[0];
        
        if (!dailyStats.has(date)) {
          dailyStats.set(date, {
            date,
            sessions: 0,
            minutes: 0,
            cost: 0
          });
        }
        
        const stats = dailyStats.get(date);
        stats.sessions += 1;
        stats.minutes += record.duration_minutes || 0;
        stats.cost += record.total_cost || 0;
      });

      analytics.dailyUsage = Array.from(dailyStats.values())
        .sort((a, b) => a.date.localeCompare(b.date));

      setAnalytics(analytics);
    } catch (error: any) {
      console.error('Error loading analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCurrentPeriodData = () => {
    if (!analytics) return { sessions: 0, minutes: 0, cost: 0 };
    
    switch (timeRange) {
      case 'today':
        return {
          sessions: analytics.sessionsToday,
          minutes: analytics.minutesToday,
          cost: analytics.costToday
        };
      case 'week':
        return {
          sessions: analytics.sessionsThisWeek,
          minutes: analytics.minutesThisWeek,
          cost: analytics.costThisWeek
        };
      case 'month':
        return {
          sessions: analytics.sessionsThisMonth,
          minutes: analytics.minutesThisMonth,
          cost: analytics.costThisMonth
        };
      default:
        return { sessions: 0, minutes: 0, cost: 0 };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No usage data available
      </div>
    );
  }

  const currentPeriod = getCurrentPeriodData();

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex gap-2">
        <button
          onClick={() => setTimeRange('today')}
          className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
            timeRange === 'today'
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-muted-foreground hover:bg-muted/80'
          }`}
        >
          Today
        </button>
        <button
          onClick={() => setTimeRange('week')}
          className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
            timeRange === 'week'
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-muted-foreground hover:bg-muted/80'
          }`}
        >
          This Week
        </button>
        <button
          onClick={() => setTimeRange('month')}
          className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
            timeRange === 'month'
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-muted-foreground hover:bg-muted/80'
          }`}
        >
          This Month
        </button>
      </div>

      {/* Current Period Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sessions</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{currentPeriod.sessions}</div>
            <p className="text-xs text-muted-foreground">
              {timeRange === 'today' ? 'Today' : timeRange === 'week' ? 'This week' : 'This month'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Minutes</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{currentPeriod.minutes.toFixed(1)}</div>
            <p className="text-xs text-muted-foreground">
              Total usage time
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${currentPeriod.cost.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">
              Total spending
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Lifetime Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Lifetime Statistics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">{analytics.totalSessions}</div>
              <p className="text-sm text-muted-foreground">Total Sessions</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{analytics.totalMinutes.toFixed(1)}</div>
              <p className="text-sm text-muted-foreground">Total Minutes</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">${analytics.totalCost.toFixed(2)}</div>
              <p className="text-sm text-muted-foreground">Total Spent</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{analytics.averageSessionLength.toFixed(1)}</div>
              <p className="text-sm text-muted-foreground">Avg Session (min)</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Top Assistants */}
      {analytics.topAssistants.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Top Assistants
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analytics.topAssistants.map((assistant, index) => (
                <div key={assistant.assistant_id} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Badge variant="secondary">{index + 1}</Badge>
                    <div>
                      <p className="font-medium">{assistant.assistant_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {assistant.sessions} sessions • {assistant.minutes.toFixed(1)} min
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">${assistant.cost.toFixed(2)}</p>
                    <p className="text-sm text-muted-foreground">
                      ${(assistant.cost / assistant.sessions).toFixed(2)}/session
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Daily Usage Chart */}
      {analytics.dailyUsage.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Daily Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analytics.dailyUsage.map((day) => (
                <div key={day.date} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-20 text-sm">
                      {new Date(day.date).toLocaleDateString('en-US', { 
                        month: 'short', 
                        day: 'numeric' 
                      })}
                    </div>
                    <div className="flex-1">
                      <div className="flex justify-between text-sm mb-1">
                        <span>{day.sessions} sessions</span>
                        <span>{day.minutes.toFixed(1)} min</span>
                      </div>
                      <Progress 
                        value={(day.minutes / Math.max(...analytics.dailyUsage.map(d => d.minutes))) * 100} 
                        className="h-2"
                      />
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">${day.cost.toFixed(2)}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default UsageAnalytics;
