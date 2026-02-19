# Frontend Integration Plan

**Created:** 2025-10-22
**Purpose:** Clean integration of MLOps features into existing frontend without duplication

---

## Analysis Summary

### Existing Frontend Structure

**Current Pages (13):**
1. `/` - Index (Landing page)
2. `/dashboard` - User dashboard
3. `/languages` - Language browse
4. `/languages/:code` - Language detail
5. `/languages/families/:id` - Family detail
6. `/submit` - Submission forms
7. `/validate` - Validation interface
8. `/community` - Leaderboards & chat
9. `/moderation` - Moderation tools
10. `/datasets` - Dataset management **(TO BE ENHANCED)**
11. `/search` - Search interface
12. `/profile` - User profile
13. `*` - 404 Not Found

**Current API Client (`lib/api.ts`):**
- Base URL: `https://language-community-api.ailabsafrica.com/api/v1`
- Existing interfaces: Language, LanguageFamily, Submission, Validation, Notebook, etc.
- **Uses mock data** in Datasets page (comment: "For now, we'll use mock data since the dataset endpoints require authentication")

### Integration Strategy

**✅ DO:**
- Enhance existing Datasets page with real API integration
- Add new routes for Models (`/models`) and Pipelines (`/pipelines`)
- Extend existing TypeScript interfaces in `lib/api.ts`
- Create reusable components for version selection, pipeline tracking, etc.
- Wire real backend APIs to replace mock data

**❌ DON'T:**
- Create duplicate pages for existing functionality
- Add new buttons/links that already exist
- Create new submission forms (use existing `/submit`)
- Duplicate language browsing (use existing `/languages`)
- Create separate dashboard (extend existing `/dashboard`)

---

## Phase 1: API Client Enhancement

### File: `src/lib/api.ts`

#### 1.1 Add New Interfaces

```typescript
// ========================================
// NEW: ML Models
// ========================================
export interface MLModel {
  id: string;
  model_uuid: string;
  name: string;
  model_type: 'tts' | 'asr' | 'llm' | 'nmt' | 'ner' | 'pos' | 'sentiment' | 'custom';
  architecture: 'melotts' | 'styletts' | 'xtts' | 'whisper' | 'moshi' | 'llama' | 'mistral' | 'transformer' | 'custom';
  version: string;
  version_history: ModelVersion[];

  // Language support
  languages: string[];
  language_ids: string[];
  primary_language: string;
  is_multilingual: boolean;

  // Performance metrics
  performance_metrics: PerformanceMetrics;

  // Storage & files
  storage_path: string;
  model_size_mb?: number;
  checkpoint_path: string;

  // Deployment
  deployment_status: 'experimental' | 'staging' | 'production' | 'deprecated' | 'archived';
  deployment_url?: string;
  docker_image?: string;

  // Access & licensing
  license: string;
  is_public: boolean;
  access_level: 'public' | 'authenticated' | 'restricted' | 'private';
  download_count: number;

  // Contributors
  created_by: string;
  contributors: string[];

  // Metadata
  tags: string[];
  description?: string;
  paper_url?: string;
  demo_url?: string;
  created_at: string;
  updated_at: string;
}

export interface ModelVersion {
  version: string;
  released_at: string;
  changelog: string;
  storage_path: string;
  performance_metrics: Record<string, number>;
  model_size_mb?: number;
  is_stable: boolean;
  is_deprecated: boolean;
}

export interface PerformanceMetrics {
  wer?: number;       // Word Error Rate (ASR)
  cer?: number;       // Character Error Rate (ASR)
  mos?: number;       // Mean Opinion Score (TTS)
  rtf?: number;       // Real-Time Factor (TTS)
  perplexity?: number; // Perplexity (LLM)
  bleu?: number;      // BLEU score (NMT)
  inference_time_ms?: number;
  throughput?: number;
  custom_metrics?: Record<string, number>;
}

export interface ModelSearchQuery {
  query?: string;
  model_type?: string;
  architecture?: string;
  languages?: string[];
  deployment_status?: string;
  is_public?: boolean;
  min_performance?: number;
  tags?: string[];
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}

export interface ModelListResponse {
  models: MLModel[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ========================================
// NEW: Training Pipelines
// ========================================
export interface TrainingPipeline {
  id: string;
  pipeline_uuid: string;
  name: string;
  model_type: 'tts' | 'asr' | 'llm' | 'nmt';

  // Current stage
  current_stage: 'data_acquisition' | 'preprocessing' | 'training' | 'evaluation' | 'deployment';
  stage_progress: number; // 0-100

  // Pipeline stages
  stages: PipelineStageInfo[];

  // Version & results
  target_version: string;
  result_model_id?: string;

  // Datasets used
  datasets: DatasetReference[];

  // Reproducibility
  experiment_config?: ExperimentConfig;

  // Collaboration
  team_members: string[];
  created_by: string;

  // Status
  is_active: boolean;
  priority: 'low' | 'medium' | 'high' | 'critical';

  // Metadata
  description?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface PipelineStageInfo {
  stage_name: 'data_acquisition' | 'preprocessing' | 'training' | 'evaluation' | 'deployment';
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  started_at?: string;
  completed_at?: string;
  duration_minutes?: number;

  // Stage-specific details
  preprocessing_details?: PreprocessingDetails;
  training_config?: TrainingConfig;
  evaluation_plan?: Record<string, any>;

  // Artifacts produced
  artifacts: StageArtifact[];

  // Metrics
  metrics: Record<string, any>;

  // Checkpoints (for training stage)
  checkpoints: Checkpoint[];

  // Notes and logs
  notes?: string;
  logs: string[];
  error_message?: string;

  // Responsible user
  responsible_user?: string;

  // Resource usage
  resource_usage?: Record<string, number>;
}

export interface PreprocessingDetails {
  frequency?: string;
  format?: string;
  normalization?: string;
  augmentations: string[];
  phonetic_analysis?: Record<string, any>;
  quality_filters?: Record<string, any>;
}

export interface TrainingConfig {
  base_model?: string;
  epochs: number;
  current_epoch?: number;
  batch_size: number;
  learning_rate: number;
  optimizer: string;
  scheduler?: string;
  hardware?: string;
  mixed_precision: boolean;
  gradient_accumulation_steps: number;
}

export interface StageArtifact {
  name: string;
  path: string;
  size_mb?: number;
  artifact_type: 'dataset' | 'model' | 'report' | 'config';
  description?: string;
  checksum?: string;
}

export interface Checkpoint {
  epoch: number;
  path: string;
  metrics: Record<string, number>;
  is_best: boolean;
  notes?: string;
}

export interface DatasetReference {
  dataset_id: string;
  version: string;
  role: 'training' | 'validation' | 'test';
  storage_path?: string;
}

export interface ExperimentConfig {
  seed: number;
  framework: 'pytorch' | 'tensorflow' | 'jax';
  framework_version: string;
  python_version: string;
  cuda_version?: string;
  environment_variables: Record<string, string>;
}

// ========================================
// NEW: Dataset Versions
// ========================================
export interface DatasetVersion {
  id: string;
  dataset_id: string;
  version: string;

  // Storage
  storage_path: string;
  manifest_url: string;

  // Changes from previous version
  parent_version?: string;
  changelog: string;
  diff_summary?: VersionDiff;

  // Statistics
  stats: VersionStats;

  // Quality metrics
  quality_report?: QualityReport;

  // Splits
  splits: Record<string, DatasetSplit>;

  // Checksums
  checksum: string;
  file_checksums_url: string;

  // Release info
  is_stable: boolean;
  is_prerelease: boolean;
  release_notes?: string;
  released_by: string;
  released_at: string;

  // Deprecation
  is_deprecated: boolean;
  deprecation_reason?: string;

  // Usage tracking
  download_count: number;
  used_in_models: string[];

  created_at: string;
  updated_at: string;
}

export interface VersionDiff {
  files_added: number;
  files_removed: number;
  files_modified: number;
  size_change_mb: number;
  added_files: string[];
  removed_files: string[];
  modified_files: string[];
}

export interface VersionStats {
  total_files: number;
  total_size_mb: number;
  total_duration_hours?: number;
  speakers?: number;
  avg_quality_score?: number;
}

export interface QualityReport {
  transcription_accuracy?: number;
  avg_snr_db?: number;
  audio_quality_score?: number;
  consistency_score?: number;
  completeness_score?: number;
}

export interface DatasetSplit {
  files: number;
  hours?: number;
  samples?: number;
}

// ========================================
// NEW: Resource Links & Uploads
// ========================================
export interface ResourceLink {
  id: string;
  link_uuid: string;

  // Resource info
  title: string;
  url: string;
  resource_type: 'dataset' | 'model' | 'paper' | 'tool' | 'notebook' | 'documentation' | 'tutorial' | 'other';
  platform: 'huggingface' | 'github' | 'kaggle' | 'zenodo' | 'arxiv' | 'openslr' | 'commonvoice' | 'custom';

  // Classification
  model_type?: string;
  data_type?: string;

  // Language association
  languages: string[];
  language_ids: string[];
  is_multilingual: boolean;

  // Metadata
  description: string;
  tags: string[];
  license?: string;
  citation?: string;

  // Quality & status
  quality_rating: number;
  verification_status: 'verified' | 'unverified' | 'flagged' | 'broken';
  verified_by?: string;
  verified_at?: string;

  // Availability monitoring
  last_checked?: string;
  is_available: boolean;

  // Contributor
  submitted_by: string;

  // Engagement
  upvotes: number;
  downvotes: number;
  view_count: number;
  click_count: number;

  created_at: string;
  updated_at: string;
}

export interface FileUpload {
  id: string;
  upload_uuid: string;

  // User info
  uploaded_by: string;
  upload_type: 'dataset' | 'model' | 'notebook' | 'resource';

  // File info
  original_filename: string;
  file_type: string;
  mime_type: string;
  file_size_mb: number;

  // Storage
  storage_path: string;
  access_url: string;
  is_temporary: boolean;

  // Processing
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  processing_started_at?: string;
  processing_completed_at?: string;
  processing_error?: string;

  // Validation
  validation_results?: Record<string, any>;

  // Language & metadata
  language_code: string;
  language_id?: string;
  tags: string[];
  description: string;

  // Integration
  integrated_into_dataset?: string;
  integrated_at?: string;

  // Access control
  access_level: 'public' | 'authenticated' | 'private';
  license: string;

  // Security
  is_quarantined: boolean;
  virus_scan_result?: string;
  scanned_at?: string;

  created_at: string;
  expires_at?: string;
}

// ========================================
// ENHANCED: ExternalDataset (add missing fields)
// ========================================
// Add to existing ExternalDataset interface:
export interface ExternalDatasetEnhanced extends ExternalDataset {
  dataset_uuid: string;
  version: string;
  is_latest_version: boolean;
  version_history: string[];

  // Storage and distribution
  storage_path?: string;
  manifest_id?: string;
  checksum?: string;
  download_url?: string;
  is_public: boolean;

  // MLOps pipeline tracking
  used_in_pipelines: string[];
  used_in_models: string[];
  training_ready: boolean;

  // Dataset splits
  has_train_split: boolean;
  has_validation_split: boolean;
  has_test_split: boolean;
  split_ratios?: Record<string, number>;

  published_at?: string;
  download_count: number;
  view_count: number;
  citation_count: number;
  language_id?: string;
}
```

#### 1.2 Add API Client Methods

```typescript
// ========================================
// Models API
// ========================================
class ApiClient {
  // ... existing methods ...

  // NEW: Model methods
  async getModels(query?: ModelSearchQuery): Promise<ModelListResponse> {
    const params = new URLSearchParams();
    if (query) {
      Object.entries(query).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, String(value));
        }
      });
    }
    const response = await fetch(`${API_BASE_URL}/models?${params}`, {
      headers: await this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch models');
    return response.json();
  }

  async getModel(modelUuid: string): Promise<MLModel> {
    const response = await fetch(`${API_BASE_URL}/models/${modelUuid}`, {
      headers: await this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch model');
    return response.json();
  }

  async getModelDownloadUrl(modelUuid: string, version?: string): Promise<{download_url: string; expires_at: string}> {
    const params = version ? `?version=${version}` : '';
    const response = await fetch(`${API_BASE_URL}/models/${modelUuid}/download${params}`, {
      headers: await this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to get download URL');
    return response.json();
  }

  async createModel(model: Partial<MLModel>): Promise<MLModel> {
    const response = await fetch(`${API_BASE_URL}/models`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(model),
    });
    if (!response.ok) throw new Error('Failed to create model');
    return response.json();
  }

  // NEW: Pipeline methods
  async getPipelines(filters?: Record<string, any>): Promise<{pipelines: TrainingPipeline[]; total: number}> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) params.append(key, String(value));
      });
    }
    const response = await fetch(`${API_BASE_URL}/pipelines?${params}`, {
      headers: await this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch pipelines');
    return response.json();
  }

  async getPipeline(pipelineId: string): Promise<TrainingPipeline> {
    const response = await fetch(`${API_BASE_URL}/pipelines/${pipelineId}`, {
      headers: await this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch pipeline');
    return response.json();
  }

  async createPipeline(pipeline: Partial<TrainingPipeline>): Promise<TrainingPipeline> {
    const response = await fetch(`${API_BASE_URL}/pipelines`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(pipeline),
    });
    if (!response.ok) throw new Error('Failed to create pipeline');
    return response.json();
  }

  // NEW: Dataset version methods
  async getDatasetVersions(datasetId: string): Promise<{versions: DatasetVersion[]; latest_version: string}> {
    const response = await fetch(`${API_BASE_URL}/datasets/${datasetId}/versions`, {
      headers: await this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch dataset versions');
    return response.json();
  }

  async getDatasetVersion(datasetId: string, version: string): Promise<DatasetVersion> {
    const response = await fetch(`${API_BASE_URL}/datasets/${datasetId}/versions/${version}`, {
      headers: await this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch dataset version');
    return response.json();
  }

  async compareDatasetVersions(datasetId: string, versionA: string, versionB: string): Promise<VersionDiff> {
    const response = await fetch(`${API_BASE_URL}/datasets/${datasetId}/versions/compare?v1=${versionA}&v2=${versionB}`, {
      headers: await this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to compare versions');
    return response.json();
  }

  // NEW: Resource methods
  async getResourceLinks(filters?: Record<string, any>): Promise<{resources: ResourceLink[]; total: number}> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) params.append(key, String(value));
      });
    }
    const response = await fetch(`${API_BASE_URL}/resources/links?${params}`, {
      headers: await this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch resource links');
    return response.json();
  }

  async createResourceLink(resource: Partial<ResourceLink>): Promise<ResourceLink> {
    const response = await fetch(`${API_BASE_URL}/resources/links`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(resource),
    });
    if (!response.ok) throw new Error('Failed to create resource link');
    return response.json();
  }

  async uploadFile(formData: FormData): Promise<FileUpload> {
    const headers = await this.getAuthHeaders();
    // Remove Content-Type header for FormData (browser will set it with boundary)
    delete headers['Content-Type'];

    const response = await fetch(`${API_BASE_URL}/resources/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });
    if (!response.ok) throw new Error('Failed to upload file');
    return response.json();
  }

  // NEW: Discovery methods
  async getLanguageResources(languageCode: string): Promise<{
    models: MLModel[];
    datasets: ExternalDataset[];
    notebooks: Notebook[];
    pipelines: TrainingPipeline[];
    resource_links: ResourceLink[];
  }> {
    const response = await fetch(`${API_BASE_URL}/languages/${languageCode}/resources`, {
      headers: await this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch language resources');
    return response.json();
  }

  async searchAll(query: string, filters?: Record<string, any>): Promise<{
    models: MLModel[];
    datasets: ExternalDataset[];
    notebooks: Notebook[];
    resource_links: ResourceLink[];
  }> {
    const params = new URLSearchParams({query});
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) params.append(key, String(value));
      });
    }
    const response = await fetch(`${API_BASE_URL}/search?${params}`, {
      headers: await this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to search');
    return response.json();
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Get auth token from Supabase context
    const token = await this.getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  private async getAuthToken(): Promise<string | null> {
    // Implementation depends on how auth is set up
    // This should get the token from AuthContext
    return null; // Placeholder
  }
}

export const apiClient = new ApiClient();
```

---

## Phase 2: Enhance Existing Pages

### 2.1 Datasets Page Enhancement

**File:** `src/pages/Datasets.tsx`

**Current Issues:**
- Uses mock data (comment on line 60-63)
- No version selection
- No download functionality
- No filtering by processing status

**Enhancement Plan:**
```typescript
// REMOVE mock data
// REPLACE with real API calls

const Datasets = () => {
  const [datasets, setDatasets] = useState<ExternalDatasetEnhanced[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<Record<string, string>>({});

  // Replace loadData function with real API call
  const loadData = async () => {
    try {
      setIsLoading(true);

      // REAL API CALL
      const datasetsResponse = await apiClient.getDatasets(
        sourceFilter !== 'all' ? sourceFilter : undefined,
        undefined,
        languageFilter !== 'all' ? languageFilter : undefined,
        statusFilter !== 'all' ? statusFilter : undefined,
        searchTerm || undefined
      );

      setDatasets(datasetsResponse.datasets);
      setTotalCount(datasetsResponse.total);

      // Fetch stats
      const statsResponse = await apiClient.getDatasetStats();
      setStats(statsResponse);
    } catch (error) {
      console.error('Failed to load datasets:', error);
      toast({
        title: "Error",
        description: "Failed to load datasets",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // ADD version selector
  const handleVersionChange = async (datasetId: string, version: string) => {
    setSelectedVersion(prev => ({...prev, [datasetId]: version}));
    // Optionally fetch version details
  };

  // ADD download handler
  const handleDownload = async (datasetId: string, version?: string) => {
    try {
      const downloadInfo = await apiClient.getDatasetDownloadUrl(datasetId, version);
      window.open(downloadInfo.download_url, '_blank');
      toast({
        title: "Download started",
        description: `Downloading dataset version ${version || 'latest'}`,
      });
    } catch (error) {
      toast({
        title: "Download failed",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  // ... rest of component
};
```

### 2.2 Dashboard Enhancement

**File:** `src/pages/Dashboard.tsx`

**Add MLOps Stats:**
```typescript
// Add to existing dashboard stats
const [mlopsStats, setMlopsStats] = useState({
  active_pipelines: 0,
  total_models: 0,
  total_datasets: 0,
  recent_downloads: 0,
});

useEffect(() => {
  const fetchMLopsStats = async () => {
    try {
      const [pipelines, models, datasets] = await Promise.all([
        apiClient.getPipelines({is_active: true}),
        apiClient.getModels({page_size: 1}),
        apiClient.getDatasets(),
      ]);

      setMlopsStats({
        active_pipelines: pipelines.total,
        total_models: models.total,
        total_datasets: datasets.total,
        recent_downloads: 0, // TODO: Add download stats endpoint
      });
    } catch (error) {
      console.error('Failed to fetch MLOps stats:', error);
    }
  };

  fetchMLopsStats();
}, []);

// Add MLOps stat cards to dashboard
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  {/* Existing stats cards */}

  {/* NEW MLOps stat cards */}
  <Card>
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium">Active Pipelines</CardTitle>
      <Activity className="h-4 w-4 text-muted-foreground" />
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{mlopsStats.active_pipelines}</div>
      <p className="text-xs text-muted-foreground">Training in progress</p>
    </CardContent>
  </Card>

  <Card>
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium">Available Models</CardTitle>
      <Layers className="h-4 w-4 text-muted-foreground" />
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{mlopsStats.total_models}</div>
      <p className="text-xs text-muted-foreground">Across all languages</p>
    </CardContent>
  </Card>
</div>
```

### 2.3 Language Detail Page Enhancement

**File:** `src/pages/LanguageDetail.tsx`

**Add Resource Hub Tab:**
```typescript
// Add new tab for resources
<Tabs defaultValue="overview">
  <TabsList>
    <TabsTrigger value="overview">Overview</TabsTrigger>
    <TabsTrigger value="resources">Resources</TabsTrigger> {/* NEW */}
    <TabsTrigger value="submissions">Submissions</TabsTrigger>
    <TabsTrigger value="contributors">Contributors</TabsTrigger>
  </TabsList>

  {/* Existing tabs... */}

  {/* NEW Resources tab */}
  <TabsContent value="resources">
    <LanguageResourceHub languageCode={languageCode} />
  </TabsContent>
</Tabs>
```

---

## Phase 3: New Pages

### 3.1 Models Page (`/models`)

**Create:** `src/pages/Models.tsx`

```typescript
import { useState, useEffect } from 'react';
import { Grid, List, Filter, Download, ExternalLink } from 'lucide-react';
import Header from '@/components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { apiClient, MLModel, ModelSearchQuery } from '@/lib/api';
import { toast } from '@/hooks/use-toast';

const Models = () => {
  const [models, setModels] = useState<MLModel[]>([]);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filters, setFilters] = useState<ModelSearchQuery>({
    page: 1,
    page_size: 20,
    sort_by: 'updated_at',
    sort_order: 'desc',
  });
  const [isLoading, setIsLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadModels();
  }, [filters]);

  const loadModels = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.getModels(filters);
      setModels(response.models);
      setTotal(response.total);
    } catch (error) {
      toast({
        title: "Error loading models",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async (modelUuid: string) => {
    try {
      const {download_url} = await apiClient.getModelDownloadUrl(modelUuid);
      window.open(download_url, '_blank');
      toast({
        title: "Download started",
        description: "Model download has started",
      });
    } catch (error) {
      toast({
        title: "Download failed",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold">ML Model Registry</h1>
            <p className="text-muted-foreground">
              Browse {total} trained models for African languages
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant={viewMode === 'grid' ? 'default' : 'outline'}
              size="icon"
              onClick={() => setViewMode('grid')}
            >
              <Grid className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'list' ? 'default' : 'outline'}
              size="icon"
              onClick={() => setViewMode('list')}
            >
              <List className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-4 mb-6">
          <Select
            value={filters.model_type || 'all'}
            onValueChange={(value) => setFilters({...filters, model_type: value === 'all' ? undefined : value})}
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Model Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="tts">TTS</SelectItem>
              <SelectItem value="asr">ASR</SelectItem>
              <SelectItem value="llm">LLM</SelectItem>
              <SelectItem value="nmt">NMT</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={filters.deployment_status || 'all'}
            onValueChange={(value) => setFilters({...filters, deployment_status: value === 'all' ? undefined : value})}
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Deployment Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="production">Production</SelectItem>
              <SelectItem value="staging">Staging</SelectItem>
              <SelectItem value="experimental">Experimental</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Models Grid/List */}
        <div className={`grid gap-4 ${viewMode === 'grid' ? 'md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
          {models.map((model) => (
            <Card key={model.id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle>{model.name}</CardTitle>
                    <CardDescription>{model.version}</CardDescription>
                  </div>
                  <Badge variant={
                    model.deployment_status === 'production' ? 'default' :
                    model.deployment_status === 'staging' ? 'secondary' :
                    'outline'
                  }>
                    {model.deployment_status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline">{model.model_type.toUpperCase()}</Badge>
                    <Badge variant="outline">{model.architecture}</Badge>
                    {model.languages.map(lang => (
                      <Badge key={lang} variant="secondary">{lang}</Badge>
                    ))}
                  </div>

                  {/* Performance Metrics */}
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {model.performance_metrics.wer && (
                      <div>
                        <span className="text-muted-foreground">WER:</span>
                        <span className="ml-2 font-medium">{(model.performance_metrics.wer * 100).toFixed(1)}%</span>
                      </div>
                    )}
                    {model.performance_metrics.mos && (
                      <div>
                        <span className="text-muted-foreground">MOS:</span>
                        <span className="ml-2 font-medium">{model.performance_metrics.mos.toFixed(2)}/5</span>
                      </div>
                    )}
                    {model.model_size_mb && (
                      <div>
                        <span className="text-muted-foreground">Size:</span>
                        <span className="ml-2 font-medium">{model.model_size_mb.toFixed(0)} MB</span>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => handleDownload(model.model_uuid)}>
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </Button>
                    {model.demo_url && (
                      <Button size="sm" variant="outline" as="a" href={model.demo_url} target="_blank">
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Demo
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Models;
```

### 3.2 Pipelines Page (`/pipelines`)

**Create:** `src/pages/Pipelines.tsx`

```typescript
// Similar structure to Models page, but with pipeline-specific UI
// Shows pipeline stages, progress bars, metrics charts
// Real-time updates via WebSocket if available
```

### 3.3 Add Routes to App.tsx

```typescript
// In src/App.tsx, add new routes:

import Models from "./pages/Models";
import Pipelines from "./pages/Pipelines";

// In Routes component:
<Route path="/models" element={<Models />} />
<Route path="/models/:modelUuid" element={<ModelDetail />} />
<Route path="/pipelines" element={<Pipelines />} />
<Route path="/pipelines/:pipelineId" element={<PipelineDetail />} />
```

---

## Phase 4: New Reusable Components

### 4.1 VersionSelector Component

**Create:** `src/components/VersionSelector.tsx`

```typescript
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';

interface VersionSelectorProps {
  versions: Array<{version: string; is_stable: boolean; is_latest: boolean}>;
  currentVersion: string;
  onVersionChange: (version: string) => void;
}

export const VersionSelector = ({versions, currentVersion, onVersionChange}: VersionSelectorProps) => {
  return (
    <Select value={currentVersion} onValueChange={onVersionChange}>
      <SelectTrigger className="w-[200px]">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {versions.map(v => (
          <SelectItem key={v.version} value={v.version}>
            <div className="flex items-center gap-2">
              <span>v{v.version}</span>
              {v.is_latest && <Badge variant="default" className="text-xs">Latest</Badge>}
              {v.is_stable && <Badge variant="secondary" className="text-xs">Stable</Badge>}
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};
```

### 4.2 PipelineProgress Component

**Create:** `src/components/PipelineProgress.tsx`

```typescript
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Check, Clock, AlertCircle, Loader2 } from 'lucide-react';

interface PipelineProgressProps {
  stages: Array<{
    name: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
  }>;
  currentStage: string;
  overallProgress: number;
}

export const PipelineProgress = ({stages, currentStage, overallProgress}: PipelineProgressProps) => {
  const getStageIcon = (status: string) => {
    switch (status) {
      case 'completed': return <Check className="h-4 w-4 text-green-500" />;
      case 'in_progress': return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'failed': return <AlertCircle className="h-4 w-4 text-red-500" />;
      default: return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <div className="flex justify-between mb-2">
          <span className="text-sm font-medium">Overall Progress</span>
          <span className="text-sm text-muted-foreground">{overallProgress.toFixed(0)}%</span>
        </div>
        <Progress value={overallProgress} />
      </div>

      <div className="space-y-2">
        {stages.map((stage, index) => (
          <div key={stage.name} className="flex items-center gap-3">
            {getStageIcon(stage.status)}
            <span className={`text-sm ${stage.name === currentStage ? 'font-medium' : ''}`}>
              {stage.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </span>
            {stage.status !== 'pending' && (
              <Badge variant={
                stage.status === 'completed' ? 'default' :
                stage.status === 'in_progress' ? 'secondary' :
                'destructive'
              } className="ml-auto">
                {stage.status}
              </Badge>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
```

### 4.3 LanguageResourceHub Component

**Create:** `src/components/LanguageResourceHub.tsx`

```typescript
// Comprehensive component showing all resources for a language
// Tabs: Datasets | Models | Notebooks | Pipelines | Links
// Uses apiClient.getLanguageResources(languageCode)
```

---

## Phase 5: Navigation Updates

### Update Header Component

**File:** `src/components/Header.tsx`

**Add new navigation items:**
```typescript
const navItems = [
  { name: 'Home', path: '/' },
  { name: 'Languages', path: '/languages' },
  { name: 'Datasets', path: '/datasets' },
  { name: 'Models', path: '/models' }, // NEW
  { name: 'Pipelines', path: '/pipelines' }, // NEW
  { name: 'Submit', path: '/submit' },
  { name: 'Validate', path: '/validate' },
  { name: 'Community', path: '/community' },
];
```

---

## Implementation Checklist

### Phase 1: API Client (Week 1)
- [ ] Add TypeScript interfaces to `lib/api.ts`
- [ ] Implement API client methods
- [ ] Add auth header integration with Supabase
- [ ] Test API calls with backend endpoints

### Phase 2: Enhance Existing Pages (Week 1-2)
- [ ] Replace mock data in Datasets page with real API calls
- [ ] Add version selector to Datasets page
- [ ] Add download functionality
- [ ] Add MLOps stats to Dashboard
- [ ] Add Resources tab to Language Detail page

### Phase 3: New Pages (Week 2-3)
- [ ] Create Models page (`/models`)
- [ ] Create Model Detail page (`/models/:uuid`)
- [ ] Create Pipelines page (`/pipelines`)
- [ ] Create Pipeline Detail page (`/pipelines/:id`)
- [ ] Add routes to App.tsx

### Phase 4: New Components (Week 3-4)
- [ ] Create VersionSelector component
- [ ] Create PipelineProgress component
- [ ] Create LanguageResourceHub component
- [ ] Create VersionComparison component
- [ ] Create ModelCard component (reusable)
- [ ] Create DatasetCard component (enhance existing)

### Phase 5: Navigation & Polish (Week 4)
- [ ] Update Header navigation
- [ ] Add search functionality for Models/Pipelines
- [ ] Add loading states
- [ ] Add error boundaries
- [ ] Add toast notifications
- [ ] Test all user flows

---

## Testing Strategy

### Unit Tests
- Test API client methods with mock responses
- Test component rendering
- Test filter/search logic

### Integration Tests
- Test full user flows (browse → filter → download)
- Test version comparison
- Test pipeline tracking updates

### E2E Tests
- Critical paths: Model discovery → Download
- Dataset versioning flow
- Pipeline creation and tracking

---

## Deployment Strategy

### Feature Flags
Use environment variables to enable new features gradually:
```typescript
const FEATURE_FLAGS = {
  ENABLE_MODELS_PAGE: import.meta.env.VITE_ENABLE_MODELS === 'true',
  ENABLE_PIPELINES_PAGE: import.meta.env.VITE_ENABLE_PIPELINES === 'true',
  ENABLE_DOWNLOADS: import.meta.env.VITE_ENABLE_DOWNLOADS === 'true',
};
```

### Rollout Plan
1. **Week 1-2:** Deploy API enhancements to staging
2. **Week 2-3:** Deploy frontend enhancements with feature flags OFF
3. **Week 3:** Enable features for internal testing
4. **Week 4:** Public beta release
5. **Week 5:** Full release

---

## Summary

This integration plan ensures:
✅ **No Duplication:** Extends existing pages instead of creating new ones
✅ **Clean Integration:** Uses existing component patterns and styling
✅ **Backward Compatible:** Preserves all existing functionality
✅ **Type Safe:** Full TypeScript interfaces for new features
✅ **Testable:** Clear separation of concerns
✅ **Scalable:** Reusable components for future features

The key philosophy: **Enhance, don't replace. Extend, don't duplicate.**
