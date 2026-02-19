/**
 * Utility functions for handling announcement image URLs.
 * 
 * Converts old-style URLs (/storage/announcements/...) to the new API endpoint format.
 */

/**
 * Normalize an announcement image URL.
 * 
 * Converts old-style storage paths to the new API endpoint format.
 * 
 * @param imageUrl - The image URL (may be old or new format)
 * @returns Normalized URL pointing to the API endpoint
 */
export function normalizeAnnouncementImageUrl(imageUrl: string | undefined | null): string | undefined {
  if (!imageUrl) return undefined;
  
  // If it's already a full URL (http/https), return as-is
  if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
    return imageUrl;
  }
  
  // If it's the old format (/storage/announcements/filename), convert to new format
  if (imageUrl.startsWith('/storage/announcements/')) {
    const filename = imageUrl.replace('/storage/announcements/', '').split('?')[0]; // Remove query params if any
    const apiBaseUrl = import.meta.env.VITE_API_URL || 'https://churchflow-api.ailabsafrica.com';
    return `${apiBaseUrl}/api/v1/announcements/image/${encodeURIComponent(filename)}`;
  }
  
  // If it's already the new format (/api/v1/announcements/image/...), ensure it has full URL
  if (imageUrl.includes('/api/v1/announcements/image/')) {
    // If it already starts with http/https, return as-is
    if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
      return imageUrl;
    }
    // Otherwise prepend the base URL
    const apiBaseUrl = import.meta.env.VITE_API_URL || 'https://churchflow-api.ailabsafrica.com';
    return `${apiBaseUrl}${imageUrl}`;
  }
  
  // For any other relative paths, assume they need the API base URL
  if (imageUrl.startsWith('/')) {
    const apiBaseUrl = import.meta.env.VITE_API_URL || 'https://churchflow-api.ailabsafrica.com';
    return `${apiBaseUrl}${imageUrl}`;
  }
  
  // Return as-is if we can't determine the format
  return imageUrl;
}

