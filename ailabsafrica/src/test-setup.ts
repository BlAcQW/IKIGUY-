import '@testing-library/jest-dom';
import { vi } from 'vitest';
import { cleanup } from '@testing-library/react';

// Mock React 18 createRoot with a more comprehensive approach
vi.mock('react-dom/client', () => {
  const originalModule = vi.importActual('react-dom/client');
  
  return {
    ...originalModule,
    createRoot: vi.fn((container) => {
      // Validate and create container if needed
      if (!container || typeof container !== 'object') {
        container = document.createElement('div');
        container.id = 'test-root';
        document.body.appendChild(container);
      }
      
      // Ensure container has required DOM properties
      if (!container.tagName) container.tagName = 'DIV';
      if (!container.nodeType) container.nodeType = 1;
      if (!container.appendChild) container.appendChild = vi.fn();
      if (!container.removeChild) container.removeChild = vi.fn();
      if (!container.contains) container.contains = vi.fn(() => true);
      
      return {
        render: vi.fn((element) => {
          // Mock successful render
          return element;
        }),
        unmount: vi.fn(() => {
          // Clean up if we created the container
          if (container.id === 'test-root' && container.parentNode) {
            container.parentNode.removeChild(container);
          }
        }),
      };
    }),
  };
});

// Mock the main.tsx file to prevent it from executing during tests
vi.mock('@/main', () => ({
  default: vi.fn(),
}));

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
	observe: vi.fn(),
	unobserve: vi.fn(),
	disconnect: vi.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
	observe: vi.fn(),
	unobserve: vi.fn(),
	disconnect: vi.fn(),
}));

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
	writable: true,
	value: vi.fn().mockImplementation(query => ({
		matches: false,
		media: query,
		onchange: null,
		addListener: vi.fn(), // deprecated
		removeListener: vi.fn(), // deprecated
		addEventListener: vi.fn(),
		removeEventListener: vi.fn(),
		dispatchEvent: vi.fn(),
	})),
});

// Mock window.scrollTo
Object.defineProperty(window, 'scrollTo', {
	writable: true,
	value: vi.fn(),
});

// Mock window.getComputedStyle
Object.defineProperty(window, 'getComputedStyle', {
	writable: true,
	value: vi.fn().mockReturnValue({
		getPropertyValue: vi.fn().mockReturnValue(''),
	}),
});

// Mock document.createElement for download links and other DOM elements
const mockCreateElement = vi.fn();
const mockClick = vi.fn();
const mockLink = {
	href: '',
	download: '',
	click: mockClick,
	appendChild: vi.fn(),
	removeChild: vi.fn(),
	setAttribute: vi.fn(),
	getAttribute: vi.fn(),
	style: {},
	addEventListener: vi.fn(),
	removeEventListener: vi.fn(),
	dispatchEvent: vi.fn(),
};

mockCreateElement.mockReturnValue(mockLink);
Object.defineProperty(document, 'createElement', {
	value: mockCreateElement,
	writable: true,
});

// Mock document.body.appendChild and other DOM methods
const mockAppendChild = vi.fn();
const mockRemoveChild = vi.fn();
const mockContains = vi.fn(() => true);

Object.defineProperty(document.body, 'appendChild', {
	value: mockAppendChild,
	writable: true,
});

Object.defineProperty(document.body, 'removeChild', {
	value: mockRemoveChild,
	writable: true,
});

Object.defineProperty(document.body, 'contains', {
	value: mockContains,
	writable: true,
});

// Mock URL.createObjectURL and URL.revokeObjectURL
const mockCreateObjectURL = vi.fn(() => 'blob:mock-url');
const mockRevokeObjectURL = vi.fn();

Object.defineProperty(URL, 'createObjectURL', {
	value: mockCreateObjectURL,
	writable: true,
});

Object.defineProperty(URL, 'revokeObjectURL', {
	value: mockRevokeObjectURL,
	writable: true,
});

// Mock performance API
const mockPerformance = {
	now: vi.fn(() => 1000),
	memory: {
		usedJSHeapSize: 50 * 1024 * 1024, // 50MB
	},
	getEntriesByType: vi.fn(() => []),
	getEntriesByName: vi.fn(() => []),
	getEntries: vi.fn(() => []),
};

Object.defineProperty(window, 'performance', {
	value: mockPerformance,
	writable: true,
});

// Mock PerformanceObserver
const mockPerformanceObserver = vi.fn();
const mockObserve = vi.fn();
const mockDisconnect = vi.fn();

mockPerformanceObserver.mockImplementation(() => ({
	observe: mockObserve,
	disconnect: mockDisconnect,
}));

Object.defineProperty(window, 'PerformanceObserver', {
	value: mockPerformanceObserver,
	writable: true,
});

// Mock fetch
global.fetch = vi.fn();

// Mock localStorage
Object.defineProperty(window, 'localStorage', {
	value: {
		getItem: vi.fn(),
		setItem: vi.fn(),
		removeItem: vi.fn(),
		clear: vi.fn(),
	},
	writable: true,
});

// Mock sessionStorage
Object.defineProperty(window, 'sessionStorage', {
	value: {
		getItem: vi.fn(),
		setItem: vi.fn(),
		removeItem: vi.fn(),
		clear: vi.fn(),
	},
	writable: true,
});

// Mock console methods to reduce noise in tests
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;
const originalConsoleLog = console.log;

beforeAll(() => {
	console.error = (...args) => {
		// Suppress specific warnings that are expected in tests
		if (
			typeof args[0] === 'string' &&
			(args[0].includes('Warning: An update to') ||
				args[0].includes('Warning: ReactDOM.render is no longer supported') ||
				args[0].includes('Warning: createRoot') ||
				args[0].includes('Warning: findDOMNode') ||
				args[0].includes('Warning: componentWillReceiveProps') ||
				args[0].includes('Warning: componentWillUpdate') ||
				args[0].includes('Target container is not a DOM element'))
		) {
			return;
		}
		originalConsoleError.call(console, ...args);
	};

	console.warn = (...args) => {
		// Suppress specific warnings that are expected in tests
		if (
			typeof args[0] === 'string' &&
			(args[0].includes('Warning: An update to') ||
				args[0].includes('Warning: ReactDOM.render is no longer supported') ||
				args[0].includes('Warning: createRoot') ||
				args[0].includes('Warning: findDOMNode') ||
				args[0].includes('Warning: componentWillReceiveProps') ||
				args[0].includes('Warning: componentWillUpdate'))
		) {
			return;
		}
		originalConsoleWarn.call(console, ...args);
	};

	console.log = (...args) => {
		// Suppress console.log in tests unless it's important
		if (
			typeof args[0] === 'string' &&
			(args[0].includes('CDN failed') ||
				args[0].includes('CDN health check failed') ||
				args[0].includes('Error in hash_guest_password') ||
				args[0].includes('Error in verify_guest_password'))
		) {
			return;
		}
		originalConsoleLog.call(console, ...args);
	};
});

afterAll(() => {
	console.error = originalConsoleError;
	console.warn = originalConsoleWarn;
	console.log = originalConsoleLog;
});

// Cleanup after each test
afterEach(() => {
	cleanup();
	vi.clearAllMocks();
	
	// Clean up any test containers we created
	const testRoot = document.getElementById('test-root');
	if (testRoot && testRoot.parentNode) {
		testRoot.parentNode.removeChild(testRoot);
	}
});

// Custom test utilities for better Radix UI testing
export const waitForElementToBeRemoved = (element: Element | null) => {
	return new Promise<void>((resolve) => {
		if (!element) {
			resolve();
			return;
		}

		const observer = new MutationObserver(() => {
			if (!document.contains(element)) {
				observer.disconnect();
				resolve();
			}
		});

		observer.observe(document.body, {
			childList: true,
			subtree: true,
		});
	});
};

// Helper to wait for async operations to complete
export const waitForAsync = (ms = 0) => new Promise(resolve => setTimeout(resolve, ms));

// Helper to wait for all promises to settle
export const waitForPromises = () => new Promise(resolve => setImmediate(resolve));

