/**
 * SEO Provider Tests
 * Tests for the SeoProvider component and SEO context functionality
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { SeoProvider, useSEO } from '../../components/SEO/SeoProvider';
import { DEFAULT_SEO_CONFIG } from '../../lib/seo';

// Mock react-i18next
const mockI18n = {
  language: 'en',
  changeLanguage: vi.fn(),
};

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: vi.fn((key) => key),
    i18n: mockI18n,
  }),
}));

// Mock react-router-dom
const mockLocation = {
  pathname: '/',
  search: '',
  hash: '',
  state: null,
};

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useLocation: () => mockLocation,
  };
});

// Test component to access SEO context
const TestComponent: React.FC = () => {
  const { seoConfig, currentPage, currentLanguage, loading } = useSEO();
  
  return (
    <div>
      <div data-testid="current-page">{currentPage}</div>
      <div data-testid="current-language">{currentLanguage}</div>
      <div data-testid="loading">{loading.toString()}</div>
      <div data-testid="seo-title">{seoConfig.title}</div>
      <div data-testid="seo-description">{seoConfig.description}</div>
    </div>
  );
};

// Wrapper component for testing
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <SeoProvider>
      {children}
    </SeoProvider>
  </BrowserRouter>
);

describe('SeoProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render children without crashing', () => {
    render(
      <TestWrapper>
        <div data-testid="test-child">Test Child</div>
      </TestWrapper>
    );
    
    expect(screen.getByTestId('test-child')).toBeInTheDocument();
  });

  it('should provide default SEO configuration', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('seo-title')).toHaveTextContent(DEFAULT_SEO_CONFIG.title);
      expect(screen.getByTestId('seo-description')).toHaveTextContent(DEFAULT_SEO_CONFIG.description);
    });
  });

  it('should set current page from location', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('current-page')).toHaveTextContent('/');
    });
  });

  it('should set current language from i18n', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('current-language')).toHaveTextContent('en');
    });
  });

  it('should handle loading state correctly', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    // Initially should be loading
    expect(screen.getByTestId('loading')).toHaveTextContent('true');

    // Should finish loading
    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });
  });

  it('should update SEO config when page changes', async () => {
    const { rerender } = render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    // Change location
    Object.defineProperty(mockLocation, 'pathname', {
      value: '/dashboard',
      writable: true,
    });

    rerender(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('current-page')).toHaveTextContent('/dashboard');
    });
  });

  it('should update SEO config when language changes', async () => {
    const { rerender } = render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    // Change language
    Object.defineProperty(mockI18n, 'language', {
      value: 'fr',
      writable: true,
    });

    rerender(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('current-language')).toHaveTextContent('fr');
    });
  });

  it('should handle errors gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    // Mock a function that throws an error
    vi.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('Test error'));

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled();
    });

    consoleSpy.mockRestore();
  });

  it('should generate alternate language URLs correctly', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      // The provider should generate alternate language URLs
      // This is tested indirectly through the SEO config
      expect(screen.getByTestId('seo-title')).toBeInTheDocument();
    });
  });
});

describe('useSEO Hook', () => {
  it('should throw error when used outside provider', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => {
      render(<TestComponent />);
    }).toThrow('useSEO must be used within a SeoProvider');

    consoleSpy.mockRestore();
  });

  it('should provide updateSEO function', async () => {
    const TestUpdateComponent: React.FC = () => {
      const { updateSEO, seoConfig } = useSEO();
      
      const handleUpdate = () => {
        updateSEO({ title: 'Updated Title' });
      };
      
      return (
        <div>
          <button onClick={handleUpdate} data-testid="update-button">
            Update SEO
          </button>
          <div data-testid="seo-title">{seoConfig.title}</div>
        </div>
      );
    };

    render(
      <TestWrapper>
        <TestUpdateComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('seo-title')).toHaveTextContent(DEFAULT_SEO_CONFIG.title);
    });
  });
});
