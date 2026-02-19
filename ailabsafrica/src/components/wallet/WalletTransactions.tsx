import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { ArrowUpRight, ArrowDownLeft, Calendar, DollarSign, RefreshCw } from 'lucide-react';

interface Transaction {
  id: string;
  type: 'credit' | 'debit';
  amount: number;
  description: string;
  reference_id: string;
  reference_type: string;
  balance_before: number;
  balance_after: number;
  created_at: string;
}

interface WalletTransactionsProps {
  userId?: string;
}

const WalletTransactions = ({ userId }: WalletTransactionsProps) => {
  const { toast } = useToast();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (userId) {
      loadTransactions();
    }
  }, [userId]);

  const loadTransactions = async () => {
    if (!userId) return;
    
    setLoading(true);
    try {
      const { data, error } = await supabase
        .from('wallet_transactions')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })
        .limit(50);

      if (error) throw error;
      setTransactions(data || []);
    } catch (error: any) {
      console.error('Error loading transactions:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load transactions',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
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

  const getTransactionIcon = (type: 'credit' | 'debit') => {
    if (type === 'credit') {
      return <ArrowUpRight className="h-4 w-4 text-green-600" />;
    }
    return <ArrowDownLeft className="h-4 w-4 text-red-600" />;
  };

  const getTransactionBadge = (type: 'credit' | 'debit') => {
    if (type === 'credit') {
      return <Badge variant="default" className="bg-green-100 text-green-800">Credit</Badge>;
    }
    return <Badge variant="destructive">Debit</Badge>;
  };

  const getReferenceTypeLabel = (referenceType: string) => {
    switch (referenceType) {
      case 'bundle_purchase':
        return 'Bundle Purchase';
      case 'usage_tracking':
        return 'Usage';
      case 'manual_credit':
        return 'Manual Credit';
      case 'refund':
        return 'Refund';
      default:
        return referenceType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Transaction History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <DollarSign className="h-5 w-5" />
          Transaction History
        </CardTitle>
      </CardHeader>
      <CardContent>
        {transactions.length === 0 ? (
          <div className="text-center py-8">
            <DollarSign className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No transactions</h3>
            <p className="text-muted-foreground">
              Purchase a bundle or use your assistants to see transactions here.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {transactions.map((transaction) => (
              <div
                key={transaction.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-10 h-10 rounded-full bg-muted">
                    {getTransactionIcon(transaction.type)}
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold">{transaction.description}</h4>
                      {getTransactionBadge(transaction.type)}
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {formatDate(transaction.created_at)}
                      </div>
                      <div className="flex items-center gap-1">
                        <span>Type:</span>
                        <span className="font-medium">
                          {getReferenceTypeLabel(transaction.reference_type)}
                        </span>
                      </div>
                      {transaction.reference_id && (
                        <div className="flex items-center gap-1">
                          <span>Ref:</span>
                          <span className="font-mono text-xs">
                            {transaction.reference_id.slice(0, 8)}...
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className={`text-lg font-bold ${
                    transaction.type === 'credit' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {transaction.type === 'credit' ? '+' : '-'}${transaction.amount.toFixed(2)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Balance: ${transaction.balance_after.toFixed(2)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        
        {transactions.length > 0 && (
          <div className="mt-6 pt-4 border-t">
            <div className="flex justify-between items-center text-sm">
              <span className="text-muted-foreground">
                Showing {transactions.length} most recent transactions
              </span>
              <Button variant="outline" size="sm" onClick={loadTransactions}>
                <RefreshCw className="h-3 w-3 mr-1" />
                Refresh
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default WalletTransactions;
