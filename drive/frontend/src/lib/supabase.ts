/**
 * Supabase client for authentication.
 */

import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Helper to get current session
export async function getSession() {
  const { data: { session } } = await supabase.auth.getSession()
  return session
}

// Helper to get auth token
export async function getAuthToken(): Promise<string | null> {
  const session = await getSession()
  return session?.access_token || null
}

// Helper to sign out
export async function signOut() {
  await supabase.auth.signOut()
}
