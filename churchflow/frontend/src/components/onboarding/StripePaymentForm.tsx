/**
 * Stripe Payment Form - ChurchFlow SaaS
 *
 * Stripe Elements integration for collecting payment methods securely.
 */

import { useState, useEffect } from 'react';
import { loadStripe, Stripe, StripeElements } from '@stripe/stripe-js';
import {
  Elements,
  CardElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js';
import { CreditCard, Loader2, Lock } from 'lucide-react';

// ==================== Types ====================

export interface StripePaymentFormProps {
  apiBaseUrl: string;
  organizationId: string;
  selectedPlan: 'standard' | 'premium';
  onPaymentSuccess: (paymentMethodId: string) => void;
  onError: (message: string) => void;
  onBack: () => void;
}

// ==================== Payment Form Component ====================

function PaymentFormContent({
  apiBaseUrl,
  organizationId,
  selectedPlan,
  onPaymentSuccess,
  onError,
  onBack,
}: StripePaymentFormProps) {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);
  const [setupIntentClientSecret, setSetupIntentClientSecret] = useState<string | null>(null);

  useEffect(() => {
    createSetupIntent();
  }, []);

  const createSetupIntent = async () => {
    try {
      const token = localStorage.getItem('access_token') || 'temp_token';
      const response = await fetch(
        `${apiBaseUrl}/api/v1/billing/setup-intent/${organizationId}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create payment setup');
      }

      const data = await response.json();
      setSetupIntentClientSecret(data.client_secret);
    } catch (error: any) {
      onError(error.message || 'Failed to initialize payment setup');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!stripe || !elements || !setupIntentClientSecret) {
      return;
    }

    setLoading(true);

    try {
      const cardElement = elements.getElement(CardElement);

      if (!cardElement) {
        throw new Error('Card element not found');
      }

      // Confirm the SetupIntent with the card details
      const { error, setupIntent } = await stripe.confirmCardSetup(setupIntentClientSecret, {
        payment_method: {
          card: cardElement,
          billing_details: {
            // We can add billing details here if needed
          },
        },
      });

      if (error) {
        throw new Error(error.message || 'Payment setup failed');
      }

      if (setupIntent && setupIntent.payment_method) {
        // Payment method successfully attached
        onPaymentSuccess(setupIntent.payment_method as string);
      } else {
        throw new Error('Payment method not created');
      }
    } catch (error: any) {
      onError(error.message || 'Payment setup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Card Information
        </label>
        <div className="border border-gray-300 rounded-lg p-4 bg-white">
          <CardElement
            options={{
              style: {
                base: {
                  fontSize: '16px',
                  color: '#424770',
                  '::placeholder': {
                    color: '#aab7c4',
                  },
                },
                invalid: {
                  color: '#9e2146',
                },
              },
            }}
          />
        </div>
        <div className="flex items-center mt-2 text-xs text-gray-500">
          <Lock className="w-3 h-3 mr-1" />
          Secured by Stripe. Your card information is encrypted.
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>14-day free trial</strong> - Your card will only be charged after your trial
          ends. Cancel anytime before then for free.
        </p>
      </div>

      <div className="flex space-x-4">
        <button
          type="button"
          onClick={onBack}
          disabled={loading}
          className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-50 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Back
        </button>
        <button
          type="submit"
          disabled={!stripe || loading || !setupIntentClientSecret}
          className="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-medium disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <CreditCard className="w-5 h-5 mr-2" />
              Start Trial
            </>
          )}
        </button>
      </div>
    </form>
  );
}

// ==================== Main Component with Stripe Provider ====================

export default function StripePaymentForm(props: StripePaymentFormProps) {
  const [stripePromise, setStripePromise] = useState<Promise<Stripe | null> | null>(null);

  useEffect(() => {
    // Get Stripe publishable key from environment
    const stripePublishableKey =
      import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY ||
      'pk_test_51234567890'; // Replace with actual test key

    setStripePromise(loadStripe(stripePublishableKey));
  }, []);

  if (!stripePromise) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <Elements stripe={stripePromise}>
      <PaymentFormContent {...props} />
    </Elements>
  );
}
