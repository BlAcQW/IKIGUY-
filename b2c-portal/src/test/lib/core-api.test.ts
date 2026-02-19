import { describe, it, expect, vi, beforeEach } from 'vitest'
import { assistantApi, campaignApi, knowledgeBaseApi } from '@/lib/core-api'
import { createMockAssistant, createMockCampaign, createMockKnowledgeItem } from '@/test/utils/test-utils'

// Mock fetch globally
global.fetch = vi.fn()

// Mock Supabase
vi.mock('@/integrations/supabase/client', () => ({
	supabase: {
		auth: {
			getSession: vi.fn(),
		},
	},
}))

describe('Core API Client', () => {
	beforeEach(() => {
		vi.clearAllMocks()

		// Mock Supabase session
		const { supabase } = require('@/integrations/supabase/client')
		supabase.auth.getSession.mockResolvedValue({
			data: {
				session: {
					access_token: 'mock-token',
				},
			},
		})
	})

	describe('Assistant API', () => {
		const mockAssistant = createMockAssistant()

		it('creates assistant successfully', async () => {
			const mockResponse = { ...mockAssistant }
			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse),
			})

			const result = await assistantApi.create(mockAssistant)

			expect(result).toEqual(mockResponse)
			expect(global.fetch).toHaveBeenCalledWith(
				expect.stringContaining('/internal/assistants'),
				expect.objectContaining({
					method: 'POST',
					headers: expect.objectContaining({
						'Authorization': 'Bearer mock-token',
						'Content-Type': 'application/json',
					}),
					body: JSON.stringify(mockAssistant),
				})
			)
		})

		it('gets assistant by ID', async () => {
			const mockResponse = { ...mockAssistant }
			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse),
			})

			const result = await assistantApi.get('asst_123')

			expect(result).toEqual(mockResponse)
			expect(global.fetch).toHaveBeenCalledWith(
				expect.stringContaining('/internal/assistants/asst_123'),
				expect.objectContaining({
					method: 'GET',
					headers: expect.objectContaining({
						'Authorization': 'Bearer mock-token',
					}),
				})
			)
		})

		it('lists assistants for tenant', async () => {
			const mockResponse = [mockAssistant]
			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse),
			})

			const result = await assistantApi.list('tenant_123')

			expect(result).toEqual(mockResponse)
			expect(global.fetch).toHaveBeenCalledWith(
				expect.stringContaining('/internal/assistants?tenant_id=tenant_123'),
				expect.objectContaining({
					method: 'GET',
					headers: expect.objectContaining({
						'Authorization': 'Bearer mock-token',
					}),
				})
			)
		})

		it('handles API errors', async () => {
			global.fetch = vi.fn().mockResolvedValue({
				ok: false,
				status: 500,
				json: () => Promise.resolve({ error: 'Server Error' }),
			})

			await expect(assistantApi.create(mockAssistant)).rejects.toThrow('Server Error')
		})

		it('handles network errors', async () => {
			global.fetch = vi.fn().mockRejectedValue(new Error('Network Error'))

			await expect(assistantApi.create(mockAssistant)).rejects.toThrow('Network Error')
		})
	})

	describe('Campaign API', () => {
		const mockCampaign = createMockCampaign()

		it('creates campaign successfully', async () => {
			const mockResponse = { ...mockCampaign }
			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse),
			})

			const result = await campaignApi.create(mockCampaign)

			expect(result).toEqual(mockResponse)
			expect(global.fetch).toHaveBeenCalledWith(
				expect.stringContaining('/internal/campaigns'),
				expect.objectContaining({
					method: 'POST',
					body: JSON.stringify(mockCampaign),
				})
			)
		})

		it('starts campaign', async () => {
			const mockResponse = { success: true }
			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse),
			})

			const result = await campaignApi.start('camp_123')

			expect(result).toEqual(mockResponse)
			expect(global.fetch).toHaveBeenCalledWith(
				expect.stringContaining('/internal/campaigns/camp_123/start'),
				expect.objectContaining({
					method: 'POST',
				})
			)
		})

		it('stops campaign', async () => {
			const mockResponse = { success: true }
			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse),
			})

			const result = await campaignApi.stop('camp_123')

			expect(result).toEqual(mockResponse)
			expect(global.fetch).toHaveBeenCalledWith(
				expect.stringContaining('/internal/campaigns/camp_123/stop'),
				expect.objectContaining({
					method: 'POST',
				})
			)
		})
	})

	describe('Knowledge Base API', () => {
		const mockKnowledgeItem = createMockKnowledgeItem()

		it('creates knowledge item successfully', async () => {
			const mockResponse = { ...mockKnowledgeItem }
			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse),
			})

			const result = await knowledgeBaseApi.create(mockKnowledgeItem)

			expect(result).toEqual(mockResponse)
			expect(global.fetch).toHaveBeenCalledWith(
				expect.stringContaining('/internal/knowledge'),
				expect.objectContaining({
					method: 'POST',
					body: JSON.stringify(mockKnowledgeItem),
				})
			)
		})

		it('uploads document', async () => {
			const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' })
			const mockResponse = { success: true, fileId: 'file_123' }

			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse),
			})

			const result = await knowledgeBaseApi.uploadDocument(mockFile, 'tenant_123')

			expect(result).toEqual(mockResponse)
			expect(global.fetch).toHaveBeenCalledWith(
				expect.stringContaining('/internal/knowledge/upload'),
				expect.objectContaining({
					method: 'POST',
					headers: expect.not.objectContaining({
						'Content-Type': 'application/json',
					}),
				})
			)
		})
	})

	describe('Authentication', () => {
		it('includes authorization header with token', async () => {
			const mockResponse = { success: true }
			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse),
			})

			await assistantApi.list('tenant_123')

			expect(global.fetch).toHaveBeenCalledWith(
				expect.any(String),
				expect.objectContaining({
					headers: expect.objectContaining({
						'Authorization': 'Bearer mock-token',
					}),
				})
			)
		})

		it('handles missing session', async () => {
			const { supabase } = require('@/integrations/supabase/client')
			supabase.auth.getSession.mockResolvedValue({
				data: { session: null },
			})

			global.fetch = vi.fn().mockResolvedValue({
				ok: false,
				status: 401,
				json: () => Promise.resolve({ error: 'Unauthorized' }),
			})

			await expect(assistantApi.list('tenant_123')).rejects.toThrow('Unauthorized')
		})
	})

	describe('Error Handling', () => {
		it('handles 400 errors', async () => {
			global.fetch = vi.fn().mockResolvedValue({
				ok: false,
				status: 400,
				json: () => Promise.resolve({ error: 'Bad Request' }),
			})

			await expect(assistantApi.create({})).rejects.toThrow('Bad Request')
		})

		it('handles 404 errors', async () => {
			global.fetch = vi.fn().mockResolvedValue({
				ok: false,
				status: 404,
				json: () => Promise.resolve({ error: 'Not Found' }),
			})

			await expect(assistantApi.get('nonexistent')).rejects.toThrow('Not Found')
		})

		it('handles 500 errors', async () => {
			global.fetch = vi.fn().mockResolvedValue({
				ok: false,
				status: 500,
				json: () => Promise.resolve({ error: 'Internal Server Error' }),
			})

			await expect(assistantApi.create({})).rejects.toThrow('Internal Server Error')
		})

		it('handles JSON parsing errors', async () => {
			global.fetch = vi.fn().mockResolvedValue({
				ok: false,
				status: 500,
				json: () => Promise.reject(new Error('Invalid JSON')),
			})

			await expect(assistantApi.create({})).rejects.toThrow('Invalid JSON')
		})
	})
})
