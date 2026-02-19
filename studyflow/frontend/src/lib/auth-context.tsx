/**
 * Authentication Context
 *
 * Manages user authentication state and provides auth methods.
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, Session } from '@supabase/supabase-js';
import supabase from './supabase';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, fullName: string, role: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);

      // Store token in localStorage for API requests
      if (session?.access_token) {
        localStorage.setItem('auth_token', session.access_token);
        localStorage.setItem('access_token', session.access_token);
      } else {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('access_token');
      }

      setLoading(false);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);

      // Update token in localStorage
      if (session?.access_token) {
        localStorage.setItem('auth_token', session.access_token);
        localStorage.setItem('access_token', session.access_token);
      } else {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('access_token');
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const signIn = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) throw error;

    // Store token (both keys for consistency)
    if (data.session?.access_token) {
      localStorage.setItem('auth_token', data.session.access_token);
      localStorage.setItem('access_token', data.session.access_token);
    }
  };

  const signUp = async (email: string, password: string, fullName: string, role: string) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
          role: role,
        },
      },
    });

    if (error) throw error;

    // Store token (both keys for consistency)
    if (data.session?.access_token) {
      localStorage.setItem('auth_token', data.session.access_token);
      localStorage.setItem('access_token', data.session.access_token);
    }
  };

  const signOut = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;

    // Clear all auth-related items
    localStorage.removeItem('auth_token');
    localStorage.removeItem('access_token');
    localStorage.removeItem('current_organization_id');
  };

  const value = {
    user,
    session,
    loading,
    signIn,
    signUp,
    signOut,
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
