/**
 * Import Phone Numbers Modal
 * Import from Twilio, Vonage, Telnyx, or configure SIP Trunk
 * Following Vapi's two-panel layout
 */

import React, { useState } from 'react';
import { X, AlertCircle, ExternalLink } from 'lucide-react';
import { ImportRequest, ProviderConfig } from '@/lib/phone-api-client';

interface ImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImport: (request: ImportRequest) => Promise<void>;
}

type ProviderType = 'twilio' | 'vonage' | 'telnyx' | 'vapi' | 'sip_trunk';

const PROVIDERS = [
  {
    id: 'vapi' as ProviderType,
    name: 'VAPI',
    icon: '📱',
    description: 'Import your VAPI BYO phone numbers',
    docsUrl: 'https://docs.vapi.ai',
    fields: [
      {
        key: 'phone_id',
        label: 'VAPI Phone ID',
        type: 'text',
        placeholder: '6d828206-4eba-4668-9bb1-8c2f8045b682',
        helpText: 'Found in VAPI Dashboard > Phone Numbers',
        required: true,
        validation: (value: string) => value.length >= 32
      }
    ]
  },
  {
    id: 'twilio' as ProviderType,
    name: 'Twilio',
    icon: '☁️',
    description: 'Import existing Twilio numbers',
    docsUrl: 'https://www.twilio.com/docs/iam/keys/api-key',
    fields: [
      {
        key: 'account_sid',
        label: 'Account SID',
        type: 'text',
        placeholder: 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
        helpText: 'Found in your Twilio Console Dashboard',
        required: true,
        validation: (value: string) => value.startsWith('AC') && value.length === 34
      },
      {
        key: 'auth_token',
        label: 'Auth Token',
        type: 'password',
        placeholder: 'Your auth token',
        helpText: 'Click "Show" in your Twilio Console to reveal',
        required: true,
        validation: (value: string) => value.length === 32
      }
    ]
  },
  {
    id: 'vonage' as ProviderType,
    name: 'Vonage',
    icon: '📞',
    description: 'Import existing Vonage numbers',
    docsUrl: 'https://developer.vonage.com/en/getting-started/concepts/authentication',
    fields: [
      {
        key: 'api_key',
        label: 'API Key',
        type: 'text',
        placeholder: 'abcd1234',
        helpText: 'Found in your Vonage API Dashboard',
        required: true,
        validation: (value: string) => value.length >= 8
      },
      {
        key: 'api_secret',
        label: 'API Secret',
        type: 'password',
        placeholder: 'Your API secret',
        helpText: 'Keep this secure - never share publicly',
        required: true,
        validation: (value: string) => value.length >= 16
      }
    ]
  },
  {
    id: 'telnyx' as ProviderType,
    name: 'Telnyx',
    icon: '🌐',
    description: 'Import existing Telnyx numbers',
    docsUrl: 'https://developers.telnyx.com/docs/v2/development/authentication',
    fields: [
      {
        key: 'api_key',
        label: 'API Key',
        type: 'text',
        placeholder: 'KEY...',
        helpText: 'V2 API Key from your Telnyx Portal',
        required: true,
        validation: (value: string) => value.startsWith('KEY') && value.length > 20
      }
    ]
  },
  {
    id: 'sip_trunk' as ProviderType,
    name: 'SIP Trunk',
    icon: '🔌',
    description: 'Configure your own SIP trunk',
    docsUrl: null,
    fields: [
      {
        key: 'sip_server',
        label: 'SIP Server',
        type: 'text',
        placeholder: 'sip.example.com:5060',
        helpText: 'Hostname or IP address with optional port',
        required: true,
        validation: (value: string) => value.includes('.') || value.includes(':')
      },
      {
        key: 'sip_username',
        label: 'Username',
        type: 'text',
        placeholder: 'Your username',
        helpText: 'SIP authentication username',
        required: true,
        validation: (value: string) => value.length >= 3
      },
      {
        key: 'sip_password',
        label: 'Password',
        type: 'password',
        placeholder: 'Your password',
        helpText: 'SIP authentication password',
        required: true,
        validation: (value: string) => value.length >= 6
      }
    ]
  }
];

export const ImportModal: React.FC<ImportModalProps> = ({ isOpen, onClose, onImport }) => {
  const [selectedProvider, setSelectedProvider] = useState<ProviderType | null>(null);
  const [config, setConfig] = useState<Record<string, string>>({});
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  if (!isOpen) return null;

  const selectedProviderInfo = PROVIDERS.find(p => p.id === selectedProvider);

  const handleImport = async () => {
    if (!selectedProvider) return;

    setIsImporting(true);
    setError(null);

    try {
      const providerConfig: ProviderConfig = {
        provider: selectedProvider,
        ...config
      };

      await onImport({
        provider: selectedProvider as any,
        config: providerConfig
      });

      // Reset and close
      setSelectedProvider(null);
      setConfig({});
      setFieldErrors({});
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to import phone numbers');
    } finally {
      setIsImporting(false);
    }
  };

  const handleConfigChange = (key: string, value: string) => {
    setConfig(prev => ({ ...prev, [key]: value }));

    // Validate field
    const field = selectedProviderInfo?.fields.find(f => f.key === key);
    if (field && field.validation) {
      if (!field.validation(value)) {
        setFieldErrors(prev => ({
          ...prev,
          [key]: `Invalid ${field.label.toLowerCase()} format`
        }));
      } else {
        setFieldErrors(prev => {
          const newErrors = { ...prev };
          delete newErrors[key];
          return newErrors;
        });
      }
    }
  };

  const isConfigComplete = () => {
    if (!selectedProviderInfo) return false;

    // Check all required fields are filled
    const allFieldsFilled = selectedProviderInfo.fields.every(field =>
      field.required ? config[field.key]?.trim() : true
    );

    // Check no validation errors
    const noErrors = Object.keys(fieldErrors).length === 0;

    // Validate all fields that have validation
    const allValid = selectedProviderInfo.fields.every(field => {
      if (!field.validation || !config[field.key]) return true;
      return field.validation(config[field.key]);
    });

    return allFieldsFilled && noErrors && allValid;
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-card border border-border rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h2 className="text-xl font-semibold">Import Phone Numbers</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-accent rounded-md transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Two-panel layout (Vapi-style) */}
        <div className="flex-1 overflow-auto flex">
          {/* Left Panel - Provider Selection */}
          <div className="w-1/3 border-r border-border p-4 bg-muted/20">
            <h3 className="text-sm font-medium text-muted-foreground mb-3">Phone Number Options</h3>
            <div className="space-y-2">
              {PROVIDERS.map((provider) => (
                <button
                  key={provider.id}
                  onClick={() => {
                    setSelectedProvider(provider.id);
                    setConfig({});
                    setError(null);
                    setFieldErrors({});
                  }}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    selectedProvider === provider.id
                      ? 'border-primary bg-primary/10'
                      : 'border-border hover:border-muted-foreground bg-background'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-2xl flex-shrink-0">{provider.icon}</span>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium">{provider.name}</h4>
                      <p className="text-xs text-muted-foreground mt-0.5">{provider.description}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Right Panel - Configuration */}
          <div className="flex-1 p-6">
            {!selectedProvider ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center text-muted-foreground">
                  <p className="text-sm">Select a provider to get started</p>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-lg font-semibold">
                      {selectedProviderInfo?.name} Configuration
                    </h3>
                    {selectedProviderInfo?.docsUrl && (
                      <a
                        href={selectedProviderInfo.docsUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline flex items-center gap-1"
                      >
                        <ExternalLink className="h-3 w-3" />
                        View Docs
                      </a>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Enter your credentials to import phone numbers
                  </p>
                </div>

                {error && (
                  <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg flex items-start gap-2">
                    <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-destructive">{error}</p>
                  </div>
                )}

                <div className="space-y-4">
                  {selectedProviderInfo?.fields.map((field: any) => (
                    <div key={field.key}>
                      <label className="block text-sm font-medium mb-1.5">
                        {field.label}
                        {field.required && <span className="text-destructive ml-1">*</span>}
                      </label>
                      <input
                        type={field.type}
                        placeholder={field.placeholder}
                        value={config[field.key] || ''}
                        onChange={(e) => handleConfigChange(field.key, e.target.value)}
                        className={`w-full px-3 py-2 bg-background border rounded-md focus:ring-1 outline-none transition-colors ${
                          fieldErrors[field.key]
                            ? 'border-destructive focus:border-destructive focus:ring-destructive/20'
                            : 'border-border focus:border-primary focus:ring-primary/20'
                        }`}
                      />
                      {field.helpText && !fieldErrors[field.key] && (
                        <p className="mt-1 text-xs text-muted-foreground">{field.helpText}</p>
                      )}
                      {fieldErrors[field.key] && (
                        <p className="mt-1 text-xs text-destructive flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          {fieldErrors[field.key]}
                        </p>
                      )}
                    </div>
                  ))}
                </div>

                {selectedProvider !== 'sip_trunk' && (
                  <div className="p-4 bg-primary/10 border border-primary/20 rounded-lg">
                    <p className="text-sm text-primary">
                      <strong>Note:</strong> Only active numbers from your {selectedProviderInfo?.name} account
                      will be imported. Billing will continue through {selectedProviderInfo?.name}.
                    </p>
                  </div>
                )}
              </div>
            )}
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
            onClick={handleImport}
            disabled={!isConfigComplete() || isImporting}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isImporting ? 'Importing...' : 'Import Numbers'}
          </button>
        </div>
      </div>
    </div>
  );
};
