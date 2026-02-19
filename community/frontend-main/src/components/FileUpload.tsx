import React, { useCallback, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Upload, File, X, FileText, Music, Video } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  selectedFile?: File | null;
  onFileRemove: () => void;
  uploadProgress?: number;
  acceptedTypes?: string[];
  maxSizeBytes?: number;
  disabled?: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  selectedFile,
  onFileRemove,
  uploadProgress = 0,
  acceptedTypes = ['.txt', '.pdf', '.mp3', '.wav', '.m4a', '.ogg', '.webm', '.csv', '.json'],
  maxSizeBytes = 100 * 1024 * 1024, // 100MB
  disabled = false
}) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > maxSizeBytes) {
      return `File size must be less than ${Math.round(maxSizeBytes / 1024 / 1024)}MB`;
    }

    // Check file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    const mimeTypeAllowed = [
      'text/plain', 'application/pdf', 'audio/mp3', 'audio/wav',
      'audio/mpeg', 'audio/x-wav', 'text/csv', 'application/json',
      'audio/mp4', 'audio/ogg', 'audio/webm', 'audio/m4a'
    ];

    if (!acceptedTypes.includes(fileExtension) && !mimeTypeAllowed.includes(file.type)) {
      return `Please select a valid file type: ${acceptedTypes.join(', ')}`;
    }

    return null;
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const error = validateFile(file);
      if (error) {
        alert(error);
        return;
      }
      onFileSelect(file);
    }
  };

  const handleDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setIsDragOver(false);

      if (disabled) return;

      const file = event.dataTransfer.files[0];
      if (file) {
        const error = validateFile(file);
        if (error) {
          alert(error);
          return;
        }
        onFileSelect(file);
      }
    },
    [onFileSelect, disabled, maxSizeBytes, acceptedTypes]
  );

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (!disabled) {
      setIsDragOver(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
  }, []);

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();

    if (['mp3', 'wav', 'm4a', 'ogg', 'webm'].includes(extension || '')) {
      return <Music className="h-8 w-8 text-purple-500" />;
    }
    if (['mp4', 'avi', 'mov'].includes(extension || '')) {
      return <Video className="h-8 w-8 text-blue-500" />;
    }
    if (['txt', 'csv', 'json'].includes(extension || '')) {
      return <FileText className="h-8 w-8 text-green-500" />;
    }
    return <File className="h-8 w-8 text-gray-500" />;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (selectedFile) {
    return (
      <div className="border border-border rounded-lg p-4 bg-card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getFileIcon(selectedFile.name)}
            <div>
              <p className="text-sm font-medium">{selectedFile.name}</p>
              <p className="text-xs text-muted-foreground">
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onFileRemove}
            disabled={disabled}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {uploadProgress > 0 && uploadProgress < 100 && (
          <div className="mt-3">
            <div className="flex justify-between text-xs text-muted-foreground mb-1">
              <span>Uploading...</span>
              <span>{uploadProgress}%</span>
            </div>
            <Progress value={uploadProgress} className="h-2" />
          </div>
        )}

        {uploadProgress === 100 && (
          <div className="mt-3 text-xs text-green-600 flex items-center gap-1">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            Upload complete
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      className={`
        border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
        ${isDragOver ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={() => {
        if (!disabled) {
          document.getElementById('file-upload-input')?.click();
        }
      }}
    >
      <input
        id="file-upload-input"
        type="file"
        accept={acceptedTypes.join(',')}
        onChange={handleFileChange}
        className="hidden"
        disabled={disabled}
      />

      <Upload className={`h-12 w-12 mx-auto mb-4 ${isDragOver ? 'text-primary' : 'text-muted-foreground'}`} />

      <h3 className="text-lg font-semibold mb-2">
        {isDragOver ? 'Drop your file here' : 'Upload a file'}
      </h3>

      <p className="text-sm text-muted-foreground mb-4">
        Drag and drop your file here, or click to browse
      </p>

      <div className="text-xs text-muted-foreground space-y-1">
        <p>Supported formats: {acceptedTypes.join(', ')}</p>
        <p>Maximum size: {Math.round(maxSizeBytes / 1024 / 1024)}MB</p>
      </div>

      <Button type="button" variant="outline" size="sm" className="mt-4" disabled={disabled}>
        Choose File
      </Button>
    </div>
  );
};

export default FileUpload;