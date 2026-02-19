import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';

interface TrendData {
  date: string;
  deployments: number;
  successes: number;
  failures: number;
}

interface DeploymentTrendsChartProps {
  trends: TrendData[];
  isLoading: boolean;
}

const DeploymentTrendsChart: React.FC<DeploymentTrendsChartProps> = ({
  trends,
  isLoading
}) => {
  if (isLoading) {
    return (
      <Card className="animate-pulse">
        <CardHeader>
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </CardHeader>
        <CardContent>
          <div className="h-64 bg-gray-200 rounded"></div>
        </CardContent>
      </Card>
    );
  }

  if (!trends || trends.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Deployment Trends</CardTitle>
          <CardDescription>
            Historical deployment performance over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <BarChart3 className="h-16 w-16 mb-4" />
            <p>No deployment trend data available</p>
            <p className="text-sm">Deploy some automations to see trends</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const maxDeployments = Math.max(...trends.map(t => t.deployments));
  const totalDeployments = trends.reduce((sum, t) => sum + t.deployments, 0);
  const totalSuccesses = trends.reduce((sum, t) => sum + t.successes, 0);
  const overallSuccessRate = totalDeployments > 0 ? (totalSuccesses / totalDeployments) * 100 : 0;

  const getBarHeight = (value: number) => {
    if (maxDeployments === 0) return 0;
    return (value / maxDeployments) * 100;
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Deployment Trends</CardTitle>
            <CardDescription>
              Historical deployment performance over the selected period
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="flex items-center">
              {overallSuccessRate >= 80 ? (
                <TrendingUp className="h-3 w-3 text-green-600 mr-1" />
              ) : (
                <TrendingDown className="h-3 w-3 text-red-600 mr-1" />
              )}
              {overallSuccessRate.toFixed(1)}% Success
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Chart Legend */}
          <div className="flex items-center space-x-4 text-sm">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-500 rounded mr-2"></div>
              Total Deployments
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded mr-2"></div>
              Successful
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-red-500 rounded mr-2"></div>
              Failed
            </div>
          </div>

          {/* Simple Bar Chart */}
          <div className="h-48 flex items-end space-x-2 border-b border-gray-200">
            {trends.map((trend, index) => (
              <div
                key={trend.date}
                className="flex-1 flex flex-col items-center space-y-1"
              >
                {/* Bars */}
                <div className="w-full flex flex-col items-center space-y-1">
                  {/* Total deployments bar */}
                  <div className="w-6 bg-blue-200 rounded-t" style={{
                    height: `${getBarHeight(trend.deployments)}%`,
                    minHeight: trend.deployments > 0 ? '4px' : '0px'
                  }}>
                    {/* Success portion */}
                    <div
                      className="w-full bg-green-500 rounded-t"
                      style={{
                        height: `${(trend.successes / Math.max(trend.deployments, 1)) * 100}%`
                      }}
                    ></div>
                  </div>
                </div>

                {/* Date label */}
                <span className="text-xs text-muted-foreground transform rotate-45 origin-left">
                  {new Date(trend.date).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric'
                  })}
                </span>
              </div>
            ))}
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-4 pt-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">{totalDeployments}</p>
              <p className="text-sm text-muted-foreground">Total Deployments</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{totalSuccesses}</p>
              <p className="text-sm text-muted-foreground">Successful</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">{totalDeployments - totalSuccesses}</p>
              <p className="text-sm text-muted-foreground">Failed</p>
            </div>
          </div>

          {/* Trend Details */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium mb-2">Recent Activity</h4>
            <div className="space-y-2">
              {trends.slice(-3).map((trend, index) => (
                <div key={trend.date} className="flex items-center justify-between text-sm">
                  <span>{new Date(trend.date).toLocaleDateString()}</span>
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline" className="text-xs">
                      {trend.deployments} deployments
                    </Badge>
                    <Badge
                      variant={trend.successes === trend.deployments ? "default" : "destructive"}
                      className="text-xs"
                    >
                      {trend.deployments > 0
                        ? ((trend.successes / trend.deployments) * 100).toFixed(1)
                        : 0}% success
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default DeploymentTrendsChart;