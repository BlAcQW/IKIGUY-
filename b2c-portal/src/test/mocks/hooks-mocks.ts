import { vi } from 'vitest'

// Mock React Query hooks
export const mockUseQuery = vi.fn()
export const mockUseMutation = vi.fn()
export const mockUseQueryClient = vi.fn()

// Mock React Router hooks
export const mockUseNavigate = vi.fn()
export const mockUseLocation = vi.fn()
export const mockUseParams = vi.fn()

// Mock custom hooks
export const mockUseAuth = vi.fn()
export const mockUseSupabase = vi.fn()
export const mockUseCoreApi = vi.fn()

// Setup function to apply hook mocks
export const setupHookMocks = () => {
	// Mock React Query
	vi.mock('@tanstack/react-query', () => ({
		useQuery: mockUseQuery,
		useMutation: mockUseMutation,
		useQueryClient: mockUseQueryClient,
	}))

	// Mock React Router
	vi.mock('react-router-dom', () => ({
		useNavigate: mockUseNavigate,
		useLocation: mockUseLocation,
		useParams: mockUseParams,
		BrowserRouter: ({ children }: { children: React.ReactNode }) => children,
		Routes: ({ children }: { children: React.ReactNode }) => children,
		Route: ({ children }: { children: React.ReactNode }) => children,
		Link: ({ children, ...props }: any) => <a { ...props } > { children } </a>,
	}))

	// Mock custom hooks
	vi.mock('@/hooks/useAuth', () => ({
		useAuth: mockUseAuth,
	}))

	vi.mock('@/hooks/useSupabase', () => ({
		useSupabase: mockUseSupabase,
	}))

	vi.mock('@/hooks/useCoreApi', () => ({
		useCoreApi: mockUseCoreApi,
	}))
}
