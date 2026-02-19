import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { CreditCard, AlertTriangle, Loader2 } from 'lucide-react';
import { usageApi, paymentApi } from '@/lib/core-api';
import { useToast } from '@/hooks/use-toast';

interface UsageMeterProps {
  tenantId: string;
}

export function UsageMeter({ tenantId }: UsageMeterProps) {
  const [usageData, setUsageData] = useState({
    minutesUsed: 0,
    minutesIncluded: 5000, // Default plan
    usagePercentage: 0,
    loading: true
  });
  const [walletBalance, setWalletBalance] = useState({
    balance: 0,
    currency: 'USD',
    loading: true
  });
  const { toast } = useToast();

  useEffect(() => {
    loadUsageData();
    loadWalletBalance();
  }, [tenantId]);

  const loadUsageData = async () => {
    try {
      setUsageData(prev => ({ ...prev, loading: true }));
      const usage = await usageApi.getUsageData();
      const minutesUsed = usage.minutes || 0;
      const minutesIncluded = 5000; // This should come from license/plan data
      const usagePercentage = (minutesUsed / minutesIncluded) * 100;
      
      setUsageData({
        minutesUsed,
        minutesIncluded,
        usagePercentage,
        loading: false
      });
    } catch (error) {
      console.error('Failed to load usage data:', error);
      toast({
        title: "Error",
        description: "Failed to load usage data.",
        variant: "destructive",
      });
      setUsageData(prev => ({ ...prev, loading: false }));
    }
  };

  const loadWalletBalance = async () => {
    try {
      setWalletBalance(prev => ({ ...prev, loading: true }));
      const wallet = await paymentApi.getWalletBalance(tenantId);
      setWalletBalance({
        balance: wallet.balance || 0,
        currency: wallet.currency || 'USD',
        loading: false
      });
    } catch (error) {
      console.error('Failed to load wallet balance:', error);
      setWalletBalance(prev => ({ ...prev, loading: false }));
    }
  };

  const overageRate = 0.10; // $0.10 per minute

  if (usageData.loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Usage & Balance</CardTitle>
          <CardDescription>Loading usage data...</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Usage & Balance
          {usageData.usagePercentage > 80 && (
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          )}
        </CardTitle>
        <CardDescription>
          Track your current usage and remaining balance
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Usage Progress */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Minutes Used</span>
            <span className="font-medium">
              {usageData.minutesUsed.toLocaleString()} / {usageData.minutesIncluded.toLocaleString()}
            </span>
          </div>
          <Progress value={usageData.usagePercentage} className="h-2" />
          <p className="text-xs text-gray-600">
            {(usageData.minutesIncluded - usageData.minutesUsed).toLocaleString()} minutes remaining
          </p>
        </div>

        {/* Pricing Info */}
        <div className="grid grid-cols-2 gap-4 p-4 bg-muted/50 rounded-lg">
          <div>
            <p className="text-sm font-medium">Current Plan</p>
            <p className="text-2xl font-bold">5K Bundle</p>
            <p className="text-xs text-gray-600">$99.99</p>
          </div>
          <div>
            <p className="text-sm font-medium">Overage Rate</p>
            <p className="text-2xl font-bold">${overageRate}</p>
            <p className="text-xs text-gray-600">per minute</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button className="flex-1 gap-2">
            <CreditCard className="h-4 w-4" />
            Top Up Balance
          </Button>
          <Button variant="outline" className="flex-1">
            View Usage
          </Button>
        </div>

        {usageData.usagePercentage > 80 && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              <AlertTriangle className="h-4 w-4 inline mr-2" />
              You've used {Math.round(usageData.usagePercentage)}% of your included minutes. 
              Consider topping up to avoid overage charges.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}