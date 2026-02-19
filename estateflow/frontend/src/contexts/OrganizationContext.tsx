/**
 * Organization Context for EstateFlow.
 *
 * Provides organization management and switching for admin users.
 */

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import { api } from '@/lib/api';
import { getAuthTokenSync } from '@/lib/auth';
import { useQueryClient } from '@tanstack/react-query';

interface Organization {
  id: string;
  name: string;
  description?: string;
  email?: string;
  phone?: string;
}

interface OrganizationContextType {
  organizations: Organization[];
  currentOrganization: Organization | null;
  selectedOrganizationId: string | null;
  loading: boolean;
  isAdmin: boolean;
  switchOrganization: (orgId: string) => void;
  refreshOrganizations: () => Promise<void>;
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

export function OrganizationProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrganizationId, setSelectedOrganizationId] = useState<string | null>(null);
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null);
  const [loading, setLoading] = useState(true);

  // Check if user is admin
  const isAdmin = user?.user_metadata?.role === 'admin' || user?.email === 'admin@ailabsafrica.com';

  // Debug logging
  useEffect(() => {
    console.log('OrganizationContext - User:', {
      email: user?.email,
      role: user?.user_metadata?.role,
      isAdmin,
      organizationsCount: organizations.length
    });
  }, [user, isAdmin, organizations]);

  // Fetch organizations from API
  const fetchOrganizations = async () => {
    if (!user) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);

      // Get auth token
      const token = getAuthTokenSync();
      if (!token) {
        console.error('No auth token available');
        setLoading(false);
        return;
      }

      if (isAdmin) {
        // Admin users: fetch all organizations
        const response = await api.get('/api/v1/organizations', { token });
        setOrganizations(response.organizations || []);
      } else {
        // Regular users: use their assigned organization
        const orgId = user.user_metadata?.organization_id || user.id;

        // Try to fetch their organization details
        try {
          const response = await api.get(`/api/v1/organizations/${orgId}`, { token });
          setOrganizations([response]);
          setCurrentOrganization(response);
        } catch (error) {
          // If organization doesn't exist, create a minimal one
          console.log('Organization not found, using user context');
          const userOrg: Organization = {
            id: orgId,
            name: user.email?.split('@')[0] || 'My Organization',
          };
          setOrganizations([userOrg]);
          setCurrentOrganization(userOrg);
        }

        setSelectedOrganizationId(orgId);
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error);

      // Fallback: create organization from user context
      if (user) {
        const fallbackOrg: Organization = {
          id: user.user_metadata?.organization_id || user.id,
          name: user.email?.split('@')[0] || 'My Organization',
        };
        setOrganizations([fallbackOrg]);
        setCurrentOrganization(fallbackOrg);
        setSelectedOrganizationId(fallbackOrg.id);
      }
    } finally {
      setLoading(false);
    }
  };

  // Load organizations when user changes
  useEffect(() => {
    fetchOrganizations();
  }, [user]);

  // Update current organization when selection changes
  useEffect(() => {
    if (selectedOrganizationId && organizations.length > 0) {
      const org = organizations.find(o => o.id === selectedOrganizationId);
      setCurrentOrganization(org || null);

      // Store selection in localStorage for persistence
      if (isAdmin) {
        localStorage.setItem('selectedOrganizationId', selectedOrganizationId);
      }
    } else if (organizations.length > 0 && !selectedOrganizationId) {
      // Auto-select first organization if none selected
      const storedOrgId = isAdmin ? localStorage.getItem('selectedOrganizationId') : null;
      const defaultOrgId = storedOrgId || organizations[0].id;
      setSelectedOrganizationId(defaultOrgId);
    }
  }, [selectedOrganizationId, organizations, isAdmin]);

  const switchOrganization = (orgId: string) => {
    setSelectedOrganizationId(orgId);
    // Invalidate all queries to refetch data for the new organization
    queryClient.invalidateQueries();
    console.log('Switched to organization:', orgId, '- All queries invalidated');
  };

  const refreshOrganizations = async () => {
    await fetchOrganizations();
  };

  const value = {
    organizations,
    currentOrganization,
    selectedOrganizationId,
    loading,
    isAdmin,
    switchOrganization,
    refreshOrganizations,
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
