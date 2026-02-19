/**
 * Industry Module Hooks for B2C Portal
 * 
 * These hooks provide easy access to industry-specific module functionality
 * through the Core Backend API. Each hook is tailored to a specific industry
 * and provides common operations like initialization, capability execution,
 * workflow management, and analytics.
 */

import { useState, useEffect, useCallback } from 'react';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import {
	industryModuleApi,
	IndustryModuleCapability,
	IndustryModuleWorkflow,
	IndustryModuleAnalytics,
	IndustryModuleCompliance,
	IndustryModuleHealth
} from '@/lib/core-api';

// Base hook for industry module operations
function useIndustryModule(industry: string) {
	const { user, getTenantId } = useMongoAuth();
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [isInitialized, setIsInitialized] = useState(false);
	const [capabilities, setCapabilities] = useState<IndustryModuleCapability[]>([]);
	const [workflows, setWorkflows] = useState<IndustryModuleWorkflow[]>([]);

	const tenantId = getTenantId();

	// Initialize the module
	const initializeModule = useCallback(async (settings: Record<string, any> = {}) => {
		if (!tenantId) {
			setError('No tenant ID available');
			return null;
		}

		setIsLoading(true);
		setError(null);

		try {
			const result = await industryModuleApi.initializeModule(tenantId, industry, settings);
			setIsInitialized(true);
			setCapabilities(result.capabilities || []);
			return result;
		} catch (err) {
			const errorMessage = err instanceof Error ? err.message : 'Failed to initialize module';
			setError(errorMessage);
			return null;
		} finally {
			setIsLoading(false);
		}
	}, [tenantId, industry]);

	// Execute a capability
	const executeCapability = useCallback(async (capability: string, params: Record<string, any> = {}) => {
		if (!tenantId) {
			setError('No tenant ID available');
			return null;
		}

		setIsLoading(true);
		setError(null);

		try {
			const result = await industryModuleApi.executeModuleCapability(tenantId, industry, capability, params);
			return result;
		} catch (err) {
			const errorMessage = err instanceof Error ? err.message : 'Failed to execute capability';
			setError(errorMessage);
			return null;
		} finally {
			setIsLoading(false);
		}
	}, [tenantId, industry]);

	// Execute a workflow
	const executeWorkflow = useCallback(async (workflow: string, params: Record<string, any> = {}) => {
		if (!tenantId) {
			setError('No tenant ID available');
			return null;
		}

		setIsLoading(true);
		setError(null);

		try {
			const result = await industryModuleApi.executeModuleWorkflow(tenantId, industry, workflow, params);
			return result;
		} catch (err) {
			const errorMessage = err instanceof Error ? err.message : 'Failed to execute workflow';
			setError(errorMessage);
			return null;
		} finally {
			setIsLoading(false);
		}
	}, [tenantId, industry]);

	// Get analytics
	const getAnalytics = useCallback(async (
		metrics: string[] = ['performance', 'usage', 'efficiency'],
		timeRange: string = '7d',
		filters?: Record<string, any>
	) => {
		if (!tenantId) {
			setError('No tenant ID available');
			return null;
		}

		setIsLoading(true);
		setError(null);

		try {
			const result = await industryModuleApi.getIndustryAnalytics(tenantId, industry, metrics, timeRange, filters);
			return result;
		} catch (err) {
			const errorMessage = err instanceof Error ? err.message : 'Failed to get analytics';
			setError(errorMessage);
			return null;
		} finally {
			setIsLoading(false);
		}
	}, [tenantId, industry]);

	// Get compliance information
	const getCompliance = useCallback(async () => {
		if (!tenantId) {
			setError('No tenant ID available');
			return null;
		}

		setIsLoading(true);
		setError(null);

		try {
			const result = await industryModuleApi.getModuleCompliance(tenantId, industry);
			return result;
		} catch (err) {
			const errorMessage = err instanceof Error ? err.message : 'Failed to get compliance information';
			setError(errorMessage);
			return null;
		} finally {
			setIsLoading(false);
		}
	}, [tenantId, industry]);

	// Get health status
	const getHealth = useCallback(async () => {
		if (!tenantId) {
			setError('No tenant ID available');
			return null;
		}

		setIsLoading(true);
		setError(null);

		try {
			const result = await industryModuleApi.getModuleHealth(tenantId, industry);
			return result;
		} catch (err) {
			const errorMessage = err instanceof Error ? err.message : 'Failed to get health status';
			setError(errorMessage);
			return null;
		} finally {
			setIsLoading(false);
		}
	}, [tenantId, industry]);

	// Load capabilities and workflows on mount
	useEffect(() => {
		if (tenantId && isInitialized) {
			const loadModuleData = async () => {
				try {
					const [capabilitiesData, workflowsData] = await Promise.all([
						industryModuleApi.getModuleCapabilities(tenantId, industry),
						industryModuleApi.getModuleWorkflows(tenantId, industry)
					]);
					setCapabilities(capabilitiesData);
					setWorkflows(workflowsData);
				} catch (err) {
					console.error('Failed to load module data:', err);
				}
			};

			loadModuleData();
		}
	}, [tenantId, industry, isInitialized]);

	return {
		isLoading,
		error,
		isInitialized,
		capabilities,
		workflows,
		initializeModule,
		executeCapability,
		executeWorkflow,
		getAnalytics,
		getCompliance,
		getHealth,
	};
}

// Industry-specific hooks
export function useRealEstateModule(tenantId?: string) {
	return useIndustryModule('real_estate');
}

export function useEducationModule(tenantId?: string) {
	return useIndustryModule('education');
}

export function useProfessionalServicesModule(tenantId?: string) {
	return useIndustryModule('professional_services');
}

export function useAutomotiveModule(tenantId?: string) {
	return useIndustryModule('automotive');
}

export function useHospitalityModule(tenantId?: string) {
	return useIndustryModule('hospitality');
}

export function useUtilitiesModule(tenantId?: string) {
	return useIndustryModule('utilities');
}

export function useGovernmentModule(tenantId?: string) {
	return useIndustryModule('government');
}

// Hook to get available industries
export function useAvailableIndustries() {
	const [industries, setIndustries] = useState<Array<{ id: string; name: string; description: string; capabilities: string[] }>>([]);
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const loadIndustries = useCallback(async () => {
		setIsLoading(true);
		setError(null);

		try {
			const result = await industryModuleApi.getAvailableIndustries();
			setIndustries(result);
		} catch (err) {
			const errorMessage = err instanceof Error ? err.message : 'Failed to load available industries';
			setError(errorMessage);
		} finally {
			setIsLoading(false);
		}
	}, []);

	useEffect(() => {
		loadIndustries();
	}, [loadIndustries]);

	return {
		industries,
		isLoading,
		error,
		reload: loadIndustries,
	};
}
