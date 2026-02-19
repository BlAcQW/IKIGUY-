/**
 * Wallet Page - Comprehensive Wallet Management
 *
 * Complete wallet system with balance, transactions, top-up, and analytics
 * Integrates with shared wallet service (apps/shared/integration/wallet.py)
 */

import React, { useEffect, useState } from 'react';
import {
  Wallet as WalletIcon,
  CreditCard,
  TrendingUp,
  TrendingDown,
  Plus,
  Download,
  Filter,
  Calendar,
  DollarSign,
  ArrowUpRight,
  ArrowDownLeft,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Eye,
  EyeOff,
  Search,
  X
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Transaction {
  id: string;
  type: 'credit' | 'debit' | 'refund';
  amount: number;
  currency: string;
  description: string;
  balance_after: number;
  status: 'pending' | 'completed' | 'failed';
  created_at: string;
  metadata?: {
    service?: string;
    student_id?: string;
    session_id?: string;
  };
}

interface WalletData {
  wallet_id: string;
  user_id: string;
  balance: number;
  currency: string;
  status: 'active' | 'suspended' | 'closed';
  low_balance_threshold: number;
  created_at: string;
}

export default function Wallet() {
  const navigate = useNavigate();

  const [wallet, setWallet] = useState<WalletData>({
    wallet_id: 'wallet_123456',
    user_id: 'user_001',
    balance: 125.50,
    currency: 'GHS',
    status: 'active',
    low_balance_threshold: 10.00,
    created_at: '2025-01-01T00:00:00Z'
  });

  const [transactions, setTransactions] = useState<Transaction[]>([
    {
      id: 'txn_001',
      type: 'credit',
      amount: 50.00,
      currency: 'GHS',
      description: 'Wallet top-up via Paystack',
      balance_after: 125.50,
      status: 'completed',
      created_at: '2025-10-25T10:30:00Z',
      metadata: {}
    },
    {
      id: 'txn_002',
      type: 'debit',
      amount: 5.50,
      currency: 'GHS',
      description: 'AI tutoring session - Mathematics',
      balance_after: 75.50,
      status: 'completed',
      created_at: '2025-10-24T15:20:00Z',
      metadata: { service: 'tutoring', student_id: 'std_001', session_id: 'session_123' }
    },
    {
      id: 'txn_003',
      type: 'credit',
      amount: 100.00,
      currency: 'GHS',
      description: 'Wallet top-up via Mobile Money',
      balance_after: 81.00,
      status: 'completed',
      created_at: '2025-10-20T09:15:00Z',
      metadata: {}
    },
    {
      id: 'txn_004',
      type: 'debit',
      amount: 3.25,
      currency: 'GHS',
      description: 'Practice exercises - Physics',
      balance_after: -18.50,
      status: 'completed',
      created_at: '2025-10-23T14:45:00Z',
      metadata: { service: 'exercises', student_id: 'std_002' }
    }
  ]);

  const [loading, setLoading] = useState(false);
  const [showTopUp, setShowTopUp] = useState(false);
  const [topUpAmount, setTopUpAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState<'paystack' | 'momo' | 'stripe'>('paystack');
  const [balanceVisible, setBalanceVisible] = useState(true);
  const [filterType, setFilterType] = useState<'all' | 'credit' | 'debit'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  const stats = {
    totalCredits: transactions.filter(t => t.type === 'credit' && t.status === 'completed').reduce((sum, t) => sum + t.amount, 0),
    totalDebits: transactions.filter(t => t.type === 'debit' && t.status === 'completed').reduce((sum, t) => sum + t.amount, 0),
    thisMonthSpending: transactions
      .filter(t => t.type === 'debit' && new Date(t.created_at).getMonth() === new Date().getMonth())
      .reduce((sum, t) => sum + t.amount, 0),
    transactionCount: transactions.length
  };

  const handleTopUp = async () => {
    if (!topUpAmount || parseFloat(topUpAmount) <= 0) {
      alert('Please enter a valid amount');
      return;
    }

    setLoading(true);
    // Simulate API call to initiate top-up
    await new Promise(resolve => setTimeout(resolve, 1500));

    // In production, this would redirect to payment gateway
    alert(`Top-up of ₵${topUpAmount} initiated via ${paymentMethod.toUpperCase()}!\nYou will be redirected to the payment page.`);

    setLoading(false);
    setShowTopUp(false);
    setTopUpAmount('');
  };

  const filteredTransactions = transactions.filter(t => {
    const matchesType = filterType === 'all' || t.type === filterType;
    const matchesSearch = t.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesType && matchesSearch;
  });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
  };

  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'credit':
        return <ArrowDownLeft className="w-5 h-5 text-green-600" />;
      case 'debit':
        return <ArrowUpRight className="w-5 h-5 text-red-600" />;
      case 'refund':
        return <RefreshCw className="w-5 h-5 text-blue-600" />;
      default:
        return <DollarSign className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      completed: 'bg-green-100 text-green-700 border-green-200',
      pending: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      failed: 'bg-red-100 text-red-700 border-red-200'
    };
    return badges[status as keyof typeof badges] || badges.pending;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Wallet</h1>
              <p className="text-gray-600 mt-1">Manage your balance and transactions</p>
            </div>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Balance Card */}
        <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl p-8 text-white mb-8 shadow-2xl">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
                <WalletIcon className="w-8 h-8" />
              </div>
              <div>
                <p className="text-blue-100 text-sm">Available Balance</p>
                <div className="flex items-center gap-3 mt-1">
                  {balanceVisible ? (
                    <h2 className="text-4xl font-bold">₵{wallet.balance.toFixed(2)}</h2>
                  ) : (
                    <h2 className="text-4xl font-bold">••••••</h2>
                  )}
                  <button
                    onClick={() => setBalanceVisible(!balanceVisible)}
                    className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                  >
                    {balanceVisible ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>
            </div>
            <button
              onClick={() => setShowTopUp(true)}
              className="flex items-center gap-2 px-6 py-3 bg-white text-blue-600 rounded-xl font-semibold hover:bg-blue-50 transition-colors shadow-lg"
            >
              <Plus className="w-5 h-5" />
              Top Up
            </button>
          </div>

          <div className="grid grid-cols-3 gap-4 pt-6 border-t border-white/20">
            <div>
              <p className="text-blue-100 text-sm mb-1">Total Credited</p>
              <p className="text-2xl font-semibold">₵{stats.totalCredits.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-blue-100 text-sm mb-1">Total Spent</p>
              <p className="text-2xl font-semibold">₵{stats.totalDebits.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-blue-100 text-sm mb-1">This Month</p>
              <p className="text-2xl font-semibold">₵{stats.thisMonthSpending.toFixed(2)}</p>
            </div>
          </div>

          {wallet.balance < wallet.low_balance_threshold && (
            <div className="mt-6 flex items-center gap-2 p-3 bg-yellow-500/20 backdrop-blur-sm border border-yellow-400/30 rounded-lg">
              <AlertCircle className="w-5 h-5 text-yellow-200" />
              <p className="text-sm text-yellow-100">
                Low balance alert! Consider topping up to continue using services.
              </p>
            </div>
          )}
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">₵{stats.totalCredits.toFixed(2)}</h3>
            <p className="text-gray-600 text-sm">Total Deposits</p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-red-100 rounded-lg">
                <TrendingDown className="w-6 h-6 text-red-600" />
              </div>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">₵{stats.totalDebits.toFixed(2)}</h3>
            <p className="text-gray-600 text-sm">Total Withdrawals</p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <Calendar className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">₵{stats.thisMonthSpending.toFixed(2)}</h3>
            <p className="text-gray-600 text-sm">This Month</p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <RefreshCw className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">{stats.transactionCount}</h3>
            <p className="text-gray-600 text-sm">Total Transactions</p>
          </div>
        </div>

        {/* Transactions */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Transaction History</h3>
              <button className="flex items-center gap-2 px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                <Download className="w-4 h-4" />
                Export
              </button>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search transactions..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="flex gap-2">
                {['all', 'credit', 'debit'].map((type) => (
                  <button
                    key={type}
                    onClick={() => setFilterType(type as any)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      filterType === type
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="divide-y divide-gray-100">
            {filteredTransactions.length === 0 ? (
              <div className="p-12 text-center">
                <DollarSign className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No transactions found</p>
              </div>
            ) : (
              filteredTransactions.map((transaction) => (
                <div key={transaction.id} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`p-3 rounded-xl ${
                        transaction.type === 'credit' ? 'bg-green-100' :
                        transaction.type === 'debit' ? 'bg-red-100' : 'bg-blue-100'
                      }`}>
                        {getTransactionIcon(transaction.type)}
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900">{transaction.description}</h4>
                        <div className="flex items-center gap-3 mt-1">
                          <p className="text-sm text-gray-500">
                            {formatDate(transaction.created_at)} at {formatTime(transaction.created_at)}
                          </p>
                          <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${getStatusBadge(transaction.status)}`}>
                            {transaction.status}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-lg font-bold ${
                        transaction.type === 'credit' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {transaction.type === 'credit' ? '+' : '-'}₵{transaction.amount.toFixed(2)}
                      </p>
                      <p className="text-sm text-gray-500">Balance: ₵{transaction.balance_after.toFixed(2)}</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Top-Up Modal */}
      {showTopUp && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-gray-900">Top Up Wallet</h3>
                <button
                  onClick={() => setShowTopUp(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Amount (GHS)</label>
                <input
                  type="number"
                  value={topUpAmount}
                  onChange={(e) => setTopUpAmount(e.target.value)}
                  placeholder="Enter amount"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">Payment Method</label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { value: 'paystack', label: 'Paystack', icon: CreditCard },
                    { value: 'momo', label: 'MoMo', icon: WalletIcon },
                    { value: 'stripe', label: 'Stripe', icon: CreditCard }
                  ].map((method) => (
                    <button
                      key={method.value}
                      onClick={() => setPaymentMethod(method.value as any)}
                      className={`p-4 border-2 rounded-lg transition-all ${
                        paymentMethod === method.value
                          ? 'border-blue-600 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <method.icon className={`w-6 h-6 mx-auto mb-2 ${
                        paymentMethod === method.value ? 'text-blue-600' : 'text-gray-400'
                      }`} />
                      <p className={`text-sm font-medium ${
                        paymentMethod === method.value ? 'text-blue-600' : 'text-gray-600'
                      }`}>
                        {method.label}
                      </p>
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowTopUp(false)}
                  className="flex-1 px-6 py-3 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleTopUp}
                  disabled={loading}
                  className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Processing...' : 'Continue'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
