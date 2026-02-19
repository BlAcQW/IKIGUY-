/**
 * React Query Hooks for Campaign Management
 *
 * Provides type-safe hooks for campaign operations including:
 * - Campaign CRUD operations
 * - Contact management
 * - Segment preview
 * - Campaign analytics
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  Campaign,
  CampaignCreate,
  CampaignType,
  CampaignStatus,
  Contact,
  ContactCreate,
  ContactUpdate,
  SegmentFilter,
  CampaignAnalytics,
  createCampaign,
  getCampaigns,
  getCampaign,
  deleteCampaign,
  launchCampaign,
  pauseCampaign,
  getCampaignAnalytics,
  createContact,
  getContacts,
  getContact,
  updateContact,
  deleteContact,
  importContacts,
  previewSegment,
} from '@/lib/api/campaign-api';

// ==================== Campaign Hooks ====================

export interface UseCampaignsParams {
  campaign_type?: CampaignType;
  status?: CampaignStatus;
  limit?: number;
  offset?: number;
}

/**
 * Hook to fetch campaigns list with optional filters
 */
export function useCampaigns(params?: UseCampaignsParams) {
  return useQuery({
    queryKey: ['campaigns', params],
    queryFn: () => getCampaigns(params),
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Hook to fetch a single campaign by ID
 */
export function useCampaign(campaignId: string | undefined) {
  return useQuery({
    queryKey: ['campaigns', campaignId],
    queryFn: () => {
      if (!campaignId) throw new Error('Campaign ID required');
      return getCampaign(campaignId);
    },
    enabled: !!campaignId,
  });
}

/**
 * Hook to create a new campaign
 */
export function useCreateCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CampaignCreate) => createCampaign(data),
    onSuccess: (newCampaign) => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      toast.success(`Campaign "${newCampaign.name}" created successfully`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to create campaign: ${error.message}`);
    },
  });
}

/**
 * Hook to launch a campaign
 */
export function useLaunchCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (campaignId: string) => launchCampaign(campaignId),
    onSuccess: (campaign) => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      queryClient.invalidateQueries({ queryKey: ['campaigns', campaign.id] });
      toast.success(`Campaign "${campaign.name}" launched successfully`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to launch campaign: ${error.message}`);
    },
  });
}

/**
 * Hook to pause a running campaign
 */
export function usePauseCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (campaignId: string) => pauseCampaign(campaignId),
    onSuccess: (campaign) => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      queryClient.invalidateQueries({ queryKey: ['campaigns', campaign.id] });
      toast.success(`Campaign "${campaign.name}" paused`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to pause campaign: ${error.message}`);
    },
  });
}

/**
 * Hook to delete a campaign
 */
export function useDeleteCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (campaignId: string) => deleteCampaign(campaignId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      toast.success('Campaign deleted successfully');
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete campaign: ${error.message}`);
    },
  });
}

/**
 * Hook to fetch campaign analytics
 */
export function useCampaignAnalytics(campaignId: string | undefined) {
  return useQuery({
    queryKey: ['campaigns', campaignId, 'analytics'],
    queryFn: () => {
      if (!campaignId) throw new Error('Campaign ID required');
      return getCampaignAnalytics(campaignId);
    },
    enabled: !!campaignId,
    refetchInterval: (data) => {
      // Refetch every 10s if campaign is running
      return data?.status === 'running' ? 10000 : false;
    },
  });
}

// ==================== Contact Hooks ====================

export interface UseContactsParams {
  limit?: number;
  offset?: number;
  search?: string;
}

/**
 * Hook to fetch contacts list with optional filters
 */
export function useContacts(params?: UseContactsParams) {
  return useQuery({
    queryKey: ['contacts', params],
    queryFn: () => getContacts(params),
    staleTime: 30000,
  });
}

/**
 * Hook to fetch a single contact by ID
 */
export function useContact(contactId: string | undefined) {
  return useQuery({
    queryKey: ['contacts', contactId],
    queryFn: () => {
      if (!contactId) throw new Error('Contact ID required');
      return getContact(contactId);
    },
    enabled: !!contactId,
  });
}

/**
 * Hook to create a new contact
 */
export function useCreateContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ContactCreate) => createContact(data),
    onSuccess: (newContact) => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      toast.success(`Contact "${newContact.name}" created successfully`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to create contact: ${error.message}`);
    },
  });
}

/**
 * Hook to update a contact
 */
export function useUpdateContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ContactUpdate }) =>
      updateContact(id, data),
    onSuccess: (updatedContact) => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      queryClient.invalidateQueries({ queryKey: ['contacts', updatedContact.id] });
      toast.success(`Contact "${updatedContact.name}" updated successfully`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to update contact: ${error.message}`);
    },
  });
}

/**
 * Hook to delete a contact
 */
export function useDeleteContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (contactId: string) => deleteContact(contactId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      toast.success('Contact deleted successfully');
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete contact: ${error.message}`);
    },
  });
}

/**
 * Hook to import contacts from CSV file
 */
export function useImportContacts() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => importContacts(file),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      toast.success(
        `Successfully imported ${result.imported} out of ${result.total_rows} contacts`
      );
    },
    onError: (error: Error) => {
      toast.error(`Failed to import contacts: ${error.message}`);
    },
  });
}

// ==================== Segment Hooks ====================

/**
 * Hook to preview segment results
 * This helps users see how many contacts match their segment filter before creating a campaign
 */
export function useSegmentPreview(
  segmentFilter: SegmentFilter,
  campaignType: CampaignType,
  enabled: boolean = false
) {
  return useQuery({
    queryKey: ['segment-preview', segmentFilter, campaignType],
    queryFn: () => previewSegment(segmentFilter, campaignType),
    enabled: enabled && Object.keys(segmentFilter).length > 0,
    staleTime: 10000, // 10 seconds
  });
}

// ==================== Composite Hooks ====================

/**
 * Hook that combines campaign data with its analytics
 * Useful for campaign detail pages
 */
export function useCampaignWithAnalytics(campaignId: string | undefined) {
  const campaignQuery = useCampaign(campaignId);
  const analyticsQuery = useCampaignAnalytics(campaignId);

  return {
    campaign: campaignQuery.data,
    analytics: analyticsQuery.data,
    isLoading: campaignQuery.isLoading || analyticsQuery.isLoading,
    isError: campaignQuery.isError || analyticsQuery.isError,
    error: campaignQuery.error || analyticsQuery.error,
  };
}

/**
 * Hook for managing campaign state with optimistic updates
 * Provides unified interface for campaign actions
 */
export function useCampaignActions(campaignId: string) {
  const launchMutation = useLaunchCampaign();
  const pauseMutation = usePauseCampaign();
  const deleteMutation = useDeleteCampaign();

  return {
    launch: () => launchMutation.mutate(campaignId),
    pause: () => pauseMutation.mutate(campaignId),
    delete: () => deleteMutation.mutate(campaignId),
    isLoading:
      launchMutation.isPending ||
      pauseMutation.isPending ||
      deleteMutation.isPending,
  };
}
