/**
 * Organization Settings Admin Page - InkWave
 */

import { useState, useEffect } from 'react';
import { OrganizationSettings } from '../../components/admin';
import AdminLayoutTabs from '../../components/admin/AdminLayoutTabs';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

export default function SettingsPage() {
  useEffect(() => {
    document.title = 'Admin Settings - InkWave';
  }, []);

  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [currentOrgId, setCurrentOrgId] = useState<string>('');
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:30033';

  useEffect(() => {
    const orgId = localStorage.getItem('current_organization_id');
    if (orgId) setCurrentOrgId(orgId);
  }, []);

  if (!currentOrgId) {
    return (
      <AdminLayoutTabs currentPage="/admin/settings" appName="InkWave" user={user}>
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
    <AdminLayoutTabs currentPage="/admin/settings" appName="InkWave" user={user}>
      <OrganizationSettings
        organizationId={currentOrgId}
        apiBaseUrl={apiBaseUrl}
        onError={(msg) => console.error(msg)}
        onSuccess={(msg) => console.log(msg)}
      />
    </AdminLayoutTabs>
  );
}
