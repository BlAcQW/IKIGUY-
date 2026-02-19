import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/use-toast";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, AreaChart, Area } from "recharts";
import { Download, TrendingUp, Eye, MousePointer, Users, Clock, Share2, Code } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";

interface DemoAnalyticsData {
  id: string;
  assistant_name: string;
  assistant_type: string;
  total_views: number;
  total_interactions: number;
  total_conversions: number;
  avg_session_duration: number;
  last_analytics_update: string;
  created_at: string;
}

interface AnalyticsEvent {
  event_type: string;
  count: number;
  date: string;
}

interface SessionData {
  session_id: string;
  duration_seconds: number;
  interaction_count: number;
  started_at: string;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const DemoAnalytics = () => {
  const { toast } = useToast();
  const [analyticsData, setAnalyticsData] = useState<DemoAnalyticsData[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30d');
  const [selectedDemo, setSelectedDemo] = useState<string>('all');
  const [eventData, setEventData] = useState<AnalyticsEvent[]>([]);
  const [sessionData, setSessionData] = useState<SessionData[]>([]);
  const [summaryMetrics, setSummaryMetrics] = useState({
    totalDemos: 0,
    totalViews: 0,
    totalInteractions: 0,
    totalConversions: 0,
    avgSessionDuration: 0,
    conversionRate: 0
  });

  useEffect(() => {
    loadAnalyticsData();
  }, [timeRange, selectedDemo]);

  const loadAnalyticsData = async () => {
    setLoading(true);
    try {
      // Load demo analytics summary
      const { data: demos, error: demosError } = await supabase
        .from('custom_demos')
        .select('*')
        .order('created_at', { ascending: false });

      if (demosError) throw demosError;

      setAnalyticsData(demos || []);

      // Calculate summary metrics
      const totalViews = demos?.reduce((sum, demo) => sum + (demo.total_views || 0), 0) || 0;
      const totalInteractions = demos?.reduce((sum, demo) => sum + (demo.total_interactions || 0), 0) || 0;
      const totalConversions = demos?.reduce((sum, demo) => sum + (demo.total_conversions || 0), 0) || 0;
      const avgSessionDuration = demos?.reduce((sum, demo) => sum + (demo.avg_session_duration || 0), 0) / (demos?.length || 1) || 0;
      const conversionRate = totalViews > 0 ? (totalConversions / totalViews) * 100 : 0;

      setSummaryMetrics({
        totalDemos: demos?.length || 0,
        totalViews,
        totalInteractions,
        totalConversions,
        avgSessionDuration: Math.round(avgSessionDuration),
        conversionRate: Math.round(conversionRate * 100) / 100
      });

      // Load detailed analytics if a specific demo is selected
      if (selectedDemo !== 'all') {
        await loadDetailedAnalytics(selectedDemo);
      }

    } catch (error: any) {
      console.error('Error loading analytics data:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to load analytics data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const loadDetailedAnalytics = async (demoId: string) => {
    try {
      const daysAgo = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : timeRange === '90d' ? 90 : 365;
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - daysAgo);

      // Load event data
      const { data: events, error: eventsError } = await supabase
        .from('demo_analytics')
        .select('event_type, created_at')
        .eq('demo_id', demoId)
        .gte('created_at', startDate.toISOString())
        .order('created_at', { ascending: true });

      if (eventsError) throw eventsError;

      // Process event data for charts
      const eventCounts = events?.reduce((acc, event) => {
        const date = new Date(event.created_at).toLocaleDateString();
        const eventType = event.event_type;
        
        if (!acc[date]) acc[date] = {};
        if (!acc[date][eventType]) acc[date][eventType] = 0;
        acc[date][eventType]++;
        
        return acc;
      }, {} as Record<string, Record<string, number>>);

      const chartData = Object.entries(eventCounts || {}).map(([date, events]) => ({
        date,
        views: events.view || 0,
        interactions: events.interaction || 0,
        conversions: events.conversion || 0,
        shares: events.share || 0,
        embeds: events.embed || 0
      }));

      setEventData(chartData);

      // Load session data
      const { data: sessions, error: sessionsError } = await supabase
        .from('demo_sessions')
        .select('session_id, duration_seconds, interaction_count, started_at')
        .eq('demo_id', demoId)
        .gte('started_at', startDate.toISOString())
        .order('started_at', { ascending: true });

      if (sessionsError) throw sessionsError;

      setSessionData(sessions || []);

    } catch (error: any) {
      console.error('Error loading detailed analytics:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to load detailed analytics",
        variant: "destructive"
      });
    }
  };

  const exportAnalytics = async () => {
    try {
      const csvData = analyticsData.map(demo => ({
        'Assistant Name': demo.assistant_name,
        'Type': demo.assistant_type,
        'Total Views': demo.total_views,
        'Total Interactions': demo.total_interactions,
        'Total Conversions': demo.total_conversions,
        'Avg Session Duration (s)': demo.avg_session_duration,
        'Created': new Date(demo.created_at).toLocaleDateString(),
        'Last Updated': demo.last_analytics_update ? new Date(demo.last_analytics_update).toLocaleDateString() : 'Never'
      }));

      const headers = Object.keys(csvData[0]);
      const csvContent = [
        headers.join(','),
        ...csvData.map(row => headers.map(header => `"${row[header]}"`).join(','))
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `demo-analytics-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: "Success",
        description: "Analytics data exported successfully"
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to export analytics data",
        variant: "destructive"
      });
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Demo Analytics</h2>
          <div className="animate-pulse bg-muted h-10 w-32 rounded"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="animate-pulse">
                  <div className="bg-muted h-4 w-20 rounded mb-2"></div>
                  <div className="bg-muted h-8 w-16 rounded"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Demo Analytics</h2>
        <div className="flex items-center gap-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
              <SelectItem value="1y">Last year</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={selectedDemo} onValueChange={setSelectedDemo}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select demo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Demos</SelectItem>
              {analyticsData.map(demo => (
                <SelectItem key={demo.id} value={demo.id}>
                  {demo.assistant_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Button onClick={exportAnalytics} variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Demos</p>
                <p className="text-2xl font-bold">{summaryMetrics.totalDemos}</p>
              </div>
              <Code className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Views</p>
                <p className="text-2xl font-bold">{summaryMetrics.totalViews.toLocaleString()}</p>
              </div>
              <Eye className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Interactions</p>
                <p className="text-2xl font-bold">{summaryMetrics.totalInteractions.toLocaleString()}</p>
              </div>
              <MousePointer className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Conversion Rate</p>
                <p className="text-2xl font-bold">{summaryMetrics.conversionRate}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Demo List */}
      <Card>
        <CardHeader>
          <CardTitle>Demo Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {analyticsData.map(demo => (
              <div key={demo.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold">{demo.assistant_name}</h3>
                    <Badge variant="outline" className="text-xs">
                      {demo.assistant_type.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Created {new Date(demo.created_at).toLocaleDateString()}
                  </p>
                </div>
                
                <div className="flex items-center gap-6 text-sm">
                  <div className="text-center">
                    <p className="font-semibold">{demo.total_views}</p>
                    <p className="text-muted-foreground">Views</p>
                  </div>
                  <div className="text-center">
                    <p className="font-semibold">{demo.total_interactions}</p>
                    <p className="text-muted-foreground">Interactions</p>
                  </div>
                  <div className="text-center">
                    <p className="font-semibold">{demo.total_conversions}</p>
                    <p className="text-muted-foreground">Conversions</p>
                  </div>
                  <div className="text-center">
                    <p className="font-semibold">{formatDuration(demo.avg_session_duration)}</p>
                    <p className="text-muted-foreground">Avg Session</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Detailed Charts for Selected Demo */}
      {selectedDemo !== 'all' && eventData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Event Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={eventData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="views" stackId="1" stroke="#8884d8" fill="#8884d8" />
                  <Area type="monotone" dataKey="interactions" stackId="1" stroke="#82ca9d" fill="#82ca9d" />
                  <Area type="monotone" dataKey="conversions" stackId="1" stroke="#ffc658" fill="#ffc658" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Session Duration Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={sessionData.slice(0, 20)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="session_id" hide />
                  <YAxis />
                  <Tooltip formatter={(value) => formatDuration(value as number)} />
                  <Bar dataKey="duration_seconds" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default DemoAnalytics;
