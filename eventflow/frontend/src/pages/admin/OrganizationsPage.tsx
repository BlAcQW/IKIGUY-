import React from 'react';
import AdminLayoutTabs from '../../components/admin/AdminLayoutTabs';
import { OrganizationManagement } from '../../components/admin';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../../lib/store';

/**
 * Organizations Admin Page - EventFlow
 */

export const OrganizationsPage: React.FC = () => {
  const { user } = useStore();
  const navigate = useNavigate();
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:30032';

  const handleError = (error: string) => {
    console.error('Organization Error:', error);
  };

  return (
    <AdminLayoutTabs
      currentPage="/admin/organizations"
      appName="EventFlow"
      onBack={() => navigate("/home")} user={user ? {
        name: user.name || user.email,
        email: user.email
      } : undefined}
    >
      <OrganizationManagement
        apiBaseUrl={apiBaseUrl}
        onError={handleError}
      />
    </AdminLayoutTabs>
  );
};
