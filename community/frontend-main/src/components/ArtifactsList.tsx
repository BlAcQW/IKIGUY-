import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import {
  Download,
  Trash2,
  FileIcon,
  Search,
  Loader2,
  AlertCircle,
  Filter,
} from "lucide-react";
import { format } from "date-fns";

interface Artifact {
  id: string;
  name: string;
  description?: string;
  type: string;
  version?: string;
  file_size: number;
  file_name: string;
  uploaded_by: string;
  uploaded_at: string;
  download_count?: number;
}

interface ArtifactsListProps {
  pipelineId: string;
  currentUserId?: string;
  onRefresh?: () => void;
}

const ARTIFACT_TYPE_LABELS: Record<string, string> = {
  model_weights: "Model Weights",
  training_logs: "Training Logs",
  metrics: "Metrics/Results",
  visualizations: "Visualizations",
  configuration: "Configuration",
  other: "Other",
};

const ARTIFACT_TYPE_COLORS: Record<string, string> = {
  model_weights: "bg-purple-100 text-purple-800",
  training_logs: "bg-blue-100 text-blue-800",
  metrics: "bg-green-100 text-green-800",
  visualizations: "bg-orange-100 text-orange-800",
  configuration: "bg-yellow-100 text-yellow-800",
  other: "bg-gray-100 text-gray-800",
};

export function ArtifactsList({
  pipelineId,
  currentUserId,
  onRefresh,
}: ArtifactsListProps) {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [filteredArtifacts, setFilteredArtifacts] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("date_desc");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    loadArtifacts();
  }, [pipelineId]);

  useEffect(() => {
    applyFiltersAndSort();
  }, [artifacts, searchQuery, typeFilter, sortBy]);

  const loadArtifacts = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getPipelineArtifacts(pipelineId);
      setArtifacts(Array.isArray(data) ? data : data?.items || []);
    } catch (error: any) {
      console.error("Failed to load artifacts:", error);
      toast({
        title: "Failed to Load Artifacts",
        description: error.message || "An error occurred while loading artifacts.",
        variant: "destructive",
      });
      setArtifacts([]);
    } finally {
      setLoading(false);
    }
  };

  const applyFiltersAndSort = () => {
    let filtered = [...artifacts];

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (artifact) =>
          artifact.name.toLowerCase().includes(query) ||
          artifact.description?.toLowerCase().includes(query) ||
          artifact.file_name.toLowerCase().includes(query)
      );
    }

    // Apply type filter
    if (typeFilter !== "all") {
      filtered = filtered.filter((artifact) => artifact.type === typeFilter);
    }

    // Apply sorting
    switch (sortBy) {
      case "date_desc":
        filtered.sort(
          (a, b) =>
            new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime()
        );
        break;
      case "date_asc":
        filtered.sort(
          (a, b) =>
            new Date(a.uploaded_at).getTime() - new Date(b.uploaded_at).getTime()
        );
        break;
      case "name_asc":
        filtered.sort((a, b) => a.name.localeCompare(b.name));
        break;
      case "name_desc":
        filtered.sort((a, b) => b.name.localeCompare(a.name));
        break;
      case "size_desc":
        filtered.sort((a, b) => b.file_size - a.file_size);
        break;
      case "size_asc":
        filtered.sort((a, b) => a.file_size - b.file_size);
        break;
    }

    setFilteredArtifacts(filtered);
  };

  const handleDownload = async (artifact: Artifact) => {
    try {
      setDownloadingId(artifact.id);
      const blob = await apiClient.downloadPipelineArtifact(
        pipelineId,
        artifact.id
      );

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = artifact.file_name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: "Download Started",
        description: `Downloading ${artifact.name}...`,
      });
    } catch (error: any) {
      console.error("Failed to download artifact:", error);
      toast({
        title: "Download Failed",
        description: error.message || "Failed to download the artifact.",
        variant: "destructive",
      });
    } finally {
      setDownloadingId(null);
    }
  };

  const handleDelete = async (artifact: Artifact) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${artifact.name}"? This action cannot be undone.`
    );

    if (!confirmed) return;

    try {
      setDeletingId(artifact.id);
      await apiClient.deletePipelineArtifact(pipelineId, artifact.id);

      toast({
        title: "Artifact Deleted",
        description: `${artifact.name} has been deleted successfully.`,
      });

      // Refresh artifacts list
      await loadArtifacts();
      if (onRefresh) onRefresh();
    } catch (error: any) {
      console.error("Failed to delete artifact:", error);
      toast({
        title: "Delete Failed",
        description: error.message || "Failed to delete the artifact.",
        variant: "destructive",
      });
    } finally {
      setDeletingId(null);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  const canDelete = (artifact: Artifact): boolean => {
    // Allow deletion if current user is the uploader
    // In production, also check for admin permissions
    return currentUserId === artifact.uploaded_by;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters and Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search artifacts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Type Filter */}
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger>
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {Object.entries(ARTIFACT_TYPE_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Sort */}
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger>
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="date_desc">Newest First</SelectItem>
                <SelectItem value="date_asc">Oldest First</SelectItem>
                <SelectItem value="name_asc">Name (A-Z)</SelectItem>
                <SelectItem value="name_desc">Name (Z-A)</SelectItem>
                <SelectItem value="size_desc">Largest First</SelectItem>
                <SelectItem value="size_asc">Smallest First</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Artifacts Count */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600">
          {filteredArtifacts.length} artifact{filteredArtifacts.length !== 1 ? "s" : ""}{" "}
          {searchQuery || typeFilter !== "all" ? "found" : "total"}
        </p>
      </div>

      {/* Artifacts List */}
      {filteredArtifacts.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-600 mb-2">
                {artifacts.length === 0
                  ? "No artifacts uploaded yet"
                  : "No artifacts match your filters"}
              </p>
              <p className="text-sm text-gray-500">
                {artifacts.length === 0
                  ? "Upload model files, logs, or visualizations to get started."
                  : "Try adjusting your search or filter criteria."}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredArtifacts.map((artifact) => (
            <Card key={artifact.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  {/* Artifact Info */}
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <FileIcon className="h-10 w-10 text-gray-400 flex-shrink-0 mt-1" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start gap-2 mb-2">
                        <h3 className="font-medium text-lg truncate">
                          {artifact.name}
                        </h3>
                        <Badge
                          className={
                            ARTIFACT_TYPE_COLORS[artifact.type] ||
                            ARTIFACT_TYPE_COLORS.other
                          }
                        >
                          {ARTIFACT_TYPE_LABELS[artifact.type] || "Other"}
                        </Badge>
                        {artifact.version && (
                          <Badge variant="outline">{artifact.version}</Badge>
                        )}
                      </div>

                      {artifact.description && (
                        <p className="text-sm text-gray-600 mb-2">
                          {artifact.description}
                        </p>
                      )}

                      <div className="flex flex-wrap gap-4 text-xs text-gray-500">
                        <span>File: {artifact.file_name}</span>
                        <span>Size: {formatFileSize(artifact.file_size)}</span>
                        <span>
                          Uploaded:{" "}
                          {format(new Date(artifact.uploaded_at), "MMM d, yyyy")}
                        </span>
                        {artifact.download_count !== undefined && (
                          <span>Downloads: {artifact.download_count}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 flex-shrink-0">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDownload(artifact)}
                      disabled={downloadingId === artifact.id}
                    >
                      {downloadingId === artifact.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <>
                          <Download className="h-4 w-4 mr-1" />
                          Download
                        </>
                      )}
                    </Button>

                    {canDelete(artifact) && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDelete(artifact)}
                        disabled={deletingId === artifact.id}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        {deletingId === artifact.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
