/**
 * Church Signup Wizard - ChurchFlow SaaS
 *
 * 5-step onboarding flow for new churches:
 * 1. Church Information
 * 2. Admin Account
 * 3. Phone Verification
 * 4. Plan Selection
 * 5. Payment Setup (for paid plans)
 */

import { useState } from 'react';
import {
  Building2,
  User,
  Phone,
  CreditCard,
  Check,
  AlertCircle,
  Loader2
} from 'lucide-react';
import StripePaymentForm from './StripePaymentForm';

// ==================== Types ====================

export interface ChurchInfo {
  name: string;
  email: string;
  phone: string;
  address: string;
  website: string;
}

export interface AdminInfo {
  name: string;
  email: string;
  phone: string;
}

export interface SignupData {
  church: ChurchInfo;
  admin: AdminInfo;
  selectedPlan: 'free' | 'standard' | 'premium';
  organizationId?: string;
}

export interface SignupWizardProps {
  apiBaseUrl: string;
  onComplete: (organizationId: string) => void;
  onError: (message: string) => void;
}

// ==================== Plan Details ====================

const PLANS = {
  free: {
    name: 'Free',
    price: 0,
    memberLimit: 100,
    features: [
      'Up to 100 members',
      '100 SMS credits/month',
      'Events & Check-in',
      'Visitor tracking',
      'Basic SMS notifications',
    ],
  },
  standard: {
    name: 'Standard',
    price: 49,
    memberLimit: 500,
    features: [
      'Up to 500 members',
      '500 SMS credits/month',
      'Everything in Free',
      'Giving management',
      'Volunteer coordination',
      'Custom branding',
    ],
  },
  premium: {
    name: 'Premium',
    price: 99,
    memberLimit: -1,
    features: [
      'Unlimited members',
      '2000 SMS credits/month',
      'Everything in Standard',
      'AI-powered analytics',
      'Priority support',
      'White-label options',
    ],
  },
};

// ==================== Main Component ====================

export default function SignupWizard({ apiBaseUrl, onComplete, onError }: SignupWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState('');

  const [signupData, setSignupData] = useState<SignupData>({
    church: {
      name: '',
      email: '',
      phone: '',
      address: '',
      website: '',
    },
    admin: {
      name: '',
      email: '',
      phone: '',
    },
    selectedPlan: 'free',
  });

  // ==================== Step Handlers ====================

  const handleChurchInfoNext = () => {
    const { church } = signupData;
    if (!church.name || !church.email || !church.phone) {
      onError('Please fill in all required church information');
      return;
    }
    setCurrentStep(2);
  };

  const handleAdminInfoNext = () => {
    const { admin } = signupData;
    if (!admin.name || !admin.email || !admin.phone) {
      onError('Please fill in all required admin information');
      return;
    }
    setCurrentStep(3);
  };

  const handleSubmitSignup = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/onboarding/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          church_name: signupData.church.name,
          church_email: signupData.church.email,
          church_phone: signupData.church.phone,
          church_address: signupData.church.address,
          church_website: signupData.church.website,
          admin_name: signupData.admin.name,
          admin_email: signupData.admin.email,
          admin_phone: signupData.admin.phone,
          selected_plan: signupData.selectedPlan,
          trial_days: signupData.selectedPlan === 'free' ? 0 : 14,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Signup failed');
      }

      const result = await response.json();
      setSignupData({ ...signupData, organizationId: result.organization_id });
      setOtpSent(true);
      onError(''); // Clear any previous errors
    } catch (error: any) {
      onError(error.message || 'Failed to create church account');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyPhone = async () => {
    if (otp.length < 4) {
      onError('Please enter the OTP code');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/onboarding/verify-phone`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: signupData.admin.phone,
          otp: otp,
          organization_id: signupData.organizationId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Verification failed');
      }

      setCurrentStep(4);
      onError('');
    } catch (error: any) {
      onError(error.message || 'Failed to verify phone number');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPlan = (plan: 'free' | 'standard' | 'premium') => {
    setSignupData({ ...signupData, selectedPlan: plan });

    // If free plan, complete onboarding
    if (plan === 'free') {
      if (signupData.organizationId) {
        onComplete(signupData.organizationId);
      }
    } else {
      // For paid plans, go to payment setup
      setCurrentStep(5);
    }
  };

  const handlePaymentComplete = async (paymentMethodId: string) => {
    setLoading(true);
    try {
      // Create subscription with payment method
      const response = await fetch(`${apiBaseUrl}/api/v1/billing/subscriptions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan: signupData.selectedPlan,
          payment_method_id: paymentMethodId,
          trial_days: 14,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Payment setup failed');
      }

      if (signupData.organizationId) {
        onComplete(signupData.organizationId);
      }
    } catch (error: any) {
      onError(error.message || 'Failed to set up payment');
    } finally {
      setLoading(false);
    }
  };

  // ==================== Step Indicators ====================

  const steps = [
    { number: 1, name: 'Church Info', icon: Building2 },
    { number: 2, name: 'Admin Account', icon: User },
    { number: 3, name: 'Verification', icon: Phone },
    { number: 4, name: 'Select Plan', icon: Check },
    { number: 5, name: 'Payment', icon: CreditCard },
  ];

  // ==================== Render ====================

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome to ChurchFlow</h1>
          <p className="text-gray-600">Let's get your church set up in just a few steps</p>
        </div>

        {/* Step Indicators */}
        <div className="flex items-center justify-between mb-8 px-4">
          {steps.map((step, index) => (
            <div key={step.number} className="flex items-center flex-1">
              <div className="flex flex-col items-center">
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center ${
                    currentStep >= step.number
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-400'
                  }`}
                >
                  {currentStep > step.number ? (
                    <Check className="w-6 h-6" />
                  ) : (
                    <step.icon className="w-6 h-6" />
                  )}
                </div>
                <span className="text-xs mt-2 font-medium text-gray-600">{step.name}</span>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`flex-1 h-1 mx-2 ${
                    currentStep > step.number ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-lg shadow-md p-8">
          {/* Step 1: Church Information */}
          {currentStep === 1 && (
            <div>
              <h2 className="text-2xl font-bold mb-6">Church Information</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Church Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={signupData.church.name}
                    onChange={(e) =>
                      setSignupData({
                        ...signupData,
                        church: { ...signupData.church, name: e.target.value },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Grace Community Church"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Church Email <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    value={signupData.church.email}
                    onChange={(e) =>
                      setSignupData({
                        ...signupData,
                        church: { ...signupData.church, email: e.target.value },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="info@church.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Church Phone <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    value={signupData.church.phone}
                    onChange={(e) =>
                      setSignupData({
                        ...signupData,
                        church: { ...signupData.church, phone: e.target.value },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="+1234567890"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Church Address
                  </label>
                  <input
                    type="text"
                    value={signupData.church.address}
                    onChange={(e) =>
                      setSignupData({
                        ...signupData,
                        church: { ...signupData.church, address: e.target.value },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="123 Main Street, City, State"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Website
                  </label>
                  <input
                    type="url"
                    value={signupData.church.website}
                    onChange={(e) =>
                      setSignupData({
                        ...signupData,
                        church: { ...signupData.church, website: e.target.value },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="https://church.com"
                  />
                </div>
              </div>
              <button
                onClick={handleChurchInfoNext}
                className="mt-6 w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-medium"
              >
                Continue
              </button>
            </div>
          )}

          {/* Step 2: Admin Account */}
          {currentStep === 2 && (
            <div>
              <h2 className="text-2xl font-bold mb-6">Admin Account</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Full Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={signupData.admin.name}
                    onChange={(e) =>
                      setSignupData({
                        ...signupData,
                        admin: { ...signupData.admin, name: e.target.value },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="John Doe"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    value={signupData.admin.email}
                    onChange={(e) =>
                      setSignupData({
                        ...signupData,
                        admin: { ...signupData.admin, email: e.target.value },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="admin@church.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Phone Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    value={signupData.admin.phone}
                    onChange={(e) =>
                      setSignupData({
                        ...signupData,
                        admin: { ...signupData.admin, phone: e.target.value },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="+1234567890"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    We'll send a verification code to this number
                  </p>
                </div>
              </div>
              <div className="mt-6 flex space-x-4">
                <button
                  onClick={() => setCurrentStep(1)}
                  className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-50 font-medium"
                >
                  Back
                </button>
                <button
                  onClick={handleAdminInfoNext}
                  className="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-medium"
                >
                  Continue
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Phone Verification */}
          {currentStep === 3 && (
            <div>
              <h2 className="text-2xl font-bold mb-6">Verify Your Phone</h2>

              {!otpSent ? (
                <div>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                    <div className="flex items-start">
                      <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 mr-3" />
                      <div>
                        <p className="text-sm text-blue-800">
                          We'll send a verification code to <strong>{signupData.admin.phone}</strong>
                        </p>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={handleSubmitSignup}
                    disabled={loading}
                    className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-medium disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        Creating Account...
                      </>
                    ) : (
                      'Send Verification Code'
                    )}
                  </button>
                  <button
                    onClick={() => setCurrentStep(2)}
                    className="w-full mt-4 border border-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-50 font-medium"
                  >
                    Back
                  </button>
                </div>
              ) : (
                <div>
                  <p className="text-gray-600 mb-4">
                    Enter the 6-digit code sent to <strong>{signupData.admin.phone}</strong>
                  </p>
                  <input
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    maxLength={6}
                    className="w-full px-3 py-3 text-center text-2xl tracking-widest border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 mb-6"
                    placeholder="000000"
                  />
                  <button
                    onClick={handleVerifyPhone}
                    disabled={loading}
                    className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-medium disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        Verifying...
                      </>
                    ) : (
                      'Verify Phone'
                    )}
                  </button>
                  <button
                    onClick={() => setOtpSent(false)}
                    className="w-full mt-4 text-blue-600 hover:underline"
                  >
                    Resend Code
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Step 4: Plan Selection */}
          {currentStep === 4 && (
            <div>
              <h2 className="text-2xl font-bold mb-6">Choose Your Plan</h2>
              <p className="text-gray-600 mb-6">
                Start with our free plan and upgrade anytime as your church grows
              </p>
              <div className="grid md:grid-cols-3 gap-6">
                {Object.entries(PLANS).map(([key, plan]) => (
                  <div
                    key={key}
                    className={`border-2 rounded-lg p-6 cursor-pointer transition-all ${
                      signupData.selectedPlan === key
                        ? 'border-blue-600 bg-blue-50'
                        : 'border-gray-200 hover:border-blue-300'
                    }`}
                    onClick={() => handleSelectPlan(key as 'free' | 'standard' | 'premium')}
                  >
                    <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
                    <div className="text-3xl font-bold mb-4">
                      ${plan.price}
                      <span className="text-sm font-normal text-gray-600">/month</span>
                    </div>
                    <ul className="space-y-2">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="flex items-start text-sm">
                          <Check className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                    {key !== 'free' && (
                      <div className="mt-4 text-sm text-blue-600 font-medium">
                        14-day free trial included
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 5: Payment Setup */}
          {currentStep === 5 && signupData.organizationId && (
            <div>
              <h2 className="text-2xl font-bold mb-6">Payment Setup</h2>
              <p className="text-gray-600 mb-6">
                Add your payment method to start your {PLANS[signupData.selectedPlan].name} plan
                trial.
              </p>
              <StripePaymentForm
                apiBaseUrl={apiBaseUrl}
                organizationId={signupData.organizationId}
                selectedPlan={signupData.selectedPlan as 'standard' | 'premium'}
                onPaymentSuccess={handlePaymentComplete}
                onError={onError}
                onBack={() => setCurrentStep(4)}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
