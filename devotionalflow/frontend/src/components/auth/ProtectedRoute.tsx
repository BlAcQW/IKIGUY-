import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

interface ProtectedRouteProps {
	children: React.ReactNode;
}

/**
 * ProtectedRoute - Wrapper component that requires authentication
 * Redirects to /auth if user is not authenticated
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
	const { user, loading } = useAuth();
	const location = useLocation();

	// Immediate synchronous check for token in localStorage
	// This runs on every render to catch direct navigation or stale state
	const hasToken = typeof window !== 'undefined' && !!localStorage.getItem('access_token');

	// CRITICAL: If no token exists, redirect immediately (even during loading)
	// This prevents any flash of content for unauthorized users
	if (!hasToken) {
		return <Navigate to="/auth" state={{ from: location }} replace />;
	}

	// Show nothing while checking authentication (only if token exists)
	if (loading) {
		return (
			<div className="min-h-screen flex items-center justify-center">
				<div className="text-muted-foreground">Loading...</div>
			</div>
		);
	}

	// Check user state - redirect if missing
	if (!user) {
		return <Navigate to="/auth" state={{ from: location }} replace />;
	}

	return <>{children}</>;
}

