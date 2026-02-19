/**
 * Organizations Admin Page - StudyFlow
 */

import React from 'react';
import { OrganizationManagement } from '../../components/admin';
import AdminLayoutTabs from '../../components/admin/AdminLayoutTabs';
import { useAuth } from '../../lib/auth-context';
import { useNavigate } from 'react-router-dom';

export default function OrganizationsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:30031';

  const handleError = (error: string) => {
    console.error('Organization Error:', error);
  };

  return (
    <AdminLayoutTabs
      currentPage="/admin/organizations"
      appName="StudyFlow"
      user={user ? {
        name: user.name || user.email,
        email: user.email
      } : undefined}
      onBack={() => navigate('/dashboard')}
    >
      <OrganizationManagement
        apiBaseUrl={apiBaseUrl}
        onError={handleError}
      />
    </AdminLayoutTabs>
  );
}
