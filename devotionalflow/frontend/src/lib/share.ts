/**
 * Social sharing utilities for DevotionalFlow
 * Generates platform-specific share URLs and handles sharing actions
 */

export interface ShareData {
  title: string;
  text: string;
  url: string;
  imageUrl?: string;
}

export type SharePlatform =
  | 'facebook'
  | 'whatsapp'
  | 'twitter'
  | 'instagram'
  | 'tiktok'
  | 'copy'
  | 'native';

/**
 * Generate share URL for specific platform
 */
export function getShareUrl(platform: SharePlatform, data: ShareData): string | null {
  const encodedUrl = encodeURIComponent(data.url);
  const encodedTitle = encodeURIComponent(data.title);
  const encodedText = encodeURIComponent(data.text);

  switch (platform) {
    case 'facebook':
      // Facebook share dialog
      return `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;

    case 'whatsapp':
      // WhatsApp share
      const whatsappText = `${data.title}\n\n${data.text}\n\n${data.url}`;
      return `https://wa.me/?text=${encodeURIComponent(whatsappText)}`;

    case 'twitter':
      // Twitter/X share
      return `https://twitter.com/intent/tweet?text=${encodedTitle}&url=${encodedUrl}`;

    case 'instagram':
      // Instagram doesn't support direct sharing via URL
      // Return null to indicate clipboard copy needed
      return null;

    case 'tiktok':
      // TikTok doesn't support direct sharing via URL
      // Return null to indicate clipboard copy needed
      return null;

    case 'copy':
      // Clipboard copy
      return null;

    case 'native':
      // Native share API
      return null;

    default:
      return null;
  }
}

/**
 * Share content on specified platform
 */
export async function shareOn(
  platform: SharePlatform,
  data: ShareData,
  onCopy?: () => void
): Promise<boolean> {
  const shareUrl = getShareUrl(platform, data);

  switch (platform) {
    case 'facebook':
    case 'whatsapp':
    case 'twitter':
      if (shareUrl) {
        // Open share URL in new window
        const width = 600;
        const height = 400;
        const left = (screen.width - width) / 2;
        const top = (screen.height - height) / 2;

        window.open(
          shareUrl,
          'share',
          `width=${width},height=${height},left=${left},top=${top},toolbar=0,status=0`
        );
        return true;
      }
      return false;

    case 'instagram':
    case 'tiktok':
      // These platforms don't support direct URL sharing
      // Copy link to clipboard with instructions
      await navigator.clipboard.writeText(data.url);
      onCopy?.();
      return true;

    case 'copy':
      // Copy link to clipboard
      await navigator.clipboard.writeText(data.url);
      onCopy?.();
      return true;

    case 'native':
      // Use native share API if available
      if (navigator.share) {
        try {
          await navigator.share({
            title: data.title,
            text: data.text,
            url: data.url,
          });
          return true;
        } catch (err) {
          // User cancelled or error occurred
          return false;
        }
      }
      return false;

    default:
      return false;
  }
}

/**
 * Check if native share is available
 */
export function isNativeShareAvailable(): boolean {
  return typeof navigator !== 'undefined' && !!navigator.share;
}

/**
 * Get platform display name
 */
export function getPlatformName(platform: SharePlatform): string {
  const names: Record<SharePlatform, string> = {
    facebook: 'Facebook',
    whatsapp: 'WhatsApp',
    twitter: 'X (Twitter)',
    instagram: 'Instagram',
    tiktok: 'TikTok',
    copy: 'Copy Link',
    native: 'Share',
  };

  return names[platform];
}

/**
 * Get platform-specific instructions for clipboard-only platforms
 */
export function getCopyInstructions(platform: SharePlatform): string | null {
  const instructions: Partial<Record<SharePlatform, string>> = {
    instagram: 'Link copied! Open Instagram and paste in your Story or DM',
    tiktok: 'Link copied! Open TikTok and paste in your video description or comment',
  };

  return instructions[platform] || null;
}
