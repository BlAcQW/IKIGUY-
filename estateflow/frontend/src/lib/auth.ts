/**
 * Authentication utilities for EstateFlow.
 *
 * Provides authentication token management using Supabase.
 */

import { supabase } from './supabase';

/**
 * Get authentication token from Supabase session.
 *
 * @returns Authentication token or null if not authenticated
 */
export async function getAuthToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

/**
 * Get authentication token synchronously.
 * Uses cached session data from Supabase.
 *
 * IMPORTANT: Use this in API calls (sync contexts).
 * For async contexts, use getAuthToken() instead.
 *
 * @returns Authentication token or null if not authenticated
 */
export function getAuthTokenSync(): string | null {
  // Supabase stores session in localStorage with key pattern
  const keys = Object.keys(localStorage).filter(key => key.startsWith('sb-') && key.endsWith('-auth-token'));

  if (keys.length === 0) {
    return null;
  }

  try {
    const sessionData = localStorage.getItem(keys[0]);
    if (sessionData) {
      const parsed = JSON.parse(sessionData);
      return parsed.access_token || null;
    }
  } catch (error) {
    console.error('Error parsing auth token:', error);
  }

  return null;
}

/**
 * Check if user is authenticated.
 *
 * @returns True if authenticated, false otherwise
 */
export async function isAuthenticated(): Promise<boolean> {
  const token = await getAuthToken();
  return token !== null;
}

/**
 * Get current user information from Supabase.
 *
 * @returns User information or null
 */
export async function getCurrentUser() {
  const { data: { user } } = await supabase.auth.getUser();
  return user;
}

/**
 * Sign out the current user.
 */
export async function signOut() {
  await supabase.auth.signOut();
}
