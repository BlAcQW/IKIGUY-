/**
 * Giving Page - Member giving interface
 *
 * Allows members to make one-time or recurring donations.
 */

import React, { useState } from 'react';
import { Heart, CreditCard, Calendar, History, TrendingUp } from 'lucide-react';
import { useMyDonationHistory, useDonorProfile } from '../hooks/useGiving';
import DonationForm from '../components/giving/DonationForm';
import RecurringDonationForm from '../components/giving/RecurringDonationForm';
import DonorDashboard from '../components/giving/DonorDashboard';

type TabType = 'give-once' | 'give-recurring' | 'history' | 'dashboard';

export default function GivingPage() {
  const [activeTab, setActiveTab] = useState<TabType>('give-once');
  const token = localStorage.getItem('access_token');
  const organizationId = localStorage.getItem('current_organization_id');
  const isAuthenticated = !!token;

  // Only fetch user-specific data if authenticated
  const { data: donationHistory } = useMyDonationHistory(token || null, organizationId || null);
  const { data: donorProfile } = useDonorProfile(token || null, organizationId || null);

  // Show different tabs based on authentication
  const tabs = isAuthenticated
    ? [
        { id: 'give-once', label: 'Give Once', icon: Heart },
        { id: 'give-recurring', label: 'Give Recurring', icon: Calendar },
        { id: 'history', label: 'My Giving', icon: History },
        { id: 'dashboard', label: 'Dashboard', icon: TrendingUp },
      ]
    : [
        { id: 'give-once', label: 'Give Once', icon: Heart },
        { id: 'give-recurring', label: 'Give Recurring', icon: Calendar },
      ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex items-center space-x-4">
            <Heart className="h-12 w-12" />
            <div>
              <h1 className="text-4xl font-bold">Online Giving</h1>
              <p className="mt-2 text-blue-100">
                Thank you for your generosity and support
              </p>
            </div>
          </div>

          {/* Quick Stats */}
          {donorProfile && (
            <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                <div className="text-blue-100 text-sm">Total Given</div>
                <div className="text-2xl font-bold">
                  ${donorProfile.total_donated.toFixed(2)}
                </div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                <div className="text-blue-100 text-sm">Donations</div>
                <div className="text-2xl font-bold">
                  {donorProfile.donation_count}
                </div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                <div className="text-blue-100 text-sm">Average Gift</div>
                <div className="text-2xl font-bold">
                  ${donorProfile.average_donation.toFixed(2)}
                </div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                <div className="text-blue-100 text-sm">Recurring Gifts</div>
                <div className="text-2xl font-bold">
                  {donorProfile.active_recurring_count}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200 -mt-4">
          <nav className="flex space-x-8 bg-white rounded-t-lg px-6" aria-label="Tabs">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as TabType)}
                  className={`
                    flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm
                    ${
                      isActive
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="h-5 w-5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="py-8">
          {activeTab === 'give-once' && (
            <div className="max-w-2xl mx-auto">
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center space-x-3 mb-6">
                  <CreditCard className="h-6 w-6 text-blue-600" />
                  <h2 className="text-2xl font-bold text-gray-900">
                    Make a One-Time Donation
                  </h2>
                </div>
                <p className="text-gray-600 mb-6">
                  Your generous gift helps us continue our mission and impact lives.
                </p>
                <DonationForm />
              </div>
            </div>
          )}

          {activeTab === 'give-recurring' && (
            <div className="max-w-2xl mx-auto">
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center space-x-3 mb-6">
                  <Calendar className="h-6 w-6 text-purple-600" />
                  <h2 className="text-2xl font-bold text-gray-900">
                    Set Up Recurring Giving
                  </h2>
                </div>
                <p className="text-gray-600 mb-6">
                  Make a lasting impact with automatic recurring donations.
                </p>
                <RecurringDonationForm />
              </div>
            </div>
          )}

          {activeTab === 'history' && isAuthenticated && (
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-bold text-gray-900">
                  My Donation History
                </h2>
              </div>
              <div className="overflow-x-auto">
                {donationHistory && donationHistory.donations.length > 0 ? (
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Amount
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Type
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Category
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Receipt
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {donationHistory.donations.map((donation) => (
                        <tr key={donation._id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {new Date(donation.created_at).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            ${donation.amount.toFixed(2)} {donation.currency}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {donation.donation_type.replace('_', ' ')}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {donation.category}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span
                              className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                donation.status === 'completed'
                                  ? 'bg-green-100 text-green-800'
                                  : donation.status === 'pending'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-red-100 text-red-800'
                              }`}
                            >
                              {donation.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {donation.receipt_url ? (
                              <a
                                href={donation.receipt_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:text-blue-800"
                              >
                                Download
                              </a>
                            ) : (
                              <span className="text-gray-400">N/A</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="text-center py-12">
                    <History className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">
                      No donations yet
                    </h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Get started by making your first donation.
                    </p>
                    <div className="mt-6">
                      <button
                        onClick={() => setActiveTab('give-once')}
                        className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                      >
                        <Heart className="h-5 w-5 mr-2" />
                        Give Now
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'dashboard' && isAuthenticated && <DonorDashboard />}
          {activeTab === 'history' && !isAuthenticated && (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <History className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">
                Sign in to view your donation history
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Please sign in to access your giving history and dashboard.
              </p>
              <div className="mt-6">
                <a
                  href="/login"
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  Sign In
                </a>
              </div>
            </div>
          )}
          {activeTab === 'dashboard' && !isAuthenticated && (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <TrendingUp className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">
                Sign in to view your donor dashboard
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Please sign in to access your giving dashboard and statistics.
              </p>
              <div className="mt-6">
                <a
                  href="/login"
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  Sign In
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
