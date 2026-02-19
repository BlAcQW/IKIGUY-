import { describe, it, expect } from 'vitest'
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
} from '@/lib/type-conversions'

describe('Type Conversion Utilities', () => {
	describe('serializeUUID', () => {
		it('converts UUID object to string', () => {
			const uuidObj = { toString: () => '123e4567-e89b-12d3-a456-426614174000' }
			const result = serializeUUID(uuidObj)
			expect(result).toBe('123e4567-e89b-12d3-a456-426614174000')
		})

		it('returns string as-is', () => {
			const uuidString = '123e4567-e89b-12d3-a456-426614174000'
			const result = serializeUUID(uuidString)
			expect(result).toBe(uuidString)
		})

		it('handles null and undefined', () => {
			expect(serializeUUID(null)).toBeNull()
			expect(serializeUUID(undefined)).toBeUndefined()
		})
	})

	describe('serializeDateTime', () => {
		it('converts Date object to ISO string', () => {
			const date = new Date('2024-01-01T00:00:00Z')
			const result = serializeDateTime(date)
			expect(result).toBe('2024-01-01T00:00:00.000Z')
		})

		it('converts datetime object with isoformat method', () => {
			const datetimeObj = { isoformat: () => '2024-01-01T00:00:00Z' }
			const result = serializeDateTime(datetimeObj)
			expect(result).toBe('2024-01-01T00:00:00Z')
		})

		it('returns string as-is', () => {
			const dateString = '2024-01-01T00:00:00Z'
			const result = serializeDateTime(dateString)
			expect(result).toBe(dateString)
		})

		it('handles null and undefined', () => {
			expect(serializeDateTime(null)).toBeNull()
			expect(serializeDateTime(undefined)).toBeUndefined()
		})
	})

	describe('serializeDecimal', () => {
		it('converts Decimal object to number', () => {
			const decimalObj = { toNumber: () => 123.45 }
			const result = serializeDecimal(decimalObj)
			expect(result).toBe(123.45)
		})

		it('converts string to number', () => {
			const decimalString = '123.45'
			const result = serializeDecimal(decimalString)
			expect(result).toBe(123.45)
		})

		it('returns number as-is', () => {
			const decimalNumber = 123.45
			const result = serializeDecimal(decimalNumber)
			expect(result).toBe(decimalNumber)
		})

		it('handles null and undefined', () => {
			expect(serializeDecimal(null)).toBeNull()
			expect(serializeDecimal(undefined)).toBeUndefined()
		})
	})

	describe('transformResponse', () => {
		it('transforms object with UUID and datetime fields', () => {
			const input = {
				id: { toString: () => '123e4567-e89b-12d3-a456-426614174000' },
				created_at: { isoformat: () => '2024-01-01T00:00:00Z' },
				updated_at: { isoformat: () => '2024-01-02T00:00:00Z' },
				amount: { toNumber: () => 123.45 },
				name: 'Test Item',
			}

			const result = transformResponse(input)

			expect(result).toEqual({
				id: '123e4567-e89b-12d3-a456-426614174000',
				created_at: '2024-01-01T00:00:00Z',
				updated_at: '2024-01-02T00:00:00Z',
				amount: 123.45,
				name: 'Test Item',
			})
		})

		it('transforms nested objects', () => {
			const input = {
				id: { toString: () => '123e4567-e89b-12d3-a456-426614174000' },
				assistant: {
					id: { toString: () => '456e7890-e89b-12d3-a456-426614174000' },
					created_at: { isoformat: () => '2024-01-01T00:00:00Z' },
				},
			}

			const result = transformResponse(input)

			expect(result).toEqual({
				id: '123e4567-e89b-12d3-a456-426614174000',
				assistant: {
					id: '456e7890-e89b-12d3-a456-426614174000',
					created_at: '2024-01-01T00:00:00Z',
				},
			})
		})

		it('transforms arrays', () => {
			const input = {
				id: { toString: () => '123e4567-e89b-12d3-a456-426614174000' },
				items: [
					{ id: { toString: () => 'item1' }, created_at: { isoformat: () => '2024-01-01T00:00:00Z' } },
					{ id: { toString: () => 'item2' }, created_at: { isoformat: () => '2024-01-02T00:00:00Z' } },
				],
			}

			const result = transformResponse(input)

			expect(result).toEqual({
				id: '123e4567-e89b-12d3-a456-426614174000',
				items: [
					{ id: 'item1', created_at: '2024-01-01T00:00:00Z' },
					{ id: 'item2', created_at: '2024-01-02T00:00:00Z' },
				],
			})
		})

		it('handles null and undefined values', () => {
			const input = {
				id: { toString: () => '123e4567-e89b-12d3-a456-426614174000' },
				created_at: null,
				updated_at: undefined,
				amount: null,
			}

			const result = transformResponse(input)

			expect(result).toEqual({
				id: '123e4567-e89b-12d3-a456-426614174000',
				created_at: null,
				updated_at: undefined,
				amount: null,
			})
		})
	})

	describe('transformResponseArray', () => {
		it('transforms array of objects', () => {
			const input = [
				{
					id: { toString: () => '123e4567-e89b-12d3-a456-426614174000' },
					created_at: { isoformat: () => '2024-01-01T00:00:00Z' },
				},
				{
					id: { toString: () => '456e7890-e89b-12d3-a456-426614174000' },
					created_at: { isoformat: () => '2024-01-02T00:00:00Z' },
				},
			]

			const result = transformResponseArray(input)

			expect(result).toEqual([
				{
					id: '123e4567-e89b-12d3-a456-426614174000',
					created_at: '2024-01-01T00:00:00Z',
				},
				{
					id: '456e7890-e89b-12d3-a456-426614174000',
					created_at: '2024-01-02T00:00:00Z',
				},
			])
		})

		it('handles empty array', () => {
			const result = transformResponseArray([])
			expect(result).toEqual([])
		})

		it('handles null and undefined', () => {
			expect(transformResponseArray(null)).toBeNull()
			expect(transformResponseArray(undefined)).toBeUndefined()
		})
	})

	describe('transformRequest', () => {
		it('transforms request object for API calls', () => {
			const input = {
				id: '123e4567-e89b-12d3-a456-426614174000',
				created_at: '2024-01-01T00:00:00Z',
				amount: 123.45,
				name: 'Test Item',
			}

			const result = transformRequest(input)

			// Request transformation should be minimal since we're sending to API
			expect(result).toEqual(input)
		})

		it('handles nested objects in requests', () => {
			const input = {
				id: '123e4567-e89b-12d3-a456-426614174000',
				assistant: {
					id: '456e7890-e89b-12d3-a456-426614174000',
					name: 'Test Assistant',
				},
			}

			const result = transformRequest(input)

			expect(result).toEqual(input)
		})
	})

	describe('hasUUIDProperties', () => {
		it('identifies UUID properties correctly', () => {
			expect(hasUUIDProperties('id')).toBe(true)
			expect(hasUUIDProperties('user_id')).toBe(true)
			expect(hasUUIDProperties('assistant_id')).toBe(true)
			expect(hasUUIDProperties('campaign_id')).toBe(true)
			expect(hasUUIDProperties('tenant_id')).toBe(true)
		})

		it('identifies non-UUID properties correctly', () => {
			expect(hasUUIDProperties('name')).toBe(false)
			expect(hasUUIDProperties('description')).toBe(false)
			expect(hasUUIDProperties('status')).toBe(false)
			expect(hasUUIDProperties('type')).toBe(false)
		})
	})

	describe('hasDateTimeProperties', () => {
		it('identifies datetime properties correctly', () => {
			expect(hasDateTimeProperties('created_at')).toBe(true)
			expect(hasDateTimeProperties('updated_at')).toBe(true)
			expect(hasDateTimeProperties('start_date')).toBe(true)
			expect(hasDateTimeProperties('end_date')).toBe(true)
			expect(hasDateTimeProperties('last_login')).toBe(true)
		})

		it('identifies non-datetime properties correctly', () => {
			expect(hasDateTimeProperties('name')).toBe(false)
			expect(hasDateTimeProperties('description')).toBe(false)
			expect(hasDateTimeProperties('status')).toBe(false)
			expect(hasDateTimeProperties('type')).toBe(false)
		})
	})

	describe('createTransformer', () => {
		it('creates custom transformer function', () => {
			const customTransform = createTransformer({
				uuidFields: ['custom_id'],
				datetimeFields: ['custom_date'],
				decimalFields: ['custom_amount'],
			})

			const input = {
				custom_id: { toString: () => '123e4567-e89b-12d3-a456-426614174000' },
				custom_date: { isoformat: () => '2024-01-01T00:00:00Z' },
				custom_amount: { toNumber: () => 123.45 },
				name: 'Test Item',
			}

			const result = customTransform(input)

			expect(result).toEqual({
				custom_id: '123e4567-e89b-12d3-a456-426614174000',
				custom_date: '2024-01-01T00:00:00Z',
				custom_amount: 123.45,
				name: 'Test Item',
			})
		})

		it('handles empty configuration', () => {
			const customTransform = createTransformer({})
			const input = { name: 'Test Item' }

			const result = customTransform(input)

			expect(result).toEqual(input)
		})
	})

	describe('Edge Cases', () => {
		it('handles circular references', () => {
			const input: any = { name: 'Test' }
			input.self = input

			// Should not throw error
			expect(() => transformResponse(input)).not.toThrow()
		})

		it('handles very deep nesting', () => {
			const input = {
				level1: {
					level2: {
						level3: {
							level4: {
								level5: {
									id: { toString: () => 'deep-id' },
									created_at: { isoformat: () => '2024-01-01T00:00:00Z' },
								},
							},
						},
					},
				},
			}

			const result = transformResponse(input)

			expect(result.level1.level2.level3.level4.level5.id).toBe('deep-id')
			expect(result.level1.level2.level3.level4.level5.created_at).toBe('2024-01-01T00:00:00Z')
		})

		it('handles mixed data types', () => {
			const input = {
				id: { toString: () => '123e4567-e89b-12d3-a456-426614174000' },
				created_at: { isoformat: () => '2024-01-01T00:00:00Z' },
				amount: { toNumber: () => 123.45 },
				name: 'Test Item',
				active: true,
				count: 42,
				tags: ['tag1', 'tag2'],
				metadata: { key: 'value' },
			}

			const result = transformResponse(input)

			expect(result).toEqual({
				id: '123e4567-e89b-12d3-a456-426614174000',
				created_at: '2024-01-01T00:00:00Z',
				amount: 123.45,
				name: 'Test Item',
				active: true,
				count: 42,
				tags: ['tag1', 'tag2'],
				metadata: { key: 'value' },
			})
		})
	})
})
