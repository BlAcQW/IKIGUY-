/**
 * User Management Admin Page - EventFlow
 */

import React from 'react';
import { UserManagement } from '../../components/admin';
import AdminLayoutTabs from '../../components/admin/AdminLayoutTabs';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../../lib/store';
import { useOrganization } from '../../contexts/OrganizationContext';

export const UsersPage: React.FC = () => {
  const { user } = useStore();
  const navigate = useNavigate();
  const { currentOrganization, currentRole, isUniversalAdmin, loading: orgLoading, organizations } = useOrganization();
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:30032';

  // Show loading state
  if (orgLoading) {
    return (
      <AdminLayoutTabs
        currentPage="/admin/users"
        appName="EventFlow"
        onBack={() => navigate("/home")} user={user ? {
          name: user.name || user.email,
          email: user.email
        } : undefined}
      >
        <div className="text-center py-12">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading organizations...</p>
        </div>
      </AdminLayoutTabs>
    );
  }

  // Show message if no organizations
  if (!currentOrganization && organizations.length === 0) {
    return (
      <AdminLayoutTabs
        currentPage="/admin/users"
        appName="EventFlow"
        onBack={() => navigate("/home")} user={user ? {
          name: user.name || user.email,
          email: user.email
        } : undefined}
      >
        <div className="text-center py-12">
          <p className="text-gray-600 mb-4">You are not a member of any organization yet.</p>
          <a href="/admin/organizations" className="text-purple-600 hover:underline font-medium">
            Create or Join an Organization
          </a>
        </div>
      </AdminLayoutTabs>
    );
  }

  // Fallback
  if (!currentOrganization) {
    return (
      <AdminLayoutTabs
        currentPage="/admin/users"
        appName="EventFlow"
        onBack={() => navigate("/home")} user={user ? {
          name: user.name || user.email,
          email: user.email
        } : undefined}
      >
        <div className="text-center py-12">
          <p className="text-gray-600 mb-4">Please select an organization</p>
          <a href="/admin/organizations" className="text-purple-600 hover:underline font-medium">
            Go to Organizations
          </a>
        </div>
      </AdminLayoutTabs>
    );
  }

  return (
    <AdminLayoutTabs
      currentPage="/admin/users"
      appName="EventFlow"
      onBack={() => navigate("/home")} user={user ? {
        name: user.name || user.email,
        email: user.email
      } : undefined}
    >
      <UserManagement
        organizationId={currentOrganization.id}
        apiBaseUrl={apiBaseUrl}
        currentRole={currentRole}
        isUniversalAdmin={isUniversalAdmin}
        onError={(msg) => console.error(msg)}
        onSuccess={(msg) => console.log(msg)}
      />
    </AdminLayoutTabs>
  );
};
