/**
 * Authentication utilities for EstateFlow.
 *
 * Standalone local authentication - no external services required.
 */

import { getAuthToken as getToken, removeAuthToken } from './api-config';

/**
 * Get authentication token from localStorage.
 *
 * @returns Authentication token or null if not authenticated
 */
export async function getAuthToken(): Promise<string | null> {
  return getToken();
}

/**
 * Get authentication token synchronously.
 *
 * @returns Authentication token or null if not authenticated
 */
export function getAuthTokenSync(): string | null {
  return getToken();
}

/**
 * Check if user is authenticated.
 *
 * @returns True if authenticated, false otherwise
 */
export async function isAuthenticated(): Promise<boolean> {
  const token = getToken();
  return token !== null;
}

/**
 * Sign out the current user.
 */
export async function signOut() {
  removeAuthToken();
}
