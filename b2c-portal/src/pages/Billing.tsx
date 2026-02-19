import React, { useState, useEffect } from 'react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import EnhancedBilling from '@/components/billing/EnhancedBilling';
import { Card, CardContent } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import { usageApi, paymentApi } from '@/lib/core-api';
import { Loader2 } from 'lucide-react';

interface UsageData {
  minutes_used?: number;
  minutes_included?: number;
  overage_rate?: number;
  stt_calls?: number;
  tts_calls?: number;
  telephony_cost?: number;
  stt_cost?: number;
  tts_cost?: number;
  automation_cost?: number;
  automation_calls?: number;
}

const Billing: React.FC = () => {
  const [currentBalance, setCurrentBalance] = useState<number>(0);
  const [usageData, setUsageData] = useState<UsageData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();
  const { user } = useMongoAuth();

  useEffect(() => {
    const loadBillingData = async () => {
      if (!user?.id) {
        toast({
          title: 'Authentication Required',
          description: 'User not authenticated',
          variant: 'destructive'
        });
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);

        // Load wallet balance and usage data in parallel
        const [walletResponse, usageResponse] = await Promise.allSettled([
          paymentApi.getWalletBalance(),
          usageApi.getUsageData()
        ]);

        // Handle wallet balance
        if (walletResponse.status === 'fulfilled') {
          setCurrentBalance(walletResponse.value.balance || 0);
        } else {
          console.error('Failed to load wallet balance:', walletResponse.reason);
          setCurrentBalance(0);
        }

        // Handle usage data
        if (usageResponse.status === 'fulfilled') {
          const usage = usageResponse.value;
          setUsageData({
            minutes_used: usage.minutes || 0,
            minutes_included: 1000, // Default monthly allocation
            overage_rate: 0.10, // Default rate per minute
            stt_calls: usage.stt_calls || 0,
            tts_calls: usage.tts_calls || 0,
            telephony_cost: usage.telephony_cost || 0,
            stt_cost: usage.stt_cost || 0,
            tts_cost: usage.tts_cost || 0,
            automation_cost: usage.automation_cost || 0,
            automation_calls: usage.automation_calls || 0,
          });
        } else {
          console.error('Failed to load usage data:', usageResponse.reason);
          // Set default usage data
          setUsageData({
            minutes_used: 0,
            minutes_included: 1000,
            overage_rate: 0.10,
            stt_calls: 0,
            tts_calls: 0,
            telephony_cost: 0,
            stt_cost: 0,
            tts_cost: 0,
            automation_cost: 0,
            automation_calls: 0,
          });
        }

        // Show error toast only if both requests failed
        if (walletResponse.status === 'rejected' && usageResponse.status === 'rejected') {
          toast({
            title: 'Error loading billing data',
            description: 'Some billing information may not be current',
            variant: 'destructive'
          });
        }

      } catch (error) {
        console.error('Error loading billing data:', error);
        toast({
          title: 'Error loading billing data',
          description: 'Please try refreshing the page',
          variant: 'destructive'
        });

        // Set fallback data
        setCurrentBalance(0);
        setUsageData({
          minutes_used: 0,
          minutes_included: 1000,
          overage_rate: 0.10,
          stt_calls: 0,
          tts_calls: 0,
          telephony_cost: 0,
          stt_cost: 0,
          tts_cost: 0,
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadBillingData();
  }, [user?.id, toast]);

  if (isLoading) {
    return (
      <div className="flex h-screen">
        <DashboardSidebar />
        <main className="flex-1 p-6">
          <div className="flex items-center justify-center h-full">
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
              <p className="text-gray-600">Loading billing information...</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <DashboardSidebar />
      <main className="flex-1 overflow-auto">
        <div className="container mx-auto p-6 pb-12 max-w-7xl">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Billing & Usage</h1>
              <p className="text-gray-600 mt-2">
                Manage your account balance, view usage, and download invoices
              </p>
            </div>
          </div>

          {!user ? (
            <Card>
              <CardContent className="p-6">
                <div className="text-center">
                  <p className="text-gray-600">
                    Please log in to view billing information
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <EnhancedBilling
              currentBalance={currentBalance}
              usageData={usageData}
            />
          )}
        </div>
      </main>
    </div>
  );
};

export default Billing;