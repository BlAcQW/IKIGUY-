import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { supabase } from './supabase'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests with automatic refresh
api.interceptors.request.use(async (config) => {
  try {
    // Get current session (Supabase auto-refreshes if needed)
    const { data: { session }, error } = await supabase.auth.getSession()
    
    if (error) {
      console.warn('Session error (may need login):', error.message)
      // Don't try to refresh if there's an error - let the response interceptor handle it
    }
    
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`
    }

    // Add organization ID header
    const orgId = localStorage.getItem('current_organization_id')
    if (orgId) {
      config.headers['X-Organization-ID'] = orgId
    }
  } catch (err) {
    console.error('Error in request interceptor:', err)
  }

  return config
})

// Handle errors with token refresh retry
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Handle 401/422 authentication errors (including "Invalid Refresh Token")
    if ((error.response?.status === 401 || error.response?.status === 422) && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // Check if we have a current session first
        const { data: { session: currentSession } } = await supabase.auth.getSession()
        
        // Only try to refresh if we have a session with a refresh token
        if (currentSession?.refresh_token) {
          const { data: { session }, error: refreshError } = await supabase.auth.refreshSession()
          
          if (!refreshError && session?.access_token) {
            // Refresh succeeded - update header and retry
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${session.access_token}`
            }
            return api(originalRequest)
          }
        }
        
        // No refresh token or refresh failed - redirect to login
        console.warn('Session expired or invalid - redirecting to login')
        await supabase.auth.signOut()
        localStorage.removeItem('current_organization_id')
        window.location.href = '/login'
        return Promise.reject(error)
      } catch (refreshErr) {
        // Refresh failed - redirect to login
        console.error('Error refreshing session:', refreshErr)
        await supabase.auth.signOut()
        localStorage.removeItem('current_organization_id')
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    return Promise.reject(error)
  }
)

export default api
