import React, { createContext, useContext, useEffect, useState } from 'react'
import api from '@/lib/api'
import { useAuth } from './AuthContext'

interface Organization {
  id: string
  name: string
  display_name: string
  description?: string
}

interface OrganizationMembership {
  organization: Organization
  role: string
  is_universal_admin?: boolean
}

interface OrganizationContextType {
  organizations: OrganizationMembership[]
  currentOrganization: Organization | null
  currentRole: string | null
  isUniversalAdmin: boolean
  loading: boolean
  setCurrentOrganization: (orgId: string) => void
  refreshOrganizations: () => Promise<void>
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined)

export function OrganizationProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  const [organizations, setOrganizations] = useState<OrganizationMembership[]>([])
  const [currentOrganization, setCurrentOrg] = useState<Organization | null>(null)
  const [currentRole, setCurrentRole] = useState<string | null>(null)
  const [isUniversalAdmin, setIsUniversalAdmin] = useState(false)
  const [loading, setLoading] = useState(true)

  const fetchOrganizations = async () => {
    try {
      const response = await api.get('/organizations')
      setOrganizations(response.data)

      // Set universal admin flag
      const universalAdmin = response.data.some((m: OrganizationMembership) => m.is_universal_admin)
      setIsUniversalAdmin(universalAdmin)

      // Set current organization
      const storedOrgId = localStorage.getItem('current_organization_id')
      if (storedOrgId) {
        const membership = response.data.find((m: OrganizationMembership) => m.organization.id === storedOrgId)
        if (membership) {
          setCurrentOrg(membership.organization)
          setCurrentRole(membership.role)
        }
      } else if (response.data.length > 0) {
        // Auto-select first organization
        const firstMembership = response.data[0]
        setCurrentOrg(firstMembership.organization)
        setCurrentRole(firstMembership.role)
        localStorage.setItem('current_organization_id', firstMembership.organization.id)
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (user) {
      fetchOrganizations()
    } else {
      setLoading(false)
    }
  }, [user])

  const setCurrentOrganization = (orgId: string) => {
    const membership = organizations.find(m => m.organization.id === orgId)
    if (membership) {
      setCurrentOrg(membership.organization)
      setCurrentRole(membership.role)
      localStorage.setItem('current_organization_id', orgId)
      window.location.reload() // Reload to refresh data for new org
    }
  }

  return (
    <OrganizationContext.Provider
      value={{
        organizations,
        currentOrganization,
        currentRole,
        isUniversalAdmin,
        loading,
        setCurrentOrganization,
        refreshOrganizations: fetchOrganizations,
      }}
    >
      {children}
    </OrganizationContext.Provider>
  )
}

export function useOrganization() {
  const context = useContext(OrganizationContext)
  if (context === undefined) {
    throw new Error('useOrganization must be used within an OrganizationProvider')
  }
  return context
}
