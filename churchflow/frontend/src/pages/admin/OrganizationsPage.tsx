/**
 * Organizations Admin Page - ChurchFlow
 */

import { useState, useEffect } from 'react';
import AdminLayoutTabs from '../../components/admin/AdminLayoutTabs';
import { OrganizationManagement } from '../../components/admin';

interface User {
  id: string;
  name: string;
  email?: string;
  phone?: string;
}

export default function OrganizationsPage() {
  const [user, setUser] = useState<User | null>(null);
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

  const handleError = (error: string) => {
    console.error('Organization Error:', error);
  };

  return (
    <AdminLayoutTabs
      currentPage="/admin/organizations"
      appName="ChurchFlow"
      onBack={() => window.location.href = "/dashboard"} user={user ? {
        name: user.name,
        email: user.email || user.phone || ''
      } : undefined}
    >
      <OrganizationManagement
        apiBaseUrl={apiBaseUrl}
        onError={handleError}
      />
    </AdminLayoutTabs>
  );
}
