/**
 * AI Tools API Client
 *
 * Handles AI content generation API calls including property listings,
 * social media posts, email campaigns, and contract analysis.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { API_BASE_URL } from '@/lib/api-config';
import { getAuthTokenSync } from '@/lib/auth';

// ==================== Types ====================

export type GenerationType = 'listing' | 'social_media' | 'email' | 'contract_analysis';

export interface GenerationRequest {
  generation_type: GenerationType;
  prompt: string;
  property_id?: string;
  additional_context?: string;
}

export interface GenerationResponse {
  id: string;
  organization_id: string;
  generation_type: GenerationType;
  prompt: string;
  result: string;
  property_id?: string;
  tokens_used?: number;
  model_used: string;
  created_at: string;
}

export interface GenerationListResponse {
  generations: GenerationResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface AIStats {
  total_generations: number;
  generations_today: number;
  tokens_used_total: number;
  most_used_type: string | null;
}

// ==================== Helpers ====================

function buildHeaders(): HeadersInit {
  const headers: HeadersInit = { 'Content-Type': 'application/json' };
  const token = getAuthTokenSync();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const orgId = localStorage.getItem('selectedOrganizationId');
  if (orgId) headers['X-Organization-ID'] = orgId;
  return headers;
}

// ==================== API Functions ====================

export async function generateListing(data: GenerationRequest): Promise<GenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/ai/generate/listing`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to generate listing' }));
    throw new Error(error.detail || 'Failed to generate listing');
  }
  return response.json();
}

export async function generateSocialPost(data: GenerationRequest): Promise<GenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/ai/generate/social`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to generate social post' }));
    throw new Error(error.detail || 'Failed to generate social post');
  }
  return response.json();
}

export async function generateEmail(data: GenerationRequest): Promise<GenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/ai/generate/email`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to generate email' }));
    throw new Error(error.detail || 'Failed to generate email');
  }
  return response.json();
}

export async function analyzeContract(data: GenerationRequest): Promise<GenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/ai/analyze/contract`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to analyze contract' }));
    throw new Error(error.detail || 'Failed to analyze contract');
  }
  return response.json();
}

export async function fetchGenerations(params?: { limit?: number; offset?: number }): Promise<GenerationListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  if (params?.offset) searchParams.set('offset', params.offset.toString());

  const response = await fetch(`${API_BASE_URL}/api/v1/ai/generations?${searchParams}`, { headers: buildHeaders() });
  if (!response.ok) throw new Error('Failed to fetch generations');
  return response.json();
}

export async function fetchAIStats(): Promise<AIStats> {
  const response = await fetch(`${API_BASE_URL}/api/v1/ai/stats`, { headers: buildHeaders() });
  if (!response.ok) throw new Error('Failed to fetch AI stats');
  return response.json();
}

// ==================== React Query Hooks ====================

export function useGenerateListing() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GenerationRequest) => generateListing(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-generations'] });
      queryClient.invalidateQueries({ queryKey: ['ai-stats'] });
      toast.success('Listing generated successfully');
    },
    onError: (error: Error) => {
      toast.error(`Failed to generate listing: ${error.message}`);
    },
  });
}

export function useGenerateSocialPost() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GenerationRequest) => generateSocialPost(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-generations'] });
      queryClient.invalidateQueries({ queryKey: ['ai-stats'] });
      toast.success('Social post generated successfully');
    },
    onError: (error: Error) => {
      toast.error(`Failed to generate social post: ${error.message}`);
    },
  });
}

export function useGenerateEmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GenerationRequest) => generateEmail(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-generations'] });
      queryClient.invalidateQueries({ queryKey: ['ai-stats'] });
      toast.success('Email generated successfully');
    },
    onError: (error: Error) => {
      toast.error(`Failed to generate email: ${error.message}`);
    },
  });
}

export function useAnalyzeContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GenerationRequest) => analyzeContract(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-generations'] });
      queryClient.invalidateQueries({ queryKey: ['ai-stats'] });
      toast.success('Contract analyzed successfully');
    },
    onError: (error: Error) => {
      toast.error(`Failed to analyze contract: ${error.message}`);
    },
  });
}

export function useGenerations(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ['ai-generations', params],
    queryFn: () => fetchGenerations(params),
    staleTime: 30000,
  });
}

export function useAIStats() {
  return useQuery({
    queryKey: ['ai-stats'],
    queryFn: fetchAIStats,
    staleTime: 30000,
  });
}
