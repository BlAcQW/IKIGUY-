import { describe, it, expect } from 'vitest';
import {
  serializeUUID,
  serializeDateTime,
  serializeDecimal,
  transformResponse,
  transformResponseArray,
  transformRequest,
  hasUUIDProperties,
  hasDateTimeProperties,
  createTransformer,
} from '../type-conversions';

describe('Type Conversion Utilities', () => {
  describe('serializeUUID', () => {
    it('should return string UUID as-is', () => {
      const uuid = '123e4567-e89b-12d3-a456-426614174000';
      expect(serializeUUID(uuid)).toBe(uuid);
    });

    it('should convert UUID object to string', () => {
      const uuidObj = { toString: () => '123e4567-e89b-12d3-a456-426614174000' };
      expect(serializeUUID(uuidObj)).toBe('123e4567-e89b-12d3-a456-426614174000');
    });
  });

  describe('serializeDateTime', () => {
    it('should return ISO string as-is', () => {
      const isoString = '2023-12-01T10:30:00.000Z';
      expect(serializeDateTime(isoString)).toBe(isoString);
    });

    it('should convert Date object to ISO string', () => {
      const date = new Date('2023-12-01T10:30:00.000Z');
      expect(serializeDateTime(date)).toBe('2023-12-01T10:30:00.000Z');
    });

    it('should handle Python datetime-like objects', () => {
      const pythonDateTime = { isoformat: () => '2023-12-01T10:30:00.000Z' };
      expect(serializeDateTime(pythonDateTime)).toBe('2023-12-01T10:30:00.000Z');
    });

    it('should handle invalid date strings gracefully', () => {
      const invalidDate = 'invalid-date';
      expect(serializeDateTime(invalidDate)).toBe(invalidDate);
    });
  });

  describe('serializeDecimal', () => {
    it('should return number as-is', () => {
      expect(serializeDecimal(123.45)).toBe(123.45);
    });

    it('should convert string to number', () => {
      expect(serializeDecimal('123.45')).toBe(123.45);
    });

    it('should handle Python Decimal-like objects', () => {
      const pythonDecimal = { __float__: () => 123.45 };
      expect(serializeDecimal(pythonDecimal)).toBe(123.45);
    });

    it('should handle invalid numbers', () => {
      expect(serializeDecimal('invalid')).toBe(NaN);
    });
  });

  describe('transformResponse', () => {
    it('should transform UUID fields', () => {
      const response = {
        id: { toString: () => '123e4567-e89b-12d3-a456-426614174000' },
        tenant_id: { toString: () => '987fcdeb-51a2-43d1-b789-123456789abc' },
        name: 'Test Assistant',
      };

      const transformed = transformResponse(response);
      expect(transformed.id).toBe('123e4567-e89b-12d3-a456-426614174000');
      expect(transformed.tenant_id).toBe('987fcdeb-51a2-43d1-b789-123456789abc');
      expect(transformed.name).toBe('Test Assistant');
    });

    it('should transform datetime fields', () => {
      const response = {
        created_at: { isoformat: () => '2023-12-01T10:30:00.000Z' },
        updated_at: { isoformat: () => '2023-12-01T11:30:00.000Z' },
        name: 'Test Assistant',
      };

      const transformed = transformResponse(response);
      expect(transformed.created_at).toBe('2023-12-01T10:30:00.000Z');
      expect(transformed.updated_at).toBe('2023-12-01T11:30:00.000Z');
      expect(transformed.name).toBe('Test Assistant');
    });

    it('should transform decimal fields', () => {
      const response = {
        cost: { __float__: () => 123.45 },
        price: { __float__: () => 67.89 },
        balance: { __float__: () => 1000.00 },
        name: 'Test Assistant',
      };

      const transformed = transformResponse(response);
      expect(transformed.cost).toBe(123.45);
      expect(transformed.price).toBe(67.89);
      expect(transformed.balance).toBe(1000.00);
      expect(transformed.name).toBe('Test Assistant');
    });

    it('should handle mixed data types', () => {
      const response = {
        id: { toString: () => '123e4567-e89b-12d3-a456-426614174000' },
        created_at: { isoformat: () => '2023-12-01T10:30:00.000Z' },
        cost: { __float__: () => 123.45 },
        name: 'Test Assistant',
        status: 'active',
      };

      const transformed = transformResponse(response);
      expect(transformed.id).toBe('123e4567-e89b-12d3-a456-426614174000');
      expect(transformed.created_at).toBe('2023-12-01T10:30:00.000Z');
      expect(transformed.cost).toBe(123.45);
      expect(transformed.name).toBe('Test Assistant');
      expect(transformed.status).toBe('active');
    });
  });

  describe('transformResponseArray', () => {
    it('should transform array of objects', () => {
      const responses = [
        {
          id: { toString: () => '123e4567-e89b-12d3-a456-426614174000' },
          created_at: { isoformat: () => '2023-12-01T10:30:00.000Z' },
          name: 'Assistant 1',
        },
        {
          id: { toString: () => '987fcdeb-51a2-43d1-b789-123456789abc' },
          created_at: { isoformat: () => '2023-12-01T11:30:00.000Z' },
          name: 'Assistant 2',
        },
      ];

      const transformed = transformResponseArray(responses);
      expect(transformed).toHaveLength(2);
      expect(transformed[0].id).toBe('123e4567-e89b-12d3-a456-426614174000');
      expect(transformed[0].created_at).toBe('2023-12-01T10:30:00.000Z');
      expect(transformed[1].id).toBe('987fcdeb-51a2-43d1-b789-123456789abc');
      expect(transformed[1].created_at).toBe('2023-12-01T11:30:00.000Z');
    });
  });

  describe('transformRequest', () => {
    it('should validate UUID format', () => {
      const request = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        tenant_id: '987fcdeb-51a2-43d1-b789-123456789abc',
        name: 'Test Assistant',
      };

      const transformed = transformRequest(request);
      expect(transformed).toEqual(request);
    });

    it('should throw error for invalid UUID', () => {
      const request = {
        id: 'invalid-uuid',
        name: 'Test Assistant',
      };

      expect(() => transformRequest(request)).toThrow('Invalid UUID format');
    });

    it('should convert Date objects to ISO strings', () => {
      const date = new Date('2023-12-01T10:30:00.000Z');
      const request = {
        created_at: date,
        name: 'Test Assistant',
      };

      const transformed = transformRequest(request);
      expect(transformed.created_at).toBe('2023-12-01T10:30:00.000Z');
      expect(transformed.name).toBe('Test Assistant');
    });

    it('should validate date strings', () => {
      const request = {
        created_at: '2023-12-01T10:30:00.000Z',
        name: 'Test Assistant',
      };

      const transformed = transformRequest(request);
      expect(transformed).toEqual(request);
    });

    it('should throw error for invalid date', () => {
      const request = {
        created_at: 'invalid-date',
        name: 'Test Assistant',
      };

      expect(() => transformRequest(request)).toThrow('Invalid date format');
    });

    it('should convert string numbers to numbers', () => {
      const request = {
        cost: '123.45',
        price: '67.89',
        balance: '1000.00',
        name: 'Test Assistant',
      };

      const transformed = transformRequest(request);
      expect(transformed.cost).toBe(123.45);
      expect(transformed.price).toBe(67.89);
      expect(transformed.balance).toBe(1000.00);
      expect(transformed.name).toBe('Test Assistant');
    });

    it('should throw error for invalid numbers', () => {
      const request = {
        cost: 'invalid-number',
        name: 'Test Assistant',
      };

      expect(() => transformRequest(request)).toThrow('Invalid number format');
    });
  });

  describe('Type Guards', () => {
    it('should identify objects with UUID properties', () => {
      const objWithId = { id: '123e4567-e89b-12d3-a456-426614174000' };
      const objWithoutId = { name: 'Test' };

      expect(hasUUIDProperties(objWithId)).toBe(true);
      expect(hasUUIDProperties(objWithoutId)).toBe(false);
    });

    it('should identify objects with datetime properties', () => {
      const objWithDates = { created_at: '2023-12-01T10:30:00.000Z' };
      const objWithoutDates = { name: 'Test' };

      expect(hasDateTimeProperties(objWithDates)).toBe(true);
      expect(hasDateTimeProperties(objWithoutDates)).toBe(false);
    });
  });

  describe('createTransformer', () => {
    it('should create type-safe transformer', () => {
      interface TestType {
        id: string;
        name: string;
        created_at: string;
      }

      const transformer = createTransformer<TestType>();
      
      const response = {
        id: { toString: () => '123e4567-e89b-12d3-a456-426614174000' },
        name: 'Test',
        created_at: { isoformat: () => '2023-12-01T10:30:00.000Z' },
      };

      const transformed = transformer.transformResponse(response);
      expect(transformed.id).toBe('123e4567-e89b-12d3-a456-426614174000');
      expect(transformed.created_at).toBe('2023-12-01T10:30:00.000Z');
    });
  });
});
