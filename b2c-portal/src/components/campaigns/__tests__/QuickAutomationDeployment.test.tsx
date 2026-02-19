/**
 * Unit tests for QuickAutomationDeployment component
 * Tests the new quick deploy extraction functionality using the /vapi-consolidated/quick-deploy-extract endpoint
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import QuickAutomationDeployment from '../QuickAutomationDeployment';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


// Mock external dependencies
vi.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      id: 'test-user-id',
      email: 'test@example.com'
    },
    getAccessToken: vi.fn().mockResolvedValue('mock-token')
  })
}));

vi.mock('../../../lib/core-api', () => ({
  saveAutomationConfiguration: vi.fn(),
  saveAssistantConfiguration: vi.fn(),
  storeDemoHTML: vi.fn()
}));

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock environment variables
vi.stubEnv('VITE_CORE_API_BASE_URL', API_BASE_URL);

describe('QuickAutomationDeployment', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const defaultProps = {
    companyName: 'Test Company',
    description: 'Test Description',
    automationType: 'sales' as const,
    onBack: vi.fn(),
    onNext: vi.fn(),
    onComplete: vi.fn(),
    industry: 'technology'
  };

  describe('Initial Rendering', () => {
    it('renders the component with correct initial state', () => {
      render(<QuickAutomationDeployment {...defaultProps} />);

      expect(screen.getByText('Quick VAPI Deployment')).toBeInTheDocument();
      expect(screen.getByText('Test Company')).toBeInTheDocument();
      expect(screen.getByText('Extract Company Information')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /start deployment/i })).toBeInTheDocument();
    });

    it('renders automation type and industry information', () => {
      render(<QuickAutomationDeployment {...defaultProps} />);

      expect(screen.getByText('sales')).toBeInTheDocument();
      expect(screen.getByText('technology')).toBeInTheDocument();
    });

    it('renders URL input field', () => {
      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      expect(urlInput).toBeInTheDocument();
      expect(urlInput).toHaveValue('');
    });
  });

  describe('Company Information Extraction', () => {
    const mockSuccessResponse = {
      success: true,
      extracted_data: {
        companyName: 'Test Company',
        name: 'Test Company',
        description: 'Extracted description',
        aboutText: 'About the company',
        services: ['Service 1', 'Service 2'],
        businessHours: 'Mon-Fri 9AM-5PM',
        contactInfo: {
          phone: '+1-234-567-8900',
          email: 'contact@testcompany.com',
          address: '123 Test St, Test City'
        },
        industry: 'technology',
        extraction_method: 'firecrawl_enhanced',
        confidence_score: 0.9,
        ai_enhanced: true,
        business_type: 'Technology Company',
        tone_style: 'Professional',
        target_audience: 'Business professionals'
      },
      system_prompt: 'You are a professional sales assistant for Test Company.',
      extraction_details: {
        method: 'firecrawl_enhanced',
        url: 'https://testcompany.com',
        automation_type: 'sales',
        timestamp: '2025-09-27T20:30:00.000Z'
      }
    };

    it('successfully extracts company information when valid URL is provided', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockSuccessResponse)
      });

      render(<QuickAutomationDeployment {...defaultProps} />);

      // Fill in URL and start extraction
      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://testcompany.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          'https://api.ailabsafrica.com/vapi-consolidated/quick-deploy-extract',
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Content-Type': 'application/json',
              'Authorization': 'Bearer mock-token'
            }),
            body: JSON.stringify({
              url: 'https://testcompany.com',
              automation_type: 'sales',
              company_name: null,
              industry: 'technology'
            })
          })
        );
      });

      await waitFor(() => {
        expect(screen.getByText('You are a professional sales assistant for Test Company.')).toBeInTheDocument();
        expect(screen.getByText('Service 1')).toBeInTheDocument();
        expect(screen.getByText('Service 2')).toBeInTheDocument();
        expect(screen.getByText('+1-234-567-8900')).toBeInTheDocument();
        expect(screen.getByText('contact@testcompany.com')).toBeInTheDocument();
      });
    });

    it('handles extraction failure with specific error types', async () => {
      const mockErrorResponse = {
        success: false,
        error: 'Failed to extract company information',
        error_type: 'extraction_failed'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockErrorResponse)
      });

      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://invalid-site.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText(/extraction failed/i)).toBeInTheDocument();
        expect(screen.getByText(/failed to extract company information/i)).toBeInTheDocument();
      });
    });

    it('handles network errors during extraction', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://testcompany.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });

    it('handles authentication errors (401)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Unauthorized' })
      });

      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://testcompany.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText(/authentication required/i)).toBeInTheDocument();
      });
    });

    it('handles rate limiting errors (429)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: () => Promise.resolve({ error: 'Rate limit exceeded', retry_after: 60 })
      });

      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://testcompany.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText(/rate limit/i)).toBeInTheDocument();
      });
    });
  });

  describe('URL Validation', () => {
    it('validates URL format before extraction', () => {
      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'invalid-url' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      // Should show validation error or prevent submission
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('handles empty URL input', () => {
      render(<QuickAutomationDeployment {...defaultProps} />);

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      // Should not make API call with empty URL
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('accepts valid HTTP URLs', () => {
      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'http://testcompany.com' } });

      expect(urlInput).toHaveValue('http://testcompany.com');
    });

    it('accepts valid HTTPS URLs', () => {
      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://testcompany.com' } });

      expect(urlInput).toHaveValue('https://testcompany.com');
    });
  });

  describe('Loading States', () => {
    it('shows loading state during extraction', async () => {
      // Create a pending promise to simulate loading
      let resolvePromise: (value: any) => void;
      const pendingPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      mockFetch.mockReturnValueOnce(pendingPromise);

      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://testcompany.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      // Check for loading indicators
      expect(screen.getByText(/extracting/i)).toBeInTheDocument();
      expect(startButton).toBeDisabled();

      // Resolve the promise to complete the test
      resolvePromise!({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          extracted_data: {},
          system_prompt: 'Test prompt'
        })
      });

      await waitFor(() => {
        expect(screen.queryByText(/extracting/i)).not.toBeInTheDocument();
      });
    });

    it('disables form during extraction', async () => {
      let resolvePromise: (value: any) => void;
      const pendingPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      mockFetch.mockReturnValueOnce(pendingPromise);

      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://testcompany.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      // Form should be disabled during extraction
      expect(urlInput).toBeDisabled();
      expect(startButton).toBeDisabled();

      // Resolve the promise
      resolvePromise!({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          extracted_data: {},
          system_prompt: 'Test prompt'
        })
      });

      await waitFor(() => {
        expect(urlInput).not.toBeDisabled();
      });
    });
  });

  describe('Error Recovery', () => {
    it('resets error state when starting new extraction', async () => {
      render(<QuickAutomationDeployment {...defaultProps} />);

      // First extraction fails
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          success: false,
          error: 'First error'
        })
      });

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://testcompany.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText(/first error/i)).toBeInTheDocument();
      });

      // Second extraction succeeds
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          extracted_data: {
            companyName: 'Success Company',
            services: []
          },
          system_prompt: 'Success prompt'
        })
      });

      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.queryByText(/first error/i)).not.toBeInTheDocument();
        expect(screen.getByText('Success prompt')).toBeInTheDocument();
      });
    });

    it('provides retry functionality after errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ error: 'Server error' })
      });

      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://testcompany.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText(/server error/i)).toBeInTheDocument();
      });

      // Retry should be possible
      expect(startButton).not.toBeDisabled();
    });
  });

  describe('Props and Callbacks', () => {
    it('calls onBack when back button is clicked', () => {
      render(<QuickAutomationDeployment {...defaultProps} />);

      const backButton = screen.getByRole('button', { name: /back/i });
      fireEvent.click(backButton);

      expect(defaultProps.onBack).toHaveBeenCalledTimes(1);
    });

    it('displays different automation types correctly', () => {
      const { rerender } = render(
        <QuickAutomationDeployment {...defaultProps} automationType="helpdesk" />
      );

      expect(screen.getByText('helpdesk')).toBeInTheDocument();

      rerender(
        <QuickAutomationDeployment {...defaultProps} automationType="healthcare" />
      );

      expect(screen.getByText('healthcare')).toBeInTheDocument();
    });

    it('displays different industries correctly', () => {
      const { rerender } = render(
        <QuickAutomationDeployment {...defaultProps} industry="healthcare" />
      );

      expect(screen.getByText('healthcare')).toBeInTheDocument();

      rerender(
        <QuickAutomationDeployment {...defaultProps} industry="finance" />
      );

      expect(screen.getByText('finance')).toBeInTheDocument();
    });

    it('handles missing industry prop', () => {
      const propsWithoutIndustry = {
        ...defaultProps,
        industry: undefined
      };

      render(<QuickAutomationDeployment {...propsWithoutIndustry} />);

      // Should still render without errors
      expect(screen.getByText('Quick VAPI Deployment')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      expect(urlInput).toHaveAttribute('aria-label');
    });

    it('supports keyboard navigation', () => {
      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      urlInput.focus();

      expect(document.activeElement).toBe(urlInput);
    });

    it('shows error messages with proper ARIA attributes', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          success: false,
          error: 'Test error'
        })
      });

      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://testcompany.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        const errorMessage = screen.getByText(/test error/i);
        expect(errorMessage).toBeInTheDocument();
        expect(errorMessage).toHaveAttribute('role', 'alert');
      });
    });
  });
});