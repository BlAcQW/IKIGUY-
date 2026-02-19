import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Bot,
  Phone,
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  HelpCircle,
  Plus,
  Target,
  Building2,
  Users
} from 'lucide-react';
import { API_BASE_URL } from '@/config/api-config';
import { useOrganization } from '@/contexts/OrganizationContext';

interface DashboardStats {
  activeAutomations: number;
  runningCampaigns: number;
  connectRate: number;
  conversionRate: number;
  automationChange: string;
  campaignChange: string;
  connectRateChange: string;
  conversionRateChange: string;
  totalCalls?: number;
  totalDuration?: number;
  totalCost?: number;
  phoneNumbers?: number;
  totalAudience?: number;
  totalAudiences?: number;
  audienceChange?: string;
}

interface AutomationCallStats {
  automation_id: string;
  automation_name: string;
  assistant_id: string;
  total_calls: number;
  completed_calls: number;
  total_duration: number;
  avg_duration: number;
  total_cost: number;
}

interface RecentActivity {
  title: string;
  description: string;
  time: string;
  status: 'success' | 'info' | 'warning';
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { currentOrganization } = useOrganization();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats>({
    activeAutomations: 0,
    runningCampaigns: 0,
    connectRate: 0,
    conversionRate: 0,
    automationChange: '0',
    campaignChange: '0',
    connectRateChange: '0%',
    conversionRateChange: '0%'
  });
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [automationCallStats, setAutomationCallStats] = useState<AutomationCallStats[]>([]);

  useEffect(() => {
    fetchDashboardStats();
  }, [currentOrganization]);

  const fetchDashboardStats = async () => {
    setLoading(true);
    try {
      // Get auth token from localStorage (MongoDB auth uses mongo_access_token)
      const token = localStorage.getItem('mongo_access_token');

      // Fetch dashboard stats from the new unified endpoint
      const response = await fetch(`${API_BASE_URL}/api/analytics/dashboard-stats`, {
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
          ...(currentOrganization?.id && { 'X-Organization-ID': currentOrganization.id })
        }
      });

      if (response.ok) {
        const data = await response.json();

        if (data.success && data.stats) {
          setStats({
            activeAutomations: data.stats.activeAutomations || 0,
            runningCampaigns: data.stats.runningCampaigns || 0,
            connectRate: data.stats.connectRate || 0,
            conversionRate: data.stats.conversionRate || 0,
            automationChange: data.stats.automationChange || '0',
            campaignChange: data.stats.campaignChange || '0',
            connectRateChange: data.stats.connectRateChange || '0%',
            conversionRateChange: data.stats.conversionRateChange || '0%',
            totalCalls: data.stats.totalCalls,
            totalDuration: data.stats.totalDuration,
            totalCost: data.stats.totalCost,
            phoneNumbers: data.stats.phoneNumbers,
            totalAudience: data.stats.totalAudience,
            totalAudiences: data.stats.totalAudiences,
            audienceChange: data.stats.audienceChange || '0'
          });
        }

        if (data.recentActivity && data.recentActivity.length > 0) {
          setRecentActivity(data.recentActivity);
        } else {
          // Set empty state message if no activity
          setRecentActivity([]);
        }

        if (data.automationCallStats && data.automationCallStats.length > 0) {
          setAutomationCallStats(data.automationCallStats);
        }
      } else {
        console.error('Failed to fetch dashboard stats:', response.status);
      }
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  // Determine if change is positive or negative based on the value
  const getChangeType = (change: string): 'positive' | 'negative' | 'neutral' => {
    if (change.startsWith('+') && change !== '+0' && change !== '+0%') return 'positive';
    if (change.startsWith('-')) return 'negative';
    return 'neutral';
  };

  const statCards = [
    {
      title: "Active Automations",
      value: stats.activeAutomations,
      change: stats.automationChange,
      changeType: getChangeType(stats.automationChange),
      description: "Deployed automation workflows",
      icon: Bot
    },
    {
      title: "Active Campaigns",
      value: stats.runningCampaigns,
      change: stats.campaignChange,
      changeType: getChangeType(stats.campaignChange),
      description: "Outbound campaigns in progress",
      icon: Phone
    },
    {
      title: "Total Calls",
      value: stats.totalCalls || 0,
      change: undefined,
      changeType: 'neutral',
      description: "Total calls in last 7 days",
      icon: Phone
    },
    {
      title: "Total Audience",
      value: (stats.totalAudience || 0).toLocaleString(),
      change: stats.audienceChange,
      changeType: getChangeType(stats.audienceChange || '0'),
      description: `Across ${stats.totalAudiences || 0} audience${(stats.totalAudiences || 0) !== 1 ? 's' : ''}`,
      icon: Users
    },
    {
      title: "Connect Rate",
      value: `${stats.connectRate}%`,
      change: stats.connectRateChange,
      changeType: getChangeType(stats.connectRateChange),
      description: "Calls answered this week",
      icon: Target
    },
    {
      title: "Conversion Rate",
      value: `${stats.conversionRate}%`,
      change: stats.conversionRateChange,
      changeType: getChangeType(stats.conversionRateChange),
      description: "Successful outcomes this week",
      icon: TrendingUp
    }
  ];

  return (
    <div className="flex h-screen bg-background">
      <DashboardSidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
                  {currentOrganization && (
                    <Badge variant="outline" className="flex items-center gap-1.5 px-3 py-1 text-sm">
                      <Building2 className="h-3.5 w-3.5" />
                      {currentOrganization.display_name}
                    </Badge>
                  )}
                </div>
                <p className="text-muted-foreground">
                  Welcome back! Here's what's happening with your automations.
                </p>
              </div>
              <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
            </div>
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                onClick={() => navigate('/automations')}
              >
                <Activity className="mr-2 h-4 w-4" />
                View All Activity
              </Button>
              <Button onClick={() => navigate('/automations/new')}>
                <Plus className="mr-2 h-4 w-4" />
                Create Campaign
              </Button>
            </div>
          </div>

          {/* KPI Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {statCards.map((card) => {
              const Icon = card.icon;
              const ChangeIcon = card.changeType === 'positive' ? TrendingUp :
                                 card.changeType === 'negative' ? TrendingDown : Activity;
              const changeColor = card.changeType === 'positive' ? 'text-green-500' :
                                  card.changeType === 'negative' ? 'text-red-500' : 'text-muted-foreground';
              return (
                <Card key={card.title}>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      {card.title}
                    </CardTitle>
                    <Icon className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {loading ? <span className="animate-pulse">...</span> : card.value}
                    </div>
                    <p className="text-xs text-muted-foreground flex items-center mt-1">
                      {card.change && card.changeType !== 'neutral' && (
                        <>
                          <ChangeIcon className={`mr-1 h-3 w-3 ${changeColor}`} />
                          <span className={changeColor}>
                            {card.change}
                          </span>
                        </>
                      )}
                      <span className={card.change && card.changeType !== 'neutral' ? "ml-1" : ""}>{card.description}</span>
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            {/* Active Campaigns */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Phone className="mr-2 h-5 w-5" />
                    <CardTitle>Active Campaigns</CardTitle>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">
                  Monitor your ongoing outbound campaigns
                </p>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-muted-foreground">
                  No active campaigns found
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <div className="flex items-center">
                  <Clock className="mr-2 h-5 w-5" />
                  <CardTitle>Recent Activity</CardTitle>
                </div>
                <p className="text-sm text-muted-foreground">
                  Latest call activity from your automations
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                {loading ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <div className="animate-pulse">Loading activity...</div>
                  </div>
                ) : recentActivity.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No recent activity found
                  </div>
                ) : (
                  recentActivity.map((activity, index) => (
                    <div key={index} className="flex items-start space-x-3 pb-3 border-b last:border-0 last:pb-0">
                      <div className={`mt-1 h-2 w-2 rounded-full flex-shrink-0 ${
                        activity.status === "success" ? "bg-green-500" :
                        activity.status === "warning" ? "bg-yellow-500" :
                        "bg-blue-500"
                      }`} />
                      <div className="flex-1 space-y-1 min-w-0">
                        <p className="font-medium text-sm">{activity.title}</p>
                        <p className="text-xs text-muted-foreground line-clamp-2">{activity.description}</p>
                        <p className="text-xs text-muted-foreground">{activity.time}</p>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* Automation Call Statistics */}
          {automationCallStats.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center">
                  <Bot className="mr-2 h-5 w-5" />
                  <CardTitle>Automation Call Statistics (Last 7 Days)</CardTitle>
                </div>
                <p className="text-sm text-muted-foreground">
                  Call metrics for each automation with Vapi assistant
                </p>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {automationCallStats.map((automation, index) => (
                    <div key={automation.automation_id} className="flex items-center justify-between pb-4 border-b last:border-0 last:pb-0">
                      <div className="flex-1">
                        <p className="font-medium text-sm">{automation.automation_name}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          Assistant ID: {automation.assistant_id.substring(0, 8)}...
                        </p>
                      </div>
                      <div className="flex items-center gap-6 text-sm">
                        <div className="text-right">
                          <p className="font-semibold">{automation.total_calls}</p>
                          <p className="text-xs text-muted-foreground">Total Calls</p>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold">{automation.completed_calls}</p>
                          <p className="text-xs text-muted-foreground">Completed</p>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold">{Math.round(automation.avg_duration)}s</p>
                          <p className="text-xs text-muted-foreground">Avg Duration</p>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold">${automation.total_cost.toFixed(2)}</p>
                          <p className="text-xs text-muted-foreground">Cost</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
