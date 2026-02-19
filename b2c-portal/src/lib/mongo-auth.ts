import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';

/**
 * MongoDB Authentication API Client for B2C Portal
 *
 * This service handles authentication with the MongoDB-based backend
 * authentication system, replacing Supabase authentication.
 */

// Core Backend API configuration
const CORE_API_BASE_URL = import.meta.env.VITE_CORE_API_URL || API_BASE_URL;
const CORE_API_TIMEOUT = 30000; // 30 seconds

export interface MongoUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  display_name: string;
  is_active: boolean;
  is_verified: boolean;
  is_universal_admin?: boolean;
  created_at: string;
  updated_at: string;
  primary_organization_id?: string;
}

export interface MongoOrganization {
  id: string;
  name: string;
  display_name: string;
  description: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MongoAuthResponse {
  success: boolean;
  user: MongoUser;
  access_token: string;
  refresh_token: string;
  expires_at: string;
  organization?: MongoOrganization;
  message: string;
}

export interface MongoSignupRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  organization_name?: string;
}

export interface MongoSigninRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

/**
 * MongoDB Authentication Service
 */
class MongoAuthService {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private user: MongoUser | null = null;
  private organization: MongoOrganization | null = null;

  constructor() {
    // Load stored tokens on initialization
    this.loadStoredAuth();
  }

  /**
   * Load authentication data from localStorage
   */
  private loadStoredAuth(): void {
    try {
      this.accessToken = localStorage.getItem('mongo_access_token');
      this.refreshToken = localStorage.getItem('mongo_refresh_token');

      const storedUser = localStorage.getItem('mongo_user');
      if (storedUser) {
        this.user = JSON.parse(storedUser);
      }

      const storedOrg = localStorage.getItem('mongo_organization');
      if (storedOrg) {
        this.organization = JSON.parse(storedOrg);
      }
    } catch (error) {
      console.error('Error loading stored auth:', error);
      this.clearStoredAuth();
    }
  }

  /**
   * Store authentication data in localStorage
   */
  private storeAuth(authResponse: MongoAuthResponse): void {
    try {
      localStorage.setItem('mongo_access_token', authResponse.access_token);
      localStorage.setItem('mongo_refresh_token', authResponse.refresh_token);
      localStorage.setItem('mongo_user', JSON.stringify(authResponse.user));

      if (authResponse.organization) {
        localStorage.setItem('mongo_organization', JSON.stringify(authResponse.organization));
      }

      this.accessToken = authResponse.access_token;
      this.refreshToken = authResponse.refresh_token;
      this.user = authResponse.user;
      this.organization = authResponse.organization || null;
    } catch (error) {
      console.error('Error storing auth:', error);
    }
  }

  /**
   * Clear stored authentication data
   */
  private clearStoredAuth(): void {
    localStorage.removeItem('mongo_access_token');
    localStorage.removeItem('mongo_refresh_token');
    localStorage.removeItem('mongo_user');
    localStorage.removeItem('mongo_organization');

    this.accessToken = null;
    this.refreshToken = null;
    this.user = null;
    this.organization = null;
  }

  /**
   * Make authenticated request to auth API
   */
  private async authApiRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${CORE_API_BASE_URL}/auth${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(this.accessToken && { 'Authorization': `Bearer ${this.accessToken}` }),
        ...options.headers,
      },
      signal: AbortSignal.timeout(CORE_API_TIMEOUT),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Sign up new user
   */
  async signup(signupData: MongoSignupRequest): Promise<MongoAuthResponse> {
    try {
      const response = await this.authApiRequest<MongoAuthResponse>('/signup', {
        method: 'POST',
        body: JSON.stringify(signupData),
      });

      if (response.success) {
        this.storeAuth(response);
      }

      return response;
    } catch (error) {
      console.error('Signup error:', error);
      throw error;
    }
  }

  /**
   * Sign in user
   */
  async signin(signinData: MongoSigninRequest): Promise<MongoAuthResponse> {
    try {
      const response = await this.authApiRequest<MongoAuthResponse>('/signin', {
        method: 'POST',
        body: JSON.stringify(signinData),
      });

      if (response.success) {
        this.storeAuth(response);
      }

      return response;
    } catch (error) {
      console.error('Signin error:', error);
      throw error;
    }
  }

  /**
   * Sign out user
   */
  async signout(): Promise<void> {
    try {
      if (this.accessToken) {
        await this.authApiRequest('/signout', {
          method: 'POST',
        });
      }
    } catch (error) {
      console.error('Signout error:', error);
      // Don't throw error - we want to clear local state regardless
    } finally {
      this.clearStoredAuth();
    }
  }

  /**
   * Get current user
   */
  async getCurrentUser(): Promise<MongoUser> {
    try {
      if (!this.accessToken) {
        throw new Error('No access token available');
      }

      const response = await this.authApiRequest<MongoUser>('/me');
      this.user = response;
      localStorage.setItem('mongo_user', JSON.stringify(response));

      return response;
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  }

  /**
   * Refresh access token
   */
  async refreshSession(): Promise<MongoAuthResponse> {
    try {
      if (!this.refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await this.authApiRequest<MongoAuthResponse>('/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });

      if (response.success) {
        this.storeAuth(response);
      }

      return response;
    } catch (error) {
      console.error('Refresh session error:', error);
      // If refresh fails, clear auth
      this.clearStoredAuth();
      throw error;
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!(this.accessToken && this.user);
  }

  /**
   * Get current user (cached)
   */
  getUser(): MongoUser | null {
    return this.user;
  }

  /**
   * Get current organization (cached)
   */
  getOrganization(): MongoOrganization | null {
    return this.organization;
  }

  /**
   * Get access token
   */
  getAccessToken(): string | null {
    return this.accessToken;
  }

  /**
   * Get tenant ID (organization ID for compatibility)
   */
  getTenantId(): string | null {
    return this.organization?.id || this.user?.primary_organization_id || this.user?.id || null;
  }

  /**
   * Validate current session
   */
  async validateSession(): Promise<boolean> {
    try {
      if (!this.accessToken) {
        return false;
      }

      await this.getCurrentUser();
      return true;
    } catch (error) {
      // Try to refresh the session
      try {
        await this.refreshSession();
        return true;
      } catch (refreshError) {
        this.clearStoredAuth();
        return false;
      }
    }
  }
}

// Create singleton instance
export const mongoAuth = new MongoAuthService();

// Health check endpoint
export const mongoAuthHealthCheck = async (): Promise<{ status: string; service: string }> => {
  const response = await fetch(`${CORE_API_BASE_URL}/auth/health`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    signal: AbortSignal.timeout(CORE_API_TIMEOUT),
  });

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return response.json();
};