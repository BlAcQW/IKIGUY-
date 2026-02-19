/**
 * Organization Billing Page
 *
 * Manage organization wallet, billing history, and payment methods.
 */

import React, { useState, useEffect } from 'react';
import { encodeHeaderValue } from '../../lib/header-utils';
import {
  Wallet,
  CreditCard,
  Download,
  Plus,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Calendar,
  FileText,
  AlertCircle,
  CheckCircle,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw
} from 'lucide-react';

interface Transaction {
  id: string;
  type: 'credit' | 'debit';
  amount: number;
  currency: string;
  description: string;
  created_at: string;
  status: 'completed' | 'pending' | 'failed';
}

interface Invoice {
  id: string;
  invoice_number: string;
  amount: number;
  currency: string;
  status: 'paid' | 'unpaid' | 'overdue';
  issue_date: string;
  due_date: string;
  pdf_url?: string;
}

interface UsageStats {
  current_period: {
    start_date: string;
    end_date: string;
    total_cost: number;
    services: {
      [key: string]: {
        count: number;
        cost: number;
      };
    };
  };
}

interface OrganizationBillingProps {
  organizationId: string;
  apiBaseUrl: string;
  onError?: (error: string) => void;
}

export default function OrganizationBilling({
  organizationId,
  apiBaseUrl,
  onError
}: OrganizationBillingProps) {
  const [balance, setBalance] = useState(0);
  const [currency, setCurrency] = useState('USD');
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'transactions' | 'invoices' | 'usage'>('overview');
  const [showAddFundsModal, setShowAddFundsModal] = useState(false);

  useEffect(() => {
    loadBillingData();
  }, [organizationId]);

  const loadBillingData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');

      // Load wallet balance
      const walletResponse = await fetch(`${apiBaseUrl}/api/v1/organizations/${organizationId}/wallet`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Organization-ID': encodeHeaderValue(organizationId) || ''
        }
      });

      if (walletResponse.ok) {
        const walletData = await walletResponse.json();
        setBalance(walletData.balance || 0);
        setCurrency(walletData.currency || 'USD');
      }

      // Load transactions
      const transactionsResponse = await fetch(
        `${apiBaseUrl}/api/v1/organizations/${organizationId}/transactions?limit=50`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Organization-ID': encodeHeaderValue(organizationId) || ''
          }
        }
      );

      if (transactionsResponse.ok) {
        const transactionsData = await transactionsResponse.json();
        setTransactions(transactionsData.transactions || []);
      }

      // Load usage stats
      const usageResponse = await fetch(
        `${apiBaseUrl}/api/v1/organizations/${organizationId}/usage?period=month`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Organization-ID': encodeHeaderValue(organizationId) || ''
          }
        }
      );

      if (usageResponse.ok) {
        const usageData = await usageResponse.json();
        setUsageStats(usageData);
      }
    } catch (error) {
      onError?.('Failed to load billing data');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'paid':
        return 'bg-green-100 text-green-800';
      case 'pending':
      case 'unpaid':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
      case 'overdue':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const AddFundsModal = () => {
    const [amount, setAmount] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${apiBaseUrl}/api/v1/organizations/${organizationId}/wallet/add-funds`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'X-Organization-ID': encodeHeaderValue(organizationId) || ''
          },
          body: JSON.stringify({ amount: parseFloat(amount) })
        });

        if (!response.ok) throw new Error('Failed to add funds');

        await loadBillingData();
        setShowAddFundsModal(false);
        setAmount('');
      } catch (error) {
        onError?.('Failed to add funds');
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">Add Funds</h2>
            <p className="text-sm text-gray-600 mt-1">Top up your organization wallet</p>
          </div>
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Amount ({currency})
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="number"
                  step="0.01"
                  min="1"
                  required
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 text-lg border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0.00"
                />
              </div>
            </div>

            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-900">
                <strong>Note:</strong> Funds will be added to your organization wallet and can be used for all services.
              </p>
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowAddFundsModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Add Funds
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading billing data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Billing & Usage</h1>
          <p className="text-gray-600 mt-1">Manage your organization's billing and view usage statistics</p>
        </div>
        <button
          onClick={() => setShowAddFundsModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Add Funds
        </button>
      </div>

      {/* Balance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center justify-between mb-4">
            <Wallet className="w-8 h-8 opacity-80" />
            <RefreshCw className="w-5 h-5 opacity-60 cursor-pointer hover:opacity-100 transition-opacity" onClick={loadBillingData} />
          </div>
          <p className="text-blue-100 text-sm mb-1">Current Balance</p>
          <p className="text-3xl font-bold">{formatCurrency(balance)}</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">This Month</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(usageStats?.current_period?.total_cost || 0)}
              </p>
            </div>
          </div>
          <p className="text-xs text-gray-500">Total usage this billing period</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <FileText className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Invoices</p>
              <p className="text-2xl font-bold text-gray-900">{invoices.length}</p>
            </div>
          </div>
          <p className="text-xs text-gray-500">
            {invoices.filter(i => i.status === 'unpaid').length} pending
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <div className="flex">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === 'overview'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('transactions')}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === 'transactions'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Transactions
            </button>
            <button
              onClick={() => setActiveTab('invoices')}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === 'invoices'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Invoices
            </button>
            <button
              onClick={() => setActiveTab('usage')}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === 'usage'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Usage
            </button>
          </div>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Stats</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600">Total Spent</p>
                        <p className="text-2xl font-bold text-gray-900 mt-1">
                          {formatCurrency(transactions.filter(t => t.type === 'debit').reduce((sum, t) => sum + t.amount, 0))}
                        </p>
                      </div>
                      <ArrowDownRight className="w-8 h-8 text-red-500" />
                    </div>
                  </div>

                  <div className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600">Total Added</p>
                        <p className="text-2xl font-bold text-gray-900 mt-1">
                          {formatCurrency(transactions.filter(t => t.type === 'credit').reduce((sum, t) => sum + t.amount, 0))}
                        </p>
                      </div>
                      <ArrowUpRight className="w-8 h-8 text-green-500" />
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Transactions</h3>
                <div className="space-y-2">
                  {transactions.slice(0, 5).map((transaction) => (
                    <div key={transaction.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                          transaction.type === 'credit' ? 'bg-green-100' : 'bg-red-100'
                        }`}>
                          {transaction.type === 'credit' ? (
                            <ArrowUpRight className="w-5 h-5 text-green-600" />
                          ) : (
                            <ArrowDownRight className="w-5 h-5 text-red-600" />
                          )}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{transaction.description}</p>
                          <p className="text-sm text-gray-600">{formatDate(transaction.created_at)}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`font-semibold ${
                          transaction.type === 'credit' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {transaction.type === 'credit' ? '+' : '-'}
                          {formatCurrency(transaction.amount)}
                        </p>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(transaction.status)}`}>
                          {transaction.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Transactions Tab */}
          {activeTab === 'transactions' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">All Transactions</h3>
                <button className="flex items-center gap-2 px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                  <Download className="w-4 h-4" />
                  Export CSV
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900">Date</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900">Description</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900">Type</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-900">Status</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-900">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {transactions.map((transaction) => (
                      <tr key={transaction.id} className="hover:bg-gray-50 transition-colors">
                        <td className="py-3 px-4 text-sm text-gray-900">{formatDate(transaction.created_at)}</td>
                        <td className="py-3 px-4 text-sm text-gray-900">{transaction.description}</td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            transaction.type === 'credit' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {transaction.type}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(transaction.status)}`}>
                            {transaction.status}
                          </span>
                        </td>
                        <td className={`py-3 px-4 text-right font-semibold ${
                          transaction.type === 'credit' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {transaction.type === 'credit' ? '+' : '-'}
                          {formatCurrency(transaction.amount)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Invoices Tab */}
          {activeTab === 'invoices' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Invoices</h3>
              {invoices.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No invoices available</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {invoices.map((invoice) => (
                    <div key={invoice.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                          <FileText className="w-5 h-5 text-gray-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{invoice.invoice_number}</p>
                          <p className="text-sm text-gray-600">Due {formatDate(invoice.due_date)}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="font-semibold text-gray-900">{formatCurrency(invoice.amount)}</p>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(invoice.status)}`}>
                            {invoice.status}
                          </span>
                        </div>
                        {invoice.pdf_url && (
                          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                            <Download className="w-5 h-5 text-gray-600" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Usage Tab */}
          {activeTab === 'usage' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Billing Period</h3>
                {usageStats?.current_period && (
                  <div className="p-4 bg-gray-50 rounded-lg mb-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Calendar className="w-4 h-4" />
                        {formatDate(usageStats.current_period.start_date)} - {formatDate(usageStats.current_period.end_date)}
                      </div>
                      <p className="text-lg font-bold text-gray-900">
                        {formatCurrency(usageStats.current_period.total_cost)}
                      </p>
                    </div>
                  </div>
                )}

                <div className="space-y-3">
                  {usageStats?.current_period?.services && Object.entries(usageStats.current_period.services).map(([service, data]) => (
                    <div key={service} className="p-4 border border-gray-200 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900 capitalize">{service.replace('_', ' ')}</h4>
                        <p className="font-semibold text-gray-900">{formatCurrency(data.cost)}</p>
                      </div>
                      <div className="flex items-center justify-between text-sm text-gray-600">
                        <span>{data.count.toLocaleString()} requests</span>
                        <span>{data.count > 0 ? formatCurrency(data.cost / data.count) : '$0.00'} per request</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Add Funds Modal */}
      {showAddFundsModal && <AddFundsModal />}
    </div>
  );
}
