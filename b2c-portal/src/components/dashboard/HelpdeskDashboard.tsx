import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Headphones,
  BarChart3,
  Calendar,
  Ticket,
  Users,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  MoreHorizontal,
  Play,
  Pause,
  Settings,
  Eye,
  Trash2,
  Phone,
  Star,
  MessageSquare,
  Activity
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import { getAuthHeaders } from '@/lib/auth-utils';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


interface HelpdeskStats {
  total_calls: number;
  successful_calls: number;
  success_rate: number;
  avg_call_duration: number;
  appointments_booked: number;
  tickets_created: number;
  customer_satisfaction: number;
  escalation_rate: number;
}

interface HelpdeskCampaign {
  id: string;
  company_name: string;
  status: 'active' | 'inactive' | 'paused';
  demo_url: string;
  analytics_url: string;
  vapi_assistant_id: string;
  created_at: string;
  stats: HelpdeskStats;
}

interface AnalyticsData {
  overview: HelpdeskStats;
  actions: {
    appointments_booked: number;
    tickets_created: number;
    knowledge_searches: number;
    escalations: number;
  };
  trends: {
    daily_calls: number[];
    daily_success_rate: number[];
    daily_satisfaction: number[];
  };
  top_intents: Array<{
    intent: string;
    count: number;
    percentage: number;
  }>;
}

export const HelpdeskDashboard: React.FC = () => {
  const [helpdesks, setHelpdesks] = useState<HelpdeskCampaign[]>([]);
  const [selectedHelpdesk, setSelectedHelpdesk] = useState<string | null>(null);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const { toast } = useToast();
  const { user, getTenantId } = useMongoAuth();

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || API_BASE_URL;

  useEffect(() => {
    fetchHelpdesks();
  }, []);

  useEffect(() => {
    if (selectedHelpdesk) {
      fetchAnalytics(selectedHelpdesk);
    }
  }, [selectedHelpdesk]);

  const fetchHelpdesks = async () => {
    try {
      setLoading(true);
      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/enhanced-helpdesk/list`, {
        headers: authHeaders
      });

      if (!response.ok) {
        throw new Error('Failed to fetch helpdesks');
      }

      const data = await response.json();
      setHelpdesks(data.data || []);

      // Select first helpdesk by default
      if (data.data?.length > 0 && !selectedHelpdesk) {
        setSelectedHelpdesk(data.data[0].id);
      }
    } catch (error) {
      console.error('Error fetching helpdesks:', error);
      toast({
        title: "Error",
        description: "Failed to load helpdesk campaigns",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async (helpdeskId: string) => {
    try {
      setAnalyticsLoading(true);
      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/enhanced-helpdesk/${helpdeskId}/analytics`, {
        headers: authHeaders
      });

      if (!response.ok) {
        throw new Error('Failed to fetch analytics');
      }

      const data = await response.json();
      setAnalyticsData(data.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      toast({
        title: "Error",
        description: "Failed to load analytics data",
        variant: "destructive"
      });
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const toggleHelpdeskStatus = async (helpdeskId: string) => {
    try {
      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/enhanced-helpdesk/${helpdeskId}/toggle`, {
        method: 'POST',
        headers: authHeaders
      });

      if (!response.ok) {
        throw new Error('Failed to toggle status');
      }

      toast({
        title: "Success",
        description: "Helpdesk status updated successfully"
      });

      fetchHelpdesks();
    } catch (error) {
      console.error('Error toggling status:', error);
      toast({
        title: "Error",
        description: "Failed to update helpdesk status",
        variant: "destructive"
      });
    }
  };

  const deleteHelpdesk = async (helpdeskId: string) => {
    if (!confirm('Are you sure you want to delete this helpdesk? This action cannot be undone.')) {
      return;
    }

    try {
      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/enhanced-helpdesk/${helpdeskId}`, {
        method: 'DELETE',
        headers: authHeaders
      });

      if (!response.ok) {
        throw new Error('Failed to delete helpdesk');
      }

      toast({
        title: "Success",
        description: "Helpdesk deleted successfully"
      });

      fetchHelpdesks();
      if (selectedHelpdesk === helpdeskId) {
        setSelectedHelpdesk(null);
        setAnalyticsData(null);
      }
    } catch (error) {
      console.error('Error deleting helpdesk:', error);
      toast({
        title: "Error",
        description: "Failed to delete helpdesk",
        variant: "destructive"
      });
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      active: { variant: 'default' as const, color: 'bg-green-500', label: 'Active' },
      inactive: { variant: 'secondary' as const, color: 'bg-gray-500', label: 'Inactive' },
      paused: { variant: 'outline' as const, color: 'bg-yellow-500', label: 'Paused' }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.inactive;

    return (
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${config.color}`} />
        <Badge variant={config.variant}>{config.label}</Badge>
      </div>
    );
  };

  const selectedHelpdeskData = helpdesks.find(h => h.id === selectedHelpdesk);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (helpdesks.length === 0) {
    return (
      <div className="text-center py-12">
        <Headphones className="h-12 w-12 mx-auto text-gray-600 mb-4" />
        <h3 className="text-lg font-semibold mb-2">No Helpdesk Campaigns</h3>
        <p className="text-gray-600 mb-4">
          Create your first enhanced helpdesk campaign to start providing AI-powered customer support.
        </p>
        <Button onClick={() => window.location.href = '/campaigns'}>
          Create Helpdesk Campaign
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Helpdesk Dashboard</h1>
          <p className="text-gray-600">Monitor and manage your AI-powered helpdesk campaigns</p>
        </div>
        <Button onClick={() => window.location.href = '/campaigns'} className="gap-2">
          <Headphones className="h-4 w-4" />
          Create New Helpdesk
        </Button>
      </div>

      {/* Helpdesk Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Headphones className="h-5 w-5" />
            Active Helpdesk Campaigns
          </CardTitle>
          <CardDescription>Select a helpdesk to view detailed analytics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {helpdesks.map((helpdesk) => (
              <Card
                key={helpdesk.id}
                className={`cursor-pointer transition-all hover:shadow-md ${
                  selectedHelpdesk === helpdesk.id ? 'ring-2 ring-primary border-primary' : ''
                }`}
                onClick={() => setSelectedHelpdesk(helpdesk.id)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-base">{helpdesk.company_name}</CardTitle>
                      <CardDescription className="text-xs">
                        {new Date(helpdesk.created_at).toLocaleDateString()}
                      </CardDescription>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => window.open(helpdesk.demo_url, '_blank')}>
                          <Eye className="h-4 w-4 mr-2" />
                          View Demo
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => toggleHelpdeskStatus(helpdesk.id)}>
                          {helpdesk.status === 'active' ? (
                            <>
                              <Pause className="h-4 w-4 mr-2" />
                              Pause
                            </>
                          ) : (
                            <>
                              <Play className="h-4 w-4 mr-2" />
                              Activate
                            </>
                          )}
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => deleteHelpdesk(helpdesk.id)} className="text-red-600">
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    {getStatusBadge(helpdesk.status)}
                    <div className="flex items-center gap-2 text-xs text-gray-600">
                      <Phone className="h-3 w-3" />
                      {helpdesk.stats.total_calls} calls
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <div className="font-medium">{helpdesk.stats.success_rate.toFixed(1)}%</div>
                      <div className="text-gray-600">Success Rate</div>
                    </div>
                    <div>
                      <div className="font-medium">{helpdesk.stats.customer_satisfaction.toFixed(1)}</div>
                      <div className="text-gray-600">Satisfaction</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Analytics Dashboard */}
      {selectedHelpdeskData && (
        <Tabs defaultValue="overview" className="space-y-6">
          <div className="flex items-center justify-between">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
              <TabsTrigger value="intents">Top Intents</TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </TabsList>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(selectedHelpdeskData.demo_url, '_blank')}
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                View Demo
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(selectedHelpdeskData.analytics_url, '_blank')}
              >
                <BarChart3 className="h-4 w-4 mr-2" />
                Full Analytics
              </Button>
            </div>
          </div>

          <TabsContent value="overview" className="space-y-6">
            {/* Key Metrics */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
                  <Phone className="h-4 w-4 text-gray-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{selectedHelpdeskData.stats.total_calls.toLocaleString()}</div>
                  <p className="text-xs text-gray-600">
                    {selectedHelpdeskData.stats.successful_calls} successful
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
                  <TrendingUp className="h-4 w-4 text-gray-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{selectedHelpdeskData.stats.success_rate.toFixed(1)}%</div>
                  <Progress value={selectedHelpdeskData.stats.success_rate} className="mt-2" />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Appointments</CardTitle>
                  <Calendar className="h-4 w-4 text-gray-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{selectedHelpdeskData.stats.appointments_booked}</div>
                  <p className="text-xs text-gray-600">
                    {((selectedHelpdeskData.stats.appointments_booked / selectedHelpdeskData.stats.total_calls) * 100).toFixed(1)}% conversion
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Satisfaction</CardTitle>
                  <Star className="h-4 w-4 text-gray-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{selectedHelpdeskData.stats.customer_satisfaction.toFixed(1)}</div>
                  <p className="text-xs text-gray-600">
                    Average rating out of 5.0
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Action Summary */}
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5" />
                    Actions Performed
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-blue-500" />
                      <span className="text-sm">Appointments Booked</span>
                    </div>
                    <span className="font-medium">{selectedHelpdeskData.stats.appointments_booked}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Ticket className="h-4 w-4 text-green-500" />
                      <span className="text-sm">Support Tickets</span>
                    </div>
                    <span className="font-medium">{selectedHelpdeskData.stats.tickets_created}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <AlertCircle className="h-4 w-4 text-orange-500" />
                      <span className="text-sm">Escalations</span>
                    </div>
                    <span className="font-medium">
                      {Math.round((selectedHelpdeskData.stats.escalation_rate / 100) * selectedHelpdeskData.stats.total_calls)}
                    </span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    Performance Metrics
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Average Call Duration</span>
                    <span className="font-medium">{selectedHelpdeskData.stats.avg_call_duration.toFixed(1)} min</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Escalation Rate</span>
                    <span className="font-medium">{selectedHelpdeskData.stats.escalation_rate.toFixed(1)}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Response Quality</span>
                    <span className="font-medium text-green-600">Excellent</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6">
            {analyticsLoading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : analyticsData ? (
              <div className="grid gap-6 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Call Trends (7 days)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {analyticsData.trends.daily_calls.map((calls, index) => (
                        <div key={index} className="flex items-center gap-4">
                          <span className="text-sm w-16">Day {index + 1}</span>
                          <div className="flex-1 bg-muted rounded-full h-2">
                            <div
                              className="bg-indigo-600 h-2 rounded-full"
                              style={{
                                width: `${(calls / Math.max(...analyticsData.trends.daily_calls)) * 100}%`
                              }}
                            />
                          </div>
                          <span className="text-sm font-medium w-8">{calls}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Success Rate Trends</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {analyticsData.trends.daily_success_rate.map((rate, index) => (
                        <div key={index} className="flex items-center gap-4">
                          <span className="text-sm w-16">Day {index + 1}</span>
                          <div className="flex-1 bg-muted rounded-full h-2">
                            <div
                              className="bg-green-500 h-2 rounded-full"
                              style={{ width: `${rate}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium w-12">{rate}%</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <div className="text-center py-8">
                <BarChart3 className="h-12 w-12 mx-auto text-gray-600 mb-4" />
                <p className="text-gray-600">No analytics data available</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="intents" className="space-y-6">
            {analyticsData ? (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5" />
                    Top Customer Intents
                  </CardTitle>
                  <CardDescription>Most common reasons customers contact your helpdesk</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {analyticsData.top_intents.map((intent, index) => (
                      <div key={index} className="flex items-center gap-4">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                          <span className="text-sm font-medium">{index + 1}</span>
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium">{intent.intent}</span>
                            <span className="text-sm text-gray-600">{intent.percentage}%</span>
                          </div>
                          <Progress value={intent.percentage} className="h-2" />
                        </div>
                        <span className="text-sm font-medium w-12">{intent.count}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="text-center py-8">
                <MessageSquare className="h-12 w-12 mx-auto text-gray-600 mb-4" />
                <p className="text-gray-600">No intent data available</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Helpdesk Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="text-sm font-medium">Company Name</label>
                    <p className="text-sm text-gray-600">{selectedHelpdeskData.company_name}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium">VAPI Assistant ID</label>
                    <p className="text-sm text-gray-600">{selectedHelpdeskData.vapi_assistant_id}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Status</label>
                    <div className="mt-1">{getStatusBadge(selectedHelpdeskData.status)}</div>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Created</label>
                    <p className="text-sm text-gray-600">
                      {new Date(selectedHelpdeskData.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="flex gap-2 pt-4 border-t">
                  <Button variant="outline" onClick={() => window.open(selectedHelpdeskData.demo_url, '_blank')}>
                    <ExternalLink className="h-4 w-4 mr-2" />
                    View Demo
                  </Button>
                  <Button variant="outline" onClick={() => window.open(selectedHelpdeskData.analytics_url, '_blank')}>
                    <BarChart3 className="h-4 w-4 mr-2" />
                    Full Analytics
                  </Button>
                  <Button
                    variant={selectedHelpdeskData.status === 'active' ? 'secondary' : 'default'}
                    onClick={() => toggleHelpdeskStatus(selectedHelpdeskData.id)}
                  >
                    {selectedHelpdeskData.status === 'active' ? (
                      <>
                        <Pause className="h-4 w-4 mr-2" />
                        Pause
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4 mr-2" />
                        Activate
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
};