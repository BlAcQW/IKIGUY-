import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { Download, Eye, RefreshCw, ArrowLeft } from 'lucide-react';
import RefundRequest from '@/components/RefundRequest';

interface PaymentTransaction {
  id: string;
  transaction_id: string;
  amount: number;
  currency: string;
  payment_method: string;
  status: 'pending' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  completed_at?: string;
  payment_reference?: string;
}

const PaymentHistory: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [transactions, setTransactions] = useState<PaymentTransaction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState<PaymentTransaction | null>(null);
  const [showRefundRequest, setShowRefundRequest] = useState(false);

  const loadTransactions = async () => {
    if (!user) return;
    
    setIsLoading(true);
    try {
      const { data, error } = await supabase
        .from('payment_transactions')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })
        .limit(20);

      if (error) throw error;
      setTransactions(data || []);
    } catch (error: any) {
      console.error('Error loading transactions:', error);
      toast({
        title: "Error loading transactions",
        description: error.message || "Failed to load payment history",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, [user]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'successful':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      case 'refunded':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
      case 'successful':
        return 'Completed';
      case 'pending':
        return 'Pending';
      case 'failed':
        return 'Failed';
      case 'cancelled':
        return 'Cancelled';
      case 'refunded':
        return 'Refunded';
      default:
        return status;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatAmount = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD'
    }).format(amount);
  };

  const exportTransactions = () => {
    const csvContent = [
      ['Date', 'Transaction ID', 'Amount', 'Payment Method', 'Status', 'Reference'],
      ...transactions.map(tx => [
        formatDate(tx.created_at),
        tx.transaction_id,
        formatAmount(tx.amount, tx.currency),
        tx.payment_method,
        getStatusText(tx.status),
        tx.payment_reference || ''
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `payment-history-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    toast({
      title: "Export successful",
      description: "Payment history has been downloaded as CSV",
    });
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Payment History</CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingSpinner text="Loading transactions..." />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Payment History</CardTitle>
            <CardDescription>
              Your recent payment transactions and wallet top-ups
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadTransactions}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={exportTransactions}
              disabled={transactions.length === 0}
            >
              <Download className="h-4 w-4" />
              Export
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {transactions.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-muted-foreground">No payment transactions found</p>
            <p className="text-sm text-muted-foreground mt-2">
              Your payment history will appear here once you make your first transaction.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {transactions.map((transaction) => (
              <div
                key={transaction.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <div>
                      <p className="font-medium text-sm">
                        {formatAmount(transaction.amount, transaction.currency)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {transaction.payment_method.replace('_', ' ').toUpperCase()}
                      </p>
                    </div>
                    <Badge className={getStatusColor(transaction.status)}>
                      {getStatusText(transaction.status)}
                    </Badge>
                  </div>
                  <div className="mt-2">
                    <p className="text-xs text-muted-foreground">
                      {formatDate(transaction.created_at)}
                    </p>
                    {transaction.payment_reference && (
                      <p className="text-xs text-muted-foreground">
                        Ref: {transaction.payment_reference}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      navigator.clipboard.writeText(transaction.transaction_id);
                      toast({
                        title: "Copied!",
                        description: "Transaction ID copied to clipboard",
                      });
                    }}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  {(transaction.status === 'completed' || transaction.status === 'successful') && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedTransaction(transaction);
                        setShowRefundRequest(true);
                      }}
                    >
                      <ArrowLeft className="h-4 w-4" />
                      Refund
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>

      {/* Refund Request Modal */}
      {showRefundRequest && selectedTransaction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-background rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto">
            <RefundRequest
              transaction={selectedTransaction}
              onClose={() => {
                setShowRefundRequest(false);
                setSelectedTransaction(null);
              }}
              onRefundSuccess={() => {
                loadTransactions();
                setShowRefundRequest(false);
                setSelectedTransaction(null);
              }}
            />
          </div>
        </div>
      )}
    </Card>
  );
};

export default PaymentHistory;
