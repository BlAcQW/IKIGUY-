/**
 * Auth hook compatibility layer
 *
 * Provides a unified interface that works with the new BackendAuthContext
 * while maintaining compatibility with existing code that uses useAuth().
 */

import { useBackendAuth, BackendUser } from '@/contexts/BackendAuthContext'

// Map BackendUser to the profile format expected by existing code
export function useAuth() {
  const { user, tokens, loading, signIn, signUp, signOut, updateProfile, refreshProfile } = useBackendAuth()

  // Transform backend user to match old Supabase profile format
  const profile = user ? {
    id: user.id,
    email: user.email,
    username: user.username,
    full_name: user.full_name,
    avatar_url: user.avatar_url,
    bio: user.bio,
    location: user.location,
    languages_spoken: user.languages_spoken,
    level: user.level,
    total_points: user.total_points,
    achievements: user.achievements,
    badges: user.badges,
    verified_languages: user.verified_languages,
    can_validate: user.can_validate,
    can_moderate: user.can_moderate,
  } : null

  // Create a user object that matches Supabase User interface
  const supabaseCompatibleUser = user ? {
    id: user.id,
    email: user.email,
    created_at: user.created_at,
  } : null

  return {
    user: supabaseCompatibleUser,
    profile,
    session: tokens ? {
      access_token: tokens.access_token,
      refresh_token: tokens.refresh_token,
    } : null,
    loading,
    signIn,
    signUp,
    signOut,
    updateProfile,
    refreshProfile,
    // Deprecated - not supported with backend auth
    signInWithProvider: async () => ({ error: new Error('OAuth not supported with backend auth') }),
  }
}
