import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { generateCallSummary } from '@/lib/gemini';
import { getVapiCallHistory, getVapiAssistant, getVapiCallDetails } from '@/lib/vapi';
import { ArrowLeft, Phone, Clock, DollarSign, TrendingUp, BarChart3, Calendar, User, MessageSquare, Play, Pause, Stop, Download, Eye, FileText, Activity, Zap, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface VoiceAgent {
  id: string;
  name: string;
  description: string;
  status: string;
  vapi_assistant_id: string;
  created_at: string;
  updated_at: string;
  user_id: string;
}

interface CallRecord {
  id: string;
  vapi_call_id: string;
  voice_agent_id: string;
  user_id: string;
  status: string;
  start_time: string;
  end_time?: string;
  duration_minutes?: number;
  total_cost?: number;
  communication_medium: string;
  transcript?: string;
  summary?: string;
  created_at: string;
}

interface CallAnalytics {
  total_calls: number;
  total_duration: number;
  total_cost: number;
  success_rate: number;
  average_duration: number;
  calls_by_status: Array<{ status: string; count: number }>;
  calls_by_medium: Array<{ medium: string; count: number }>;
  daily_calls: Array<{ date: string; count: number }>;
  cost_trend: Array<{ date: string; cost: number }>;
}

const VoiceAgentDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const { toast } = useToast();

  const [agent, setAgent] = useState<VoiceAgent | null>(null);
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [analytics, setAnalytics] = useState<CallAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCall, setSelectedCall] = useState<CallRecord | null>(null);
  const [showTranscript, setShowTranscript] = useState(false);
  const [timeRange, setTimeRange] = useState('7d');
  const [statusFilter, setStatusFilter] = useState('all');
  const [generatingSummary, setGeneratingSummary] = useState<string | null>(null);

  useEffect(() => {
    if (id && user) {
      loadAgentDetails();
      loadCallHistory();
      loadAnalytics();
    }
  }, [id, user, timeRange, statusFilter]);

  const loadAgentDetails = async () => {
    if (!user || !id) return;

    try {
      const { data, error } = await supabase
        .from('voice_agents')
        .select('*')
        .eq('id', id)
        .eq('user_id', user.id)
        .single();

      if (error) throw error;

      // Try to get additional details from Vapi API
      let vapiAssistant = null;
      try {
        if (data?.assistant_id) {
          vapiAssistant = await getVapiAssistant(data.assistant_id);
        }
      } catch (vapiError) {
        console.warn('Could not fetch Vapi assistant details:', vapiError);
      }

      setAgent({
        ...data,
        vapi_data: vapiAssistant
      });
    } catch (error) {
      console.error('Error loading agent details:', error);
      toast({
        title: "Error",
        description: "Failed to load agent details",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const loadCallHistory = async () => {
    if (!user || !id) return;

    try {
      // First try to get data from Supabase (our local database)
      let query = supabase
        .from('usage_tracking')
        .select('*')
        .eq('user_id', user.id)
        .eq('voice_agent_id', id)
        .order('start_time', { ascending: false });

      // Apply time range filter
      if (timeRange !== 'all') {
        const now = new Date();
        let startDate = new Date();
        
        switch (timeRange) {
          case '24h':
            startDate.setHours(now.getHours() - 24);
            break;
          case '7d':
            startDate.setDate(now.getDate() - 7);
            break;
          case '30d':
            startDate.setDate(now.getDate() - 30);
            break;
          case '90d':
            startDate.setDate(now.getDate() - 90);
            break;
        }
        
        query = query.gte('start_time', startDate.toISOString());
      }

      // Apply status filter
      if (statusFilter !== 'all') {
        query = query.eq('status', statusFilter);
      }

      const { data: supabaseData, error } = await query;

      if (error) throw error;

      // Try to get additional data from Vapi API
      let vapiData = [];
      try {
        if (agent?.assistant_id) {
          const vapiParams: any = {
            assistantId: agent.assistant_id,
            limit: 100
          };

          if (timeRange !== 'all') {
            const now = new Date();
            let startDate = new Date();
            
            switch (timeRange) {
              case '24h':
                startDate.setHours(now.getHours() - 24);
                break;
              case '7d':
                startDate.setDate(now.getDate() - 7);
                break;
              case '30d':
                startDate.setDate(now.getDate() - 30);
                break;
              case '90d':
                startDate.setDate(now.getDate() - 90);
                break;
            }
            
            vapiParams.startDate = startDate.toISOString();
            vapiParams.endDate = now.toISOString();
          }

          if (statusFilter !== 'all') {
            vapiParams.status = statusFilter;
          }

          vapiData = await getVapiCallHistory(vapiParams);
        }
      } catch (vapiError) {
        console.warn('Could not fetch Vapi call history:', vapiError);
      }

      // Merge and deduplicate data
      const mergedData = [...(supabaseData || [])];
      
      // Add Vapi data that's not already in Supabase
      vapiData.forEach(vapiCall => {
        const exists = mergedData.find(call => call.vapi_call_id === vapiCall.id);
        if (!exists) {
          mergedData.push({
            id: vapiCall.id,
            vapi_call_id: vapiCall.id,
            assistant_id: vapiCall.assistantId,
            voice_agent_id: id,
            user_id: user.id,
            status: vapiCall.status,
            start_time: vapiCall.startTime,
            end_time: vapiCall.endTime,
            duration_minutes: vapiCall.duration,
            total_cost: vapiCall.cost,
            transcript: vapiCall.transcript,
            summary: vapiCall.summary,
            communication_medium: 'phone',
            created_at: vapiCall.startTime,
            updated_at: vapiCall.endTime || vapiCall.startTime
          });
        }
      });

      // Sort by start time (newest first)
      mergedData.sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime());

      setCalls(mergedData);
    } catch (error) {
      console.error('Error loading call history:', error);
      toast({
        title: "Error",
        description: "Failed to load call history",
        variant: "destructive"
      });
    }
  };

  const loadAnalytics = async () => {
    if (!user || !id) return;

    try {
      const { data: callsData, error } = await supabase
        .from('usage_tracking')
        .select('*')
        .eq('user_id', user.id)
        .eq('voice_agent_id', id);

      if (error) throw error;

      if (callsData) {
        const total_calls = callsData.length;
        const total_duration = callsData.reduce((sum, call) => sum + (call.duration_minutes || 0), 0);
        const total_cost = callsData.reduce((sum, call) => sum + (call.total_cost || 0), 0);
        const completed_calls = callsData.filter(call => call.status === 'completed').length;
        const success_rate = total_calls > 0 ? (completed_calls / total_calls) * 100 : 0;
        const average_duration = total_calls > 0 ? total_duration / total_calls : 0;

        // Group calls by status
        const calls_by_status = Object.entries(
          callsData.reduce((acc, call) => {
            acc[call.status] = (acc[call.status] || 0) + 1;
            return acc;
          }, {} as Record<string, number>)
        ).map(([status, count]) => ({ status, count }));

        // Group calls by medium
        const calls_by_medium = Object.entries(
          callsData.reduce((acc, call) => {
            acc[call.communication_medium] = (acc[call.communication_medium] || 0) + 1;
            return acc;
          }, {} as Record<string, number>)
        ).map(([medium, count]) => ({ medium, count }));

        // Daily calls data
        const daily_calls = Object.entries(
          callsData.reduce((acc, call) => {
            const date = new Date(call.start_time).toLocaleDateString();
            acc[date] = (acc[date] || 0) + 1;
            return acc;
          }, {} as Record<string, number>)
        ).map(([date, count]) => ({ date, count }));

        // Cost trend data
        const cost_trend = Object.entries(
          callsData.reduce((acc, call) => {
            const date = new Date(call.start_time).toLocaleDateString();
            acc[date] = (acc[date] || 0) + (call.total_cost || 0);
            return acc;
          }, {} as Record<string, number>)
        ).map(([date, cost]) => ({ date, cost }));

        setAnalytics({
          total_calls,
          total_duration,
          total_cost,
          success_rate,
          average_duration,
          calls_by_status,
          calls_by_medium,
          daily_calls,
          cost_trend
        });
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
      toast({
        title: "Error",
        description: "Failed to load analytics data",
        variant: "destructive"
      });
    }
  };

  const generateSummaryWithGemini = async (callId: string, transcript: string) => {
    if (!transcript) return;

    setGeneratingSummary(callId);
    
    try {
      // Get the call record to include additional context
      const callRecord = calls.find(call => call.id === callId);
      
      // Generate summary using Gemini
      const summaryResponse = await generateCallSummary({
        transcript,
        callId,
        assistantName: agent?.name,
        callDuration: callRecord?.duration_minutes
      });

      // Create a formatted summary
      const formattedSummary = `${summaryResponse.summary}\n\nKey Points:\n${summaryResponse.keyPoints.map(point => `• ${point}`).join('\n')}\n\nSentiment: ${summaryResponse.sentiment}\n${summaryResponse.actionItems.length > 0 ? `\nAction Items:\n${summaryResponse.actionItems.map(item => `• ${item}`).join('\n')}` : ''}`;
      
      // Update the call record with the new summary
      const { error } = await supabase
        .from('usage_tracking')
        .update({ 
          summary: formattedSummary,
          // Store additional metadata if you have columns for it
          // sentiment: summaryResponse.sentiment,
          // key_points: summaryResponse.keyPoints,
          // action_items: summaryResponse.actionItems
        })
        .eq('id', callId);

      if (error) throw error;

      // Update local state
      setCalls(prev => prev.map(call => 
        call.id === callId ? { ...call, summary: formattedSummary } : call
      ));

      toast({
        title: "Success",
        description: "Summary generated successfully with AI analysis",
      });
    } catch (error) {
      console.error('Error generating summary:', error);
      toast({
        title: "Error",
        description: "Failed to generate summary. Please check your Gemini API key.",
        variant: "destructive"
      });
    } finally {
      setGeneratingSummary(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'in_progress':
        return <Activity className="h-4 w-4 text-blue-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-gray-600" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading agent details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Agent Not Found</h1>
          <p className="text-muted-foreground mb-4">The voice agent you're looking for doesn't exist or you don't have access to it.</p>
          <Button asChild>
            <Link to="/voice-agents">Back to Voice Agents</Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-4 mb-4">
          <Button variant="outline" size="sm" asChild>
            <Link to="/voice-agents">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Voice Agents
            </Link>
          </Button>
        </div>
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">{agent.name}</h1>
            <p className="text-muted-foreground">{agent.description}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={agent.status === 'active' ? 'default' : 'secondary'}>
              {agent.status}
            </Badge>
            <Button variant="outline" size="sm">
              <Play className="h-4 w-4 mr-2" />
              Test Call
            </Button>
          </div>
        </div>
      </div>

      {/* Analytics Overview */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
              <Phone className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.total_calls}</div>
              <p className="text-xs text-muted-foreground">
                All time
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Duration</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatDuration(analytics.total_duration)}</div>
              <p className="text-xs text-muted-foreground">
                Avg: {formatDuration(analytics.average_duration)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${analytics.total_cost.toFixed(2)}</div>
              <p className="text-xs text-muted-foreground">
                Lifetime spending
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.success_rate.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">
                Completed calls
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs defaultValue="analytics" className="space-y-6">
        <TabsList>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="calls">Call History</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="analytics" className="space-y-6">
          {analytics && (
            <>
              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Daily Call Volume</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={analytics.daily_calls}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Line type="monotone" dataKey="count" stroke="#8884d8" strokeWidth={2} />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Cost Trend</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={analytics.cost_trend}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Line type="monotone" dataKey="cost" stroke="#82ca9d" strokeWidth={2} />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>

              {/* Status and Medium Distribution */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Call Status Distribution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={analytics.calls_by_status}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ status, percent }) => `${status} ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="count"
                        >
                          {analytics.calls_by_status.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Communication Medium Distribution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={analytics.calls_by_medium}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ medium, percent }) => `${medium} ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="count"
                        >
                          {analytics.calls_by_medium.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </TabsContent>

        <TabsContent value="calls" className="space-y-6">
          {/* Filters */}
          <Card>
            <CardHeader>
              <CardTitle>Call History</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4 mb-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Time Range:</span>
                  <Select value={timeRange} onValueChange={setTimeRange}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="24h">Last 24h</SelectItem>
                      <SelectItem value="7d">Last 7 days</SelectItem>
                      <SelectItem value="30d">Last 30 days</SelectItem>
                      <SelectItem value="90d">Last 90 days</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Status:</span>
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                      <SelectItem value="in_progress">In Progress</SelectItem>
                      <SelectItem value="failed">Failed</SelectItem>
                      <SelectItem value="cancelled">Cancelled</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Calls Table */}
              <div className="border rounded-lg">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Status</TableHead>
                      <TableHead>Start Time</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Cost</TableHead>
                      <TableHead>Medium</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {calls.map((call) => (
                      <TableRow key={call.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {getStatusIcon(call.status)}
                            <Badge className={getStatusColor(call.status)}>
                              {call.status}
                            </Badge>
                          </div>
                        </TableCell>
                        <TableCell>{formatDate(call.start_time)}</TableCell>
                        <TableCell>{formatDuration(call.duration_minutes || 0)}</TableCell>
                        <TableCell>${call.total_cost?.toFixed(4) || '0.0000'}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="capitalize">
                            {call.communication_medium}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Dialog>
                              <DialogTrigger asChild>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => setSelectedCall(call)}
                                >
                                  <Eye className="h-4 w-4" />
                                </Button>
                              </DialogTrigger>
                              <DialogContent className="max-w-4xl">
                                <DialogHeader>
                                  <DialogTitle>Call Details</DialogTitle>
                                </DialogHeader>
                                <div className="space-y-4">
                                  <div className="grid grid-cols-2 gap-4">
                                    <div>
                                      <label className="text-sm font-medium">Call ID</label>
                                      <p className="text-sm text-muted-foreground">{call.vapi_call_id}</p>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium">Status</label>
                                      <p className="text-sm text-muted-foreground">{call.status}</p>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium">Start Time</label>
                                      <p className="text-sm text-muted-foreground">{formatDate(call.start_time)}</p>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium">End Time</label>
                                      <p className="text-sm text-muted-foreground">
                                        {call.end_time ? formatDate(call.end_time) : 'N/A'}
                                      </p>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium">Duration</label>
                                      <p className="text-sm text-muted-foreground">{formatDuration(call.duration_minutes || 0)}</p>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium">Cost</label>
                                      <p className="text-sm text-muted-foreground">${call.total_cost?.toFixed(4) || '0.0000'}</p>
                                    </div>
                                  </div>

                                  {call.transcript && (
                                    <div>
                                      <div className="flex items-center justify-between mb-2">
                                        <label className="text-sm font-medium">Transcript</label>
                                        <Button
                                          variant="outline"
                                          size="sm"
                                          onClick={() => setShowTranscript(!showTranscript)}
                                        >
                                          {showTranscript ? 'Hide' : 'Show'} Transcript
                                        </Button>
                                      </div>
                                      {showTranscript && (
                                        <div className="bg-gray-50 p-4 rounded-lg max-h-64 overflow-y-auto">
                                          <pre className="text-sm whitespace-pre-wrap">{call.transcript}</pre>
                                        </div>
                                      )}
                                    </div>
                                  )}

                                  {call.summary && (
                                    <div>
                                      <label className="text-sm font-medium">Summary</label>
                                      <div className="bg-blue-50 p-4 rounded-lg mt-2">
                                        <p className="text-sm">{call.summary}</p>
                                      </div>
                                    </div>
                                  )}

                                  {call.transcript && !call.summary && (
                                    <div>
                                      <Button
                                        onClick={() => generateSummaryWithGemini(call.id, call.transcript!)}
                                        disabled={generatingSummary === call.id}
                                        className="mt-2"
                                      >
                                        {generatingSummary === call.id ? (
                                          <>
                                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                            Generating Summary...
                                          </>
                                        ) : (
                                          <>
                                            <Zap className="h-4 w-4 mr-2" />
                                            Generate Summary with Gemini
                                          </>
                                        )}
                                      </Button>
                                    </div>
                                  )}
                                </div>
                              </DialogContent>
                            </Dialog>

                            {call.transcript && (
                              <Button variant="outline" size="sm">
                                <FileText className="h-4 w-4" />
                              </Button>
                            )}

                            <Button variant="outline" size="sm">
                              <Download className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {calls.length === 0 && (
                <div className="text-center py-8">
                  <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium mb-2">No calls found</h3>
                  <p className="text-muted-foreground">
                    This agent hasn't received any calls yet. Try adjusting your filters or make a test call.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Agent Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Vapi Assistant ID</label>
                  <p className="text-sm text-muted-foreground">{agent.vapi_assistant_id}</p>
                </div>
                <div>
                  <label className="text-sm font-medium">Created</label>
                  <p className="text-sm text-muted-foreground">{formatDate(agent.created_at)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium">Last Updated</label>
                  <p className="text-sm text-muted-foreground">{formatDate(agent.updated_at)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default VoiceAgentDetails;
