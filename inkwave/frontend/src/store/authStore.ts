/**
 * Auth Store (Zustand)
 * Manages authentication state
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, Session } from '@supabase/supabase-js';
import { supabase, authHelpers } from '../lib/supabase';
import toast from 'react-hot-toast';

interface SignupResult {
  success: boolean;
  error?: string;
  invitationRedeemed?: boolean;
  libraryBook?: {
    book_id: string;
    book_title: string;
    book_cover_url?: string;
  };
}

interface AuthState {
  user: User | null;
  session: Session | null;
  loading: boolean;
  initialized: boolean;

  // Actions
  initialize: () => Promise<void>;
  signUp: (email: string, password: string, invitationToken?: string) => Promise<SignupResult>;
  signIn: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signInWithGoogle: () => Promise<{ success: boolean; error?: string }>;
  signOut: () => Promise<void>;
  setUser: (user: User | null) => void;
  setSession: (session: Session | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      session: null,
      loading: false,
      initialized: false,

      initialize: async () => {
        if (get().initialized) return;

        set({ loading: true });

        try {
          // Get current session
          const { session, error } = await authHelpers.getSession();

          console.log('[Auth] Initializing auth store:', {
            hasSession: !!session,
            hasUser: !!session?.user,
            error: error?.message,
          });

          if (error) {
            console.error('[Auth] Session retrieval error:', error);
            set({ initialized: true, loading: false, user: null, session: null });
            return;
          }

          // Track if we've already shown welcome toast in this session
          // Use sessionStorage so it persists only for the browser session
          const welcomeToastShown = sessionStorage.getItem('inkwave_welcome_toast_shown') === 'true';
          
          if (session) {
            // Validate session hasn't expired
            const expiresAt = session.expires_at;
            const now = Math.floor(Date.now() / 1000);

            if (expiresAt && expiresAt < now) {
              console.warn('[Auth] Session expired, attempting refresh');
              try {
                const { data, error: refreshError } = await supabase.auth.refreshSession();
                if (refreshError || !data.session) {
                  console.error('[Auth] Session refresh failed:', refreshError);
                  set({ initialized: true, loading: false, user: null, session: null });
                  return;
                }
                console.log('[Auth] Session refreshed successfully');
                set({
                  user: data.session.user,
                  session: data.session,
                  initialized: true,
                  loading: false,
                });
              } catch (refreshError) {
                console.error('[Auth] Unexpected refresh error:', refreshError);
                set({ initialized: true, loading: false, user: null, session: null });
                return;
              }
            } else {
              set({
                user: session.user,
                session,
                initialized: true,
                loading: false,
              });
            }
            
            // Mark that we've seen an existing session (don't show welcome toast on restore)
            if (!welcomeToastShown) {
              sessionStorage.setItem('inkwave_welcome_toast_shown', 'true');
            }
          } else {
            set({ initialized: true, loading: false });
            // Clear the flag if no session (user signed out)
            sessionStorage.removeItem('inkwave_welcome_toast_shown');
          }

          // Listen for auth changes (only set up once)
          const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
            console.log('Auth state changed:', event, session ? 'with session' : 'no session');

            // Only update state for specific events to prevent loops
            if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED' || event === 'USER_UPDATED') {
              if (session && session.access_token !== get().session?.access_token) {
                set({ user: session.user, session });
              }
            } else if (event === 'SIGNED_OUT') {
              // Only clear state on explicit sign out
              set({ user: null, session: null });
              // Clear welcome toast flag on sign out
              sessionStorage.removeItem('inkwave_welcome_toast_shown');
            }

            // Show toast notifications only for explicit user actions
            // Only show welcome toast on actual sign-in, not on session restore
            if (event === 'SIGNED_IN') {
              // Check if this is a new sign-in (not a session restore)
              const hasShownWelcome = sessionStorage.getItem('inkwave_welcome_toast_shown') === 'true';
              if (!hasShownWelcome) {
                toast.success('Welcome back!');
                sessionStorage.setItem('inkwave_welcome_toast_shown', 'true');
              }
            } else if (event === 'SIGNED_OUT') {
              toast.success('Signed out successfully');
            } else if (event === 'USER_UPDATED') {
              toast.success('Profile updated');
            } else if (event === 'TOKEN_REFRESHED') {
              console.log('Token refreshed successfully');
            }
          });

          // Clean up subscription on unmount (stored for future use)
          if (typeof window !== 'undefined') {
            window.addEventListener('beforeunload', () => {
              subscription?.unsubscribe();
            });
          }
        } catch (error) {
          console.error('Auth initialization error:', error);
          set({ initialized: true, loading: false });
        }
      },

      signUp: async (email: string, password: string, invitationToken?: string): Promise<SignupResult> => {
        set({ loading: true });

        try {
          // Use backend signup endpoint (creates user with auto-confirmed email)
          const { api } = await import('../lib/api');
          const response = await api.auth.signup(email, password, invitationToken);

          if (response.data.success && response.data.session) {
            // Backend returns session data after auto-signin
            // We need to properly set this in Supabase's session storage
            const sessionData = {
              access_token: response.data.session.access_token,
              refresh_token: response.data.session.refresh_token,
              token_type: 'bearer',
              expires_in: 3600, // 1 hour default
              expires_at: Math.floor(Date.now() / 1000) + 3600,
              user: response.data.user,
            };

            // Set session in Supabase client (this stores it in localStorage)
            const { data, error: sessionError } = await supabase.auth.setSession({
              access_token: sessionData.access_token,
              refresh_token: sessionData.refresh_token,
            });

            if (sessionError) {
              console.error('Failed to set Supabase session:', sessionError);
              toast.error('Account created but session setup failed. Please sign in.');
              set({ loading: false });
              return { success: false, error: sessionError.message };
            }

            // Update state with properly formatted session
            set({
              user: data.user,
              session: data.session,
              loading: false,
            });

            toast.success(response.data.message || 'Account created! Welcome to Inkwave 🎉');

            // Return with invitation info if applicable
            return {
              success: true,
              invitationRedeemed: response.data.invitation_redeemed,
              libraryBook: response.data.library_book,
            };
          }

          set({ loading: false });
          return { success: false, error: response.data.message || 'Signup failed' };
        } catch (error: any) {
          console.error('Signup error:', error);
          const errorMessage = error.response?.data?.detail || error.message || 'Signup failed';
          toast.error(errorMessage);
          set({ loading: false });
          return { success: false, error: errorMessage };
        }
      },

      signIn: async (email: string, password: string) => {
        set({ loading: true });

        try {
          const { data, error } = await authHelpers.signIn(email, password);

          if (error) {
            toast.error(error.message);
            set({ loading: false });
            return { success: false, error: error.message };
          }

          if (data.user && data.session) {
            set({
              user: data.user,
              session: data.session,
              loading: false,
            });
            return { success: true };
          }

          set({ loading: false });
          return { success: false, error: 'Login failed' };
        } catch (error: any) {
          console.error('Login error:', error);
          toast.error(error.message || 'Login failed');
          set({ loading: false });
          return { success: false, error: error.message };
        }
      },

      signInWithGoogle: async () => {
        set({ loading: true });

        try {
          const { error } = await authHelpers.signInWithGoogle();

          if (error) {
            toast.error(error.message);
            set({ loading: false });
            return { success: false, error: error.message };
          }

          // Google auth redirects, so we don't set state here
          return { success: true };
        } catch (error: any) {
          console.error('Google login error:', error);
          toast.error(error.message || 'Google login failed');
          set({ loading: false });
          return { success: false, error: error.message };
        }
      },

      signOut: async () => {
        set({ loading: true });

        try {
          await authHelpers.signOut();
          set({
            user: null,
            session: null,
            loading: false,
          });
        } catch (error: any) {
          console.error('Signout error:', error);
          toast.error(error.message || 'Signout failed');
          set({ loading: false });
        }
      },

      setUser: (user) => set({ user }),
      setSession: (session) => set({ session }),
    }),
    {
      name: 'inkwave-auth',
      partialize: (state) => ({
        user: state.user,
        session: state.session,
      }),
    }
  )
);
