import React, { useEffect, useState } from 'react';
import { Plus, TrendingDown, TrendingUp, DollarSign, Lock } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardContent } from '../components/Card';
import { Button } from '../components/Button';
import { useStore } from '../lib/store';
import api from '../lib/api';
import { formatCurrency, formatDateTime } from '../lib/utils';
import type { Transaction } from '../types';

export const Wallet: React.FC = () => {
  const { wallet, setWallet, isAuthenticated } = useStore();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [topUpAmount, setTopUpAmount] = useState('');
  const [showTopUp, setShowTopUp] = useState(false);
  const [authRequired, setAuthRequired] = useState(false);

  useEffect(() => {
    loadWalletData();
  }, []);

  const loadWalletData = async () => {
    try {
      setLoading(true);
      const [walletRes, transactionsRes] = await Promise.all([
        api.wallet.getBalance(),
        api.wallet.getTransactions(1, 20),
      ]);
      setWallet(walletRes);
      // Ensure data is always an array
      setTransactions(Array.isArray(transactionsRes?.data) ? transactionsRes.data : []);
    } catch (error: any) {
      console.error('Error loading wallet:', error);
      // Check if it's an authentication error
      if (error?.response?.status === 403) {
        // Set special state to show login prompt
        setAuthRequired(true);
        setWallet(null);
        setTransactions([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleTopUp = async () => {
    try {
      const amount = parseFloat(topUpAmount);
      if (isNaN(amount) || amount <= 0) {
        alert('Please enter a valid amount');
        return;
      }
      const res = await api.wallet.topUp({
        amount,
        payment_method: 'paystack',
        callback_url: window.location.origin + '/wallet',
      });
      if (res.payment_url) {
        window.location.href = res.payment_url;
      }
    } catch (error) {
      console.error('Error initiating top-up:', error);
      alert('Failed to initiate top-up. Please try again.');
    }
  };

  // Ensure transactions is always an array
  const safeTransactions = Array.isArray(transactions) ? transactions : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  // Show login prompt if authentication is required
  if (authRequired || !isAuthenticated) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Wallet</h1>
          <p className="text-gray-600 mt-1">Manage your balance and transactions</p>
        </div>

        <Card className="text-center py-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-100 rounded-full mb-4">
            <Lock size={32} className="text-emerald-600" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Authentication Required</h3>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Please sign in to access your wallet, view transactions, and manage your EventFlow credits.
          </p>
          <Link to="/login">
            <Button>Sign In to Continue</Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Wallet</h1>
        <p className="text-gray-600 mt-1">Manage your balance and transactions</p>
      </div>

      {/* Balance Card */}
      <Card className="bg-gradient-to-br from-emerald-500 to-emerald-700 text-white">
        <div className="text-center py-6">
          <p className="text-sm opacity-90 mb-2">Available Balance</p>
          <p className="text-5xl font-bold mb-6">
            {wallet ? formatCurrency(wallet.balance, wallet.currency) : '₵0.00'}
          </p>
          <Button
            onClick={() => setShowTopUp(!showTopUp)}
            variant="secondary"
            icon={<Plus size={20} />}
          >
            Top Up
          </Button>
        </div>
      </Card>

      {/* Top Up Form */}
      {showTopUp && (
        <Card>
          <CardHeader title="Top Up Wallet" subtitle="Add credits to your wallet" />
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Amount (GHS)
                </label>
                <input
                  type="number"
                  value={topUpAmount}
                  onChange={(e) => setTopUpAmount(e.target.value)}
                  placeholder="Enter amount"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
              <div className="flex gap-2">
                {[10, 20, 50, 100].map((amount) => (
                  <button
                    key={amount}
                    onClick={() => setTopUpAmount(String(amount))}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm font-medium"
                  >
                    ₵{amount}
                  </button>
                ))}
              </div>
              <div className="flex gap-3">
                <Button onClick={handleTopUp} className="flex-1">
                  Continue to Payment
                </Button>
                <Button onClick={() => setShowTopUp(false)} variant="outline">
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Transaction History */}
      <Card>
        <CardHeader title="Transaction History" subtitle="Your recent transactions" />
        <CardContent>
          {safeTransactions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <DollarSign size={48} className="mx-auto mb-3 text-gray-300" />
              <p>No transactions yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {safeTransactions.map((txn) => (
                <div
                  key={txn.id}
                  className="flex items-center justify-between p-3 rounded-lg border border-gray-200"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-2 rounded-lg ${
                        txn.type === 'credit'
                          ? 'bg-green-100 text-green-600'
                          : 'bg-red-100 text-red-600'
                      }`}
                    >
                      {txn.type === 'credit' ? (
                        <TrendingUp size={20} />
                      ) : (
                        <TrendingDown size={20} />
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{txn.description}</p>
                      <p className="text-sm text-gray-600">{formatDateTime(txn.timestamp)}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p
                      className={`font-semibold ${
                        txn.type === 'credit' ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {txn.type === 'credit' ? '+' : '-'}
                      {formatCurrency(txn.amount, wallet?.currency)}
                    </p>
                    <p className="text-xs text-gray-600">
                      Balance: {formatCurrency(txn.balance_after, wallet?.currency)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
