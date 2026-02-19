import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { apiClient } from '@/lib/api';

interface User {
  id: string;
  email: string;
  name: string;
  role: 'user' | 'admin';
  avatar_url?: string;
  bio?: string;
  ministry_name?: string;
  ministry_website?: string;
  subscription_plan?: 'free' | 'pro' | 'ministry';
  reading_streak?: number;
  reading_preferences?: {
    font_size?: 'small' | 'medium' | 'large';
    theme?: 'light' | 'sepia' | 'dark';
    line_height?: 'compact' | 'normal' | 'relaxed';
    notification_time?: string;
    notifications_enabled?: boolean;
  };
  privacy_settings?: {
    profile_visibility?: 'public' | 'private';
    show_reading_history?: boolean;
    show_bookmarks?: boolean;
    show_email?: boolean;
    show_activity?: boolean;
    allow_comments_on_activity?: boolean;
    marketing_emails?: boolean;
    announcement_emails?: boolean;
    notifications_enabled?: boolean;
  };
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (data: {
    email: string;
    password: string;
    name: string;
    role?: 'user' | 'admin';
  }) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (data: Partial<User>) => Promise<void>;
  refreshUser: () => Promise<void>;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * AuthProvider - Manages global authentication state
 * Provides user data, login/logout functions, and auth status
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Load user on mount if tokens exist
  useEffect(() => {
    const loadUser = async () => {
      const accessToken = localStorage.getItem('access_token');

      if (!accessToken) {
        setUser(null);
        setLoading(false);
        return;
      }

      try {
        const userData = await apiClient.getCurrentUser();
        setUser(userData);
      } catch (error) {
        // Silently clear invalid tokens - don't log as error since this is expected when not logged in
        apiClient.clearTokens();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    loadUser();

    // Listen for storage changes (logout from other tabs)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'access_token' && !e.newValue) {
        // Token was removed (logout)
        setUser(null);
        setLoading(false);
      } else if (e.key === 'access_token' && e.newValue && !user) {
        // Token was added (login from other tab)
        loadUser();
      }
    };

    // Listen for custom logout event (same tab)
    const handleLogout = () => {
      setUser(null);
      setLoading(false);
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('auth:logout', handleLogout);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('auth:logout', handleLogout);
    };
  }, []);

  /**
   * Login user with email and password
   */
  const login = async (email: string, password: string) => {
    try {
      const response = await apiClient.login(email, password);
      setUser(response.user);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  /**
   * Register new user
   */
  const signup = async (data: {
    email: string;
    password: string;
    name: string;
    role?: 'user' | 'admin';
  }) => {
    try {
      const signupData = { ...data, role: data.role || 'user' };
      const response = await apiClient.signup(signupData as any);
      setUser(response.user || response);
    } catch (error) {
      console.error('Signup failed:', error);
      throw error;
    }
  };

  /**
   * Logout user and clear tokens
   */
  const logout = async () => {
    try {
      await apiClient.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear tokens and user state
      apiClient.clearTokens();
      setUser(null);
      // Reset loading to false to ensure route guards work immediately
      setLoading(false);
    }
  };

  /**
   * Update user profile
   */
  const updateUser = async (data: Partial<User>) => {
    try {
      const updatedUser = await apiClient.updateProfile(data);
      setUser(updatedUser);
    } catch (error) {
      console.error('Update user failed:', error);
      throw error;
    }
  };

  /**
   * Refresh user data from server
   */
  const refreshUser = async () => {
    try {
      const userData = await apiClient.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Refresh user failed:', error);
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    login,
    signup,
    logout,
    updateUser,
    refreshUser,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin'
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * useAuth hook - Access authentication context
 * Must be used within AuthProvider
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
