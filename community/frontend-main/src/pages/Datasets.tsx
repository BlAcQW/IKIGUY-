import { useState, useEffect } from "react";
import { Plus, Search, Download, Play, Pause, Trash2, Filter, RefreshCw, Loader2, Package, ExternalLink } from "lucide-react";
import Header from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "@/hooks/use-toast";
import DatasetVersionsModal from "@/components/DatasetVersionsModal";
import {
  apiClient,
  ExternalDataset,
  DatasetStats,
  DatasetCreate
} from "@/lib/api";

interface NewDatasetForm {
  name: string;
  source: string;
  dataset_type: string;
  language_code: string;
  source_url: string;
  license_type: string;
  description: string;
  tags: string;
}

const Datasets = () => {
  const [datasets, setDatasets] = useState<ExternalDataset[]>([]);
  const [stats, setStats] = useState<DatasetStats | null>(null);
  const [filteredDatasets, setFilteredDatasets] = useState<ExternalDataset[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [languageFilter, setLanguageFilter] = useState("all");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [newDataset, setNewDataset] = useState<NewDatasetForm>({
    name: "",
    source: "",
    dataset_type: "",
    language_code: "",
    source_url: "",
    license_type: "",
    description: "",
    tags: ""
  });
  const [totalCount, setTotalCount] = useState(0);

  // Version modal state
  const [versionsModalOpen, setVersionsModalOpen] = useState(false);
  const [selectedDatasetForVersions, setSelectedDatasetForVersions] = useState<{
    id: string;
    name: string;
    version?: string;
  } | null>(null);

  const handleOpenVersionsModal = (dataset: ExternalDataset) => {
    setSelectedDatasetForVersions({
      id: dataset.id,
      name: dataset.name,
      version: dataset.version,
    });
    setVersionsModalOpen(true);
  };

  // Load data function
  const loadData = async () => {
    try {
      setIsLoading(true);

      // Connect to real backend APIs
      const datasetsResponse = await apiClient.getDatasets(
        sourceFilter !== 'all' ? sourceFilter : undefined,
        undefined,
        languageFilter !== 'all' ? languageFilter : undefined,
        statusFilter !== 'all' ? statusFilter : undefined,
        searchTerm || undefined
      );
      const statsResponse = await apiClient.getDatasetStats();

      setDatasets(datasetsResponse.datasets);
      setStats(statsResponse);
      setTotalCount(datasetsResponse.total_count);

    } catch (error) {
      console.error("Failed to load dataset data:", error);

      // Fallback to mock data on error
      const mockDatasets: ExternalDataset[] = [
        {
          id: "1",
          name: "Common Voice 11.0 - Yoruba",
          source: "common_voice",
          dataset_type: "audio_speech",
          language_code: "yo",
          language_family: "niger-congo",
          processing_status: "completed",
          total_files: 15420,
          total_size_mb: 2340.5,
          total_duration_hours: 45.2,
          quality_score: 0.89,
          files_processed: 15420,
          files_integrated: 14895,
          files_rejected: 525,
          duplicate_files: 0,
          created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
          created_by: "admin",
          description: "Yoruba speech dataset from Mozilla Common Voice project containing validated audio clips with transcriptions",
          tags: ["speech", "yoruba", "voice", "africa", "validated"],
          license_type: "cc0",
          commercial_use_allowed: true,
          auto_process: true,
          priority: 2
        },
        {
          id: "2",
          name: "OpenSLR32 - Yoruba Speech Corpus",
          source: "openslr",
          dataset_type: "audio_speech",
          language_code: "yo",
          language_family: "niger-congo",
          processing_status: "processing",
          total_files: 8750,
          total_size_mb: 1250.0,
          total_duration_hours: 28.5,
          quality_score: 0.94,
          files_processed: 4200,
          files_integrated: 3980,
          files_rejected: 220,
          duplicate_files: 15,
          created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
          created_by: "researcher",
          description: "High-quality Yoruba speech corpus from OpenSLR with phonetic transcriptions",
          tags: ["speech", "yoruba", "openslr", "phonetic"],
          license_type: "cc_by_sa",
          commercial_use_allowed: true,
          processing_started_at: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
          auto_process: true,
          priority: 2
        },
        {
          id: "3",
          name: "Masakhane MT - English-Twi",
          source: "masakhane",
          dataset_type: "translation_pairs",
          language_code: "tw",
          language_family: "niger-congo",
          processing_status: "completed",
          total_files: 25000,
          total_size_mb: 45.2,
          total_words: 850000,
          quality_score: 0.76,
          files_processed: 25000,
          files_integrated: 23800,
          files_rejected: 1200,
          duplicate_files: 240,
          created_at: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString(),
          created_by: "contributor",
          description: "English-Twi translation pairs from Masakhane project based on JW300 corpus",
          tags: ["translation", "twi", "masakhane", "parallel"],
          license_type: "cc_by",
          commercial_use_allowed: true,
          processing_completed_at: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
          auto_process: true,
          priority: 3
        },
        {
          id: "4",
          name: "BBC Hausa News Corpus",
          source: "custom_scrape",
          dataset_type: "text_corpus",
          language_code: "ha",
          language_family: "afroasiatic",
          processing_status: "downloading",
          total_files: 45000,
          total_size_mb: 230.5,
          total_words: 2500000,
          files_processed: 12000,
          files_integrated: 11450,
          files_rejected: 550,
          duplicate_files: 890,
          created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          created_by: "researcher",
          description: "News articles scraped from BBC Hausa service for text corpus development",
          tags: ["news", "hausa", "scraping", "bbc", "current"],
          license_type: "custom",
          commercial_use_allowed: false,
          processing_started_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
          auto_process: true,
          priority: 3
        },
        {
          id: "5",
          name: "OpenSLR56 - Hausa Speech Corpus",
          source: "openslr",
          dataset_type: "audio_speech",
          language_code: "ha",
          language_family: "afroasiatic",
          processing_status: "failed",
          total_files: 12340,
          total_size_mb: 1890.3,
          files_processed: 0,
          files_integrated: 0,
          files_rejected: 0,
          duplicate_files: 0,
          created_at: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
          created_by: "contributor",
          description: "Hausa speech corpus with orthographic transcriptions",
          tags: ["speech", "hausa", "openslr", "orthographic"],
          license_type: "cc_by",
          commercial_use_allowed: true,
          processing_error: "Download failed: Connection timeout after multiple retries",
          auto_process: true,
          priority: 3
        }
      ];

      const mockStats: DatasetStats = {
        total_datasets: 5,
        datasets_by_source: { "common_voice": 1, "openslr": 2, "masakhane": 1, "custom_scrape": 1 },
        datasets_by_language: { "yo": 2, "tw": 1, "ha": 2 },
        datasets_by_status: { "completed": 2, "processing": 1, "downloading": 1, "failed": 1 },
        total_files_integrated: 53125,
        total_size_gb: 5.8,
        total_audio_hours: 73.7,
        average_quality_score: 0.84,
        processing_queue_length: 2
      };

      // Use mock data as fallback
      setDatasets(mockDatasets);
      setStats(mockStats);
      setTotalCount(mockDatasets.length);

      toast({
        title: "Using fallback data",
        description: "Could not load real dataset data. Showing sample data.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    // Filter datasets based on search and filters
    let filtered = datasets.filter(dataset => {
      const matchesSearch = dataset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           dataset.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           dataset.language_code.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesSource = sourceFilter === "all" || dataset.source === sourceFilter;
      const matchesStatus = statusFilter === "all" || dataset.processing_status === statusFilter;
      const matchesLanguage = languageFilter === "all" || dataset.language_code === languageFilter;

      return matchesSearch && matchesSource && matchesStatus && matchesLanguage;
    });

    setFilteredDatasets(filtered);
  }, [datasets, searchTerm, sourceFilter, statusFilter, languageFilter]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed": return "bg-green-100 text-green-800";
      case "processing": return "bg-blue-100 text-blue-800";
      case "downloading": return "bg-yellow-100 text-yellow-800";
      case "failed": return "bg-red-100 text-red-800";
      case "paused": return "bg-gray-100 text-gray-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getSourceIcon = (source: string) => {
    switch (source) {
      case "common_voice": return "🎤";
      case "openslr": return "📊";
      case "masakhane": return "🌍";
      case "custom_scrape": return "🔍";
      default: return "📁";
    }
  };

  const handleCreateDataset = async () => {
    try {
      const datasetData: DatasetCreate = {
        name: newDataset.name,
        source: newDataset.source,
        dataset_type: newDataset.dataset_type,
        language_code: newDataset.language_code,
        source_url: newDataset.source_url,
        license_type: newDataset.license_type,
        description: newDataset.description,
        tags: (newDataset.tags || "").split(",").map(tag => tag.trim()).filter(Boolean),
        auto_process: true,
        quality_threshold: 0.7,
        priority: 3
      };

      // Call real backend API
      const createdDataset = await apiClient.createDataset(datasetData);

      // Refresh dataset list
      await loadData();

      setIsCreateDialogOpen(false);
      setNewDataset({
        name: "",
        source: "",
        dataset_type: "",
        language_code: "",
        source_url: "",
        license_type: "",
        description: "",
        tags: ""
      });

      toast({
        title: "Dataset Integration Created",
        description: `${newDataset.name} has been added to the processing queue.`
      });
    } catch (error) {
      console.error("Failed to create dataset:", error);
      toast({
        title: "Error",
        description: "Failed to create dataset integration. Please try again.",
        variant: "destructive"
      });
    }
  };

  const handleStartProcessing = async (datasetId: string) => {
    try {
      // Call real backend API
      await apiClient.startDatasetProcessing(datasetId);

      // Refresh dataset list
      await loadData();

      toast({
        title: "Processing Started",
        description: "Dataset processing has been initiated."
      });
    } catch (error) {
      console.error("Failed to start processing:", error);
      toast({
        title: "Error",
        description: "Failed to start processing. Please try again.",
        variant: "destructive"
      });
    }
  };

  const handlePauseProcessing = async (datasetId: string) => {
    try {
      // Call real backend API
      await apiClient.pauseDatasetProcessing(datasetId);

      // Refresh dataset list
      await loadData();

      toast({
        title: "Processing Paused",
        description: "Dataset processing has been paused."
      });
    } catch (error) {
      console.error("Failed to pause processing:", error);
      toast({
        title: "Error",
        description: "Failed to pause processing. Please try again.",
        variant: "destructive"
      });
    }
  };

  const handleDeleteDataset = async (datasetId: string) => {
    try {
      // Call real backend API
      await apiClient.deleteDataset(datasetId);

      // Refresh dataset list
      await loadData();

      toast({
        title: "Dataset Deleted",
        description: "Dataset integration has been removed."
      });
    } catch (error) {
      console.error("Failed to delete dataset:", error);
      toast({
        title: "Error",
        description: "Failed to delete dataset. Please try again.",
        variant: "destructive"
      });
    }
  };

  const handleExportManifest = async (datasetId: string) => {
    try {
      // Call real backend API
      const blob = await apiClient.exportDatasetManifest(datasetId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `dataset_${datasetId}_manifest.json`;
      link.click();
      window.URL.revokeObjectURL(url);

      toast({
        title: "Export Complete",
        description: "Dataset manifest has been downloaded."
      });
    } catch (error) {
      console.error("Failed to export manifest:", error);
      toast({
        title: "Error",
        description: "Failed to export dataset manifest. Please try again.",
        variant: "destructive"
      });
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <span className="ml-2 text-lg">Loading datasets...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Dataset Integration</h1>
          <p className="text-gray-600">
            Manage external dataset integrations from Common Voice, OpenSLR, Masakhane, and custom sources.
          </p>
        </div>

        {/* Statistics Overview */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Total Datasets</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">{stats.total_datasets}</div>
                <p className="text-xs text-gray-500 mt-1">{stats.processing_queue_length} in queue</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Files Integrated</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">{stats.total_files_integrated.toLocaleString()}</div>
                <p className="text-xs text-gray-500 mt-1">{stats.total_size_gb.toFixed(1)} GB total</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Audio Hours</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-purple-600">{stats.total_audio_hours.toFixed(1)}</div>
                <p className="text-xs text-gray-500 mt-1">of speech data</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Avg Quality</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-600">{(stats.average_quality_score * 100).toFixed(1)}%</div>
                <p className="text-xs text-gray-500 mt-1">quality score</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Controls */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="Search datasets by name, language, or description..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <Select value={sourceFilter} onValueChange={setSourceFilter}>
              <SelectTrigger className="w-[140px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Source" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sources</SelectItem>
                <SelectItem value="common_voice">Common Voice</SelectItem>
                <SelectItem value="openslr">OpenSLR</SelectItem>
                <SelectItem value="masakhane">Masakhane</SelectItem>
                <SelectItem value="custom_scrape">Custom Scrape</SelectItem>
              </SelectContent>
            </Select>

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="downloading">Downloading</SelectItem>
                <SelectItem value="processing">Processing</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="paused">Paused</SelectItem>
              </SelectContent>
            </Select>

            <Select value={languageFilter} onValueChange={setLanguageFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Languages</SelectItem>
                <SelectItem value="yo">Yoruba (yo)</SelectItem>
                <SelectItem value="tw">Twi (tw)</SelectItem>
                <SelectItem value="sw">Swahili (sw)</SelectItem>
                <SelectItem value="ha">Hausa (ha)</SelectItem>
                <SelectItem value="ig">Igbo (ig)</SelectItem>
                <SelectItem value="zu">Zulu (zu)</SelectItem>
              </SelectContent>
            </Select>

            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Integration
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Create Dataset Integration</DialogTitle>
                  <DialogDescription>
                    Add a new external dataset to integrate with the platform.
                  </DialogDescription>
                </DialogHeader>

                <Tabs defaultValue="basic" className="w-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="basic">Basic Info</TabsTrigger>
                    <TabsTrigger value="source">Source Config</TabsTrigger>
                  </TabsList>

                  <TabsContent value="basic" className="space-y-4">
                    <div>
                      <Label htmlFor="name">Dataset Name</Label>
                      <Input
                        id="name"
                        value={newDataset.name}
                        onChange={(e) => setNewDataset({ ...newDataset, name: e.target.value })}
                        placeholder="e.g., Common Voice 11.0 - Yoruba"
                      />
                    </div>

                    <div>
                      <Label htmlFor="source">Source</Label>
                      <Select value={newDataset.source} onValueChange={(value) => setNewDataset({ ...newDataset, source: value })}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select source" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="common_voice">Common Voice</SelectItem>
                          <SelectItem value="openslr">OpenSLR</SelectItem>
                          <SelectItem value="masakhane">Masakhane</SelectItem>
                          <SelectItem value="custom_scrape">Custom Scrape</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="dataset_type">Dataset Type</Label>
                      <Select value={newDataset.dataset_type} onValueChange={(value) => setNewDataset({ ...newDataset, dataset_type: value })}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="audio_speech">Audio Speech</SelectItem>
                          <SelectItem value="text_corpus">Text Corpus</SelectItem>
                          <SelectItem value="translation_pairs">Translation Pairs</SelectItem>
                          <SelectItem value="pronunciation_dict">Pronunciation Dictionary</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="language_code">Language Code</Label>
                      <Input
                        id="language_code"
                        value={newDataset.language_code}
                        onChange={(e) => setNewDataset({ ...newDataset, language_code: e.target.value })}
                        placeholder="e.g., yo, tw, sw"
                      />
                    </div>
                  </TabsContent>

                  <TabsContent value="source" className="space-y-4">
                    <div>
                      <Label htmlFor="source_url">Source URL</Label>
                      <Input
                        id="source_url"
                        value={newDataset.source_url}
                        onChange={(e) => setNewDataset({ ...newDataset, source_url: e.target.value })}
                        placeholder="https://example.com/dataset.tar.gz"
                      />
                    </div>

                    <div>
                      <Label htmlFor="license_type">License Type</Label>
                      <Select value={newDataset.license_type} onValueChange={(value) => setNewDataset({ ...newDataset, license_type: value })}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select license" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="cc0">CC0 - Public Domain</SelectItem>
                          <SelectItem value="cc_by">CC BY - Attribution</SelectItem>
                          <SelectItem value="cc_by_sa">CC BY-SA - Attribution-ShareAlike</SelectItem>
                          <SelectItem value="mit">MIT License</SelectItem>
                          <SelectItem value="apache_2">Apache 2.0</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="description">Description</Label>
                      <Textarea
                        id="description"
                        value={newDataset.description}
                        onChange={(e) => setNewDataset({ ...newDataset, description: e.target.value })}
                        placeholder="Describe the dataset and its contents..."
                        rows={3}
                      />
                    </div>

                    <div>
                      <Label htmlFor="tags">Tags (comma-separated)</Label>
                      <Input
                        id="tags"
                        value={newDataset.tags}
                        onChange={(e) => setNewDataset({ ...newDataset, tags: e.target.value })}
                        placeholder="speech, voice, african, yoruba"
                      />
                    </div>
                  </TabsContent>
                </Tabs>

                <div className="flex justify-end gap-2 mt-6">
                  <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateDataset} disabled={!newDataset.name || !newDataset.source}>
                    Create Integration
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Dataset Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {(filteredDatasets || []).map((dataset) => (
            <Card key={dataset.id} className="h-full">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{getSourceIcon(dataset.source)}</span>
                    <div>
                      <CardTitle className="text-lg">{dataset.name}</CardTitle>
                      <CardDescription className="text-sm">
                        {dataset.language_code.toUpperCase()} • {dataset.dataset_type.replace('_', ' ')}
                      </CardDescription>
                    </div>
                  </div>
                  <Badge className={getStatusColor(dataset.processing_status)}>
                    {dataset.processing_status}
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {dataset.description && (
                  <p className="text-sm text-gray-600 line-clamp-2">{dataset.description}</p>
                )}

                {/* Progress bar for processing datasets */}
                {["downloading", "processing"].includes(dataset.processing_status) && dataset.total_files && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Progress</span>
                      <span>{Math.round((dataset.files_processed / dataset.total_files) * 100)}%</span>
                    </div>
                    <Progress
                      value={(dataset.files_processed / dataset.total_files) * 100}
                      className="h-2"
                    />
                  </div>
                )}

                {/* Dataset Statistics */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Total Files</p>
                    <p className="font-medium">{dataset.total_files?.toLocaleString() || "—"}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Size</p>
                    <p className="font-medium">
                      {dataset.total_size_mb ? `${(dataset.total_size_mb / 1024).toFixed(1)} GB` : "—"}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Integrated</p>
                    <p className="font-medium text-green-600">{dataset.files_integrated.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Quality</p>
                    <p className="font-medium">
                      {dataset.quality_score ? `${(dataset.quality_score * 100).toFixed(0)}%` : "—"}
                    </p>
                  </div>
                </div>

                {/* Tags */}
                {dataset.tags && dataset.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {(dataset.tags || []).slice(0, 3).map((tag, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                    {dataset.tags.length > 3 && (
                      <Badge variant="secondary" className="text-xs">
                        +{dataset.tags.length - 3} more
                      </Badge>
                    )}
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex justify-between items-center pt-2">
                  <div className="flex gap-1">
                    {dataset.processing_status === "pending" && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleStartProcessing(dataset.id)}
                      >
                        <Play className="h-3 w-3 mr-1" />
                        Start
                      </Button>
                    )}

                    {["downloading", "processing"].includes(dataset.processing_status) && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handlePauseProcessing(dataset.id)}
                      >
                        <Pause className="h-3 w-3 mr-1" />
                        Pause
                      </Button>
                    )}

                    {dataset.processing_status === "completed" && (
                      <>
                        {dataset.hosting_type === 'local' ? (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              // TODO: Implement download for local datasets
                              console.log('Download dataset:', dataset.id, dataset.download_url);
                              alert('Download functionality coming soon!');
                            }}
                          >
                            <Download className="h-3 w-3 mr-1" />
                            Download
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              if (dataset.source_url) {
                                window.open(dataset.source_url, '_blank');
                              }
                            }}
                            disabled={!dataset.source_url}
                          >
                            <ExternalLink className="h-3 w-3 mr-1" />
                            View Source
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleExportManifest(dataset.id)}
                        >
                          <Download className="h-3 w-3 mr-1" />
                          Export
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleOpenVersionsModal(dataset)}
                        >
                          <Package className="h-3 w-3 mr-1" />
                          Versions
                        </Button>
                      </>
                    )}
                  </div>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDeleteDataset(dataset.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredDatasets.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <Search className="h-12 w-12 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No datasets found</h3>
            <p className="text-gray-500 mb-4">
              {searchTerm || sourceFilter !== "all" || statusFilter !== "all" || languageFilter !== "all"
                ? "Try adjusting your search or filters"
                : "Start by creating your first dataset integration"
              }
            </p>
            {!searchTerm && sourceFilter === "all" && statusFilter === "all" && languageFilter === "all" && (
              <Button onClick={() => setIsCreateDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Dataset Integration
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Dataset Versions Modal */}
      {selectedDatasetForVersions && (
        <DatasetVersionsModal
          datasetId={selectedDatasetForVersions.id}
          datasetName={selectedDatasetForVersions.name}
          currentVersion={selectedDatasetForVersions.version}
          open={versionsModalOpen}
          onOpenChange={setVersionsModalOpen}
        />
      )}
    </div>
  );
};

export default Datasets;