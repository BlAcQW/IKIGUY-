import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { AdminSidebar } from '@/components/admin/AdminSidebar';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import { useOrganization } from '@/contexts/OrganizationContext';
import { Loader2, ShieldAlert } from 'lucide-react';

export default function AdminLayout() {
  const { user, isLoading: authLoading } = useMongoAuth();
  const { canAccessAdmin, isLoading: orgLoading } = useOrganization();

  const isLoading = authLoading || orgLoading;

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  // Check if user is authenticated
  if (!user) {
    return <Navigate to="/auth" replace />;
  }

  // Check if user has admin access
  if (!canAccessAdmin) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center space-y-4 p-8 max-w-md">
          <ShieldAlert className="h-16 w-16 text-destructive mx-auto" />
          <h1 className="text-2xl font-bold text-heading">Access Denied</h1>
          <p className="text-muted-foreground">
            You don't have permission to access the admin panel.
            Please contact your organization administrator if you believe this is an error.
          </p>
          <button
            onClick={() => window.location.href = '/dashboard'}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 mt-4"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background">
      <DashboardSidebar />
      <div className="flex-1 flex">
        <AdminSidebar />
        <div className="flex-1 overflow-auto">
          <Outlet />
        </div>
      </div>
    </div>
  );
}