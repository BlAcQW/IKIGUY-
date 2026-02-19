/**
 * Role-Protected Route Component
 * Redirects based on user role permissions
 */

import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useProfile } from '../hooks/useProfile';

type Role = 'author' | 'admin' | 'superadmin' | 'universal_admin';

interface RoleProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles: Role[];
  fallbackPath?: string;
}

export default function RoleProtectedRoute({
  children,
  allowedRoles,
  fallbackPath = '/'
}: RoleProtectedRouteProps) {
  const { user, loading: authLoading } = useAuthStore();
  const { data: profileData, isLoading: profileLoading } = useProfile();
  const location = useLocation();

  // Show loading while auth or profile is loading
  if (authLoading || profileLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check if user has required role
  const userRole = profileData?.role as Role | undefined;
  const isAdmin = profileData?.is_admin === true;

  // Check role access
  const hasAccess =
    // Direct role match
    (userRole && allowedRoles.includes(userRole)) ||
    // is_admin flag grants admin access
    (isAdmin && (allowedRoles.includes('admin') || allowedRoles.includes('superadmin'))) ||
    // universal_admin and superadmin have access to everything
    userRole === 'universal_admin' ||
    userRole === 'superadmin';

  if (!hasAccess) {
    // Redirect to fallback path if no access
    return <Navigate to={fallbackPath} replace />;
  }

  return <>{children}</>;
}
