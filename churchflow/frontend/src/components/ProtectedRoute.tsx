import { Navigate, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'

interface ProtectedRouteProps {
  children: React.ReactNode
}

/**
 * ProtectedRoute component that checks if user is authenticated.
 * Verifies both localStorage token AND active Supabase session.
 * If not authenticated, redirects to login page.
 * Stores the attempted URL to redirect back after login.
 */
export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation()
  const [isChecking, setIsChecking] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token')

      if (!token) {
        setIsAuthenticated(false)
        setIsChecking(false)
        return
      }

      // Verify Supabase session is still valid
      try {
        const { data: { session }, error } = await supabase.auth.getSession()

        if (error || !session) {
          // Session is invalid, clear localStorage
          localStorage.removeItem('access_token')
          localStorage.removeItem('user_id')
          localStorage.removeItem('user_role')
          localStorage.removeItem('user_email')
          setIsAuthenticated(false)
        } else {
          setIsAuthenticated(true)
        }
      } catch (error) {
        console.error('Error checking auth session:', error)
        setIsAuthenticated(false)
      } finally {
        setIsChecking(false)
      }
    }

    checkAuth()
  }, [])

  // Show loading state while checking authentication
  if (isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Verifying authentication...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    // Save the location they were trying to access
    sessionStorage.setItem('redirect_after_login', location.pathname)
    // Redirect to login page
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return <>{children}</>
}
