import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/integrations/supabase/client';
import { ArrowLeft, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';

interface RefundRequestProps {
  transaction: any;
  onClose?: () => void;
  onRefundSuccess?: () => void;
}

const RefundRequest: React.FC<RefundRequestProps> = ({ transaction, onClose, onRefundSuccess }) => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [refundType, setRefundType] = useState<'full' | 'partial'>('full');
  const [refundAmount, setRefundAmount] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleRefundRequest = async () => {
    if (!reason.trim()) {
      toast({
        title: "Reason Required",
        description: "Please provide a reason for the refund request",
        variant: "destructive",
      });
      return;
    }

    if (refundType === 'partial' && (!refundAmount || parseFloat(refundAmount) <= 0)) {
      toast({
        title: "Invalid Amount",
        description: "Please enter a valid refund amount",
        variant: "destructive",
      });
      return;
    }

    if (refundType === 'partial' && parseFloat(refundAmount) > transaction.amount) {
      toast({
        title: "Invalid Amount",
        description: "Refund amount cannot exceed the original transaction amount",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsProcessing(true);
      const { data, error } = await supabase.functions.invoke('process-refund', {
        body: {
          transaction_id: transaction.transaction_id,
          amount: refundType === 'partial' ? parseFloat(refundAmount) : undefined,
          reason: reason.trim(),
          user_id: user?.id
        }
      });

      if (error) throw error;

      if (data.success) {
        toast({
          title: "Refund Request Submitted",
          description: "Your refund request has been processed successfully",
        });
        
        if (onRefundSuccess) {
          onRefundSuccess();
        }
        
        if (onClose) {
          onClose();
        }
      }
    } catch (error: any) {
      toast({
        title: "Refund Request Failed",
        description: error.message || "Failed to process refund request",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ArrowLeft className="h-5 w-5" />
          Request Refund
        </CardTitle>
        <CardDescription>
          Submit a refund request for this transaction
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Transaction Details */}
        <div className="p-3 border rounded-lg bg-muted/50">
          <h4 className="font-medium mb-2">Transaction Details</h4>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span>Amount:</span>
              <span className="font-medium">{formatCurrency(transaction.amount, transaction.currency)}</span>
            </div>
            <div className="flex justify-between">
              <span>Date:</span>
              <span>{formatDate(transaction.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span>Status:</span>
              <Badge variant={transaction.status === 'successful' ? 'default' : 'secondary'}>
                {transaction.status}
              </Badge>
            </div>
          </div>
        </div>

        {/* Refund Type Selection */}
        <div className="space-y-2">
          <Label htmlFor="refund-type">Refund Type</Label>
          <Select value={refundType} onValueChange={(value: 'full' | 'partial') => setRefundType(value)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="full">Full Refund</SelectItem>
              <SelectItem value="partial">Partial Refund</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Partial Refund Amount */}
        {refundType === 'partial' && (
          <div className="space-y-2">
            <Label htmlFor="refund-amount">Refund Amount ({transaction.currency})</Label>
            <Input
              id="refund-amount"
              type="number"
              step="0.01"
              min="0.01"
              max={transaction.amount}
              placeholder={`Enter amount (max: ${formatCurrency(transaction.amount, transaction.currency)})`}
              value={refundAmount}
              onChange={(e) => setRefundAmount(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Maximum refund amount: {formatCurrency(transaction.amount, transaction.currency)}
            </p>
          </div>
        )}

        {/* Refund Reason */}
        <div className="space-y-2">
          <Label htmlFor="refund-reason">Reason for Refund *</Label>
          <Textarea
            id="refund-reason"
            placeholder="Please explain why you're requesting a refund..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
          />
        </div>

        {/* Refund Summary */}
        {refundType === 'partial' && refundAmount && (
          <div className="p-3 border rounded-lg bg-muted/50">
            <h4 className="font-medium mb-2">Refund Summary</h4>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span>Original Amount:</span>
                <span>{formatCurrency(transaction.amount, transaction.currency)}</span>
              </div>
              <div className="flex justify-between">
                <span>Refund Amount:</span>
                <span className="font-medium text-green-600">
                  {formatCurrency(parseFloat(refundAmount), transaction.currency)}
                </span>
              </div>
              <div className="flex justify-between border-t pt-1">
                <span>Remaining Balance:</span>
                <span className="font-medium">
                  {formatCurrency(transaction.amount - parseFloat(refundAmount), transaction.currency)}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 pt-4">
          <Button
            onClick={handleRefundRequest}
            disabled={isProcessing || !reason.trim() || (refundType === 'partial' && !refundAmount)}
            className="flex-1"
          >
            {isProcessing ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <CheckCircle className="h-4 w-4 mr-2" />
            )}
            {isProcessing ? 'Processing...' : 'Submit Refund Request'}
          </Button>
          {onClose && (
            <Button variant="outline" onClick={onClose} disabled={isProcessing}>
              Cancel
            </Button>
          )}
        </div>

        {/* Important Notice */}
        <div className="p-3 border rounded-lg bg-yellow-50 border-yellow-200">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5" />
            <div className="text-sm text-yellow-800">
              <p className="font-medium">Important Notice</p>
              <p>Refund requests are processed within 3-5 business days. You will receive an email confirmation once the refund is processed.</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default RefundRequest;
