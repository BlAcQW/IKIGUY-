/**
 * Recurring Donation Form Component
 *
 * Form for setting up recurring donations with Stripe subscriptions.
 */

import React, { useState } from 'react';
import { Calendar, CreditCard, AlertCircle, CheckCircle, Repeat } from 'lucide-react';
import { useCreateRecurringDonation, useMyRecurringDonations, useCancelRecurringDonation } from '../../hooks/useGiving';

const FREQUENCIES = [
  { value: 'weekly', label: 'Weekly' },
  { value: 'biweekly', label: 'Bi-weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'yearly', label: 'Yearly' },
];

const DONATION_TYPES = [
  { value: 'tithe', label: 'Tithe' },
  { value: 'offering', label: 'Offering' },
  { value: 'mission', label: 'Mission Support' },
  { value: 'building_fund', label: 'Building Fund' },
];

export default function RecurringDonationForm() {
  const token = localStorage.getItem('access_token');
  const organizationId = localStorage.getItem('current_organization_id');

  const [amount, setAmount] = useState<number>(50);
  const [frequency, setFrequency] = useState('monthly');
  const [donationType, setDonationType] = useState('tithe');
  const [category, setCategory] = useState('Tithes & Offerings');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [processing, setProcessing] = useState(false);

  const createRecurring = useCreateRecurringDonation(token, organizationId);
  const { data: recurringDonations } = useMyRecurringDonations(token, organizationId);
  const cancelRecurring = useCancelRecurringDonation(token, organizationId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    setProcessing(true);

    try {
      // For demo purposes, use mock payment method
      // In production, this would integrate with Stripe Elements
      const mockPaymentMethodId = 'pm_card_visa';

      await createRecurring.mutateAsync({
        amount,
        frequency,
        donation_type: donationType,
        category,
        payment_method: 'card',
        stripe_payment_method_id: mockPaymentMethodId,
      });

      setSuccess(true);
      setAmount(50);

      // Reset success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to set up recurring donation');
    } finally {
      setProcessing(false);
    }
  };

  const handleCancel = async (recurringId: string) => {
    if (!confirm('Are you sure you want to cancel this recurring donation?')) {
      return;
    }

    try {
      await cancelRecurring.mutateAsync(recurringId);
      alert('Recurring donation cancelled successfully');
    } catch (err: any) {
      alert(err.message || 'Failed to cancel recurring donation');
    }
  };

  return (
    <div className="space-y-8">
      {/* Setup Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Amount */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Amount per Payment
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className="text-gray-500 sm:text-sm">$</span>
            </div>
            <input
              type="number"
              step="0.01"
              min="1"
              value={amount}
              onChange={(e) => setAmount(parseFloat(e.target.value))}
              className="block w-full pl-7 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-purple-500 focus:border-purple-500"
              required
            />
          </div>
        </div>

        {/* Frequency */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Frequency
          </label>
          <select
            value={frequency}
            onChange={(e) => setFrequency(e.target.value)}
            className="block w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-purple-500 focus:border-purple-500"
          >
            {FREQUENCIES.map((freq) => (
              <option key={freq.value} value={freq.value}>
                {freq.label}
              </option>
            ))}
          </select>
        </div>

        {/* Donation Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Donation Type
          </label>
          <select
            value={donationType}
            onChange={(e) => {
              setDonationType(e.target.value);
              const type = DONATION_TYPES.find((t) => t.value === e.target.value);
              if (type) {
                setCategory(type.label);
              }
            }}
            className="block w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-purple-500 focus:border-purple-500"
          >
            {DONATION_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {/* Category */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Fund/Category
          </label>
          <input
            type="text"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="block w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-purple-500 focus:border-purple-500"
          />
        </div>

        {/* Summary */}
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-start">
            <Repeat className="h-5 w-5 text-purple-600 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-purple-900">
                Recurring Summary
              </h3>
              <p className="mt-1 text-sm text-purple-700">
                You will be charged <strong>${amount.toFixed(2)}</strong>{' '}
                <strong>{frequency}</strong> for {category}.
              </p>
              <p className="mt-2 text-xs text-purple-600">
                You can cancel this recurring donation at any time.
              </p>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start">
              <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-900">Error</h3>
                <p className="mt-1 text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-start">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-900">
                  Recurring donation set up successfully!
                </h3>
                <p className="mt-1 text-sm text-green-700">
                  Your {frequency} donation of ${amount.toFixed(2)} has been activated.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={processing || amount <= 0}
          className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-base font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {processing ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              Processing...
            </>
          ) : (
            <>
              <Calendar className="h-5 w-5 mr-2" />
              Set Up Recurring Donation
            </>
          )}
        </button>
      </form>

      {/* Active Recurring Donations */}
      {recurringDonations && recurringDonations.recurring_donations.length > 0 && (
        <div className="border-t pt-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Your Active Recurring Donations
          </h3>
          <div className="space-y-4">
            {recurringDonations.recurring_donations.map((recurring) => (
              <div
                key={recurring._id}
                className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <Repeat className="h-5 w-5 text-purple-600" />
                      <h4 className="text-base font-medium text-gray-900">
                        {recurring.category}
                      </h4>
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          recurring.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {recurring.status}
                      </span>
                    </div>
                    <div className="mt-2 text-sm text-gray-600">
                      <p>
                        <strong>${recurring.amount.toFixed(2)}</strong>{' '}
                        {recurring.frequency}
                      </p>
                      <p className="mt-1">
                        Total donated: ${recurring.total_amount.toFixed(2)} ({recurring.total_donations}{' '}
                        payments)
                      </p>
                      {recurring.next_payment_date && (
                        <p className="mt-1 text-xs">
                          Next payment:{' '}
                          {new Date(recurring.next_payment_date).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => handleCancel(recurring._id)}
                    className="ml-4 px-3 py-1 text-sm font-medium text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
