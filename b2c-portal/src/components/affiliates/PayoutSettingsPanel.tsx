import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { affiliateApi, AffiliateProfile } from '@/lib/core-api';
import { Calendar, DollarSign, Clock, Save, Info } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface PayoutSettingsPanelProps {
  profile: AffiliateProfile;
  onUpdate: () => void;
}

const PayoutSettingsPanel: React.FC<PayoutSettingsPanelProps> = ({ profile, onUpdate }) => {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [settings, setSettings] = useState({
    auto_payout_enabled: profile.auto_payout_enabled || false,
    auto_payout_schedule: profile.auto_payout_schedule || 'monthly',
    auto_payout_day: profile.auto_payout_day || 15,
    payout_threshold: profile.payout_threshold || 20,
    preferred_payout_method: profile.preferred_payout_method || 'wallet_credit'
  });

  // Get day options based on schedule type
  const getDayOptions = () => {
    if (settings.auto_payout_schedule === 'weekly') {
      return [
        { value: 0, label: 'Monday' },
        { value: 1, label: 'Tuesday' },
        { value: 2, label: 'Wednesday' },
        { value: 3, label: 'Thursday' },
        { value: 4, label: 'Friday' },
        { value: 5, label: 'Saturday' },
        { value: 6, label: 'Sunday' }
      ];
    } else {
      // Monthly - days 1-31
      return Array.from({ length: 31 }, (_, i) => ({
        value: i + 1,
        label: `Day ${i + 1}`
      }));
    }
  };

  const handleSave = async () => {
    setIsSubmitting(true);

    try {
      await affiliateApi.updateProfile({
        auto_payout_enabled: settings.auto_payout_enabled,
        auto_payout_schedule: settings.auto_payout_schedule,
        auto_payout_day: settings.auto_payout_day,
        payout_threshold: settings.payout_threshold,
        preferred_payout_method: settings.preferred_payout_method
      });

      toast({
        title: 'Settings Saved',
        description: 'Your payout settings have been updated successfully'
      });

      onUpdate();
    } catch (error: any) {
      toast({
        title: 'Error Saving Settings',
        description: error.message || 'Failed to update settings',
        variant: 'destructive'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Payout Settings</h2>
        <p className="text-muted-foreground">Configure your automated payout preferences</p>
      </div>

      {/* Automated Payouts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Automated Payouts
          </CardTitle>
          <CardDescription>
            Automatically process payouts when you reach your threshold
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Enable/Disable Toggle */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="auto-payout">Enable Automated Payouts</Label>
              <p className="text-sm text-muted-foreground">
                Automatically create payout requests based on your schedule
              </p>
            </div>
            <Switch
              id="auto-payout"
              checked={settings.auto_payout_enabled}
              onCheckedChange={(checked) =>
                setSettings(prev => ({ ...prev, auto_payout_enabled: checked }))
              }
            />
          </div>

          {settings.auto_payout_enabled && (
            <>
              {/* Schedule Type */}
              <div className="space-y-3">
                <Label>Payout Schedule</Label>
                <RadioGroup
                  value={settings.auto_payout_schedule}
                  onValueChange={(value) => {
                    setSettings(prev => ({
                      ...prev,
                      auto_payout_schedule: value,
                      auto_payout_day: value === 'weekly' ? 0 : 15 // Reset to default
                    }));
                  }}
                >
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="weekly" id="weekly" />
                    <Label htmlFor="weekly" className="font-normal cursor-pointer">
                      Weekly - Process payouts every week
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="monthly" id="monthly" />
                    <Label htmlFor="monthly" className="font-normal cursor-pointer">
                      Monthly - Process payouts once per month
                    </Label>
                  </div>
                </RadioGroup>
              </div>

              {/* Day Selection */}
              <div className="space-y-3">
                <Label htmlFor="payout-day">
                  {settings.auto_payout_schedule === 'weekly' ? 'Day of Week' : 'Day of Month'}
                </Label>
                <Select
                  value={settings.auto_payout_day.toString()}
                  onValueChange={(value) =>
                    setSettings(prev => ({ ...prev, auto_payout_day: parseInt(value) }))
                  }
                >
                  <SelectTrigger id="payout-day">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {getDayOptions().map(option => (
                      <SelectItem key={option.value} value={option.value.toString()}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  {settings.auto_payout_schedule === 'weekly'
                    ? 'Payouts will be processed on this day each week'
                    : 'Payouts will be processed on this day each month (if balance meets threshold)'}
                </p>
              </div>

              {/* Info Alert */}
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  Automated payouts run daily at 2:00 AM UTC. If your balance meets the threshold on your
                  selected day, a payout request will be created automatically.
                </AlertDescription>
              </Alert>
            </>
          )}
        </CardContent>
      </Card>

      {/* Payout Threshold */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5" />
            Payout Threshold
          </CardTitle>
          <CardDescription>
            Minimum balance required to request a payout
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="threshold">Minimum Payout Amount ($)</Label>
            <Input
              id="threshold"
              type="number"
              min="20"
              step="1"
              value={settings.payout_threshold}
              onChange={(e) =>
                setSettings(prev => ({ ...prev, payout_threshold: parseFloat(e.target.value) }))
              }
            />
            <p className="text-sm text-muted-foreground mt-1">
              Minimum: $20 USD. Payouts will only process when your pending commissions reach this amount.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Preferred Payout Method */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Preferred Payout Method
          </CardTitle>
          <CardDescription>
            Your default payment method for automated payouts
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="payout-method">Payment Method</Label>
            <Select
              value={settings.preferred_payout_method}
              onValueChange={(value) =>
                setSettings(prev => ({ ...prev, preferred_payout_method: value }))
              }
            >
              <SelectTrigger id="payout-method">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="wallet_credit">
                  Wallet Credit (Free)
                </SelectItem>
                <SelectItem value="mobile_money">
                  Mobile Money (2% fee, min $1.00)
                </SelectItem>
                <SelectItem value="bank_transfer">
                  Bank Transfer (1.5% fee, min $1.00)
                </SelectItem>
                <SelectItem value="paypal">
                  PayPal (2.5% fee, min $1.00)
                </SelectItem>
              </SelectContent>
            </Select>

            {/* Processing Fees Info */}
            <Alert className="mt-4">
              <Info className="h-4 w-4" />
              <AlertDescription>
                <strong>Processing Fees:</strong>
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li>Wallet Credit: No fees (instant)</li>
                  <li>Mobile Money: 2% (minimum $1.00)</li>
                  <li>Bank Transfer: 1.5% (minimum $1.00)</li>
                  <li>PayPal: 2.5% (minimum $1.00)</li>
                </ul>
              </AlertDescription>
            </Alert>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          disabled={isSubmitting}
          className="min-w-[150px]"
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
              Saving...
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              Save Settings
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

export default PayoutSettingsPanel;
