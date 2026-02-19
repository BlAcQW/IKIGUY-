import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Activity, TrendingUp, Clock, AlertTriangle } from "lucide-react";

export const UsageTab = () => {
  // Mock data - in real implementation, fetch from API
  const usageData = {
    current_period: {
      requests: 1247,
      requests_limit: 10000,
      minutes: 23.5,
      minutes_limit: 100,
      period_start: "2024-01-01",
      period_end: "2024-01-31"
    },
    daily_stats: [
      { date: "2024-01-15", requests: 142, minutes: 2.3, errors: 1 },
      { date: "2024-01-14", requests: 98, minutes: 1.8, errors: 0 },
      { date: "2024-01-13", requests: 156, minutes: 3.1, errors: 2 },
      { date: "2024-01-12", requests: 203, minutes: 4.2, errors: 0 },
      { date: "2024-01-11", requests: 87, minutes: 1.5, errors: 1 }
    ],
    top_endpoints: [
      { path: "/v1/assistants", requests: 523, avg_latency: 245 },
      { path: "/v1/campaigns", requests: 312, avg_latency: 189 },
      { path: "/v1/kb/sources", requests: 198, avg_latency: 567 },
      { path: "/v1/analytics/summary", requests: 156, avg_latency: 123 },
      { path: "/v1/webhooks", requests: 58, avg_latency: 98 }
    ],
    error_breakdown: {
      "4xx": 23,
      "5xx": 7,
      "Rate Limited": 12
    }
  };

  const requestsPercentage = (usageData.current_period.requests / usageData.current_period.requests_limit) * 100;
  const minutesPercentage = (usageData.current_period.minutes / usageData.current_period.minutes_limit) * 100;

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Usage Analytics</h3>
        <p className="text-sm text-muted-foreground">
          Monitor your API usage, quotas, and performance metrics
        </p>
      </div>

      {/* Current Period Overview */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">API Requests</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{usageData.current_period.requests.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mb-2">
              of {usageData.current_period.requests_limit.toLocaleString()} this month
            </p>
            <Progress value={requestsPercentage} className="h-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {requestsPercentage.toFixed(1)}% used
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Call Minutes</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{usageData.current_period.minutes}</div>
            <p className="text-xs text-muted-foreground mb-2">
              of {usageData.current_period.minutes_limit} minutes this month
            </p>
            <Progress value={minutesPercentage} className="h-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {minutesPercentage.toFixed(1)}% used
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>API usage over the last 5 days</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {usageData.daily_stats.map((day) => (
              <div key={day.date} className="flex items-center justify-between py-2 border-b last:border-0">
                <div className="space-y-1">
                  <div className="font-medium">{new Date(day.date).toLocaleDateString()}</div>
                  <div className="text-sm text-muted-foreground">
                    {day.requests} requests • {day.minutes} minutes
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {day.errors > 0 && (
                    <Badge variant="destructive" className="text-xs">
                      {day.errors} errors
                    </Badge>
                  )}
                  <TrendingUp className="h-4 w-4 text-green-500" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Top Endpoints */}
        <Card>
          <CardHeader>
            <CardTitle>Top Endpoints</CardTitle>
            <CardDescription>Most frequently used API endpoints</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {usageData.top_endpoints.map((endpoint, index) => (
                <div key={endpoint.path} className="flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="font-mono text-sm">{endpoint.path}</div>
                    <div className="text-xs text-muted-foreground">
                      {endpoint.requests} requests • avg {endpoint.avg_latency}ms
                    </div>
                  </div>
                  <Badge variant="outline">#{index + 1}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Error Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Error Breakdown</CardTitle>
            <CardDescription>Errors by type this month</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(usageData.error_breakdown).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    <span className="font-medium">{type} Errors</span>
                  </div>
                  <Badge variant="secondary">{count}</Badge>
                </div>
              ))}
            </div>
            {Object.values(usageData.error_breakdown).reduce((a, b) => a + b, 0) === 0 && (
              <div className="text-center py-4 text-muted-foreground">
                No errors recorded this month
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Rate Limiting Info */}
      <Card>
        <CardHeader>
          <CardTitle>Rate Limits</CardTitle>
          <CardDescription>Current rate limiting configuration</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <div className="font-medium">Requests per Minute</div>
              <div className="text-2xl font-bold">300</div>
              <div className="text-xs text-muted-foreground">Burst limit</div>
            </div>
            <div className="space-y-2">
              <div className="font-medium">Requests per Hour</div>
              <div className="text-2xl font-bold">10,000</div>
              <div className="text-xs text-muted-foreground">Sustained limit</div>
            </div>
            <div className="space-y-2">
              <div className="font-medium">Concurrent Requests</div>
              <div className="text-2xl font-bold">10</div>
              <div className="text-xs text-muted-foreground">Max parallel</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};