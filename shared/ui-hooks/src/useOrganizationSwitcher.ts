/**
 * Shared Organization Switcher Hook
 *
 * Provides organization switching functionality for all KasaAI apps.
 * Can be used in ChurchFlow, EventFlow, InkWave, StudyFlow, etc.
 *
 * @example
 * ```tsx
 * import { useOrganizationSwitcher } from '@kasaai/ui-hooks';
 *
 * function MyComponent() {
 *   const {
 *     currentOrg,
 *     organizations,
 *     allOrganizations,
 *     isUniversalAdmin,
 *     switchOrg,
 *     isLoading
 *   } = useOrganizationSwitcher({
 *     apiUrl: 'https://api.ailabsafrica.com',
 *     onSwitch: (org) => console.log('Switched to:', org.display_name)
 *   });
 *
 *   return (
 *     <select
 *       value={currentOrg?.id || ''}
 *       onChange={(e) => switchOrg(e.target.value)}
 *     >
 *       {organizations.map(org => (
 *         <option key={org.id} value={org.id}>{org.display_name}</option>
 *       ))}
 *     </select>
 *   );
 * }
 * ```
 */

import { useState, useEffect, useCallback } from 'react';

export interface Organization {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  industry?: string;
  company_size?: string;
  website?: string;
  style_settings?: Record<string, any>;
}

export interface OrganizationMembership {
  id: string;
  organization_id: string;
  user_id: string;
  email: string;
  role: 'UNIVERSAL_ADMIN' | 'OWNER' | 'ADMIN' | 'MANAGER' | 'MEMBER' | 'VIEWER';
  is_active: boolean;
  joined_at: string;
  organization: Organization;
}

export interface UseOrganizationSwitcherOptions {
  /**
   * Base API URL (default: https://api.ailabsafrica.com)
   */
  apiUrl?: string;

  /**
   * Callback triggered when organization is switched
   */
  onSwitch?: (organization: Organization) => void;

  /**
   * Enable fetching ALL organizations for universal admins (default: true)
   */
  enableAllOrganizations?: boolean;

  /**
   * Auto-refresh interval in milliseconds (default: null - no auto refresh)
   */
  refreshInterval?: number | null;

  /**
   * Get access token function (if using custom auth)
   */
  getAccessToken?: () => string | null;

  /**
   * Check if user is universal admin (if using custom user object)
   */
  isUniversalAdmin?: boolean;
}

export interface UseOrganizationSwitcherReturn {
  /** Current active organization */
  currentOrg: Organization | null;

  /** User's organization memberships */
  organizations: OrganizationMembership[];

  /** All organizations (universal admin only) */
  allOrganizations: Organization[];

  /** Loading state for user's organizations */
  isLoading: boolean;

  /** Loading state for all organizations */
  isLoadingAll: boolean;

  /** Whether current user is universal admin */
  isUniversalAdmin: boolean;

  /** Current user's role in active organization */
  currentRole: string | null;

  /** Switch to a different organization */
  switchOrg: (organizationId: string, forceReload?: boolean) => Promise<void>;

  /** Refresh user's organizations */
  refreshOrganizations: () => Promise<void>;

  /** Refresh all organizations (universal admin only) */
  refreshAllOrganizations: () => Promise<void>;

  /** Error state */
  error: Error | null;
}

const STORAGE_KEY = 'kasaai_current_organization_id';
const DEFAULT_API_URL = 'https://api.ailabsafrica.com';

/**
 * Hook for managing organization switching across KasaAI apps
 */
export function useOrganizationSwitcher(
  options: UseOrganizationSwitcherOptions = {}
): UseOrganizationSwitcherReturn {
  const {
    apiUrl = DEFAULT_API_URL,
    onSwitch,
    enableAllOrganizations = true,
    refreshInterval = null,
    getAccessToken: customGetToken,
    isUniversalAdmin: customIsUniversalAdmin,
  } = options;

  const [currentOrg, setCurrentOrg] = useState<Organization | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationMembership[]>([]);
  const [allOrganizations, setAllOrganizations] = useState<Organization[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingAll, setIsLoadingAll] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Get access token from localStorage or custom function
  const getAccessToken = useCallback(() => {
    if (customGetToken) {
      return customGetToken();
    }
    return localStorage.getItem('access_token');
  }, [customGetToken]);

  // Check if user is universal admin
  const [isUniversalAdmin, setIsUniversalAdmin] = useState(false);

  useEffect(() => {
    if (customIsUniversalAdmin !== undefined) {
      setIsUniversalAdmin(customIsUniversalAdmin);
    } else {
      // Try to get from user object in localStorage
      const userStr = localStorage.getItem('user');
      if (userStr) {
        try {
          const user = JSON.parse(userStr);
          setIsUniversalAdmin(user.is_universal_admin ?? false);
        } catch (e) {
          setIsUniversalAdmin(false);
        }
      }
    }
  }, [customIsUniversalAdmin]);

  // Get current user's role in active organization
  const currentRole = organizations.find(
    org => org.organization_id === currentOrg?.id
  )?.role || (isUniversalAdmin ? 'UNIVERSAL_ADMIN' : null);

  // Fetch user's organization memberships
  const fetchOrganizations = useCallback(async () => {
    try {
      const token = getAccessToken();
      if (!token) {
        setIsLoading(false);
        return;
      }

      const response = await fetch(`${apiUrl}/organizations/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch organizations: ${response.status}`);
      }

      const data = await response.json();
      const orgs: OrganizationMembership[] = data.organizations || [];

      setOrganizations(orgs);

      // Set current organization
      if (orgs.length > 0) {
        const storedOrgId = localStorage.getItem(STORAGE_KEY);

        let selectedOrg: OrganizationMembership | undefined;

        if (storedOrgId) {
          selectedOrg = orgs.find(org => org.organization_id === storedOrgId);
        }

        if (!selectedOrg) {
          selectedOrg = orgs[0];
        }

        if (selectedOrg) {
          setCurrentOrg(selectedOrg.organization);
          localStorage.setItem(STORAGE_KEY, selectedOrg.organization_id);
        }
      }

      setError(null);
    } catch (err) {
      console.error('Failed to fetch organizations:', err);
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [apiUrl, getAccessToken]);

  // Fetch ALL organizations (universal admin only)
  const fetchAllOrganizations = useCallback(async () => {
    if (!isUniversalAdmin || !enableAllOrganizations) {
      setAllOrganizations([]);
      return;
    }

    try {
      setIsLoadingAll(true);
      const token = getAccessToken();
      if (!token) return;

      const response = await fetch(`${apiUrl}/organizations/all`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch all organizations: ${response.status}`);
      }

      const data = await response.json();
      setAllOrganizations(data || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch all organizations:', err);
      setError(err as Error);
    } finally {
      setIsLoadingAll(false);
    }
  }, [isUniversalAdmin, enableAllOrganizations, apiUrl, getAccessToken]);

  // Switch to a different organization
  const switchOrg = useCallback(
    async (organizationId: string, forceReload: boolean = false) => {
      // Try to find in user's memberships first
      const membership = organizations.find(org => org.organization_id === organizationId);

      let targetOrg: Organization | null = null;

      if (membership) {
        targetOrg = membership.organization;
      } else if (isUniversalAdmin) {
        // Find in allOrganizations
        const allOrg = allOrganizations.find(org => org.id === organizationId);
        if (allOrg) {
          targetOrg = allOrg;
        }
      }

      if (!targetOrg) {
        throw new Error('Organization not found');
      }

      // Update current organization
      setCurrentOrg(targetOrg);
      localStorage.setItem(STORAGE_KEY, organizationId);

      // Trigger callback
      if (onSwitch) {
        onSwitch(targetOrg);
      }

      // Force reload as fallback if requested
      if (forceReload) {
        setTimeout(() => window.location.reload(), 500);
      }
    },
    [organizations, allOrganizations, isUniversalAdmin, onSwitch]
  );

  // Refresh organizations list
  const refreshOrganizations = useCallback(async () => {
    setIsLoading(true);
    await fetchOrganizations();
  }, [fetchOrganizations]);

  // Refresh all organizations (universal admin only)
  const refreshAllOrganizations = useCallback(async () => {
    await fetchAllOrganizations();
  }, [fetchAllOrganizations]);

  // Initial load
  useEffect(() => {
    fetchOrganizations();

    // Auto-fetch all organizations for universal admins
    if (isUniversalAdmin && enableAllOrganizations) {
      fetchAllOrganizations();
    }
  }, [fetchOrganizations, fetchAllOrganizations, isUniversalAdmin, enableAllOrganizations]);

  // Auto-refresh if interval is set
  useEffect(() => {
    if (refreshInterval && refreshInterval > 0) {
      const interval = setInterval(() => {
        fetchOrganizations();
        if (isUniversalAdmin && enableAllOrganizations) {
          fetchAllOrganizations();
        }
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [refreshInterval, fetchOrganizations, fetchAllOrganizations, isUniversalAdmin, enableAllOrganizations]);

  return {
    currentOrg,
    organizations,
    allOrganizations,
    isLoading,
    isLoadingAll,
    isUniversalAdmin,
    currentRole,
    switchOrg,
    refreshOrganizations,
    refreshAllOrganizations,
    error,
  };
}
