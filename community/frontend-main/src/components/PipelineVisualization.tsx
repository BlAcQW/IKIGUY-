import { useMemo } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  CheckCircle,
  XCircle,
  Clock,
  Circle,
  ArrowRight,
  Database,
  Activity,
  Cpu,
  TestTube,
  Upload,
  Play
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface StageInfo {
  stage_name: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  duration_minutes?: number;
  metrics?: Record<string, any>;
  notes?: string;
  error_message?: string;
}

interface PipelineVisualizationProps {
  stages: Record<string, StageInfo>;
  currentStage: string;
  isActive: boolean;
  progressPercentage: number;
}

const STAGE_ORDER = [
  'data_acquisition',
  'preprocessing',
  'training',
  'evaluation',
  'deployment'
];

const getStageIcon = (stageName: string) => {
  switch (stageName.toLowerCase()) {
    case 'data_acquisition':
      return <Database className="h-5 w-5" />;
    case 'preprocessing':
      return <Activity className="h-5 w-5" />;
    case 'training':
      return <Cpu className="h-5 w-5" />;
    case 'evaluation':
      return <TestTube className="h-5 w-5" />;
    case 'deployment':
      return <Upload className="h-5 w-5" />;
    default:
      return <Play className="h-5 w-5" />;
  }
};

const getStatusIcon = (status: string) => {
  switch (status.toLowerCase()) {
    case 'completed':
      return <CheckCircle className="h-6 w-6 text-green-500" />;
    case 'failed':
      return <XCircle className="h-6 w-6 text-red-500" />;
    case 'in_progress':
      return <Clock className="h-6 w-6 text-blue-500 animate-pulse" />;
    case 'pending':
      return <Circle className="h-6 w-6 text-gray-400" />;
    default:
      return <Circle className="h-6 w-6 text-gray-300" />;
  }
};

const getStatusColor = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'bg-green-500';
    case 'failed':
      return 'bg-red-500';
    case 'in_progress':
      return 'bg-blue-500';
    case 'pending':
      return 'bg-gray-400';
    default:
      return 'bg-gray-300';
  }
};

const getStatusBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
  switch (status.toLowerCase()) {
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

export function PipelineVisualization({
  stages,
  currentStage,
  isActive,
  progressPercentage
}: PipelineVisualizationProps) {
  const orderedStages = useMemo(() => {
    const stageEntries = Object.entries(stages);

    // Sort by predefined order if stages match, otherwise by entry order
    return stageEntries.sort((a, b) => {
      const indexA = STAGE_ORDER.indexOf(a[0].toLowerCase());
      const indexB = STAGE_ORDER.indexOf(b[0].toLowerCase());

      if (indexA !== -1 && indexB !== -1) {
        return indexA - indexB;
      }
      if (indexA !== -1) return -1;
      if (indexB !== -1) return 1;
      return 0;
    });
  }, [stages]);

  const currentStageIndex = orderedStages.findIndex(
    ([name]) => name.toLowerCase() === currentStage.toLowerCase()
  );

  return (
    <div className="space-y-8">
      {/* Progress Overview */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">Pipeline Progress</span>
              <span className="text-muted-foreground">{progressPercentage}% Complete</span>
            </div>
            <div className="relative h-3 w-full overflow-hidden rounded-full bg-gray-200">
              <div
                className={cn(
                  "h-full transition-all duration-500 ease-out",
                  isActive ? "bg-blue-500" : "bg-green-500"
                )}
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{orderedStages.filter(([, info]) => info.status === 'completed').length} of {orderedStages.length} stages completed</span>
              {isActive && <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                In Progress
              </span>}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Visual Pipeline Flow */}
      <div className="relative">
        {/* Timeline Line */}
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-200" />

        {/* Stages */}
        <div className="space-y-6">
          {orderedStages.map(([stageName, stageInfo], index) => {
            const isCurrentStage = stageName.toLowerCase() === currentStage.toLowerCase();
            const isPastStage = index < currentStageIndex || stageInfo.status === 'completed';
            const isFutureStage = index > currentStageIndex && stageInfo.status === 'pending';

            return (
              <div key={stageName} className="relative">
                {/* Stage Node */}
                <div className="relative flex items-start gap-4">
                  {/* Icon Container */}
                  <div className="relative z-10 flex-shrink-0">
                    <div
                      className={cn(
                        "flex h-16 w-16 items-center justify-center rounded-full border-4 border-background shadow-sm transition-all",
                        isPastStage && "bg-green-500 text-white",
                        isCurrentStage && "bg-blue-500 text-white ring-4 ring-blue-100",
                        isFutureStage && "bg-gray-100 text-gray-400",
                        stageInfo.status === 'failed' && "bg-red-500 text-white"
                      )}
                    >
                      {getStageIcon(stageName)}
                    </div>

                    {/* Status Badge on Icon */}
                    <div className="absolute -bottom-1 -right-1">
                      {getStatusIcon(stageInfo.status)}
                    </div>
                  </div>

                  {/* Stage Content */}
                  <div className="flex-1 pb-8">
                    <Card
                      className={cn(
                        "transition-all",
                        isCurrentStage && "ring-2 ring-blue-500 shadow-lg",
                        isPastStage && "opacity-90"
                      )}
                    >
                      <CardContent className="p-4">
                        <div className="space-y-3">
                          {/* Stage Header */}
                          <div className="flex items-start justify-between">
                            <div>
                              <h3 className="font-semibold text-lg capitalize">
                                {stageName.replace(/_/g, ' ')}
                              </h3>
                              <p className="text-sm text-muted-foreground mt-0.5">
                                Step {index + 1} of {orderedStages.length}
                              </p>
                            </div>
                            <Badge variant={getStatusBadgeVariant(stageInfo.status)} className="capitalize">
                              {stageInfo.status.replace('_', ' ')}
                            </Badge>
                          </div>

                          {/* Stage Info */}
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                            {stageInfo.duration_minutes !== undefined && (
                              <div className="flex items-center gap-2">
                                <Clock className="h-4 w-4 text-muted-foreground" />
                                <span>
                                  {stageInfo.duration_minutes.toFixed(1)} min
                                </span>
                              </div>
                            )}
                            {stageInfo.started_at && (
                              <div className="text-muted-foreground">
                                Started: {new Date(stageInfo.started_at).toLocaleString()}
                              </div>
                            )}
                            {stageInfo.completed_at && (
                              <div className="text-muted-foreground">
                                Completed: {new Date(stageInfo.completed_at).toLocaleString()}
                              </div>
                            )}
                          </div>

                          {/* Key Metrics */}
                          {stageInfo.metrics && Object.keys(stageInfo.metrics).length > 0 && (
                            <div className="border-t pt-3">
                              <p className="text-xs font-medium text-muted-foreground mb-2">KEY METRICS</p>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                {Object.entries(stageInfo.metrics)
                                  .slice(0, 4)
                                  .map(([key, value]) => (
                                    <div key={key} className="bg-muted/50 rounded px-2 py-1.5">
                                      <p className="text-xs text-muted-foreground truncate">{key}</p>
                                      <p className="text-sm font-medium">
                                        {typeof value === 'number' ? value.toFixed(3) : String(value)}
                                      </p>
                                    </div>
                                  ))}
                              </div>
                            </div>
                          )}

                          {/* Error Message */}
                          {stageInfo.error_message && (
                            <div className="border-t border-red-200 pt-3 bg-red-50 -mx-4 -mb-4 px-4 py-3 rounded-b-lg">
                              <p className="text-xs font-medium text-red-900 mb-1">ERROR</p>
                              <p className="text-sm text-red-700">{stageInfo.error_message}</p>
                            </div>
                          )}

                          {/* Notes */}
                          {stageInfo.notes && !stageInfo.error_message && (
                            <div className="border-t pt-3 text-sm text-muted-foreground">
                              {stageInfo.notes}
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>

                {/* Arrow Connector */}
                {index < orderedStages.length - 1 && (
                  <div className="absolute left-8 -bottom-3 z-10 flex items-center justify-center">
                    <div className={cn(
                      "rounded-full p-1",
                      isPastStage ? "bg-green-500" : "bg-gray-200"
                    )}>
                      <ArrowRight className={cn(
                        "h-4 w-4",
                        isPastStage ? "text-white" : "text-gray-400"
                      )} />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Completed</p>
                <p className="text-2xl font-bold text-green-600">
                  {orderedStages.filter(([, info]) => info.status === 'completed').length}
                </p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">In Progress</p>
                <p className="text-2xl font-bold text-blue-600">
                  {orderedStages.filter(([, info]) => info.status === 'in_progress').length}
                </p>
              </div>
              <Clock className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pending</p>
                <p className="text-2xl font-bold text-gray-600">
                  {orderedStages.filter(([, info]) => info.status === 'pending').length}
                </p>
              </div>
              <Circle className="h-8 w-8 text-gray-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Failed</p>
                <p className="text-2xl font-bold text-red-600">
                  {orderedStages.filter(([, info]) => info.status === 'failed').length}
                </p>
              </div>
              <XCircle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
