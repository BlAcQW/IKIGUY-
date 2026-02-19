/**
 * Frontend configuration
 */

// API base URL - uses environment variable or defaults to production backend
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://churchflow-api.ailabsafrica.com/api/v1';

// Get API URL for requests
export const getApiUrl = (endpoint: string): string => {
  // Remove leading slash if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;

  // Always use the absolute API URL to avoid domain mismatch
  // Production: https://churchflow-api.ailabsafrica.com/api/v1
  // Dev: https://dev-churchflow-api.ailabsafrica.com/api/v1 (or localhost)
  return `${API_BASE_URL}/${cleanEndpoint}`;
};
