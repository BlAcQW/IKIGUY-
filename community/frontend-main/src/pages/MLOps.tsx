import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Filter, Download, Play, Pause, Trash2, Plus, TrendingUp, Eye } from "lucide-react";
import Header from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { toast } from "@/hooks/use-toast";
import { ModelRegistrationModal } from "@/components/ModelRegistrationModal";
import { PipelineCreationModal } from "@/components/PipelineCreationModal";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://language-community-api.ailabsafrica.com/api/v1';

interface MLModel {
  model_uuid: string;
  name: string;
  model_type: string;
  architecture: string;
  version: string;
  deployment_status: string;
  languages: string[];
  created_at: string;
  download_count?: number;
  performance_metrics?: Record<string, number>;
}

interface TrainingPipeline {
  pipeline_uuid: string;
  name: string;
  model_type: string;
  current_stage: string;
  is_active: boolean;
  progress_percentage: number;
  created_at: string;
  stages?: Record<string, any>;
}

interface ResourceLink {
  link_uuid: string;
  url: string;
  title: string;
  resource_type: string;
  platform: string;
  languages: string[];
  verification_status: string;
  click_count?: number;
  upvotes?: number;
}

interface ModelStats {
  total_models: number;
  models_by_type: Record<string, number>;
  models_by_status: Record<string, number>;
  total_downloads: number;
  languages_supported: number;
}

interface PipelineStats {
  total_pipelines: number;
  active_pipelines: number;
  completed_pipelines: number;
  pipelines_by_type: Record<string, number>;
  avg_completion_time_hours?: number;
}

const MLOps = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("models");
  const [models, setModels] = useState<MLModel[]>([]);
  const [pipelines, setPipelines] = useState<TrainingPipeline[]>([]);
  const [resources, setResources] = useState<ResourceLink[]>([]);
  const [modelStats, setModelStats] = useState<ModelStats | null>(null);
  const [pipelineStats, setPipelineStats] = useState<PipelineStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [modelTypeFilter, setModelTypeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  // Modal states
  const [isModelRegisterOpen, setIsModelRegisterOpen] = useState(false);
  const [isPipelineCreateOpen, setIsPipelineCreateOpen] = useState(false);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === "models") {
        await Promise.all([loadModels(), loadModelStats()]);
      } else if (activeTab === "pipelines") {
        await Promise.all([loadPipelines(), loadPipelineStats()]);
      } else if (activeTab === "resources") {
        await loadResources();
      }
    } catch (error) {
      console.error("Failed to load data:", error);
      toast({
        title: "Error",
        description: "Failed to load data. Please try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const loadModels = async () => {
    try {
      const params = new URLSearchParams();
      if (modelTypeFilter !== "all") params.append("model_type", modelTypeFilter);
      if (statusFilter !== "all") params.append("deployment_status", statusFilter);
      if (searchTerm) params.append("search", searchTerm);

      const response = await fetch(`${API_BASE_URL}/models?${params}`);
      if (!response.ok) throw new Error("Failed to fetch models");

      const data = await response.json();
      setModels(data.models || []);
    } catch (error) {
      console.error("Error loading models:", error);
      setModels([]);
    }
  };

  const loadPipelines = async () => {
    try {
      const params = new URLSearchParams();
      if (modelTypeFilter !== "all") params.append("model_type", modelTypeFilter);
      if (statusFilter !== "all") params.append("is_active", statusFilter === "active" ? "true" : "false");

      const response = await fetch(`${API_BASE_URL}/pipelines?${params}`);
      if (!response.ok) throw new Error("Failed to fetch pipelines");

      const data = await response.json();
      setPipelines(data.pipelines || []);
    } catch (error) {
      console.error("Error loading pipelines:", error);
      setPipelines([]);
    }
  };

  const loadResources = async () => {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append("search", searchTerm);

      const response = await fetch(`${API_BASE_URL}/resources/links?${params}`);
      if (!response.ok) throw new Error("Failed to fetch resources");

      const data = await response.json();
      setResources(data || []);
    } catch (error) {
      console.error("Error loading resources:", error);
      setResources([]);
    }
  };

  const loadModelStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/models/stats`);
      if (!response.ok) throw new Error("Failed to fetch model stats");

      const data = await response.json();
      setModelStats(data);
    } catch (error) {
      console.error("Error loading model stats:", error);
      setModelStats(null);
    }
  };

  const loadPipelineStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/pipelines/stats`);
      if (!response.ok) throw new Error("Failed to fetch pipeline stats");

      const data = await response.json();
      setPipelineStats(data);
    } catch (error) {
      console.error("Error loading pipeline stats:", error);
      setPipelineStats(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "production": return "bg-green-100 text-green-800";
      case "staging": return "bg-blue-100 text-blue-800";
      case "experimental": return "bg-yellow-100 text-yellow-800";
      case "deprecated": return "bg-red-100 text-red-800";
      case "verified": return "bg-green-100 text-green-800";
      case "pending": return "bg-yellow-100 text-yellow-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getStageIcon = (stage: string) => {
    switch (stage.toLowerCase()) {
      case "data_preparation": return "📊";
      case "training": return "🎯";
      case "evaluation": return "📈";
      case "optimization": return "⚙️";
      case "deployment": return "🚀";
      default: return "📦";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">MLOps Platform</h1>
            <p className="text-gray-600">
              Manage machine learning models, training pipelines, and resources for African languages.
            </p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setIsModelRegisterOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Register Model
            </Button>
            <Button onClick={() => setIsPipelineCreateOpen(true)} variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              Create Pipeline
            </Button>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="models">Models ({models.length})</TabsTrigger>
            <TabsTrigger value="pipelines">Pipelines ({pipelines.length})</TabsTrigger>
            <TabsTrigger value="resources">Resources ({resources.length})</TabsTrigger>
          </TabsList>

          {/* Search and Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && loadData()}
                  className="pl-10"
                />
              </div>
            </div>

            <Select value={modelTypeFilter} onValueChange={setModelTypeFilter}>
              <SelectTrigger className="w-[180px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Model Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="tts">Text-to-Speech</SelectItem>
                <SelectItem value="asr">Speech Recognition</SelectItem>
                <SelectItem value="llm">Language Model</SelectItem>
                <SelectItem value="nmt">Translation</SelectItem>
              </SelectContent>
            </Select>

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                {activeTab === "models" ? (
                  <>
                    <SelectItem value="production">Production</SelectItem>
                    <SelectItem value="staging">Staging</SelectItem>
                    <SelectItem value="experimental">Experimental</SelectItem>
                  </>
                ) : (
                  <>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                  </>
                )}
              </SelectContent>
            </Select>

            <Button onClick={loadData}>
              <TrendingUp className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>

          {/* Models Tab */}
          <TabsContent value="models" className="space-y-4">
            {/* Model Statistics */}
            {modelStats && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm text-muted-foreground">Total Models</div>
                    <div className="text-2xl font-bold">{modelStats.total_models}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm text-muted-foreground">Total Downloads</div>
                    <div className="text-2xl font-bold">{modelStats.total_downloads}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm text-muted-foreground">Languages Supported</div>
                    <div className="text-2xl font-bold">{modelStats.languages_supported}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm text-muted-foreground">Production Models</div>
                    <div className="text-2xl font-bold">{modelStats.models_by_status?.production || 0}</div>
                  </CardContent>
                </Card>
              </div>
            )}

            {loading ? (
              <div className="text-center py-12">Loading models...</div>
            ) : models.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <p className="text-gray-500">No models found. Start by registering your first model.</p>
                  <Button className="mt-4" onClick={() => setIsModelRegisterOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Register Model
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {models.map((model) => (
                  <Card key={model.model_uuid}>
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-lg">{model.name}</CardTitle>
                          <CardDescription>{model.architecture} • v{model.version}</CardDescription>
                        </div>
                        <Badge className={getStatusColor(model.deployment_status)}>
                          {model.deployment_status}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex flex-wrap gap-1">
                        {model.languages.map((lang, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">{lang}</Badge>
                        ))}
                      </div>

                      {model.performance_metrics && Object.keys(model.performance_metrics).length > 0 && (
                        <div className="space-y-2">
                          {Object.entries(model.performance_metrics).slice(0, 2).map(([key, value]) => (
                            <div key={key} className="flex justify-between text-sm">
                              <span className="text-gray-600">{key}:</span>
                              <span className="font-medium">{value.toFixed(3)}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="flex-1"
                          onClick={() => navigate(`/models/${model.model_uuid}`)}
                        >
                          <Eye className="h-3 w-3 mr-1" />
                          View Details
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => navigate(`/models/${model.model_uuid}`)}
                        >
                          <Download className="h-3 w-3" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Pipelines Tab */}
          <TabsContent value="pipelines" className="space-y-4">
            {/* Pipeline Statistics */}
            {pipelineStats && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm text-muted-foreground">Total Pipelines</div>
                    <div className="text-2xl font-bold">{pipelineStats.total_pipelines}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm text-muted-foreground">Active Pipelines</div>
                    <div className="text-2xl font-bold text-green-600">{pipelineStats.active_pipelines}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm text-muted-foreground">Completed</div>
                    <div className="text-2xl font-bold text-blue-600">{pipelineStats.completed_pipelines}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm text-muted-foreground">Avg Completion</div>
                    <div className="text-2xl font-bold">
                      {pipelineStats.avg_completion_time_hours ?
                        `${pipelineStats.avg_completion_time_hours.toFixed(1)}h` :
                        'N/A'}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {loading ? (
              <div className="text-center py-12">Loading pipelines...</div>
            ) : pipelines.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <p className="text-gray-500">No training pipelines found. Create your first pipeline.</p>
                  <Button className="mt-4" onClick={() => setIsPipelineCreateOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Pipeline
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {pipelines.map((pipeline) => (
                  <Card key={pipeline.pipeline_uuid}>
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle>{pipeline.name}</CardTitle>
                          <CardDescription>
                            {pipeline.model_type} • {getStageIcon(pipeline.current_stage)} {pipeline.current_stage}
                          </CardDescription>
                        </div>
                        <Badge className={pipeline.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}>
                          {pipeline.is_active ? "Active" : "Paused"}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <div className="flex justify-between text-sm mb-2">
                          <span>Progress</span>
                          <span>{pipeline.progress_percentage}%</span>
                        </div>
                        <Progress value={pipeline.progress_percentage} className="h-2" />
                      </div>

                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="flex-1"
                          onClick={() => navigate(`/pipelines/${pipeline.pipeline_uuid}`)}
                        >
                          <Eye className="h-3 w-3 mr-1" />
                          View Details
                        </Button>
                        {pipeline.is_active ? (
                          <Button size="sm" variant="outline">
                            <Pause className="h-3 w-3" />
                          </Button>
                        ) : (
                          <Button size="sm" variant="outline">
                            <Play className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Resources Tab */}
          <TabsContent value="resources" className="space-y-4">
            {loading ? (
              <div className="text-center py-12">Loading resources...</div>
            ) : resources.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <p className="text-gray-500">No resources found. Share an external resource.</p>
                  <Button className="mt-4">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Resource
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {resources.map((resource) => (
                  <Card key={resource.link_uuid}>
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-base">{resource.title}</CardTitle>
                          <CardDescription className="break-all">{resource.url}</CardDescription>
                        </div>
                        <Badge className={getStatusColor(resource.verification_status)}>
                          {resource.verification_status}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex items-center gap-2 text-sm">
                        <Badge variant="outline">{resource.platform}</Badge>
                        <Badge variant="outline">{resource.resource_type}</Badge>
                      </div>

                      <div className="flex flex-wrap gap-1">
                        {resource.languages.slice(0, 3).map((lang, idx) => (
                          <Badge key={idx} variant="secondary" className="text-xs">{lang}</Badge>
                        ))}
                      </div>

                      <div className="flex justify-between text-xs text-gray-500">
                        <span>👆 {resource.upvotes || 0} upvotes</span>
                        <span>👁️ {resource.click_count || 0} clicks</span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Modals */}
      <ModelRegistrationModal
        isOpen={isModelRegisterOpen}
        onClose={() => setIsModelRegisterOpen(false)}
        onSuccess={loadData}
      />
      <PipelineCreationModal
        isOpen={isPipelineCreateOpen}
        onClose={() => setIsPipelineCreateOpen(false)}
        onSuccess={loadData}
      />
    </div>
  );
};

export default MLOps;
