/**
 * Supabase client - DEPRECATED
 * 
 * This file is kept for backwards compatibility but is no longer used.
 * The application now uses local JWT authentication.
 * 
 * @deprecated Use the AuthContext and api-config instead.
 */

// Export a dummy object to prevent import errors
export const supabase = {
  auth: {
    getSession: async () => ({ data: { session: null } }),
    getUser: async () => ({ data: { user: null } }),
    signOut: async () => { },
    onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => { } } } }),
  },
};
