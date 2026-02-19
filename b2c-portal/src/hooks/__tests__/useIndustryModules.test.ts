/**
 * Unit tests for B2C Portal Industry Module Hooks
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useIndustryModules, useAvailableIndustries } from '../useIndustryModules';
import { industryModuleApi } from '@/lib/core-api';

// Mock the core API
jest.mock('@/lib/core-api', () => ({
	industryModuleApi: {
		initializeModule: jest.fn(),
		executeModuleCapability: jest.fn(),
		executeModuleWorkflow: jest.fn(),
		getIndustryAnalytics: jest.fn(),
		getModuleCapabilities: jest.fn(),
		getModuleWorkflows: jest.fn(),
		getModuleCompliance: jest.fn(),
		getModuleHealth: jest.fn(),
		getAvailableIndustries: jest.fn(),
	},
}));

// Mock the auth hook
jest.mock('../useAuth', () => ({
	useAuth: () => ({
		user: {
			tenant_id: 'test-tenant-123',
		},
	}),
}));

describe('useIndustryModules', () => {
	beforeEach(() => {
		jest.clearAllMocks();
	});

	describe('useRealEstateModule', () => {
		it('should initialize module successfully', async () => {
			const mockInitResponse = {
				status: 'success',
				module_id: 'real-estate-123',
				capabilities: [
					{
						id: 'cap-1',
						name: 'Property Search',
						description: 'Search for properties',
						category: 'search',
						parameters: {},
						estimated_duration: 30,
						required_integrations: ['database'],
					},
				],
			};

			(industryModuleApi.initializeModule as jest.Mock).mockResolvedValue(mockInitResponse);

			const { result } = renderHook(() => useIndustryModules.useRealEstateModule());

			await act(async () => {
				const response = await result.current.initializeModule({ api_key: 'test' });
				expect(response).toEqual(mockInitResponse);
			});

			expect(industryModuleApi.initializeModule).toHaveBeenCalledWith(
				'test-tenant-123',
				'real_estate',
				{ api_key: 'test' }
			);
			expect(result.current.isInitialized).toBe(true);
			expect(result.current.capabilities).toEqual(mockInitResponse.capabilities);
		});

		it('should execute capability successfully', async () => {
			const mockCapabilityResponse = {
				success: true,
				data: { properties: [] },
			};

			(industryModuleApi.executeModuleCapability as jest.Mock).mockResolvedValue(mockCapabilityResponse);

			const { result } = renderHook(() => useIndustryModules.useRealEstateModule());

			await act(async () => {
				const response = await result.current.executeCapability('property_search', { location: 'Accra' });
				expect(response).toEqual(mockCapabilityResponse);
			});

			expect(industryModuleApi.executeModuleCapability).toHaveBeenCalledWith(
				'test-tenant-123',
				'real_estate',
				'property_search',
				{ location: 'Accra' }
			);
		});

		it('should execute workflow successfully', async () => {
			const mockWorkflowResponse = {
				success: true,
				data: { workflow_id: 'workflow-123', status: 'completed' },
			};

			(industryModuleApi.executeModuleWorkflow as jest.Mock).mockResolvedValue(mockWorkflowResponse);

			const { result } = renderHook(() => useIndustryModules.useRealEstateModule());

			await act(async () => {
				const response = await result.current.executeWorkflow('lead_generation', { campaign: 'spring2024' });
				expect(response).toEqual(mockWorkflowResponse);
			});

			expect(industryModuleApi.executeModuleWorkflow).toHaveBeenCalledWith(
				'test-tenant-123',
				'real_estate',
				'lead_generation',
				{ campaign: 'spring2024' }
			);
		});

		it('should get analytics successfully', async () => {
			const mockAnalyticsResponse = {
				module_name: 'real_estate',
				metrics: { total_properties: 150, avg_price: 250000 },
				time_series: [],
				insights: ['Market is growing'],
				recommendations: ['Increase marketing budget'],
			};

			(industryModuleApi.getIndustryAnalytics as jest.Mock).mockResolvedValue(mockAnalyticsResponse);

			const { result } = renderHook(() => useIndustryModules.useRealEstateModule());

			await act(async () => {
				const response = await result.current.getAnalytics(['performance', 'usage'], '30d');
				expect(response).toEqual(mockAnalyticsResponse);
			});

			expect(industryModuleApi.getIndustryAnalytics).toHaveBeenCalledWith(
				'test-tenant-123',
				'real_estate',
				['performance', 'usage'],
				'30d',
				undefined
			);
		});

		it('should handle errors gracefully', async () => {
			const errorMessage = 'API Error';
			(industryModuleApi.initializeModule as jest.Mock).mockRejectedValue(new Error(errorMessage));

			const { result } = renderHook(() => useIndustryModules.useRealEstateModule());

			await act(async () => {
				const response = await result.current.initializeModule();
				expect(response).toBeNull();
			});

			expect(result.current.error).toBe(errorMessage);
			expect(result.current.isInitialized).toBe(false);
		});
	});

	describe('useEducationModule', () => {
		it('should initialize education module', async () => {
			const mockInitResponse = {
				status: 'success',
				module_id: 'education-123',
				capabilities: [],
			};

			(industryModuleApi.initializeModule as jest.Mock).mockResolvedValue(mockInitResponse);

			const { result } = renderHook(() => useIndustryModules.useEducationModule());

			await act(async () => {
				const response = await result.current.initializeModule();
				expect(response).toEqual(mockInitResponse);
			});

			expect(industryModuleApi.initializeModule).toHaveBeenCalledWith(
				'test-tenant-123',
				'education',
				{}
			);
		});
	});

	describe('useAvailableIndustries', () => {
		it('should load available industries successfully', async () => {
			const mockIndustries = [
				{
					id: 'real_estate',
					name: 'Real Estate',
					description: 'Property management and sales',
					capabilities: ['property_search', 'lead_generation'],
				},
				{
					id: 'education',
					name: 'Education',
					description: 'Educational institutions',
					capabilities: ['student_management', 'course_tracking'],
				},
			];

			(industryModuleApi.getAvailableIndustries as jest.Mock).mockResolvedValue(mockIndustries);

			const { result } = renderHook(() => useAvailableIndustries());

			await waitFor(() => {
				expect(result.current.isLoading).toBe(false);
			});

			expect(result.current.industries).toEqual(mockIndustries);
			expect(result.current.error).toBeNull();
		});

		it('should handle loading error', async () => {
			const errorMessage = 'Failed to load industries';
			(industryModuleApi.getAvailableIndustries as jest.Mock).mockRejectedValue(new Error(errorMessage));

			const { result } = renderHook(() => useAvailableIndustries());

			await waitFor(() => {
				expect(result.current.isLoading).toBe(false);
			});

			expect(result.current.error).toBe(errorMessage);
			expect(result.current.industries).toEqual([]);
		});

		it('should reload industries', async () => {
			const mockIndustries = [
				{
					id: 'real_estate',
					name: 'Real Estate',
					description: 'Property management and sales',
					capabilities: ['property_search'],
				},
			];

			(industryModuleApi.getAvailableIndustries as jest.Mock).mockResolvedValue(mockIndustries);

			const { result } = renderHook(() => useAvailableIndustries());

			await waitFor(() => {
				expect(result.current.isLoading).toBe(false);
			});

			// Clear mock and reload
			jest.clearAllMocks();
			(industryModuleApi.getAvailableIndustries as jest.Mock).mockResolvedValue(mockIndustries);

			await act(async () => {
				await result.current.reload();
			});

			expect(industryModuleApi.getAvailableIndustries).toHaveBeenCalledTimes(1);
		});
	});
});
