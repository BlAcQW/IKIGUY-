import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { affiliateApi, PayoutRequest, AffiliateStats } from '@/lib/core-api';
import {
  Wallet,
  CreditCard,
  Building,
  AlertCircle,
  CheckCircle,
  DollarSign,
  Info
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface PayoutRequestFormProps {
  onSuccess?: () => void;
}

interface PayoutMethod {
  id: string;
  name: string;
  icon: React.ReactNode;
  minAmount: number;
  fee: string;
  processingTime: string;
  description: string;
}

const PayoutRequestForm: React.FC<PayoutRequestFormProps> = ({ onSuccess }) => {
  const [payoutMethod, setPayoutMethod] = useState<string>('');
  const [amount, setAmount] = useState<string>('');
  const [details, setDetails] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [availableBalance, setAvailableBalance] = useState(0);
  const [stats, setStats] = useState<AffiliateStats | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const { toast } = useToast();

  const payoutMethods: PayoutMethod[] = [
    {
      id: 'wallet_credit',
      name: 'Wallet Credit',
      icon: <Wallet className="h-5 w-5" />,
      minAmount: 0,
      fee: 'Free',
      processingTime: 'Instant',
      description: 'Add funds directly to your KasaAI wallet'
    },
    {
      id: 'mobile_money',
      name: 'Mobile Money',
      icon: <CreditCard className="h-5 w-5" />,
      minAmount: 10,
      fee: '2.5%',
      processingTime: '1-2 business days',
      description: 'MTN, Airtel, or other mobile money services'
    },
    {
      id: 'bank_transfer',
      name: 'Bank Transfer',
      icon: <Building className="h-5 w-5" />,
      minAmount: 50,
      fee: '$5 flat fee',
      processingTime: '2-5 business days',
      description: 'Direct bank deposit'
    },
    {
      id: 'paypal',
      name: 'PayPal',
      icon: <CreditCard className="h-5 w-5" />,
      minAmount: 20,
      fee: '2.9% + $0.30',
      processingTime: '1-2 business days',
      description: 'Transfer to PayPal account'
    }
  ];

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const statsData = await affiliateApi.getStats();
      setStats(statsData);
      setAvailableBalance(statsData.pending_commissions);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const getSelectedMethod = (): PayoutMethod | undefined => {
    return payoutMethods.find(m => m.id === payoutMethod);
  };

  const calculateFee = (amount: number, method: PayoutMethod): number => {
    switch (method.id) {
      case 'wallet_credit':
        return 0;
      case 'mobile_money':
        return amount * 0.025;
      case 'bank_transfer':
        return 5;
      case 'paypal':
        return amount * 0.029 + 0.30;
      default:
        return 0;
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!payoutMethod) {
      newErrors.payoutMethod = 'Please select a payout method';
    }

    const amountValue = parseFloat(amount);
    if (!amount || isNaN(amountValue) || amountValue <= 0) {
      newErrors.amount = 'Please enter a valid amount';
    } else {
      const selectedMethod = getSelectedMethod();
      if (selectedMethod) {
        if (amountValue < selectedMethod.minAmount) {
          newErrors.amount = `Minimum amount for ${selectedMethod.name} is $${selectedMethod.minAmount}`;
        }
        if (amountValue > availableBalance) {
          newErrors.amount = 'Amount exceeds available balance';
        }
      }
    }

    if (!details || details.trim().length === 0) {
      newErrors.details = 'Please provide payout details';
    } else if (details.trim().length < 10) {
      newErrors.details = 'Please provide more detailed information (at least 10 characters)';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    try {
      const payoutRequest = await affiliateApi.requestPayout({
        amount: parseFloat(amount),
        payout_method: payoutMethod,
        payout_details: details
      });

      toast({
        title: 'Payout request submitted!',
        description: `Your request for ${formatCurrency(parseFloat(amount))} has been submitted and is pending review.`
      });

      // Reset form
      setPayoutMethod('');
      setAmount('');
      setDetails('');
      setErrors({});

      // Reload stats
      await loadStats();

      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      toast({
        title: 'Failed to submit payout request',
        description: error instanceof Error ? error.message : 'Please try again',
        variant: 'destructive'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const selectedMethod = getSelectedMethod();
  const amountValue = parseFloat(amount) || 0;
  const fee = selectedMethod ? calculateFee(amountValue, selectedMethod) : 0;
  const netAmount = amountValue - fee;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <DollarSign className="h-5 w-5 text-green-600" />
          Request Payout
        </CardTitle>
        <CardDescription>
          Withdraw your commission earnings to your preferred method
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Available Balance */}
        <div className="bg-blue-50 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Available Balance</p>
              <p className="text-3xl font-bold text-blue-600">
                {formatCurrency(availableBalance)}
              </p>
            </div>
            <Wallet className="h-12 w-12 text-blue-600 opacity-20" />
          </div>
        </div>

        {availableBalance === 0 ? (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              You don't have any available balance to withdraw. Start earning by referring new users!
            </AlertDescription>
          </Alert>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Payout Method Selection */}
            <div className="space-y-3">
              <Label>Select Payout Method</Label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {payoutMethods.map((method) => (
                  <div
                    key={method.id}
                    className={`border rounded-lg p-4 cursor-pointer transition-all ${
                      payoutMethod === method.id
                        ? 'border-blue-600 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => {
                      setPayoutMethod(method.id);
                      setErrors({ ...errors, payoutMethod: '' });
                    }}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${
                        payoutMethod === method.id ? 'bg-blue-600 text-white' : 'bg-gray-100'
                      }`}>
                        {method.icon}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-sm mb-1">{method.name}</h4>
                        <p className="text-xs text-muted-foreground mb-2">
                          {method.description}
                        </p>
                        <div className="flex items-center gap-2 flex-wrap">
                          <Badge variant="secondary" className="text-xs">
                            Min: ${method.minAmount}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            Fee: {method.fee}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {method.processingTime}
                          </Badge>
                        </div>
                      </div>
                      {payoutMethod === method.id && (
                        <CheckCircle className="h-5 w-5 text-blue-600 shrink-0" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
              {errors.payoutMethod && (
                <p className="text-sm text-red-600">{errors.payoutMethod}</p>
              )}
            </div>

            {/* Amount Input */}
            <div className="space-y-2">
              <Label htmlFor="amount">Amount to Withdraw</Label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="amount"
                  type="number"
                  step="0.01"
                  min="0"
                  max={availableBalance}
                  value={amount}
                  onChange={(e) => {
                    setAmount(e.target.value);
                    setErrors({ ...errors, amount: '' });
                  }}
                  placeholder="0.00"
                  className="pl-10"
                  disabled={!payoutMethod}
                />
              </div>
              {selectedMethod && (
                <p className="text-xs text-muted-foreground">
                  Minimum: ${selectedMethod.minAmount} • Maximum: {formatCurrency(availableBalance)}
                </p>
              )}
              {errors.amount && (
                <p className="text-sm text-red-600">{errors.amount}</p>
              )}
            </div>

            {/* Fee Breakdown */}
            {selectedMethod && amountValue > 0 && (
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <h4 className="font-semibold text-sm mb-3">Payout Summary</h4>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Requested Amount</span>
                  <span className="font-medium">{formatCurrency(amountValue)}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Processing Fee</span>
                  <span className="font-medium text-orange-600">-{formatCurrency(fee)}</span>
                </div>
                <div className="border-t pt-2 mt-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">You'll Receive</span>
                    <span className="font-bold text-green-600 text-lg">
                      {formatCurrency(Math.max(0, netAmount))}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Payout Details */}
            <div className="space-y-2">
              <Label htmlFor="details">
                Payout Details
                <span className="text-red-600 ml-1">*</span>
              </Label>
              <Textarea
                id="details"
                value={details}
                onChange={(e) => {
                  setDetails(e.target.value);
                  setErrors({ ...errors, details: '' });
                }}
                placeholder={
                  payoutMethod === 'wallet_credit'
                    ? 'No additional details required'
                    : payoutMethod === 'mobile_money'
                    ? 'Enter your mobile money number (e.g., +256 700 123456)'
                    : payoutMethod === 'bank_transfer'
                    ? 'Enter bank name, account number, and account name'
                    : payoutMethod === 'paypal'
                    ? 'Enter your PayPal email address'
                    : 'Select a payout method first'
                }
                rows={4}
                disabled={!payoutMethod}
              />
              {errors.details && (
                <p className="text-sm text-red-600">{errors.details}</p>
              )}
            </div>

            {/* Info Alert */}
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                <strong>Note:</strong> All payout requests are reviewed manually and typically processed within{' '}
                {selectedMethod?.processingTime || '1-5 business days'}. Requests over $500 may require additional verification.
              </AlertDescription>
            </Alert>

            {/* Submit Button */}
            <Button
              type="submit"
              className="w-full"
              disabled={isSubmitting || !payoutMethod || !amount || availableBalance === 0}
            >
              {isSubmitting ? 'Submitting...' : `Request ${amount ? formatCurrency(parseFloat(amount)) : 'Payout'}`}
            </Button>
          </form>
        )}
      </CardContent>
    </Card>
  );
};

export default PayoutRequestForm;
