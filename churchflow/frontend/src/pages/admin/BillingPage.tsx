/**
 * Organization Billing Admin Page - ChurchFlow
 */

import { useState, useEffect } from 'react';
import AdminLayoutTabs from '../../components/admin/AdminLayoutTabs';
import { SubscriptionBilling } from '../../components/admin';

interface User {
  id: string;
  name: string;
  email?: string;
  phone?: string;
}

export default function BillingPage() {
  const [user, setUser] = useState<User | null>(null);
  const [currentOrgId, setCurrentOrgId] = useState<string>('');
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:30030';

  useEffect(() => {
    fetchUser();
    const orgId = localStorage.getItem('current_organization_id');
    if (orgId) setCurrentOrgId(orgId);
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

  if (!currentOrgId) {
    return (
      <AdminLayoutTabs currentPage="/admin/billing" appName="ChurchFlow" onBack={() => window.location.href = "/dashboard"} user={user ? {
        name: user.name,
        email: user.email || user.phone || ''
      } : undefined}>
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
    <AdminLayoutTabs currentPage="/admin/billing" appName="ChurchFlow" onBack={() => window.location.href = "/dashboard"} user={user ? {
      name: user.name,
      email: user.email || user.phone || ''
    } : undefined}>
      <SubscriptionBilling
        organizationId={currentOrgId}
        apiBaseUrl={apiBaseUrl}
        onError={(msg) => console.error(msg)}
      />
    </AdminLayoutTabs>
  );
}
