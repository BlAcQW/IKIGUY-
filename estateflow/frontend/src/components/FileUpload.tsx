import { useState, useRef, ChangeEvent } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Upload, X, FileImage, FileVideo, Loader2 } from "lucide-react";
import { API_BASE_URL } from "@/lib/api-config";
import { useToast } from "@/hooks/use-toast";
import { uploadImageBatch, uploadVideo, getFileUrl, GridFSUploadResponse } from "@/lib/api/upload-api";

interface FileUploadProps {
  accept?: "images" | "videos" | "both";
  multiple?: boolean;
  maxFiles?: number;
  onUploadComplete: (urls: string[]) => void;
  existingFiles?: string[];
}

interface UploadedFile {
  id: string;
  url: string;
  filename: string;
  isUploading: boolean;
  progress: number;
  error?: string;
}

export function FileUpload({
  accept = "images",
  multiple = true,
  maxFiles = 20,
  onUploadComplete,
  existingFiles = [],
}: FileUploadProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const acceptString =
    accept === "images" ? "image/jpeg,image/png,image/gif,image/webp,image/heic,image/heif" :
    accept === "videos" ? "video/mp4,video/quicktime,video/x-msvideo,video/webm" :
    "image/jpeg,image/png,image/gif,image/webp,image/heic,image/heif,video/mp4,video/quicktime,video/x-msvideo,video/webm";

  const handleFileSelect = async (e: ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);

    if (selectedFiles.length === 0) return;

    // Check max files limit
    if (files.length + selectedFiles.length > maxFiles) {
      toast({
        title: "Too many files",
        description: `Maximum ${maxFiles} files allowed`,
        variant: "destructive",
      });
      return;
    }

    // Separate images and videos
    const imageFiles: File[] = [];
    const videoFiles: File[] = [];

    selectedFiles.forEach(file => {
      if (file.type.startsWith("video/")) {
        videoFiles.push(file);
      } else {
        imageFiles.push(file);
      }
    });

    // Create file objects with uploading state
    const newFiles: UploadedFile[] = selectedFiles.map((file, index) => ({
      id: `${Date.now()}_${index}`,
      url: "",
      filename: file.name,
      isUploading: true,
      progress: 0,
    }));

    setFiles((prev) => [...prev, ...newFiles]);

    // Upload images in batch
    if (imageFiles.length > 0) {
      try {
        await uploadImagesBatch(imageFiles, newFiles);
      } catch (error) {
        console.error("Batch upload error:", error);
      }
    }

    // Upload videos sequentially (no batch API for videos)
    if (videoFiles.length > 0) {
      for (let i = 0; i < videoFiles.length; i++) {
        const file = videoFiles[i];
        const fileObj = newFiles.find(f => f.filename === file.name);
        if (fileObj) {
          try {
            await uploadVideoFile(file, fileObj.id);
          } catch (error) {
            console.error("Video upload error:", error);
          }
        }
      }
    }

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const uploadImagesBatch = async (imageFiles: File[], fileObjects: UploadedFile[]) => {
    try {
      // Upload all images in one batch request using GridFS
      const results = await uploadImageBatch(imageFiles);

      // Process results
      const uploadedUrls: string[] = [];

      results.forEach((result, index) => {
        const file = imageFiles[index];
        const fileObj = fileObjects.find(f => f.filename === file.name);

        if (fileObj) {
          // GridFS returns full URLs already (no need for getFileUrl)
          const fileUrl = result.url;
          uploadedUrls.push(fileUrl);

          // Update file object with URL
          setFiles((prev) =>
            prev.map((f) =>
              f.id === fileObj.id
                ? { ...f, url: fileUrl, isUploading: false, progress: 100 }
                : f
            )
          );
        }
      });

      // Notify parent component with all URLs at once
      onUploadComplete(uploadedUrls);

      toast({
        title: "Upload successful",
        description: `${imageFiles.length} image(s) uploaded successfully`,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Batch upload failed";

      // Mark all files as failed
      imageFiles.forEach((file) => {
        const fileObj = fileObjects.find(f => f.filename === file.name);
        if (fileObj) {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === fileObj.id
                ? { ...f, isUploading: false, error: errorMessage }
                : f
            )
          );
        }
      });

      toast({
        title: "Upload failed",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const uploadVideoFile = async (file: File, fileId: string) => {
    try {
      const result = await uploadVideo(file);
      const fileUrl = getFileUrl(result.path);

      // Update file object with URL
      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileId
            ? { ...f, url: fileUrl, isUploading: false, progress: 100 }
            : f
        )
      );

      // Notify parent component
      onUploadComplete([fileUrl]);

      toast({
        title: "Upload successful",
        description: `${file.name} uploaded successfully`,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Upload failed";

      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileId
            ? { ...f, isUploading: false, error: errorMessage }
            : f
        )
      );

      toast({
        title: "Upload failed",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const allFiles = [
    ...existingFiles.map((url, index) => ({
      id: `existing_${index}`,
      url,
      filename: url.split("/").pop() || "File",
      isUploading: false,
      progress: 100,
    })),
    ...files,
  ];

  return (
    <div className="space-y-4">
      <input
        ref={fileInputRef}
        type="file"
        accept={acceptString}
        multiple={multiple}
        onChange={handleFileSelect}
        className="hidden"
      />

      <Button
        type="button"
        onClick={handleClick}
        variant="outline"
        className="w-full"
        disabled={allFiles.length >= maxFiles}
      >
        <Upload className="h-4 w-4 mr-2" />
        {accept === "images" ? "Upload Images" : accept === "videos" ? "Upload Videos" : "Upload Files"}
        {allFiles.length > 0 && ` (${allFiles.length}/${maxFiles})`}
      </Button>

      {allFiles.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {allFiles.map((file) => (
            <Card key={file.id} className="relative overflow-hidden">
              <CardContent className="p-3">
                {file.isUploading ? (
                  <div className="space-y-2">
                    <div className="flex items-center justify-center h-32 bg-muted rounded">
                      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                    <Progress value={file.progress} className="h-1" />
                    <p className="text-xs text-muted-foreground truncate">{file.filename}</p>
                  </div>
                ) : file.error ? (
                  <div className="space-y-2">
                    <div className="flex items-center justify-center h-32 bg-destructive/10 rounded">
                      <X className="h-8 w-8 text-destructive" />
                    </div>
                    <p className="text-xs text-destructive truncate">{file.error}</p>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => removeFile(file.id)}
                      className="w-full"
                    >
                      Remove
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {file.url.includes("video") || accept === "videos" ? (
                      <div className="flex items-center justify-center h-32 bg-muted rounded">
                        <FileVideo className="h-12 w-12 text-muted-foreground" />
                      </div>
                    ) : (
                      <img
                        src={file.url}
                        alt={file.filename}
                        className="w-full h-32 object-cover rounded"
                        loading="lazy"
                      />
                    )}
                    <p className="text-xs text-muted-foreground truncate">{file.filename}</p>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => removeFile(file.id)}
                      className="w-full"
                    >
                      <X className="h-3 w-3 mr-1" />
                      Remove
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
