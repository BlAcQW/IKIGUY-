/**
 * Donor Dashboard Component
 *
 * Shows donor giving statistics and insights.
 */

import React from 'react';
import { TrendingUp, Heart, Calendar, Award, DollarSign } from 'lucide-react';
import { useDonorProfile, useMyDonationHistory, useMyRecurringDonations } from '../../hooks/useGiving';

export default function DonorDashboard() {
  const token = localStorage.getItem('access_token');
  const organizationId = localStorage.getItem('current_organization_id');

  const { data: donorProfile, isLoading: profileLoading } = useDonorProfile(token, organizationId);
  const { data: donationHistory } = useMyDonationHistory(token, organizationId);
  const { data: recurringDonations } = useMyRecurringDonations(token, organizationId);

  if (profileLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (!donorProfile) {
    return (
      <div className="text-center py-12">
        <Heart className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No giving history yet</h3>
        <p className="mt-1 text-sm text-gray-500">
          Start giving to see your donor dashboard.
        </p>
      </div>
    );
  }

  const recentDonations = donationHistory?.donations.slice(0, 5) || [];
  const activeRecurring = recurringDonations?.recurring_donations || [];

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm">Lifetime Giving</p>
              <p className="text-3xl font-bold mt-1">
                ${donorProfile.total_donated.toFixed(2)}
              </p>
            </div>
            <DollarSign className="h-12 w-12 text-blue-200" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-sm">Total Donations</p>
              <p className="text-3xl font-bold mt-1">{donorProfile.donation_count}</p>
            </div>
            <Heart className="h-12 w-12 text-purple-200" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm">Average Gift</p>
              <p className="text-3xl font-bold mt-1">
                ${donorProfile.average_donation.toFixed(2)}
              </p>
            </div>
            <TrendingUp className="h-12 w-12 text-green-200" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-100 text-sm">Largest Gift</p>
              <p className="text-3xl font-bold mt-1">
                ${donorProfile.largest_donation.toFixed(2)}
              </p>
            </div>
            <Award className="h-12 w-12 text-orange-200" />
          </div>
        </div>
      </div>

      {/* Giving History */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Donations */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Donations</h3>
          </div>
          <div className="p-6">
            {recentDonations.length > 0 ? (
              <div className="space-y-4">
                {recentDonations.map((donation) => (
                  <div
                    key={donation._id}
                    className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0"
                  >
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {donation.category}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(donation.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-gray-900">
                        ${donation.amount.toFixed(2)}
                      </p>
                      <span
                        className={`text-xs ${
                          donation.status === 'completed'
                            ? 'text-green-600'
                            : 'text-yellow-600'
                        }`}
                      >
                        {donation.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">
                No donations yet
              </p>
            )}
          </div>
        </div>

        {/* Active Recurring */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">
              Active Recurring Donations
            </h3>
          </div>
          <div className="p-6">
            {activeRecurring.length > 0 ? (
              <div className="space-y-4">
                {activeRecurring.map((recurring) => (
                  <div
                    key={recurring._id}
                    className="flex items-center space-x-4 py-3 border-b border-gray-100 last:border-0"
                  >
                    <div className="flex-shrink-0">
                      <Calendar className="h-8 w-8 text-purple-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {recurring.category}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {recurring.frequency} • ${recurring.amount.toFixed(2)}
                      </p>
                      {recurring.next_payment_date && (
                        <p className="text-xs text-gray-400 mt-1">
                          Next: {new Date(recurring.next_payment_date).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">
                        {recurring.total_donations} payments
                      </p>
                      <p className="text-sm font-medium text-gray-900">
                        ${recurring.total_amount.toFixed(2)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">
                No active recurring donations
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Giving Stats */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Giving Statistics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-gray-500">First Donation</p>
            <p className="text-base font-medium text-gray-900 mt-1">
              {donorProfile.first_donation_date
                ? new Date(donorProfile.first_donation_date).toLocaleDateString()
                : 'N/A'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Last Donation</p>
            <p className="text-base font-medium text-gray-900 mt-1">
              {donorProfile.last_donation_date
                ? new Date(donorProfile.last_donation_date).toLocaleDateString()
                : 'N/A'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Donor Type</p>
            <p className="text-base font-medium text-gray-900 mt-1">
              {donorProfile.is_recurring_donor ? 'Recurring Donor' : 'One-Time Donor'}
            </p>
          </div>
        </div>
      </div>

      {/* Tax Information */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-base font-medium text-blue-900 mb-2">
          Tax Information
        </h3>
        <p className="text-sm text-blue-700">
          Your total tax-deductible donations for this year:{' '}
          <strong>${donorProfile.total_donated.toFixed(2)}</strong>
        </p>
        <p className="text-xs text-blue-600 mt-2">
          Tax receipts are sent automatically for each donation. You can also download
          them from your donation history.
        </p>
      </div>
    </div>
  );
}
