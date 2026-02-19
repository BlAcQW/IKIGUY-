/**
 * Organization Billing Admin Page - StudyFlow
 */

import React, { useState } from 'react';
import { OrganizationBilling } from '../../components/admin';
import AdminLayoutTabs from '../../components/admin/AdminLayoutTabs';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../lib/auth-context';

export default function BillingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [currentOrgId, setCurrentOrgId] = useState<string>('');
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:30031';

  const handleError = (error: string) => {
    console.error('Billing Error:', error);
  };

  React.useEffect(() => {
    const orgId = localStorage.getItem('current_organization_id');
    if (orgId) setCurrentOrgId(orgId);
  }, []);

  if (!currentOrgId) {
    return (
      <AdminLayoutTabs currentPage="/admin/billing" appName="StudyFlow" user={user}>
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
      currentPage="/admin/billing"
      appName="StudyFlow"
      onBack={() => navigate("/dashboard")}
      user={user ? {
        name: user.name || user.email,
        email: user.email
      } : undefined}
    >
      <OrganizationBilling
        organizationId={currentOrgId}
        apiBaseUrl={apiBaseUrl}
        onError={handleError}
      />
    </AdminLayoutTabs>
  );
}
