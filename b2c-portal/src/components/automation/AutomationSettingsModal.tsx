/**
 * Automation Settings Modal
 *
 * Allows universal_admin users to configure automation-specific settings
 * including custom per-minute cost rates for billing.
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Settings,
  DollarSign,
  Loader2,
  AlertTriangle,
  Save,
  Shield
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { getAuthHeaders } from '@/lib/auth-utils';
import { API_BASE_URL } from '@/config/api-config';

interface AutomationSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  automationId: string;
  automationName: string;
  assistantId?: string;
}

interface CostSettings {
  rate_per_call: number | null;
  currency: string;
  currency_symbol: string;
}

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'GHS', symbol: 'GH₵', name: 'Ghana Cedi' },
  { code: 'NGN', symbol: '₦', name: 'Nigerian Naira' },
  { code: 'KES', symbol: 'KSh', name: 'Kenyan Shilling' },
  { code: 'ZAR', symbol: 'R', name: 'South African Rand' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
];

export const AutomationSettingsModal: React.FC<AutomationSettingsModalProps> = ({
  isOpen,
  onClose,
  automationId,
  automationName,
  assistantId
}) => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [costSettings, setCostSettings] = useState<CostSettings>({
    rate_per_call: null,
    currency: 'GHS',
    currency_symbol: 'GH₵'
  });

  // Fetch current settings
  const fetchSettings = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/api/automation-settings/${automationId}`,
        {
          method: 'GET',
          headers: await getAuthHeaders()
        }
      );

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data?.cost_settings) {
          setCostSettings({
            rate_per_call: data.data.cost_settings.rate_per_call || null,
            currency: data.data.cost_settings.currency || 'GHS',
            currency_symbol: data.data.cost_settings.currency_symbol || 'GH₵'
          });
        }
      } else if (response.status !== 404) {
        throw new Error('Failed to load settings');
      }
    } catch (err: any) {
      console.error('Error loading settings:', err);
      // Don't show error for missing settings - they just haven't been set yet
    } finally {
      setLoading(false);
    }
  };

  // Save settings
  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/api/automation-settings/${automationId}`,
        {
          method: 'PUT',
          headers: await getAuthHeaders(),
          body: JSON.stringify({
            cost_settings: {
              rate_per_call: costSettings.rate_per_call,
              currency: costSettings.currency,
              currency_symbol: costSettings.currency_symbol
            }
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to save settings');
      }

      toast({
        title: 'Settings saved',
        description: 'Automation cost settings have been updated'
      });

      onClose();
    } catch (err: any) {
      setError(err.message);
      toast({
        title: 'Error saving settings',
        description: err.message,
        variant: 'destructive'
      });
    } finally {
      setSaving(false);
    }
  };

  // Handle currency change
  const handleCurrencyChange = (currencyCode: string) => {
    const currency = CURRENCIES.find(c => c.code === currencyCode);
    if (currency) {
      setCostSettings(prev => ({
        ...prev,
        currency: currency.code,
        currency_symbol: currency.symbol
      }));
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchSettings();
    }
  }, [isOpen, automationId]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-orange-500" />
            <Settings className="h-5 w-5" />
            Automation Settings
          </DialogTitle>
          <DialogDescription>
            Configure settings for: {automationName}
            {assistantId && (
              <span className="block text-xs mt-1">
                Assistant ID: {assistantId}
              </span>
            )}
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
          </div>
        ) : (
          <div className="space-y-6 py-4">
            {/* Cost Settings */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  Billing Cost Rate
                </CardTitle>
                <CardDescription className="text-xs">
                  Set a custom per-call rate for billing this automation's calls.
                  Leave empty to use VAPI's default cost.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="currency">Currency</Label>
                    <Select
                      value={costSettings.currency}
                      onValueChange={handleCurrencyChange}
                    >
                      <SelectTrigger id="currency">
                        <SelectValue placeholder="Select currency" />
                      </SelectTrigger>
                      <SelectContent>
                        {CURRENCIES.map(currency => (
                          <SelectItem key={currency.code} value={currency.code}>
                            {currency.symbol} {currency.code} - {currency.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="rate">Rate per Call</Label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                        {costSettings.currency_symbol}
                      </span>
                      <Input
                        id="rate"
                        type="number"
                        step="0.01"
                        min="0"
                        placeholder="e.g., 1.20"
                        className="pl-10"
                        value={costSettings.rate_per_call ?? ''}
                        onChange={(e) => setCostSettings(prev => ({
                          ...prev,
                          rate_per_call: e.target.value ? parseFloat(e.target.value) : null
                        }))}
                      />
                    </div>
                  </div>
                </div>

                {costSettings.rate_per_call && (
                  <div className="p-3 bg-green-50 dark:bg-green-950/20 rounded-lg text-sm">
                    <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
                      <DollarSign className="h-4 w-4" />
                      <span>
                        Calls will be billed at{' '}
                        <strong>
                          {costSettings.currency_symbol}{costSettings.rate_per_call}
                        </strong>{' '}
                        per call ({costSettings.currency})
                      </span>
                    </div>
                  </div>
                )}

                {!costSettings.rate_per_call && (
                  <div className="p-3 bg-gray-50 dark:bg-gray-950/20 rounded-lg text-sm text-muted-foreground">
                    No custom rate set. Using VAPI's default cost calculation.
                  </div>
                )}
              </CardContent>
            </Card>

            {error && (
              <div className="p-3 bg-red-50 dark:bg-red-950/20 rounded-lg text-sm text-red-600 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                {error}
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving || loading}>
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Settings
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default AutomationSettingsModal;
