import { vi } from 'vitest'
import { mockApiResponse, mockApiError } from '../utils/test-utils'

// Mock the core API client
export const mockCoreApi = {
	assistantApi: {
		create: vi.fn(),
		get: vi.fn(),
		list: vi.fn(),
		update: vi.fn(),
		delete: vi.fn(),
		toggleStatus: vi.fn(),
	},
	campaignApi: {
		create: vi.fn(),
		get: vi.fn(),
		list: vi.fn(),
		update: vi.fn(),
		delete: vi.fn(),
		start: vi.fn(),
		stop: vi.fn(),
		getAnalytics: vi.fn(),
	},
	knowledgeBaseApi: {
		create: vi.fn(),
		get: vi.fn(),
		list: vi.fn(),
		update: vi.fn(),
		delete: vi.fn(),
		uploadDocument: vi.fn(),
		search: vi.fn(),
		reindex: vi.fn(),
	},
	licenseApi: {
		get: vi.fn(),
		upgrade: vi.fn(),
		cancel: vi.fn(),
		getFeatures: vi.fn(),
	},
	usageApi: {
		get: vi.fn(),
		getHistory: vi.fn(),
		getLimits: vi.fn(),
	},
	paymentApi: {
		create: vi.fn(),
		get: vi.fn(),
		list: vi.fn(),
		refund: vi.fn(),
		getMethods: vi.fn(),
	},
	mcpApi: {
		crm: {
			getContacts: vi.fn(),
			createContact: vi.fn(),
			updateContact: vi.fn(),
			deleteContact: vi.fn(),
		},
		helpdesk: {
			getTickets: vi.fn(),
			createTicket: vi.fn(),
			updateTicket: vi.fn(),
			closeTicket: vi.fn(),
		},
		payments: {
			processPayment: vi.fn(),
			getTransactions: vi.fn(),
			refundTransaction: vi.fn(),
		},
		communication: {
			sendEmail: vi.fn(),
			sendSMS: vi.fn(),
			sendWhatsApp: vi.fn(),
		},
		calendar: {
			getEvents: vi.fn(),
			createEvent: vi.fn(),
			updateEvent: vi.fn(),
			deleteEvent: vi.fn(),
		},
		documents: {
			upload: vi.fn(),
			download: vi.fn(),
			list: vi.fn(),
			delete: vi.fn(),
		},
		analytics: {
			getMetrics: vi.fn(),
			getReports: vi.fn(),
			exportData: vi.fn(),
		},
		ai: {
			generateContent: vi.fn(),
			analyzeSentiment: vi.fn(),
			extractEntities: vi.fn(),
		},
	},
}

// Mock Supabase client
export const mockSupabaseClient = {
	auth: {
		getUser: vi.fn(),
		getSession: vi.fn(),
		signInWithPassword: vi.fn(),
		signUp: vi.fn(),
		signOut: vi.fn(),
		onAuthStateChange: vi.fn(),
		resetPasswordForEmail: vi.fn(),
		updateUser: vi.fn(),
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
			list: vi.fn().mockResolvedValue({ data: null, error: null }),
		})),
	},
	rpc: vi.fn().mockResolvedValue({ data: null, error: null }),
}

// Mock React Query
export const mockQueryClient = {
	getQueryData: vi.fn(),
	setQueryData: vi.fn(),
	invalidateQueries: vi.fn(),
	refetchQueries: vi.fn(),
	clear: vi.fn(),
	resetQueries: vi.fn(),
	removeQueries: vi.fn(),
	getQueryState: vi.fn(),
	getQueriesData: vi.fn(),
	setQueriesData: vi.fn(),
}

// Mock React Query hooks
export const mockUseQuery = vi.fn()
export const mockUseMutation = vi.fn()
export const mockUseQueryClient = vi.fn(() => mockQueryClient)

// Mock router
export const mockNavigate = vi.fn()
export const mockUseNavigate = vi.fn(() => mockNavigate)
export const mockUseLocation = vi.fn(() => ({
	pathname: '/',
	search: '',
	hash: '',
	state: null,
}))
export const mockUseParams = vi.fn(() => ({}))

// Mock window and browser APIs
export const mockLocalStorage = {
	getItem: vi.fn(),
	setItem: vi.fn(),
	removeItem: vi.fn(),
	clear: vi.fn(),
}

export const mockSessionStorage = {
	getItem: vi.fn(),
	setItem: vi.fn(),
	removeItem: vi.fn(),
	clear: vi.fn(),
}

export const mockFetch = vi.fn()

// Mock file upload
export const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' })
export const mockFileList = {
	0: mockFile,
	length: 1,
	item: vi.fn(() => mockFile),
	[Symbol.iterator]: function* () {
		yield mockFile
	},
}

// Mock form data
export const mockFormData = {
	append: vi.fn(),
	delete: vi.fn(),
	get: vi.fn(),
	getAll: vi.fn(),
	has: vi.fn(),
	set: vi.fn(),
	entries: vi.fn(),
	keys: vi.fn(),
	values: vi.fn(),
	forEach: vi.fn(),
}

// Mock URL
export const mockURL = {
	createObjectURL: vi.fn(() => 'mock-url'),
	revokeObjectURL: vi.fn(),
}

// Mock Intersection Observer
export const mockIntersectionObserver = {
	observe: vi.fn(),
	unobserve: vi.fn(),
	disconnect: vi.fn(),
}

// Mock Resize Observer
export const mockResizeObserver = {
	observe: vi.fn(),
	unobserve: vi.fn(),
	disconnect: vi.fn(),
}

// Mock WebSocket
export const mockWebSocket = {
	readyState: 1, // OPEN
	send: vi.fn(),
	close: vi.fn(),
	addEventListener: vi.fn(),
	removeEventListener: vi.fn(),
	dispatchEvent: vi.fn(),
}

// Mock console
export const mockConsole = {
	log: vi.fn(),
	error: vi.fn(),
	warn: vi.fn(),
	info: vi.fn(),
	debug: vi.fn(),
}

// Mock timers
export const mockSetTimeout = vi.fn()
export const mockClearTimeout = vi.fn()
export const mockSetInterval = vi.fn()
export const mockClearInterval = vi.fn()

// Mock date
export const mockDate = new Date('2024-01-01T00:00:00Z')
export const mockDateNow = vi.fn(() => mockDate.getTime())

// Setup function to apply all mocks
export const setupMocks = () => {
	// Mock global fetch
	global.fetch = mockFetch

	// Mock localStorage and sessionStorage
	Object.defineProperty(window, 'localStorage', {
		value: mockLocalStorage,
		writable: true,
	})
	Object.defineProperty(window, 'sessionStorage', {
		value: mockSessionStorage,
		writable: true,
	})

	// Mock URL methods
	Object.defineProperty(URL, 'createObjectURL', {
		value: mockURL.createObjectURL,
		writable: true,
	})
	Object.defineProperty(URL, 'revokeObjectURL', {
		value: mockURL.revokeObjectURL,
		writable: true,
	})

	// Mock IntersectionObserver
	global.IntersectionObserver = vi.fn().mockImplementation(() => mockIntersectionObserver)

	// Mock ResizeObserver
	global.ResizeObserver = vi.fn().mockImplementation(() => mockResizeObserver)

	// Mock WebSocket
	global.WebSocket = vi.fn().mockImplementation(() => mockWebSocket)

	// Mock console
	Object.assign(console, mockConsole)

	// Mock timers
	global.setTimeout = mockSetTimeout
	global.clearTimeout = mockClearTimeout
	global.setInterval = mockSetInterval
	global.clearInterval = mockClearInterval

	// Mock Date.now
	Date.now = mockDateNow
}

// Cleanup function to reset all mocks
export const cleanupMocks = () => {
	vi.clearAllMocks()
}
