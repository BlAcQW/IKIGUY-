/**
 * Type Conversion Utilities for B2C Portal
 * 
 * This module provides utilities for converting between frontend and backend data types,
 * particularly for UUID and datetime handling.
 */

/**
 * Convert a UUID object or string to a string representation
 * @param uuid - UUID object or string
 * @returns string representation of the UUID
 */
export function serializeUUID(uuid: string | { toString(): string }): string {
  if (typeof uuid === 'string') {
    return uuid;
  }
  return uuid.toString();
}

/**
 * Convert a datetime object or string to ISO string format
 * @param datetime - datetime object or string
 * @returns ISO string representation
 */
export function serializeDateTime(datetime: string | Date | { isoformat(): string }): string {
  if (typeof datetime === 'string') {
    return datetime;
  }
  
  if (datetime instanceof Date) {
    return datetime.toISOString();
  }
  
  // Handle Python datetime-like objects with isoformat method
  if (typeof datetime === 'object' && 'isoformat' in datetime) {
    return (datetime as { isoformat(): string }).isoformat();
  }
  
  // Fallback: try to convert to string and parse as ISO
  const dateStr = String(datetime);
  try {
    return new Date(dateStr).toISOString();
  } catch {
    return dateStr;
  }
}

/**
 * Convert a decimal/number to a number with proper precision
 * @param decimal - decimal object or number
 * @returns number representation
 */
export function serializeDecimal(decimal: number | string | { __float__(): number }): number {
  if (typeof decimal === 'number') {
    return decimal;
  }
  
  if (typeof decimal === 'string') {
    return parseFloat(decimal);
  }
  
  // Handle Python Decimal-like objects
  if (typeof decimal === 'object' && '__float__' in decimal) {
    return (decimal as { __float__(): number }).__float__();
  }
  
  // Fallback: try to convert to number
  return Number(decimal);
}

/**
 * Transform a backend response object to frontend format
 * @param obj - backend response object
 * @returns transformed object with proper types
 */
export function transformResponse<T extends Record<string, any>>(obj: T): T {
  const transformed = { ...obj };

  for (const [key, value] of Object.entries(transformed)) {
    if (value === null || value === undefined) {
      continue;
    }

    // Handle arrays recursively
    if (Array.isArray(value)) {
      transformed[key] = transformResponseArray(value);
      continue;
    }

    // Handle nested objects recursively
    if (typeof value === 'object' && value.constructor === Object) {
      // Only transform plain objects, not special types like Date
      transformed[key] = transformResponse(value);
      continue;
    }

    // Convert UUID fields (common patterns)
    if (key.includes('id') && typeof value === 'object' && 'toString' in value) {
      transformed[key] = serializeUUID(value);
      continue;
    }

    // Convert datetime fields (common patterns)
    if (key.includes('_at') || key.includes('date') || key.includes('time')) {
      transformed[key] = serializeDateTime(value);
      continue;
    }

    // Convert decimal/numeric fields
    if (key.includes('cost') || key.includes('price') || key.includes('amount') || key.includes('balance')) {
      transformed[key] = serializeDecimal(value);
      continue;
    }
  }

  return transformed;
}

/**
 * Transform an array of backend response objects
 * @param array - array of backend response objects
 * @returns transformed array
 */
export function transformResponseArray<T extends Record<string, any>>(array: T[]): T[] {
  if (!Array.isArray(array)) {
    console.warn('transformResponseArray called with non-array:', array);
    return array;
  }

  return array.map((item) => {
    // Only transform plain objects
    if (item && typeof item === 'object' && item.constructor === Object) {
      return transformResponse(item);
    }
    // Return primitives and special objects as-is
    return item;
  });
}

/**
 * Transform request data for backend consumption
 * @param obj - frontend request object
 * @returns transformed object for backend
 */
export function transformRequest<T extends Record<string, any>>(obj: T): T {
  const transformed = { ...obj };
  
  for (const [key, value] of Object.entries(transformed)) {
    if (value === null || value === undefined) {
      continue;
    }
    
    // Ensure UUIDs are strings
    if (key.includes('id') && typeof value === 'string') {
      // Validate UUID format
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
      if (!uuidRegex.test(value)) {
        throw new Error(`Invalid UUID format for field ${key}: ${value}`);
      }
    }
    
    // Ensure dates are ISO strings
    if (key.includes('_at') || key.includes('date') || key.includes('time')) {
      if (value instanceof Date) {
        transformed[key] = value.toISOString();
      } else if (typeof value === 'string') {
        // Validate ISO date format
        const date = new Date(value);
        if (isNaN(date.getTime())) {
          throw new Error(`Invalid date format for field ${key}: ${value}`);
        }
      }
    }
    
    // Ensure numbers are numbers
    if (key.includes('cost') || key.includes('price') || key.includes('amount') || key.includes('balance')) {
      const num = Number(value);
      if (isNaN(num)) {
        throw new Error(`Invalid number format for field ${key}: ${value}`);
      }
      transformed[key] = num;
    }
  }
  
  return transformed;
}

/**
 * Type guard to check if an object has UUID-like properties
 */
export function hasUUIDProperties(obj: any): obj is { id: string | { toString(): string } } {
  return obj && typeof obj === 'object' && 'id' in obj;
}

/**
 * Type guard to check if an object has datetime-like properties
 */
export function hasDateTimeProperties(obj: any): obj is { created_at?: any; updated_at?: any } {
  return obj && typeof obj === 'object' && ('created_at' in obj || 'updated_at' in obj);
}

/**
 * Create a type-safe transformer for specific data types
 */
export function createTransformer<T extends Record<string, any>>() {
  return {
    transformResponse: (obj: T): T => transformResponse(obj),
    transformResponseArray: (array: T[]): T[] => transformResponseArray(array),
    transformRequest: (obj: Partial<T>): Partial<T> => transformRequest(obj),
  };
}
