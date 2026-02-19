/**
 * Global Axios Configuration
 *
 * Configures axios with automatic token refresh on 401 errors
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { exchangeToken } from './api'
import { encodeHeaderValue, sanitizeToken } from './header-utils'

// Configure base URL for API requests
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://churchflow-api.ailabsafrica.com'

// Create axios instance with base URL
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Flag to prevent multiple simultaneous token refresh attempts
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: unknown) => void
  reject: (reason?: unknown) => void
}> = []

const processQueue = (error: Error | null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve()
    }
  })

  failedQueue = []
}

// Request interceptor - add token and organization ID to all requests
axiosInstance.interceptors.request.use(
  (config) => {
    const rawToken = localStorage.getItem('access_token')
    const token = sanitizeToken(rawToken)
    const orgId = localStorage.getItem('current_organization_id')
    const encodedOrgId = encodeHeaderValue(orgId)

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Add organization ID if available (base64-encoded to support Unicode chars)
    if (encodedOrgId && config.headers) {
      config.headers['X-Organization-ID'] = encodedOrgId
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle 401 errors
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    // If error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then(() => {
            // Retry the original request with new token
            const rawToken = localStorage.getItem('access_token')
            const token = sanitizeToken(rawToken)
            if (token && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`
            }
            return axiosInstance(originalRequest)
          })
          .catch((err) => {
            return Promise.reject(err)
          })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        // Exchange token
        const rawNewToken = await exchangeToken()
        const newToken = sanitizeToken(rawNewToken)

        if (newToken) {
          localStorage.setItem('access_token', newToken)

          // Update authorization header
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`
          }

          // Process queued requests
          processQueue(null)

          // Retry original request
          return axiosInstance(originalRequest)
        } else {
          throw new Error('Invalid token received from exchange')
        }
      } catch (refreshError) {
        // Token refresh failed - logout
        processQueue(refreshError as Error)

        localStorage.removeItem('access_token')
        localStorage.removeItem('user_id')
        localStorage.removeItem('user_role')
        localStorage.removeItem('user_email')
        sessionStorage.clear()

        window.location.href = '/login?expired=true'

        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default axiosInstance
