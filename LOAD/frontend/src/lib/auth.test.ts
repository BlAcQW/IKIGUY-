import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('./api', () => ({
  login: vi.fn(),
  register: vi.fn(),
  getMe: vi.fn(),
}));

import {
  getToken,
  setToken,
  clearToken,
  isAuthenticated,
  login,
  register,
  logout,
  getCurrentUser,
} from './auth';
import { login as apiLogin, register as apiRegister, getMe } from './api';

const mockedApiLogin = vi.mocked(apiLogin);
const mockedApiRegister = vi.mocked(apiRegister);
const mockedGetMe = vi.mocked(getMe);

describe('auth', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    // Prevent navigation side effects
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
    });
  });

  describe('getToken / setToken / clearToken', () => {
    it('getToken returns null when no token', () => {
      expect(getToken()).toBeNull();
    });

    it('setToken stores and getToken retrieves', () => {
      setToken('abc123');
      expect(getToken()).toBe('abc123');
    });

    it('clearToken removes token', () => {
      setToken('abc123');
      clearToken();
      expect(getToken()).toBeNull();
    });
  });

  describe('isAuthenticated', () => {
    it('returns false when no token', () => {
      expect(isAuthenticated()).toBe(false);
    });

    it('returns true when token exists', () => {
      setToken('tok');
      expect(isAuthenticated()).toBe(true);
    });
  });

  describe('login', () => {
    it('calls API, stores token and user, returns AuthUser', async () => {
      mockedApiLogin.mockResolvedValue({
        success: true,
        data: {
          token: 'jwt-token',
          user: { id: 'u1', email: 'a@b.com', name: 'Test', role: 'OWNER' as const, organizationId: 'o1', createdAt: '', updatedAt: '' },
          organization: { id: 'o1', name: 'My Org', slug: 'my-org', plan: 'FREE' as const, createdAt: '', updatedAt: '' },
        },
      });

      const result = await login('a@b.com', 'pass');

      expect(mockedApiLogin).toHaveBeenCalledWith({ email: 'a@b.com', password: 'pass' });
      expect(getToken()).toBe('jwt-token');
      expect(result.userId).toBe('u1');
      expect(result.organizationId).toBe('o1');
      expect(result.name).toBe('Test');
      expect(result.email).toBe('a@b.com');
      expect(result.organizationName).toBe('My Org');
      expect(localStorage.getItem('load_user')).toBeTruthy();
    });
  });

  describe('register', () => {
    it('calls API, stores token and user, returns AuthUser', async () => {
      mockedApiRegister.mockResolvedValue({
        success: true,
        data: {
          token: 'reg-token',
          user: { id: 'u2', email: 'b@c.com', name: 'New', role: 'OWNER' as const, organizationId: 'o2', createdAt: '', updatedAt: '' },
          organization: { id: 'o2', name: 'New Org', slug: 'new-org', plan: 'FREE' as const, createdAt: '', updatedAt: '' },
        },
      });

      const result = await register('b@c.com', 'pass', 'New', 'New Org');

      expect(mockedApiRegister).toHaveBeenCalledWith({
        email: 'b@c.com',
        password: 'pass',
        name: 'New',
        organizationName: 'New Org',
      });
      expect(getToken()).toBe('reg-token');
      expect(result.userId).toBe('u2');
      expect(result.organizationName).toBe('New Org');
    });
  });

  describe('logout', () => {
    it('clears token, user data, and redirects to /login', () => {
      setToken('tok');
      localStorage.setItem('load_user', '{}');

      logout();

      expect(getToken()).toBeNull();
      expect(localStorage.getItem('load_user')).toBeNull();
      expect(window.location.href).toBe('/login');
    });
  });

  describe('getCurrentUser', () => {
    it('returns null when not authenticated', async () => {
      const result = await getCurrentUser();
      expect(result).toBeNull();
    });

    it('calls getMe and merges stored user data', async () => {
      setToken('tok');
      localStorage.setItem('load_user', JSON.stringify({ name: 'Test', email: 'a@b.com', organizationName: 'Org' }));

      mockedGetMe.mockResolvedValue({
        success: true,
        data: { userId: 'u1', organizationId: 'o1', role: 'OWNER' },
      });

      const result = await getCurrentUser();

      expect(result).toEqual({
        userId: 'u1',
        organizationId: 'o1',
        role: 'OWNER',
        name: 'Test',
        email: 'a@b.com',
        organizationName: 'Org',
      });
    });

    it('clears token on API failure and returns null', async () => {
      setToken('tok');
      mockedGetMe.mockRejectedValue(new Error('Unauthorized'));

      const result = await getCurrentUser();

      expect(result).toBeNull();
      expect(getToken()).toBeNull();
      expect(localStorage.getItem('load_user')).toBeNull();
    });

    it('handles corrupted stored user data gracefully', async () => {
      setToken('tok');
      localStorage.setItem('load_user', 'not-json');

      mockedGetMe.mockResolvedValue({
        success: true,
        data: { userId: 'u1', organizationId: 'o1', role: 'MEMBER' },
      });

      const result = await getCurrentUser();

      expect(result).toEqual({
        userId: 'u1',
        organizationId: 'o1',
        role: 'MEMBER',
        name: undefined,
        email: undefined,
        organizationName: undefined,
      });
    });
  });
});
