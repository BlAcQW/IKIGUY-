import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { API_ENDPOINTS } from '@/config/api-config';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Activity, TrendingUp, Users, Clock } from 'lucide-react';

interface MetricsData {
  period: string;
  interval_minutes: number;
  call_volume: number[];
  peer_registrations: number[];
  system_load: number[];
  timestamps: string[];
}

interface MetricsChartProps {
  defaultPeriod?: string;
}

export const MetricsChart: React.FC<MetricsChartProps> = ({ defaultPeriod = '24h' }) => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState(defaultPeriod);
  const [activeChart, setActiveChart] = useState<'calls' | 'peers' | 'load'>('calls');

  const periods = [
    { value: '1h', label: '1 Hour' },
    { value: '6h', label: '6 Hours' },
    { value: '24h', label: '24 Hours' },
    { value: '7d', label: '7 Days' },
    { value: '30d', label: '30 Days' },
  ];

  const fetchMetrics = async (period: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_ENDPOINTS.asterisk.metrics}?period=${period}`);
      if (!response.ok) throw new Error('Failed to fetch metrics');
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics(selectedPeriod);

    // Auto-refresh every 60 seconds
    const interval = setInterval(() => fetchMetrics(selectedPeriod), 60000);
    return () => clearInterval(interval);
  }, [selectedPeriod]);

  // Transform data for charts
  const chartData = metrics ? metrics.timestamps.map((timestamp, index) => ({
    time: new Date(timestamp).toLocaleTimeString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    calls: metrics.call_volume[index],
    peers: metrics.peer_registrations[index],
    load: metrics.system_load[index],
  })) : [];

  // Calculate summary stats
  const summaryStats = metrics ? {
    totalCalls: metrics.call_volume.reduce((a, b) => a + b, 0),
    avgPeers: Math.round(metrics.peer_registrations.reduce((a, b) => a + b, 0) / metrics.peer_registrations.length),
    peakLoad: Math.max(...metrics.system_load),
    avgLoad: (metrics.system_load.reduce((a, b) => a + b, 0) / metrics.system_load.length).toFixed(2),
  } : null;

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      {summaryStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Activity className="h-4 w-4 text-blue-500" />
                Total Calls
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summaryStats.totalCalls}</div>
              <p className="text-xs text-muted-foreground mt-1">In {selectedPeriod}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Users className="h-4 w-4 text-green-500" />
                Avg Peers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summaryStats.avgPeers}</div>
              <p className="text-xs text-muted-foreground mt-1">Active endpoints</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-orange-500" />
                Peak Load
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summaryStats.peakLoad}</div>
              <p className="text-xs text-muted-foreground mt-1">System utilization</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Clock className="h-4 w-4 text-purple-500" />
                Avg Load
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summaryStats.avgLoad}</div>
              <p className="text-xs text-muted-foreground mt-1">Average utilization</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Chart Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>System Metrics</CardTitle>
              <CardDescription>
                Real-time monitoring and historical trends
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {/* Period Selector */}
              <div className="flex gap-1">
                {periods.map((period) => (
                  <Button
                    key={period.value}
                    variant={selectedPeriod === period.value ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedPeriod(period.value)}
                    disabled={isLoading}
                  >
                    {period.label}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Chart Type Selector */}
          <div className="flex gap-2 mb-4">
            <Badge
              variant={activeChart === 'calls' ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => setActiveChart('calls')}
            >
              Call Volume
            </Badge>
            <Badge
              variant={activeChart === 'peers' ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => setActiveChart('peers')}
            >
              Peer Registrations
            </Badge>
            <Badge
              variant={activeChart === 'load' ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => setActiveChart('load')}
            >
              System Load
            </Badge>
          </div>

          {/* Chart */}
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              {activeChart === 'calls' ? (
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 12 }}
                    interval={Math.floor(chartData.length / 8)}
                  />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="calls" fill="#3b82f6" name="Calls" />
                </BarChart>
              ) : activeChart === 'peers' ? (
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 12 }}
                    interval={Math.floor(chartData.length / 8)}
                  />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="peers" stroke="#10b981" strokeWidth={2} name="Peers" />
                </LineChart>
              ) : (
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 12 }}
                    interval={Math.floor(chartData.length / 8)}
                  />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="load" stroke="#f97316" strokeWidth={2} name="System Load" />
                </LineChart>
              )}
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 text-muted-foreground">
              No metrics data available
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
