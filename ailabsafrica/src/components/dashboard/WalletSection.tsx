import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import { Wallet, CreditCard, Smartphone } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';

interface WalletSectionProps {
  wallet: any;
  onWalletUpdate: () => void;
}

const WalletSection: React.FC<WalletSectionProps> = ({ wallet, onWalletUpdate }) => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [amount, setAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('');

  const handleTopUp = async () => {
    if (!amount || !paymentMethod || !user) {
      toast({
        title: "Missing information",
        description: "Please fill in all required fields",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      // Create transaction record
      const transactionId = `txn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      const { error: transactionError } = await supabase
        .from('payment_transactions')
        .insert([{
          user_id: user.id,
          wallet_id: wallet?.id,
          transaction_id: transactionId,
          payment_method: paymentMethod,
          amount: parseFloat(amount),
          currency: 'USD',
          status: 'pending'
        }]);

      if (transactionError) throw transactionError;

      // Get user profile for payment details
      const { data: profile } = await supabase
        .from('profiles')
        .select('display_name, phone')
        .eq('user_id', user.id)
        .single();

      // Call payment processing edge function
      const { data, error } = await supabase.functions.invoke('process-payment', {
        body: {
          amount: parseFloat(amount),
          currency: 'USD',
          payment_method: paymentMethod,
          transaction_id: transactionId,
          email: user.email,
          phone: profile?.phone || '',
          name: profile?.display_name || user.email
        }
      });

      if (error) throw error;

      if (data.payment_url) {
        // Open payment URL in new tab
        window.open(data.payment_url, '_blank');
        
        toast({
          title: "Payment initiated",
          description: "Complete your payment in the new tab. Your wallet will be updated once payment is confirmed.",
        });
      } else {
        toast({
          title: "Payment processing",
          description: "Your payment is being processed. Please wait...",
        });
      }

      setAmount('');
      setPaymentMethod('');
      onWalletUpdate();
    } catch (error: any) {
      console.error('Error processing payment:', error);
      toast({
        title: "Payment failed",
        description: error.message || "Please try again later.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getPaymentMethodIcon = (method: string) => {
    switch (method) {
      case 'card':
      case 'paypal':
        return <CreditCard className="h-4 w-4" />;
      case 'momo':
      case 'mpesa':
        return <Smartphone className="h-4 w-4" />;
      default:
        return <CreditCard className="h-4 w-4" />;
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wallet className="h-5 w-5" />
            Wallet Balance
          </CardTitle>
          <CardDescription>
            Your current account balance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-primary">
            ${wallet?.balance?.toFixed(2) || '0.00'}
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            Available for AI assistant usage
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Top Up Wallet</CardTitle>
          <CardDescription>
            Add funds using African mobile money or card
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="amount">Amount (USD)</Label>
            <Input
              id="amount"
              type="number"
              placeholder="Enter amount"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              min="1"
              step="0.01"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="payment-method">Payment Method</Label>
            <Select value={paymentMethod} onValueChange={setPaymentMethod}>
              <SelectTrigger>
                <SelectValue placeholder="Select payment method" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="momo" className="flex items-center gap-2">
                  <div className="flex items-center gap-2">
                    <Smartphone className="h-4 w-4" />
                    Mobile Money (MTN, Airtel, etc.)
                  </div>
                </SelectItem>
                <SelectItem value="mpesa" className="flex items-center gap-2">
                  <div className="flex items-center gap-2">
                    <Smartphone className="h-4 w-4" />
                    M-Pesa
                  </div>
                </SelectItem>
                <SelectItem value="card" className="flex items-center gap-2">
                  <div className="flex items-center gap-2">
                    <CreditCard className="h-4 w-4" />
                    Credit/Debit Card
                  </div>
                </SelectItem>
                <SelectItem value="paypal" className="flex items-center gap-2">
                  <div className="flex items-center gap-2">
                    <CreditCard className="h-4 w-4" />
                    PayPal
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button 
            onClick={handleTopUp} 
            className="w-full"
            disabled={isLoading || !amount || !paymentMethod}
          >
            {isLoading ? "Processing..." : "Top Up Wallet"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default WalletSection;