import { describe, it, expect, vi, beforeEach } from 'vitest';
import { InsuranceClaimsService } from '../insuranceClaimsService';

// Mock fetch globally
global.fetch = vi.fn();

describe('InsuranceClaimsService', () => {
  let service: InsuranceClaimsService;

  beforeEach(() => {
    vi.clearAllMocks();
    service = new InsuranceClaimsService({
      provider: 'custom',
      apiUrl: 'https://api.test-insurance.com',
      apiKey: 'test-api-key',
      version: '1.0',
      timeout: 30000
    });
  });

  describe('Policy Operations', () => {
    it('successfully looks up policy information', async () => {
      const mockPolicyData = {
        policyNumber: 'POL-123456',
        policyType: 'Auto Insurance',
        coverageAmount: 100000,
        deductible: 500,
        effectiveDate: '2024-01-01',
        expirationDate: '2024-12-31',
        status: 'active',
        policyHolder: {
          name: 'John Doe',
          email: 'john.doe@email.com',
          phone: '+1234567890',
          address: '123 Main St, Anytown, ST 12345'
        }
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPolicyData
      });

      const result = await service.lookupPolicy('POL-123456');

      expect(fetch).toHaveBeenCalledWith(
        'https://api.test-insurance.com/policies/POL-123456',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-api-key',
            'X-API-Version': '1.0'
          })
        })
      );

      expect(result).toEqual(mockPolicyData);
    });

    it('handles policy lookup failure with fallback data', async () => {
      (fetch as any).mockRejectedValueOnce(new Error('Network error'));

      const result = await service.lookupPolicy('POL-123456');

      expect(result).toEqual({
        policyNumber: 'POL-123456',
        policyType: 'Auto Insurance',
        coverageAmount: 100000,
        deductible: 500,
        effectiveDate: '2024-01-01',
        expirationDate: '2024-12-31',
        status: 'active',
        policyHolder: {
          name: 'John Doe',
          email: 'john.doe@email.com',
          phone: '+1234567890',
          address: '123 Main St, Anytown, ST 12345'
        }
      });
    });

    it('verifies policy with matching phone number', async () => {
      const mockPolicyData = {
        policyNumber: 'POL-123456',
        status: 'active',
        policyHolder: { phone: '+1234567890' }
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPolicyData
      });

      const result = await service.verifyPolicy('POL-123456', '+1234567890');

      expect(result).toEqual({ verified: true });
    });

    it('rejects policy verification with non-matching phone', async () => {
      const mockPolicyData = {
        policyNumber: 'POL-123456',
        status: 'active',
        policyHolder: { phone: '+1234567890' }
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPolicyData
      });

      const result = await service.verifyPolicy('POL-123456', '+9876543210');

      expect(result).toEqual({
        verified: false,
        reason: 'Phone number does not match policy holder'
      });
    });
  });

  describe('Claims Operations', () => {
    it('creates a new claim successfully', async () => {
      const claimRequest = {
        policyNumber: 'POL-123456',
        incidentDate: '2024-01-15',
        incidentLocation: '123 Main St',
        incidentDescription: 'Vehicle collision',
        claimType: 'auto',
        estimatedDamage: 5000,
        customerPhone: '+1234567890'
      };

      const mockClaimResponse = {
        claimNumber: 'CLM-123456-ABCD',
        policyNumber: 'POL-123456',
        incidentDate: '2024-01-15',
        reportedDate: '2024-01-16T10:00:00Z',
        claimType: 'auto',
        status: 'pending',
        description: 'Vehicle collision',
        estimatedAmount: 5000,
        documents: []
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockClaimResponse
      });

      const result = await service.createClaim(claimRequest);

      expect(fetch).toHaveBeenCalledWith(
        'https://api.test-insurance.com/claims',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-api-key'
          }),
          body: expect.stringContaining('"policyNumber":"POL-123456"')
        })
      );

      expect(result.claimNumber).toMatch(/^CLM-/);
      expect(result.status).toBe('pending');
    });

    it('gets claim status', async () => {
      const mockClaimData = {
        claimNumber: 'CLM-123456-ABCD',
        policyNumber: 'POL-123456',
        status: 'under_review',
        adjusterAssigned: 'Jane Smith'
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockClaimData
      });

      const result = await service.getClaimStatus('CLM-123456-ABCD');

      expect(result.claimNumber).toBe('CLM-123456-ABCD');
      expect(result.status).toBe('under_review');
    });

    it('updates claim information', async () => {
      const updates = { status: 'approved', settledAmount: 4500 };
      const mockUpdatedClaim = {
        claimNumber: 'CLM-123456-ABCD',
        status: 'approved',
        settledAmount: 4500
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUpdatedClaim
      });

      const result = await service.updateClaim('CLM-123456-ABCD', updates);

      expect(fetch).toHaveBeenCalledWith(
        'https://api.test-insurance.com/claims/CLM-123456-ABCD',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify(updates)
        })
      );

      expect(result.status).toBe('approved');
    });
  });

  describe('Fraud Assessment', () => {
    it('performs fraud assessment on claim', async () => {
      const mockFraudAssessment = {
        riskScore: 25,
        riskLevel: 'low',
        flags: [],
        recommendation: 'approve',
        reasoning: 'No significant fraud indicators detected'
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockFraudAssessment
      });

      const result = await service.assessFraud('CLM-123456-ABCD');

      expect(result.riskScore).toBe(25);
      expect(result.riskLevel).toBe('low');
      expect(result.recommendation).toBe('approve');
    });

    it('handles fraud assessment with high risk score', async () => {
      const mockHighRiskAssessment = {
        riskScore: 85,
        riskLevel: 'high',
        flags: [
          {
            type: 'duplicate_claim',
            description: 'Similar claim filed recently',
            severity: 'warning'
          }
        ],
        recommendation: 'investigate',
        reasoning: 'Multiple risk indicators detected'
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHighRiskAssessment
      });

      const result = await service.assessFraud('CLM-123456-ABCD');

      expect(result.riskScore).toBe(85);
      expect(result.riskLevel).toBe('high');
      expect(result.recommendation).toBe('investigate');
      expect(result.flags).toHaveLength(1);
    });
  });

  describe('Settlement Calculation', () => {
    it('calculates settlement amount correctly', async () => {
      const damageAssessment = {
        totalDamage: 5000,
        laborCosts: 3000,
        partsCosts: 2000
      };

      const mockSettlement = {
        claimNumber: 'CLM-123456-ABCD',
        totalDamage: 5000,
        deductible: 500,
        coverageLimit: 100000,
        depreciation: 0,
        settlementAmount: 4500,
        breakdown: [
          {
            category: 'Vehicle Repair',
            amount: 5000,
            description: 'Total repair costs'
          },
          {
            category: 'Deductible',
            amount: -500,
            description: 'Policy deductible'
          }
        ]
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettlement
      });

      const result = await service.calculateSettlement('CLM-123456-ABCD', damageAssessment);

      expect(result.settlementAmount).toBe(4500);
      expect(result.breakdown).toHaveLength(2);
      expect(result.totalDamage - result.deductible).toBe(result.settlementAmount);
    });
  });

  describe('VAPI Function Handling', () => {
    it('handles check_policy_status function', async () => {
      const mockPolicy = {
        status: 'active',
        policyType: 'Auto Insurance',
        coverageAmount: 100000,
        deductible: 500,
        expirationDate: '2024-12-31'
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPolicy
      });

      const result = await service.handleVAPIFunction(
        'check_policy_status',
        { policyNumber: 'POL-123456' },
        { customerPhone: '+1234567890' }
      );

      expect(result.status).toBe('active');
      expect(result.policyType).toBe('Auto Insurance');
    });

    it('handles create_claim function', async () => {
      const mockClaim = {
        claimNumber: 'CLM-123456-ABCD',
        status: 'pending'
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockClaim
      });

      const result = await service.handleVAPIFunction(
        'create_claim',
        {
          policyNumber: 'POL-123456',
          incidentDate: '2024-01-15',
          incidentDescription: 'Vehicle collision'
        },
        { customerPhone: '+1234567890' }
      );

      expect(result.success).toBe(true);
      expect(result.claimNumber).toMatch(/^CLM-/);
    });

    it('handles unknown function gracefully', async () => {
      const result = await service.handleVAPIFunction(
        'unknown_function',
        {},
        { customerPhone: '+1234567890' }
      );

      expect(result.error).toBe(true);
      expect(result.message).toContain('error');
    });
  });

  describe('Connection Testing', () => {
    it('successfully tests API connection', async () => {
      const mockHealthResponse = {
        status: 'healthy',
        version: '1.0.0'
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealthResponse
      });

      const result = await service.testConnection();

      expect(result.success).toBe(true);
      expect(result.message).toContain('Successfully connected');
    });

    it('handles connection failure', async () => {
      (fetch as any).mockRejectedValueOnce(new Error('Connection failed'));

      const result = await service.testConnection();

      expect(result.success).toBe(false);
      expect(result.message).toContain('Failed to connect');
    });
  });

  describe('Document Upload', () => {
    it('uploads claim document successfully', async () => {
      const mockFile = new File(['test'], 'document.pdf', { type: 'application/pdf' });
      const mockDocument = {
        id: 'doc_123456',
        type: 'police_report',
        filename: 'document.pdf',
        uploadDate: '2024-01-16T10:00:00Z',
        status: 'pending'
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDocument
      });

      const result = await service.uploadDocument('CLM-123456-ABCD', mockFile, 'police_report');

      expect(result.id).toBe('doc_123456');
      expect(result.filename).toBe('document.pdf');
    });
  });

  describe('Utility Functions', () => {
    it('generates unique claim numbers', () => {
      const claimNumber1 = (service as any).generateClaimNumber();
      const claimNumber2 = (service as any).generateClaimNumber();

      expect(claimNumber1).toMatch(/^CLM-\d{6}-[A-Z0-9]{4}$/);
      expect(claimNumber2).toMatch(/^CLM-\d{6}-[A-Z0-9]{4}$/);
      expect(claimNumber1).not.toBe(claimNumber2);
    });

    it('calculates business days correctly', () => {
      const startDate = new Date('2024-01-15'); // Monday
      const result = (service as any).addBusinessDays(startDate, 5);

      expect(result.getDay()).not.toBe(0); // Not Sunday
      expect(result.getDay()).not.toBe(6); // Not Saturday
    });
  });
});