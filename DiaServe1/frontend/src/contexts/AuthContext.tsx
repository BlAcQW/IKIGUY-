/**
 * Authentication Context for EstateFlow.
 *
 * Standalone local authentication - no external services required.
 */

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import {
  API_BASE_URL,
  API_ENDPOINTS,
  getAuthToken,
  setAuthToken,
  removeAuthToken,
  getDefaultHeaders,
  USE_MOCK_DATA
} from '@/lib/api-config';
import { mockFetch } from '@/lib/mock-api';

// User type
interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
}

// Auth context type
interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
  signUp: (
    email: string,
    password: string,
    metadata?: { first_name?: string; last_name?: string }
  ) => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
  getAccessToken: () => string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);


export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Helper to choose fetch implementation
  const apiFetch = async (url: string, options?: RequestInit) => {
    if (USE_MOCK_DATA) {
      return mockFetch(url, options);
    }
    return fetch(url, options);
  };

  // Check for existing session on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = getAuthToken();
      if (token) {
        try {
          // Verify token by fetching user info
          const response = await apiFetch(`${API_BASE_URL}${API_ENDPOINTS.auth.me}`, {
            headers: getDefaultHeaders(token),
          });

          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
          } else {
            // Token invalid, remove it
            removeAuthToken();
          }
        } catch (error) {
          console.error('Auth check failed:', error);
          removeAuthToken();
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const signIn = async (email: string, password: string) => {
    try {
      const response = await apiFetch(`${API_BASE_URL}${API_ENDPOINTS.auth.login}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const data = await response.json();

      // Store token and user
      setAuthToken(data.access_token);
      setUser(data.user);

      return { error: null };
    } catch (error) {
      return { error: error as Error };
    }
  };

  const signUp = async (
    email: string,
    password: string,
    metadata?: { first_name?: string; last_name?: string }
  ) => {
    try {
      const response = await apiFetch(`${API_BASE_URL}${API_ENDPOINTS.auth.signup}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          first_name: metadata?.first_name || '',
          last_name: metadata?.last_name || '',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Sign up failed');
      }

      const data = await response.json();

      // Store token and user
      setAuthToken(data.access_token);
      setUser(data.user);

      return { error: null };
    } catch (error) {
      return { error: error as Error };
    }
  };

  const signOut = async () => {
    try {
      const token = getAuthToken();
      if (token) {
        // Optional: Call logout endpoint
        await apiFetch(`${API_BASE_URL}${API_ENDPOINTS.auth.logout}`, {
          method: 'POST',
          headers: getDefaultHeaders(token),
        }).catch(() => { });
      }
    } finally {
      removeAuthToken();
      setUser(null);
    }
  };


  const getAccessToken = () => {
    return getAuthToken();
  };

  const value = {
    user,
    loading,
    signIn,
    signUp,
    signOut,
    getAccessToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
