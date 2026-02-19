import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Card, CardContent } from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";
import { 
  Share2, 
  Twitter, 
  Facebook, 
  Linkedin, 
  MessageCircle, 
  Mail, 
  Copy, 
  Check,
  Link as LinkIcon,
  X
} from "lucide-react";

interface DemoSharingProps {
  demoId: string;
  assistantName: string;
  assistantType: string;
  demoUrl: string;
  description?: string;
  onShare?: (platform: string, url: string) => void;
}

interface SharePlatform {
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  url: (params: ShareParams) => string;
  mobileUrl?: (params: ShareParams) => string;
}

interface ShareParams {
  url: string;
  title: string;
  description: string;
  hashtags?: string;
}

const sharePlatforms: SharePlatform[] = [
  {
    name: "Twitter",
    icon: Twitter,
    color: "#1DA1F2",
    url: ({ url, title, description, hashtags }) => 
      `https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(url)}&hashtags=${hashtags || 'AI,VoicAssistant'}`,
  },
  {
    name: "Facebook",
    icon: Facebook,
    color: "#1877F2",
    url: ({ url, title, description }) => 
      `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}&quote=${encodeURIComponent(title)}`,
  },
  {
    name: "LinkedIn",
    icon: Linkedin,
    color: "#0A66C2",
    url: ({ url, title, description }) => 
      `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}&title=${encodeURIComponent(title)}&summary=${encodeURIComponent(description)}`,
  },
  {
    name: "WhatsApp",
    icon: MessageCircle,
    color: "#25D366",
    url: ({ url, title, description }) => 
      `https://wa.me/?text=${encodeURIComponent(`${title} - ${description} ${url}`)}`,
    mobileUrl: ({ url, title, description }) => 
      `whatsapp://send?text=${encodeURIComponent(`${title} - ${description} ${url}`)}`,
  },
  {
    name: "Email",
    icon: Mail,
    color: "#EA4335",
    url: ({ url, title, description }) => 
      `mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(`${description}\n\nTry it here: ${url}`)}`,
  },
];

const DemoSharing = ({ 
  demoId, 
  assistantName, 
  assistantType, 
  demoUrl, 
  description = "", 
  onShare 
}: DemoSharingProps) => {
  const { toast } = useToast();
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [customMessage, setCustomMessage] = useState("");
  const [copied, setCopied] = useState(false);

  const defaultMessage = `Check out ${assistantName}, an AI voice assistant for ${assistantType.replace(/_/g, ' ')}! 🎤✨`;
  const shareMessage = customMessage || defaultMessage;

  const handleShare = (platform: SharePlatform) => {
    const params: ShareParams = {
      url: demoUrl,
      title: shareMessage,
      description: description || `Experience ${assistantName} - an AI voice assistant for ${assistantType.replace(/_/g, ' ')}`,
      hashtags: "AI,VoiceAssistant,Technology"
    };

    const shareUrl = platform.url(params);
    
    // Track share event
    if (onShare) {
      onShare(platform.name.toLowerCase(), shareUrl);
    }

    // Open share URL
    if (platform.name === "WhatsApp" && /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
      // Use mobile URL for WhatsApp on mobile devices
      const mobileUrl = platform.mobileUrl?.(params) || shareUrl;
      window.location.href = mobileUrl;
    } else {
      // Open in popup for other platforms
      const popup = window.open(shareUrl, '_blank', 'width=600,height=400,scrollbars=yes,resizable=yes');
      if (popup) {
        popup.focus();
      } else {
        // Fallback to direct navigation if popup is blocked
        window.open(shareUrl, '_blank');
      }
    }

    toast({
      title: "Shared!",
      description: `Shared on ${platform.name}`,
    });
  };

  const copyShareLink = async () => {
    try {
      await navigator.clipboard.writeText(demoUrl);
      setCopied(true);
      
      // Track copy event
      if (onShare) {
        onShare('copy_link', demoUrl);
      }

      toast({
        title: "Link copied!",
        description: "Demo link copied to clipboard",
      });
      
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast({
        title: "Failed to copy",
        description: "Could not copy link to clipboard",
        variant: "destructive"
      });
    }
  };

  const copyShareText = async () => {
    try {
      const shareText = `${shareMessage}\n\n${demoUrl}`;
      await navigator.clipboard.writeText(shareText);
      setCopied(true);
      
      // Track copy event
      if (onShare) {
        onShare('copy_text', shareText);
      }

      toast({
        title: "Text copied!",
        description: "Share text copied to clipboard",
      });
      
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast({
        title: "Failed to copy",
        description: "Could not copy text to clipboard",
        variant: "destructive"
      });
    }
  };

  return (
    <>
      {/* Quick Share Button */}
      <Button 
        variant="outline" 
        onClick={() => setShareDialogOpen(true)}
        className="flex items-center gap-1 px-2 py-1 text-xs"
      >
        <Share2 className="h-3 w-3" />
        <span className="hidden sm:inline">Share Demo</span>
      </Button>

      {/* Share Dialog */}
      <Dialog open={shareDialogOpen} onOpenChange={setShareDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Share2 className="h-5 w-5" />
              Share Demo
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* Demo Preview */}
            <Card>
              <CardContent className="p-4">
                <h3 className="font-semibold text-lg mb-1">{assistantName}</h3>
                <p className="text-sm text-muted-foreground capitalize mb-2">
                  {assistantType.replace(/_/g, ' ')}
                </p>
                {description && (
                  <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                    {description}
                  </p>
                )}
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <LinkIcon className="h-3 w-3" />
                  <span className="truncate">{demoUrl}</span>
                </div>
              </CardContent>
            </Card>

            {/* Custom Message */}
            <div className="space-y-2">
              <Label htmlFor="share-message">Custom Message (Optional)</Label>
              <Textarea
                id="share-message"
                value={customMessage}
                onChange={(e) => setCustomMessage(e.target.value)}
                placeholder={defaultMessage}
                rows={3}
                className="resize-none"
              />
            </div>

            {/* Share Platforms */}
            <div className="space-y-3">
              <Label>Share on Social Media</Label>
              <div className="grid grid-cols-5 gap-2">
                {sharePlatforms.map((platform) => (
                  <Button
                    key={platform.name}
                    variant="outline"
                    size="sm"
                    onClick={() => handleShare(platform)}
                    className="flex flex-col items-center gap-1 h-auto py-3 hover:scale-105 transition-transform"
                    style={{ borderColor: platform.color }}
                  >
                    <platform.icon className="h-5 w-5" style={{ color: platform.color }} />
                    <span className="text-xs">{platform.name}</span>
                  </Button>
                ))}
              </div>
            </div>

            {/* Copy Options */}
            <div className="space-y-2">
              <Label>Copy Options</Label>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyShareLink}
                  className="flex items-center gap-2 flex-1"
                >
                  {copied ? <Check className="h-4 w-4" /> : <LinkIcon className="h-4 w-4" />}
                  {copied ? "Copied!" : "Copy Link"}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyShareText}
                  className="flex items-center gap-2 flex-1"
                >
                  {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  {copied ? "Copied!" : "Copy Text"}
                </Button>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShareDialogOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default DemoSharing;
