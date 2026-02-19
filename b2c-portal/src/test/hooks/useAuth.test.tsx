import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, renderHook, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { MongoAuthProvider, useMongoAuth } from '@/components/auth/MongoAuthContext';

// Mock the MongoDB auth client
const mockMongoAuth = {
  signin: vi.fn(),
  signout: vi.fn(),
  signup: vi.fn(),
  getUser: vi.fn(),
  getAccessToken: vi.fn(),
  isAuthenticated: vi.fn(),
  validateSession: vi.fn(),
  getTenantId: vi.fn()
};

vi.mock('@/lib/mongo-auth', () => ({
  mongoAuth: mockMongoAuth
}));

// Mock toast
const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: mockToast })
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <MongoAuthProvider>
      {children}
    </MongoAuthProvider>
  </BrowserRouter>
);

describe('useMongoAuth Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Setup default MongoDB auth mock responses
    mockMongoAuth.isAuthenticated.mockReturnValue(false);
    mockMongoAuth.getUser.mockReturnValue(null);
    mockMongoAuth.getAccessToken.mockReturnValue(null);
    mockMongoAuth.validateSession.mockResolvedValue(false);
    mockMongoAuth.getTenantId.mockReturnValue(null);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('MongoAuthProvider', () => {
    it('should render children without crashing', () => {
      const { getByText } = render(
        <TestWrapper>
          <div>Test Child</div>
        </TestWrapper>
      );

      expect(getByText('Test Child')).toBeInTheDocument();
    });

    it('should initialize with loading state', () => {
      const { result } = renderHook(() => useMongoAuth(), {
        wrapper: TestWrapper,
      });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.user).toBeNull();
      expect(result.current.organization).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('useMongoAuth Hook', () => {
    it('should throw error when used outside MongoAuthProvider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        renderHook(() => useMongoAuth());
      }).toThrow('useMongoAuth must be used within a MongoAuthProvider');

      consoleSpy.mockRestore();
    });

    it('should provide signIn function', async () => {
      const { result } = renderHook(() => useMongoAuth(), {
        wrapper: TestWrapper,
      });

      expect(typeof result.current.signIn).toBe('function');
    });

    it('should provide signUp function', async () => {
      const { result } = renderHook(() => useMongoAuth(), {
        wrapper: TestWrapper,
      });

      expect(typeof result.current.signUp).toBe('function');
    });

    it('should provide signOut function', async () => {
      const { result } = renderHook(() => useMongoAuth(), {
        wrapper: TestWrapper,
      });

      expect(typeof result.current.signOut).toBe('function');
    });

    it('should provide getTenantId function', async () => {
      const { result } = renderHook(() => useMongoAuth(), {
        wrapper: TestWrapper,
      });

      expect(typeof result.current.getTenantId).toBe('function');
    });

    it('should provide getAccessToken function', async () => {
      const { result } = renderHook(() => useMongoAuth(), {
        wrapper: TestWrapper,
      });

      expect(typeof result.current.getAccessToken).toBe('function');
    });

    it('should call MongoDB auth signin when signIn is called', async () => {
      mockMongoAuth.signin.mockResolvedValue({
        success: true,
        user: { id: '123', email: 'test@example.com' },
        access_token: 'fake-token'
      });

      const { result } = renderHook(() => useMongoAuth(), {
        wrapper: TestWrapper,
      });

      await result.current.signIn('test@example.com', 'password123');

      expect(mockMongoAuth.signin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
        remember_me: false
      });
    });

    it('should call MongoDB auth signout when signOut is called', async () => {
      mockMongoAuth.signout.mockResolvedValue(undefined);

      const { result } = renderHook(() => useMongoAuth(), {
        wrapper: TestWrapper,
      });

      await result.current.signOut();

      expect(mockMongoAuth.signout).toHaveBeenCalled();
    });

    it('should return tenant ID from getTenantId', () => {
      const mockTenantId = 'tenant-123';
      mockMongoAuth.getTenantId.mockReturnValue(mockTenantId);

      const { result } = renderHook(() => useMongoAuth(), {
        wrapper: TestWrapper,
      });

      const tenantId = result.current.getTenantId();
      expect(tenantId).toBe(mockTenantId);
      expect(mockMongoAuth.getTenantId).toHaveBeenCalled();
    });

    it('should return access token from getAccessToken', () => {
      const mockToken = 'access-token-123';
      mockMongoAuth.getAccessToken.mockReturnValue(mockToken);

      const { result } = renderHook(() => useMongoAuth(), {
        wrapper: TestWrapper,
      });

      const token = result.current.getAccessToken();
      expect(token).toBe(mockToken);
      expect(mockMongoAuth.getAccessToken).toHaveBeenCalled();
    });

    it('should handle authentication state when user is logged in', async () => {
      const mockUser = { id: '123', email: 'test@example.com' };
      mockMongoAuth.isAuthenticated.mockReturnValue(true);
      mockMongoAuth.getUser.mockReturnValue(mockUser);

      const { result } = renderHook(() => useMongoAuth(), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(false); // Initially false until validated
      });
    });
  });
});