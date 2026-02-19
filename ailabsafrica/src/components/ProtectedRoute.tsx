import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { UserRole, canAccessRoute } from '@/lib/roles';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Shield, Lock } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: UserRole;
  requiredPermission?: {
    resource: string;
    action: string;
  };
  fallback?: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
  requiredPermission,
  fallback
}) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!user) {
    return <Navigate to="/auth" state={{ from: location }} replace />;
  }

  // Get user role from user metadata or default to USER
  const userRole = (user.user_metadata?.role as UserRole) || UserRole.USER;

  // Check route access permission
  if (!canAccessRoute(userRole, location.pathname)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <Lock className="h-5 w-5" />
              Access Denied
            </CardTitle>
            <CardDescription>
              You don't have permission to access this page
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center">
              <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-sm text-muted-foreground">
                This page requires elevated permissions. Please contact your administrator if you believe this is an error.
              </p>
            </div>
            
            <div className="space-y-2">
              <Button asChild className="w-full">
                <Navigate to="/dashboard" replace>
                  Go to Dashboard
                </Navigate>
              </Button>
              
              <Button variant="outline" asChild className="w-full">
                <Navigate to="/" replace>
                  Go Home
                </Navigate>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Check specific role requirement
  if (requiredRole && userRole !== requiredRole) {
    if (fallback) {
      return <>{fallback}</>;
    }
    
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-600">
              <Shield className="h-5 w-5" />
              Role Required
            </CardTitle>
            <CardDescription>
              This page requires the {requiredRole} role
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center">
              <p className="text-sm text-muted-foreground">
                Your current role: <strong>{userRole}</strong>
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Required role: <strong>{requiredRole}</strong>
              </p>
            </div>
            
            <Button asChild className="w-full">
              <Navigate to="/dashboard" replace>
                Go to Dashboard
              </Navigate>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Check specific permission requirement
  if (requiredPermission) {
    const hasPermission = canAccessRoute(userRole, location.pathname);
    if (!hasPermission) {
      if (fallback) {
        return <>{fallback}</>;
      }
      
      return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-red-600">
                <Lock className="h-5 w-5" />
                Permission Required
              </CardTitle>
              <CardDescription>
                You need permission to {requiredPermission.action} {requiredPermission.resource}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild className="w-full">
                <Navigate to="/dashboard" replace>
                  Go to Dashboard
                </Navigate>
              </Button>
            </CardContent>
          </Card>
        </div>
      );
    }
  }

  // All checks passed, render the protected content
  return <>{children}</>;
};

export default ProtectedRoute;
