import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';

/**
 * Phone Number Service
 * Handles all phone number operations including imports from various providers
 * and virtual number provisioning
 */

export interface PhoneNumber {
  id: string;
  number: string;
  provider: string;
  type: 'inbound' | 'outbound' | 'both';
  status: 'active' | 'inactive' | 'pending' | 'provisioning';
  country: string;
  capabilities: string[];
  monthly_cost?: number;
  setup_cost?: number;
  ported_from?: string;
  created_at: string;
  metadata?: Record<string, any>;
}

export interface ImportConfig {
  provider: string;
  credentials: Record<string, string>;
}

export interface KasaAIPlan {
  name: string;
  price: string;
  features: string[];
  limits?: {
    numbers: number;
    inbound_minutes: number | 'unlimited';
    outbound_minutes: number | 'unlimited';
  };
}

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? API_BASE_URL 
  : API_BASE_URL;

class PhoneNumberService {
  /**
   * Fetch all phone numbers for the current user
   */
  async getPhoneNumbers(userId: string): Promise<PhoneNumber[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/phone-numbers?user_id=${userId}`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch phone numbers: ${response.statusText}`);
      }

      const data = await response.json();
      return data.numbers || [];
    } catch (error) {
      console.error('Error fetching phone numbers:', error);
      throw error;
    }
  }

  /**
   * Import numbers from Vonage
   */
  async importFromVonage(apiKey: string, apiSecret: string): Promise<PhoneNumber[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/vonage/import`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_key: apiKey,
          api_secret: apiSecret,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to import from Vonage');
      }

      const data = await response.json();
      return data.numbers || [];
    } catch (error) {
      console.error('Error importing from Vonage:', error);
      throw error;
    }
  }

  /**
   * Import numbers from Telnyx
   */
  async importFromTelnyx(apiKey: string): Promise<PhoneNumber[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/telnyx/import`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_key: apiKey,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to import from Telnyx');
      }

      const data = await response.json();
      return data.numbers || [];
    } catch (error) {
      console.error('Error importing from Telnyx:', error);
      throw error;
    }
  }

  /**
   * Import numbers from Twilio
   */
  async importFromTwilio(accountSid: string, authToken: string): Promise<PhoneNumber[]> {
    try {
      // Validate Account SID format
      if (!accountSid.startsWith('AC') || accountSid.length !== 34) {
        throw new Error('Invalid Twilio Account SID format');
      }

      const response = await fetch(`${API_BASE_URL}/api/twilio/import`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          account_sid: accountSid,
          auth_token: authToken,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to import from Twilio');
      }

      const data = await response.json();
      return data.numbers || [];
    } catch (error) {
      console.error('Error importing from Twilio:', error);
      throw error;
    }
  }

  /**
   * Configure SIP trunk
   */
  async configureSIPTrunk(serverUrl: string, username: string, password: string): Promise<any> {
    try {
      // Validate SIP server URL
      const urlPattern = /^(sip:|sips:)?([a-zA-Z0-9.-]+)(:[0-9]+)?$/;
      if (!urlPattern.test(serverUrl)) {
        throw new Error('Invalid SIP server URL format');
      }

      const response = await fetch(`${API_BASE_URL}/api/sip/configure`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          server_url: serverUrl,
          username,
          password,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to configure SIP trunk');
      }

      const data = await response.json();
      return data.trunk;
    } catch (error) {
      console.error('Error configuring SIP trunk:', error);
      throw error;
    }
  }

  /**
   * Provision a Kasa AI virtual number
   */
  async provisionKasaAINumber(plan: string, countryCode: string = 'US'): Promise<PhoneNumber> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/kasaai/provision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          plan: plan.toLowerCase(),
          country_code: countryCode,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to provision Kasa AI number');
      }

      const data = await response.json();
      return data.number;
    } catch (error) {
      console.error('Error provisioning Kasa AI number:', error);
      throw error;
    }
  }

  /**
   * Delete a phone number
   */
  async deletePhoneNumber(numberId: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/phone-numbers/${numberId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to delete phone number');
      }

      return true;
    } catch (error) {
      console.error('Error deleting phone number:', error);
      throw error;
    }
  }

  /**
   * Update phone number settings
   */
  async updatePhoneNumber(numberId: string, updates: Partial<PhoneNumber>): Promise<PhoneNumber> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/phone-numbers/${numberId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to update phone number');
      }

      const data = await response.json();
      return data.number;
    } catch (error) {
      console.error('Error updating phone number:', error);
      throw error;
    }
  }

  /**
   * Port a number from another provider
   */
  async portNumber(
    number: string, 
    fromProvider: string, 
    accountDetails: Record<string, string>
  ): Promise<PhoneNumber> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/phone-numbers/port`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          number,
          from_provider: fromProvider,
          account_details: accountDetails,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to initiate number porting');
      }

      const data = await response.json();
      return data.number;
    } catch (error) {
      console.error('Error porting number:', error);
      throw error;
    }
  }

  /**
   * Validate provider credentials
   */
  async validateCredentials(provider: string, credentials: Record<string, string>): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/${provider}/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        return false;
      }

      const data = await response.json();
      return data.valid === true;
    } catch (error) {
      console.error(`Error validating ${provider} credentials:`, error);
      return false;
    }
  }

  /**
   * Get available Kasa AI plans
   */
  getKasaAIPlans(): KasaAIPlan[] {
    return [
      {
        name: 'Starter',
        price: '$1/month',
        features: [
          '1 phone number',
          'Unlimited inbound calls',
          '100 outbound minutes',
          'Basic analytics',
          'Email support'
        ],
        limits: {
          numbers: 1,
          inbound_minutes: 'unlimited',
          outbound_minutes: 100
        }
      },
      {
        name: 'Professional',
        price: '$5/month',
        features: [
          '5 phone numbers',
          'Unlimited calls',
          'Advanced analytics',
          'Call recording',
          'Priority support',
          'API access'
        ],
        limits: {
          numbers: 5,
          inbound_minutes: 'unlimited',
          outbound_minutes: 'unlimited'
        }
      },
      {
        name: 'Enterprise',
        price: '$20/month',
        features: [
          '20 phone numbers',
          'Unlimited everything',
          'Custom integrations',
          'Priority support',
          'Dedicated account manager',
          'SLA guarantee',
          'White-label options'
        ],
        limits: {
          numbers: 20,
          inbound_minutes: 'unlimited',
          outbound_minutes: 'unlimited'
        }
      }
    ];
  }

  /**
   * Search for available numbers by area code or country
   */
  async searchAvailableNumbers(
    countryCode: string, 
    areaCode?: string, 
    pattern?: string
  ): Promise<Array<{ number: string; monthly_cost: number; setup_cost: number }>> {
    try {
      const params = new URLSearchParams({
        country: countryCode,
        ...(areaCode && { area_code: areaCode }),
        ...(pattern && { pattern }),
      });

      const response = await fetch(`${API_BASE_URL}/api/phone-numbers/search?${params}`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to search available numbers');
      }

      const data = await response.json();
      return data.numbers || [];
    } catch (error) {
      console.error('Error searching available numbers:', error);
      throw error;
    }
  }

  /**
   * Get number usage statistics
   */
  async getNumberUsageStats(numberId: string, period: string = '30d'): Promise<any> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/phone-numbers/${numberId}/usage?period=${period}`,
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch usage statistics');
      }

      const data = await response.json();
      return data.stats;
    } catch (error) {
      console.error('Error fetching usage stats:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const phoneNumberService = new PhoneNumberService();

// Export class for testing
export default PhoneNumberService;