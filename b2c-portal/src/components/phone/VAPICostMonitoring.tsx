/**
 * VAPI Cost Monitoring Component
 * Displays phone numbers with credit balance, usage stats, and cost tracking
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Phone,
  Plus,
  TrendingUp,
  Clock,
  AlertCircle,
  DollarSign,
  RefreshCw
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import type { PhoneNumber, CostSummary } from '@/lib/phone-api-client';
import { getCostSummary, sendSlackLowCreditAlert } from '@/lib/phone-api-client';

// Low credit threshold in GHC
const LOW_CREDIT_THRESHOLD = 500;

interface VAPICostMonitoringProps {
  onAddCredit: (phone: PhoneNumber) => void;
  onViewDetails: (phone: PhoneNumber) => void;
  refreshTrigger?: number; // Add refresh trigger prop
}

export const VAPICostMonitoring: React.FC<VAPICostMonitoringProps> = ({
  onAddCredit,
  onViewDetails,
  refreshTrigger
}) => {
  const { toast } = useToast();
  const [costSummary, setCostSummary] = useState<CostSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Track which phones have already had Slack alerts sent this session
  // Using a ref to persist across re-renders without triggering updates
  const alertedPhonesRef = useRef<Set<string>>(new Set());

  /**
   * Check for low credit phones and send Slack alerts
   * Only alerts once per phone per session to avoid spam
   */
  const checkAndAlertLowCredit = async (phones: CostSummary['phones']) => {
    for (const phone of phones) {
      // Check if credit is below threshold (500 GHC)
      if (phone.credit_balance < LOW_CREDIT_THRESHOLD) {
        // Only send alert if we haven't already alerted for this phone this session
        if (!alertedPhonesRef.current.has(phone.id)) {
          try {
            const remainingMinutes = phone.cost_per_minute > 0
              ? phone.credit_balance / phone.cost_per_minute
              : 0;

            const result = await sendSlackLowCreditAlert({
              phone_number: phone.number,
              current_balance: phone.credit_balance,
              threshold: LOW_CREDIT_THRESHOLD,
              currency: phone.currency,
              remaining_minutes: remainingMinutes
            });

            // Mark as alerted regardless of outcome to prevent spam
            alertedPhonesRef.current.add(phone.id);

            if (result.success && !result.skipped) {
              console.log(`[VAPICostMonitoring] Slack alert sent for ${phone.number}: balance ${phone.credit_balance} ${phone.currency}`);
            }
          } catch (error) {
            console.error(`[VAPICostMonitoring] Failed to send Slack alert for ${phone.number}:`, error);
            // Still mark as alerted to prevent repeated failures
            alertedPhonesRef.current.add(phone.id);
          }
        }
      }
    }
  };

  const loadCostSummary = async () => {
    try {
      setIsLoading(true);
      const summary = await getCostSummary();
      setCostSummary(summary);

      // Check for low credit phones and send Slack alerts
      if (summary.phones && summary.phones.length > 0) {
        await checkAndAlertLowCredit(summary.phones);
      }
    } catch (error: any) {
      toast({
        title: 'Error loading cost summary',
        description: error.message,
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCostSummary();
  }, [refreshTrigger]); // Reload when refreshTrigger changes

  // Auto-refresh every 10 seconds for real-time updates during campaigns
  useEffect(() => {
    const interval = setInterval(() => {
      loadCostSummary();
    }, 10000); // 10 seconds

    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (amount: number, currency: string) => {
    return `${currency} ${amount.toFixed(2)}`;
  };

  const getBalanceColor = (phone: any) => {
    if (phone.low_balance_alert) return 'text-red-500';
    if (phone.credit_balance < 10) return 'text-yellow-500';
    return 'text-green-500';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-2 text-sm text-muted-foreground">Loading cost data...</p>
        </div>
      </div>
    );
  }

  if (!costSummary) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground" />
        <p className="mt-4 text-lg font-medium">No cost data available</p>
        <button
          onClick={loadCostSummary}
          className="mt-4 inline-flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry
        </button>
      </div>
    );
  }

  // Calculate total remaining minutes across all phones
  const totalRemainingMinutes = costSummary?.phones.reduce((total, phone) => {
    const remainingMinutes = phone.cost_per_minute > 0
      ? phone.credit_balance / phone.cost_per_minute
      : 0;
    return total + remainingMinutes;
  }, 0) || 0;

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Cost Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Balance</p>
                <p className="text-2xl font-bold mt-1">
                  GHC {costSummary.summary.total_balance.toFixed(2)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-green-500" />
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Remaining Minutes</p>
                <p className="text-2xl font-bold mt-1 text-primary">
                  {totalRemainingMinutes.toFixed(1)}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  @ GHC 0.15/min
                </p>
              </div>
              <Clock className="h-8 w-8 text-primary" />
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Minutes Used</p>
                <p className="text-2xl font-bold mt-1">
                  {costSummary.summary.total_minutes_used.toFixed(1)}
                </p>
              </div>
              <Clock className="h-8 w-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Cost Spent</p>
                <p className="text-2xl font-bold mt-1">
                  GHC {costSummary.summary.total_cost_spent.toFixed(2)}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-500" />
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Low Balance Alerts</p>
                <p className="text-2xl font-bold mt-1 text-red-500">
                  {costSummary.summary.low_balance_alerts}
                </p>
              </div>
              <AlertCircle className="h-8 w-8 text-red-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Phone Numbers List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">VAPI Phone Numbers</h2>
          <button
            onClick={loadCostSummary}
            className="inline-flex items-center px-3 py-1 text-sm border border-border rounded-md hover:bg-accent"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
        </div>

        {costSummary.phones.length === 0 ? (
          <div className="bg-card border border-border rounded-lg p-8 text-center">
            <Phone className="mx-auto h-12 w-12 text-muted-foreground" />
            <p className="mt-4 text-lg font-medium">No phone numbers with activity</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Phone numbers will appear here once they have credit or usage
            </p>
          </div>
        ) : (
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Phone Number
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Provider
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Credit Balance
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Remaining Minutes
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Minutes Used
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      VAPI Cost (USD)
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Phone Cost (GHC)
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Rate/Min
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {costSummary.phones.map((phone) => (
                    <tr key={phone.id} className="hover:bg-muted/50">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center">
                          <Phone className="w-4 h-4 mr-2 text-muted-foreground" />
                          <span className="font-medium">{phone.number}</span>
                          {phone.low_balance_alert && (
                            <AlertCircle className="w-4 h-4 ml-2 text-red-500" />
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm capitalize">
                        {phone.provider}
                      </td>
                      <td className={`px-4 py-3 whitespace-nowrap text-right font-medium ${getBalanceColor(phone)}`}>
                        {formatCurrency(phone.credit_balance, phone.currency)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm">
                        <div className="flex flex-col items-end">
                          <span className="font-semibold text-primary">
                            {phone.cost_per_minute > 0
                              ? (phone.credit_balance / phone.cost_per_minute).toFixed(1)
                              : '∞'} min
                          </span>
                          <span className="text-xs text-muted-foreground">
                            ({formatCurrency(phone.cost_per_minute, phone.currency)}/min)
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm">
                        {phone.total_minutes_used.toFixed(1)} min
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium text-blue-600">
                        ${phone.vapi_cost_usd.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium text-green-600">
                        GHC {phone.total_cost_spent.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm">
                        {formatCurrency(phone.cost_per_minute, phone.currency)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-center">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => onAddCredit(phone as any)}
                            className="inline-flex items-center px-3 py-1 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90"
                          >
                            <Plus className="w-3 h-3 mr-1" />
                            Add Credit
                          </button>
                          <button
                            onClick={() => onViewDetails(phone as any)}
                            className="inline-flex items-center px-3 py-1 text-xs border border-border rounded hover:bg-accent"
                          >
                            View Details
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
