import { login as apiLogin, register as apiRegister, getMe, refreshAccessToken, logoutApi } from './api';

export interface AuthUser {
  userId: string;
  organizationId: string;
  role: string;
  name?: string;
  email?: string;
  organizationName?: string;
}

export function getToken(): string | null {
  return localStorage.getItem('load_token');
}

export function setToken(token: string): void {
  localStorage.setItem('load_token', token);
}

export function clearToken(): void {
  localStorage.removeItem('load_token');
}

export function getRefreshToken(): string | null {
  return localStorage.getItem('load_refresh_token');
}

export function setRefreshToken(token: string): void {
  localStorage.setItem('load_refresh_token', token);
}

export function clearRefreshToken(): void {
  localStorage.removeItem('load_refresh_token');
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const result = await apiLogin({ email, password });
  setToken(result.data.token);
  if (result.data.refreshToken) {
    setRefreshToken(result.data.refreshToken);
  }
  const authUser: AuthUser = {
    userId: result.data.user.id,
    organizationId: result.data.organization.id,
    role: result.data.user.role,
    name: result.data.user.name,
    email: result.data.user.email,
    organizationName: result.data.organization.name,
  };
  localStorage.setItem('load_user', JSON.stringify(authUser));
  return authUser;
}

export async function register(
  email: string,
  password: string,
  name: string,
  organizationName: string
): Promise<AuthUser> {
  const result = await apiRegister({ email, password, name, organizationName });
  setToken(result.data.token);
  if (result.data.refreshToken) {
    setRefreshToken(result.data.refreshToken);
  }
  const authUser: AuthUser = {
    userId: result.data.user.id,
    organizationId: result.data.organization.id,
    role: result.data.user.role,
    name: result.data.user.name,
    email: result.data.user.email,
    organizationName: result.data.organization.name,
  };
  localStorage.setItem('load_user', JSON.stringify(authUser));
  return authUser;
}

export async function logout(): Promise<void> {
  try {
    await logoutApi();
  } catch {
    // Best-effort server-side logout
  }
  clearToken();
  clearRefreshToken();
  localStorage.removeItem('load_user');
  window.location.href = '/login';
}

export async function tryRefreshToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const result = await refreshAccessToken(refreshToken);
    setToken(result.data.token);
    setRefreshToken(result.data.refreshToken);
    return true;
  } catch {
    clearToken();
    clearRefreshToken();
    localStorage.removeItem('load_user');
    return false;
  }
}

export async function getCurrentUser(): Promise<AuthUser | null> {
  if (!isAuthenticated()) return null;
  try {
    const result = await getMe();
    let storedUser: Partial<AuthUser> = {};
    try {
      const stored = localStorage.getItem('load_user');
      if (stored) storedUser = JSON.parse(stored);
    } catch {
      localStorage.removeItem('load_user');
    }
    return {
      ...result.data,
      name: storedUser.name,
      email: storedUser.email,
      organizationName: storedUser.organizationName,
    };
  } catch {
    // Try refreshing the token before giving up
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      try {
        const result = await getMe();
        let storedUser: Partial<AuthUser> = {};
        try {
          const stored = localStorage.getItem('load_user');
          if (stored) storedUser = JSON.parse(stored);
        } catch {
          localStorage.removeItem('load_user');
        }
        return {
          ...result.data,
          name: storedUser.name,
          email: storedUser.email,
          organizationName: storedUser.organizationName,
        };
      } catch {
        // Fall through to return null
      }
    }
    clearToken();
    clearRefreshToken();
    localStorage.removeItem('load_user');
    return null;
  }
}
