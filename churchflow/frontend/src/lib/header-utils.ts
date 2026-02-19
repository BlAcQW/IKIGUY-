/**
 * HTTP Header Utilities
 *
 * Provides functions for safely encoding and decoding header values.
 * HTTP headers must only contain ISO-8859-1 (Latin-1) characters.
 * This utility uses base64 encoding to ensure all characters are properly encoded.
 */

/**
 * Check if a string is valid base64-encoded.
 *
 * @param value - String to validate
 * @returns True if the string is valid base64
 */
export function isBase64Encoded(value: string): boolean {
  if (!value || value.trim() === '') {
    return false;
  }

  try {
    // Try to decode - if it succeeds and re-encoding matches, it's valid base64
    const decoded = atob(value);
    const reencoded = btoa(decoded);
    return reencoded === value;
  } catch (error) {
    return false;
  }
}

/**
 * Encode a header value using base64.
 *
 * HTTP headers must only contain ISO-8859-1 characters. This function
 * base64-encodes organization IDs to ensure they can be safely transmitted
 * in headers, even if they contain special characters, emojis, or unicode.
 *
 * This function is idempotent - if the value is already base64-encoded,
 * it will not be double-encoded.
 *
 * @param value - Organization ID from localStorage
 * @returns Base64-encoded organization ID suitable for HTTP headers, or null if input is null/undefined/empty
 */
export function encodeHeaderValue(value: string | null | undefined): string | null {
  // Handle null/undefined/empty
  if (!value || value.trim() === '') {
    return null;
  }

  // First, sanitize the value - remove all whitespace including newlines
  // This is critical because localStorage values might have trailing newlines
  const sanitized = value.replace(/[\r\n\t\s]+/g, '').trim();

  if (sanitized === '') {
    return null;
  }

  // Check if already encoded (prevent double-encoding)
  if (isBase64Encoded(sanitized)) {
    return sanitized;
  }

  // Encode to base64 using UTF-8 safe method
  // Standard btoa() fails on non-Latin-1 characters
  // This approach handles any Unicode string safely
  try {
    // encodeURIComponent handles UTF-8, then we decode percent-encoding to bytes
    return btoa(unescape(encodeURIComponent(sanitized)));
  } catch (error) {
    // If encoding still fails, log error and return null
    console.error('Failed to encode header value:', error);
    return null;
  }
}

/**
 * Decode a base64-encoded header value.
 *
 * Supports both base64-encoded and plain values for backward compatibility.
 * If decoding fails, returns the original value.
 *
 * @param value - Organization ID from HTTP header
 * @returns Decoded organization ID, or null if input is null/undefined/empty
 */
export function decodeHeaderValue(value: string | null | undefined): string | null {
  // Handle null/undefined/empty
  if (!value || value.trim() === '') {
    return null;
  }

  // Sanitize input first
  const sanitized = value.replace(/[\r\n\t\s]+/g, '').trim();

  if (sanitized === '') {
    return null;
  }

  // Try to decode from base64
  try {
    if (isBase64Encoded(sanitized)) {
      // Decode using UTF-8 safe method (reverse of encoding)
      return decodeURIComponent(escape(atob(sanitized)));
    }
    // Not base64-encoded, return sanitized value (backward compatibility)
    return sanitized;
  } catch (error) {
    // If decoding fails, return sanitized value (backward compatibility)
    console.warn('Failed to decode header value, using as-is:', error);
    return sanitized;
  }
}

/**
 * Sanitize an authentication token.
 *
 * Removes newlines, carriage returns, and other invalid header characters
 * from tokens to prevent "Failed to encode header value" errors.
 *
 * @param token - Access token from localStorage or API
 * @returns Sanitized token safe for use in HTTP headers
 */
export function sanitizeToken(token: string | null | undefined): string | null {
  // Handle null/undefined/empty
  if (!token || token.trim() === '') {
    return null;
  }

  // Remove all whitespace (including newlines, carriage returns, tabs)
  // and other control characters that are invalid in HTTP headers
  const sanitized = token.replace(/[\r\n\t\s]+/g, '').trim();

  // Return null if sanitized token is empty
  return sanitized === '' ? null : sanitized;
}
