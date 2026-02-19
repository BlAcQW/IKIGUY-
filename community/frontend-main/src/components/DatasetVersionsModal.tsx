import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { toast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import {
  Package,
  Download,
  GitCompare,
  Plus,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  X,
  History,
  FileText,
  BarChart3,
  Info,
  Loader2,
} from "lucide-react";

interface DatasetVersionsModalProps {
  datasetId: string;
  datasetName: string;
  currentVersion?: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface DatasetVersion {
  id: string;
  dataset_id: string;
  version: string;
  changelog: string;
  stats: {
    total_files: number;
    total_size_mb: number;
    total_duration_hours?: number;
  };
  quality_report?: {
    transcription_accuracy?: number;
    avg_snr_db?: number;
    audio_quality_score?: number;
  };
  is_stable: boolean;
  is_prerelease: boolean;
  is_deprecated: boolean;
  released_at: string;
  download_count: number;
  checksum: string;
  diff_summary?: {
    files_added: number;
    files_removed: number;
    files_modified: number;
    size_change_mb: number;
  };
}

const DatasetVersionsModal = ({
  datasetId,
  datasetName,
  currentVersion,
  open,
  onOpenChange,
}: DatasetVersionsModalProps) => {
  const [activeTab, setActiveTab] = useState<string>("list");
  const [versions, setVersions] = useState<DatasetVersion[]>([]);
  const [latestVersion, setLatestVersion] = useState<string>("0.0.0");
  const [stableVersion, setStableVersion] = useState<string>("0.0.0");
  const [selectedVersion, setSelectedVersion] = useState<DatasetVersion | null>(null);
  const [compareVersionA, setCompareVersionA] = useState<string>("");
  const [compareVersionB, setCompareVersionB] = useState<string>("");
  const [comparisonResult, setComparisonResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isComparing, setIsComparing] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Filters
  const [showDeprecated, setShowDeprecated] = useState(false);
  const [showPrerelease, setShowPrerelease] = useState(false);

  // Create version form state
  const [newVersion, setNewVersion] = useState({
    version: "",
    storage_path: "",
    changelog: "",
    is_stable: true,
    is_prerelease: false,
    total_files: 0,
    total_size_mb: 0,
    total_duration_hours: 0,
  });

  // Load versions
  const loadVersions = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.getDatasetVersions(
        datasetId,
        showDeprecated,
        showPrerelease
      );
      setVersions(response.versions);
      setLatestVersion(response.latest_version);
      setStableVersion(response.stable_version);
    } catch (error) {
      console.error("Failed to load versions:", error);
      toast({
        title: "Error",
        description: "Failed to load dataset versions",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (open) {
      loadVersions();
    }
  }, [open, datasetId, showDeprecated, showPrerelease]);

  // Load version details
  const loadVersionDetails = async (version: string) => {
    try {
      const versionData = await apiClient.getDatasetVersion(datasetId, version);
      setSelectedVersion(versionData);
      setActiveTab("details");
    } catch (error) {
      console.error("Failed to load version details:", error);
      toast({
        title: "Error",
        description: "Failed to load version details",
        variant: "destructive",
      });
    }
  };

  // Compare versions
  const handleCompareVersions = async () => {
    if (!compareVersionA || !compareVersionB) {
      toast({
        title: "Error",
        description: "Please select two versions to compare",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsComparing(true);
      const result = await apiClient.compareDatasetVersions(
        datasetId,
        compareVersionA,
        compareVersionB
      );
      setComparisonResult(result);
    } catch (error) {
      console.error("Failed to compare versions:", error);
      toast({
        title: "Error",
        description: "Failed to compare versions",
        variant: "destructive",
      });
    } finally {
      setIsComparing(false);
    }
  };

  // Download version
  const handleDownloadVersion = async (version: string) => {
    try {
      const downloadInfo = await apiClient.downloadDatasetVersion(datasetId, version);

      // Open download URL in new tab
      window.open(downloadInfo.download_url, '_blank');

      toast({
        title: "Download Started",
        description: `Downloading dataset version ${version}`,
      });
    } catch (error) {
      console.error("Failed to download version:", error);
      toast({
        title: "Error",
        description: "Failed to initiate download",
        variant: "destructive",
      });
    }
  };

  // Create new version
  const handleCreateVersion = async () => {
    try {
      const versionData = {
        version: newVersion.version,
        storage_path: newVersion.storage_path,
        changelog: newVersion.changelog,
        is_stable: newVersion.is_stable,
        is_prerelease: newVersion.is_prerelease,
        stats: {
          total_files: newVersion.total_files,
          total_size_mb: newVersion.total_size_mb,
          total_duration_hours: newVersion.total_duration_hours || 0,
        },
      };

      await apiClient.createDatasetVersion(datasetId, versionData);

      toast({
        title: "Version Created",
        description: `Version ${newVersion.version} created successfully`,
      });

      setShowCreateForm(false);
      setNewVersion({
        version: "",
        storage_path: "",
        changelog: "",
        is_stable: true,
        is_prerelease: false,
        total_files: 0,
        total_size_mb: 0,
        total_duration_hours: 0,
      });

      await loadVersions();
      setActiveTab("list");
    } catch (error) {
      console.error("Failed to create version:", error);
      toast({
        title: "Error",
        description: "Failed to create version",
        variant: "destructive",
      });
    }
  };

  // Suggest next version
  const handleSuggestVersion = async (bumpType: 'major' | 'minor' | 'patch') => {
    try {
      const result = await apiClient.suggestNextVersion(datasetId, latestVersion, bumpType);
      setNewVersion({ ...newVersion, version: result.suggested_version });

      if (result.already_exists) {
        toast({
          title: "Warning",
          description: `Version ${result.suggested_version} already exists`,
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Failed to suggest version:", error);
    }
  };

  const getVersionBadgeColor = (version: DatasetVersion) => {
    if (version.is_deprecated) return "bg-red-100 text-red-800";
    if (version.is_prerelease) return "bg-yellow-100 text-yellow-800";
    if (version.is_stable) return "bg-green-100 text-green-800";
    return "bg-gray-100 text-gray-800";
  };

  const getVersionLabel = (version: DatasetVersion) => {
    if (version.is_deprecated) return "Deprecated";
    if (version.is_prerelease) return "Pre-release";
    if (version.is_stable) return "Stable";
    return "Beta";
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            {datasetName} - Version Management
          </DialogTitle>
          <DialogDescription>
            Manage dataset versions with semantic versioning, changelogs, and quality tracking
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="list">Versions</TabsTrigger>
            <TabsTrigger value="create">Create</TabsTrigger>
            <TabsTrigger value="compare">Compare</TabsTrigger>
            <TabsTrigger value="details" disabled={!selectedVersion}>
              Details
            </TabsTrigger>
          </TabsList>

          {/* Versions List Tab */}
          <TabsContent value="list" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex gap-2">
                <Badge variant="outline">Latest: {latestVersion}</Badge>
                <Badge variant="outline" className="bg-green-50">
                  Stable: {stableVersion}
                </Badge>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowDeprecated(!showDeprecated)}
                >
                  {showDeprecated ? "Hide" : "Show"} Deprecated
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowPrerelease(!showPrerelease)}
                >
                  {showPrerelease ? "Hide" : "Show"} Pre-release
                </Button>
              </div>
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              </div>
            ) : versions.length === 0 ? (
              <div className="text-center py-12">
                <Package className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-medium mb-2">No versions found</h3>
                <p className="text-gray-600 mb-4">Create your first dataset version</p>
                <Button onClick={() => setActiveTab("create")}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Version
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {versions.map((version) => (
                  <Card
                    key={version.id}
                    className="cursor-pointer hover:border-blue-500 transition-colors"
                    onClick={() => loadVersionDetails(version.version)}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-lg flex items-center gap-2">
                            v{version.version}
                            <Badge className={getVersionBadgeColor(version)}>
                              {getVersionLabel(version)}
                            </Badge>
                            {version.version === currentVersion && (
                              <Badge variant="outline" className="bg-blue-50">
                                Current
                              </Badge>
                            )}
                          </CardTitle>
                          <CardDescription className="text-sm mt-1">
                            Released {new Date(version.released_at).toLocaleDateString()}
                          </CardDescription>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDownloadVersion(version.version);
                          }}
                        >
                          <Download className="h-3 w-3 mr-1" />
                          Download
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                        {version.changelog}
                      </p>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <p className="text-gray-500">Files</p>
                          <p className="font-medium">{version.stats.total_files.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Size</p>
                          <p className="font-medium">
                            {(version.stats.total_size_mb / 1024).toFixed(2)} GB
                          </p>
                        </div>
                        <div>
                          <p className="text-gray-500">Downloads</p>
                          <p className="font-medium">{version.download_count}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Create Version Tab */}
          <TabsContent value="create" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Create New Version</CardTitle>
                <CardDescription>
                  Create a new semantic version with changelog and statistics
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="version">Version Number *</Label>
                  <div className="flex gap-2 mt-1">
                    <Input
                      id="version"
                      value={newVersion.version}
                      onChange={(e) => setNewVersion({ ...newVersion, version: e.target.value })}
                      placeholder="1.0.0"
                      pattern="^\d+\.\d+\.\d+$"
                    />
                    <Button
                      variant="outline"
                      onClick={() => handleSuggestVersion('patch')}
                    >
                      Patch
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleSuggestVersion('minor')}
                    >
                      Minor
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleSuggestVersion('major')}
                    >
                      Major
                    </Button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Latest version: {latestVersion} | Format: MAJOR.MINOR.PATCH
                  </p>
                </div>

                <div>
                  <Label htmlFor="storage_path">Storage Path *</Label>
                  <Input
                    id="storage_path"
                    value={newVersion.storage_path}
                    onChange={(e) => setNewVersion({ ...newVersion, storage_path: e.target.value })}
                    placeholder="/datasets/dataset-name/v1.0.0"
                  />
                </div>

                <div>
                  <Label htmlFor="changelog">Changelog *</Label>
                  <Textarea
                    id="changelog"
                    value={newVersion.changelog}
                    onChange={(e) => setNewVersion({ ...newVersion, changelog: e.target.value })}
                    placeholder="Describe what changed in this version..."
                    rows={4}
                    minLength={10}
                  />
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="total_files">Total Files</Label>
                    <Input
                      id="total_files"
                      type="number"
                      value={newVersion.total_files}
                      onChange={(e) =>
                        setNewVersion({ ...newVersion, total_files: parseInt(e.target.value) || 0 })
                      }
                    />
                  </div>
                  <div>
                    <Label htmlFor="total_size_mb">Size (MB)</Label>
                    <Input
                      id="total_size_mb"
                      type="number"
                      step="0.01"
                      value={newVersion.total_size_mb}
                      onChange={(e) =>
                        setNewVersion({ ...newVersion, total_size_mb: parseFloat(e.target.value) || 0 })
                      }
                    />
                  </div>
                  <div>
                    <Label htmlFor="total_duration_hours">Duration (hours)</Label>
                    <Input
                      id="total_duration_hours"
                      type="number"
                      step="0.1"
                      value={newVersion.total_duration_hours}
                      onChange={(e) =>
                        setNewVersion({
                          ...newVersion,
                          total_duration_hours: parseFloat(e.target.value) || 0,
                        })
                      }
                    />
                  </div>
                </div>

                <div className="flex gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newVersion.is_stable}
                      onChange={(e) =>
                        setNewVersion({ ...newVersion, is_stable: e.target.checked })
                      }
                      className="rounded"
                    />
                    <span className="text-sm">Mark as Stable</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newVersion.is_prerelease}
                      onChange={(e) =>
                        setNewVersion({ ...newVersion, is_prerelease: e.target.checked })
                      }
                      className="rounded"
                    />
                    <span className="text-sm">Pre-release</span>
                  </label>
                </div>

                <div className="flex justify-end gap-2 pt-4">
                  <Button variant="outline" onClick={() => setActiveTab("list")}>
                    Cancel
                  </Button>
                  <Button
                    onClick={handleCreateVersion}
                    disabled={
                      !newVersion.version ||
                      !newVersion.storage_path ||
                      !newVersion.changelog ||
                      newVersion.changelog.length < 10
                    }
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Create Version
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Compare Versions Tab */}
          <TabsContent value="compare" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Compare Versions</CardTitle>
                <CardDescription>
                  Compare two versions to see differences and improvements
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Version A</Label>
                    <Select value={compareVersionA} onValueChange={setCompareVersionA}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select version" />
                      </SelectTrigger>
                      <SelectContent>
                        {versions.map((v) => (
                          <SelectItem key={v.version} value={v.version}>
                            v{v.version}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Version B</Label>
                    <Select value={compareVersionB} onValueChange={setCompareVersionB}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select version" />
                      </SelectTrigger>
                      <SelectContent>
                        {versions.map((v) => (
                          <SelectItem key={v.version} value={v.version}>
                            v{v.version}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <Button onClick={handleCompareVersions} disabled={isComparing} className="w-full">
                  {isComparing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Comparing...
                    </>
                  ) : (
                    <>
                      <GitCompare className="h-4 w-4 mr-2" />
                      Compare Versions
                    </>
                  )}
                </Button>

                {comparisonResult && (
                  <div className="space-y-4 mt-6">
                    <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
                      <div>
                        <p className="font-medium">Recommendation</p>
                        <p className="text-sm text-gray-600 capitalize">
                          {comparisonResult.recommendation}
                        </p>
                      </div>
                      {comparisonResult.recommendation === "upgrade" && (
                        <ChevronRight className="h-6 w-6 text-blue-600" />
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-base">v{comparisonResult.version_a}</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Files:</span>
                            <span className="font-medium">
                              {comparisonResult.stats_comparison.total_files.version_a.toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Size:</span>
                            <span className="font-medium">
                              {(comparisonResult.stats_comparison.total_size_mb.version_a / 1024).toFixed(
                                2
                              )}{" "}
                              GB
                            </span>
                          </div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-base">v{comparisonResult.version_b}</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Files:</span>
                            <span className="font-medium">
                              {comparisonResult.stats_comparison.total_files.version_b.toLocaleString()}
                              <span className="text-green-600 ml-1">
                                (+{comparisonResult.stats_comparison.total_files.change.toLocaleString()})
                              </span>
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Size:</span>
                            <span className="font-medium">
                              {(comparisonResult.stats_comparison.total_size_mb.version_b / 1024).toFixed(
                                2
                              )}{" "}
                              GB
                              <span className="text-green-600 ml-1">
                                (+{(comparisonResult.stats_comparison.total_size_mb.change / 1024).toFixed(2)} GB)
                              </span>
                            </span>
                          </div>
                        </CardContent>
                      </Card>
                    </div>

                    {comparisonResult.diff && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">Changes</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div className="text-center">
                              <p className="text-green-600 text-2xl font-bold">
                                +{comparisonResult.diff.files_added}
                              </p>
                              <p className="text-gray-600">Added</p>
                            </div>
                            <div className="text-center">
                              <p className="text-blue-600 text-2xl font-bold">
                                {comparisonResult.diff.files_modified}
                              </p>
                              <p className="text-gray-600">Modified</p>
                            </div>
                            <div className="text-center">
                              <p className="text-red-600 text-2xl font-bold">
                                -{comparisonResult.diff.files_removed}
                              </p>
                              <p className="text-gray-600">Removed</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Version Details Tab */}
          <TabsContent value="details" className="space-y-4">
            {selectedVersion && (
              <>
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-2xl font-bold flex items-center gap-2">
                      v{selectedVersion.version}
                      <Badge className={getVersionBadgeColor(selectedVersion)}>
                        {getVersionLabel(selectedVersion)}
                      </Badge>
                    </h3>
                    <p className="text-sm text-gray-600">
                      Released {new Date(selectedVersion.released_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Button onClick={() => handleDownloadVersion(selectedVersion.version)}>
                    <Download className="h-4 w-4 mr-2" />
                    Download
                  </Button>
                </div>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      Changelog
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-700 whitespace-pre-wrap">{selectedVersion.changelog}</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="h-5 w-5" />
                      Statistics
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-6">
                      <div>
                        <p className="text-sm text-gray-600">Total Files</p>
                        <p className="text-2xl font-bold">
                          {selectedVersion.stats.total_files.toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Total Size</p>
                        <p className="text-2xl font-bold">
                          {(selectedVersion.stats.total_size_mb / 1024).toFixed(2)} GB
                        </p>
                      </div>
                      {selectedVersion.stats.total_duration_hours && (
                        <div>
                          <p className="text-sm text-gray-600">Duration</p>
                          <p className="text-2xl font-bold">
                            {selectedVersion.stats.total_duration_hours.toFixed(1)} hrs
                          </p>
                        </div>
                      )}
                      <div>
                        <p className="text-sm text-gray-600">Downloads</p>
                        <p className="text-2xl font-bold">{selectedVersion.download_count}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {selectedVersion.quality_report && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <CheckCircle2 className="h-5 w-5" />
                        Quality Report
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {selectedVersion.quality_report.transcription_accuracy && (
                          <div>
                            <div className="flex justify-between mb-1">
                              <span className="text-sm">Transcription Accuracy</span>
                              <span className="text-sm font-medium">
                                {(selectedVersion.quality_report.transcription_accuracy * 100).toFixed(1)}%
                              </span>
                            </div>
                            <Progress
                              value={selectedVersion.quality_report.transcription_accuracy * 100}
                            />
                          </div>
                        )}
                        {selectedVersion.quality_report.audio_quality_score && (
                          <div>
                            <div className="flex justify-between mb-1">
                              <span className="text-sm">Audio Quality</span>
                              <span className="text-sm font-medium">
                                {(selectedVersion.quality_report.audio_quality_score * 100).toFixed(1)}%
                              </span>
                            </div>
                            <Progress
                              value={selectedVersion.quality_report.audio_quality_score * 100}
                            />
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {selectedVersion.diff_summary && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <GitCompare className="h-5 w-5" />
                        Changes from Previous Version
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-green-600 text-xl font-bold">
                            +{selectedVersion.diff_summary.files_added}
                          </p>
                          <p className="text-gray-600">Files Added</p>
                        </div>
                        <div>
                          <p className="text-blue-600 text-xl font-bold">
                            {selectedVersion.diff_summary.files_modified}
                          </p>
                          <p className="text-gray-600">Files Modified</p>
                        </div>
                        <div>
                          <p className="text-red-600 text-xl font-bold">
                            -{selectedVersion.diff_summary.files_removed}
                          </p>
                          <p className="text-gray-600">Files Removed</p>
                        </div>
                        <div>
                          <p className="text-purple-600 text-xl font-bold">
                            {selectedVersion.diff_summary.size_change_mb > 0 ? "+" : ""}
                            {(selectedVersion.diff_summary.size_change_mb / 1024).toFixed(2)} GB
                          </p>
                          <p className="text-gray-600">Size Change</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Info className="h-5 w-5" />
                      Technical Details
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Checksum (SHA256):</span>
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {selectedVersion.checksum.substring(0, 16)}...
                      </code>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Dataset ID:</span>
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {selectedVersion.dataset_id}
                      </code>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};

export default DatasetVersionsModal;
