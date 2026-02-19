import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { 
  DollarSign, 
  Clock, 
  Phone, 
  Calendar, 
  TrendingUp, 
  BarChart3, 
  FileText, 
  Eye,
  Download,
  RefreshCw,
  Filter
} from 'lucide-react';

interface CallData {
  id: string;
  assistantId: string;
  assistantName?: string;
  status: string;
  duration: number;
  cost: number;
  startTime: string;
  endTime: string;
  transcript?: string;
  summary?: string;
  metadata?: Record<string, any>;
  phoneNumber?: string;
  callType: 'inbound' | 'outbound' | 'web';
  createdAt: string;
  updatedAt: string;
}

interface AnalyticsResponse {
  calls: CallData[];
  totalMinutes: number;
  totalCost: number;
  callCount: number;
  assistantBreakdown: {
    assistantId: string;
    assistantName: string;
    callCount: number;
    totalMinutes: number;
    totalCost: number;
    avgDuration: number;
  }[];
  timeRange: {
    start: string;
    end: string;
  };
}

const CostTracking = () => {
  const { toast } = useToast();
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedAssistant, setSelectedAssistant] = useState<string>('all');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [selectedCall, setSelectedCall] = useState<CallData | null>(null);

  // Set default date range (last 30 days)
  useEffect(() => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    
    setEndDate(end.toISOString().split('T')[0]);
    setStartDate(start.toISOString().split('T')[0]);
  }, []);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('fetch-call-analytics', {
        body: {
          assistantId: selectedAssistant === 'all' ? undefined : selectedAssistant,
          startDate: startDate ? new Date(startDate).toISOString() : undefined,
          endDate: endDate ? new Date(endDate + 'T23:59:59').toISOString() : undefined,
        }
      });

      if (error) throw error;
      setAnalytics(data);
      
      toast({
        title: "Analytics Updated",
        description: `Fetched ${data.callCount} calls with ${data.totalMinutes.toFixed(1)} minutes of usage.`,
      });
    } catch (error: any) {
      console.error('Error fetching analytics:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to fetch analytics",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (startDate && endDate) {
      fetchAnalytics();
    }
  }, [startDate, endDate, selectedAssistant]);

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const formatCost = (cost: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(cost);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const exportData = () => {
    if (!analytics) return;
    
    const csvData = [
      ['Call ID', 'Assistant', 'Duration (min)', 'Cost ($)', 'Start Time', 'End Time', 'Status', 'Type'],
      ...analytics.calls.map(call => [
        call.id,
        call.assistantName || 'Unknown',
        (call.duration / 60).toFixed(2),
        call.cost.toFixed(2),
        formatDate(call.startTime),
        formatDate(call.endTime),
        call.status,
        call.callType
      ])
    ];

    const csvContent = csvData.map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `call-analytics-${startDate}-to-${endDate}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (!analytics) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-3xl font-bold">Cost Tracking</h2>
          <Button onClick={fetchAnalytics} disabled={loading}>
            {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Refresh
          </Button>
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="text-center text-muted-foreground">
              {loading ? "Loading analytics..." : "No analytics data available"}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold">Cost Tracking</h2>
          <p className="text-muted-foreground">
            Monitor your Vapi usage, costs, and call analytics
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={exportData}>
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
          <Button onClick={fetchAnalytics} disabled={loading}>
            {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Refresh
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label>Assistant</Label>
              <Select value={selectedAssistant} onValueChange={setSelectedAssistant}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Assistants</SelectItem>
                  {analytics.assistantBreakdown.map(assistant => (
                    <SelectItem key={assistant.assistantId} value={assistant.assistantId}>
                      {assistant.assistantName}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Start Date</Label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>End Date</Label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Time Range</Label>
              <div className="text-sm text-muted-foreground">
                {formatDate(analytics.timeRange.start)} - {formatDate(analytics.timeRange.end)}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
            <Phone className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.callCount}</div>
            <p className="text-xs text-muted-foreground">
              Across {analytics.assistantBreakdown.length} assistants
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Minutes</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.totalMinutes.toFixed(1)}</div>
            <p className="text-xs text-muted-foreground">
              Average {analytics.callCount > 0 ? (analytics.totalMinutes / analytics.callCount).toFixed(1) : 0} min/call
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCost(analytics.totalCost)}</div>
            <p className="text-xs text-muted-foreground">
              ${(analytics.totalCost / analytics.totalMinutes * 60).toFixed(2)}/hour
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Assistants</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.assistantBreakdown.length}</div>
            <p className="text-xs text-muted-foreground">
              With call activity
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analytics */}
      <Tabs defaultValue="assistants" className="space-y-4">
        <TabsList>
          <TabsTrigger value="assistants">Assistant Breakdown</TabsTrigger>
          <TabsTrigger value="calls">Call Details</TabsTrigger>
        </TabsList>

        <TabsContent value="assistants" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Assistant Performance</CardTitle>
              <CardDescription>
                Cost and usage breakdown by assistant
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Assistant</TableHead>
                    <TableHead>Calls</TableHead>
                    <TableHead>Total Minutes</TableHead>
                    <TableHead>Avg Duration</TableHead>
                    <TableHead>Total Cost</TableHead>
                    <TableHead>Cost/Call</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {analytics.assistantBreakdown.map((assistant) => (
                    <TableRow key={assistant.assistantId}>
                      <TableCell className="font-medium">{assistant.assistantName}</TableCell>
                      <TableCell>{assistant.callCount}</TableCell>
                      <TableCell>{assistant.totalMinutes.toFixed(1)} min</TableCell>
                      <TableCell>{formatDuration(assistant.avgDuration)}</TableCell>
                      <TableCell>{formatCost(assistant.totalCost)}</TableCell>
                      <TableCell>{formatCost(assistant.totalCost / assistant.callCount)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="calls" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Call History</CardTitle>
              <CardDescription>
                Detailed call information with transcripts and metadata
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Assistant</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Cost</TableHead>
                    <TableHead>Start Time</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {analytics.calls.map((call) => (
                    <TableRow key={call.id}>
                      <TableCell className="font-medium">{call.assistantName}</TableCell>
                      <TableCell>{formatDuration(call.duration)}</TableCell>
                      <TableCell>{formatCost(call.cost)}</TableCell>
                      <TableCell>{formatDate(call.startTime)}</TableCell>
                      <TableCell>
                        <Badge variant={call.status === 'completed' ? 'default' : 'secondary'}>
                          {call.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{call.callType}</Badge>
                      </TableCell>
                      <TableCell>
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setSelectedCall(call)}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                            <DialogHeader>
                              <DialogTitle>Call Details - {call.assistantName}</DialogTitle>
                              <DialogDescription>
                                Call ID: {call.id}
                              </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4">
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <Label className="text-sm font-medium">Duration</Label>
                                  <p>{formatDuration(call.duration)}</p>
                                </div>
                                <div>
                                  <Label className="text-sm font-medium">Cost</Label>
                                  <p>{formatCost(call.cost)}</p>
                                </div>
                                <div>
                                  <Label className="text-sm font-medium">Start Time</Label>
                                  <p>{formatDate(call.startTime)}</p>
                                </div>
                                <div>
                                  <Label className="text-sm font-medium">End Time</Label>
                                  <p>{formatDate(call.endTime)}</p>
                                </div>
                                <div>
                                  <Label className="text-sm font-medium">Status</Label>
                                  <Badge variant={call.status === 'completed' ? 'default' : 'secondary'}>
                                    {call.status}
                                  </Badge>
                                </div>
                                <div>
                                  <Label className="text-sm font-medium">Type</Label>
                                  <Badge variant="outline">{call.callType}</Badge>
                                </div>
                              </div>
                              
                              {call.phoneNumber && (
                                <div>
                                  <Label className="text-sm font-medium">Phone Number</Label>
                                  <p>{call.phoneNumber}</p>
                                </div>
                              )}

                              {call.transcript && (
                                <div>
                                  <Label className="text-sm font-medium flex items-center gap-2">
                                    <FileText className="h-4 w-4" />
                                    Transcript
                                  </Label>
                                  <div className="mt-2 p-3 bg-muted rounded-md max-h-40 overflow-y-auto">
                                    <pre className="text-sm whitespace-pre-wrap">{call.transcript}</pre>
                                  </div>
                                </div>
                              )}

                              {call.summary && (
                                <div>
                                  <Label className="text-sm font-medium">Summary</Label>
                                  <div className="mt-2 p-3 bg-muted rounded-md">
                                    <p className="text-sm">{call.summary}</p>
                                  </div>
                                </div>
                              )}

                              {call.metadata && Object.keys(call.metadata).length > 0 && (
                                <div>
                                  <Label className="text-sm font-medium">Metadata</Label>
                                  <div className="mt-2 p-3 bg-muted rounded-md">
                                    <pre className="text-sm overflow-x-auto">
                                      {JSON.stringify(call.metadata, null, 2)}
                                    </pre>
                                  </div>
                                </div>
                              )}
                            </div>
                          </DialogContent>
                        </Dialog>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CostTracking;
