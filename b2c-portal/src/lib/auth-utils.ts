import { mongoAuth } from '@/lib/mongo-auth';

export const getAuthHeaders = async () => {
  const accessToken = mongoAuth.getAccessToken();

  if (!accessToken) {
    throw new Error('No valid authentication session');
  }

  const headers: Record<string, string> = {
    'Authorization': `Bearer ${accessToken}`,
    'x-service-token': 'kasaai-b2c-portal'
  };

  // Add organization header if available
  const currentOrgId = localStorage.getItem('kasaai_current_organization_id');
  if (currentOrgId) {
    headers['X-Organization-ID'] = currentOrgId;
  }

  return headers;
};

export const getAuthToken = async (): Promise<string> => {
  const accessToken = mongoAuth.getAccessToken();

  if (!accessToken) {
    throw new Error('No valid authentication session');
  }

  return accessToken;
};

export const isAuthenticated = async (): Promise<boolean> => {
  return mongoAuth.isAuthenticated();
};

export const getCurrentUser = async () => {
  const user = mongoAuth.getUser();

  if (!user) {
    throw new Error('No authenticated user');
  }

  return user;
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