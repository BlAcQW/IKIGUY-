/**
 * WhatsApp Media Uploader Component
 *
 * Handles media file uploads for WhatsApp campaigns
 * Supports images, videos, audio, and documents with preview
 */

import React, { useState, useRef } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Upload,
  X,
  Image as ImageIcon,
  Video,
  Music,
  FileText,
  AlertCircle,
  CheckCircle2
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface MediaConfig {
  url?: string;
  type?: 'image' | 'video' | 'audio' | 'document';
  caption?: string;
}

interface WhatsAppMediaUploaderProps {
  mediaConfig: MediaConfig;
  onChange: (config: MediaConfig) => void;
}

const MEDIA_TYPES = [
  {
    id: 'image' as const,
    name: 'Image',
    icon: ImageIcon,
    accept: 'image/jpeg,image/png',
    maxSize: 5, // MB
    description: 'JPEG, PNG up to 5MB'
  },
  {
    id: 'video' as const,
    name: 'Video',
    icon: Video,
    accept: 'video/mp4,video/3gpp',
    maxSize: 16, // MB
    description: 'MP4, 3GPP up to 16MB'
  },
  {
    id: 'audio' as const,
    name: 'Audio',
    icon: Music,
    accept: 'audio/aac,audio/mp4,audio/mpeg,audio/amr,audio/ogg',
    maxSize: 16, // MB
    description: 'AAC, M4A, MP3, AMR, OGG up to 16MB'
  },
  {
    id: 'document' as const,
    name: 'Document',
    icon: FileText,
    accept: 'application/pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx',
    maxSize: 100, // MB
    description: 'PDF, DOC, XLS, PPT up to 100MB'
  }
];

export const WhatsAppMediaUploader: React.FC<WhatsAppMediaUploaderProps> = ({
  mediaConfig,
  onChange
}) => {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(
    mediaConfig.url || null
  );

  const selectedMediaType = MEDIA_TYPES.find(t => t.id === mediaConfig.type) || MEDIA_TYPES[0];

  const handleMediaTypeChange = (type: 'image' | 'video' | 'audio' | 'document') => {
    // Reset media when type changes
    onChange({
      type,
      url: undefined,
      caption: mediaConfig.caption
    });
    setPreviewUrl(null);
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file size
    const maxSizeBytes = selectedMediaType.maxSize * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      toast({
        title: "File too large",
        description: `Maximum file size is ${selectedMediaType.maxSize}MB`,
        variant: "destructive"
      });
      return;
    }

    // Validate file type
    const fileType = file.type;
    const acceptedTypes = selectedMediaType.accept.split(',');
    const isValidType = acceptedTypes.some(type => {
      if (type.startsWith('.')) {
        return file.name.toLowerCase().endsWith(type);
      }
      return fileType === type || fileType.startsWith(type.split('/')[0]);
    });

    if (!isValidType) {
      toast({
        title: "Invalid file type",
        description: selectedMediaType.description,
        variant: "destructive"
      });
      return;
    }

    setUploading(true);

    try {
      // Create preview URL for images and videos
      if (mediaConfig.type === 'image' || mediaConfig.type === 'video') {
        const objectUrl = URL.createObjectURL(file);
        setPreviewUrl(objectUrl);
      }

      // In a real implementation, upload file to your server/storage
      // For now, we'll use a placeholder URL
      const uploadedUrl = await uploadMediaFile(file);

      onChange({
        ...mediaConfig,
        url: uploadedUrl
      });

      toast({
        title: "File uploaded",
        description: "Media file uploaded successfully"
      });
    } catch (error) {
      console.error('Upload error:', error);
      toast({
        title: "Upload failed",
        description: "Failed to upload media file",
        variant: "destructive"
      });
    } finally {
      setUploading(false);
    }
  };

  // Simulated upload function - replace with actual upload logic
  const uploadMediaFile = async (file: File): Promise<string> => {
    // This should upload to your backend/storage and return the URL
    // For now, return a placeholder
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(`https://example.com/media/${file.name}`);
      }, 1500);
    });
  };

  const handleUrlChange = (url: string) => {
    onChange({
      ...mediaConfig,
      url
    });

    // Set preview for images
    if (mediaConfig.type === 'image' || mediaConfig.type === 'video') {
      setPreviewUrl(url);
    }
  };

  const handleCaptionChange = (caption: string) => {
    onChange({
      ...mediaConfig,
      caption
    });
  };

  const handleRemoveMedia = () => {
    onChange({
      type: mediaConfig.type,
      url: undefined,
      caption: mediaConfig.caption
    });
    setPreviewUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const MediaIcon = selectedMediaType.icon;

  return (
    <div className="space-y-4">
      {/* Media Type Selection */}
      <div className="space-y-2">
        <Label>Media Type</Label>
        <Select
          value={mediaConfig.type || 'image'}
          onValueChange={handleMediaTypeChange}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {MEDIA_TYPES.map((type) => {
              const Icon = type.icon;
              return (
                <SelectItem key={type.id} value={type.id}>
                  <div className="flex items-center gap-2">
                    <Icon className="h-4 w-4" />
                    <span>{type.name}</span>
                  </div>
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
        <p className="text-xs text-gray-500">{selectedMediaType.description}</p>
      </div>

      {/* File Upload */}
      <div className="space-y-2">
        <Label>Upload Media</Label>
        <input
          ref={fileInputRef}
          type="file"
          accept={selectedMediaType.accept}
          onChange={handleFileSelect}
          className="hidden"
        />

        {!mediaConfig.url ? (
          <Card
            className="border-2 border-dashed cursor-pointer hover:border-primary transition-colors"
            onClick={() => fileInputRef.current?.click()}
          >
            <CardContent className="flex flex-col items-center justify-center py-8">
              {uploading ? (
                <>
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4"></div>
                  <p className="text-sm text-gray-600">Uploading...</p>
                </>
              ) : (
                <>
                  <MediaIcon className="h-12 w-12 text-gray-400 mb-4" />
                  <p className="text-sm font-medium mb-1">Click to upload {selectedMediaType.name.toLowerCase()}</p>
                  <p className="text-xs text-gray-500">{selectedMediaType.description}</p>
                </>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-start gap-4">
                {/* Preview */}
                {mediaConfig.type === 'image' && previewUrl && (
                  <img
                    src={previewUrl}
                    alt="Preview"
                    className="w-32 h-32 object-cover rounded border"
                  />
                )}
                {mediaConfig.type === 'video' && previewUrl && (
                  <video
                    src={previewUrl}
                    className="w-32 h-32 object-cover rounded border"
                    controls
                  />
                )}
                {(mediaConfig.type === 'audio' || mediaConfig.type === 'document') && (
                  <div className="w-32 h-32 flex items-center justify-center bg-gray-100 rounded border">
                    <MediaIcon className="h-12 w-12 text-gray-400" />
                  </div>
                )}

                {/* Details */}
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      <span className="text-sm font-medium">Media uploaded</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleRemoveMedia}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="text-xs text-gray-600 break-all">{mediaConfig.url}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-3"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Replace
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* OR Divider */}
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">Or</span>
        </div>
      </div>

      {/* URL Input */}
      <div className="space-y-2">
        <Label>Media URL</Label>
        <Input
          placeholder="https://example.com/media/file.jpg"
          value={mediaConfig.url || ''}
          onChange={(e) => handleUrlChange(e.target.value)}
        />
        <p className="text-xs text-gray-500">
          Enter a direct URL to your media file
        </p>
      </div>

      {/* Caption */}
      {(mediaConfig.type === 'image' || mediaConfig.type === 'video' || mediaConfig.type === 'document') && (
        <div className="space-y-2">
          <Label>Caption (Optional)</Label>
          <Textarea
            placeholder="Add a caption for your media..."
            value={mediaConfig.caption || ''}
            onChange={(e) => handleCaptionChange(e.target.value)}
            rows={2}
            maxLength={1024}
          />
          <p className="text-xs text-gray-500 text-right">
            {(mediaConfig.caption || '').length}/1024
          </p>
        </div>
      )}

      {/* Media Guidelines Alert */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription className="text-xs">
          <strong>Important:</strong> Ensure your media complies with WhatsApp policies.
          Media must be hosted on a publicly accessible HTTPS URL or uploaded through WhatsApp Cloud API.
        </AlertDescription>
      </Alert>
    </div>
  );
};
