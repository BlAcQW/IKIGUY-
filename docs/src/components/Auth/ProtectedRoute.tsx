import React, { useEffect, useState } from 'react';
import { useAuth } from './AuthContext';
import BrowserOnly from '@docusaurus/BrowserOnly';
import Link from '@docusaurus/Link';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'admin' | 'internal' | 'public';
  redirectTo?: string;
}

function ProtectedRouteContent({
  children,
  requiredRole = 'public',
  redirectTo = '/login'
}: ProtectedRouteProps) {
  const { user, loading, token } = useAuth();
  const [isVerifying, setIsVerifying] = useState(true);
  const [hasAccess, setHasAccess] = useState(false);

  useEffect(() => {
    const verifyAccess = async () => {
      if (loading) return;

      // If no token, redirect to login
      if (!token) {
        window.location.href = `${redirectTo}?redirect=${encodeURIComponent(window.location.pathname)}`;
        return;
      }

      // Verify token is still valid
      try {
        const response = await fetch('/api/auth/verify', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          // Token invalid, redirect to login
          window.location.href = `${redirectTo}?redirect=${encodeURIComponent(window.location.pathname)}`;
          return;
        }

        const data = await response.json();

        if (!data.authenticated) {
          window.location.href = `${redirectTo}?redirect=${encodeURIComponent(window.location.pathname)}`;
          return;
        }

        // Check role requirements
        const userRole = data.user.role;
        let hasRequiredAccess = false;

        if (requiredRole === 'admin') {
          hasRequiredAccess = userRole === 'admin';
        } else if (requiredRole === 'internal') {
          hasRequiredAccess = userRole === 'admin' || userRole === 'internal';
        } else {
          hasRequiredAccess = true; // public or any authenticated user
        }

        if (!hasRequiredAccess) {
          setHasAccess(false);
          setIsVerifying(false);
          return;
        }

        setHasAccess(true);
      } catch (error) {
        console.error('Error verifying access:', error);
        window.location.href = `${redirectTo}?redirect=${encodeURIComponent(window.location.pathname)}`;
        return;
      } finally {
        setIsVerifying(false);
      }
    };

    verifyAccess();
  }, [loading, token, requiredRole, redirectTo]);

  if (loading || isVerifying) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '400px',
        flexDirection: 'column',
        gap: '20px'
      }}>
        <div style={{
          width: '50px',
          height: '50px',
          border: '4px solid #f3f3f3',
          borderTop: '4px solid #6366f1',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
        <p>Verifying access...</p>
        <style>
          {`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}
        </style>
      </div>
    );
  }

  if (!hasAccess) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '400px',
        flexDirection: 'column',
        gap: '20px',
        padding: '20px',
        textAlign: 'center'
      }}>
        <div style={{
          fontSize: '64px',
          opacity: 0.3
        }}>
          🔒
        </div>
        <h2>Access Denied</h2>
        <p>You don't have permission to view this content.</p>
        {requiredRole === 'internal' && (
          <p style={{ color: '#666', fontSize: '14px' }}>
            This page requires internal access. Please contact your administrator to upgrade your account.
          </p>
        )}
        {requiredRole === 'admin' && (
          <p style={{ color: '#666', fontSize: '14px' }}>
            This page requires administrator access.
          </p>
        )}
        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <Link
            to="/"
            style={{
              padding: '10px 20px',
              backgroundColor: '#6366f1',
              color: 'white',
              borderRadius: '6px',
              textDecoration: 'none'
            }}
          >
            Go to Home
          </Link>
          <Link
            to={redirectTo}
            style={{
              padding: '10px 20px',
              backgroundColor: '#e5e7eb',
              color: '#374151',
              borderRadius: '6px',
              textDecoration: 'none'
            }}
          >
            Sign In with Different Account
          </Link>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

export default function ProtectedRoute(props: ProtectedRouteProps) {
  return (
    <BrowserOnly fallback={<div>Loading...</div>}>
      {() => <ProtectedRouteContent {...props} />}
    </BrowserOnly>
  );
}
