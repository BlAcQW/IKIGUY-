import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import { Upload, X, FileIcon, Loader2, CheckCircle2, AlertCircle } from "lucide-react";

interface FileWithMetadata {
  file: File;
  name: string;
  description: string;
  type: string;
  version: string;
  uploading: boolean;
  progress: number;
  uploaded: boolean;
  error: string | null;
}

interface ArtifactUploadModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  pipelineId: string;
  onSuccess?: () => void;
}

const ALLOWED_EXTENSIONS = [
  ".pt", ".pth", ".h5", ".onnx", ".pb", ".pkl", // Model files
  ".txt", ".log", // Text/log files
  ".json", ".yaml", ".yml", // Config files
  ".csv", ".tsv", // Data files
  ".png", ".jpg", ".jpeg", ".svg", // Visualizations
];

const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB

const ARTIFACT_TYPES = [
  { value: "model_weights", label: "Model Weights" },
  { value: "training_logs", label: "Training Logs" },
  { value: "metrics", label: "Metrics/Results" },
  { value: "visualizations", label: "Visualizations" },
  { value: "configuration", label: "Configuration" },
  { value: "other", label: "Other" },
];

export function ArtifactUploadModal({
  open,
  onOpenChange,
  pipelineId,
  onSuccess,
}: ArtifactUploadModalProps) {
  const [files, setFiles] = useState<FileWithMetadata[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const { toast } = useToast();

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `File size exceeds 500MB limit`;
    }

    // Check file extension
    const extension = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      return `File type not allowed. Allowed types: ${ALLOWED_EXTENSIONS.join(", ")}`;
    }

    return null;
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    addFiles(droppedFiles);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      addFiles(selectedFiles);
    }
  };

  const addFiles = (newFiles: File[]) => {
    const validFiles: FileWithMetadata[] = [];

    newFiles.forEach((file) => {
      const error = validateFile(file);
      if (error) {
        toast({
          title: "Invalid File",
          description: `${file.name}: ${error}`,
          variant: "destructive",
        });
        return;
      }

      // Auto-detect artifact type based on extension
      const extension = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
      let defaultType = "other";
      if ([".pt", ".pth", ".h5", ".onnx", ".pb", ".pkl"].includes(extension)) {
        defaultType = "model_weights";
      } else if ([".txt", ".log"].includes(extension)) {
        defaultType = "training_logs";
      } else if ([".json", ".yaml", ".yml"].includes(extension)) {
        defaultType = "configuration";
      } else if ([".csv", ".tsv"].includes(extension)) {
        defaultType = "metrics";
      } else if ([".png", ".jpg", ".jpeg", ".svg"].includes(extension)) {
        defaultType = "visualizations";
      }

      validFiles.push({
        file,
        name: file.name,
        description: "",
        type: defaultType,
        version: "",
        uploading: false,
        progress: 0,
        uploaded: false,
        error: null,
      });
    });

    setFiles((prev) => [...prev, ...validFiles]);
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const updateFileMetadata = (
    index: number,
    field: keyof FileWithMetadata,
    value: string
  ) => {
    setFiles((prev) =>
      prev.map((f, i) => (i === index ? { ...f, [field]: value } : f))
    );
  };

  const uploadFile = async (index: number) => {
    const fileData = files[index];

    try {
      // Update to uploading state
      setFiles((prev) =>
        prev.map((f, i) =>
          i === index ? { ...f, uploading: true, progress: 0, error: null } : f
        )
      );

      // Simulate progress (since we can't track actual upload progress easily)
      const progressInterval = setInterval(() => {
        setFiles((prev) =>
          prev.map((f, i) =>
            i === index && f.progress < 90
              ? { ...f, progress: f.progress + 10 }
              : f
          )
        );
      }, 200);

      await apiClient.uploadPipelineArtifact(pipelineId, fileData.file, {
        name: fileData.name,
        description: fileData.description || undefined,
        type: fileData.type,
        version: fileData.version || undefined,
      });

      clearInterval(progressInterval);

      // Update to uploaded state
      setFiles((prev) =>
        prev.map((f, i) =>
          i === index
            ? { ...f, uploading: false, progress: 100, uploaded: true }
            : f
        )
      );

      toast({
        title: "Upload Successful",
        description: `${fileData.name} has been uploaded successfully.`,
      });
    } catch (error: any) {
      // Update to error state
      setFiles((prev) =>
        prev.map((f, i) =>
          i === index
            ? {
                ...f,
                uploading: false,
                error: error.message || "Upload failed",
              }
            : f
        )
      );

      toast({
        title: "Upload Failed",
        description: `Failed to upload ${fileData.name}: ${error.message}`,
        variant: "destructive",
      });
    }
  };

  const handleUploadAll = async () => {
    setUploading(true);

    // Upload files sequentially
    for (let i = 0; i < files.length; i++) {
      if (!files[i].uploaded && !files[i].uploading) {
        await uploadFile(i);
      }
    }

    setUploading(false);

    // Check if all uploads succeeded
    const allUploaded = files.every((f) => f.uploaded);
    if (allUploaded && onSuccess) {
      onSuccess();
      handleClose();
    }
  };

  const handleClose = () => {
    if (!uploading) {
      setFiles([]);
      onOpenChange(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
  };

  const canUpload = files.length > 0 && files.every((f) => f.name.trim()) && !uploading;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Upload Pipeline Artifacts</DialogTitle>
          <DialogDescription>
            Upload model files, logs, metrics, or visualizations for this pipeline.
            Maximum file size: 500MB per file.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Drag and Drop Zone */}
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive
                ? "border-primary bg-primary/5"
                : "border-gray-300 hover:border-gray-400"
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg font-medium mb-2">
              Drag and drop files here, or click to browse
            </p>
            <p className="text-sm text-gray-500 mb-4">
              Supported formats: {ALLOWED_EXTENSIONS.slice(0, 6).join(", ")}, and more
            </p>
            <input
              type="file"
              multiple
              onChange={handleFileInput}
              className="hidden"
              id="file-upload"
              accept={ALLOWED_EXTENSIONS.join(",")}
            />
            <label htmlFor="file-upload">
              <Button variant="outline" asChild>
                <span>Browse Files</span>
              </Button>
            </label>
          </div>

          {/* Files List */}
          {files.length > 0 && (
            <div className="space-y-4">
              <h3 className="font-semibold">Files to Upload ({files.length})</h3>
              {files.map((fileData, index) => (
                <div
                  key={index}
                  className="border rounded-lg p-4 space-y-3 bg-white"
                >
                  {/* File Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      <FileIcon className="h-5 w-5 mt-1 text-gray-500" />
                      <div className="flex-1">
                        <p className="font-medium">{fileData.file.name}</p>
                        <p className="text-sm text-gray-500">
                          {formatFileSize(fileData.file.size)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {fileData.uploaded && (
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                      )}
                      {fileData.error && (
                        <AlertCircle className="h-5 w-5 text-red-600" />
                      )}
                      {!fileData.uploading && !fileData.uploaded && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => removeFile(index)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Metadata Form */}
                  {!fileData.uploaded && (
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <Label htmlFor={`name-${index}`}>Artifact Name *</Label>
                        <Input
                          id={`name-${index}`}
                          value={fileData.name}
                          onChange={(e) =>
                            updateFileMetadata(index, "name", e.target.value)
                          }
                          disabled={fileData.uploading}
                          placeholder="Enter artifact name"
                        />
                      </div>
                      <div>
                        <Label htmlFor={`type-${index}`}>Type *</Label>
                        <Select
                          value={fileData.type}
                          onValueChange={(value) =>
                            updateFileMetadata(index, "type", value)
                          }
                          disabled={fileData.uploading}
                        >
                          <SelectTrigger id={`type-${index}`}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {ARTIFACT_TYPES.map((type) => (
                              <SelectItem key={type.value} value={type.value}>
                                {type.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label htmlFor={`version-${index}`}>Version (optional)</Label>
                        <Input
                          id={`version-${index}`}
                          value={fileData.version}
                          onChange={(e) =>
                            updateFileMetadata(index, "version", e.target.value)
                          }
                          disabled={fileData.uploading}
                          placeholder="e.g., v1.0, 2024-01-15"
                        />
                      </div>
                      <div>
                        <Label htmlFor={`description-${index}`}>
                          Description (optional)
                        </Label>
                        <Input
                          id={`description-${index}`}
                          value={fileData.description}
                          onChange={(e) =>
                            updateFileMetadata(index, "description", e.target.value)
                          }
                          disabled={fileData.uploading}
                          placeholder="Brief description"
                        />
                      </div>
                    </div>
                  )}

                  {/* Upload Progress */}
                  {fileData.uploading && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Uploading...</span>
                        <span className="font-medium">{fileData.progress}%</span>
                      </div>
                      <Progress value={fileData.progress} />
                    </div>
                  )}

                  {/* Error Message */}
                  {fileData.error && (
                    <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                      {fileData.error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button variant="outline" onClick={handleClose} disabled={uploading}>
              Cancel
            </Button>
            <Button onClick={handleUploadAll} disabled={!canUpload}>
              {uploading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Upload {files.length > 0 ? `(${files.length})` : ""}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
