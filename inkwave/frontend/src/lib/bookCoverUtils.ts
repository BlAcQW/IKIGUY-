/**
 * Book Cover Utilities
 * Helper functions for generating unique placeholder covers
 */

import { INKWAVE_API_BASE } from '../config/api-config';

/**
 * Generate a color based on a string (book title).
 * Returns a consistent color for the same title.
 *
 * Args:
 *   text: The book title or identifier
 *
 * Returns:
 *   Hex color code
 */
function stringToColor(text: string): string {
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    hash = text.charCodeAt(i) + ((hash << 5) - hash);
  }

  // Generate vibrant colors (avoid too dark or too bright)
  const hue = hash % 360;
  const saturation = 65 + (hash % 20); // 65-85%
  const lightness = 45 + (hash % 15); // 45-60%

  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

/**
 * Get initials from book title.
 *
 * Args:
 *   title: Book title
 *
 * Returns:
 *   Up to 3 initials
 */
function getBookInitials(title: string): string {
  const words = title.split(' ').filter(word => word.length > 0);

  if (words.length === 0) return 'BK';
  if (words.length === 1) return words[0].substring(0, 2).toUpperCase();

  // Get first letter of first 3 words
  const initials = words
    .slice(0, 3)
    .map(word => word[0].toUpperCase())
    .join('');

  return initials;
}

/**
 * Generate a unique placeholder cover URL for a book.
 * Uses ui-avatars.com to generate a colored placeholder with book initials.
 *
 * Args:
 *   title: Book title
 *   author: Book author (optional)
 *
 * Returns:
 *   Placeholder image URL
 */
export function generatePlaceholderCover(title: string, author?: string): string {
  const initials = getBookInitials(title);
  const color = stringToColor(title);

  // Extract hex color from HSL
  const hslMatch = color.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/);
  if (!hslMatch) {
    return `https://ui-avatars.com/api/?name=${encodeURIComponent(initials)}&size=400&background=6366f1&color=fff&bold=true&format=png`;
  }

  const [, h, s, l] = hslMatch.map(Number);
  const hexColor = hslToHex(h, s, l);

  return `https://ui-avatars.com/api/?name=${encodeURIComponent(initials)}&size=400&background=${hexColor}&color=fff&bold=true&format=png`;
}

/**
 * Convert HSL to Hex color.
 *
 * Args:
 *   h: Hue (0-360)
 *   s: Saturation (0-100)
 *   l: Lightness (0-100)
 *
 * Returns:
 *   Hex color without # prefix
 */
function hslToHex(h: number, s: number, l: number): string {
  l /= 100;
  const a = s * Math.min(l, 1 - l) / 100;
  const f = (n: number) => {
    const k = (n + h / 30) % 12;
    const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
    return Math.round(255 * color).toString(16).padStart(2, '0');
  };
  return `${f(0)}${f(8)}${f(4)}`;
}

/**
 * Get book cover URL with fallback to unique placeholder.
 *
 * Args:
 *   coverUrl: Original cover URL from API
 *   title: Book title for generating placeholder
 *   author: Book author
 *   defaultCoverUrl: The default/duplicate cover URL to replace
 *
 * Returns:
 *   Cover URL or unique placeholder
 */
export function getBookCoverUrl(
  coverUrl: string | null | undefined,
  title: string,
  author?: string,
  defaultCoverUrl = 'https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg'
): string {
  // Handle null, undefined, empty string, or Python's "None" string
  if (!coverUrl || coverUrl === 'None' || coverUrl.trim() === '' || coverUrl === defaultCoverUrl) {
    return generatePlaceholderCover(title, author);
  }

  // Handle relative paths (e.g., /static/covers/...) - prefix with API base URL
  if (coverUrl.startsWith('/')) {
    return `${INKWAVE_API_BASE}${coverUrl}`;
  }

  return coverUrl;
}
