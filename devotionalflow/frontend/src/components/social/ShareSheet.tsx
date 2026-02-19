/**
 * ShareSheet Component
 * Bottom sheet for sharing devotionals on social media platforms
 */

import { motion, AnimatePresence } from "framer-motion";
import { X, Facebook, MessageCircle, Link2, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { shareOn, ShareData, SharePlatform, getPlatformName, getCopyInstructions } from "@/lib/share";
import { useToast } from "@/hooks/use-toast";

// Custom icons for platforms not in lucide-react
const XIcon = () => (
  <svg
    className="w-5 h-5"
    viewBox="0 0 24 24"
    fill="currentColor"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
  </svg>
);

const InstagramIcon = () => (
  <svg
    className="w-5 h-5"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <rect x="2" y="2" width="20" height="20" rx="5" ry="5" stroke="currentColor" strokeWidth="2" />
    <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="2" />
    <circle cx="17.5" cy="6.5" r="1.5" fill="currentColor" />
  </svg>
);

const TikTokIcon = () => (
  <svg
    className="w-5 h-5"
    viewBox="0 0 24 24"
    fill="currentColor"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z" />
  </svg>
);

interface ShareOption {
  platform: SharePlatform;
  icon: React.ReactNode;
  label: string;
  color: string;
}

const shareOptions: ShareOption[] = [
  {
    platform: 'facebook',
    icon: <Facebook className="w-5 h-5" />,
    label: 'Facebook',
    color: 'bg-[#1877F2] hover:bg-[#1877F2]/90',
  },
  {
    platform: 'whatsapp',
    icon: <MessageCircle className="w-5 h-5" />,
    label: 'WhatsApp',
    color: 'bg-[#25D366] hover:bg-[#25D366]/90',
  },
  {
    platform: 'twitter',
    icon: <XIcon />,
    label: 'X',
    color: 'bg-[#000000] hover:bg-[#000000]/90',
  },
  {
    platform: 'instagram',
    icon: <InstagramIcon />,
    label: 'Instagram',
    color: 'bg-gradient-to-br from-[#833AB4] via-[#FD1D1D] to-[#F77737] hover:opacity-90',
  },
  {
    platform: 'tiktok',
    icon: <TikTokIcon />,
    label: 'TikTok',
    color: 'bg-[#000000] hover:bg-[#000000]/90',
  },
  {
    platform: 'copy',
    icon: <Copy className="w-5 h-5" />,
    label: 'Copy Link',
    color: 'bg-gray-600 hover:bg-gray-600/90',
  },
];

interface ShareSheetProps {
  isOpen: boolean;
  onClose: () => void;
  shareData: ShareData;
  onShare?: (platform: SharePlatform) => void;
}

export function ShareSheet({ isOpen, onClose, shareData, onShare }: ShareSheetProps) {
  const { toast } = useToast();

  const handleShare = async (platform: SharePlatform) => {
    try {
      const instructions = getCopyInstructions(platform);

      await shareOn(platform, shareData, () => {
        // Callback for copy actions
        if (instructions) {
          toast({
            title: "Link copied!",
            description: instructions,
            duration: 5000,
          });
        } else {
          toast({
            title: "Link copied!",
            description: "Share link copied to clipboard",
          });
        }
      });

      // Notify parent component
      onShare?.(platform);

      // Close sheet after share (except for Instagram/TikTok which need instructions)
      if (!instructions) {
        setTimeout(() => onClose(), 500);
      }
    } catch (error) {
      console.error('Share error:', error);
      toast({
        title: "Share failed",
        description: "Could not share devotional. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-foreground/20 z-50"
            onClick={onClose}
          />

          {/* Sheet */}
          <motion.div
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 25 }}
            className="fixed bottom-0 left-0 right-0 z-50 bg-background rounded-t-3xl overflow-hidden"
          >
            {/* Header */}
            <div className="p-4 border-b border-border">
              <div className="w-12 h-1 bg-muted rounded-full mx-auto mb-4" />
              <div className="flex items-center justify-between">
                <h3 className="font-serif text-lg font-semibold">Share Devotional</h3>
                <Button variant="ghost" size="icon" onClick={onClose}>
                  <X className="w-5 h-5" />
                </Button>
              </div>
              <p className="text-sm text-muted-foreground mt-2">
                Inspire others with today's devotional
              </p>
            </div>

            {/* Share Options */}
            <div className="p-6 space-y-3">
              {shareOptions.map((option) => (
                <button
                  key={option.platform}
                  onClick={() => handleShare(option.platform)}
                  className={`w-full flex items-center gap-4 p-4 rounded-xl text-white transition-all active:scale-95 ${option.color}`}
                >
                  {option.icon}
                  <span className="font-medium">Share on {option.label}</span>
                </button>
              ))}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-border bg-muted/30">
              <p className="text-xs text-center text-muted-foreground">
                Share the Holy Spirit's inspiration with your friends and family
              </p>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
