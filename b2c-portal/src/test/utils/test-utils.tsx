import React, { ReactElement } from 'react'
import { render, RenderOptions, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { vi } from 'vitest'
import { MongoAuthProvider } from '@/components/auth/MongoAuthContext'

// Mock MongoDB auth service
export const mockMongoAuth = {
  signin: vi.fn(),
  signout: vi.fn(),
  signup: vi.fn(),
  getUser: vi.fn(),
  getAccessToken: vi.fn(),
  isAuthenticated: vi.fn(),
  validateSession: vi.fn(),
  getTenantId: vi.fn(),
  refreshSession: vi.fn()
};

// Mock toast hook
export const mockToast = vi.fn();

// Setup mocks for MongoDB auth
export const setupMongoAuthMocks = () => {
  vi.mock('@/lib/mongo-auth', () => ({
    mongoAuth: mockMongoAuth
  }));

  vi.mock('@/hooks/use-toast', () => ({
    useToast: () => ({ toast: mockToast })
  }));

  // Setup default mock responses
  mockMongoAuth.isAuthenticated.mockReturnValue(false);
  mockMongoAuth.getUser.mockReturnValue(null);
  mockMongoAuth.getAccessToken.mockReturnValue(null);
  mockMongoAuth.validateSession.mockResolvedValue(false);
  mockMongoAuth.getTenantId.mockReturnValue(null);
};

// Custom render function with providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
	queryClient?: QueryClient
	withRouter?: boolean
	withQueryClient?: boolean
	withAuth?: boolean
}

const createTestQueryClient = () =>
	new QueryClient({
		defaultOptions: {
			queries: {
				retry: false,
				gcTime: 0,
			},
			mutations: {
				retry: false,
			},
		},
	})

const AllTheProviders = ({
	children,
	queryClient,
	withRouter = true,
	withQueryClient = true,
	withAuth = true,
}: {
	children: React.ReactNode
	queryClient?: QueryClient
	withRouter?: boolean
	withQueryClient?: boolean
	withAuth?: boolean
}) => {
	let content = children

	if (withAuth) {
		content = <MongoAuthProvider>{content}</MongoAuthProvider>
	}

	if (withQueryClient) {
		const testQueryClient = queryClient || createTestQueryClient()
		content = <QueryClientProvider client={testQueryClient}>{content}</QueryClientProvider>
	}

	if (withRouter) {
		content = <BrowserRouter>{content}</BrowserRouter>
	}

	return <>{content}</>
}

const customRender = (
	ui: ReactElement,
	options: CustomRenderOptions = {}
): ReturnType<typeof render> => {
	const {
		queryClient,
		withRouter = true,
		withQueryClient = true,
		withAuth = true,
		...renderOptions
	} = options

	return render(ui, {
		wrapper: ({ children }) => (
			<AllTheProviders
				queryClient={queryClient}
				withRouter={withRouter}
				withQueryClient={withQueryClient}
				withAuth={withAuth}
			>
				{children}
			</AllTheProviders>
		),
		...renderOptions,
	})
}

// Mock data factories
export const createMockAssistant = (overrides = {}) => ({
	id: 'asst_123',
	name: 'Test Assistant',
	description: 'A test assistant',
	type: 'customer_support',
	model: 'gpt-4',
	instructions: 'Test instructions',
	isActive: true,
	createdAt: '2024-01-01T00:00:00Z',
	updatedAt: '2024-01-01T00:00:00Z',
	tenantId: 'tenant_123',
	...overrides,
})

export const createMockCampaign = (overrides = {}) => ({
	id: 'camp_123',
	name: 'Test Campaign',
	description: 'A test campaign',
	status: 'draft',
	type: 'outbound',
	startDate: '2024-01-01T00:00:00Z',
	endDate: '2024-01-31T23:59:59Z',
	assistantId: 'asst_123',
	tenantId: 'tenant_123',
	createdAt: '2024-01-01T00:00:00Z',
	updatedAt: '2024-01-01T00:00:00Z',
	...overrides,
})

export const createMockLicense = (overrides = {}) => ({
	id: 'lic_123',
	type: 'pro',
	status: 'active',
	features: ['assistants', 'campaigns', 'analytics'],
	startDate: '2024-01-01T00:00:00Z',
	endDate: '2024-12-31T23:59:59Z',
	tenantId: 'tenant_123',
	createdAt: '2024-01-01T00:00:00Z',
	updatedAt: '2024-01-01T00:00:00Z',
	...overrides,
})

export const createMockPayment = (overrides = {}) => ({
	id: 'pay_123',
	amount: 99.99,
	currency: 'USD',
	status: 'completed',
	method: 'card',
	description: 'Pro License Payment',
	tenantId: 'tenant_123',
	createdAt: '2024-01-01T00:00:00Z',
	updatedAt: '2024-01-01T00:00:00Z',
	...overrides,
})

export const createMockUsage = (overrides = {}) => ({
	id: 'usage_123',
	type: 'api_calls',
	quantity: 1000,
	period: 'month',
	tenantId: 'tenant_123',
	createdAt: '2024-01-01T00:00:00Z',
	...overrides,
})

export const createMockKnowledgeItem = (overrides = {}) => ({
	id: 'kb_123',
	title: 'Test Knowledge Item',
	content: 'Test content',
	type: 'document',
	category: 'general',
	isActive: true,
	tenantId: 'tenant_123',
	createdAt: '2024-01-01T00:00:00Z',
	updatedAt: '2024-01-01T00:00:00Z',
	...overrides,
})

// API mock helpers
export const mockApiResponse = (data: any, status = 200) => {
	return Promise.resolve({
		ok: status >= 200 && status < 300,
		status,
		json: () => Promise.resolve(data),
		text: () => Promise.resolve(JSON.stringify(data)),
		headers: new Headers({
			'Content-Type': 'application/json',
		}),
	})
}

export const mockApiError = (status = 500, message = 'Internal Server Error') => {
	return Promise.resolve({
		ok: false,
		status,
		json: () => Promise.resolve({ error: message }),
		text: () => Promise.resolve(JSON.stringify({ error: message })),
		headers: new Headers({
			'Content-Type': 'application/json',
		}),
	})
}

// Test helpers
export const waitForElementToBeRemoved = async (element: HTMLElement) => {
	await waitFor(() => {
		expect(element).not.toBeInTheDocument()
	})
}

export const waitForLoadingToFinish = async () => {
	await waitFor(() => {
		expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
	})
}

export const waitForErrorToAppear = async (errorMessage?: string) => {
	await waitFor(() => {
		if (errorMessage) {
			expect(screen.getByText(errorMessage)).toBeInTheDocument()
		} else {
			expect(screen.getByTestId('error-message')).toBeInTheDocument()
		}
	})
}

// Form testing helpers
export const fillFormField = async (name: string, value: string) => {
	const field = screen.getByRole('textbox', { name: new RegExp(name, 'i') })
	await field.clear()
	await field.type(value)
}

export const selectOption = async (name: string, option: string) => {
	const select = screen.getByRole('combobox', { name: new RegExp(name, 'i') })
	await select.click()
	const optionElement = screen.getByRole('option', { name: option })
	await optionElement.click()
}

export const clickButton = async (name: string) => {
	const button = screen.getByRole('button', { name: new RegExp(name, 'i') })
	await button.click()
}

// Mock Supabase
export const mockSupabase = {
	auth: {
		getUser: vi.fn(),
		getSession: vi.fn(),
		signInWithPassword: vi.fn(),
		signUp: vi.fn(),
		signOut: vi.fn(),
		onAuthStateChange: vi.fn(),
	},
	from: vi.fn(() => ({
		select: vi.fn().mockReturnThis(),
		insert: vi.fn().mockReturnThis(),
		update: vi.fn().mockReturnThis(),
		delete: vi.fn().mockReturnThis(),
		eq: vi.fn().mockReturnThis(),
		neq: vi.fn().mockReturnThis(),
		gt: vi.fn().mockReturnThis(),
		lt: vi.fn().mockReturnThis(),
		gte: vi.fn().mockReturnThis(),
		lte: vi.fn().mockReturnThis(),
		like: vi.fn().mockReturnThis(),
		ilike: vi.fn().mockReturnThis(),
		in: vi.fn().mockReturnThis(),
		not: vi.fn().mockReturnThis(),
		or: vi.fn().mockReturnThis(),
		order: vi.fn().mockReturnThis(),
		limit: vi.fn().mockReturnThis(),
		range: vi.fn().mockReturnThis(),
		single: vi.fn().mockReturnThis(),
		maybeSingle: vi.fn().mockReturnThis(),
		then: vi.fn().mockResolvedValue({ data: null, error: null }),
	})),
	storage: {
		from: vi.fn(() => ({
			upload: vi.fn().mockResolvedValue({ data: null, error: null }),
			download: vi.fn().mockResolvedValue({ data: null, error: null }),
			remove: vi.fn().mockResolvedValue({ data: null, error: null }),
			getPublicUrl: vi.fn().mockReturnValue({ data: { publicUrl: 'mock-url' } }),
		})),
	},
}

// Mock authenticated user helper
export const mockAuthenticatedUser = (user = { id: '123', email: 'test@example.com' }) => {
  mockMongoAuth.isAuthenticated.mockReturnValue(true);
  mockMongoAuth.getUser.mockReturnValue(user);
  mockMongoAuth.getAccessToken.mockReturnValue('mock-access-token');
  mockMongoAuth.getTenantId.mockReturnValue('mock-tenant-id');
};

// Mock unauthenticated user helper
export const mockUnauthenticatedUser = () => {
  mockMongoAuth.isAuthenticated.mockReturnValue(false);
  mockMongoAuth.getUser.mockReturnValue(null);
  mockMongoAuth.getAccessToken.mockReturnValue(null);
  mockMongoAuth.getTenantId.mockReturnValue(null);
};

// Clear all mocks helper
export const clearAllAuthMocks = () => {
  Object.values(mockMongoAuth).forEach(mock => {
    if (vi.isMockFunction(mock)) {
      mock.mockClear();
    }
  });
  mockToast.mockClear();
};

// Re-export everything from testing-library
export * from '@testing-library/react'
export { customRender as render }
