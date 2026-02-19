/**
 * Organizations Admin Page - InkWave
 */

import { useEffect } from 'react';
import { OrganizationManagement } from '../../components/admin';
import AdminLayoutTabs from '../../components/admin/AdminLayoutTabs';
import { useAuthStore } from '../../store/authStore';
import { useNavigate } from 'react-router-dom';

export default function OrganizationsPage() {
  useEffect(() => {
    document.title = 'Organizations - InkWave';
  }, []);

  const { user } = useAuthStore();
  const navigate = useNavigate();
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:30033';

  const handleError = (error: string) => {
    console.error('Organization Error:', error);
  };

  return (
    <AdminLayoutTabs
      currentPage="/admin/organizations"
      appName="InkWave"
      user={user ? {
        name: user.user_metadata?.display_name || user.email?.split('@')[0] || 'User',
        email: user.email || 'no-email@example.com'
      } : undefined}
      onBack={() => navigate('/')}
    >
      <OrganizationManagement
        apiBaseUrl={apiBaseUrl}
        onError={handleError}
      />
    </AdminLayoutTabs>
  );
}
