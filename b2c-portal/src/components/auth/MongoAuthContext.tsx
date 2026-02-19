/**
 * MongoDB Authentication Context
 * Provides global authentication state and methods using MongoDB backend
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { mongoAuth, MongoUser, MongoOrganization, MongoSignupRequest, MongoSigninRequest } from '@/lib/mongo-auth';
import { useToast } from '@/hooks/use-toast';

interface MongoAuthContextType {
  user: MongoUser | null;
  organization: MongoOrganization | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  signUp: (signupData: MongoSignupRequest) => Promise<void>;
  signIn: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  signOut: () => Promise<void>;
  refreshSession: () => Promise<void>;
  getTenantId: () => string | null;
  getAccessToken: () => string | null;
}

const MongoAuthContext = createContext<MongoAuthContextType | undefined>(undefined);

export const useMongoAuth = () => {
  const context = useContext(MongoAuthContext);
  if (!context) {
    throw new Error('useMongoAuth must be used within a MongoAuthProvider');
  }
  return context;
};

interface MongoAuthProviderProps {
  children: React.ReactNode;
}

export const MongoAuthProvider: React.FC<MongoAuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<MongoUser | null>(null);
  const [organization, setOrganization] = useState<MongoOrganization | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const { toast } = useToast();

  // Update state from auth service
  const updateAuthState = useCallback(() => {
    const currentUser = mongoAuth.getUser();
    const currentOrg = mongoAuth.getOrganization();
    const authenticated = mongoAuth.isAuthenticated();

    setUser(currentUser);
    setOrganization(currentOrg);
    setIsAuthenticated(authenticated);
  }, []);

  // Initialize authentication state
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        setIsLoading(true);

        // Check if we have stored authentication
        if (mongoAuth.isAuthenticated()) {
          // Validate the session (this will call /me to refresh user data)
          const isValid = await mongoAuth.validateSession();
          if (isValid) {
            updateAuthState();

            // Force refresh if is_universal_admin is missing (for existing sessions)
            const currentUser = mongoAuth.getUser();
            if (currentUser && currentUser.is_universal_admin === undefined) {
              console.log('User missing is_universal_admin field, refreshing user data...');
              try {
                await mongoAuth.getCurrentUser();
                updateAuthState();
              } catch (error) {
                console.error('Failed to refresh user data:', error);
              }
            }
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        // Clear invalid auth state
        await mongoAuth.signout();
        updateAuthState();
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, [updateAuthState]);

  const signUp = async (signupData: MongoSignupRequest) => {
    setIsLoading(true);
    try {
      const response = await mongoAuth.signup(signupData);

      if (response.success) {
        updateAuthState();
        toast({
          title: 'Account Created',
          description: `Welcome to KasaAI, ${response.user.display_name}!`,
        });
      } else {
        throw new Error(response.message || 'Signup failed');
      }
    } catch (error) {
      console.error('Sign up error:', error);
      toast({
        title: 'Sign Up Failed',
        description: error instanceof Error ? error.message : 'Failed to create account',
        variant: 'destructive',
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const signIn = async (email: string, password: string, rememberMe: boolean = false) => {
    setIsLoading(true);
    try {
      const response = await mongoAuth.signin({
        email,
        password,
        remember_me: rememberMe,
      });

      if (response.success) {
        updateAuthState();
        toast({
          title: 'Welcome back!',
          description: `Signed in as ${response.user.email}`,
        });
      } else {
        throw new Error(response.message || 'Sign in failed');
      }
    } catch (error) {
      console.error('Sign in error:', error);
      toast({
        title: 'Sign In Failed',
        description: error instanceof Error ? error.message : 'Failed to sign in',
        variant: 'destructive',
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const signOut = async () => {
    setIsLoading(true);
    try {
      await mongoAuth.signout();
      updateAuthState();
      toast({
        title: 'Signed out',
        description: 'You have been signed out successfully',
      });
    } catch (error) {
      console.error('Sign out error:', error);
      // Still update state even if API call fails
      updateAuthState();
      toast({
        title: 'Signed out',
        description: 'You have been signed out',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const refreshSession = async () => {
    try {
      await mongoAuth.refreshSession();
      updateAuthState();
    } catch (error) {
      console.error('Refresh session error:', error);
      // If refresh fails, user needs to sign in again
      updateAuthState();
      toast({
        title: 'Session Expired',
        description: 'Please sign in again',
        variant: 'destructive',
      });
      throw error;
    }
  };

  const getTenantId = (): string | null => {
    return mongoAuth.getTenantId();
  };

  const getAccessToken = (): string | null => {
    return mongoAuth.getAccessToken();
  };

  const value: MongoAuthContextType = {
    user,
    organization,
    isLoading,
    isAuthenticated,
    signUp,
    signIn,
    signOut,
    refreshSession,
    getTenantId,
    getAccessToken,
  };

  return (
    <MongoAuthContext.Provider value={value}>
      {children}
    </MongoAuthContext.Provider>
  );
};