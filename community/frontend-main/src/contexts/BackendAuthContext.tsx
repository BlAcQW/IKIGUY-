import React, { createContext, useContext, useEffect, useState } from 'react'

// Backend user type (matches backend User model)
export interface BackendUser {
  id: string
  email: string
  username?: string
  full_name?: string
  avatar_url?: string
  bio?: string
  location?: string
  languages_spoken: string[]
  language_expertise: any[]
  level: string
  total_points: number
  level_points: number
  achievements: string[]
  badges: string[]
  verified_languages: string[]
  can_validate: boolean
  can_moderate: boolean
  contributions_count: number
  validations_count: number
  quality_rating: number
  reputation_score: number
  is_active: boolean
  created_at: string
}

interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

interface AuthContextType {
  user: BackendUser | null
  tokens: AuthTokens | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>
  signUp: (email: string, password: string, full_name?: string) => Promise<{ error: Error | null }>
  signOut: () => Promise<{ error: Error | null }>
  updateProfile: (updates: Partial<BackendUser>) => Promise<{ error: any | null }>
  refreshProfile: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://language-community-api.ailabsafrica.com/api/v1'

// Token storage keys
const ACCESS_TOKEN_KEY = 'auth_access_token'
const REFRESH_TOKEN_KEY = 'auth_refresh_token'
const USER_DATA_KEY = 'auth_user_data'

export function BackendAuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<BackendUser | null>(null)
  const [tokens, setTokens] = useState<AuthTokens | null>(null)
  const [loading, setLoading] = useState(true)

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedAccessToken = localStorage.getItem(ACCESS_TOKEN_KEY)
        const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
        const storedUserData = localStorage.getItem(USER_DATA_KEY)

        if (storedAccessToken && storedRefreshToken && storedUserData) {
          const userData = JSON.parse(storedUserData)
          setUser(userData)
          setTokens({
            access_token: storedAccessToken,
            refresh_token: storedRefreshToken,
            token_type: 'bearer'
          })

          // Validate token by fetching current user
          await loadCurrentUser(storedAccessToken)
        }
      } catch (error) {
        console.error('Error initializing auth:', error)
        clearAuthData()
      } finally {
        setLoading(false)
      }
    }

    initAuth()
  }, [])

  const clearAuthData = () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_DATA_KEY)
    setUser(null)
    setTokens(null)
  }

  const saveAuthData = (accessToken: string, refreshToken: string, userData: BackendUser) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
    localStorage.setItem(USER_DATA_KEY, JSON.stringify(userData))
    setTokens({
      access_token: accessToken,
      refresh_token: refreshToken,
      token_type: 'bearer'
    })
    setUser(userData)
  }

  const loadCurrentUser = async (accessToken: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/profile`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Failed to load user profile')
      }

      const result = await response.json()
      const userData = result.data || result

      setUser(userData)
      localStorage.setItem(USER_DATA_KEY, JSON.stringify(userData))
    } catch (error) {
      console.error('Error loading current user:', error)
      clearAuthData()
      throw error
    }
  }

  const signIn = async (email: string, password: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Login failed')
      }

      const authResult = await response.json()

      // authResult should have: { user, access_token, refresh_token, token_type }
      saveAuthData(authResult.access_token, authResult.refresh_token, authResult.user)

      return { error: null }
    } catch (error: any) {
      console.error('Sign in error:', error)
      return { error }
    }
  }

  const signUp = async (email: string, password: string, full_name?: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email,
          password,
          full_name,
          username: email.split('@')[0]
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Registration failed')
      }

      const result = await response.json()
      const newUser = result.data || result

      // After registration, auto-login
      const loginResult = await signIn(email, password)
      return loginResult

    } catch (error: any) {
      console.error('Sign up error:', error)
      return { error }
    }
  }

  const signOut = async () => {
    try {
      // Call backend logout endpoint if we have a token
      if (tokens?.access_token) {
        await fetch(`${API_BASE_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${tokens.access_token}`,
            'Content-Type': 'application/json'
          }
        })
      }

      clearAuthData()
      return { error: null }
    } catch (error: any) {
      console.error('Sign out error:', error)
      clearAuthData() // Clear local data even if backend call fails
      return { error }
    }
  }

  const updateProfile = async (updates: Partial<BackendUser>) => {
    if (!user || !tokens?.access_token) {
      return { error: new Error('No user logged in') }
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${tokens.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      })

      if (!response.ok) {
        throw new Error('Profile update failed')
      }

      const result = await response.json()
      const updatedUser = result.data || result

      setUser(updatedUser)
      localStorage.setItem(USER_DATA_KEY, JSON.stringify(updatedUser))

      return { error: null }
    } catch (error) {
      console.error('Profile update error:', error)
      return { error }
    }
  }

  const refreshProfile = async () => {
    if (tokens?.access_token) {
      await loadCurrentUser(tokens.access_token)
    }
  }

  const value = {
    user,
    tokens,
    loading,
    signIn,
    signUp,
    signOut,
    updateProfile,
    refreshProfile,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useBackendAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useBackendAuth must be used within a BackendAuthProvider')
  }
  return context
}
