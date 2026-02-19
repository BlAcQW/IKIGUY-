import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { paymentApi, WalletSettings, WalletPaymentMethod } from '@/lib/core-api';
import {
  Settings,
  Loader2,
  DollarSign,
  Bell,
  Zap,
  CreditCard,
  Info
} from 'lucide-react';

interface WalletSettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const WalletSettingsDialog: React.FC<WalletSettingsDialogProps> = ({
  open,
  onOpenChange
}) => {
  const [settings, setSettings] = useState<WalletSettings | null>(null);
  const [paymentMethods, setPaymentMethods] = useState<WalletPaymentMethod[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();

  // Form state
  const [autoReloadEnabled, setAutoReloadEnabled] = useState(false);
  const [autoReloadThreshold, setAutoReloadThreshold] = useState('10.00');
  const [autoReloadAmount, setAutoReloadAmount] = useState('50.00');
  const [autoReloadPaymentMethodId, setAutoReloadPaymentMethodId] = useState('');
  const [lowBalanceAlertEnabled, setLowBalanceAlertEnabled] = useState(true);
  const [lowBalanceThreshold, setLowBalanceThreshold] = useState('20.00');

  useEffect(() => {
    if (open) {
      fetchSettings();
      fetchPaymentMethods();
    }
  }, [open]);

  const fetchSettings = async () => {
    setIsLoading(true);
    try {
      const data = await paymentApi.getWalletSettings();
      setSettings(data);

      // Populate form
      setAutoReloadEnabled(data.auto_reload_enabled);
      setAutoReloadThreshold(data.auto_reload_threshold.toFixed(2));
      setAutoReloadAmount(data.auto_reload_amount.toFixed(2));
      setAutoReloadPaymentMethodId(data.auto_reload_payment_method_id || '');
      setLowBalanceAlertEnabled(data.low_balance_alert_enabled);
      setLowBalanceThreshold(data.low_balance_threshold.toFixed(2));
    } catch (error) {
      console.error('Failed to fetch wallet settings:', error);
      toast({
        title: 'Error loading settings',
        description: 'Could not load wallet settings',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const fetchPaymentMethods = async () => {
    try {
      const methods = await paymentApi.getPaymentMethods();
      setPaymentMethods(methods.filter(m => m.is_active && m.is_verified));
    } catch (error) {
      console.error('Failed to fetch payment methods:', error);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const updates = {
        auto_reload_enabled: autoReloadEnabled,
        auto_reload_threshold: parseFloat(autoReloadThreshold),
        auto_reload_amount: parseFloat(autoReloadAmount),
        auto_reload_payment_method_id: autoReloadPaymentMethodId || undefined,
        low_balance_alert_enabled: lowBalanceAlertEnabled,
        low_balance_threshold: parseFloat(lowBalanceThreshold)
      };

      await paymentApi.updateWalletSettings(updates);

      toast({
        title: 'Settings saved',
        description: 'Your wallet settings have been updated successfully',
        variant: 'default'
      });

      onOpenChange(false);
    } catch (error: any) {
      console.error('Failed to update wallet settings:', error);
      toast({
        title: 'Error saving settings',
        description: error.message || 'Could not save wallet settings',
        variant: 'destructive'
      });
    } finally {
      setIsSaving(false);
    }
  };

  const formatCurrency = (amount: string) => {
    const num = parseFloat(amount);
    if (isNaN(num)) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(num);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md bg-gradient-card border-accent/20">
        <DialogHeader>
          <DialogTitle className="text-xl font-playfair text-accent flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Wallet Settings
          </DialogTitle>
          <DialogDescription className="text-gray-600">
            Configure auto-reload and balance alerts
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Auto-Reload Section */}
            <div className="space-y-4 border-b pb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Zap className="h-5 w-5 text-purple-600" />
                  <Label htmlFor="auto-reload" className="text-base font-semibold">
                    Auto-Reload
                  </Label>
                </div>
                <Switch
                  id="auto-reload"
                  checked={autoReloadEnabled}
                  onCheckedChange={setAutoReloadEnabled}
                />
              </div>

              {autoReloadEnabled && (
                <div className="space-y-3 pl-7">
                  <div>
                    <Label htmlFor="threshold" className="text-sm">
                      Reload when balance drops below
                    </Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="threshold"
                        type="number"
                        step="0.01"
                        min="0"
                        value={autoReloadThreshold}
                        onChange={(e) => setAutoReloadThreshold(e.target.value)}
                        className="pl-9"
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="reload-amount" className="text-sm">
                      Reload amount
                    </Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="reload-amount"
                        type="number"
                        step="0.01"
                        min="0"
                        value={autoReloadAmount}
                        onChange={(e) => setAutoReloadAmount(e.target.value)}
                        className="pl-9"
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="payment-method" className="text-sm">
                      Payment method
                    </Label>
                    {paymentMethods.length === 0 ? (
                      <div className="mt-1 border rounded-lg p-3 bg-yellow-50 border-yellow-200">
                        <p className="text-sm text-yellow-800">
                          No payment methods available. Add a payment method by making a top-up first.
                        </p>
                      </div>
                    ) : (
                      <Select
                        value={autoReloadPaymentMethodId}
                        onValueChange={setAutoReloadPaymentMethodId}
                      >
                        <SelectTrigger className="mt-1">
                          <SelectValue placeholder="Select payment method" />
                        </SelectTrigger>
                        <SelectContent>
                          {paymentMethods.map((method) => (
                            <SelectItem key={method.id} value={method.id}>
                              <div className="flex items-center gap-2">
                                <CreditCard className="h-4 w-4" />
                                {method.display_name}
                                {method.is_default && (
                                  <span className="text-xs text-gray-500">(Default)</span>
                                )}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  </div>

                  <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
                    <div className="flex gap-2">
                      <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                      <p className="text-xs text-blue-800">
                        When your balance drops below {formatCurrency(autoReloadThreshold)},
                        we'll automatically add {formatCurrency(autoReloadAmount)} to your wallet
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Low Balance Alerts Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bell className="h-5 w-5 text-orange-600" />
                  <Label htmlFor="low-balance-alert" className="text-base font-semibold">
                    Low Balance Alerts
                  </Label>
                </div>
                <Switch
                  id="low-balance-alert"
                  checked={lowBalanceAlertEnabled}
                  onCheckedChange={setLowBalanceAlertEnabled}
                />
              </div>

              {lowBalanceAlertEnabled && (
                <div className="pl-7">
                  <Label htmlFor="alert-threshold" className="text-sm">
                    Alert when balance drops below
                  </Label>
                  <div className="relative mt-1">
                    <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="alert-threshold"
                      type="number"
                      step="0.01"
                      min="0"
                      value={lowBalanceThreshold}
                      onChange={(e) => setLowBalanceThreshold(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    We'll notify you when your balance is running low
                  </p>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 pt-4">
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}
                className="flex-1"
                disabled={isSaving}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                className="flex-1 bg-gradient-premium"
                disabled={isSaving}
              >
                {isSaving ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  'Save Settings'
                )}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default WalletSettingsDialog;
