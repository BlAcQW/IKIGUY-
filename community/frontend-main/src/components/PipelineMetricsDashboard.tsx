/**
 * Pipeline Metrics Dashboard Component
 *
 * Real-time metrics dashboard for monitoring pipeline performance:
 * - Live metric updates
 * - Training progress visualization
 * - Loss/accuracy charts
 * - Resource utilization
 * - Stage-specific metrics
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Clock,
  Cpu,
  HardDrive,
  Zap,
  Target,
  AlertCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface MetricValue {
  value: number;
  unit: string;
  trend?: 'up' | 'down' | 'stable';
  change?: number;
}

interface StageMetrics {
  stage_name: string;
  metrics: Record<string, any>;
  resource_usage?: {
    cpu_percent: number;
    memory_mb: number;
    gpu_percent?: number;
  };
  timestamps: string[];
}

interface PipelineMetricsDashboardProps {
  pipelineId: string;
  currentStage: string;
  stageMetrics: Record<string, StageMetrics>;
  isActive: boolean;
  refreshInterval?: number; // milliseconds
  onRefresh?: () => void;
}

export const PipelineMetricsDashboard = ({
  pipelineId,
  currentStage,
  stageMetrics,
  isActive,
  refreshInterval = 5000,
  onRefresh
}: PipelineMetricsDashboardProps) => {
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(isActive);

  // Auto-refresh metrics for active pipelines
  useEffect(() => {
    if (!autoRefresh || !onRefresh) return;

    const interval = setInterval(() => {
      onRefresh();
      setLastUpdate(new Date());
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, onRefresh]);

  const currentMetrics = stageMetrics[currentStage];

  const formatMetricValue = (value: any): string => {
    if (typeof value === 'number') {
      if (value < 0.01 && value > 0) {
        return value.toExponential(3);
      }
      return value.toFixed(4);
    }
    return String(value);
  };

  const getMetricTrend = (metricName: string, currentValue: number): 'up' | 'down' | 'stable' => {
    // For loss metrics, down is good
    if (metricName.toLowerCase().includes('loss')) {
      return currentValue < 0 ? 'down' : 'up';
    }
    // For accuracy/performance metrics, up is good
    if (metricName.toLowerCase().includes('accuracy') ||
        metricName.toLowerCase().includes('score')) {
      return currentValue > 0 ? 'up' : 'down';
    }
    return 'stable';
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-400" />;
    }
  };

  const renderMetricCard = (name: string, value: any, unit?: string) => {
    const trend = typeof value === 'number' ? getMetricTrend(name, value) : 'stable';
    const formattedValue = formatMetricValue(value);

    return (
      <Card key={name} className="hover:shadow-md transition-shadow">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-muted-foreground">
              {name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </span>
            {getTrendIcon(trend)}
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold">{formattedValue}</span>
            {unit && <span className="text-sm text-muted-foreground">{unit}</span>}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderResourceUsage = (usage: StageMetrics['resource_usage']) => {
    if (!usage) return null;

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            Resource Utilization
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* CPU Usage */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium flex items-center gap-2">
                <Cpu className="h-4 w-4" />
                CPU
              </span>
              <span className="text-sm font-bold">{usage.cpu_percent.toFixed(1)}%</span>
            </div>
            <Progress value={usage.cpu_percent} className="h-2" />
          </div>

          {/* Memory Usage */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium flex items-center gap-2">
                <HardDrive className="h-4 w-4" />
                Memory
              </span>
              <span className="text-sm font-bold">
                {(usage.memory_mb / 1024).toFixed(2)} GB
              </span>
            </div>
            <Progress
              value={Math.min((usage.memory_mb / 1024 / 16) * 100, 100)}
              className="h-2"
            />
          </div>

          {/* GPU Usage (if available) */}
          {usage.gpu_percent !== undefined && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  GPU
                </span>
                <span className="text-sm font-bold">{usage.gpu_percent.toFixed(1)}%</span>
              </div>
              <Progress value={usage.gpu_percent} className="h-2" />
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderTrainingMetrics = (metrics: Record<string, any>) => {
    const trainingMetrics = Object.entries(metrics).filter(([key]) =>
      key.includes('loss') ||
      key.includes('accuracy') ||
      key.includes('learning_rate') ||
      key.includes('epoch')
    );

    if (trainingMetrics.length === 0) return null;

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Training Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {trainingMetrics.map(([key, value]) =>
              renderMetricCard(key, value)
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderDataMetrics = (metrics: Record<string, any>) => {
    const dataMetrics = Object.entries(metrics).filter(([key]) =>
      key.includes('sample') ||
      key.includes('batch') ||
      key.includes('size') ||
      key.includes('count')
    );

    if (dataMetrics.length === 0) return null;

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Data Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {dataMetrics.map(([key, value]) =>
              renderMetricCard(key, value)
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  if (!currentMetrics) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <AlertCircle className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">
            No metrics available for stage: {currentStage}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Auto-Refresh Control */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Pipeline Metrics Dashboard</h2>
          <p className="text-sm text-muted-foreground">
            Current Stage: <Badge>{currentStage}</Badge>
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            Last updated: {lastUpdate.toLocaleTimeString()}
          </div>
          {isActive && (
            <Badge
              variant={autoRefresh ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              {autoRefresh ? '🔄 Auto-refresh ON' : '⏸ Auto-refresh OFF'}
            </Badge>
          )}
        </div>
      </div>

      {/* Resource Utilization */}
      {currentMetrics.resource_usage && renderResourceUsage(currentMetrics.resource_usage)}

      {/* Training Metrics */}
      {renderTrainingMetrics(currentMetrics.metrics)}

      {/* Data Metrics */}
      {renderDataMetrics(currentMetrics.metrics)}

      {/* All Other Metrics */}
      {Object.keys(currentMetrics.metrics).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              All Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(currentMetrics.metrics).map(([key, value]) =>
                renderMetricCard(key, value)
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pipeline Status */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Pipeline ID:</span>
              <span className="font-mono">{pipelineId}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Status:</span>
              <Badge variant={isActive ? "default" : "secondary"}>
                {isActive ? 'Running' : 'Idle'}
              </Badge>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Current Stage:</span>
              <span className="font-medium">{currentStage}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PipelineMetricsDashboard;
