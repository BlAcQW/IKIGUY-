import { useState } from 'react'
import { Mail, Key } from 'lucide-react'
import { supabase } from '../lib/supabase'
import { exchangeToken } from '../lib/api'
import { sanitizeToken } from '../lib/header-utils'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Supabase email/password authentication
  const handleSupabaseLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const { data, error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (authError) {
        throw authError
      }

      if (!data.session) {
        throw new Error('No session returned')
      }

      // Store Supabase token temporarily for exchange (sanitize first)
      const supabaseToken = sanitizeToken(data.session.access_token)
      if (supabaseToken) {
        localStorage.setItem('access_token', supabaseToken)
      }
      localStorage.setItem('user_id', data.user.id)
      localStorage.setItem('user_email', data.user.email || '')

      console.log('Login successful with Supabase authentication')

      // Exchange Supabase token for backend JWT
      try {
        const rawBackendToken = await exchangeToken()
        const backendToken = sanitizeToken(rawBackendToken)
        // Replace Supabase token with backend JWT (sanitize first)
        if (backendToken) {
          localStorage.setItem('access_token', backendToken)
        }
        console.log('Token exchange successful - using backend JWT')
      } catch (exchangeError: any) {
        console.error('Token exchange failed:', exchangeError)
        throw new Error(`Token exchange failed: ${exchangeError.message}`)
      }

      // Fetch user's organizations and set default
      try {
        const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:30030'
        const orgResponse = await fetch(`${apiBaseUrl}/api/v1/organizations`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        })

        if (orgResponse.ok) {
          const organizations = await orgResponse.json()

          // Set default organization to Action Chapel International for all users
          // This handles both single-org users and universal admins
          const aciOrg = organizations.find((m: any) =>
            m.organization?.name === 'action-chapel-international' ||
            m.organization?.display_name === 'Action Chapel International'
          )

          if (aciOrg) {
            localStorage.setItem('current_organization_id', aciOrg.organization.id)
            console.log('Default organization set to Action Chapel International')
          } else if (organizations.length > 0) {
            // Fallback to first organization if ACI not found
            localStorage.setItem('current_organization_id', organizations[0].organization.id)
            console.log('Default organization set to first available')
          }
        }
      } catch (orgError) {
        console.error('Failed to fetch organizations:', orgError)
        // Don't throw - continue with login even if org fetch fails
      }

      // Redirect to intended page or dashboard
      const redirectPath = sessionStorage.getItem('redirect_after_login') || '/dashboard'
      sessionStorage.removeItem('redirect_after_login')
      window.location.href = redirectPath
    } catch (err: any) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-sm w-full">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4">
            <Key className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">ChurchFlow</h1>
          <p className="text-gray-500 text-sm">Sign in to admin dashboard</p>
        </div>

        <div className="card">
          <form onSubmit={handleSupabaseLogin} className="space-y-4">
            <div>
              <label className="label">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input pl-10 min-h-[44px] text-base"
                  placeholder="admin@ailabsafrica.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="label">Password</label>
              <div className="relative">
                <Key className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input pl-10 min-h-[44px] text-base"
                  placeholder="Enter password"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-2.5 min-h-[48px] touch-manipulation"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          Secure authentication powered by Supabase
        </p>
      </div>
    </div>
  )
}
