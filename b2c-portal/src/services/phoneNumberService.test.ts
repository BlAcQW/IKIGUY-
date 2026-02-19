import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import PhoneNumberService, { phoneNumberService } from './phoneNumberService';

// Mock fetch globally
global.fetch = vi.fn();

describe('PhoneNumberService', () => {
  let service: PhoneNumberService;

  beforeEach(() => {
    service = new PhoneNumberService();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('getPhoneNumbers', () => {
    it('should fetch phone numbers successfully', async () => {
      const mockNumbers = [
        {
          id: '1',
          number: '+1-555-1234',
          provider: 'Kasa AI',
          type: 'both',
          status: 'active',
          country: 'US',
          capabilities: ['voice', 'sms'],
          created_at: '2024-01-01'
        }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ numbers: mockNumbers })
      });

      const result = await service.getPhoneNumbers('user-123');
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/phone-numbers?user_id=user-123'),
        expect.objectContaining({
          headers: {
            'Content-Type': 'application/json'
          }
        })
      );
      expect(result).toEqual(mockNumbers);
    });

    it('should handle fetch errors', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error'
      });

      await expect(service.getPhoneNumbers('user-123')).rejects.toThrow(
        'Failed to fetch phone numbers: Internal Server Error'
      );
    });
  });

  describe('importFromVonage', () => {
    it('should import numbers from Vonage successfully', async () => {
      const mockNumbers = [
        {
          id: 'vonage-1',
          number: '+1-555-VONAGE',
          provider: 'Vonage',
          type: 'both',
          status: 'active',
          country: 'US',
          capabilities: ['voice', 'sms'],
          created_at: '2024-01-01'
        }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ numbers: mockNumbers })
      });

      const result = await service.importFromVonage('api-key', 'api-secret');
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/vonage/import'),
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            api_key: 'api-key',
            api_secret: 'api-secret'
          })
        })
      );
      expect(result).toEqual(mockNumbers);
    });

    it('should handle Vonage API errors', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ message: 'Invalid API credentials' })
      });

      await expect(service.importFromVonage('bad-key', 'bad-secret')).rejects.toThrow(
        'Invalid API credentials'
      );
    });
  });

  describe('importFromTelnyx', () => {
    it('should import numbers from Telnyx successfully', async () => {
      const mockNumbers = [
        {
          id: 'telnyx-1',
          number: '+1-555-TELNYX',
          provider: 'Telnyx',
          type: 'both',
          status: 'active',
          country: 'US',
          capabilities: ['voice', 'sms', 'mms'],
          created_at: '2024-01-01'
        }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ numbers: mockNumbers })
      });

      const result = await service.importFromTelnyx('telnyx-api-key');
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/telnyx/import'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            api_key: 'telnyx-api-key'
          })
        })
      );
      expect(result).toEqual(mockNumbers);
    });
  });

  describe('importFromTwilio', () => {
    it('should validate Twilio Account SID format', async () => {
      await expect(service.importFromTwilio('invalid-sid', 'auth-token')).rejects.toThrow(
        'Invalid Twilio Account SID format'
      );
    });

    it('should import numbers from Twilio with valid SID', async () => {
      const validSid = 'AC' + '0'.repeat(32); // Valid format: AC + 32 characters
      const mockNumbers = [
        {
          id: 'twilio-1',
          number: '+1-555-TWILIO',
          provider: 'Twilio',
          type: 'both',
          status: 'active',
          country: 'US',
          capabilities: ['voice', 'sms', 'mms', 'fax'],
          created_at: '2024-01-01'
        }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ numbers: mockNumbers })
      });

      const result = await service.importFromTwilio(validSid, 'auth-token');
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/twilio/import'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            account_sid: validSid,
            auth_token: 'auth-token'
          })
        })
      );
      expect(result).toEqual(mockNumbers);
    });
  });

  describe('configureSIPTrunk', () => {
    it('should validate SIP server URL format', async () => {
      await expect(service.configureSIPTrunk('not-a-valid-url!@#', 'user', 'pass')).rejects.toThrow(
        'Invalid SIP server URL format'
      );
    });

    it('should configure SIP trunk with valid URL', async () => {
      const mockTrunk = {
        id: 'sip-trunk-1',
        server: 'sip.example.com',
        status: 'connected'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ trunk: mockTrunk })
      });

      const result = await service.configureSIPTrunk('sip.example.com', 'user', 'pass');
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/sip/configure'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            server_url: 'sip.example.com',
            username: 'user',
            password: 'pass'
          })
        })
      );
      expect(result).toEqual(mockTrunk);
    });

    it('should accept SIP URLs with port numbers', async () => {
      const mockTrunk = { id: 'sip-trunk-1', status: 'connected' };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ trunk: mockTrunk })
      });

      const result = await service.configureSIPTrunk('sip:example.com:5060', 'user', 'pass');
      expect(result).toEqual(mockTrunk);
    });
  });

  describe('provisionKasaAINumber', () => {
    it('should provision a Kasa AI number successfully', async () => {
      const mockNumber = {
        id: 'kasaai-1',
        number: '+1-555-KASAAI',
        provider: 'Kasa AI',
        type: 'both',
        status: 'provisioning',
        country: 'US',
        capabilities: ['voice', 'sms', 'mms', 'ai-enhanced'],
        created_at: '2024-01-01'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ number: mockNumber })
      });

      const result = await service.provisionKasaAINumber('Starter', 'US');
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/kasaai/provision'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            plan: 'starter',
            country_code: 'US'
          })
        })
      );
      expect(result).toEqual(mockNumber);
    });

    it('should convert plan name to lowercase', async () => {
      const mockNumber = { id: 'kasaai-1', number: '+1-555-KASAAI' };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ number: mockNumber })
      });

      await service.provisionKasaAINumber('ENTERPRISE', 'US');
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/kasaai/provision'),
        expect.objectContaining({
          body: JSON.stringify({
            plan: 'enterprise',
            country_code: 'US'
          })
        })
      );
    });
  });

  describe('deletePhoneNumber', () => {
    it('should delete a phone number successfully', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      const result = await service.deletePhoneNumber('number-123');
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/phone-numbers/number-123'),
        expect.objectContaining({
          method: 'DELETE'
        })
      );
      expect(result).toBe(true);
    });
  });

  describe('updatePhoneNumber', () => {
    it('should update a phone number successfully', async () => {
      const updates = { status: 'inactive' as const };
      const mockUpdatedNumber = {
        id: 'number-123',
        number: '+1-555-1234',
        status: 'inactive'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ number: mockUpdatedNumber })
      });

      const result = await service.updatePhoneNumber('number-123', updates);
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/phone-numbers/number-123'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updates)
        })
      );
      expect(result).toEqual(mockUpdatedNumber);
    });
  });

  describe('portNumber', () => {
    it('should initiate number porting successfully', async () => {
      const mockPortedNumber = {
        id: 'ported-1',
        number: '+1-555-PORT',
        status: 'pending',
        ported_from: 'Twilio'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ number: mockPortedNumber })
      });

      const result = await service.portNumber(
        '+1-555-PORT',
        'Twilio',
        { account_sid: 'AC123', auth_token: 'token' }
      );
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/phone-numbers/port'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            number: '+1-555-PORT',
            from_provider: 'Twilio',
            account_details: { account_sid: 'AC123', auth_token: 'token' }
          })
        })
      );
      expect(result).toEqual(mockPortedNumber);
    });
  });

  describe('validateCredentials', () => {
    it('should return true for valid credentials', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ valid: true })
      });

      const result = await service.validateCredentials('vonage', {
        api_key: 'valid-key',
        api_secret: 'valid-secret'
      });
      
      expect(result).toBe(true);
    });

    it('should return false for invalid credentials', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false
      });

      const result = await service.validateCredentials('vonage', {
        api_key: 'invalid-key',
        api_secret: 'invalid-secret'
      });
      
      expect(result).toBe(false);
    });

    it('should handle network errors gracefully', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      const result = await service.validateCredentials('vonage', {
        api_key: 'key',
        api_secret: 'secret'
      });
      
      expect(result).toBe(false);
    });
  });

  describe('getKasaAIPlans', () => {
    it('should return all available plans', () => {
      const plans = service.getKasaAIPlans();
      
      expect(plans).toHaveLength(3);
      expect(plans[0].name).toBe('Starter');
      expect(plans[1].name).toBe('Professional');
      expect(plans[2].name).toBe('Enterprise');
    });

    it('should include plan limits', () => {
      const plans = service.getKasaAIPlans();
      
      expect(plans[0].limits).toEqual({
        numbers: 1,
        inbound_minutes: 'unlimited',
        outbound_minutes: 100
      });
    });
  });

  describe('searchAvailableNumbers', () => {
    it('should search for available numbers', async () => {
      const mockAvailableNumbers = [
        { number: '+1-555-0001', monthly_cost: 1.00, setup_cost: 0 },
        { number: '+1-555-0002', monthly_cost: 1.00, setup_cost: 0 }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ numbers: mockAvailableNumbers })
      });

      const result = await service.searchAvailableNumbers('US', '555', '000*');
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/phone-numbers/search?country=US&area_code=555&pattern=000*'),
        expect.any(Object)
      );
      expect(result).toEqual(mockAvailableNumbers);
    });
  });

  describe('getNumberUsageStats', () => {
    it('should fetch usage statistics', async () => {
      const mockStats = {
        inbound_calls: 150,
        outbound_calls: 75,
        sms_sent: 200,
        sms_received: 180,
        total_minutes: 1250
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ stats: mockStats })
      });

      const result = await service.getNumberUsageStats('number-123', '30d');
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/phone-numbers/number-123/usage?period=30d'),
        expect.any(Object)
      );
      expect(result).toEqual(mockStats);
    });
  });
});