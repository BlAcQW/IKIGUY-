import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link as LinkIcon, Upload, X, Loader2 } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { PropertyCreate } from "@/lib/types/property";
import { FileUpload } from "@/components/FileUpload";
import { useToast } from "@/hooks/use-toast";

interface MediaStepProps {
  formData: Partial<PropertyCreate>;
  updateFormData: (data: Partial<PropertyCreate>) => void;
}

export function MediaStep({ formData, updateFormData }: MediaStepProps) {
  const [uploadMethod, setUploadMethod] = useState<"upload" | "url">("upload");
  const [isValidatingUrl, setIsValidatingUrl] = useState(false);
  const { toast } = useToast();

  const handleImageUpload = (newUrls: string[]) => {
    const currentImages = formData.images || [];
    updateFormData({ images: [...currentImages, ...newUrls] });
  };

  const handleVideoUpload = (newUrls: string[]) => {
    if (newUrls.length > 0) {
      updateFormData({ video_url: newUrls[0] });
    }
  };

  const handleRemoveImage = (indexToRemove: number) => {
    const currentImages = formData.images || [];
    const updatedImages = currentImages.filter((_, index) => index !== indexToRemove);
    updateFormData({ images: updatedImages });
  };

  const validateImageUrl = async (url: string): Promise<boolean> => {
    try {
      // Check URL format
      new URL(url);

      // Attempt to fetch image with HEAD request to verify it exists
      const response = await fetch(url, {
        method: 'HEAD',
        mode: 'no-cors' // Avoid CORS issues, we just check if URL is accessible
      });

      // With no-cors, we can't check response.ok, so we assume success if no error
      return true;
    } catch (error) {
      return false;
    }
  };

  const handleAddImageUrl = async (url: string) => {
    if (!url.trim()) return;

    setIsValidatingUrl(true);

    // Basic validation - check if it looks like an image URL
    const imageExtensions = /\.(jpg|jpeg|png|gif|webp|heic|heif|svg)(\?.*)?$/i;
    if (!imageExtensions.test(url) && !url.includes('images') && !url.includes('photo')) {
      toast({
        title: "Invalid Image URL",
        description: "URL doesn't appear to be an image. Please check the URL.",
        variant: "destructive",
      });
      setIsValidatingUrl(false);
      return;
    }

    // Validate URL
    const isValid = await validateImageUrl(url);

    if (isValid) {
      const currentImages = formData.images || [];
      updateFormData({ images: [...currentImages, url] });
      toast({
        title: "Image Added",
        description: "Image URL added successfully",
      });
    } else {
      toast({
        title: "Invalid URL",
        description: "Unable to access the image URL. Please check the URL.",
        variant: "destructive",
      });
    }

    setIsValidatingUrl(false);
  };

  return (
    <div className="space-y-6 animate-slide-up-fade">
      <Card variant="elevated">
        <CardContent className="p-6">
          <Label className="text-base font-semibold mb-4 block">Property Images</Label>

          <Tabs value={uploadMethod} onValueChange={(v) => setUploadMethod(v as "upload" | "url")}>
            <TabsList className="grid w-full grid-cols-2 mb-4">
              <TabsTrigger value="upload">
                <Upload className="h-4 w-4 mr-2" />
                Upload from Device
              </TabsTrigger>
              <TabsTrigger value="url">
                <LinkIcon className="h-4 w-4 mr-2" />
                Add from URL
              </TabsTrigger>
            </TabsList>

            <TabsContent value="upload" className="space-y-4">
              <FileUpload
                accept="images"
                multiple={true}
                maxFiles={20}
                onUploadComplete={handleImageUpload}
              />
              <p className="text-xs text-muted-foreground">
                Supported formats: JPEG, PNG, GIF, WebP, HEIC. Max size: 10 MB per image.
              </p>
            </TabsContent>
            <TabsContent value="url" className="space-y-4">
              <div className="space-y-2">
                <div className="relative">
                  <Input
                    placeholder="https://example.com/image.jpg"
                    disabled={isValidatingUrl}
                    onKeyDown={async (e) => {
                      if (e.key === "Enter" && e.currentTarget.value.trim()) {
                        e.preventDefault();
                        const url = e.currentTarget.value.trim();
                        await handleAddImageUrl(url);
                        e.currentTarget.value = "";
                      }
                    }}
                  />
                  {isValidatingUrl && (
                    <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  Press Enter to add image URL (validates before adding)
                </p>
              </div>
            </TabsContent>
          </Tabs>

          {/* Unified Gallery - Shows all images (uploaded + URL) with removal buttons */}
          {formData.images && formData.images.length > 0 && (
            <div className="mt-6">
              <Label className="text-sm font-medium mb-3 block">
                Added Images ({formData.images.length})
              </Label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {formData.images.map((url, index) => (
                  <div key={index} className="relative group">
                    <img
                      src={url}
                      alt={`Property ${index + 1}`}
                      className="w-full h-32 object-cover rounded-lg border"
                      loading="lazy"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = "/placeholder-image.png";
                      }}
                    />
                    <Button
                      type="button"
                      size="icon"
                      variant="destructive"
                      className="absolute top-2 right-2 h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={() => handleRemoveImage(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                    {index === 0 && (
                      <div className="absolute bottom-2 left-2">
                        <span className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded">
                          Cover Image
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card variant="elevated">
        <CardContent className="p-6">
          <Label className="text-base font-semibold mb-4 block">Property Video (Optional)</Label>

          <Tabs defaultValue="upload">
            <TabsList className="grid w-full grid-cols-2 mb-4">
              <TabsTrigger value="upload">
                <Upload className="h-4 w-4 mr-2" />
                Upload Video
              </TabsTrigger>
              <TabsTrigger value="url">
                <LinkIcon className="h-4 w-4 mr-2" />
                YouTube/Vimeo URL
              </TabsTrigger>
            </TabsList>

            <TabsContent value="upload" className="space-y-4">
              <FileUpload
                accept="videos"
                multiple={false}
                maxFiles={1}
                onUploadComplete={handleVideoUpload}
                existingFiles={formData.video_url ? [formData.video_url] : []}
              />
              <p className="text-xs text-muted-foreground">
                Supported formats: MP4, MOV, AVI, WebM. Max size: 100 MB.
              </p>
            </TabsContent>

            <TabsContent value="url" className="space-y-2">
              <Input
                id="video_url"
                placeholder="https://youtube.com/watch?v=... or https://vimeo.com/..."
                value={formData.video_url || ""}
                onChange={(e) => updateFormData({ video_url: e.target.value })}
              />
              <p className="text-xs text-muted-foreground">
                YouTube or Vimeo video URL for property tour
              </p>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <div className="space-y-2">
        <Label htmlFor="virtual_tour_url">
          <LinkIcon className="h-4 w-4 inline mr-1" />
          Virtual Tour URL (Optional)
        </Label>
        <Input
          id="virtual_tour_url"
          placeholder="https://my.matterport.com/... or 360 tour link"
          value={formData.virtual_tour_url || ""}
          onChange={(e) => updateFormData({ virtual_tour_url: e.target.value })}
        />
        <p className="text-xs text-muted-foreground">
          Matterport, 360, or other virtual tour link
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="agent_name">Agent Name (Optional)</Label>
        <Input
          id="agent_name"
          placeholder="John Doe"
          value={formData.agent_name || ""}
          onChange={(e) => updateFormData({ agent_name: e.target.value })}
        />
        <p className="text-xs text-muted-foreground">
          Name of the agent responsible for this property
        </p>
      </div>
    </div>
  );
}
