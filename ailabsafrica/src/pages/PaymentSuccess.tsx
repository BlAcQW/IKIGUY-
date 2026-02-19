import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/components/ui/use-toast';

const PaymentSuccess = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [verificationStatus, setVerificationStatus] = useState<'loading' | 'success' | 'failed'>('loading');
  const [amount, setAmount] = useState<number | null>(null);

  const txRef = searchParams.get('tx_ref') || searchParams.get('transaction_id');

  useEffect(() => {
    if (txRef) {
      verifyPayment();
    } else {
      setVerificationStatus('failed');
    }
  }, [txRef]);

  const verifyPayment = async () => {
    try {
      const { data, error } = await supabase.functions.invoke('verify-payment', {
        body: { tx_ref: txRef }
      });

      if (error) throw error;

      if (data.success) {
        setVerificationStatus('success');
        setAmount(data.amount);
        toast({
          title: "Payment Successful!",
          description: `Your wallet has been credited with $${data.amount}`,
        });
      } else {
        setVerificationStatus('failed');
        toast({
          title: "Payment Failed",
          description: data.error || "Payment verification failed",
          variant: "destructive",
        });
      }
    } catch (error: any) {
      console.error('Payment verification error:', error);
      setVerificationStatus('failed');
      toast({
        title: "Payment Verification Failed",
        description: error.message || "Unable to verify your payment",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted flex items-center justify-center p-4">
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <div className="flex justify-center mb-4">
            {verificationStatus === 'loading' && (
              <Loader2 className="h-16 w-16 text-primary animate-spin" />
            )}
            {verificationStatus === 'success' && (
              <CheckCircle className="h-16 w-16 text-green-600" />
            )}
            {verificationStatus === 'failed' && (
              <XCircle className="h-16 w-16 text-red-600" />
            )}
          </div>
          
          <CardTitle className="text-2xl">
            {verificationStatus === 'loading' && 'Verifying Payment...'}
            {verificationStatus === 'success' && 'Payment Successful!'}
            {verificationStatus === 'failed' && 'Payment Failed'}
          </CardTitle>
          
          <CardDescription>
            {verificationStatus === 'loading' && 'Please wait while we verify your payment.'}
            {verificationStatus === 'success' && `Your wallet has been credited with $${amount?.toFixed(2)}`}
            {verificationStatus === 'failed' && 'There was an issue processing your payment.'}
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          {verificationStatus === 'success' && (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-green-800 font-medium">
                  Transaction Reference: {txRef}
                </p>
              </div>
              <Button onClick={() => navigate('/dashboard')} className="w-full">
                Go to Dashboard
              </Button>
            </div>
          )}
          
          {verificationStatus === 'failed' && (
            <div className="space-y-4">
              <Button onClick={() => navigate('/dashboard')} variant="outline" className="w-full">
                Back to Dashboard
              </Button>
              <Button onClick={() => window.location.reload()} className="w-full">
                Try Again
              </Button>
            </div>
          )}
          
          {verificationStatus === 'loading' && (
            <p className="text-muted-foreground">
              This may take a few moments...
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default PaymentSuccess;