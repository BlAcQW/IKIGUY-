import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase } from '@/integrations/supabase/client';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signUp: (email: string, password: string, metadata?: any) => Promise<{ error?: any }>;
  signIn: (email: string, password: string) => Promise<{ error?: any }>;
  signOut: () => Promise<void>;
  refreshSession: () => Promise<void>;
  isSessionExpired: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [isSessionExpired, setIsSessionExpired] = useState(false);

  useEffect(() => {
    console.log('[AuthContext] Setting up auth state listener');
    
    // Set up auth state listener FIRST
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.info(`Auth state change: ${event}`, {
          event,
          userId: session?.user?.id,
          userEmail: session?.user?.email,
          hasSession: !!session,
          sessionExpiry: session?.expires_at ? new Date(session.expires_at * 1000).toISOString() : null
        });
        
        setSession(session);
        setUser(session?.user ?? null);
        setIsSessionExpired(false);
        setLoading(false);
        
        // Handle session expiration
        if (event === 'TOKEN_REFRESHED') {
          if (!session) {
            console.log('[AuthContext] Token refresh failed - session expired');
            setIsSessionExpired(true);
            setUser(null);
            setSession(null);
          } else {
            console.log('[AuthContext] Token refreshed successfully');
            setIsSessionExpired(false);
          }
        }
        
        // If session expired, clear everything
        if (event === 'SIGNED_OUT') {
          if (!session) {
            console.log('[AuthContext] Clearing user state due to sign out');
            setUser(null);
            setSession(null);
            setIsSessionExpired(false);
          }
        }
      }
    );

    // THEN check for existing session
    console.log('[AuthContext] Checking for existing session');
    supabase.auth.getSession().then(({ data: { session }, error }) => {
      if (error) {
        console.error('[AuthContext] Session error:', {
          error: error.message,
          status: error.status,
          name: error.name
        });
        setUser(null);
        setSession(null);
      } else {
        console.log('[AuthContext] Initial session check:', {
          hasSession: !!session,
          userId: session?.user?.id,
          userEmail: session?.user?.email,
          sessionExpiry: session?.expires_at ? new Date(session.expires_at * 1000).toISOString() : null
        });
        setSession(session);
        setUser(session?.user ?? null);
      }
      setLoading(false);
    });

    return () => {
      console.log('[AuthContext] Cleaning up auth subscription');
      subscription.unsubscribe();
    };
  }, []);

  const signUp = async (email: string, password: string, metadata?: any) => {
    console.log('[AuthContext] Starting sign up process', {
      email,
      hasPassword: !!password,
      redirectUrl: `${window.location.origin}/`,
      metadata: metadata ? Object.keys(metadata) : []
    });
    
    const redirectUrl = `${window.location.origin}/`;
    
    try {
      const { error, data } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: redirectUrl,
          data: metadata
        }
      });
      
      if (error) {
        console.error('[AuthContext] Sign up error:', {
          message: error.message,
          status: error.status,
          name: error.name,
          details: error
        });
        
        // Handle specific error cases
        if (error.message.includes('Password')) {
          console.error('[AuthContext] Password validation error:', error.message);
        } else if (error.message.includes('Email')) {
          console.error('[AuthContext] Email validation error:', error.message);
        } else if (error.status === 500) {
          console.error('[AuthContext] Server error during signup:', error.message);
        }
      } else {
        console.log('[AuthContext] Sign up successful:', {
          userId: data.user?.id,
          email: data.user?.email,
          needsConfirmation: !data.session,
          sessionExists: !!data.session
        });
      }
      
      return { error };
    } catch (catchError) {
      console.error('[AuthContext] Unexpected error during signup:', catchError);
      return { 
        error: { 
          message: 'An unexpected error occurred during signup. Please try again.',
          status: 500 
        } 
      };
    }
  };

  const signIn = async (email: string, password: string) => {
    console.log('[AuthContext] Starting sign in process', {
      email,
      hasPassword: !!password,
      timestamp: new Date().toISOString()
    });
    
    const { error, data } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    
    if (error) {
      console.error('[AuthContext] Sign in error:', {
        message: error.message,
        status: error.status,
        name: error.name,
        email
      });
    } else {
      console.log('[AuthContext] Sign in successful:', {
        userId: data.user?.id,
        email: data.user?.email,
        hasSession: !!data.session
      });
    }
    
    return { error };
  };

  const refreshSession = async () => {
    console.log('[AuthContext] Attempting to refresh session');
    
    try {
      const { data, error } = await supabase.auth.refreshSession();
      
      if (error) {
        console.error('[AuthContext] Session refresh error:', error);
        setIsSessionExpired(true);
        setUser(null);
        setSession(null);
      } else {
        console.log('[AuthContext] Session refreshed successfully');
        setSession(data.session);
        setUser(data.user);
        setIsSessionExpired(false);
      }
    } catch (error) {
      console.error('[AuthContext] Session refresh failed:', error);
      setIsSessionExpired(true);
      setUser(null);
      setSession(null);
    }
  };

  const signOut = async () => {
    console.log('[AuthContext] Starting sign out process', {
      currentUserId: user?.id,
      currentUserEmail: user?.email
    });
    
    const { error } = await supabase.auth.signOut();
    
    if (error) {
      console.error('[AuthContext] Sign out error:', {
        message: error.message,
        status: error.status
      });
    } else {
      console.log('[AuthContext] Sign out successful');
      setIsSessionExpired(false);
    }
  };

  const value = {
    user,
    session,
    loading,
    signUp,
    signIn,
    signOut,
    refreshSession,
    isSessionExpired,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};