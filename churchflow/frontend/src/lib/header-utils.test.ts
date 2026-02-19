/**
 * Unit tests for HTTP header utilities
 */

import { describe, it, expect } from 'vitest';
import { encodeHeaderValue, decodeHeaderValue, isBase64Encoded } from './header-utils';

describe('Header Utilities', () => {
  describe('isBase64Encoded', () => {
    it('should return true for valid base64 strings', () => {
      const encoded = btoa('test-org-id');
      expect(isBase64Encoded(encoded)).toBe(true);
    });

    it('should return false for plain strings', () => {
      expect(isBase64Encoded('plain-org-id')).toBe(false);
    });

    it('should return false for empty strings', () => {
      expect(isBase64Encoded('')).toBe(false);
    });

    it('should return false for invalid base64', () => {
      expect(isBase64Encoded('not-valid-base64!@#')).toBe(false);
    });
  });

  describe('encodeHeaderValue', () => {
    it('should encode plain organization ID', () => {
      const input = 'org-123';
      const encoded = encodeHeaderValue(input);

      expect(encoded).not.toBeNull();
      expect(encoded).not.toEqual(input);
      expect(encoded).toMatch(/^[A-Za-z0-9+/=]+$/); // Valid base64
    });

    it('should handle null gracefully', () => {
      expect(encodeHeaderValue(null)).toBeNull();
    });

    it('should handle undefined gracefully', () => {
      expect(encodeHeaderValue(undefined)).toBeNull();
    });

    it('should handle empty string gracefully', () => {
      expect(encodeHeaderValue('')).toBeNull();
      expect(encodeHeaderValue('   ')).toBeNull();
    });

    it('should encode and decode correctly', () => {
      const input = 'org-123';
      const encoded = encodeHeaderValue(input);
      const decoded = decodeHeaderValue(encoded);

      expect(decoded).toEqual(input);
    });

    it('should handle special characters', () => {
      const input = 'org-测试-🎉';
      const encoded = encodeHeaderValue(input);

      expect(encoded).not.toBeNull();
      expect(decodeHeaderValue(encoded)).toEqual(input);
    });

    it('should be idempotent (not double-encode)', () => {
      const input = 'org-123';
      const encoded1 = encodeHeaderValue(input);
      const encoded2 = encodeHeaderValue(encoded1!);

      expect(encoded1).toEqual(encoded2);
    });

    it('should handle MongoDB ObjectIDs', () => {
      const objectId = '507f1f77bcf86cd799439011';
      const encoded = encodeHeaderValue(objectId);
      const decoded = decodeHeaderValue(encoded);

      expect(decoded).toEqual(objectId);
    });

    it('should handle UUIDs', () => {
      const uuid = '550e8400-e29b-41d4-a716-446655440000';
      const encoded = encodeHeaderValue(uuid);
      const decoded = decodeHeaderValue(encoded);

      expect(decoded).toEqual(uuid);
    });

    it('should handle organization names with spaces', () => {
      const name = 'My Organization Name';
      const encoded = encodeHeaderValue(name);
      const decoded = decodeHeaderValue(encoded);

      expect(decoded).toEqual(name);
    });

    it('should handle emojis', () => {
      const input = 'org-🏢-123';
      const encoded = encodeHeaderValue(input);
      const decoded = decodeHeaderValue(encoded);

      expect(decoded).toEqual(input);
    });

    it('should handle Arabic characters', () => {
      const input = 'مؤسسة-123';
      const encoded = encodeHeaderValue(input);
      const decoded = decodeHeaderValue(encoded);

      expect(decoded).toEqual(input);
    });

    it('should handle Chinese characters', () => {
      const input = '组织-123';
      const encoded = encodeHeaderValue(input);
      const decoded = decodeHeaderValue(encoded);

      expect(decoded).toEqual(input);
    });
  });

  describe('decodeHeaderValue', () => {
    it('should decode base64 organization ID', () => {
      const original = 'org-123';
      const encoded = btoa(original);
      const decoded = decodeHeaderValue(encoded);

      expect(decoded).toEqual(original);
    });

    it('should handle plain (non-encoded) values', () => {
      const plain = 'plain-org-id';
      const decoded = decodeHeaderValue(plain);

      expect(decoded).toEqual(plain);
    });

    it('should handle null gracefully', () => {
      expect(decodeHeaderValue(null)).toBeNull();
    });

    it('should handle undefined gracefully', () => {
      expect(decodeHeaderValue(undefined)).toBeNull();
    });

    it('should handle empty string gracefully', () => {
      expect(decodeHeaderValue('')).toBeNull();
      expect(decodeHeaderValue('   ')).toBeNull();
    });

    it('should handle malformed base64 gracefully', () => {
      const invalid = 'not-valid-base64!@#';
      const decoded = decodeHeaderValue(invalid);

      // Should return original value for backward compatibility
      expect(decoded).toEqual(invalid);
    });

    it('should decode special characters correctly', () => {
      const original = 'org-测试-🎉';
      const encoded = btoa(original);
      const decoded = decodeHeaderValue(encoded);

      expect(decoded).toEqual(original);
    });
  });

  describe('Edge Cases', () => {
    it('should handle very long organization IDs', () => {
      const longId = 'a'.repeat(1000);
      const encoded = encodeHeaderValue(longId);
      const decoded = decodeHeaderValue(encoded);

      expect(decoded).toEqual(longId);
    });

    it('should handle organization IDs with only special characters', () => {
      const specialChars = '!@#$%^&*()_+-=[]{}|;:,.<>?';
      const encoded = encodeHeaderValue(specialChars);
      const decoded = decodeHeaderValue(encoded);

      expect(decoded).toEqual(specialChars);
    });

    it('should handle whitespace in organization IDs', () => {
      const withSpaces = 'org with spaces';
      const encoded = encodeHeaderValue(withSpaces);
      const decoded = decodeHeaderValue(encoded);

      expect(decoded).toEqual(withSpaces);
    });
  });
});
