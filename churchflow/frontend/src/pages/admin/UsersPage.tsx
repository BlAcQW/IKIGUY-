/**
 * User Management Admin Page - ChurchFlow
 */

import { useState, useEffect } from 'react';
import AdminLayoutTabs from '../../components/admin/AdminLayoutTabs';
import { UserManagement } from '../../components/admin';
import { useOrganization } from '../../contexts/OrganizationContext';

interface User {
  id: string;
  name: string;
  email?: string;
  phone?: string;
}

export default function UsersPage() {
  const [user, setUser] = useState<User | null>(null);
  const { currentOrganization, currentRole, isUniversalAdmin, loading: orgLoading, organizations } = useOrganization();
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:30030';

  useEffect(() => {
    fetchUser();
  }, []);

  const fetchUser = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setUser({
        id: 'demo',
        name: 'Demo User',
        email: 'demo@churchflow.com'
      });
      return;
    }

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/users/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const userData = await response.json();
        setUser({
          id: userData.id,
          name: userData.name || 'User',
          email: userData.email,
          phone: userData.phone
        });
      } else {
        console.error('Failed to fetch user:', response.statusText);
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
    }
  };

  // Show loading state while fetching organizations
  if (orgLoading) {
    return (
      <AdminLayoutTabs currentPage="/admin/users" appName="ChurchFlow" onBack={() => window.location.href = "/dashboard"} user={user ? {
        name: user.name,
        email: user.email || user.phone || ''
      } : undefined}>
        <div className="text-center py-12">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading organizations...</p>
        </div>
      </AdminLayoutTabs>
    );
  }

  // Show message if no organizations found
  if (!currentOrganization && organizations.length === 0) {
    return (
      <AdminLayoutTabs currentPage="/admin/users" appName="ChurchFlow" onBack={() => window.location.href = "/dashboard"} user={user ? {
        name: user.name,
        email: user.email || user.phone || ''
      } : undefined}>
        <div className="text-center py-12">
          <p className="text-gray-600 mb-4">You are not a member of any organization yet.</p>
          <a href="/admin/organizations" className="text-purple-600 hover:underline font-medium">
            Create or Join an Organization
          </a>
        </div>
      </AdminLayoutTabs>
    );
  }

  // This shouldn't happen with the context, but keep as fallback
  if (!currentOrganization) {
    return (
      <AdminLayoutTabs currentPage="/admin/users" appName="ChurchFlow" onBack={() => window.location.href = "/dashboard"} user={user ? {
        name: user.name,
        email: user.email || user.phone || ''
      } : undefined}>
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
    <AdminLayoutTabs currentPage="/admin/users" appName="ChurchFlow" onBack={() => window.location.href = "/dashboard"} user={user ? {
      name: user.name,
      email: user.email || user.phone || ''
    } : undefined}>
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
}
