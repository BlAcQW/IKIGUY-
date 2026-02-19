/**
 * VideoPlayer Component
 *
 * Responsive video player for property tours supporting:
 * - YouTube embeds
 * - Vimeo embeds
 * - Direct video URLs
 */

import { useState } from "react";
import { Play, X } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface VideoPlayerProps {
  videoUrl: string;
  title?: string;
  thumbnail?: string;
  className?: string;
  autoplay?: boolean;
}

export function VideoPlayer({
  videoUrl,
  title = "Property Video Tour",
  thumbnail,
  className,
  autoplay = false
}: VideoPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(autoplay);

  /**
   * Extract video ID and platform from URL.
   *
   * Supports:
   * - YouTube: youtube.com/watch?v=ID, youtu.be/ID
   * - Vimeo: vimeo.com/ID
   */
  const getVideoEmbedUrl = (url: string): { embedUrl: string; platform: "youtube" | "vimeo" | "direct" } | null => {
    if (!url) return null;

    // YouTube patterns
    const youtubeRegex = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/;
    const youtubeMatch = url.match(youtubeRegex);

    if (youtubeMatch && youtubeMatch[1]) {
      const videoId = youtubeMatch[1];
      return {
        embedUrl: `https://www.youtube.com/embed/${videoId}?autoplay=${autoplay ? 1 : 0}`,
        platform: "youtube"
      };
    }

    // Vimeo patterns
    const vimeoRegex = /vimeo\.com\/(?:video\/)?(\d+)/;
    const vimeoMatch = url.match(vimeoRegex);

    if (vimeoMatch && vimeoMatch[1]) {
      const videoId = vimeoMatch[1];
      return {
        embedUrl: `https://player.vimeo.com/video/${videoId}?autoplay=${autoplay ? 1 : 0}`,
        platform: "vimeo"
      };
    }

    // Direct video URL (mp4, webm, etc.)
    if (url.match(/\.(mp4|webm|ogg)$/i)) {
      return {
        embedUrl: url,
        platform: "direct"
      };
    }

    return null;
  };

  const videoInfo = getVideoEmbedUrl(videoUrl);

  if (!videoInfo) {
    return (
      <Card className={cn("p-6 text-center", className)}>
        <p className="text-muted-foreground">Invalid video URL format</p>
        <p className="text-sm text-muted-foreground mt-2">
          Supported: YouTube, Vimeo, or direct video links
        </p>
      </Card>
    );
  }

  const { embedUrl, platform } = videoInfo;

  // Render direct video player
  if (platform === "direct") {
    return (
      <div className={cn("relative rounded-lg overflow-hidden bg-black", className)}>
        <video
          src={embedUrl}
          controls
          autoPlay={autoplay}
          className="w-full h-full"
          title={title}
        >
          Your browser does not support the video tag.
        </video>
      </div>
    );
  }

  // Render embed player with play button overlay
  return (
    <div className={cn("relative group", className)}>
      {!isPlaying && thumbnail && (
        <div
          className="relative aspect-video rounded-lg overflow-hidden cursor-pointer"
          onClick={() => setIsPlaying(true)}
        >
          {/* Thumbnail */}
          <img
            src={thumbnail}
            alt={title}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
          />

          {/* Dark overlay */}
          <div className="absolute inset-0 bg-black/40 group-hover:bg-black/50 transition-colors" />

          {/* Play button */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex items-center justify-center w-20 h-20 rounded-full bg-white/90 group-hover:bg-white group-hover:scale-110 transition-all shadow-lg">
              <Play className="h-10 w-10 text-black fill-current ml-1" />
            </div>
          </div>

          {/* Title */}
          <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent">
            <p className="text-white font-semibold">{title}</p>
          </div>
        </div>
      )}

      {(isPlaying || !thumbnail) && (
        <div className="relative aspect-video rounded-lg overflow-hidden bg-black">
          <iframe
            src={embedUrl}
            title={title}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            className="absolute inset-0 w-full h-full"
          />

          {/* Close button (only if thumbnail was shown initially) */}
          {thumbnail && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-2 right-2 bg-black/50 hover:bg-black/70 text-white"
              onClick={() => setIsPlaying(false)}
            >
              <X className="h-5 w-5" />
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * VideoGallery Component
 *
 * Displays multiple videos in a gallery format.
 */
interface VideoGalleryProps {
  videos: Array<{
    url: string;
    title?: string;
    thumbnail?: string;
  }>;
  className?: string;
}

export function VideoGallery({ videos, className }: VideoGalleryProps) {
  if (!videos || videos.length === 0) {
    return null;
  }

  return (
    <div className={cn("space-y-6", className)}>
      <h3 className="text-xl font-semibold">Property Videos</h3>

      {videos.length === 1 ? (
        <VideoPlayer
          videoUrl={videos[0].url}
          title={videos[0].title}
          thumbnail={videos[0].thumbnail}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {videos.map((video, index) => (
            <VideoPlayer
              key={index}
              videoUrl={video.url}
              title={video.title || `Video ${index + 1}`}
              thumbnail={video.thumbnail}
            />
          ))}
        </div>
      )}
    </div>
  );
}
