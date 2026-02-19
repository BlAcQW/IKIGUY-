/**
 * Platform Admin Page - ChurchFlow SaaS
 *
 * Dashboard for platform owners to manage all churches.
 * Requires universal admin permissions.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminLayoutTabs from '../../components/admin/AdminLayoutTabs';
import { PlatformAdminDashboard } from '../../components/admin';

interface User {
  id: string;
  name: string;
  email?: string;
  phone?: string;
}

export default function PlatformAdminPage() {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string>('');
  const [authorized, setAuthorized] = useState<boolean | null>(null);
  const navigate = useNavigate();
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:30030';

  useEffect(() => {
    checkAuthorization();
  }, []);

  const checkAuthorization = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setAuthorized(false);
      return;
    }

    try {
      // Fetch user info
      const userResponse = await fetch(`${apiBaseUrl}/api/v1/users/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!userResponse.ok) {
        throw new Error('Failed to fetch user');
      }

      const userData = await userResponse.json();
      setUser({
        id: userData.id,
        name: userData.name || 'Admin',
        email: userData.email,
        phone: userData.phone,
      });

      // Check if user is platform admin by attempting to fetch dashboard
      const dashboardResponse = await fetch(`${apiBaseUrl}/api/v1/platform-admin/dashboard`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (dashboardResponse.status === 403) {
        setAuthorized(false);
        setError('Access denied. Platform admin permissions required.');
      } else if (!dashboardResponse.ok) {
        throw new Error('Failed to verify authorization');
      } else {
        setAuthorized(true);
      }
    } catch (error: any) {
      console.error('Authorization check failed:', error);
      setError(error.message || 'Authorization check failed');
      setAuthorized(false);
    }
  };

  if (authorized === null) {
    return (
      <AdminLayoutTabs
        currentPage="/admin/platform"
        appName="ChurchFlow"
        onBack={() => navigate('/dashboard')}
        user={user ? { name: user.name, email: user.email || user.phone || '' } : undefined}
      >
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-4">Verifying permissions...</p>
          </div>
        </div>
      </AdminLayoutTabs>
    );
  }

  if (!authorized) {
    return (
      <AdminLayoutTabs
        currentPage="/admin/platform"
        appName="ChurchFlow"
        onBack={() => navigate('/dashboard')}
        user={user ? { name: user.name, email: user.email || user.phone || '' } : undefined}
      >
        <div className="text-center py-12">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
            <h2 className="text-xl font-bold text-red-800 mb-2">Access Denied</h2>
            <p className="text-red-700 mb-4">
              {error || 'You do not have platform admin permissions.'}
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      </AdminLayoutTabs>
    );
  }

  return (
    <AdminLayoutTabs
      currentPage="/admin/platform"
      appName="ChurchFlow"
      onBack={() => navigate('/dashboard')}
      user={user ? { name: user.name, email: user.email || user.phone || '' } : undefined}
    >
      <PlatformAdminDashboard
        apiBaseUrl={apiBaseUrl}
        onError={(msg) => setError(msg)}
      />
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-50 border border-red-200 rounded-lg p-4 max-w-md shadow-lg">
          <p className="text-red-800 text-sm">{error}</p>
          <button
            onClick={() => setError('')}
            className="text-red-600 text-xs hover:underline mt-2"
          >
            Dismiss
          </button>
        </div>
      )}
    </AdminLayoutTabs>
  );
}
