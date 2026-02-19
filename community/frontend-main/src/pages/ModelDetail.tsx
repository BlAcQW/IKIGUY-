import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Download,
  ArrowLeft,
  Star,
  GitBranch,
  Clock,
  Database,
  Cpu,
  Globe,
  ExternalLink,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  Package,
  Loader2,
  Play,
  FileText,
  Users
} from 'lucide-react';
import { useBackendAuth } from '@/contexts/BackendAuthContext';
import { useNotification } from '@/contexts/NotificationContext';
import { ModelVersionsModal } from '@/components/ModelVersionsModal';

const API_BASE = 'https://language-community-api.ailabsafrica.com/api/v1';

interface ModelVersion {
  version: string;
  released_at: string;
  changelog: string;
  storage_path: string;
  performance_metrics?: Record<string, number>;
  model_size_mb?: number;
  is_stable: boolean;
  is_deprecated: boolean;
}

interface KnownIssue {
  issue: string;
  severity: string;
  reported_by: string;
  reported_at: string;
  workaround?: string;
  is_resolved: boolean;
}

interface MLModel {
  model_uuid: string;
  name: string;
  description?: string;
  model_type: string;
  architecture: string;
  version: string;
  languages: string[];
  primary_language: string;
  is_multilingual: boolean;
  deployment_status: string;
  deployment_url?: string;
  storage_path: string;
  performance_metrics?: Record<string, number>;
  training_datasets?: any[];
  version_history?: ModelVersion[];
  known_issues?: KnownIssue[];
  download_count: number;
  created_at: string;
  updated_at: string;
  created_by: string;
  license: string;
  is_public: boolean;
  tags?: string[];
}

const ModelDetail = () => {
  const { modelId } = useParams<{ modelId: string }>();
  const navigate = useNavigate();
  const { user } = useBackendAuth();
  const { showSuccess, showError } = useNotification();

  const [model, setModel] = useState<MLModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [reportingIssue, setReportingIssue] = useState(false);
  const [versionsModalOpen, setVersionsModalOpen] = useState(false);

  // Issue reporting state
  const [issueText, setIssueText] = useState('');
  const [issueSeverity, setIssueSeverity] = useState('medium');
  const [issueWorkaround, setIssueWorkaround] = useState('');

  useEffect(() => {
    if (modelId) {
      loadModelData();
    }
  }, [modelId]);

  const loadModelData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/models/${modelId}`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Model not found');
        }
        throw new Error('Failed to load model');
      }

      const data = await response.json();
      setModel(data);
    } catch (error: any) {
      console.error('Failed to load model:', error);
      showError(error.message || 'Failed to load model data');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!model || !user) {
      showError('Please sign in to download models');
      return;
    }

    try {
      setDownloading(true);
      const token = localStorage.getItem('auth_access_token');

      const response = await fetch(`${API_BASE}/models/${model.model_uuid}/download`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const data = await response.json();

      // Open download URL in new tab or trigger download
      if (data.download_url) {
        window.open(data.download_url, '_blank');
        showSuccess('Download started successfully');

        // Refresh model data to update download count
        await loadModelData();
      }
    } catch (error: any) {
      console.error('Download failed:', error);
      showError(error.message || 'Failed to download model');
    } finally {
      setDownloading(false);
    }
  };

  const handleReportIssue = async () => {
    if (!user) {
      showError('Please sign in to report issues');
      return;
    }

    if (!issueText.trim()) {
      showError('Please describe the issue');
      return;
    }

    try {
      setReportingIssue(true);
      const token = localStorage.getItem('auth_access_token');

      const response = await fetch(`${API_BASE}/models/${model?.model_uuid}/issues`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          issue: issueText,
          severity: issueSeverity,
          workaround: issueWorkaround || undefined
        })
      });

      if (!response.ok) {
        throw new Error('Failed to report issue');
      }

      showSuccess('Issue reported successfully');
      setIssueText('');
      setIssueWorkaround('');
      setIssueSeverity('medium');

      // Reload model data to show new issue
      await loadModelData();
    } catch (error: any) {
      console.error('Failed to report issue:', error);
      showError(error.message || 'Failed to report issue');
    } finally {
      setReportingIssue(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'production': return 'bg-green-100 text-green-800';
      case 'staging': return 'bg-blue-100 text-blue-800';
      case 'experimental': return 'bg-yellow-100 text-yellow-800';
      case 'deprecated': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
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
      day: 'numeric'
    });
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

  if (!model) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold mb-4">Model Not Found</h2>
            <p className="text-muted-foreground mb-6">
              The model you're looking for doesn't exist or has been removed.
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
              <h1 className="text-3xl font-bold">{model.name}</h1>
              <Badge className={getStatusColor(model.deployment_status)}>
                {model.deployment_status}
              </Badge>
            </div>
            <p className="text-muted-foreground">{model.description || 'No description provided'}</p>
            <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <Package className="h-4 w-4" />
                {model.architecture}
              </span>
              <span className="flex items-center gap-1">
                <GitBranch className="h-4 w-4" />
                v{model.version}
              </span>
              <span className="flex items-center gap-1">
                <Download className="h-4 w-4" />
                {model.download_count} downloads
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {formatDate(model.created_at)}
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            {model.deployment_url && (
              <Button variant="outline" asChild>
                <a href={model.deployment_url} target="_blank" rel="noopener noreferrer">
                  <Play className="h-4 w-4 mr-2" />
                  Try Live
                </a>
              </Button>
            )}
            <Button variant="outline" onClick={() => setVersionsModalOpen(true)}>
              <GitBranch className="h-4 w-4 mr-2" />
              Manage Versions
            </Button>
            <Button onClick={handleDownload} disabled={downloading}>
              {downloading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              Download Model
            </Button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Globe className="h-5 w-5 text-blue-500" />
                <div>
                  <p className="text-2xl font-bold">{model.languages.length}</p>
                  <p className="text-sm text-muted-foreground">Languages</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Cpu className="h-5 w-5 text-purple-500" />
                <div>
                  <p className="text-2xl font-bold">{model.model_type.toUpperCase()}</p>
                  <p className="text-sm text-muted-foreground">Model Type</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-green-500" />
                <div>
                  <p className="text-2xl font-bold">{model.training_datasets?.length || 0}</p>
                  <p className="text-sm text-muted-foreground">Datasets</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Star className="h-5 w-5 text-yellow-500" />
                <div>
                  <p className="text-2xl font-bold">{model.is_public ? 'Public' : 'Private'}</p>
                  <p className="text-sm text-muted-foreground">Access Level</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="versions">Versions</TabsTrigger>
            <TabsTrigger value="issues">Issues</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                {/* Details Card */}
                <Card>
                  <CardHeader>
                    <CardTitle>Model Details</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-sm font-medium mb-1">Model Type</div>
                        <div className="text-sm text-muted-foreground">{model.model_type.toUpperCase()}</div>
                      </div>
                      <div>
                        <div className="text-sm font-medium mb-1">Architecture</div>
                        <div className="text-sm text-muted-foreground">{model.architecture}</div>
                      </div>
                      <div>
                        <div className="text-sm font-medium mb-1">Version</div>
                        <div className="text-sm text-muted-foreground">v{model.version}</div>
                      </div>
                      <div>
                        <div className="text-sm font-medium mb-1">License</div>
                        <div className="text-sm text-muted-foreground">{model.license}</div>
                      </div>
                      <div>
                        <div className="text-sm font-medium mb-1">Primary Language</div>
                        <div className="text-sm text-muted-foreground">{model.primary_language}</div>
                      </div>
                      <div>
                        <div className="text-sm font-medium mb-1">Multilingual</div>
                        <div className="text-sm text-muted-foreground">{model.is_multilingual ? 'Yes' : 'No'}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Languages Card */}
                <Card>
                  <CardHeader>
                    <CardTitle>Supported Languages</CardTitle>
                    <CardDescription>Languages this model can process</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {model.languages.map((lang) => (
                        <Badge key={lang} variant="outline">
                          {lang}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Training Datasets */}
                {model.training_datasets && model.training_datasets.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Training Datasets</CardTitle>
                      <CardDescription>Datasets used to train this model</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {model.training_datasets.map((dataset, idx) => (
                          <div key={idx} className="flex items-center justify-between p-3 border rounded-lg">
                            <div>
                              <div className="font-medium">{dataset.version}</div>
                              <div className="text-sm text-muted-foreground">
                                Split: {dataset.split}
                                {dataset.hours && ` • ${dataset.hours}h`}
                                {dataset.samples && ` • ${dataset.samples.toLocaleString()} samples`}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>

              {/* Sidebar */}
              <div className="space-y-6">
                {/* Metadata Card */}
                <Card>
                  <CardHeader>
                    <CardTitle>Metadata</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    <div>
                      <div className="font-medium mb-1">Created</div>
                      <div className="text-muted-foreground">{formatDate(model.created_at)}</div>
                    </div>
                    <div>
                      <div className="font-medium mb-1">Last Updated</div>
                      <div className="text-muted-foreground">{formatDate(model.updated_at)}</div>
                    </div>
                    <div>
                      <div className="font-medium mb-1">Downloads</div>
                      <div className="text-muted-foreground">{model.download_count}</div>
                    </div>
                    {model.tags && model.tags.length > 0 && (
                      <div>
                        <div className="font-medium mb-2">Tags</div>
                        <div className="flex flex-wrap gap-1">
                          {model.tags.map((tag) => (
                            <Badge key={tag} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Links Card */}
                <Card>
                  <CardHeader>
                    <CardTitle>Links</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {model.deployment_url && (
                      <a
                        href={model.deployment_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-sm hover:underline"
                      >
                        <ExternalLink className="h-4 w-4" />
                        Live Demo
                      </a>
                    )}
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <FileText className="h-4 w-4" />
                      Model Card (Coming Soon)
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="performance" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
                <CardDescription>Model performance on benchmark datasets</CardDescription>
              </CardHeader>
              <CardContent>
                {model.performance_metrics && Object.keys(model.performance_metrics).length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(model.performance_metrics).map(([key, value]) => (
                      <div key={key} className="p-4 border rounded-lg">
                        <div className="text-sm text-muted-foreground mb-1">{key.toUpperCase()}</div>
                        <div className="text-2xl font-bold">{typeof value === 'number' ? value.toFixed(4) : value}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <TrendingUp className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No performance metrics available yet</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="versions" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Version History</CardTitle>
                <CardDescription>All versions of this model</CardDescription>
              </CardHeader>
              <CardContent>
                {model.version_history && model.version_history.length > 0 ? (
                  <div className="space-y-4">
                    {model.version_history.map((version, idx) => (
                      <div key={idx} className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Badge variant={version.is_stable ? 'default' : 'secondary'}>
                              v{version.version}
                            </Badge>
                            {version.is_deprecated && (
                              <Badge variant="destructive">Deprecated</Badge>
                            )}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {formatDate(version.released_at)}
                          </div>
                        </div>
                        <p className="text-sm mb-2">{version.changelog}</p>
                        {version.model_size_mb && (
                          <div className="text-xs text-muted-foreground">
                            Size: {version.model_size_mb.toFixed(1)} MB
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <GitBranch className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No version history available</p>
                    <p className="text-sm mt-1">Current version: v{model.version}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="issues" className="space-y-6">
            {/* Report New Issue */}
            {user && (
              <Card>
                <CardHeader>
                  <CardTitle>Report an Issue</CardTitle>
                  <CardDescription>Help improve this model by reporting problems</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Issue Description</label>
                    <Textarea
                      placeholder="Describe the issue you encountered..."
                      value={issueText}
                      onChange={(e) => setIssueText(e.target.value)}
                      rows={3}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">Severity</label>
                      <Select value={issueSeverity} onValueChange={setIssueSeverity}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="low">Low</SelectItem>
                          <SelectItem value="medium">Medium</SelectItem>
                          <SelectItem value="high">High</SelectItem>
                          <SelectItem value="critical">Critical</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Workaround (Optional)</label>
                    <Textarea
                      placeholder="Any temporary solutions or workarounds..."
                      value={issueWorkaround}
                      onChange={(e) => setIssueWorkaround(e.target.value)}
                      rows={2}
                    />
                  </div>
                  <Button onClick={handleReportIssue} disabled={reportingIssue}>
                    {reportingIssue ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <AlertCircle className="h-4 w-4 mr-2" />
                    )}
                    Submit Issue
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Known Issues */}
            <Card>
              <CardHeader>
                <CardTitle>Known Issues</CardTitle>
                <CardDescription>Reported problems and workarounds</CardDescription>
              </CardHeader>
              <CardContent>
                {model.known_issues && model.known_issues.length > 0 ? (
                  <div className="space-y-4">
                    {model.known_issues.map((issue, idx) => (
                      <div key={idx} className="p-4 border rounded-lg">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Badge className={getSeverityColor(issue.severity)}>
                              {issue.severity}
                            </Badge>
                            {issue.is_resolved && (
                              <Badge variant="outline" className="bg-green-50 text-green-700">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Resolved
                              </Badge>
                            )}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {formatDate(issue.reported_at)}
                          </div>
                        </div>
                        <p className="text-sm mb-2">{issue.issue}</p>
                        {issue.workaround && (
                          <div className="mt-2 p-2 bg-muted rounded text-sm">
                            <div className="font-medium mb-1">Workaround:</div>
                            <div className="text-muted-foreground">{issue.workaround}</div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <CheckCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No known issues reported</p>
                    <p className="text-sm mt-1">This model appears to be working well!</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
      <Footer />

      {/* Model Versions Modal */}
      {model && (
        <ModelVersionsModal
          open={versionsModalOpen}
          onOpenChange={setVersionsModalOpen}
          modelId={modelId!}
          modelName={model.name}
          currentVersion={model.version}
        />
      )}
    </div>
  );
};

export default ModelDetail;
