/**
 * Authentication Context for EstateFlow.
 *
 * Provides authentication state and methods throughout the application.
 */

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, Session, AuthError } from '@supabase/supabase-js';
import { supabase } from '@/lib/supabase';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{ error: AuthError | null }>;
  signUp: (
    email: string,
    password: string,
    metadata?: { first_name?: string; last_name?: string; [key: string]: any }
  ) => Promise<{ error: AuthError | null }>;
  signOut: () => Promise<void>;
  getAccessToken: () => string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    return { error };
  };

  /**
   * Sign up a new user.
   *
   * Email confirmation is DISABLED in Supabase dashboard (Authentication → Email → Confirm email).
   * Users have immediate access after signup without email verification.
   * This provides a frictionless onboarding experience.
   *
   * Important: Email confirmation must be disabled in Supabase project settings,
   * not just in the client code. Check dashboard if signup errors occur.
   *
   * @param email - User's email address
   * @param password - User's password (min 8 characters)
   * @param metadata - Optional user metadata (first_name, last_name, etc)
   * @returns Auth response with error if signup failed
   */
  const signUp = async (
    email: string,
    password: string,
    metadata?: { first_name?: string; last_name?: string; [key: string]: any }
  ) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: metadata || {},
        // Email confirmation is disabled in Supabase dashboard settings
        // No emailRedirectTo needed since confirmation is off
      },
    });
    return { error };
  };

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  const getAccessToken = () => {
    return session?.access_token ?? null;
  };

  const value = {
    user,
    session,
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
