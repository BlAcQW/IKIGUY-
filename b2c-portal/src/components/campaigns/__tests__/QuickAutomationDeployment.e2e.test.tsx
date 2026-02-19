/**
 * End-to-End tests for QuickAutomationDeployment component
 * Tests the complete workflow from URL input to automation deployment
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
    getAccessToken: vi.fn().mockResolvedValue('test-token')
  })
}));

const mockSaveAutomationConfiguration = vi.fn();
const mockSaveAssistantConfiguration = vi.fn();
const mockStoreDemoHTML = vi.fn();

vi.mock('../../../lib/core-api', () => ({
  saveAutomationConfiguration: mockSaveAutomationConfiguration,
  saveAssistantConfiguration: mockSaveAssistantConfiguration,
  storeDemoHTML: mockStoreDemoHTML
}));

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock environment variables
vi.stubEnv('VITE_CORE_API_BASE_URL', API_BASE_URL);

describe('QuickAutomationDeployment E2E Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockClear();
    mockSaveAutomationConfiguration.mockClear();
    mockSaveAssistantConfiguration.mockClear();
    mockStoreDemoHTML.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const defaultProps = {
    companyName: 'TechCorp Solutions',
    description: 'Leading technology solutions provider',
    automationType: 'sales' as const,
    onBack: vi.fn(),
    onNext: vi.fn(),
    onComplete: vi.fn(),
    industry: 'technology'
  };

  const mockCompleteExtractionResponse = {
    success: true,
    extracted_data: {
      companyName: 'TechCorp Solutions',
      name: 'TechCorp Solutions',
      description: 'Leading technology solutions provider specializing in enterprise software',
      aboutText: 'We provide cutting-edge technology solutions to help businesses scale and innovate.',
      services: [
        'Enterprise Software Development',
        'Cloud Migration Services',
        'AI/ML Consulting',
        'Digital Transformation'
      ],
      businessHours: 'Monday-Friday 9AM-6PM EST',
      contactInfo: {
        phone: '+1-555-0123',
        email: 'contact@techcorp.com',
        address: '123 Tech Street, San Francisco, CA 94105'
      },
      industry: 'technology',
      extraction_method: 'firecrawl_enhanced',
      confidence_score: 0.95,
      ai_enhanced: true,
      business_type: 'B2B Software Company',
      tone_style: 'Professional and innovative',
      target_audience: 'Enterprise decision makers and IT professionals'
    },
    system_prompt: `You are a professional sales assistant for TechCorp Solutions, a leading technology solutions provider.

Company Information:
- Name: TechCorp Solutions
- Industry: Technology
- Services: Enterprise Software Development, Cloud Migration Services, AI/ML Consulting, Digital Transformation
- Contact: +1-555-0123, contact@techcorp.com
- Business Hours: Monday-Friday 9AM-6PM EST

Your role is to:
1. Qualify leads and identify their technology needs
2. Explain our services and how they solve business challenges
3. Schedule consultations with our technical team
4. Provide accurate information about pricing and timelines

Maintain a professional, knowledgeable tone and focus on understanding the prospect's specific technology challenges and goals.`,
    extraction_details: {
      method: 'firecrawl_enhanced',
      url: 'https://techcorp.com',
      automation_type: 'sales',
      timestamp: '2025-09-27T20:30:00.000Z'
    }
  };

  describe('Complete Deployment Workflow', () => {
    it('completes the full deployment workflow successfully', async () => {
      // Mock the extraction API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockCompleteExtractionResponse)
      });

      // Mock VAPI assistant creation response
      const vapiCreateResponse = {
        success: true,
        data: {
          id: 'asst_123456789',
          name: 'TechCorp Sales Assistant',
          model: 'gpt-4',
          instructions: mockCompleteExtractionResponse.system_prompt,
          tools: []
        }
      };

      // Mock demo HTML generation response
      const demoHtmlResponse = {
        success: true,
        html_content: '<html><head><title>TechCorp Demo</title></head><body><h1>Voice Demo</h1></body></html>',
        demo_url: 'https://demo.techcorp.com/voice-demo'
      };

      // Setup subsequent API responses for full workflow
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(vapiCreateResponse)
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(demoHtmlResponse)
        });

      // Mock core API functions
      mockSaveAutomationConfiguration.mockResolvedValue({
        success: true,
        id: 'automation_123'
      });

      mockSaveAssistantConfiguration.mockResolvedValue({
        success: true,
        id: 'assistant_123'
      });

      mockStoreDemoHTML.mockResolvedValue({
        success: true,
        demo_id: 'demo_123'
      });

      render(<QuickAutomationDeployment {...defaultProps} />);

      // Step 1: Enter company URL
      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://techcorp.com' } });

      // Step 2: Start deployment
      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      // Wait for extraction to complete
      await waitFor(() => {
        expect(screen.getByText(/Enterprise Software Development/)).toBeInTheDocument();
      }, { timeout: 10000 });

      // Verify extraction API was called correctly
      expect(mockFetch).toHaveBeenNthCalledWith(1,
        'https://api.ailabsafrica.com/vapi-consolidated/quick-deploy-extract',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token'
          }),
          body: JSON.stringify({
            url: 'https://techcorp.com',
            automation_type: 'sales',
            company_name: null,
            industry: 'technology'
          })
        })
      );

      // Verify extracted data is displayed
      expect(screen.getByText('TechCorp Solutions')).toBeInTheDocument();
      expect(screen.getByText(/Enterprise Software Development/)).toBeInTheDocument();
      expect(screen.getByText(/Cloud Migration Services/)).toBeInTheDocument();
      expect(screen.getByText('+1-555-0123')).toBeInTheDocument();
      expect(screen.getByText('contact@techcorp.com')).toBeInTheDocument();

      // Verify system prompt is displayed
      expect(screen.getByText(/You are a professional sales assistant for TechCorp Solutions/)).toBeInTheDocument();

      // Step 3: Continue with VAPI assistant creation
      const continueButton = screen.getByRole('button', { name: /continue/i });
      fireEvent.click(continueButton);

      // Wait for VAPI assistant creation
      await waitFor(() => {
        expect(screen.getByText(/assistant created/i)).toBeInTheDocument();
      }, { timeout: 10000 });

      // Verify VAPI API was called
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/vapi'),
        expect.objectContaining({
          method: 'POST'
        })
      );

      // Step 4: Generate and deploy demo HTML
      const deployButton = screen.getByRole('button', { name: /deploy demo/i });
      fireEvent.click(deployButton);

      // Wait for demo generation
      await waitFor(() => {
        expect(screen.getByText(/demo deployed successfully/i)).toBeInTheDocument();
      }, { timeout: 10000 });

      // Verify all core API functions were called
      expect(mockSaveAutomationConfiguration).toHaveBeenCalledWith(
        expect.objectContaining({
          companyName: 'TechCorp Solutions',
          automationType: 'sales',
          industry: 'technology'
        })
      );

      expect(mockSaveAssistantConfiguration).toHaveBeenCalledWith(
        expect.objectContaining({
          assistant_id: 'asst_123456789',
          name: 'TechCorp Sales Assistant'
        })
      );

      expect(mockStoreDemoHTML).toHaveBeenCalledWith(
        expect.objectContaining({
          html_content: expect.stringContaining('<html>'),
          demo_url: 'https://demo.techcorp.com/voice-demo'
        })
      );

      // Verify completion callback
      expect(defaultProps.onComplete).toHaveBeenCalledWith(
        expect.objectContaining({
          automationId: 'automation_123',
          assistantId: 'assistant_123',
          demoId: 'demo_123'
        })
      );
    });

    it('handles partial workflow failures gracefully', async () => {
      // Mock successful extraction but failed VAPI creation
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockCompleteExtractionResponse)
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          json: () => Promise.resolve({
            success: false,
            error: 'VAPI API key not configured'
          })
        });

      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://techcorp.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      // Wait for extraction success
      await waitFor(() => {
        expect(screen.getByText('TechCorp Solutions')).toBeInTheDocument();
      });

      // Continue to VAPI creation
      const continueButton = screen.getByRole('button', { name: /continue/i });
      fireEvent.click(continueButton);

      // Wait for VAPI creation failure
      await waitFor(() => {
        expect(screen.getByText(/vapi.*error/i)).toBeInTheDocument();
      });

      // Verify error handling doesn't break the component
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });
  });

  describe('Different Automation Types', () => {
    it('handles helpdesk automation type', async () => {
      const helpdeskProps = {
        ...defaultProps,
        automationType: 'helpdesk' as const
      };

      const helpdeskResponse = {
        ...mockCompleteExtractionResponse,
        system_prompt: 'You are a professional helpdesk assistant for TechCorp Solutions.'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(helpdeskResponse)
      });

      render(<QuickAutomationDeployment {...helpdeskProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://techcorp.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            body: JSON.stringify({
              url: 'https://techcorp.com',
              automation_type: 'helpdesk',
              company_name: null,
              industry: 'technology'
            })
          })
        );
      });

      await waitFor(() => {
        expect(screen.getByText(/helpdesk assistant/i)).toBeInTheDocument();
      });
    });

    it('handles healthcare automation type', async () => {
      const healthcareProps = {
        ...defaultProps,
        automationType: 'healthcare' as const,
        industry: 'healthcare'
      };

      const healthcareResponse = {
        ...mockCompleteExtractionResponse,
        system_prompt: 'You are a professional healthcare assistant.',
        extracted_data: {
          ...mockCompleteExtractionResponse.extracted_data,
          industry: 'healthcare'
        }
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(healthcareResponse)
      });

      render(<QuickAutomationDeployment {...healthcareProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://healthcarecorp.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            body: JSON.stringify({
              url: 'https://healthcarecorp.com',
              automation_type: 'healthcare',
              company_name: null,
              industry: 'healthcare'
            })
          })
        );
      });
    });
  });

  describe('Real-world Scenarios', () => {
    it('handles slow extraction responses', async () => {
      // Simulate slow response
      const slowPromise = new Promise(resolve => {
        setTimeout(() => {
          resolve({
            ok: true,
            json: () => Promise.resolve(mockCompleteExtractionResponse)
          });
        }, 3000);
      });

      mockFetch.mockReturnValueOnce(slowPromise);

      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://techcorp.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      // Should show loading state
      expect(screen.getByText(/extracting/i)).toBeInTheDocument();
      expect(startButton).toBeDisabled();

      // Wait for completion
      await waitFor(() => {
        expect(screen.getByText('TechCorp Solutions')).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('handles rate limiting with retry', async () => {
      // First call rate limited
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: () => Promise.resolve({
          error: 'Rate limit exceeded',
          retry_after: 1
        })
      });

      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://techcorp.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText(/rate limit/i)).toBeInTheDocument();
      });

      // Second call succeeds
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockCompleteExtractionResponse)
      });

      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText('TechCorp Solutions')).toBeInTheDocument();
      });
    });

    it('handles malformed URLs gracefully', async () => {
      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);

      // Test various malformed URLs
      const malformedUrls = [
        'not-a-url',
        'ftp://example.com',
        'javascript:alert(1)',
        'http://',
        'https://'
      ];

      for (const url of malformedUrls) {
        fireEvent.change(urlInput, { target: { value: url } });

        const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
        fireEvent.click(startButton);

        // Should not make API calls for invalid URLs
        expect(mockFetch).not.toHaveBeenCalled();

        // Clear input for next test
        fireEvent.change(urlInput, { target: { value: '' } });
      }
    });

    it('handles different extraction confidence levels', async () => {
      const lowConfidenceResponse = {
        ...mockCompleteExtractionResponse,
        extracted_data: {
          ...mockCompleteExtractionResponse.extracted_data,
          confidence_score: 0.3
        }
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(lowConfidenceResponse)
      });

      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://techcorp.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText(/low confidence/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Recovery Scenarios', () => {
    it('allows retry after extraction failures', async () => {
      // First call fails
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          success: false,
          error: 'Website unreachable',
          error_type: 'website_unreachable'
        })
      });

      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://unreachable.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText(/website unreachable/i)).toBeInTheDocument();
      });

      // Second call succeeds
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockCompleteExtractionResponse)
      });

      fireEvent.change(urlInput, { target: { value: 'https://techcorp.com' } });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.queryByText(/website unreachable/i)).not.toBeInTheDocument();
        expect(screen.getByText('TechCorp Solutions')).toBeInTheDocument();
      });
    });

    it('maintains state across navigation', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockCompleteExtractionResponse)
      });

      render(<QuickAutomationDeployment {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/https:\/\/company\.com/i);
      fireEvent.change(urlInput, { target: { value: 'https://techcorp.com' } });

      const startButton = screen.getByRole('button', { name: /Extract Company Info.*Deploy/i });
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByText('TechCorp Solutions')).toBeInTheDocument();
      });

      // Navigate back and forward
      const backButton = screen.getByRole('button', { name: /back/i });
      fireEvent.click(backButton);

      expect(defaultProps.onBack).toHaveBeenCalled();

      // Extracted data should still be available when returning
      expect(screen.getByText('TechCorp Solutions')).toBeInTheDocument();
    });
  });
});