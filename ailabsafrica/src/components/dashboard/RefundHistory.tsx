import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/integrations/supabase/client';
import { RefreshCw, ArrowLeft, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface RefundRecord {
  id: string;
  transaction_id: string;
  amount: number;
  currency: string;
  reason: string;
  status: 'pending' | 'processing' | 'successful' | 'failed' | 'cancelled';
  refund_type: 'full' | 'partial';
  flw_refund_id?: string;
  error_message?: string;
  processed_at?: string;
  created_at: string;
  transaction?: {
    amount: number;
    currency: string;
    payment_method: string;
    created_at: string;
  };
}

const RefundHistory: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [refunds, setRefunds] = useState<RefundRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      fetchRefunds();
    }
  }, [user]);

  const fetchRefunds = async () => {
    try {
      setLoading(true);
      const { data, error } = await supabase
        .from('refunds')
        .select(`
          *,
          transaction:payment_transactions(
            amount,
            currency,
            payment_method,
            created_at
          )
        `)
        .eq('user_id', user?.id)
        .order('created_at', { ascending: false });

      if (error) throw error;

      setRefunds(data || []);
    } catch (error: any) {
      console.error('Error fetching refunds:', error);
      toast({
        title: "Error",
        description: "Failed to load refund history",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'successful':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'pending':
      case 'processing':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-gray-600" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'successful':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
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
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatRelativeTime = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
    return formatDate(dateString);
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Refund History</CardTitle>
          <CardDescription>Your refund requests and their status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Refund History</CardTitle>
            <CardDescription>Your refund requests and their status</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={fetchRefunds}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {refunds.length === 0 ? (
          <div className="text-center py-8">
            <ArrowLeft className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-muted-foreground mb-2">No Refunds Yet</h3>
            <p className="text-sm text-muted-foreground">
              You haven't requested any refunds yet. Refund requests will appear here once submitted.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {refunds.map((refund) => (
              <div key={refund.id} className="border rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(refund.status)}
                    <div>
                      <h4 className="font-medium">
                        {formatCurrency(refund.amount, refund.currency)} Refund
                      </h4>
                      <p className="text-sm text-muted-foreground">
                        Transaction: {refund.transaction_id.slice(-8)}
                      </p>
                    </div>
                  </div>
                  <Badge className={getStatusColor(refund.status)}>
                    {refund.status.charAt(0).toUpperCase() + refund.status.slice(1)}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm mb-3">
                  <div>
                    <span className="text-muted-foreground">Type:</span>
                    <span className="ml-2 font-medium capitalize">{refund.refund_type}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Requested:</span>
                    <span className="ml-2">{formatRelativeTime(refund.created_at)}</span>
                  </div>
                  {refund.processed_at && (
                    <div>
                      <span className="text-muted-foreground">Processed:</span>
                      <span className="ml-2">{formatRelativeTime(refund.processed_at)}</span>
                    </div>
                  )}
                  {refund.flw_refund_id && (
                    <div>
                      <span className="text-muted-foreground">Refund ID:</span>
                      <span className="ml-2 font-mono text-xs">{refund.flw_refund_id}</span>
                    </div>
                  )}
                </div>

                <div className="mb-3">
                  <span className="text-sm text-muted-foreground">Reason:</span>
                  <p className="text-sm mt-1">{refund.reason}</p>
                </div>

                {refund.error_message && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-start gap-2">
                      <XCircle className="h-4 w-4 text-red-600 mt-0.5" />
                      <div className="text-sm text-red-800">
                        <p className="font-medium">Error</p>
                        <p>{refund.error_message}</p>
                      </div>
                    </div>
                  </div>
                )}

                {refund.transaction && (
                  <div className="p-3 bg-muted/50 rounded-lg">
                    <h5 className="text-sm font-medium mb-2">Original Transaction</h5>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-muted-foreground">Amount:</span>
                        <span className="ml-2 font-medium">
                          {formatCurrency(refund.transaction.amount, refund.transaction.currency)}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Method:</span>
                        <span className="ml-2 capitalize">{refund.transaction.payment_method}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Date:</span>
                        <span className="ml-2">{formatDate(refund.transaction.created_at)}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default RefundHistory;
