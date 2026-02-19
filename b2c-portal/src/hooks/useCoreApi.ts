/**
 * React hooks for Core Backend API integration
 * 
 * These hooks provide a clean interface for B2C Portal components to interact
 * with the Core Backend's internal APIs.
 */

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';
import {
	coreApi,
	Assistant,
	AssistantCreate,
	Campaign,
	CampaignCreate,
	LicenseInfo,
	UsageData,
	WalletBalance,
	PaymentMethod
} from '@/lib/core-api.ts';

/**
 * Hook for assistant management
 */
export function useAssistants(tenantId: string) {
	const queryClient = useQueryClient();
	const { toast } = useToast();

	// Query for listing assistants
	const {
		data: assistants = [],
		isLoading: isLoadingAssistants,
		error: assistantsError,
		refetch: refetchAssistants
	} = useQuery({
		queryKey: ['assistants', tenantId],
		queryFn: () => coreApi.assistant.list(tenantId),
		enabled: !!tenantId,
	});

	// Mutation for creating assistant
	const createAssistantMutation = useMutation({
		mutationFn: (assistant: AssistantCreate) => coreApi.assistant.create(assistant),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ['assistants', tenantId] });
			toast({
				title: "Success",
				description: "Assistant created successfully",
			});
		},
		onError: (error) => {
			toast({
				title: "Error",
				description: `Failed to create assistant: ${error.message}`,
				variant: "destructive",
			});
		},
	});

	// Mutation for getting assistant by ID
	const getAssistantMutation = useMutation({
		mutationFn: (id: string) => coreApi.assistant.get(id),
	});

	return {
		assistants,
		isLoadingAssistants,
		assistantsError,
		refetchAssistants,
		createAssistant: createAssistantMutation.mutate,
		createAssistantAsync: createAssistantMutation.mutateAsync,
		isCreatingAssistant: createAssistantMutation.isPending,
		getAssistant: getAssistantMutation.mutate,
		getAssistantAsync: getAssistantMutation.mutateAsync,
		isGettingAssistant: getAssistantMutation.isPending,
	};
}

/**
 * Hook for campaign management
 */
export function useCampaigns(tenantId: string) {
	const queryClient = useQueryClient();
	const { toast } = useToast();

	// Query for listing campaigns
	const {
		data: campaigns = [],
		isLoading: isLoadingCampaigns,
		error: campaignsError,
		refetch: refetchCampaigns
	} = useQuery({
		queryKey: ['campaigns', tenantId],
		queryFn: () => coreApi.campaign.list(tenantId),
		enabled: !!tenantId,
	});

	// Mutation for creating campaign
	const createCampaignMutation = useMutation({
		mutationFn: (campaign: CampaignCreate) => coreApi.campaign.create(campaign),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ['campaigns', tenantId] });
			toast({
				title: "Success",
				description: "Campaign created successfully",
			});
		},
		onError: (error) => {
			toast({
				title: "Error",
				description: `Failed to create campaign: ${error.message}`,
				variant: "destructive",
			});
		},
	});

	// Mutation for getting campaign by ID
	const getCampaignMutation = useMutation({
		mutationFn: (id: string) => coreApi.campaign.get(id),
	});

	return {
		campaigns,
		isLoadingCampaigns,
		campaignsError,
		refetchCampaigns,
		createCampaign: createCampaignMutation.mutate,
		createCampaignAsync: createCampaignMutation.mutateAsync,
		isCreatingCampaign: createCampaignMutation.isPending,
		getCampaign: getCampaignMutation.mutate,
		getCampaignAsync: getCampaignMutation.mutateAsync,
		isGettingCampaign: getCampaignMutation.isPending,
	};
}

/**
 * Hook for license management
 */
export function useLicense(tenantId: string) {
	const { toast } = useToast();

	// Query for license status
	const {
		data: licenseInfo,
		isLoading: isLoadingLicense,
		error: licenseError,
		refetch: refetchLicense
	} = useQuery({
		queryKey: ['license', tenantId],
		queryFn: () => coreApi.license.getStatus(tenantId),
		enabled: !!tenantId,
	});

	// Mutation for license verification
	const verifyLicenseMutation = useMutation({
		mutationFn: ({ agents, channels, minutes }: { agents?: number; channels?: number; minutes?: number }) =>
			coreApi.license.verify(tenantId, agents || 0, channels || 0, minutes || 0),
		onError: (error) => {
			toast({
				title: "License Error",
				description: `License verification failed: ${error.message}`,
				variant: "destructive",
			});
		},
	});

	// Mutation for license activation
	const activateLicenseMutation = useMutation({
		mutationFn: ({ licenseKey, features, limits }: { licenseKey: string; features?: Record<string, any>; limits?: Record<string, any> }) =>
			coreApi.license.activate(tenantId, licenseKey, features, limits),
		onSuccess: () => {
			refetchLicense();
			toast({
				title: "Success",
				description: "License activated successfully",
			});
		},
		onError: (error) => {
			toast({
				title: "Error",
				description: `Failed to activate license: ${error.message}`,
				variant: "destructive",
			});
		},
	});

	return {
		licenseInfo,
		isLoadingLicense,
		licenseError,
		refetchLicense,
		verifyLicense: verifyLicenseMutation.mutate,
		verifyLicenseAsync: verifyLicenseMutation.mutateAsync,
		isVerifyingLicense: verifyLicenseMutation.isPending,
		activateLicense: activateLicenseMutation.mutate,
		activateLicenseAsync: activateLicenseMutation.mutateAsync,
		isActivatingLicense: activateLicenseMutation.isPending,
	};
}

/**
 * Hook for usage analytics
 */
export function useUsage(tenantId: string) {
	const { toast } = useToast();

	// Query for usage data
	const {
		data: usageData,
		isLoading: isLoadingUsage,
		error: usageError,
		refetch: refetchUsage
	} = useQuery({
		queryKey: ['usage', tenantId],
		queryFn: () => coreApi.usage.getUsage(tenantId),
		enabled: !!tenantId,
	});

	// Query for usage dashboard
	const {
		data: usageDashboard,
		isLoading: isLoadingDashboard,
		error: dashboardError,
		refetch: refetchDashboard
	} = useQuery({
		queryKey: ['usage-dashboard', tenantId],
		queryFn: () => coreApi.usage.getDashboard(tenantId),
		enabled: !!tenantId,
	});

	return {
		usageData,
		isLoadingUsage,
		usageError,
		refetchUsage,
		usageDashboard,
		isLoadingDashboard,
		dashboardError,
		refetchDashboard,
	};
}

/**
 * Hook for usage data with time range
 */
export function useUsageData(tenantId: string, timeRange?: string) {
	const { toast } = useToast();

	// Query for usage data with time range
	const {
		data: usageData,
		isLoading: isLoadingUsage,
		error: usageError,
		refetch: refetchUsage
	} = useQuery({
		queryKey: ['usage-data', tenantId, timeRange],
		queryFn: () => coreApi.usage.getUsageData(tenantId, timeRange),
		enabled: !!tenantId,
	});

	return {
		data: usageData,
		isLoading: isLoadingUsage,
		error: usageError,
		refetch: refetchUsage,
	};
}

/**
 * Hook for usage summary with time range
 */
export function useUsageSummary(tenantId: string, timeRange?: string) {
	const { toast } = useToast();

	// Query for usage summary with time range
	const {
		data: usageSummary,
		isLoading: isLoadingSummary,
		error: summaryError,
		refetch: refetchSummary
	} = useQuery({
		queryKey: ['usage-summary', tenantId, timeRange],
		queryFn: () => coreApi.usage.getUsageSummary(tenantId),
		enabled: !!tenantId,
	});

	return {
		data: usageSummary,
		isLoading: isLoadingSummary,
		error: summaryError,
		refetch: refetchSummary,
	};
}

/**
 * Hook for payment management
 */
export function usePayments(tenantId: string) {
	const queryClient = useQueryClient();
	const { toast } = useToast();

	// Query for payment methods
	const {
		data: paymentMethods = { methods: [], currency: 'USD' },
		isLoading: isLoadingPaymentMethods,
		error: paymentMethodsError,
		refetch: refetchPaymentMethods
	} = useQuery({
		queryKey: ['payment-methods', tenantId],
		queryFn: () => coreApi.payment.getPaymentMethods(tenantId),
		enabled: !!tenantId,
	});

	// Query for wallet balance
	const {
		data: walletBalance,
		isLoading: isLoadingWallet,
		error: walletError,
		refetch: refetchWallet
	} = useQuery({
		queryKey: ['wallet-balance', tenantId],
		queryFn: () => coreApi.payment.getWalletBalance(tenantId),
		enabled: !!tenantId,
	});

	// Mutation for creating deposit
	const createDepositMutation = useMutation({
		mutationFn: ({ amount, currency, paymentMethodId, description, metadata }: {
			amount: number;
			currency: string;
			paymentMethodId: string;
			description?: string;
			metadata?: Record<string, any>;
		}) => coreApi.payment.createDeposit(tenantId, amount, currency, paymentMethodId, description, metadata),
		onSuccess: () => {
			refetchWallet();
			toast({
				title: "Success",
				description: "Deposit created successfully",
			});
		},
		onError: (error) => {
			toast({
				title: "Error",
				description: `Failed to create deposit: ${error.message}`,
				variant: "destructive",
			});
		},
	});

	// Mutation for mobile money payment
	const mobileMoneyMutation = useMutation({
		mutationFn: ({ transactionId, phoneNumber, provider }: {
			transactionId: string;
			phoneNumber: string;
			provider: string;
		}) => coreApi.payment.processMobileMoney(tenantId, transactionId, phoneNumber, provider),
		onSuccess: () => {
			refetchWallet();
			toast({
				title: "Success",
				description: "Mobile money payment processed successfully",
			});
		},
		onError: (error) => {
			toast({
				title: "Error",
				description: `Failed to process mobile money payment: ${error.message}`,
				variant: "destructive",
			});
		},
	});

	return {
		paymentMethods,
		isLoadingPaymentMethods,
		paymentMethodsError,
		refetchPaymentMethods,
		walletBalance,
		isLoadingWallet,
		walletError,
		refetchWallet,
		createDeposit: createDepositMutation.mutate,
		createDepositAsync: createDepositMutation.mutateAsync,
		isCreatingDeposit: createDepositMutation.isPending,
		processMobileMoney: mobileMoneyMutation.mutate,
		processMobileMoneyAsync: mobileMoneyMutation.mutateAsync,
		isProcessingMobileMoney: mobileMoneyMutation.isPending,
	};
}

/**
 * Hook for knowledge base management
 */
export function useKnowledgeBase(tenantId: string) {
	const { toast } = useToast();

	// Mutation for ingesting content
	const ingestMutation = useMutation({
		mutationFn: ({ content, url }: { content?: string; url?: string }) =>
			coreApi.knowledgeBase.ingest(tenantId, content, url),
		onSuccess: () => {
			toast({
				title: "Success",
				description: "Content ingested successfully",
			});
		},
		onError: (error) => {
			toast({
				title: "Error",
				description: `Failed to ingest content: ${error.message}`,
				variant: "destructive",
			});
		},
	});

	// Mutation for searching knowledge base
	const searchMutation = useMutation({
		mutationFn: ({ query, topK }: { query: string; topK?: number }) =>
			coreApi.knowledgeBase.search({ tenant_id: tenantId, query, top_k: topK }),
		onError: (error) => {
			toast({
				title: "Error",
				description: `Failed to search knowledge base: ${error.message}`,
				variant: "destructive",
			});
		},
	});

	return {
		ingestContent: ingestMutation.mutate,
		ingestContentAsync: ingestMutation.mutateAsync,
		isIngesting: ingestMutation.isPending,
		searchKnowledgeBase: searchMutation.mutate,
		searchKnowledgeBaseAsync: searchMutation.mutateAsync,
		isSearching: searchMutation.isPending,
		searchResults: searchMutation.data,
	};
}

/**
 * Hook for MCP integrations
 */
export function useMCP(tenantId: string) {
	const { toast } = useToast();

	// Mutation for creating CRM lead
	const createCrmLeadMutation = useMutation({
		mutationFn: (leadData: Record<string, any>) => coreApi.mcp.createCrmLead(tenantId, leadData),
		onSuccess: () => {
			toast({
				title: "Success",
				description: "CRM lead created successfully",
			});
		},
		onError: (error) => {
			toast({
				title: "Error",
				description: `Failed to create CRM lead: ${error.message}`,
				variant: "destructive",
			});
		},
	});

	// Mutation for updating CRM contact
	const updateCrmContactMutation = useMutation({
		mutationFn: ({ contactId, contactData }: { contactId: string; contactData: Record<string, any> }) =>
			coreApi.mcp.updateCrmContact(tenantId, contactId, contactData),
		onSuccess: () => {
			toast({
				title: "Success",
				description: "CRM contact updated successfully",
			});
		},
		onError: (error) => {
			toast({
				title: "Error",
				description: `Failed to update CRM contact: ${error.message}`,
				variant: "destructive",
			});
		},
	});

	// Mutation for creating helpdesk ticket
	const createHelpdeskTicketMutation = useMutation({
		mutationFn: (ticketData: Record<string, any>) => coreApi.mcp.createHelpdeskTicket(tenantId, ticketData),
		onSuccess: () => {
			toast({
				title: "Success",
				description: "Helpdesk ticket created successfully",
			});
		},
		onError: (error) => {
			toast({
				title: "Error",
				description: `Failed to create helpdesk ticket: ${error.message}`,
				variant: "destructive",
			});
		},
	});

	// Mutation for processing payment
	const processPaymentMutation = useMutation({
		mutationFn: (paymentData: Record<string, any>) => coreApi.mcp.processPayment(tenantId, paymentData),
		onSuccess: () => {
			toast({
				title: "Success",
				description: "Payment processed successfully",
			});
		},
		onError: (error) => {
			toast({
				title: "Error",
				description: `Failed to process payment: ${error.message}`,
				variant: "destructive",
			});
		},
	});

	return {
		createCrmLead: createCrmLeadMutation.mutate,
		createCrmLeadAsync: createCrmLeadMutation.mutateAsync,
		isCreatingCrmLead: createCrmLeadMutation.isPending,
		updateCrmContact: updateCrmContactMutation.mutate,
		updateCrmContactAsync: updateCrmContactMutation.mutateAsync,
		isUpdatingCrmContact: updateCrmContactMutation.isPending,
		createHelpdeskTicket: createHelpdeskTicketMutation.mutate,
		createHelpdeskTicketAsync: createHelpdeskTicketMutation.mutateAsync,
		isCreatingHelpdeskTicket: createHelpdeskTicketMutation.isPending,
		processPayment: processPaymentMutation.mutate,
		processPaymentAsync: processPaymentMutation.mutateAsync,
		isProcessingPayment: processPaymentMutation.isPending,
	};
}

/**
 * Hook for health check
 */
export function useHealth() {
	const {
		data: healthStatus,
		isLoading: isLoadingHealth,
		error: healthError,
		refetch: refetchHealth
	} = useQuery({
		queryKey: ['health'],
		queryFn: () => coreApi.health.check(),
		refetchInterval: 30000, // Check every 30 seconds
	});

	return {
		healthStatus,
		isLoadingHealth,
		healthError,
		refetchHealth,
	};
}
