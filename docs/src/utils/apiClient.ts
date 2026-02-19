/**
 * API Client utility for making authenticated requests
 * Handles authentication errors and redirects automatically
 */

interface RequestOptions extends RequestInit {
  requiresAuth?: boolean;
}

/**
 * Makes an authenticated API request
 * @param url - The URL to fetch
 * @param options - Fetch options with optional requiresAuth flag
 * @returns Response object
 */
export async function apiRequest(
  url: string,
  options: RequestOptions = {}
): Promise<Response> {
  const { requiresAuth = false, ...fetchOptions } = options;

  // Get auth token from localStorage if authentication is required
  if (requiresAuth && typeof window !== 'undefined') {
    const token = localStorage.getItem('docs_auth_token');

    if (!token) {
      // No token available, redirect to login
      window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
      throw new Error('Authentication required');
    }

    // Add authorization header
    fetchOptions.headers = {
      ...fetchOptions.headers,
      'Authorization': `Bearer ${token}`,
    };
  }

  try {
    const response = await fetch(url, fetchOptions);

    // Handle authentication errors
    if (response.status === 401) {
      // Unauthorized - clear auth and redirect to login
      if (typeof window !== 'undefined') {
        localStorage.removeItem('docs_auth_token');
        localStorage.removeItem('docs_auth_user');
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
      }
      throw new Error('Authentication expired');
    }

    // Handle forbidden errors
    if (response.status === 403) {
      // Forbidden - user doesn't have permission
      throw new Error('Access denied');
    }

    return response;
  } catch (error) {
    // Network or other errors
    console.error('API request failed:', error);
    throw error;
  }
}

/**
 * Convenience method for GET requests
 */
export async function apiGet(
  url: string,
  requiresAuth: boolean = false
): Promise<Response> {
  return apiRequest(url, {
    method: 'GET',
    requiresAuth,
  });
}

/**
 * Convenience method for POST requests
 */
export async function apiPost(
  url: string,
  data: any,
  requiresAuth: boolean = false
): Promise<Response> {
  return apiRequest(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
    requiresAuth,
  });
}

/**
 * Convenience method for PUT requests
 */
export async function apiPut(
  url: string,
  data: any,
  requiresAuth: boolean = false
): Promise<Response> {
  return apiRequest(url, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
    requiresAuth,
  });
}

/**
 * Convenience method for DELETE requests
 */
export async function apiDelete(
  url: string,
  requiresAuth: boolean = false
): Promise<Response> {
  return apiRequest(url, {
    method: 'DELETE',
    requiresAuth,
  });
}
