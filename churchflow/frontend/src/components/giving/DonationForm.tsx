/**
 * Donation Form Component
 *
 * Form for making one-time donations with Stripe integration.
 */

import React, { useState } from 'react';
import { DollarSign, CreditCard, AlertCircle, CheckCircle } from 'lucide-react';
import { useCreateDonation, useProcessDonation } from '../../hooks/useGiving';

const DONATION_TYPES = [
  { value: 'tithe', label: 'Tithe' },
  { value: 'offering', label: 'Offering' },
  { value: 'mission', label: 'Mission' },
  { value: 'building_fund', label: 'Building Fund' },
  { value: 'special_project', label: 'Special Project' },
  { value: 'one_time', label: 'General Donation' },
];

const PRESET_AMOUNTS = [25, 50, 100, 250, 500, 1000];

export default function DonationForm() {
  const token = localStorage.getItem('access_token');
  const organizationId = localStorage.getItem('current_organization_id');
  const isAuthenticated = !!token;

  const [amount, setAmount] = useState<number>(100);
  const [customAmount, setCustomAmount] = useState<string>('');
  const [donationType, setDonationType] = useState('tithe');
  const [category, setCategory] = useState('Tithes & Offerings');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [processing, setProcessing] = useState(false);

  // Public donor info fields (only shown when not authenticated)
  const [donorName, setDonorName] = useState('');
  const [donorEmail, setDonorEmail] = useState('');
  const [donorPhone, setDonorPhone] = useState('');

  const createDonation = useCreateDonation(token, organizationId);
  const processDonation = useProcessDonation(token, organizationId);

  const handleAmountSelect = (selectedAmount: number) => {
    setAmount(selectedAmount);
    setCustomAmount('');
  };

  const handleCustomAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setCustomAmount(value);
    const numValue = parseFloat(value);
    if (!isNaN(numValue) && numValue > 0) {
      setAmount(numValue);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    setProcessing(true);

    try {
      let donor_name: string;
      let donor_email: string;
      let donor_phone: string;

      if (isAuthenticated) {
        // Get user info from API if authenticated
        const userResponse = await fetch(
          `${import.meta.env.VITE_API_URL || 'http://localhost:30030'}/api/v1/users/me`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!userResponse.ok) {
          throw new Error('Failed to fetch user information');
        }

        const user = await userResponse.json();
        donor_name = user.name || user.email;
        donor_email = user.email;
        donor_phone = user.phone || '';
      } else {
        // Use form inputs for public donations
        if (!donorName.trim()) {
          throw new Error('Please enter your name');
        }
        if (!donorEmail.trim() || !donorEmail.includes('@')) {
          throw new Error('Please enter a valid email address');
        }
        donor_name = donorName.trim();
        donor_email = donorEmail.trim();
        donor_phone = donorPhone.trim() || '';
      }

      // Create donation
      const donation = await createDonation.mutateAsync({
        donor_name,
        donor_email,
        donor_phone,
        amount,
        donation_type: donationType,
        category,
        payment_method: 'card',
        is_anonymous: isAnonymous,
        notes: notes || undefined,
      });

      // For demo purposes, simulate successful payment
      // In production, this would integrate with Stripe Elements
      // and create a real PaymentMethod

      // Simulate payment processing
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // For now, we'll use a placeholder payment method ID
      // In production, this would come from Stripe Elements
      const mockPaymentMethodId = 'pm_card_visa'; // Stripe test payment method

      try {
        await processDonation.mutateAsync({
          donation_id: donation._id,
          stripe_payment_method_id: mockPaymentMethodId,
        });

        setSuccess(true);
        setAmount(100);
        setCustomAmount('');
        setNotes('');
        // Reset public donor fields
        if (!isAuthenticated) {
          setDonorName('');
          setDonorEmail('');
          setDonorPhone('');
        }

        // Show success message for 3 seconds
        setTimeout(() => setSuccess(false), 3000);
      } catch (paymentError: any) {
        setError(paymentError.message || 'Payment processing failed');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to create donation');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Public Donor Information (only shown when not authenticated) */}
      {!isAuthenticated && (
        <div className="space-y-4 bg-gray-50 p-4 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Your Information
          </h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Full Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={donorName}
              onChange={(e) => setDonorName(e.target.value)}
              placeholder="Enter your full name"
              className="block w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email Address <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              required
              value={donorEmail}
              onChange={(e) => setDonorEmail(e.target.value)}
              placeholder="Enter your email address"
              className="block w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Phone Number (Optional)
            </label>
            <input
              type="tel"
              value={donorPhone}
              onChange={(e) => setDonorPhone(e.target.value)}
              placeholder="Enter your phone number"
              className="block w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      )}

      {/* Amount Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Amount
        </label>
        <div className="grid grid-cols-3 gap-3 mb-3">
          {PRESET_AMOUNTS.map((presetAmount) => (
            <button
              key={presetAmount}
              type="button"
              onClick={() => handleAmountSelect(presetAmount)}
              className={`py-3 px-4 border rounded-lg font-medium transition-colors ${
                amount === presetAmount && !customAmount
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              ${presetAmount}
            </button>
          ))}
        </div>

        {/* Custom Amount */}
        <div className="relative mt-3">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <DollarSign className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="number"
            step="0.01"
            min="1"
            placeholder="Other amount"
            value={customAmount}
            onChange={handleCustomAmountChange}
            className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
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
          className="block w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
        >
          {DONATION_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* Category/Fund */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Fund/Category
        </label>
        <input
          type="text"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          placeholder="e.g., Building Fund, Mission Trip"
          className="block w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Notes (Optional)
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
          placeholder="Add a note or dedication..."
          className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Anonymous Option */}
      <div className="flex items-center">
        <input
          type="checkbox"
          id="anonymous"
          checked={isAnonymous}
          onChange={(e) => setIsAnonymous(e.target.checked)}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="anonymous" className="ml-2 block text-sm text-gray-700">
          Make this donation anonymous
        </label>
      </div>

      {/* Payment Info Note */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <CreditCard className="h-5 w-5 text-blue-600 mt-0.5" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-900">
              Secure Payment
            </h3>
            <p className="mt-1 text-sm text-blue-700">
              Your payment is processed securely through Stripe. We never store your
              card information.
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
                Thank you for your donation!
              </h3>
              <p className="mt-1 text-sm text-green-700">
                Your donation of ${amount.toFixed(2)} has been processed successfully.
                You will receive a receipt via email.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={processing || amount <= 0}
        className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-base font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        {processing ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
            Processing...
          </>
        ) : (
          <>
            <CreditCard className="h-5 w-5 mr-2" />
            Donate ${amount.toFixed(2)}
          </>
        )}
      </button>

      {/* Tax Deductible Note */}
      <p className="text-xs text-gray-500 text-center">
        Your donation is tax-deductible to the extent allowed by law. You will receive
        a receipt for your records.
      </p>
    </form>
  );
}
