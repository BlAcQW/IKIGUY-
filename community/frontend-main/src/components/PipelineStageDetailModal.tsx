/**
 * Pipeline Stage Detail Modal Component
 *
 * Displays detailed information about a specific pipeline stage:
 * - Stage status and timeline
 * - Metrics and performance data
 * - Logs and error messages
 * - Artifacts produced
 * - Configuration parameters
 */

import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  FileText,
  Download,
  Terminal,
  Settings,
  BarChart3,
  Play
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface StageArtifact {
  name: string;
  type: string;
  size_mb: number;
  created_at: string;
  download_url?: string;
}

interface StageLog {
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
  message: string;
}

interface StageDetail {
  stage_name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
  duration_minutes?: number;
  metrics?: Record<string, any>;
  config?: Record<string, any>;
  artifacts?: StageArtifact[];
  logs?: StageLog[];
  error_message?: string;
  notes?: string;
}

interface PipelineStageDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  stageDetail: StageDetail | null;
  pipelineId: string;
}

export const PipelineStageDetailModal = ({
  isOpen,
  onClose,
  stageDetail,
  pipelineId
}: PipelineStageDetailModalProps) => {
  const [activeTab, setActiveTab] = useState('overview');

  if (!stageDetail) return null;

  const getStatusIcon = () => {
    switch (stageDetail.status) {
      case 'completed':
        return <CheckCircle className="h-6 w-6 text-green-500" />;
      case 'failed':
        return <XCircle className="h-6 w-6 text-red-500" />;
      case 'in_progress':
        return <Play className="h-6 w-6 text-blue-500 animate-pulse" />;
      default:
        return <Clock className="h-6 w-6 text-gray-400" />;
    }
  };

  const getStatusBadgeVariant = (): "default" | "secondary" | "destructive" | "outline" => {
    switch (stageDetail.status) {
      case 'completed':
        return 'default';
      case 'failed':
        return 'destructive';
      case 'in_progress':
        return 'default';
      default:
        return 'secondary';
    }
  };

  const formatDuration = (minutes?: number): string => {
    if (!minutes) return 'N/A';
    if (minutes < 1) return `${Math.round(minutes * 60)}s`;
    if (minutes < 60) return `${Math.round(minutes)}m`;
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  const formatTimestamp = (timestamp?: string): string => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString();
  };

  const getLogLevelColor = (level: StageLog['level']): string => {
    switch (level) {
      case 'ERROR':
        return 'text-red-600 dark:text-red-400';
      case 'WARNING':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'INFO':
        return 'text-blue-600 dark:text-blue-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const handleDownloadArtifact = async (artifact: StageArtifact) => {
    if (!artifact.download_url) {
      console.error('No download URL available for artifact');
      return;
    }
    window.open(artifact.download_url, '_blank');
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            {getStatusIcon()}
            <div>
              <DialogTitle className="text-2xl">
                {stageDetail.stage_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </DialogTitle>
              <DialogDescription>
                Pipeline ID: <span className="font-mono text-xs">{pipelineId}</span>
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="mt-4">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid grid-cols-5 w-full">
              <TabsTrigger value="overview">
                <FileText className="h-4 w-4 mr-2" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="metrics">
                <BarChart3 className="h-4 w-4 mr-2" />
                Metrics
              </TabsTrigger>
              <TabsTrigger value="config">
                <Settings className="h-4 w-4 mr-2" />
                Config
              </TabsTrigger>
              <TabsTrigger value="artifacts">
                <Download className="h-4 w-4 mr-2" />
                Artifacts
              </TabsTrigger>
              <TabsTrigger value="logs">
                <Terminal className="h-4 w-4 mr-2" />
                Logs
              </TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-4 mt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Status & Timeline</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Status:</span>
                    <Badge variant={getStatusBadgeVariant()}>
                      {stageDetail.status.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Started:</span>
                    <span className="text-sm font-medium">{formatTimestamp(stageDetail.started_at)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Completed:</span>
                    <span className="text-sm font-medium">{formatTimestamp(stageDetail.completed_at)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Duration:</span>
                    <span className="text-sm font-medium">{formatDuration(stageDetail.duration_minutes)}</span>
                  </div>
                </CardContent>
              </Card>

              {stageDetail.error_message && (
                <Card className="border-red-200 dark:border-red-900">
                  <CardHeader>
                    <CardTitle className="text-red-600 dark:text-red-400 flex items-center gap-2">
                      <AlertCircle className="h-5 w-5" />
                      Error
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="text-sm bg-red-50 dark:bg-red-950 p-4 rounded overflow-x-auto">
                      {stageDetail.error_message}
                    </pre>
                  </CardContent>
                </Card>
              )}

              {stageDetail.notes && (
                <Card>
                  <CardHeader>
                    <CardTitle>Notes</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{stageDetail.notes}</p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Metrics Tab */}
            <TabsContent value="metrics" className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Stage Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  {stageDetail.metrics && Object.keys(stageDetail.metrics).length > 0 ? (
                    <div className="space-y-2">
                      {Object.entries(stageDetail.metrics).map(([key, value]) => (
                        <div key={key} className="flex justify-between items-center py-2 border-b last:border-0">
                          <span className="text-sm font-medium">
                            {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </span>
                          <span className="text-sm font-mono bg-muted px-2 py-1 rounded">
                            {typeof value === 'number' ? value.toFixed(4) : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground text-center py-8">
                      No metrics recorded for this stage
                    </p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Config Tab */}
            <TabsContent value="config" className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Configuration Parameters</CardTitle>
                </CardHeader>
                <CardContent>
                  {stageDetail.config && Object.keys(stageDetail.config).length > 0 ? (
                    <pre className="text-xs bg-muted p-4 rounded overflow-x-auto">
                      {JSON.stringify(stageDetail.config, null, 2)}
                    </pre>
                  ) : (
                    <p className="text-sm text-muted-foreground text-center py-8">
                      No configuration data available
                    </p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Artifacts Tab */}
            <TabsContent value="artifacts" className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Stage Artifacts</CardTitle>
                </CardHeader>
                <CardContent>
                  {stageDetail.artifacts && stageDetail.artifacts.length > 0 ? (
                    <div className="space-y-2">
                      {stageDetail.artifacts.map((artifact, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-3 border rounded hover:bg-muted/50 transition-colors"
                        >
                          <div>
                            <p className="font-medium text-sm">{artifact.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {artifact.type} • {artifact.size_mb.toFixed(2)} MB •
                              {' '}{new Date(artifact.created_at).toLocaleString()}
                            </p>
                          </div>
                          {artifact.download_url && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDownloadArtifact(artifact)}
                            >
                              <Download className="h-4 w-4 mr-2" />
                              Download
                            </Button>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground text-center py-8">
                      No artifacts generated yet
                    </p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Logs Tab */}
            <TabsContent value="logs" className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Execution Logs</CardTitle>
                </CardHeader>
                <CardContent>
                  {stageDetail.logs && stageDetail.logs.length > 0 ? (
                    <div className="bg-black text-white p-4 rounded font-mono text-xs max-h-96 overflow-y-auto">
                      {stageDetail.logs.map((log, idx) => (
                        <div key={idx} className="py-1">
                          <span className="text-gray-500">[{log.timestamp}]</span>
                          {' '}
                          <span className={getLogLevelColor(log.level)}>[{log.level}]</span>
                          {' '}
                          <span>{log.message}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground text-center py-8">
                      No logs available
                    </p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        <div className="mt-6 flex justify-end">
          <Button onClick={onClose}>Close</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default PipelineStageDetailModal;
