/**
 * Organization Settings Admin Page - StudyFlow
 */

import React, { useState } from 'react';
import { OrganizationSettings } from '../../components/admin';
import AdminLayoutTabs from '../../components/admin/AdminLayoutTabs';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../lib/auth-context';

export default function SettingsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [currentOrgId, setCurrentOrgId] = useState<string>('');
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:30031';

  const handleError = (error: string) => {
    console.error('Settings Error:', error);
  };

  const handleSuccess = (message: string) => {
    console.log('Success:', message);
  };

  // Get org ID from localStorage or context
  React.useEffect(() => {
    const orgId = localStorage.getItem('current_organization_id');
    if (orgId) setCurrentOrgId(orgId);
  }, []);

  if (!currentOrgId) {
    return (
      <AdminLayoutTabs currentPage="/admin/settings" appName="StudyFlow" user={user}>
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
      appName="StudyFlow"
      onBack={() => navigate("/dashboard")}
      user={user ? {
        name: user.name || user.email,
        email: user.email
      } : undefined}
    >
      <OrganizationSettings
        organizationId={currentOrgId}
        apiBaseUrl={apiBaseUrl}
        onError={handleError}
        onSuccess={handleSuccess}
      />
    </AdminLayoutTabs>
  );
}
