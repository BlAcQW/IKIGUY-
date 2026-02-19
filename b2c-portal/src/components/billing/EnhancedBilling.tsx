import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { paymentApi, WalletTransaction } from '@/lib/core-api';
import PaymentMethodSelector from './PaymentMethodSelector';
import TransactionList from './TransactionList';
import WalletSettingsDialog from './WalletSettingsDialog';
import {
  Download,
  CreditCard,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Plus,
  Receipt,
  Wallet,
  Bell,
  ArrowLeft,
  Search,
  Filter,
  Settings
} from 'lucide-react';

interface EnhancedBillingProps {
  currentBalance: number;
  usageData: any;
}

interface TopUpOption {
  id: string;
  amount: number;
  bonus: number;
  popular?: boolean;
}

const EnhancedBilling: React.FC<EnhancedBillingProps> = ({ currentBalance, usageData }) => {
  const [topUpDialogOpen, setTopUpDialogOpen] = useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [selectedTopUpAmount, setSelectedTopUpAmount] = useState<number>(50);
  const [customAmount, setCustomAmount] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [showPaymentMethods, setShowPaymentMethods] = useState(false);
  const [transactions, setTransactions] = useState<WalletTransaction[]>([]);
  const [isLoadingTransactions, setIsLoadingTransactions] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const { toast } = useToast();

  const topUpOptions: TopUpOption[] = [
    { id: '1', amount: 25, bonus: 0 },
    { id: '2', amount: 50, bonus: 5, popular: true },
    { id: '3', amount: 100, bonus: 15 },
    { id: '4', amount: 250, bonus: 50 },
    { id: '5', amount: 500, bonus: 125 },
    { id: '6', amount: 1000, bonus: 300 }
  ];

  // Fetch transactions on component mount
  useEffect(() => {
    const fetchTransactions = async () => {
      setIsLoadingTransactions(true);
      try {
        const txs = await paymentApi.getTransactions(50, 0); // Get last 50 transactions
        setTransactions(txs);
      } catch (error) {
        console.error('Failed to fetch transactions:', error);
        toast({
          title: 'Error loading transactions',
          description: 'Could not load transaction history',
          variant: 'destructive'
        });
      } finally {
        setIsLoadingTransactions(false);
      }
    };

    fetchTransactions();
  }, [toast]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };


  // Filter transactions based on search and filters
  const filteredTransactions = transactions.filter((tx) => {
    const matchesSearch = searchQuery === '' ||
      tx.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tx.id.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = statusFilter === 'all' || tx.status.toLowerCase() === statusFilter.toLowerCase();
    const matchesType = typeFilter === 'all' || tx.transaction_type.toLowerCase() === typeFilter.toLowerCase();

    return matchesSearch && matchesStatus && matchesType;
  });

  const handleContinueToPayment = () => {
    const amount = customAmount ? parseFloat(customAmount) : selectedTopUpAmount;
    if (amount <= 0) {
      toast({
        title: "Invalid amount",
        description: "Please enter a valid amount",
        variant: "destructive"
      });
      return;
    }
    setShowPaymentMethods(true);
  };

  const handlePaymentMethodSelected = async (method: any, additionalData?: any) => {
    setIsProcessing(true);
    try {
      const amount = customAmount ? parseFloat(customAmount) : selectedTopUpAmount;

      // First, add the payment method if it's new
      let paymentMethodId = method.id;
      if (!paymentMethodId) {
        const newMethod = await paymentApi.addPaymentMethod({
          provider: method.provider,
          method_type: method.method_type,
          display_name: method.display_name,
          phone_number: additionalData?.phone_number,
          phone_network: method.provider,
        });
        paymentMethodId = newMethod.id;
      }

      // Create deposit transaction
      const transaction = await paymentApi.createDeposit({
        amount,
        currency: 'USD',
        payment_method_id: paymentMethodId,
        description: `Wallet top-up: ${formatCurrency(amount)}`,
      });

      toast({
        title: "Payment initiated",
        description: method.method_type === 'mobile_money'
          ? `Check your phone (${additionalData?.phone_number}) to approve payment`
          : `Processing ${formatCurrency(amount)} payment`,
        variant: "default"
      });

      setTopUpDialogOpen(false);
      setCustomAmount('');
      setShowPaymentMethods(false);

      // Refresh wallet balance after successful deposit
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    } catch (error: any) {
      console.error('Payment failed:', error);
      toast({
        title: "Payment failed",
        description: error.message || "Please try again or contact support",
        variant: "destructive"
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleBackToAmountSelection = () => {
    setShowPaymentMethods(false);
  };

  const isLowBalance = currentBalance < 10;
  const isOverLimit = usageData?.minutes_used > usageData?.minutes_included;

  return (
    <div className="space-y-6">
      {/* Current Balance & Alerts */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-gradient-card border-accent/20 shadow-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-sm text-gray-600">Current Balance</p>
                <p className="text-3xl font-bold text-accent">{formatCurrency(currentBalance)}</p>
              </div>
              <div className="flex flex-col gap-2">
                <Wallet className="h-8 w-8 text-accent" />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSettingsDialogOpen(true)}
                  className="h-6 w-8 p-0"
                >
                  <Settings className="h-4 w-4 text-gray-500 hover:text-accent" />
                </Button>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                className="flex-1 bg-gradient-premium text-accent-foreground shadow-accent"
                onClick={() => setTopUpDialogOpen(true)}
              >
                <Plus className="h-4 w-4 mr-2" />
                Top Up
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-card border-accent/20 shadow-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Monthly Usage</p>
                <p className="text-3xl font-bold text-primary-glow">
                  {usageData?.minutes_used || 0} / {usageData?.minutes_included || 0}
                </p>
              </div>
              <Clock className="h-8 w-8 text-primary-glow" />
            </div>
            <div className="mt-2">
              <Progress 
                value={Math.min((usageData?.minutes_used || 0) / (usageData?.minutes_included || 1) * 100, 100)} 
                className="h-2" 
              />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-card border-accent/20 shadow-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Overage Rate</p>
                <p className="text-3xl font-bold text-accent">
                  {formatCurrency(usageData?.overage_rate || 0.10)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-accent" />
            </div>
            <p className="text-xs text-gray-600 mt-1">per minute over limit</p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts */}
      {(isLowBalance || isOverLimit) && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5" />
              <div className="flex-1">
                <h4 className="font-medium text-orange-800">Account Alerts</h4>
                <div className="space-y-1 mt-1">
                  {isLowBalance && (
                    <p className="text-sm text-orange-700">
                      • Low balance: {formatCurrency(currentBalance)} remaining
                    </p>
                  )}
                  {isOverLimit && (
                    <p className="text-sm text-orange-700">
                      • Over monthly limit: {usageData?.minutes_used - usageData?.minutes_included} extra minutes used
                    </p>
                  )}
                </div>
                <Button 
                  size="sm" 
                  className="mt-2 bg-orange-600 hover:bg-orange-700"
                  onClick={() => setTopUpDialogOpen(true)}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Credits
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Service Cost Breakdown */}
      <Card className="bg-gradient-card border-accent/20 shadow-card">
        <CardHeader>
          <CardTitle className="text-xl font-playfair text-accent flex items-center gap-2">
            <Receipt className="h-5 w-5" />
            Service Cost Breakdown
          </CardTitle>
          <CardDescription>Detailed usage costs by service</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Telephony Costs */}
            <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-blue-900">Telephony</span>
                <span className="text-lg font-bold text-blue-700">
                  {formatCurrency(usageData?.telephony_cost || 0)}
                </span>
              </div>
              <p className="text-xs text-blue-600">Voice calls and phone services</p>
            </div>

            {/* STT Costs */}
            <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg border border-purple-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-purple-900">Speech-to-Text</span>
                <span className="text-lg font-bold text-purple-700">
                  {formatCurrency(usageData?.stt_cost || 0)}
                </span>
              </div>
              <p className="text-xs text-purple-600">
                {usageData?.stt_calls || 0} transcription calls
              </p>
            </div>

            {/* TTS Costs */}
            <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-green-900">Text-to-Speech</span>
                <span className="text-lg font-bold text-green-700">
                  {formatCurrency(usageData?.tts_cost || 0)}
                </span>
              </div>
              <p className="text-xs text-green-600">
                {usageData?.tts_calls || 0} synthesis calls
              </p>
            </div>

            {/* Automation Costs */}
            <div className="p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg border border-orange-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-orange-900">Automation</span>
                <span className="text-lg font-bold text-orange-700">
                  {formatCurrency(usageData?.automation_cost || 0)}
                </span>
              </div>
              <p className="text-xs text-orange-600">
                {usageData?.automation_calls || 0} automation executions
              </p>
            </div>
          </div>

          {/* Total Current Period Cost */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-base font-semibold text-gray-900">Total Usage Cost</span>
              <span className="text-2xl font-bold text-accent">
                {formatCurrency(
                  (usageData?.telephony_cost || 0) +
                  (usageData?.stt_cost || 0) +
                  (usageData?.tts_cost || 0) +
                  (usageData?.automation_cost || 0)
                )}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">Current billing period</p>
          </div>
        </CardContent>
      </Card>

      {/* Transaction History */}
      <TransactionList
        transactions={filteredTransactions}
        isLoading={isLoadingTransactions}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        typeFilter={typeFilter}
        setTypeFilter={setTypeFilter}
      />

      {/* Top-up Dialog */}
      <Dialog open={topUpDialogOpen} onOpenChange={(open) => {
        setTopUpDialogOpen(open);
        if (!open) {
          setShowPaymentMethods(false);
          setCustomAmount('');
        }
      }}>
        <DialogContent className="max-w-md bg-gradient-card border-accent/20 shadow-glow">
          <DialogHeader>
            <DialogTitle className="text-xl font-playfair text-accent flex items-center gap-2">
              {showPaymentMethods && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleBackToAmountSelection}
                  className="p-0 h-auto hover:bg-transparent"
                >
                  <ArrowLeft className="h-5 w-5" />
                </Button>
              )}
              {showPaymentMethods ? 'Select Payment Method' : 'Top Up Your Balance'}
            </DialogTitle>
            <DialogDescription className="text-gray-600">
              {showPaymentMethods
                ? 'Choose how you want to pay'
                : 'Add credits to your account for uninterrupted service'}
            </DialogDescription>
          </DialogHeader>

          {!showPaymentMethods ? (
            <div className="space-y-4">
              <div>
                <Label htmlFor="top-up-amount">Select Amount</Label>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  {topUpOptions.map((option) => (
                    <Button
                      key={option.id}
                      variant={selectedTopUpAmount === option.amount ? "default" : "outline"}
                      className={`justify-between ${
                        option.popular ? 'border-accent bg-accent/10' : ''
                      }`}
                      onClick={() => {
                        setSelectedTopUpAmount(option.amount);
                        setCustomAmount('');
                      }}
                    >
                      <span>{formatCurrency(option.amount)}</span>
                      {option.bonus > 0 && (
                        <Badge variant="secondary" className="text-xs">
                          +{formatCurrency(option.bonus)}
                        </Badge>
                      )}
                    </Button>
                  ))}
                </div>
              </div>

              <div>
                <Label htmlFor="custom-amount">Or enter custom amount</Label>
                <Input
                  id="custom-amount"
                  type="number"
                  placeholder="Enter amount"
                  value={customAmount}
                  onChange={(e) => {
                    setCustomAmount(e.target.value);
                    if (e.target.value) {
                      setSelectedTopUpAmount(0);
                    }
                  }}
                  className="mt-1"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setTopUpDialogOpen(false)}
                  className="border-accent/20 hover:border-accent"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleContinueToPayment}
                  disabled={!selectedTopUpAmount && !customAmount}
                  className="bg-gradient-premium text-accent-foreground shadow-accent"
                >
                  <CreditCard className="h-4 w-4 mr-2" />
                  Continue to Payment
                </Button>
              </div>
            </div>
          ) : (
            <PaymentMethodSelector
              amount={customAmount ? parseFloat(customAmount) : selectedTopUpAmount}
              currency="USD"
              onPaymentMethodSelected={handlePaymentMethodSelected}
              onCancel={handleBackToAmountSelection}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Wallet Settings Dialog */}
      <WalletSettingsDialog
        open={settingsDialogOpen}
        onOpenChange={setSettingsDialogOpen}
      />
    </div>
  );
};

export default EnhancedBilling; 