import { supabase } from '@/lib/supabase';

export const getAuthHeaders = async () => {
  const { data: { session } } = await supabase.auth.getSession();

  if (!session?.access_token) {
    throw new Error('No valid authentication session');
  }

  return {
    'Authorization': `Bearer ${session.access_token}`,
  };
};

export const getAuthToken = async (): Promise<string> => {
  const { data: { session } } = await supabase.auth.getSession();

  if (!session?.access_token) {
    throw new Error('No valid authentication session');
  }

  return session.access_token;
};