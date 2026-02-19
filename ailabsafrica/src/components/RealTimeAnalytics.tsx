import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts';
import { 
  TrendingUp, 
  TrendingDown,
  Users, 
  Star, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Download,
  Share2,
  Eye,
  MessageSquare,
  Activity,
  Zap,
  Target,
  BarChart3,
  Settings,
  Plus,
  X
} from 'lucide-react';

interface RealTimeMetrics {
  activeUsers: number;
  totalCalls: number;
  avgResponseTime: number;
  successRate: number;
  errorRate: number;
  revenue: number;
  conversions: number;
  satisfaction: number;
}

interface Widget {
  id: string;
  type: 'metric' | 'chart' | 'list';
  title: string;
  data: any;
  position: { x: number; y: number; w: number; h: number };
  config?: any;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

export default function RealTimeAnalytics() {
  const [metrics, setMetrics] = useState<RealTimeMetrics>({
    activeUsers: 0,
    totalCalls: 0,
    avgResponseTime: 0,
    successRate: 0,
    errorRate: 0,
    revenue: 0,
    conversions: 0,
    satisfaction: 0,
  });

  const [widgets, setWidgets] = useState<Widget[]>([
    {
      id: 'active-users',
      type: 'metric',
      title: 'Active Users',
      data: { value: 0, change: 0 },
      position: { x: 0, y: 0, w: 3, h: 1 },
    },
    {
      id: 'response-time',
      type: 'chart',
      title: 'Response Time Trend',
      data: [],
      position: { x: 3, y: 0, w: 6, h: 2 },
      config: { type: 'line' },
    },
    {
      id: 'success-rate',
      type: 'metric',
      title: 'Success Rate',
      data: { value: 0, change: 0 },
      position: { x: 9, y: 0, w: 3, h: 1 },
    },
  ]);

  const [timeRange, setTimeRange] = useState('1h');
  const [isCustomizing, setIsCustomizing] = useState(false);

  // Simulate real-time data updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        activeUsers: Math.floor(Math.random() * 100) + 50,
        totalCalls: prev.totalCalls + Math.floor(Math.random() * 10),
        avgResponseTime: Math.random() * 3 + 1,
        successRate: Math.random() * 20 + 80,
        errorRate: Math.random() * 10,
        revenue: prev.revenue + Math.random() * 100,
        conversions: prev.conversions + Math.floor(Math.random() * 5),
        satisfaction: Math.random() * 2 + 3,
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const renderMetricWidget = (widget: Widget) => (
    <Card key={widget.id} className="h-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">{widget.title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {widget.data.value}
          {widget.title.includes('Rate') && '%'}
          {widget.title.includes('Time') && 's'}
          {widget.title.includes('Revenue') && '$'}
        </div>
        <div className="flex items-center gap-1 text-xs">
          {widget.data.change > 0 ? (
            <TrendingUp className="h-3 w-3 text-green-500" />
          ) : (
            <TrendingDown className="h-3 w-3 text-red-500" />
          )}
          <span className={widget.data.change > 0 ? 'text-green-500' : 'text-red-500'}>
            {Math.abs(widget.data.change)}%
          </span>
          <span className="text-muted-foreground">from last hour</span>
        </div>
      </CardContent>
    </Card>
  );

  const renderChartWidget = (widget: Widget) => {
    const chartData = [
      { time: '00:00', value: 2.1 },
      { time: '00:15', value: 2.3 },
      { time: '00:30', value: 2.0 },
      { time: '00:45', value: 2.4 },
      { time: '01:00', value: 2.2 },
    ];

    return (
      <Card key={widget.id} className="h-full">
        <CardHeader>
          <CardTitle className="text-sm font-medium">{widget.title}</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#0088FE" 
                strokeWidth={2}
                dot={{ fill: '#0088FE', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    );
  };

  const addWidget = (type: 'metric' | 'chart', title: string) => {
    const newWidget: Widget = {
      id: `widget-${Date.now()}`,
      type,
      title,
      data: type === 'metric' ? { value: 0, change: 0 } : [],
      position: { x: 0, y: widgets.length, w: 3, h: type === 'chart' ? 2 : 1 },
      config: type === 'chart' ? { type: 'line' } : undefined,
    };
    setWidgets([...widgets, newWidget]);
  };

  const removeWidget = (widgetId: string) => {
    setWidgets(widgets.filter(w => w.id !== widgetId));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Real-Time Analytics</h2>
          <p className="text-muted-foreground">Live metrics and performance insights</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="15m">Last 15 min</SelectItem>
              <SelectItem value="1h">Last hour</SelectItem>
              <SelectItem value="24h">Last 24 hours</SelectItem>
              <SelectItem value="7d">Last 7 days</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant={isCustomizing ? "default" : "outline"}
            onClick={() => setIsCustomizing(!isCustomizing)}
            className="flex items-center gap-2"
          >
            <Settings className="h-4 w-4" />
            {isCustomizing ? 'Done' : 'Customize'}
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Live Status */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-muted-foreground">Live data updating every 5 seconds</span>
        </div>
        <Badge variant="secondary" className="flex items-center gap-1">
          <Activity className="h-3 w-3" />
          {metrics.activeUsers} active users
        </Badge>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-blue-500" />
              <div>
                <p className="text-xs text-muted-foreground">Active Users</p>
                <p className="text-lg font-bold">{metrics.activeUsers}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-green-500" />
              <div>
                <p className="text-xs text-muted-foreground">Total Calls</p>
                <p className="text-lg font-bold">{metrics.totalCalls}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-orange-500" />
              <div>
                <p className="text-xs text-muted-foreground">Avg Response</p>
                <p className="text-lg font-bold">{metrics.avgResponseTime.toFixed(1)}s</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <div>
                <p className="text-xs text-muted-foreground">Success Rate</p>
                <p className="text-lg font-bold">{metrics.successRate.toFixed(1)}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-500" />
              <div>
                <p className="text-xs text-muted-foreground">Error Rate</p>
                <p className="text-lg font-bold">{metrics.errorRate.toFixed(1)}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-purple-500" />
              <div>
                <p className="text-xs text-muted-foreground">Revenue</p>
                <p className="text-lg font-bold">${metrics.revenue.toFixed(0)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-indigo-500" />
              <div>
                <p className="text-xs text-muted-foreground">Conversions</p>
                <p className="text-lg font-bold">{metrics.conversions}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Star className="h-4 w-4 text-yellow-500" />
              <div>
                <p className="text-xs text-muted-foreground">Satisfaction</p>
                <p className="text-lg font-bold">{metrics.satisfaction.toFixed(1)}/5</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Customizable Dashboard */}
      <Tabs defaultValue="dashboard" className="w-full">
        <TabsList>
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="users">User Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard" className="space-y-4">
          {isCustomizing && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Add Widgets</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => addWidget('metric', 'Custom Metric')}
                    className="flex items-center gap-2"
                  >
                    <Plus className="h-4 w-4" />
                    Add Metric
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => addWidget('chart', 'Custom Chart')}
                    className="flex items-center gap-2"
                  >
                    <BarChart3 className="h-4 w-4" />
                    Add Chart
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="grid grid-cols-12 gap-4">
            {widgets.map(widget => (
              <div
                key={widget.id}
                className={`col-span-${widget.position.w} row-span-${widget.position.h} relative`}
              >
                {isCustomizing && (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => removeWidget(widget.id)}
                    className="absolute top-2 right-2 z-10 h-6 w-6 p-0"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                )}
                {widget.type === 'metric' && renderMetricWidget(widget)}
                {widget.type === 'chart' && renderChartWidget(widget)}
              </div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Response Time Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={[
                    { range: '0-1s', count: 45 },
                    { range: '1-2s', count: 32 },
                    { range: '2-3s', count: 18 },
                    { range: '3-5s', count: 8 },
                    { range: '5s+', count: 2 },
                  ]}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="range" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#0088FE" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Error Types</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Network', value: 35 },
                        { name: 'Timeout', value: 25 },
                        { name: 'Invalid Input', value: 20 },
                        { name: 'Server Error', value: 15 },
                        { name: 'Other', value: 5 },
                      ]}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {[
                        { name: 'Network', value: 35 },
                        { name: 'Timeout', value: 25 },
                        { name: 'Invalid Input', value: 20 },
                        { name: 'Server Error', value: 15 },
                        { name: 'Other', value: 5 },
                      ].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="users" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>User Activity Heatmap</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={[
                  { hour: '00:00', users: 12 },
                  { hour: '04:00', users: 8 },
                  { hour: '08:00', users: 45 },
                  { hour: '12:00', users: 78 },
                  { hour: '16:00', users: 92 },
                  { hour: '20:00', users: 65 },
                  { hour: '24:00', users: 15 },
                ]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <Tooltip />
                  <Area 
                    type="monotone" 
                    dataKey="users" 
                    stroke="#00C49F" 
                    fill="#00C49F" 
                    fillOpacity={0.6}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
