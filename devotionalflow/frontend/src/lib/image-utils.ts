/**
 * Image URL utilities
 * Handles both absolute URLs (Unsplash, external) and relative paths (uploaded media)
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://freshmanna-api.ailabsafrica.com';

/**
 * Get the full URL for an image
 * If the URL is already absolute (starts with http:// or https://), returns it as-is
 * If it's a relative path, prepends the media API endpoint
 *
 * @param imageUrl - The image URL from the API (can be absolute or relative)
 * @returns Full image URL ready for use in img src
 */
export function getImageUrl(imageUrl: string | undefined | null): string | undefined {
  if (!imageUrl) {
    return undefined;
  }

  // If URL is already absolute (Unsplash, external CDN, etc.), use it directly
  if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
    return imageUrl;
  }

  // If it's a relative path, prepend the media proxy endpoint
  return `${API_BASE_URL}/api/v1/media/image/${imageUrl}`;
}
