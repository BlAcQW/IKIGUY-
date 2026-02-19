/**
 * Organization Context
 * Manages current organization state and organization switching
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import { useToast } from '@/hooks/use-toast';
import { API_BASE_URL } from '@/config/api-config';

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

interface OrganizationContextType {
  currentOrganization: Organization | null;
  organizations: OrganizationMembership[];
  allOrganizations: Organization[]; // All organizations (universal admin only)
  isLoading: boolean;
  isLoadingAll: boolean;
  isUniversalAdmin: boolean;
  currentRole: string | null;
  switchOrganization: (organizationId: string, forceReload?: boolean) => Promise<void>;
  refreshOrganizations: () => Promise<void>;
  refreshAllOrganizations: () => Promise<void>;
  canAccessAdmin: boolean;
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

export const useOrganization = () => {
  const context = useContext(OrganizationContext);
  if (!context) {
    throw new Error('useOrganization must be used within an OrganizationProvider');
  }
  return context;
};

interface OrganizationProviderProps {
  children: React.ReactNode;
}

const STORAGE_KEY = 'kasaai_current_organization_id';

export const OrganizationProvider: React.FC<OrganizationProviderProps> = ({ children }) => {
  const { user, getAccessToken, isAuthenticated } = useMongoAuth();
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationMembership[]>([]);
  const [allOrganizations, setAllOrganizations] = useState<Organization[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingAll, setIsLoadingAll] = useState(false);
  const { toast } = useToast();

  const isUniversalAdmin = user?.is_universal_admin ?? false;

  // Get current user's role in the current organization
  const currentRole = React.useMemo(() => {
    if (isUniversalAdmin) return 'UNIVERSAL_ADMIN';
    if (!currentOrganization) return null;

    const membership = organizations.find(
      org => org.organization_id === currentOrganization.id
    );
    return membership?.role || null;
  }, [currentOrganization, organizations, isUniversalAdmin]);

  // Check if user can access admin panel
  const canAccessAdmin = React.useMemo(() => {
    if (isUniversalAdmin) return true;

    // Check if user is ADMIN or OWNER in any organization
    return organizations.some(
      org => ['ADMIN', 'OWNER'].includes(org.role) && org.is_active
    );
  }, [isUniversalAdmin, organizations]);

  // Fetch user's organizations
  const fetchOrganizations = useCallback(async () => {
    if (!isAuthenticated) {
      setOrganizations([]);
      setCurrentOrganization(null);
      return;
    }

    try {
      const token = getAccessToken();
      if (!token) {
        console.warn('No access token available');
        return;
      }

      // Fetch user's organization memberships
      // Reason: Add trailing slash to match backend route and avoid 307 redirect
      const response = await fetch(`${API_BASE_URL}/organizations/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      // Reason: Handle 401 errors by clearing auth and redirecting to login
      if (response.status === 401) {
        console.warn('Authentication expired, redirecting to login');
        // Clear expired token
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // Redirect to login
        window.location.href = '/auth';
        return;
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch organizations: ${response.status}`);
      }

      const data = await response.json();
      const orgs: OrganizationMembership[] = data.organizations || [];

      setOrganizations(orgs);

      // Set current organization
      if (orgs.length > 0) {
        // Try to restore last selected org from localStorage
        const storedOrgId = localStorage.getItem(STORAGE_KEY);

        let selectedOrg: OrganizationMembership | undefined;

        if (storedOrgId) {
          // First try to find in user's memberships
          selectedOrg = orgs.find(org => org.organization_id === storedOrgId);

          // If not found in memberships but user has it stored, they might be universal admin
          // Keep the stored ID for later use when allOrganizations loads
          if (!selectedOrg && isUniversalAdmin) {
            // Don't override with primary_organization_id - trust localStorage
            // The org will be set when allOrganizations loads or via switchOrganization
            console.log(`Stored org ${storedOrgId} not in memberships, universal admin will load it from allOrganizations`);
          }
        }

        // Only fallback to primary org if NO stored org exists
        if (!selectedOrg && !storedOrgId) {
          selectedOrg = orgs.find(org => org.organization_id === user?.primary_organization_id) || orgs[0];
        }

        if (selectedOrg) {
          setCurrentOrganization(selectedOrg.organization);
          localStorage.setItem(STORAGE_KEY, selectedOrg.organization_id);
        }
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
      toast({
        title: 'Error',
        description: 'Failed to load organizations',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
    // Reason: Removed user?.primary_organization_id from deps to prevent re-fetch on every user change
    // It's only used for fallback logic inside the function, not as a trigger
  }, [isAuthenticated, getAccessToken, toast]);

  // Fetch ALL organizations (universal admin only)
  const fetchAllOrganizations = useCallback(async () => {
    if (!isUniversalAdmin || !isAuthenticated) {
      setAllOrganizations([]);
      return;
    }

    try {
      setIsLoadingAll(true);
      const token = getAccessToken();
      if (!token) return;

      const response = await fetch(`${API_BASE_URL}/organizations/all`, {
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
    } catch (error) {
      console.error('Failed to fetch all organizations:', error);
      toast({
        title: 'Error',
        description: 'Failed to load all organizations',
        variant: 'destructive',
      });
    } finally {
      setIsLoadingAll(false);
    }
  }, [isUniversalAdmin, isAuthenticated, getAccessToken, toast]);

  // Switch to a different organization
  const switchOrganization = useCallback(async (organizationId: string, forceReload: boolean = false) => {
    // Try to find in user's memberships first
    const membership = organizations.find(org => org.organization_id === organizationId);

    // If not found in memberships, try allOrganizations (universal admin)
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
      toast({
        title: 'Error',
        description: 'Organization not found',
        variant: 'destructive',
      });
      return;
    }

    // Update current organization
    setCurrentOrganization(targetOrg);
    localStorage.setItem(STORAGE_KEY, organizationId);

    toast({
      title: 'Organization Switched',
      description: `Now viewing ${targetOrg.display_name}`,
    });

    // Force reload as fallback if requested
    if (forceReload) {
      setTimeout(() => window.location.reload(), 500);
    }
  }, [organizations, allOrganizations, isUniversalAdmin, toast]);

  // Refresh organizations list
  const refreshOrganizations = useCallback(async () => {
    setIsLoading(true);
    await fetchOrganizations();
  }, [fetchOrganizations]);

  // Refresh all organizations (universal admin only)
  const refreshAllOrganizations = useCallback(async () => {
    await fetchAllOrganizations();
  }, [fetchAllOrganizations]);

  // Load organizations on mount and when auth state changes
  // Reason: Removed fetchOrganizations from deps to prevent infinite loop
  // since fetchOrganizations already depends on user via useCallback
  useEffect(() => {
    if (isAuthenticated && user) {
      fetchOrganizations();

      // Auto-fetch all organizations for universal admins
      if (isUniversalAdmin) {
        fetchAllOrganizations();
      }
    } else {
      setOrganizations([]);
      setAllOrganizations([]);
      setCurrentOrganization(null);
      setIsLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, user, isUniversalAdmin]);

  // Restore organization from localStorage for universal admins after allOrganizations loads
  useEffect(() => {
    if (!isUniversalAdmin || allOrganizations.length === 0 || currentOrganization) {
      return;
    }

    const storedOrgId = localStorage.getItem(STORAGE_KEY);
    if (storedOrgId) {
      // Check if stored org exists in allOrganizations
      const storedOrg = allOrganizations.find(org => org.id === storedOrgId);
      if (storedOrg) {
        console.log(`Restoring universal admin org from localStorage: ${storedOrg.display_name}`);
        setCurrentOrganization(storedOrg);
      }
    }
  }, [isUniversalAdmin, allOrganizations, currentOrganization]);

  const value: OrganizationContextType = {
    currentOrganization,
    organizations,
    allOrganizations,
    isLoading,
    isLoadingAll,
    isUniversalAdmin,
    currentRole,
    switchOrganization,
    refreshOrganizations,
    refreshAllOrganizations,
    canAccessAdmin,
  };

  return (
    <OrganizationContext.Provider value={value}>
      {children}
    </OrganizationContext.Provider>
  );
};
