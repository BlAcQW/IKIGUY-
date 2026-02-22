import { login as apiLogin, register as apiRegister, getMe } from './api';

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

export function isAuthenticated(): boolean {
  return getToken() !== null;
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const result = await apiLogin({ email, password });
  setToken(result.data.token);
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

export function logout(): void {
  clearToken();
  localStorage.removeItem('load_user');
  window.location.href = '/login';
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
    clearToken();
    localStorage.removeItem('load_user');
    return null;
  }
}
