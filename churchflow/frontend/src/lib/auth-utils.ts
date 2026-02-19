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

export const isAuthenticated = async (): Promise<boolean> => {
  const { data: { session } } = await supabase.auth.getSession();
  return !!session?.access_token;
};

export const getCurrentUser = async () => {
  const { data: { session } } = await supabase.auth.getSession();

  if (!session?.user) {
    throw new Error('No authenticated user');
  }

  return session.user;
};

export const isAdminUser = async (): Promise<boolean> => {
  try {
    const user = await getCurrentUser();

    // Define admin email addresses
    const adminEmails = [
      'ailabsafrica@gmail.com',
      'admin@ailabsafrica.com',
      'support@ailabsafrica.com',
      'alfred.anyan@gmail.com'
    ];

    // Check if user email is in admin list
    return adminEmails.includes(user.email || '');
  } catch (error) {
    return false;
  }
};