import React, { createContext, useContext } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Create a mock Supabase client
export const mockSupabaseClient = {
  auth: {
    signUp: vi.fn(),
    signInWithPassword: vi.fn(),
    signOut: vi.fn(),
    getUser: vi.fn(),
    getSession: vi.fn(),
    onAuthStateChange: vi.fn(),
  },
  from: vi.fn(),
};

// Mock AuthContext (for Supabase-based AuthProvider)
export const mockAuthContext = {
  user: null,
  session: null,
  loading: false,
  signUp: vi.fn(),
  signIn: vi.fn(),
  signOut: vi.fn(),
  updateProfile: vi.fn(),
};

// Mock BackendUser type (matches BackendAuthContext)
export interface MockBackendUser {
  id: string;
  email: string;
  username?: string;
  full_name?: string;
  avatar_url?: string;
  bio?: string;
  location?: string;
  languages_spoken: string[];
  language_expertise: any[];
  level: string;
  total_points: number;
  level_points: number;
  achievements: string[];
  badges: string[];
  verified_languages: string[];
  can_validate: boolean;
  can_moderate: boolean;
  contributions_count: number;
  validations_count: number;
  quality_rating: number;
  reputation_score: number;
  is_active: boolean;
  created_at: string;
}

// Mock BackendAuthContext type
interface MockBackendAuthContextType {
  user: MockBackendUser | null;
  tokens: { access_token: string; refresh_token: string; token_type: string } | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
  signUp: (email: string, password: string, full_name?: string) => Promise<{ error: Error | null }>;
  signOut: () => Promise<{ error: Error | null }>;
  updateProfile: (updates: Partial<MockBackendUser>) => Promise<{ error: any | null }>;
  refreshProfile: () => Promise<void>;
}

// Create mock BackendAuthContext
const MockBackendAuthContext = createContext<MockBackendAuthContextType | undefined>(undefined);

// Mock BackendAuthContext values
export const mockBackendAuthContext: MockBackendAuthContextType = {
  user: null,
  tokens: null,
  loading: false,
  signIn: vi.fn().mockResolvedValue({ error: null }),
  signUp: vi.fn().mockResolvedValue({ error: null }),
  signOut: vi.fn().mockResolvedValue({ error: null }),
  updateProfile: vi.fn().mockResolvedValue({ error: null }),
  refreshProfile: vi.fn().mockResolvedValue(undefined),
};

// Mock BackendAuthProvider for tests
export const MockBackendAuthProvider: React.FC<{ children: React.ReactNode; value?: Partial<MockBackendAuthContextType> }> = ({
  children,
  value = {},
}) => {
  const contextValue = { ...mockBackendAuthContext, ...value };
  return (
    <MockBackendAuthContext.Provider value={contextValue}>
      {children}
    </MockBackendAuthContext.Provider>
  );
};

// Hook to use mock backend auth in tests
export const useMockBackendAuth = () => {
  const context = useContext(MockBackendAuthContext);
  if (context === undefined) {
    throw new Error('useMockBackendAuth must be used within a MockBackendAuthProvider');
  }
  return context;
};

interface AllTheProvidersProps {
  children: React.ReactNode;
}

const AllTheProviders: React.FC<AllTheProvidersProps> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <MockBackendAuthProvider>
          {children}
        </MockBackendAuthProvider>
      </QueryClientProvider>
    </BrowserRouter>
  );
};

const customRender = (ui: React.ReactElement, options?: Omit<RenderOptions, 'wrapper'>) =>
  render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };

// Helper to create mock form events
export const createMockFormEvent = (name: string, value: string) => ({
  target: { name, value },
  preventDefault: vi.fn(),
});

// Mock form data for auth tests
export const mockAuthFormData = {
  validSignUp: {
    email: 'test@example.com',
    password: 'TestPassword123!',
    confirmPassword: 'TestPassword123!',
    fullName: 'Test User',
    username: 'testuser',
  },
  invalidSignUp: {
    email: 'invalid-email',
    password: '123',
    confirmPassword: '456',
    fullName: '',
    username: '',
  },
  validSignIn: {
    email: 'test@example.com',
    password: 'TestPassword123!',
  },
  invalidSignIn: {
    email: 'invalid-email',
    password: 'wrongpass',
  },
};

// Helper to wait for async operations
export const waitFor = (fn: () => boolean | Promise<boolean>, timeout = 5000) => {
  return new Promise((resolve, reject) => {
    const start = Date.now();

    const check = async () => {
      try {
        const result = await fn();
        if (result) {
          resolve(true);
          return;
        }
      } catch (error) {
        // Continue checking
      }

      if (Date.now() - start >= timeout) {
        reject(new Error('Timeout waiting for condition'));
        return;
      }

      setTimeout(check, 100);
    };

    check();
  });
};