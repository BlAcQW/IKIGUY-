/**
 * Organization Context for ChurchFlow
 *
 * Provides organization management, switching, and role-based access control.
 * Integrated from ERP implementation with ChurchFlow-specific enhancements.
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { supabase } from '@/lib/supabase';
import { sanitizeToken } from '@/lib/header-utils';

interface Organization {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  logo_url?: string;
  website?: string;
  is_active: boolean;
  created_at: string;
}

interface OrganizationMembership {
  organization: Organization;
  role: string;
  joined_at?: string;
  is_universal_admin?: boolean;
}

interface OrganizationContextType {
  organizations: OrganizationMembership[];
  currentOrganization: Organization | null;
  currentRole: string | null;
  isUniversalAdmin: boolean;
  loading: boolean;
  error: string | null;
  setCurrentOrganization: (orgId: string) => void;
  refreshOrganizations: () => Promise<void>;
  clearError: () => void;
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

interface OrganizationProviderProps {
  children: ReactNode;
  apiBaseUrl?: string;
}

export function OrganizationProvider({ children, apiBaseUrl }: OrganizationProviderProps) {
  const [organizations, setOrganizations] = useState<OrganizationMembership[]>([]);
  const [currentOrganization, setCurrentOrg] = useState<Organization | null>(null);
  const [currentRole, setCurrentRole] = useState<string | null>(null);
  const [isUniversalAdmin, setIsUniversalAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const baseUrl = apiBaseUrl || import.meta.env.VITE_API_URL || 'http://localhost:30030';

  const fetchOrganizations = async (retryWithTokenExchange = true) => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await fetch(`${baseUrl}/api/v1/organizations`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      // If we get 401, try to get a fresh Supabase token and exchange it
      if (response.status === 401 && retryWithTokenExchange) {
        try {
          // Get fresh Supabase session token (not the localStorage backend token)
          const { data: { session } } = await supabase.auth.getSession();

          if (!session?.access_token) {
            // No valid Supabase session - user needs to log in again
            localStorage.removeItem('access_token');
            setLoading(false);
            return;
          }

          // Exchange the fresh Supabase token for a backend JWT
          const exchangeResponse = await fetch(`${baseUrl}/api/v1/auth/exchange-token`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${session.access_token}`,
              'Content-Type': 'application/json'
            }
          });

          if (exchangeResponse.ok) {
            const exchangeData = await exchangeResponse.json();
            // Store the new backend token (sanitize first)
            const newToken = sanitizeToken(exchangeData.access_token);
            if (newToken) {
              localStorage.setItem('access_token', newToken);
            }
            // Retry the request with the new token (but don't retry again to avoid loops)
            return fetchOrganizations(false);
          } else {
            // Token exchange failed - clear stale token silently
            // User will need to log in again on protected pages
            localStorage.removeItem('access_token');
            setLoading(false);
            return;
          }
        } catch (exchangeError) {
          // Token exchange failed - clear stale token silently
          localStorage.removeItem('access_token');
          setLoading(false);
          return;
        }
      }

      if (!response.ok) {
        // For 401 without retry, just clear token and return silently
        if (response.status === 401) {
          localStorage.removeItem('access_token');
          setLoading(false);
          return;
        }
        throw new Error(`Failed to fetch organizations: ${response.statusText}`);
      }

      const data = await response.json();

      // Handle both ERP format (array of objects) and ChurchFlow format
      const memberships: OrganizationMembership[] = Array.isArray(data) ? data : [];

      setOrganizations(memberships);

      // Check if any membership has universal admin flag
      const hasUniversalAdmin = memberships.some(
        (m: OrganizationMembership) => m.is_universal_admin || m.role === 'UNIVERSAL_ADMIN'
      );
      setIsUniversalAdmin(hasUniversalAdmin);

      // Set current organization from localStorage or first org
      const storedOrgId = localStorage.getItem('current_organization_id');

      if (storedOrgId) {
        const membership = memberships.find(
          (m: OrganizationMembership) => m.organization.id === storedOrgId
        );

        if (membership) {
          setCurrentOrg(membership.organization);
          setCurrentRole(membership.role);
        } else if (memberships.length > 0) {
          // Stored org not found, use first available
          const firstMembership = memberships[0];
          setCurrentOrg(firstMembership.organization);
          setCurrentRole(firstMembership.role);
          localStorage.setItem('current_organization_id', firstMembership.organization.id);
        }
      } else if (memberships.length > 0) {
        // No stored org, auto-select first
        const firstMembership = memberships[0];
        setCurrentOrg(firstMembership.organization);
        setCurrentRole(firstMembership.role);
        localStorage.setItem('current_organization_id', firstMembership.organization.id);
      }
    } catch (err) {
      console.error('Failed to fetch organizations:', err);
      setError(err instanceof Error ? err.message : 'Failed to load organizations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchOrganizations();
    } else {
      setLoading(false);
    }
  }, []);

  const setCurrentOrganization = (orgId: string) => {
    const membership = organizations.find(m => m.organization.id === orgId);

    if (membership) {
      setCurrentOrg(membership.organization);
      setCurrentRole(membership.role);
      localStorage.setItem('current_organization_id', orgId);

      // Add X-Organization-ID header to future requests
      // This will be handled by axios interceptor or fetch wrapper

      // Reload page to refresh all data for new organization
      window.location.reload();
    } else {
      setError(`Organization ${orgId} not found in your memberships`);
    }
  };

  const clearError = () => {
    setError(null);
  };

  const value: OrganizationContextType = {
    organizations,
    currentOrganization,
    currentRole,
    isUniversalAdmin,
    loading,
    error,
    setCurrentOrganization,
    refreshOrganizations: fetchOrganizations,
    clearError
  };

  return (
    <OrganizationContext.Provider value={value}>
      {children}
    </OrganizationContext.Provider>
  );
}

/**
 * Hook to use organization context
 *
 * @throws Error if used outside OrganizationProvider
 */
export function useOrganization() {
  const context = useContext(OrganizationContext);

  if (context === undefined) {
    throw new Error('useOrganization must be used within an OrganizationProvider');
  }

  return context;
}

export type { Organization, OrganizationMembership, OrganizationContextType };
