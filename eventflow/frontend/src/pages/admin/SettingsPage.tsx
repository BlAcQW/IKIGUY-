/**
import AdminLayoutTabs from '../../components/admin/AdminLayoutTabs';
 * Organization Settings Admin Page - EventFlow
 */

import React, { useState, useEffect } from 'react';
import { OrganizationSettings } from '../../components/admin';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../../lib/store';

export const SettingsPage: React.FC = () => {
  const { user } = useStore();
  const navigate = useNavigate();
  const [currentOrgId, setCurrentOrgId] = useState<string>('');
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:30032';

  useEffect(() => {
    const orgId = localStorage.getItem('current_organization_id');
    if (orgId) setCurrentOrgId(orgId);
  }, []);

  if (!currentOrgId) {
    return (
      <AdminLayoutTabs
        currentPage="/admin/settings"
        appName="EventFlow"
        onBack={() => navigate("/home")} user={user ? {
          name: user.name || user.email,
          email: user.email
        } : undefined}
      >
        <div className="text-center py-12">
          <p className="text-gray-600">Please select an organization first</p>
          <a href="/admin/organizations" className="text-blue-600 hover:underline mt-4 inline-block">
            Go to Organizations
          </a>
        </div>
      </AdminLayoutTabs>
    );
  }

  return (
    <AdminLayoutTabs
      currentPage="/admin/settings"
      appName="EventFlow"
      onBack={() => navigate("/home")} user={user ? {
        name: user.name || user.email,
        email: user.email
      } : undefined}
    >
      <OrganizationSettings
        organizationId={currentOrgId}
        apiBaseUrl={apiBaseUrl}
        onError={(msg) => console.error(msg)}
        onSuccess={(msg) => console.log(msg)}
      />
    </AdminLayoutTabs>
  );
};
