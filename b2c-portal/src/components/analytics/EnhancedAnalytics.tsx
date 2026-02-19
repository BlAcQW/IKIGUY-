/**
 * @deprecated This component's features have been absorbed into other analytics components.
 * Use UnifiedAutomationDashboard, DeploymentAnalyticsDashboard, or RealTimeHealthMonitor instead.
 * This file will be removed in a future release.
 */
import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { useUsageData, useUsageSummary } from '@/hooks/useCoreApi';
import { useMongoAuth } from '@/components/auth/MongoAuthContext'; // Add this import
import { 
  Download, 
  TrendingUp, 
  TrendingDown,
  Phone,
  MessageSquare,
  Clock,
  Users,
  Target,
  BarChart3,
  PieChart,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface EnhancedAnalyticsProps {
  timeRange: string;
}

interface IntentData {
  intent: string;
  count: number;
  percentage: number;
  trend: 'up' | 'down' | 'stable';
  avgDuration: number;
}

interface DropOffData {
  step: string;
  totalReached: number;
  droppedOff: number;
  percentage: number;
  reason?: string;
}

const EnhancedAnalytics: React.FC<EnhancedAnalyticsProps> = ({ timeRange }) => {
  const [selectedCampaign, setSelectedCampaign] = useState('all');
  const { toast } = useToast();
  const { user, getTenantId } = useMongoAuth(); // Get the current user to extract tenant ID

  // Get tenant ID from user metadata or use a default
  const tenantId = user?.user_metadata?.tenant_id || user?.id || '';

  // Use Core Backend APIs instead of mock data
  const { data: usageData, isLoading: usageLoading, error: usageError } = useUsageData(tenantId, timeRange);
  const { data: usageSummary, isLoading: summaryLoading, error: summaryError } = useUsageSummary(tenantId, timeRange);

  // Mock data for intents and drop-offs (these would come from Core Backend in the future)
  const topIntents: IntentData[] = [
    {
      intent: 'Product Inquiry',
      count: 456,
      percentage: 32.1,
      trend: 'up',
      avgDuration: 145
    },
    {
      intent: 'Appointment Booking',
      count: 324,
      percentage: 22.8,
      trend: 'up',
      avgDuration: 180
    },
    {
      intent: 'Technical Support',
      count: 298,
      percentage: 21.0,
      trend: 'stable',
      avgDuration: 210
    },
    {
      intent: 'Pricing Question',
      count: 187,
      percentage: 13.2,
      trend: 'down',
      avgDuration: 95
    },
    {
      intent: 'General Information',
      count: 156,
      percentage: 11.0,
      trend: 'stable',
      avgDuration: 75
    }
  ];

  const dropOffData: DropOffData[] = [
    {
      step: 'Initial Greeting',
      totalReached: 1250,
      droppedOff: 45,
      percentage: 3.6,
      reason: 'Connection issues'
    },
    {
      step: 'Intent Recognition',
      totalReached: 1205,
      droppedOff: 89,
      percentage: 7.4,
      reason: 'Unclear user intent'
    },
    {
      step: 'Information Gathering',
      totalReached: 1116,
      droppedOff: 156,
      percentage: 14.0,
      reason: 'User impatience'
    },
    {
      step: 'Solution Presentation',
      totalReached: 960,
      droppedOff: 78,
      percentage: 8.1,
      reason: 'Solution not relevant'
    },
    {
      step: 'Call Completion',
      totalReached: 882,
      droppedOff: 23,
      percentage: 2.6,
      reason: 'Technical issues'
    }
  ];

  const exportAnalytics = (format: 'csv' | 'json' | 'xlsx') => {
    if (!usageData?.data || !usageSummary?.data) {
      toast({
        title: "Export Error",
        description: "No data available for export",
        variant: "destructive"
      });
      return;
    }

    const exportData = {
      timeRange,
      selectedCampaign,
      usageData: usageData.data,
      usageSummary: usageSummary.data,
      topIntents,
      dropOffData,
      exportDate: new Date().toISOString()
    };

    let content: string;
    let filename: string;
    let mimeType: string;

    if (format === 'csv') {
      // Generate CSV content
      const csvRows = [
        ['Metric', 'Value', 'Unit'],
        ['Total Minutes', usageData.data.total_minutes?.toString() || '0', 'minutes'],
        ['Total Messages', usageData.data.total_messages?.toString() || '0', 'messages'],
        ['Total Calls', usageData.data.total_calls?.toString() || '0', 'calls'],
        ['Telephony Cost', usageData.data.costs?.telephony?.toString() || '0', 'USD'],
        ['STT Cost', usageData.data.costs?.stt?.toString() || '0', 'USD'],
        ['TTS Cost', usageData.data.costs?.tts?.toString() || '0', 'USD'],
        ['Total Cost', usageData.data.costs?.total?.toString() || '0', 'USD'],
        [],
        ['Top Intents', 'Count', 'Percentage', 'Avg Duration (s)'],
        ...topIntents.map(intent => [
          intent.intent,
          intent.count.toString(),
          intent.percentage.toString(),
          intent.avgDuration.toString()
        ]),
        [],
        ['Drop-off Step', 'Total Reached', 'Dropped Off', 'Percentage', 'Reason'],
        ...dropOffData.map(drop => [
          drop.step,
          drop.totalReached.toString(),
          drop.droppedOff.toString(),
          drop.percentage.toString(),
          drop.reason || ''
        ])
      ];

      content = csvRows.map(row => row.join(',')).join('\n');
      filename = `analytics_${timeRange}_${new Date().toISOString().split('T')[0]}.csv`;
      mimeType = 'text/csv';
    } else if (format === 'json') {
      content = JSON.stringify(exportData, null, 2);
      filename = `analytics_${timeRange}_${new Date().toISOString().split('T')[0]}.json`;
      mimeType = 'application/json';
    } else {
      // For XLSX, we'll just export as JSON for now
      content = JSON.stringify(exportData, null, 2);
      filename = `analytics_${timeRange}_${new Date().toISOString().split('T')[0]}.json`;
      mimeType = 'application/json';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: "Export Successful",
      description: `Analytics data exported as ${format.toUpperCase()}`,
    });
  };

  // Handle isLoading and error states
  if (usageLoading || summaryLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Enhanced Analytics</h2>
          <div className="flex gap-2">
            <Button variant="outline" disabled>
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </div>
        <div className="text-center py-12">
          <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading analytics data...</p>
        </div>
      </div>
    );
  }

  if (usageError || summaryError) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Enhanced Analytics</h2>
        </div>
        <div className="text-center py-12">
          <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Failed to load analytics</h3>
          <p className="text-gray-600">
            {usageError?.message || summaryError?.message || 'An error occurred while isLoading analytics data'}
          </p>
          <Button 
            variant="outline" 
            className="mt-4"
            onClick={() => window.location.reload()}
          >
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      case 'stable':
        return <Activity className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getDropOffColor = (percentage: number) => {
    if (percentage < 5) return 'text-green-600';
    if (percentage < 10) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      {/* Usage Counters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Usage Counters</CardTitle>
              <CardDescription>Detailed usage metrics and costs</CardDescription>
            </div>
            <div className="flex gap-2">
              <Select value={selectedCampaign} onValueChange={setSelectedCampaign}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Select campaign" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Campaigns</SelectItem>
                  <SelectItem value="insurance">Insurance Follow-up</SelectItem>
                  <SelectItem value="product">Product Demo</SelectItem>
                  <SelectItem value="survey">Customer Survey</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" onClick={() => exportAnalytics('csv')}>
                <Download className="h-4 w-4 mr-2" />
                Export CSV
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="h-5 w-5 text-blue-500" />
                  <span className="font-medium">Total Minutes</span>
                </div>
                <span className="text-2xl font-bold">{usageData.data.total_minutes?.toLocaleString() || '0'}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-green-500" />
                  <span className="font-medium">Total Messages</span>
                </div>
                <span className="text-2xl font-bold">{usageData.data.total_messages?.toLocaleString() || '0'}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Phone className="h-5 w-5 text-purple-500" />
                  <span className="font-medium">Total Calls</span>
                </div>
                <span className="text-2xl font-bold">{usageData.data.total_calls?.toLocaleString() || '0'}</span>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="font-semibold text-lg">Cost Breakdown</h4>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Telephony</span>
                  <span className="font-medium">${usageData.data.costs?.telephony?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Speech-to-Text</span>
                  <span className="font-medium">${usageData.data.costs?.stt?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Text-to-Speech</span>
                  <span className="font-medium">${usageData.data.costs?.tts?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="border-t pt-2">
                  <div className="flex justify-between font-semibold">
                    <span>Total Cost</span>
                    <span>${usageData.data.costs?.total?.toFixed(2) || '0.00'}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="font-semibold text-lg">Usage Trends</h4>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">STT Calls</span>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{usageData.data.stt_calls?.toLocaleString() || '0'}</span>
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">TTS Calls</span>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{usageData.data.tts_calls?.toLocaleString() || '0'}</span>
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Top Intents & Questions */}
      <Card>
        <CardHeader>
          <CardTitle>Top Intents & Questions</CardTitle>
          <CardDescription>Most common user intents and questions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {topIntents.map((intent, index) => (
              <div key={index} className="border rounded-lg p-4 hover:bg-secondary/50 transition-colors">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="font-medium">
                      #{index + 1}
                    </Badge>
                    <h4 className="font-semibold">{intent.intent}</h4>
                    {getTrendIcon(intent.trend)}
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">{intent.count.toLocaleString()}</div>
                    <div className="text-sm text-gray-600">
                      {intent.percentage}% of total
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-gray-600" />
                      <span className="text-sm text-gray-600">
                        Avg: {Math.floor(intent.avgDuration / 60)}:{(intent.avgDuration % 60).toString().padStart(2, '0')}
                      </span>
                    </div>
                  </div>
                  <Progress value={intent.percentage} className="w-32 h-2" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Drop-offs by Step */}
      <Card>
        <CardHeader>
          <CardTitle>Drop-offs by Step</CardTitle>
          <CardDescription>Analyze where users drop off in the conversation flow</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {dropOffData.map((drop, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      {index === 0 && <CheckCircle className="h-4 w-4 text-green-500" />}
                      {index > 0 && index < dropOffData.length - 1 && <AlertTriangle className="h-4 w-4 text-yellow-500" />}
                      {index === dropOffData.length - 1 && <XCircle className="h-4 w-4 text-red-500" />}
                      <h4 className="font-semibold">{drop.step}</h4>
                    </div>
                    <Badge 
                      variant="outline" 
                      className={`${getDropOffColor(drop.percentage)} border-current`}
                    >
                      {drop.percentage}% drop-off
                    </Badge>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-600">
                      {drop.droppedOff.toLocaleString()} of {drop.totalReached.toLocaleString()}
                    </div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Drop-off Rate</span>
                    <span className="font-medium">{drop.percentage}%</span>
                  </div>
                  <Progress 
                    value={drop.percentage} 
                    className="h-2"
                    style={{
                      '--progress-background': drop.percentage < 5 ? '#10b981' : drop.percentage < 10 ? '#f59e0b' : '#ef4444'
                    } as React.CSSProperties}
                  />
                  {drop.reason && (
                    <div className="text-sm text-gray-600 mt-2">
                      <strong>Primary reason:</strong> {drop.reason}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default EnhancedAnalytics; 