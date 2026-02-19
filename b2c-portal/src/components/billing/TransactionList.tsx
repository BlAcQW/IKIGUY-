import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { WalletTransaction } from '@/lib/core-api';
import {
  Download,
  CheckCircle,
  XCircle,
  Clock,
  Search,
  Filter,
  Receipt,
  Loader2,
  ArrowUpRight,
  ArrowDownLeft
} from 'lucide-react';

interface TransactionListProps {
  transactions: WalletTransaction[];
  isLoading: boolean;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  statusFilter: string;
  setStatusFilter: (status: string) => void;
  typeFilter: string;
  setTypeFilter: (type: string) => void;
}

export const TransactionList: React.FC<TransactionListProps> = ({
  transactions,
  isLoading,
  searchQuery,
  setSearchQuery,
  statusFilter,
  setStatusFilter,
  typeFilter,
  setTypeFilter,
}) => {
  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
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

  const getStatusColor = (status: string) => {
    const statusLower = status.toLowerCase();
    switch (statusLower) {
      case 'completed':
      case 'success':
        return 'bg-green-500/20 text-green-600 border-green-500/30';
      case 'pending':
      case 'processing':
        return 'bg-yellow-500/20 text-yellow-600 border-yellow-500/30';
      case 'failed':
      case 'cancelled':
        return 'bg-red-500/20 text-red-600 border-red-500/30';
      default:
        return 'bg-gray-500/20 text-gray-600 border-gray-500/30';
    }
  };

  const getStatusIcon = (status: string) => {
    const statusLower = status.toLowerCase();
    switch (statusLower) {
      case 'completed':
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'pending':
      case 'processing':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      case 'failed':
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getTransactionIcon = (type: string) => {
    const typeLower = type.toLowerCase();
    if (typeLower.includes('deposit') || typeLower.includes('credit')) {
      return <ArrowDownLeft className="h-5 w-5 text-green-600" />;
    } else if (typeLower.includes('withdrawal') || typeLower.includes('debit') || typeLower.includes('charge')) {
      return <ArrowUpRight className="h-5 w-5 text-red-600" />;
    }
    return <Receipt className="h-5 w-5 text-gray-600" />;
  };

  const downloadTransaction = async (transaction: WalletTransaction) => {
    try {
      // Download PDF receipt from API
      const response = await fetch(
        `https://flow-api.ailabsafrica.com/api/wallet/transactions/${transaction.id}/receipt`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to download receipt');
      }

      // Get PDF blob
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `receipt_${transaction.id.slice(0, 8)}_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download receipt:', error);
      // Fallback to JSON download
      const txData = {
        transaction,
        downloadDate: new Date().toISOString()
      };

      const blob = new Blob([JSON.stringify(txData, null, 2)], {
        type: 'application/json'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `transaction_${transaction.id}_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between mb-4">
          <div>
            <CardTitle>Transaction History</CardTitle>
            <CardDescription>View and filter your wallet transactions</CardDescription>
          </div>
          <Badge variant="secondary" className="text-sm">
            {transactions.length} total
          </Badge>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search transactions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>

          {/* Status Filter */}
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger>
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
            </SelectContent>
          </Select>

          {/* Type Filter */}
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger>
              <SelectValue placeholder="Filter by type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="deposit">Deposits</SelectItem>
              <SelectItem value="withdrawal">Withdrawals</SelectItem>
              <SelectItem value="charge">Charges</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
          </div>
        ) : transactions.length === 0 ? (
          <div className="text-center py-12">
            <Receipt className="h-12 w-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">No transactions found</p>
            <p className="text-sm text-gray-500 mt-1">Your transaction history will appear here</p>
          </div>
        ) : (
          <div className="space-y-3">
            {transactions.map((tx) => (
              <div
                key={tx.id}
                className="border rounded-lg p-4 hover:bg-secondary/30 transition-colors"
              >
                <div className="flex items-start justify-between">
                  {/* Left: Icon and Details */}
                  <div className="flex items-start gap-3 flex-1">
                    <div className="mt-1">
                      {getTransactionIcon(tx.transaction_type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-semibold">{tx.description}</h4>
                        {getStatusIcon(tx.status)}
                        <Badge className={`${getStatusColor(tx.status)} border text-xs`}>
                          {tx.status}
                        </Badge>
                      </div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <p>
                          ID: <span className="font-mono text-xs">{tx.id.slice(0, 16)}...</span>
                        </p>
                        {tx.payment_method_display && (
                          <p>Payment method: {tx.payment_method_display}</p>
                        )}
                        <p>Created: {formatDate(tx.created_at)}</p>
                        {tx.completed_at && (
                          <p>Completed: {formatDate(tx.completed_at)}</p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Right: Amount and Actions */}
                  <div className="text-right">
                    <div className="text-xl font-bold mb-1">
                      {formatCurrency(tx.amount, tx.currency)}
                    </div>
                    {tx.processing_fee > 0 && (
                      <div className="text-xs text-gray-500 mb-2">
                        Fee: {formatCurrency(tx.processing_fee, tx.currency)}
                      </div>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => downloadTransaction(tx)}
                    >
                      <Download className="h-3 w-3 mr-1" />
                      Receipt
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TransactionList;
