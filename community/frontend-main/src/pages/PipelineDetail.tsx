import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import {
  ArrowLeft,
  Play,
  Pause,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  Database,
  Cpu,
  HardDrive,
  Loader2,
  AlertCircle,
  FileText,
  Activity,
  Upload
} from 'lucide-react';
import { useNotification } from '@/contexts/NotificationContext';
import { ArtifactUploadModal } from '@/components/ArtifactUploadModal';
import { ArtifactsList } from '@/components/ArtifactsList';
import { PipelineVisualization } from '@/components/PipelineVisualization';
import { useAuth } from '@/contexts/AuthContext';

const API_BASE = 'https://language-community-api.ailabsafrica.com/api/v1';

interface StageInfo {
  stage_name: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  duration_minutes?: number;
  metrics?: Record<string, any>;
  artifacts?: Array<{
    name: string;
    path: string;
    size_mb?: number;
    artifact_type: string;
  }>;
  notes?: string;
  error_message?: string;
}

interface Pipeline {
  pipeline_uuid: string;
  name: string;
  model_type: string;
  current_stage: string;
  is_active: boolean;
  progress_percentage: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  stages: Record<string, StageInfo>;
  datasets?: Array<{
    dataset_id: string;
    version: string;
    role: string;
  }>;
  priority?: string;
  tags?: string[];
}

const PipelineDetail = () => {
  const { pipelineId } = useParams<{ pipelineId: string }>();
  const navigate = useNavigate();
  const { showSuccess, showError } = useNotification();
  const { user } = useAuth();

  const [pipeline, setPipeline] = useState<Pipeline | null>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [artifactsRefreshKey, setArtifactsRefreshKey] = useState(0);

  useEffect(() => {
    if (pipelineId) {
      loadPipelineData();
    }
  }, [pipelineId]);

  const loadPipelineData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/pipelines/${pipelineId}`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Pipeline not found');
        }
        throw new Error('Failed to load pipeline');
      }

      const data = await response.json();
      setPipeline(data);

      // Load metrics
      loadMetrics();
    } catch (error: any) {
      console.error('Failed to load pipeline:', error);
      showError(error.message || 'Failed to load pipeline data');
    } finally {
      setLoading(false);
    }
  };

  const loadMetrics = async () => {
    try {
      setMetricsLoading(true);
      const response = await fetch(`${API_BASE}/pipelines/${pipelineId}/metrics`);

      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      }
    } catch (error) {
      console.error('Failed to load metrics:', error);
    } finally {
      setMetricsLoading(false);
    }
  };

  const getStageIcon = (stageName: string) => {
    switch (stageName.toLowerCase()) {
      case 'data_acquisition': return <Database className="h-5 w-5" />;
      case 'preprocessing': return <Activity className="h-5 w-5" />;
      case 'training': return <Cpu className="h-5 w-5" />;
      case 'evaluation': return <TrendingUp className="h-5 w-5" />;
      case 'deployment': return <Play className="h-5 w-5" />;
      default: return <FileText className="h-5 w-5" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'in_progress': return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'failed': return <XCircle className="h-5 w-5 text-red-500" />;
      case 'pending': return <Clock className="h-5 w-5 text-gray-400" />;
      default: return <AlertCircle className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-gray-100 text-gray-800';
      default: return 'bg-yellow-100 text-yellow-800';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDuration = (minutes?: number) => {
    if (!minutes) return 'N/A';
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (!pipeline) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-4">Pipeline Not Found</h2>
            <p className="text-muted-foreground mb-6">
              The pipeline you're looking for doesn't exist or has been removed.
            </p>
            <Button onClick={() => navigate('/mlops')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to MLOps
            </Button>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const stages = Object.entries(pipeline.stages || {});

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-start gap-4 mb-8">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/mlops')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold">{pipeline.name}</h1>
              <Badge className={pipeline.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}>
                {pipeline.is_active ? 'Active' : 'Inactive'}
              </Badge>
              {pipeline.priority && (
                <Badge className={getPriorityColor(pipeline.priority)}>
                  {pipeline.priority}
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <Cpu className="h-4 w-4" />
                {pipeline.model_type.toUpperCase()}
              </span>
              <span className="flex items-center gap-1">
                Current Stage: {pipeline.current_stage.replace('_', ' ')}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {formatDate(pipeline.created_at)}
              </span>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Overall Progress</CardTitle>
            <CardDescription>Pipeline completion status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span className="font-medium">{pipeline.progress_percentage}%</span>
              </div>
              <Progress value={pipeline.progress_percentage} className="h-3" />
            </div>
          </CardContent>
        </Card>

        {/* Main Content */}
        <Tabs defaultValue="visualization" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="visualization">Visualization</TabsTrigger>
            <TabsTrigger value="stages">Stages</TabsTrigger>
            <TabsTrigger value="metrics">Metrics</TabsTrigger>
            <TabsTrigger value="datasets">Datasets</TabsTrigger>
            <TabsTrigger value="artifacts">Artifacts</TabsTrigger>
          </TabsList>

          <TabsContent value="visualization" className="space-y-6">
            <PipelineVisualization
              stages={pipeline.stages}
              currentStage={pipeline.current_stage}
              isActive={pipeline.is_active}
              progressPercentage={pipeline.progress_percentage}
            />
          </TabsContent>

          <TabsContent value="stages" className="space-y-6">
            {stages.length > 0 ? (
              <div className="space-y-4">
                {stages.map(([stageName, stageInfo]) => (
                  <Card key={stageName}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {getStageIcon(stageName)}
                          <div>
                            <CardTitle className="text-lg capitalize">
                              {stageName.replace('_', ' ')}
                            </CardTitle>
                            {stageInfo.started_at && (
                              <CardDescription>
                                Started: {formatDate(stageInfo.started_at)}
                              </CardDescription>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(stageInfo.status)}
                          <Badge className={getStatusColor(stageInfo.status)}>
                            {stageInfo.status}
                          </Badge>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Stage Details */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <div className="text-muted-foreground mb-1">Duration</div>
                          <div className="font-medium">{formatDuration(stageInfo.duration_minutes)}</div>
                        </div>
                        {stageInfo.completed_at && (
                          <div>
                            <div className="text-muted-foreground mb-1">Completed</div>
                            <div className="font-medium">{formatDate(stageInfo.completed_at)}</div>
                          </div>
                        )}
                        {stageInfo.artifacts && stageInfo.artifacts.length > 0 && (
                          <div>
                            <div className="text-muted-foreground mb-1">Artifacts</div>
                            <div className="font-medium">{stageInfo.artifacts.length}</div>
                          </div>
                        )}
                      </div>

                      {/* Artifacts */}
                      {stageInfo.artifacts && stageInfo.artifacts.length > 0 && (
                        <div>
                          <div className="font-medium mb-2">Artifacts</div>
                          <div className="space-y-2">
                            {stageInfo.artifacts.map((artifact, idx) => (
                              <div key={idx} className="flex items-center justify-between p-2 border rounded">
                                <div className="flex items-center gap-2">
                                  <HardDrive className="h-4 w-4 text-muted-foreground" />
                                  <div>
                                    <div className="text-sm font-medium">{artifact.name}</div>
                                    <div className="text-xs text-muted-foreground">
                                      {artifact.artifact_type}
                                      {artifact.size_mb && ` • ${artifact.size_mb.toFixed(1)} MB`}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Metrics */}
                      {stageInfo.metrics && Object.keys(stageInfo.metrics).length > 0 && (
                        <div>
                          <div className="font-medium mb-2">Stage Metrics</div>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                            {Object.entries(stageInfo.metrics).map(([key, value]) => (
                              <div key={key} className="p-2 border rounded">
                                <div className="text-xs text-muted-foreground mb-1">{key}</div>
                                <div className="font-medium">{String(value)}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Notes */}
                      {stageInfo.notes && (
                        <div>
                          <div className="font-medium mb-2">Notes</div>
                          <div className="p-3 bg-muted rounded text-sm">{stageInfo.notes}</div>
                        </div>
                      )}

                      {/* Error Message */}
                      {stageInfo.error_message && (
                        <div className="p-3 bg-red-50 border border-red-200 rounded">
                          <div className="flex items-center gap-2 text-red-800 font-medium mb-1">
                            <AlertCircle className="h-4 w-4" />
                            Error
                          </div>
                          <div className="text-sm text-red-700">{stageInfo.error_message}</div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="text-center py-12">
                  <FileText className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                  <p className="text-muted-foreground">No stage information available</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="metrics" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Pipeline Metrics</CardTitle>
                <CardDescription>Performance and training metrics across all stages</CardDescription>
              </CardHeader>
              <CardContent>
                {metricsLoading ? (
                  <div className="text-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
                  </div>
                ) : metrics && Object.keys(metrics).length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(metrics).map(([key, value]) => (
                      <div key={key} className="p-4 border rounded-lg">
                        <div className="text-sm text-muted-foreground mb-1">{key}</div>
                        <div className="text-2xl font-bold">{String(value)}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <TrendingUp className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No metrics available yet</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="datasets" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Training Datasets</CardTitle>
                <CardDescription>Datasets used in this pipeline</CardDescription>
              </CardHeader>
              <CardContent>
                {pipeline.datasets && pipeline.datasets.length > 0 ? (
                  <div className="space-y-3">
                    {pipeline.datasets.map((dataset, idx) => (
                      <div key={idx} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex items-center gap-3">
                          <Database className="h-5 w-5 text-muted-foreground" />
                          <div>
                            <div className="font-medium">Dataset {dataset.dataset_id}</div>
                            <div className="text-sm text-muted-foreground">
                              Version: {dataset.version} • Role: {dataset.role}
                            </div>
                          </div>
                        </div>
                        <Badge variant="outline">{dataset.role}</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <Database className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No datasets configured</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="artifacts" className="space-y-6">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h2 className="text-2xl font-bold">Pipeline Artifacts</h2>
                <p className="text-sm text-muted-foreground mt-1">
                  Upload and manage model files, logs, metrics, and visualizations
                </p>
              </div>
              <Button onClick={() => setUploadModalOpen(true)}>
                <Upload className="h-4 w-4 mr-2" />
                Upload Artifact
              </Button>
            </div>

            <ArtifactsList
              key={artifactsRefreshKey}
              pipelineId={pipelineId!}
              currentUserId={user?.id}
              onRefresh={() => setArtifactsRefreshKey((prev) => prev + 1)}
            />
          </TabsContent>
        </Tabs>

        {/* Upload Modal */}
        <ArtifactUploadModal
          open={uploadModalOpen}
          onOpenChange={setUploadModalOpen}
          pipelineId={pipelineId!}
          onSuccess={() => {
            setArtifactsRefreshKey((prev) => prev + 1);
            showSuccess('Artifacts uploaded successfully!');
          }}
        />
      </main>
      <Footer />
    </div>
  );
};

export default PipelineDetail;
