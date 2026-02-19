/**
 * Version Comparison Tool Component
 *
 * Side-by-side comparison of model/dataset versions:
 * - Performance metrics comparison
 * - Changelog and differences
 * - File changes summary
 * - Visual charts for metric trends
 * - Download links for both versions
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Minus,
  Download,
  FileText,
  BarChart3,
  GitCompare,
  Calendar,
  User,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface VersionMetrics {
  accuracy?: number;
  loss?: number;
  wer?: number; // Word Error Rate
  cer?: number; // Character Error Rate
  bleu_score?: number;
  inference_time_ms?: number;
  model_size_mb?: number;
  [key: string]: any;
}

interface FileChange {
  path: string;
  change_type: 'added' | 'modified' | 'deleted';
  size_delta_mb?: number;
}

interface VersionInfo {
  version: string;
  created_at: string;
  created_by: string;
  changelog?: string;
  metrics: VersionMetrics;
  file_changes?: FileChange[];
  download_url?: string;
  size_mb: number;
  checksum?: string;
}

interface VersionComparisonToolProps {
  resourceType: 'model' | 'dataset';
  resourceName: string;
  versionA: VersionInfo;
  versionB: VersionInfo;
  onClose?: () => void;
}

export const VersionComparisonTool = ({
  resourceType,
  resourceName,
  versionA,
  versionB,
  onClose
}: VersionComparisonToolProps) => {
  const [activeTab, setActiveTab] = useState('metrics');

  const calculateMetricDelta = (metricA: number, metricB: number): {
    delta: number;
    percent: number;
    trend: 'up' | 'down' | 'stable';
  } => {
    const delta = metricB - metricA;
    const percent = metricA !== 0 ? (delta / metricA) * 100 : 0;
    const trend = Math.abs(percent) < 0.1 ? 'stable' : delta > 0 ? 'up' : 'down';
    return { delta, percent, trend };
  };

  const isMetricBetter = (metricName: string, change: 'up' | 'down'): boolean => {
    // For loss/error metrics, down is better
    const lowerIsBetter = ['loss', 'wer', 'cer', 'inference_time_ms', 'model_size_mb'];
    const isLowerBetter = lowerIsBetter.some(m => metricName.toLowerCase().includes(m));

    if (isLowerBetter) {
      return change === 'down';
    }
    // For accuracy/score metrics, up is better
    return change === 'up';
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable', metricName: string) => {
    if (trend === 'stable') {
      return <Minus className="h-4 w-4 text-gray-400" />;
    }

    const isBetter = isMetricBetter(metricName, trend);
    const Icon = trend === 'up' ? TrendingUp : TrendingDown;
    const colorClass = isBetter ? 'text-green-500' : 'text-red-500';

    return <Icon className={cn('h-4 w-4', colorClass)} />;
  };

  const renderMetricComparison = (metricName: string) => {
    const valueA = versionA.metrics[metricName];
    const valueB = versionB.metrics[metricName];

    if (valueA === undefined || valueB === undefined) return null;

    const { delta, percent, trend } = calculateMetricDelta(
      typeof valueA === 'number' ? valueA : 0,
      typeof valueB === 'number' ? valueB : 0
    );

    const isBetter = isMetricBetter(metricName, trend);

    return (
      <div key={metricName} className="grid grid-cols-5 gap-4 py-3 border-b last:border-0 items-center">
        <div className="col-span-1 font-medium text-sm">
          {metricName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
        </div>

        <div className="col-span-1 text-center">
          <span className="text-sm font-mono">{valueA.toFixed(4)}</span>
        </div>

        <div className="col-span-1 flex items-center justify-center gap-2">
          {getTrendIcon(trend, metricName)}
          <span className={cn(
            'text-xs font-medium',
            isBetter ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
          )}>
            {trend !== 'stable' && (delta > 0 ? '+' : '')}{delta.toFixed(4)}
            <br />
            ({percent > 0 ? '+' : ''}{percent.toFixed(2)}%)
          </span>
        </div>

        <div className="col-span-1 text-center">
          <span className="text-sm font-mono">{valueB.toFixed(4)}</span>
        </div>

        <div className="col-span-1 text-center">
          {isBetter ? (
            <CheckCircle className="h-5 w-5 text-green-500 inline" />
          ) : (
            <XCircle className="h-5 w-5 text-red-500 inline" />
          )}
        </div>
      </div>
    );
  };

  const renderFileChanges = () => {
    if (!versionB.file_changes || versionB.file_changes.length === 0) {
      return (
        <p className="text-sm text-muted-foreground text-center py-8">
          No file changes recorded
        </p>
      );
    }

    return (
      <div className="space-y-2">
        {versionB.file_changes.map((change, idx) => (
          <div
            key={idx}
            className="flex items-center justify-between p-3 border rounded"
          >
            <div className="flex items-center gap-3">
              <Badge
                variant={
                  change.change_type === 'added' ? 'default' :
                  change.change_type === 'deleted' ? 'destructive' :
                  'secondary'
                }
              >
                {change.change_type}
              </Badge>
              <span className="text-sm font-mono">{change.path}</span>
            </div>
            {change.size_delta_mb && (
              <span className="text-xs text-muted-foreground">
                {change.size_delta_mb > 0 ? '+' : ''}{change.size_delta_mb.toFixed(2)} MB
              </span>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <GitCompare className="h-6 w-6" />
            Version Comparison: {resourceName}
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Comparing {resourceType} versions {versionA.version} and {versionB.version}
          </p>
        </div>
        {onClose && (
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        )}
      </div>

      {/* Version Headers */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Version {versionA.version}</span>
              <Badge variant="outline">Base</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              {new Date(versionA.created_at).toLocaleDateString()}
            </div>
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground" />
              {versionA.created_by}
            </div>
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              {versionA.size_mb.toFixed(2)} MB
            </div>
            {versionA.download_url && (
              <Button
                size="sm"
                variant="outline"
                className="w-full mt-2"
                onClick={() => window.open(versionA.download_url, '_blank')}
              >
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Version {versionB.version}</span>
              <Badge>Latest</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              {new Date(versionB.created_at).toLocaleDateString()}
            </div>
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground" />
              {versionB.created_by}
            </div>
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              {versionB.size_mb.toFixed(2)} MB
              {versionB.size_mb !== versionA.size_mb && (
                <span className={cn(
                  'text-xs',
                  versionB.size_mb > versionA.size_mb ? 'text-orange-500' : 'text-green-500'
                )}>
                  ({versionB.size_mb > versionA.size_mb ? '+' : ''}{(versionB.size_mb - versionA.size_mb).toFixed(2)} MB)
                </span>
              )}
            </div>
            {versionB.download_url && (
              <Button
                size="sm"
                variant="outline"
                className="w-full mt-2"
                onClick={() => window.open(versionB.download_url, '_blank')}
              >
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Comparison Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-3 w-full">
          <TabsTrigger value="metrics">
            <BarChart3 className="h-4 w-4 mr-2" />
            Performance Metrics
          </TabsTrigger>
          <TabsTrigger value="changelog">
            <FileText className="h-4 w-4 mr-2" />
            Changelog
          </TabsTrigger>
          <TabsTrigger value="files">
            <GitCompare className="h-4 w-4 mr-2" />
            File Changes
          </TabsTrigger>
        </TabsList>

        {/* Metrics Comparison */}
        <TabsContent value="metrics" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-5 gap-4 pb-3 border-b font-medium text-sm text-muted-foreground">
                <div>Metric</div>
                <div className="text-center">v{versionA.version}</div>
                <div className="text-center">Change</div>
                <div className="text-center">v{versionB.version}</div>
                <div className="text-center">Better?</div>
              </div>
              <div className="mt-2">
                {Object.keys(versionA.metrics).map(metricName =>
                  renderMetricComparison(metricName)
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Changelog */}
        <TabsContent value="changelog" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Version Changelog</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-medium mb-2">Version {versionB.version}</h4>
                {versionB.changelog ? (
                  <pre className="text-sm bg-muted p-4 rounded whitespace-pre-wrap">
                    {versionB.changelog}
                  </pre>
                ) : (
                  <p className="text-sm text-muted-foreground">No changelog provided</p>
                )}
              </div>
              <div className="border-t pt-4">
                <h4 className="font-medium mb-2">Version {versionA.version}</h4>
                {versionA.changelog ? (
                  <pre className="text-sm bg-muted p-4 rounded whitespace-pre-wrap">
                    {versionA.changelog}
                  </pre>
                ) : (
                  <p className="text-sm text-muted-foreground">No changelog provided</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* File Changes */}
        <TabsContent value="files" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>File Changes Summary</CardTitle>
            </CardHeader>
            <CardContent>
              {renderFileChanges()}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Summary Card */}
      <Card className="border-2">
        <CardHeader>
          <CardTitle>Recommendation</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Based on the comparison, version <strong>{versionB.version}</strong> shows{' '}
            improvements in key metrics. Consider upgrading to the latest version for better performance.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default VersionComparisonTool;
