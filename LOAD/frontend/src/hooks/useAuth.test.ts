import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';

vi.mock('@/lib/auth', () => ({
  isAuthenticated: vi.fn(),
  getCurrentUser: vi.fn(),
}));

import { useAuth } from './useAuth';
import { isAuthenticated, getCurrentUser } from '@/lib/auth';

const mockedIsAuthenticated = vi.mocked(isAuthenticated);
const mockedGetCurrentUser = vi.mocked(getCurrentUser);

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns loading true initially', () => {
    mockedIsAuthenticated.mockReturnValue(true);
    mockedGetCurrentUser.mockReturnValue(new Promise(() => {})); // never resolves

    const { result } = renderHook(() => useAuth());
    expect(result.current.loading).toBe(true);
  });

  it('sets user when authenticated', async () => {
    const mockUser = { userId: 'u1', organizationId: 'o1', role: 'OWNER' };
    mockedIsAuthenticated.mockReturnValue(true);
    mockedGetCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user).toEqual(mockUser);
  });

  it('sets user to null when not authenticated', async () => {
    mockedIsAuthenticated.mockReturnValue(false);

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user).toBeNull();
  });

  it('sets user to null when getCurrentUser throws', async () => {
    mockedIsAuthenticated.mockReturnValue(true);
    mockedGetCurrentUser.mockRejectedValue(new Error('fail'));

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user).toBeNull();
  });

  it('refresh triggers re-check', async () => {
    mockedIsAuthenticated.mockReturnValue(true);
    mockedGetCurrentUser.mockResolvedValue({ userId: 'u1', organizationId: 'o1', role: 'OWNER' });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(mockedGetCurrentUser).toHaveBeenCalledTimes(1);

    mockedGetCurrentUser.mockResolvedValue({ userId: 'u2', organizationId: 'o2', role: 'ADMIN' });

    await act(async () => {
      await result.current.refresh();
    });

    expect(mockedGetCurrentUser).toHaveBeenCalledTimes(2);
    expect(result.current.user?.userId).toBe('u2');
  });
});
