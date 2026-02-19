import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAssistants, useCampaigns, useLicense, useUsage, usePayments, useKnowledgeBase, useMCP, useHealth } from '@/hooks/useCoreApi';

// Mock the core API
vi.mock('@/lib/core-api', () => ({
  coreApi: {
    assistant: {
      list: vi.fn().mockResolvedValue([]),
      create: vi.fn().mockResolvedValue({}),
      get: vi.fn().mockResolvedValue({}),
    },
    campaign: {
      list: vi.fn().mockResolvedValue([]),
      create: vi.fn().mockResolvedValue({}),
      get: vi.fn().mockResolvedValue({}),
    },
    license: {
      getStatus: vi.fn().mockResolvedValue({}),
      verify: vi.fn().mockResolvedValue({}),
      activate: vi.fn().mockResolvedValue({}),
    },
    usage: {
      getUsage: vi.fn().mockResolvedValue({}),
      getDashboard: vi.fn().mockResolvedValue({}),
    },
    payment: {
      getPaymentMethods: vi.fn().mockResolvedValue({}),
      getWalletBalance: vi.fn().mockResolvedValue({}),
      createDeposit: vi.fn().mockResolvedValue({}),
      processMobileMoney: vi.fn().mockResolvedValue({}),
    },
    knowledgeBase: {
      ingest: vi.fn().mockResolvedValue({}),
      search: vi.fn().mockResolvedValue([]),
    },
    mcp: {
      createCrmLead: vi.fn().mockResolvedValue({}),
      updateCrmContact: vi.fn().mockResolvedValue({}),
      createHelpdeskTicket: vi.fn().mockResolvedValue({}),
      processPayment: vi.fn().mockResolvedValue({}),
    },
    health: {
      check: vi.fn().mockResolvedValue({}),
    },
  },
}));

// Mock the toast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

// Mock Supabase
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({ data: { session: null }, error: null }),
      onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
    },
    from: vi.fn(() => ({
      select: vi.fn(),
      insert: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    })),
    storage: {
      from: vi.fn(() => ({
        upload: vi.fn(),
        download: vi.fn(),
        remove: vi.fn(),
      })),
    },
    rpc: vi.fn(),
  },
}));

// Create a test query client
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

// Wrapper component for testing hooks
const wrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createTestQueryClient();
  return React.createElement(QueryClientProvider, { client: queryClient }, children);
};

describe('useCoreApi Hooks', () => {
  const testTenantId = 'test-tenant-123';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('useAssistants', () => {
    it('should provide assistants hook', () => {
      const { result } = renderHook(() => useAssistants(testTenantId), { wrapper });

      expect(result.current.assistants).toBeDefined();
      expect(result.current.isLoadingAssistants).toBeDefined();
      expect(result.current.assistantsError).toBeDefined();
      expect(result.current.createAssistantAsync).toBeDefined();
      expect(result.current.getAssistantAsync).toBeDefined();
    });

    it('should not fetch when tenantId is empty', () => {
      const { result } = renderHook(() => useAssistants(''), { wrapper });

      expect(result.current.isLoadingAssistants).toBe(false);
    });
  });

  describe('useCampaigns', () => {
    it('should provide campaigns hook', () => {
      const { result } = renderHook(() => useCampaigns(testTenantId), { wrapper });

      expect(result.current.campaigns).toBeDefined();
      expect(result.current.isLoadingCampaigns).toBeDefined();
      expect(result.current.campaignsError).toBeDefined();
      expect(result.current.createCampaignAsync).toBeDefined();
      expect(result.current.getCampaignAsync).toBeDefined();
    });
  });

  describe('useLicense', () => {
    it('should provide license hook', () => {
      const { result } = renderHook(() => useLicense(testTenantId), { wrapper });

      expect(result.current.licenseInfo).toBeDefined();
      expect(result.current.isLoadingLicense).toBeDefined();
      expect(result.current.licenseError).toBeDefined();
      expect(result.current.verifyLicenseAsync).toBeDefined();
      expect(result.current.activateLicenseAsync).toBeDefined();
    });
  });

  describe('useUsage', () => {
    it('should provide usage hook', () => {
      const { result } = renderHook(() => useUsage(testTenantId), { wrapper });

      expect(result.current.usageData).toBeDefined();
      expect(result.current.isLoadingUsage).toBeDefined();
      expect(result.current.usageError).toBeDefined();
      expect(result.current.usageDashboard).toBeDefined();
      expect(result.current.isLoadingDashboard).toBeDefined();
      expect(result.current.dashboardError).toBeDefined();
    });
  });

  describe('usePayments', () => {
    it('should provide payments hook', () => {
      const { result } = renderHook(() => usePayments(testTenantId), { wrapper });

      expect(result.current.paymentMethods).toBeDefined();
      expect(result.current.isLoadingPaymentMethods).toBeDefined();
      expect(result.current.paymentMethodsError).toBeDefined();
      expect(result.current.walletBalance).toBeDefined();
      expect(result.current.isLoadingWallet).toBeDefined();
      expect(result.current.walletError).toBeDefined();
      expect(result.current.createDepositAsync).toBeDefined();
      expect(result.current.processMobileMoneyAsync).toBeDefined();
    });
  });

  describe('useKnowledgeBase', () => {
    it('should provide knowledge base hook', () => {
      const { result } = renderHook(() => useKnowledgeBase(testTenantId), { wrapper });

      expect(result.current.isIngesting).toBeDefined();
      expect(result.current.ingestError).toBeDefined();
      expect(result.current.ingestContentAsync).toBeDefined();
      expect(result.current.isSearching).toBeDefined();
      expect(result.current.searchResults).toBeDefined();
      expect(result.current.searchError).toBeDefined();
      expect(result.current.searchKnowledgeBaseAsync).toBeDefined();
    });
  });

  describe('useMCP', () => {
    it('should provide MCP hook', () => {
      const { result } = renderHook(() => useMCP(testTenantId), { wrapper });

      expect(result.current.isCreatingCrmLead).toBeDefined();
      expect(result.current.createCrmLeadError).toBeDefined();
      expect(result.current.createCrmLeadAsync).toBeDefined();
      expect(result.current.isUpdatingCrmContact).toBeDefined();
      expect(result.current.updateCrmContactError).toBeDefined();
      expect(result.current.updateCrmContactAsync).toBeDefined();
      expect(result.current.isCreatingHelpdeskTicket).toBeDefined();
      expect(result.current.createHelpdeskTicketError).toBeDefined();
      expect(result.current.createHelpdeskTicketAsync).toBeDefined();
      expect(result.current.isProcessingPayment).toBeDefined();
      expect(result.current.processPaymentError).toBeDefined();
      expect(result.current.processPaymentAsync).toBeDefined();
    });
  });

  describe('useHealth', () => {
    it('should provide health hook', () => {
      const { result } = renderHook(() => useHealth(), { wrapper });

      expect(result.current.healthStatus).toBeDefined();
      expect(result.current.isLoadingHealth).toBeDefined();
      expect(result.current.healthError).toBeDefined();
    });
  });
});
