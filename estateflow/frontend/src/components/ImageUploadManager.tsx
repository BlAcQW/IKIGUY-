/**
 * Image Upload Manager Component
 *
 * Comprehensive image upload component with:
 * - Drag & drop
 * - Multiple file selection
 * - Preview thumbnails
 * - Progress indicators
 * - Image ordering (drag to reorder)
 * - Featured image selection
 * - Delete functionality
 */

import { useState, useCallback, useRef } from "react";
import { Upload, X, Star, GripVertical, Loader2, ImagePlus, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { uploadImage, validateImageFile, getFileUrl, UploadResponse } from "@/lib/api/upload-api";
import { useToast } from "@/hooks/use-toast";

export interface UploadedImage extends UploadResponse {
  preview?: string;
}

interface ImageUploadManagerProps {
  images: UploadedImage[];
  onChange: (images: UploadedImage[]) => void;
  maxImages?: number;
  featuredIndex?: number;
  onFeaturedChange?: (index: number) => void;
}

interface UploadingFile {
  file: File;
  preview: string;
  progress: number;
  error?: string;
}

export function ImageUploadManager({
  images,
  onChange,
  maxImages = 20,
  featuredIndex = 0,
  onFeaturedChange,
}: ImageUploadManagerProps) {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const handleFileSelect = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;

      const remainingSlots = maxImages - images.length - uploadingFiles.length;
      if (remainingSlots <= 0) {
        toast({
          title: "Maximum images reached",
          description: `You can upload up to ${maxImages} images per property.`,
          variant: "destructive",
        });
        return;
      }

      const filesToUpload = Array.from(files).slice(0, remainingSlots);
      const newUploadingFiles: UploadingFile[] = [];

      for (const file of filesToUpload) {
        const validation = validateImageFile(file);
        if (!validation.valid) {
          toast({
            title: "Invalid file",
            description: validation.error,
            variant: "destructive",
          });
          continue;
        }

        // Create preview
        const preview = URL.createObjectURL(file);
        newUploadingFiles.push({
          file,
          preview,
          progress: 0,
        });
      }

      if (newUploadingFiles.length === 0) return;

      setUploadingFiles((prev) => [...prev, ...newUploadingFiles]);

      // Upload files
      for (let i = 0; i < newUploadingFiles.length; i++) {
        const uploadFile = newUploadingFiles[i];

        try {
          const response = await uploadImage(uploadFile.file, (progress) => {
            setUploadingFiles((prev) =>
              prev.map((f, idx) =>
                f.file === uploadFile.file ? { ...f, progress: progress.percentage } : f
              )
            );
          });

          // Add to images list
          const uploadedImage: UploadedImage = {
            ...response,
            preview: uploadFile.preview,
          };

          onChange([...images, uploadedImage]);

          // Remove from uploading
          setUploadingFiles((prev) => prev.filter((f) => f.file !== uploadFile.file));
        } catch (error) {
          // Mark as error
          setUploadingFiles((prev) =>
            prev.map((f) =>
              f.file === uploadFile.file
                ? { ...f, error: error instanceof Error ? error.message : "Upload failed" }
                : f
            )
          );

          toast({
            title: "Upload failed",
            description: error instanceof Error ? error.message : "Failed to upload image",
            variant: "destructive",
          });
        }
      }
    },
    [images, uploadingFiles, maxImages, onChange, toast]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      handleFileSelect(e.dataTransfer.files);
    },
    [handleFileSelect]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDelete = useCallback(
    (index: number) => {
      const newImages = images.filter((_, i) => i !== index);
      onChange(newImages);

      // Adjust featured index if needed
      if (onFeaturedChange) {
        if (featuredIndex === index) {
          onFeaturedChange(0); // Reset to first image
        } else if (featuredIndex > index) {
          onFeaturedChange(featuredIndex - 1); // Shift down
        }
      }
    },
    [images, onChange, featuredIndex, onFeaturedChange]
  );

  const handleSetFeatured = useCallback(
    (index: number) => {
      if (onFeaturedChange) {
        onFeaturedChange(index);
      }
    },
    [onFeaturedChange]
  );

  const handleDragStart = useCallback((index: number) => {
    setDraggedIndex(index);
  }, []);

  const handleDragEnd = useCallback(() => {
    setDraggedIndex(null);
  }, []);

  const handleDragOverImage = useCallback(
    (e: React.DragEvent, targetIndex: number) => {
      e.preventDefault();

      if (draggedIndex === null || draggedIndex === targetIndex) return;

      const newImages = [...images];
      const draggedImage = newImages[draggedIndex];
      newImages.splice(draggedIndex, 1);
      newImages.splice(targetIndex, 0, draggedImage);

      onChange(newImages);

      // Adjust featured index
      if (onFeaturedChange) {
        if (featuredIndex === draggedIndex) {
          onFeaturedChange(targetIndex);
        } else if (featuredIndex === targetIndex) {
          onFeaturedChange(draggedIndex < targetIndex ? targetIndex - 1 : targetIndex + 1);
        }
      }

      setDraggedIndex(targetIndex);
    },
    [draggedIndex, images, onChange, featuredIndex, onFeaturedChange]
  );

  const handleRetry = useCallback(
    (uploadFile: UploadingFile) => {
      setUploadingFiles((prev) =>
        prev.map((f) => (f.file === uploadFile.file ? { ...f, error: undefined, progress: 0 } : f))
      );

      uploadImage(uploadFile.file, (progress) => {
        setUploadingFiles((prev) =>
          prev.map((f) =>
            f.file === uploadFile.file ? { ...f, progress: progress.percentage } : f
          )
        );
      })
        .then((response) => {
          const uploadedImage: UploadedImage = {
            ...response,
            preview: uploadFile.preview,
          };
          onChange([...images, uploadedImage]);
          setUploadingFiles((prev) => prev.filter((f) => f.file !== uploadFile.file));
        })
        .catch((error) => {
          setUploadingFiles((prev) =>
            prev.map((f) =>
              f.file === uploadFile.file
                ? { ...f, error: error instanceof Error ? error.message : "Upload failed" }
                : f
            )
          );
        });
    },
    [images, onChange]
  );

  const handleCancelUpload = useCallback((uploadFile: UploadingFile) => {
    setUploadingFiles((prev) => prev.filter((f) => f.file !== uploadFile.file));
    URL.revokeObjectURL(uploadFile.preview);
  }, []);

  return (
    <div className="space-y-4">
      {/* Upload Area */}
      <Card
        className={cn(
          "border-2 border-dashed transition-colors",
          dragOver ? "border-primary bg-primary/5" : "border-border"
        )}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <CardContent className="p-8 text-center">
          <div className="flex flex-col items-center gap-4">
            <div
              className={cn(
                "p-4 rounded-full transition-colors",
                dragOver ? "bg-primary/20" : "bg-muted"
              )}
            >
              {dragOver ? (
                <ImagePlus className="h-8 w-8 text-primary" />
              ) : (
                <Upload className="h-8 w-8 text-muted-foreground" />
              )}
            </div>
            <div>
              <p className="text-sm font-medium mb-1">
                {dragOver ? "Drop images here" : "Drag & drop images or click to browse"}
              </p>
              <p className="text-xs text-muted-foreground">
                JPEG, PNG, GIF, WebP • Max 10 MB per image • Up to {maxImages} images
              </p>
            </div>
            <Button
              type="button"
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              disabled={images.length + uploadingFiles.length >= maxImages}
            >
              <Upload className="h-4 w-4 mr-2" />
              Choose Files
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/gif,image/webp"
              multiple
              className="hidden"
              onChange={(e) => handleFileSelect(e.target.files)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Image Grid */}
      {(images.length > 0 || uploadingFiles.length > 0) && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {/* Uploaded Images */}
          {images.map((image, index) => (
            <div
              key={image.file_id}
              draggable
              onDragStart={() => handleDragStart(index)}
              onDragEnd={handleDragEnd}
              onDragOver={(e) => handleDragOverImage(e, index)}
              className={cn(
                "relative group rounded-lg overflow-hidden border-2 transition-all cursor-move",
                draggedIndex === index ? "opacity-50 scale-95" : "",
                featuredIndex === index ? "border-primary ring-2 ring-primary/20" : "border-border"
              )}
            >
              <div className="aspect-square bg-muted">
                <img
                  src={image.preview || getFileUrl(image.path)}
                  alt={image.filename}
                  className="w-full h-full object-cover"
                />
              </div>

              {/* Overlay Actions */}
              <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="text-white hover:bg-white/20"
                  onClick={() => handleSetFeatured(index)}
                  title="Set as featured"
                >
                  <Star
                    className={cn("h-5 w-5", featuredIndex === index && "fill-yellow-400")}
                  />
                </Button>
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="text-white hover:bg-white/20"
                  onClick={() => handleDelete(index)}
                  title="Delete"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>

              {/* Featured Badge */}
              {featuredIndex === index && (
                <Badge className="absolute top-2 left-2 bg-yellow-500 text-white">
                  <Star className="h-3 w-3 mr-1 fill-white" />
                  Featured
                </Badge>
              )}

              {/* Drag Handle */}
              <div className="absolute top-2 right-2 bg-black/40 rounded p-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <GripVertical className="h-4 w-4 text-white" />
              </div>

              {/* Image Number */}
              <Badge variant="secondary" className="absolute bottom-2 left-2">
                {index + 1}
              </Badge>
            </div>
          ))}

          {/* Uploading Files */}
          {uploadingFiles.map((uploadFile, index) => (
            <div
              key={index}
              className="relative rounded-lg overflow-hidden border-2 border-border"
            >
              <div className="aspect-square bg-muted">
                <img
                  src={uploadFile.preview}
                  alt="Uploading..."
                  className="w-full h-full object-cover"
                />
              </div>

              {/* Upload Progress/Error */}
              <div className="absolute inset-0 bg-black/70 flex flex-col items-center justify-center gap-2 p-4">
                {uploadFile.error ? (
                  <>
                    <AlertCircle className="h-8 w-8 text-destructive" />
                    <p className="text-xs text-white text-center">{uploadFile.error}</p>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        className="text-xs"
                        onClick={() => handleRetry(uploadFile)}
                      >
                        Retry
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="ghost"
                        className="text-xs"
                        onClick={() => handleCancelUpload(uploadFile)}
                      >
                        Cancel
                      </Button>
                    </div>
                  </>
                ) : (
                  <>
                    <Loader2 className="h-6 w-6 text-white animate-spin" />
                    <div className="w-full">
                      <Progress value={uploadFile.progress} className="h-1" />
                    </div>
                    <p className="text-xs text-white">{uploadFile.progress}%</p>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info */}
      {images.length > 0 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            {images.length} / {maxImages} images uploaded
          </span>
          <span>Drag images to reorder • First image is cover</span>
        </div>
      )}
    </div>
  );
}
