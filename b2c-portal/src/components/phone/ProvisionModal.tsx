/**
 * Provision Kasa AI Phone Number Modal
 * Plan selection and phone number provisioning
 */

import React, { useState } from 'react';
import { X, Check, AlertCircle, Info } from 'lucide-react';
import { ProvisionRequest } from '@/lib/phone-api-client';

interface ProvisionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProvision: (request: ProvisionRequest) => Promise<void>;
}

const PLANS = [
  {
    id: 'starter',
    name: 'Starter',
    price: '$1',
    period: 'month',
    features: [
      '1 phone number',
      'Unlimited inbound calls',
      '100 outbound minutes',
      'Basic analytics',
      'Email support'
    ],
    recommended: false
  },
  {
    id: 'professional',
    name: 'Professional',
    price: '$5',
    period: 'month',
    features: [
      '5 phone numbers',
      'Unlimited calls (in/out)',
      'Advanced analytics',
      'Call recording',
      'Priority support',
      'Custom integrations'
    ],
    recommended: true
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: '$20',
    period: 'month',
    features: [
      '20 phone numbers',
      'Unlimited everything',
      'White-label options',
      'Custom integrations',
      'Dedicated support',
      'SLA guarantee'
    ],
    recommended: false
  }
];

const COUNTRIES = [
  { code: '+1', name: 'United States', flag: '🇺🇸' },
  { code: '+44', name: 'United Kingdom', flag: '🇬🇧' },
  { code: '+233', name: 'Ghana', flag: '🇬🇭' },
  { code: '+234', name: 'Nigeria', flag: '🇳🇬' },
  { code: '+254', name: 'Kenya', flag: '🇰🇪' }
];

const SIP_PROVIDERS = [
  {
    id: 'freeswitch',
    name: 'FreeSWITCH',
    icon: '🚀',
    description: 'Modern SIP server with dynamic provisioning',
    features: ['Dynamic user creation', 'No restarts needed', 'REST API'],
    recommended: true
  },
  {
    id: 'asterisk',
    name: 'Asterisk',
    icon: '📞',
    description: 'Traditional PBX system',
    features: ['PJSIP support', 'Mature & stable', 'Wide adoption'],
    recommended: false
  }
];

export const ProvisionModal: React.FC<ProvisionModalProps> = ({ isOpen, onClose, onProvision }) => {
  const [selectedPlan, setSelectedPlan] = useState<string>('professional');
  const [selectedCountry, setSelectedCountry] = useState<string>('+1');
  const [selectedProvider, setSelectedProvider] = useState<string>('freeswitch');
  const [areaCode, setAreaCode] = useState<string>('');
  const [isProvisioning, setIsProvisioning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleProvision = async () => {
    setIsProvisioning(true);
    setError(null);

    try {
      await onProvision({
        provider: 'kasaai',
        country_code: selectedCountry,
        area_code: areaCode || undefined,
        capabilities: ['voice', 'sms', 'mms', 'fax'],
        plan: selectedPlan as 'starter' | 'professional' | 'enterprise',
        sip_provider: selectedProvider as 'freeswitch' | 'asterisk'
      });

      // Reset and close
      setSelectedPlan('professional');
      setSelectedCountry('+1');
      setSelectedProvider('freeswitch');
      setAreaCode('');
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to provision phone number');
    } finally {
      setIsProvisioning(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-card border border-border rounded-lg w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">Get Kasa AI Phone Number</h2>
            <p className="text-sm text-muted-foreground mt-0.5">
              Instant provisioning • Global coverage • Low cost
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-accent rounded-md transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6 space-y-6">
          {error && (
            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0 mt-0.5" />
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          {/* Plan Selection */}
          <div>
            <h3 className="text-base font-semibold mb-3">Select Plan</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {PLANS.map((plan) => (
                <button
                  key={plan.id}
                  onClick={() => setSelectedPlan(plan.id)}
                  className={`relative p-4 border rounded-lg text-left transition-all ${
                    selectedPlan === plan.id
                      ? 'border-primary bg-primary/5 shadow-sm'
                      : 'border-border hover:border-muted-foreground'
                  }`}
                >
                  {plan.recommended && (
                    <div className="absolute -top-2 left-1/2 -translate-x-1/2">
                      <span className="px-2 py-0.5 bg-primary text-primary-foreground text-xs font-medium rounded-full">
                        Recommended
                      </span>
                    </div>
                  )}

                  <div className="mb-3">
                    <h4 className="text-base font-semibold">{plan.name}</h4>
                    <div className="mt-1">
                      <span className="text-2xl font-bold">{plan.price}</span>
                      <span className="text-sm text-muted-foreground">/{plan.period}</span>
                    </div>
                  </div>

                  <ul className="space-y-2">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-start gap-2 text-xs">
                        <Check className="h-3 w-3 text-green-500 flex-shrink-0 mt-0.5" />
                        <span className="text-muted-foreground">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </button>
              ))}
            </div>
          </div>

          {/* SIP Provider Selection */}
          <div>
            <h3 className="text-base font-semibold mb-3">Select SIP Provider</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {SIP_PROVIDERS.map((provider) => (
                <button
                  key={provider.id}
                  onClick={() => setSelectedProvider(provider.id)}
                  className={`relative p-4 border rounded-lg text-left transition-all ${
                    selectedProvider === provider.id
                      ? 'border-primary bg-primary/5 shadow-sm'
                      : 'border-border hover:border-muted-foreground'
                  }`}
                >
                  {provider.recommended && (
                    <div className="absolute -top-2 left-1/2 -translate-x-1/2">
                      <span className="px-2 py-0.5 bg-green-500 text-white text-xs font-medium rounded-full">
                        Recommended
                      </span>
                    </div>
                  )}

                  <div className="flex items-start gap-3 mb-3">
                    <span className="text-2xl">{provider.icon}</span>
                    <div>
                      <h4 className="text-base font-semibold">{provider.name}</h4>
                      <p className="text-xs text-muted-foreground mt-0.5">{provider.description}</p>
                    </div>
                  </div>

                  <ul className="space-y-1">
                    {provider.features.map((feature, index) => (
                      <li key={index} className="flex items-start gap-2 text-xs">
                        <Check className="h-3 w-3 text-green-500 flex-shrink-0 mt-0.5" />
                        <span className="text-muted-foreground">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </button>
              ))}
            </div>
          </div>

          {/* Country Selection */}
          <div>
            <h3 className="text-base font-semibold mb-3">Select Country</h3>
            <select
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:border-primary focus:ring-1 focus:ring-primary outline-none"
            >
              {COUNTRIES.map((country) => (
                <option key={country.code} value={country.code}>
                  {country.flag} {country.name} ({country.code})
                </option>
              ))}
            </select>
          </div>

          {/* Area Code (Optional) */}
          <div>
            <label className="block text-sm font-medium mb-1.5">
              Area Code (Optional)
            </label>
            <input
              type="text"
              placeholder={selectedCountry === '+1' ? 'e.g. 555, 415, 212' : 'e.g. 20, 24, 50'}
              value={areaCode}
              onChange={(e) => setAreaCode(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:border-primary focus:ring-1 focus:ring-primary outline-none"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Leave empty for random selection
            </p>
          </div>

          {/* Info Box */}
          <div className="p-4 bg-primary/10 border border-primary/20 rounded-lg">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 text-primary flex-shrink-0" />
              <div className="text-sm">
                <p className="font-medium text-primary mb-1">What's included:</p>
                <ul className="space-y-1 text-primary/90">
                  <li>• Instant activation (no waiting)</li>
                  <li>• Powered by Asterisk/FreeSWITCH</li>
                  <li>• Full SIP trunk access</li>
                  <li>• WebRTC & voice agent integration</li>
                  <li>• Cancel anytime</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-border flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-border rounded-md hover:bg-accent transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleProvision}
            disabled={isProvisioning}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isProvisioning ? 'Provisioning...' : 'Get Phone Number'}
          </button>
        </div>
      </div>
    </div>
  );
};
