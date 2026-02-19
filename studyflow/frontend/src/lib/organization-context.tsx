/**
 * Organization Context
 *
 * Manages the current organization selection and provides
 * organization switching functionality across the app.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useAuth } from './auth-context';

interface Organization {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  industry?: string;
  website?: string;
  is_active: boolean;
  created_at: string;
}

interface OrganizationMembership {
  organization: Organization;
  role: string;
  joined_at: string | null;
}

interface OrganizationContextType {
  currentOrganization: Organization | null;
  organizations: OrganizationMembership[];
  loading: boolean;
  error: string | null;
  switchOrganization: (orgId: string) => void;
  refreshOrganizations: () => Promise<void>;
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

interface OrganizationProviderProps {
  children: ReactNode;
}

export function OrganizationProvider({ children }: OrganizationProviderProps) {
  const { session, loading: authLoading } = useAuth();
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationMembership[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:30031';

  const fetchOrganizations = async () => {
    try {
      setLoading(true);
      setError(null);

      // Wait for auth to be ready and check if we have a valid session
      if (!session?.access_token) {
        setLoading(false);
        return;
      }

      const token = session.access_token;

      const response = await fetch(`${apiBaseUrl}/api/v1/organizations`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch organizations');
      }

      const data: OrganizationMembership[] = await response.json();
      setOrganizations(data);

      // Set current organization from localStorage or default to first org
      const savedOrgId = localStorage.getItem('current_organization_id');
      let orgToSelect: Organization | null = null;

      if (savedOrgId) {
        const savedOrg = data.find(om => om.organization.id === savedOrgId);
        if (savedOrg) {
          orgToSelect = savedOrg.organization;
        }
      }

      // If no saved org or saved org not found, use first org
      if (!orgToSelect && data.length > 0) {
        orgToSelect = data[0].organization;
      }

      if (orgToSelect) {
        setCurrentOrganization(orgToSelect);
        localStorage.setItem('current_organization_id', orgToSelect.id);
      }

    } catch (err) {
      console.error('Error fetching organizations:', err);
      setError(err instanceof Error ? err.message : 'Failed to load organizations');
    } finally {
      setLoading(false);
    }
  };

  const switchOrganization = (orgId: string) => {
    const membership = organizations.find(om => om.organization.id === orgId);
    if (membership) {
      setCurrentOrganization(membership.organization);
      localStorage.setItem('current_organization_id', orgId);

      // Trigger a page reload to refresh all data for the new organization
      window.location.reload();
    }
  };

  const refreshOrganizations = async () => {
    await fetchOrganizations();
  };

  useEffect(() => {
    // Only fetch organizations when auth is ready
    if (!authLoading) {
      fetchOrganizations();
    }
  }, [authLoading, session]);

  const value: OrganizationContextType = {
    currentOrganization,
    organizations,
    loading,
    error,
    switchOrganization,
    refreshOrganizations
  };

  return (
    <OrganizationContext.Provider value={value}>
      {children}
    </OrganizationContext.Provider>
  );
}

export function useOrganization() {
  const context = useContext(OrganizationContext);
  if (context === undefined) {
    throw new Error('useOrganization must be used within an OrganizationProvider');
  }
  return context;
}
