/**
 * Subscription Billing Component - ChurchFlow SaaS
 *
 * Displays current subscription plan, usage metrics, billing history,
 * and allows plan upgrades/downgrades.
 */

import React, { useState, useEffect } from 'react';
import {
  CreditCard,
  TrendingUp,
  Users,
  MessageSquare,
  HardDrive,
  Calendar,
  Download,
  AlertCircle,
  CheckCircle,
  ArrowUpRight,
  Crown,
  Zap,
  Shield
} from 'lucide-react';
import { ResponsiveTable } from '../common';
import { encodeHeaderValue } from '../../lib/header-utils';

interface Subscription {
  organization_id: string;
  plan: 'free' | 'standard' | 'premium';
  status: string;
  current_period_start: string;
  current_period_end: string;
  stripe_customer_id?: string;
  stripe_subscription_id?: string;
  trial_end?: string;
  canceled_at?: string;
}

interface UsageMetrics {
  organization_id: string;
  current_plan: string;
  members_count: number;
  members_limit: number;
  sms_credits: number;
  sms_limit: number | null;
  storage_mb: number;
  storage_limit_mb: number | null;
  billing_period_start: string;
  billing_period_end: string;
}

interface Invoice {
  id: string;
  amount: number;
  currency: string;
  status: string;
  invoice_pdf: string | null;
  created_at: string;
  paid_at: string | null;
}

interface SubscriptionBillingProps {
  organizationId: string;
  apiBaseUrl: string;
  onError?: (error: string) => void;
}

const PLAN_DETAILS = {
  free: {
    name: 'Free',
    price: 0,
    icon: Shield,
    color: 'text-gray-600',
    bgColor: 'bg-gray-100',
    features: [
      'Up to 100 members',
      '100 SMS credits/month',
      'Events & Check-in',
      'Basic features'
    ]
  },
  standard: {
    name: 'Standard',
    price: 49,
    icon: Zap,
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
    features: [
      'Up to 500 members',
      '500 SMS credits/month',
      'Events & Check-in',
      'Giving & Volunteers',
      'Email support'
    ]
  },
  premium: {
    name: 'Premium',
    price: 99,
    icon: Crown,
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
    features: [
      'Unlimited members',
      '2000 SMS credits/month',
      'All features',
      'AI Analytics',
      'Priority support',
      'Custom branding'
    ]
  }
};

export default function SubscriptionBilling({
  organizationId,
  apiBaseUrl,
  onError
}: SubscriptionBillingProps) {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<UsageMetrics | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'usage' | 'invoices' | 'upgrade'>('overview');
  const [upgrading, setUpgrading] = useState(false);

  useEffect(() => {
    loadSubscriptionData();
  }, [organizationId]);

  const loadSubscriptionData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || ''
      };

      // Load subscription
      const subResponse = await fetch(
        `${apiBaseUrl}/api/v1/billing/subscriptions/${organizationId}`,
        { headers }
      );

      if (subResponse.ok) {
        const subData = await subResponse.json();
        setSubscription(subData);
      }

      // Load usage
      const usageResponse = await fetch(
        `${apiBaseUrl}/api/v1/billing/usage/${organizationId}`,
        { headers }
      );

      if (usageResponse.ok) {
        const usageData = await usageResponse.json();
        setUsage(usageData);
      }

      // Load invoices
      const invoicesResponse = await fetch(
        `${apiBaseUrl}/api/v1/billing/invoices/${organizationId}`,
        { headers }
      );

      if (invoicesResponse.ok) {
        const invoicesData = await invoicesResponse.json();
        setInvoices(invoicesData);
      }

    } catch (error) {
      console.error('Failed to load subscription data:', error);
      onError?.('Failed to load subscription information');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (newPlan: 'standard' | 'premium') => {
    try {
      setUpgrading(true);
      const token = localStorage.getItem('access_token');

      const response = await fetch(
        `${apiBaseUrl}/api/v1/billing/subscriptions/${organizationId}/plan`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Organization-ID': encodeHeaderValue(organizationId) || '',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ new_plan: newPlan })
        }
      );

      if (response.ok) {
        await loadSubscriptionData();
        alert(`Successfully upgraded to ${PLAN_DETAILS[newPlan].name} plan!`);
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to upgrade plan');
      }
    } catch (error: any) {
      console.error('Failed to upgrade:', error);
      alert(`Failed to upgrade: ${error.message}`);
    } finally {
      setUpgrading(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription? It will remain active until the end of the billing period.')) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');

      const response = await fetch(
        `${apiBaseUrl}/api/v1/billing/subscriptions/${organizationId}/cancel`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Organization-ID': encodeHeaderValue(organizationId) || ''
          }
        }
      );

      if (response.ok) {
        await loadSubscriptionData();
        alert('Subscription cancelled. It will remain active until the end of the billing period.');
      } else {
        throw new Error('Failed to cancel subscription');
      }
    } catch (error) {
      console.error('Failed to cancel:', error);
      alert('Failed to cancel subscription');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const currentPlan = subscription?.plan || 'free';
  const PlanIcon = PLAN_DETAILS[currentPlan].icon;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Billing & Subscription</h1>
        <p className="mt-2 text-gray-600">Manage your ChurchFlow subscription and billing</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { key: 'overview', label: 'Overview' },
            { key: 'usage', label: 'Usage' },
            { key: 'invoices', label: 'Invoices' },
            { key: 'upgrade', label: 'Plans' }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Current Plan Card */}
          <div className={`rounded-lg p-6 ${PLAN_DETAILS[currentPlan].bgColor}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className={`p-3 rounded-full bg-white`}>
                  <PlanIcon className={`h-8 w-8 ${PLAN_DETAILS[currentPlan].color}`} />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {PLAN_DETAILS[currentPlan].name} Plan
                  </h2>
                  <p className="text-gray-600">
                    ${PLAN_DETAILS[currentPlan].price}/month
                  </p>
                </div>
              </div>
              {currentPlan !== 'premium' && (
                <button
                  onClick={() => setActiveTab('upgrade')}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
                >
                  Upgrade Plan
                </button>
              )}
            </div>

            {/* Subscription Status */}
            <div className="mt-6 flex items-center space-x-2">
              {subscription?.status === 'active' && (
                <>
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="text-green-600 font-medium">Active</span>
                </>
              )}
              {subscription?.status === 'trialing' && (
                <>
                  <AlertCircle className="h-5 w-5 text-blue-600" />
                  <span className="text-blue-600 font-medium">
                    Trial (ends {subscription.trial_end ? new Date(subscription.trial_end).toLocaleDateString() : 'soon'})
                  </span>
                </>
              )}
              {subscription?.status === 'canceled' && (
                <>
                  <AlertCircle className="h-5 w-5 text-orange-600" />
                  <span className="text-orange-600 font-medium">
                    Cancelled (active until {subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : 'period end'})
                  </span>
                </>
              )}
              {subscription?.current_period_end && (
                <span className="text-gray-600 ml-4">
                  • Renews on {new Date(subscription.current_period_end).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>

          {/* Usage Summary Cards */}
          {usage && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <Users className="h-8 w-8 text-blue-600" />
                  <span className="text-sm text-gray-500">Members</span>
                </div>
                <div className="mt-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {usage.members_count} / {usage.members_limit === -1 ? '∞' : usage.members_limit}
                  </div>
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{
                        width: usage.members_limit === -1
                          ? '0%'
                          : `${Math.min(100, (usage.members_count / usage.members_limit) * 100)}%`
                      }}
                    />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <MessageSquare className="h-8 w-8 text-green-600" />
                  <span className="text-sm text-gray-500">SMS Credits</span>
                </div>
                <div className="mt-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {usage.sms_credits} / {usage.sms_limit === null ? '∞' : usage.sms_limit}
                  </div>
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{
                        width: usage.sms_limit === null
                          ? '0%'
                          : `${Math.min(100, (usage.sms_credits / usage.sms_limit) * 100)}%`
                      }}
                    />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <HardDrive className="h-8 w-8 text-purple-600" />
                  <span className="text-sm text-gray-500">Storage</span>
                </div>
                <div className="mt-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {(usage.storage_mb / 1024).toFixed(2)} GB
                  </div>
                  <div className="mt-2 text-sm text-gray-500">
                    {usage.storage_limit_mb === null ? 'Unlimited' : `of ${(usage.storage_limit_mb / 1024).toFixed(0)} GB`}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Billing Actions</h3>
            <div className="space-y-3">
              {subscription?.status === 'canceled' && (
                <button className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
                  Reactivate Subscription
                </button>
              )}
              {subscription?.status === 'active' && currentPlan !== 'free' && (
                <button
                  onClick={handleCancelSubscription}
                  className="w-full py-3 px-4 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 font-medium"
                >
                  Cancel Subscription
                </button>
              )}
              <button
                onClick={() => setActiveTab('upgrade')}
                className="w-full py-3 px-4 bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 font-medium"
              >
                View All Plans
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Usage Tab */}
      {activeTab === 'usage' && usage && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Usage Period: {new Date(usage.billing_period_start).toLocaleDateString()} - {new Date(usage.billing_period_end).toLocaleDateString()}
            </h3>

            <div className="space-y-6">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-700 font-medium">Members</span>
                  <span className="text-gray-900 font-semibold">
                    {usage.members_count} / {usage.members_limit === -1 ? 'Unlimited' : usage.members_limit}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-blue-600 h-3 rounded-full transition-all"
                    style={{
                      width: usage.members_limit === -1
                        ? '0%'
                        : `${Math.min(100, (usage.members_count / usage.members_limit) * 100)}%`
                    }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-700 font-medium">SMS Credits</span>
                  <span className="text-gray-900 font-semibold">
                    {usage.sms_credits} / {usage.sms_limit === null ? 'Unlimited' : usage.sms_limit}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-green-600 h-3 rounded-full transition-all"
                    style={{
                      width: usage.sms_limit === null
                        ? '0%'
                        : `${Math.min(100, (usage.sms_credits / usage.sms_limit) * 100)}%`
                    }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-700 font-medium">Storage</span>
                  <span className="text-gray-900 font-semibold">
                    {(usage.storage_mb / 1024).toFixed(2)} GB
                    {usage.storage_limit_mb !== null && ` / ${(usage.storage_limit_mb / 1024).toFixed(0)} GB`}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-purple-600 h-3 rounded-full transition-all"
                    style={{
                      width: usage.storage_limit_mb === null
                        ? '5%'
                        : `${Math.min(100, (usage.storage_mb / usage.storage_limit_mb) * 100)}%`
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Invoices Tab */}
      {activeTab === 'invoices' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Billing History</h3>
          </div>
          <ResponsiveTable
            columns={[
              {
                key: 'created_at',
                label: 'Date',
                render: (value) => new Date(value).toLocaleDateString(),
              },
              {
                key: 'amount',
                label: 'Amount',
                render: (value, invoice) => `$${invoice.amount.toFixed(2)} ${invoice.currency.toUpperCase()}`,
              },
              {
                key: 'status',
                label: 'Status',
                render: (value) => (
                  <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    value === 'paid'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {value}
                  </span>
                ),
              },
              {
                key: 'invoice_pdf',
                label: 'Invoice',
                render: (value) =>
                  value ? (
                    <a
                      href={value}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 flex items-center"
                    >
                      <Download className="h-4 w-4 mr-1" />
                      Download
                    </a>
                  ) : (
                    <span className="text-gray-400">N/A</span>
                  ),
              },
            ]}
            data={invoices}
            keyField="id"
            emptyMessage="No invoices yet"
          />
        </div>
      )}

      {/* Upgrade Tab */}
      {activeTab === 'upgrade' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {(['free', 'standard', 'premium'] as const).map((plan) => {
            const PlanIcon = PLAN_DETAILS[plan].icon;
            const isCurrentPlan = currentPlan === plan;
            const canUpgrade =
              (currentPlan === 'free' && (plan === 'standard' || plan === 'premium')) ||
              (currentPlan === 'standard' && plan === 'premium');

            return (
              <div
                key={plan}
                className={`rounded-lg p-6 ${
                  isCurrentPlan
                    ? 'border-2 border-blue-500 bg-blue-50'
                    : 'border border-gray-200 bg-white'
                } shadow-lg`}
              >
                <div className={`p-3 rounded-full ${PLAN_DETAILS[plan].bgColor} inline-block`}>
                  <PlanIcon className={`h-8 w-8 ${PLAN_DETAILS[plan].color}`} />
                </div>
                <h3 className="mt-4 text-2xl font-bold text-gray-900">
                  {PLAN_DETAILS[plan].name}
                </h3>
                <div className="mt-2 text-4xl font-extrabold text-gray-900">
                  ${PLAN_DETAILS[plan].price}
                  <span className="text-lg font-normal text-gray-600">/month</span>
                </div>

                <ul className="mt-6 space-y-3">
                  {PLAN_DETAILS[plan].features.map((feature, idx) => (
                    <li key={idx} className="flex items-start">
                      <CheckCircle className="h-5 w-5 text-green-500 mr-2 flex-shrink-0" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => canUpgrade && handleUpgrade(plan as 'standard' | 'premium')}
                  disabled={!canUpgrade || upgrading}
                  className={`mt-8 w-full py-3 px-4 rounded-lg font-medium ${
                    isCurrentPlan
                      ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                      : canUpgrade
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  {isCurrentPlan
                    ? 'Current Plan'
                    : canUpgrade
                    ? upgrading ? 'Upgrading...' : 'Upgrade Now'
                    : 'Not Available'}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
