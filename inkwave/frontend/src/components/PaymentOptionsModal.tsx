/**
 * PaymentOptionsModal
 * Enhanced modal for selecting payment gateway and processing payments
 * Supports Stripe (redirect), Paystack (inline popup), and ExpressPay (Ghana)
 * Features: Recommended badges, trust indicators, amount breakdown
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CreditCard, Loader2, CheckCircle, Shield, Zap, Globe, Smartphone, AlertCircle, RefreshCw } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { api } from '../lib/api';
import toast from 'react-hot-toast';

type VerificationState = 'idle' | 'verifying' | 'success' | 'failed';

// Declare Paystack inline type
declare global {
  interface Window {
    PaystackPop: {
      setup: (config: any) => { openIframe: () => void };
    };
  }
}

interface PaymentOptionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  amount: number;
  onSuccess: () => void;
}

export default function PaymentOptionsModal({
  isOpen,
  onClose,
  amount,
  onSuccess,
}: PaymentOptionsModalProps) {
  const { user } = useAuthStore();
  const [processing, setProcessing] = useState(false);
  const [paystackConfig, setPaystackConfig] = useState<any>(null);
  const [selectedMethod, setSelectedMethod] = useState<'paystack' | 'stripe' | 'expresspay' | null>(null);
  const [verificationState, setVerificationState] = useState<VerificationState>('idle');
  const [pendingReference, setPendingReference] = useState<string | null>(null);
  const [verificationError, setVerificationError] = useState<string | null>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const pollCountRef = useRef(0);

  const paystackPublicKey = (import.meta as any).env?.VITE_PAYSTACK_PUBLIC_KEY || '';

  // Max polling attempts (15 * 2s = 30 seconds)
  const MAX_POLL_ATTEMPTS = 15;
  const POLL_INTERVAL = 2000;

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  // Load Paystack inline JS
  useEffect(() => {
    if (!document.getElementById('paystack-script')) {
      const script = document.createElement('script');
      script.id = 'paystack-script';
      script.src = 'https://js.paystack.co/v1/inline.js';
      script.async = true;
      document.body.appendChild(script);
    }
  }, []);

  // Open Paystack popup when config is ready
  const openPaystackPopup = useCallback((config: any) => {
    if (!window.PaystackPop) {
      toast.error('Payment system loading... Please try again.');
      setProcessing(false);
      return;
    }

    console.log('[Payment] Opening Paystack popup with config:', config);

    const handler = window.PaystackPop.setup({
      key: paystackPublicKey,
      email: config.email,
      amount: config.amount,
      currency: config.currency || 'GHS',
      ref: config.reference,
      onClose: () => {
        console.log('[Payment] Paystack popup closed');
        // If we have a reference, user may have completed payment
        if (config.reference) {
          setPendingReference(config.reference);
          pollPaymentStatus(config.reference);
        } else {
          toast.error('Payment cancelled');
          resetState();
        }
      },
      callback: (response: any) => {
        console.log('[Payment] Paystack callback:', response);
        const ref = response.reference || config.reference;
        setPendingReference(ref);
        pollPaymentStatus(ref);
      },
    });

    handler.openIframe();
  }, [paystackPublicKey]);

  // Poll for payment status
  const pollPaymentStatus = useCallback(async (reference: string) => {
    pollCountRef.current = 0;
    setVerificationState('verifying');
    setVerificationError(null);

    const poll = async () => {
      try {
        pollCountRef.current++;
        console.log(`[Payment] Polling attempt ${pollCountRef.current}/${MAX_POLL_ATTEMPTS} for ${reference}`);

        const response = await api.wallet.getPaymentStatus(reference);
        const data = response.data;

        if (data.status === 'completed') {
          // Payment confirmed!
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          setVerificationState('success');
          toast.success('Payment confirmed! Your wallet has been credited.');

          // Wait a moment to show success state, then close
          setTimeout(() => {
            onSuccess();
            onClose();
            resetState();
          }, 1500);
          return;
        }

        if (data.status === 'failed') {
          // Payment failed
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          setVerificationState('failed');
          setVerificationError(data.error || 'Payment failed');
          toast.error(data.error || 'Payment failed');
          return;
        }

        // Still pending - check if we've exceeded max attempts
        if (pollCountRef.current >= MAX_POLL_ATTEMPTS) {
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          // Try direct verification as fallback
          await verifyPaymentDirectly(reference);
        }
      } catch (error: any) {
        console.error('[Payment] Polling error:', error);
        // Don't stop polling on network errors, just log
        if (pollCountRef.current >= MAX_POLL_ATTEMPTS) {
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          // Try direct verification as fallback
          await verifyPaymentDirectly(reference);
        }
      }
    };

    // Start polling
    pollingRef.current = setInterval(poll, POLL_INTERVAL);
    // Also poll immediately
    poll();
  }, [onSuccess, onClose]);

  // Direct verification as fallback
  const verifyPaymentDirectly = async (reference: string) => {
    try {
      console.log('[Payment] Attempting direct verification for', reference);
      const response = await api.wallet.verifyPaystackPayment(reference);
      const data = response.data;

      if (data.success) {
        setVerificationState('success');
        toast.success('Payment verified! Your wallet has been credited.');
        setTimeout(() => {
          onSuccess();
          onClose();
          resetState();
        }, 1500);
      } else {
        setVerificationState('failed');
        setVerificationError('Payment verification failed. Please check your wallet or contact support.');
      }
    } catch (error: any) {
      console.error('[Payment] Direct verification failed:', error);
      setVerificationState('failed');
      setVerificationError('Unable to verify payment. If you completed the payment, your wallet will be credited shortly.');
    }
  };

  // Reset state
  const resetState = () => {
    setProcessing(false);
    setPaystackConfig(null);
    setSelectedMethod(null);
    setVerificationState('idle');
    setPendingReference(null);
    setVerificationError(null);
    pollCountRef.current = 0;
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  // Retry verification
  const handleRetryVerification = () => {
    if (pendingReference) {
      pollPaymentStatus(pendingReference);
    }
  };

  // Calculate credits from amount (100 credits = $1)
  const credits = amount * 100;

  // Calculate approximate usage
  const approxNarration = Math.floor(credits / 2); // ~2 credits per minute
  const approxQA = Math.floor(credits / 4); // ~4 credits per question

  // Initialize Paystack payment
  const handlePaystackInit = async () => {
    if (!user?.email) {
      toast.error('User email not found');
      return;
    }

    setSelectedMethod('paystack');
    setProcessing(true);

    try {
      const response = await api.wallet.initiatePaystackTopup(
        amount,
        `${window.location.origin}/wallet?payment=success`
      );

      const data = response.data;

      if (data.success && data.reference) {
        // Store config and open popup directly
        const config = {
          email: user.email,
          amount: data.amount * 100, // Convert to pesewas (GHS smallest unit)
          reference: data.reference,
          currency: data.currency || 'GHS',
        };

        setPaystackConfig(config);
        setPendingReference(data.reference);

        // Open popup directly
        openPaystackPopup(config);
      } else {
        toast.error(data.error || 'Failed to initialize payment');
        setProcessing(false);
      }
    } catch (error: any) {
      console.error('Paystack init error:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to initialize payment';
      toast.error(errorMessage);
      setProcessing(false);
    }
  };

  // Handle Paystack success - start polling for confirmation
  const handlePaystackSuccess = async (reference: any) => {
    console.log('[Payment] Paystack popup completed:', reference);
    const ref = reference.reference || reference;

    // Store reference and start polling
    setPendingReference(ref);
    setPaystackConfig(null);

    // Start polling for payment status (webhook may have already processed it)
    pollPaymentStatus(ref);
  };

  // Handle Paystack close - could be cancel or completion
  const handlePaystackClose = () => {
    console.log('[Payment] Paystack popup closed');

    // If we have a pending reference, the user completed payment but closed popup
    // Start polling to check status
    if (pendingReference || paystackConfig?.reference) {
      const ref = pendingReference || paystackConfig?.reference;
      setPendingReference(ref);
      setPaystackConfig(null);
      pollPaymentStatus(ref);
    } else {
      // No reference means user cancelled before completing
      toast.error('Payment cancelled');
      resetState();
    }
  };

  // Handle Stripe payment
  const handleStripePayment = async () => {
    setSelectedMethod('stripe');
    setProcessing(true);

    try {
      const currentUrl = window.location.origin;
      const successUrl = `${currentUrl}/wallet?payment=success`;
      const cancelUrl = `${currentUrl}/wallet?payment=cancelled`;

      const response = await api.wallet.initiateStripeTopup(amount, successUrl, cancelUrl);
      const data = response.data;

      if (data.success && data.payment_url) {
        toast.success('Redirecting to Stripe...');
        window.location.href = data.payment_url;
      } else {
        toast.error(data.error || 'Failed to initiate payment');
        setProcessing(false);
      }
    } catch (error: any) {
      console.error('Stripe init error:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to initialize payment';
      toast.error(errorMessage);
      setProcessing(false);
    }
  };

  // Handle ExpressPay payment (Ghana - GHS only)
  const handleExpressPayPayment = async () => {
    setSelectedMethod('expresspay');
    setProcessing(true);

    try {
      const currentUrl = window.location.origin;
      const redirectUrl = `${currentUrl}/wallet?payment=expresspay&status=pending`;

      const response = await api.wallet.initiateExpressPayTopup(amount, redirectUrl);
      const data = response.data;

      if (data.success && data.payment_url) {
        toast.success('Redirecting to ExpressPay...');
        window.location.href = data.payment_url;
      } else {
        toast.error(data.error || 'Failed to initiate ExpressPay payment');
        setProcessing(false);
      }
    } catch (error: any) {
      console.error('ExpressPay init error:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to initialize ExpressPay payment';
      toast.error(errorMessage);
      setProcessing(false);
    }
  };

  // Render verification overlay
  const renderVerificationOverlay = () => {
    if (verificationState === 'idle') return null;

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="absolute inset-0 bg-gray-900/95 backdrop-blur-sm flex items-center justify-center z-20 rounded-2xl sm:rounded-3xl"
      >
        <div className="text-center p-8 max-w-md">
          {verificationState === 'verifying' && (
            <>
              <div className="relative mb-6">
                <div className="w-20 h-20 mx-auto rounded-full bg-blue-500/20 flex items-center justify-center">
                  <Loader2 className="h-10 w-10 text-blue-400 animate-spin" />
                </div>
                <div className="absolute inset-0 w-20 h-20 mx-auto rounded-full border-2 border-blue-500/30 animate-ping" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">Verifying Payment</h3>
              <p className="text-gray-400 mb-4">
                Please wait while we confirm your payment...
              </p>
              <p className="text-sm text-gray-500">
                This usually takes a few seconds
              </p>
            </>
          )}

          {verificationState === 'success' && (
            <>
              <div className="w-20 h-20 mx-auto rounded-full bg-green-500/20 flex items-center justify-center mb-6">
                <CheckCircle className="h-10 w-10 text-green-400" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">Payment Confirmed!</h3>
              <p className="text-gray-400">
                Your wallet has been credited successfully.
              </p>
            </>
          )}

          {verificationState === 'failed' && (
            <>
              <div className="w-20 h-20 mx-auto rounded-full bg-red-500/20 flex items-center justify-center mb-6">
                <AlertCircle className="h-10 w-10 text-red-400" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">Verification Issue</h3>
              <p className="text-gray-400 mb-6">
                {verificationError || 'We could not verify your payment at this time.'}
              </p>
              <div className="space-y-3">
                <button
                  onClick={handleRetryVerification}
                  className="w-full flex items-center justify-center space-x-2 bg-blue-500 hover:bg-blue-600 text-white py-3 px-6 rounded-xl font-semibold transition"
                >
                  <RefreshCw className="h-5 w-5" />
                  <span>Retry Verification</span>
                </button>
                <button
                  onClick={() => {
                    resetState();
                    onClose();
                  }}
                  className="w-full bg-gray-700 hover:bg-gray-600 text-white py-3 px-6 rounded-xl font-semibold transition"
                >
                  Close
                </button>
                <p className="text-xs text-gray-500 mt-4">
                  If you completed the payment, your wallet will be credited automatically within a few minutes.
                </p>
              </div>
            </>
          )}
        </div>
      </motion.div>
    );
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', duration: 0.5 }}
            className="bg-gradient-to-br from-gray-800 via-gray-800 to-gray-900 rounded-2xl sm:rounded-3xl p-4 sm:p-6 md:p-8 max-w-2xl w-full border border-gray-700 shadow-2xl relative overflow-hidden max-h-[90vh] overflow-y-auto"
          >
            {/* Verification Overlay */}
            {renderVerificationOverlay()}

            {/* Decorative background gradient */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl"></div>
            <div className="absolute bottom-0 left-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl"></div>

            {/* Close button */}
            <button
              onClick={onClose}
              disabled={processing || verificationState !== 'idle'}
              className="absolute top-4 right-4 text-gray-400 hover:text-white transition disabled:opacity-50 z-10"
            >
              <X className="h-6 w-6" />
            </button>

            {/* Header */}
            <div className="relative z-10 mb-4 sm:mb-6 md:mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 sm:p-3 bg-gradient-to-br from-purple-500/30 to-pink-500/30 rounded-lg sm:rounded-xl">
                  <CreditCard className="h-5 w-5 sm:h-7 sm:w-7 text-purple-400" />
                </div>
                <div>
                  <h3 className="text-xl sm:text-2xl md:text-3xl font-bold text-white">
                    Choose Payment Method
                  </h3>
                  <p className="text-xs sm:text-sm text-gray-400">
                    Secure checkout • Instant credit
                  </p>
                </div>
              </div>

              {/* Amount Summary Card */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-lg sm:rounded-xl p-3 sm:p-5"
              >
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <p className="text-xs sm:text-sm text-gray-400 mb-1">You're topping up</p>
                    <p className="text-2xl sm:text-4xl font-bold text-white">${amount.toFixed(2)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs sm:text-sm text-gray-400 mb-1">You'll receive</p>
                    <p className="text-lg sm:text-2xl font-bold text-purple-400">{credits} credits</p>
                  </div>
                </div>
                <div className="flex items-center justify-between text-[10px] sm:text-xs text-gray-500 pt-3 border-t border-gray-700">
                  <span>≈ {approxNarration} mins narration</span>
                  <span className="hidden sm:inline">or</span>
                  <span>≈ {approxQA} Q&A</span>
                </div>
              </motion.div>
            </div>

            {/* Payment Options */}
            <div className="relative z-10 space-y-4">
              <p className="text-sm text-gray-400 mb-4 flex items-center">
                <Shield className="h-4 w-4 mr-2 text-green-400" />
                All payments are encrypted and secure
              </p>

              {/* Paystack Option */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className={`relative border-2 rounded-lg sm:rounded-xl p-3 sm:p-5 transition-all cursor-pointer ${
                  selectedMethod === 'paystack'
                    ? 'border-blue-500 bg-blue-500/5 ring-2 ring-blue-500/20'
                    : processing
                    ? 'opacity-50 cursor-not-allowed border-gray-700'
                    : 'border-gray-700 hover:border-blue-500 hover:bg-blue-500/5'
                }`}
              >
                {/* Recommended Badge */}
                <div className="absolute -top-3 left-4 px-3 py-1 bg-gradient-to-r from-blue-500 to-blue-600 text-white text-xs font-bold rounded-full flex items-center space-x-1 shadow-lg">
                  <CheckCircle className="h-3 w-3" />
                  <span>RECOMMENDED FOR AFRICA</span>
                </div>
                <button
                  onClick={handlePaystackInit}
                  disabled={processing}
                  className="w-full text-left"
                >
                  <div className="flex items-start space-x-4">
                    <div className="p-3 bg-blue-500/20 rounded-lg flex-shrink-0">
                      {processing && selectedMethod === 'paystack' ? (
                        <Loader2 className="h-6 w-6 text-blue-400 animate-spin" />
                      ) : (
                        <CreditCard className="h-6 w-6 text-blue-400" />
                      )}
                    </div>
                    <div className="flex-1">
                      <h4 className="text-xl font-bold text-white mb-1">
                        Paystack
                      </h4>
                      <p className="text-sm text-gray-400 mb-3">
                        Perfect for African payments
                      </p>
                      <div className="flex flex-wrap gap-2 mb-3">
                        <span className="text-xs px-2 py-1 bg-blue-500/20 text-blue-300 rounded flex items-center space-x-1">
                          <span>💳</span>
                          <span>Cards</span>
                        </span>
                        <span className="text-xs px-2 py-1 bg-blue-500/20 text-blue-300 rounded flex items-center space-x-1">
                          <span>📱</span>
                          <span>Mobile Money</span>
                        </span>
                        <span className="text-xs px-2 py-1 bg-blue-500/20 text-blue-300 rounded flex items-center space-x-1">
                          <span>🏦</span>
                          <span>Bank Transfer</span>
                        </span>
                      </div>
                      <div className="flex items-center space-x-4 text-xs">
                        <span className="text-green-400 flex items-center">
                          <Zap className="h-3 w-3 mr-1" />
                          Instant credit
                        </span>
                        <span className="text-gray-500 flex items-center">
                          <Shield className="h-3 w-3 mr-1" />
                          Popup checkout
                        </span>
                      </div>
                    </div>
                  </div>
                </button>
              </motion.div>

              {/* Stripe Option */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
                className={`relative border-2 rounded-lg sm:rounded-xl p-3 sm:p-5 transition-all cursor-pointer ${
                  selectedMethod === 'stripe'
                    ? 'border-purple-500 bg-purple-500/5 ring-2 ring-purple-500/20'
                    : processing
                    ? 'opacity-50 cursor-not-allowed border-gray-700'
                    : 'border-gray-700 hover:border-purple-500 hover:bg-purple-500/5'
                }`}
              >
                {/* International Badge */}
                <div className="absolute -top-3 left-4 px-3 py-1 bg-gradient-to-r from-purple-500 to-purple-600 text-white text-xs font-bold rounded-full flex items-center space-x-1 shadow-lg">
                  <Globe className="h-3 w-3" />
                  <span>GLOBAL PAYMENTS</span>
                </div>

                <button
                  onClick={handleStripePayment}
                  disabled={processing}
                  className="w-full text-left"
                >
                  <div className="flex items-start space-x-4">
                    <div className="p-3 bg-purple-500/20 rounded-lg flex-shrink-0">
                      {processing && selectedMethod === 'stripe' ? (
                        <Loader2 className="h-6 w-6 text-purple-400 animate-spin" />
                      ) : (
                        <CreditCard className="h-6 w-6 text-purple-400" />
                      )}
                    </div>
                    <div className="flex-1">
                      <h4 className="text-xl font-bold text-white mb-1">
                        Stripe
                      </h4>
                      <p className="text-sm text-gray-400 mb-3">
                        Trusted worldwide payment gateway
                      </p>
                      <div className="flex flex-wrap gap-2 mb-3">
                        <span className="text-xs px-2 py-1 bg-purple-500/20 text-purple-300 rounded flex items-center space-x-1">
                          <span>💳</span>
                          <span>Cards</span>
                        </span>
                        <span className="text-xs px-2 py-1 bg-purple-500/20 text-purple-300 rounded flex items-center space-x-1">
                          <span>🍎</span>
                          <span>Apple Pay</span>
                        </span>
                        <span className="text-xs px-2 py-1 bg-purple-500/20 text-purple-300 rounded flex items-center space-x-1">
                          <span>🤖</span>
                          <span>Google Pay</span>
                        </span>
                      </div>
                      <div className="flex items-center space-x-4 text-xs">
                        <span className="text-green-400 flex items-center">
                          <Zap className="h-3 w-3 mr-1" />
                          Fast checkout
                        </span>
                        <span className="text-gray-500 flex items-center">
                          <Shield className="h-3 w-3 mr-1" />
                          PCI compliant
                        </span>
                      </div>
                    </div>
                  </div>
                </button>
              </motion.div>

              {/* ExpressPay Option - Ghana */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 }}
                className={`relative border-2 rounded-lg sm:rounded-xl p-3 sm:p-5 transition-all cursor-pointer ${
                  selectedMethod === 'expresspay'
                    ? 'border-green-500 bg-green-500/5 ring-2 ring-green-500/20'
                    : processing
                    ? 'opacity-50 cursor-not-allowed border-gray-700'
                    : 'border-gray-700 hover:border-green-500 hover:bg-green-500/5'
                }`}
              >
                {/* Ghana Badge */}
                <div className="absolute -top-3 left-4 px-3 py-1 bg-gradient-to-r from-green-500 to-green-600 text-white text-xs font-bold rounded-full flex items-center space-x-1 shadow-lg">
                  <span>🇬🇭</span>
                  <span>GHANA (GHS)</span>
                </div>

                <button
                  onClick={handleExpressPayPayment}
                  disabled={processing}
                  className="w-full text-left"
                >
                  <div className="flex items-start space-x-4">
                    <div className="p-3 bg-green-500/20 rounded-lg flex-shrink-0">
                      {processing && selectedMethod === 'expresspay' ? (
                        <Loader2 className="h-6 w-6 text-green-400 animate-spin" />
                      ) : (
                        <Smartphone className="h-6 w-6 text-green-400" />
                      )}
                    </div>
                    <div className="flex-1">
                      <h4 className="text-xl font-bold text-white mb-1">
                        ExpressPay
                      </h4>
                      <p className="text-sm text-gray-400 mb-3">
                        Best for Ghana - Mobile Money & Cards
                      </p>
                      <div className="flex flex-wrap gap-2 mb-3">
                        <span className="text-xs px-2 py-1 bg-green-500/20 text-green-300 rounded flex items-center space-x-1">
                          <span>📱</span>
                          <span>MTN MoMo</span>
                        </span>
                        <span className="text-xs px-2 py-1 bg-green-500/20 text-green-300 rounded flex items-center space-x-1">
                          <span>📱</span>
                          <span>Vodafone Cash</span>
                        </span>
                        <span className="text-xs px-2 py-1 bg-green-500/20 text-green-300 rounded flex items-center space-x-1">
                          <span>💳</span>
                          <span>Cards</span>
                        </span>
                      </div>
                      <div className="flex items-center space-x-4 text-xs">
                        <span className="text-green-400 flex items-center">
                          <Zap className="h-3 w-3 mr-1" />
                          Local payments
                        </span>
                        <span className="text-gray-500 flex items-center">
                          <Shield className="h-3 w-3 mr-1" />
                          Ghana Cedis
                        </span>
                      </div>
                    </div>
                  </div>
                </button>
              </motion.div>

              {/* Divider */}
              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-700"></div>
                </div>
              </div>

              {/* Cancel Button */}
              <button
                onClick={onClose}
                disabled={processing}
                className="w-full bg-gray-700 text-white py-3 rounded-xl font-semibold hover:bg-gray-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
            </div>

            {/* Info Text & Trust Indicators */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="relative z-10 mt-8 space-y-4"
            >
              <div className="flex items-center justify-center space-x-6 text-xs text-gray-500">
                <div className="flex items-center">
                  <Shield className="h-4 w-4 mr-1 text-green-400" />
                  <span>SSL Encrypted</span>
                </div>
                <div className="flex items-center">
                  <CheckCircle className="h-4 w-4 mr-1 text-green-400" />
                  <span>PCI Compliant</span>
                </div>
                <div className="flex items-center">
                  <Zap className="h-4 w-4 mr-1 text-yellow-400" />
                  <span>Instant Processing</span>
                </div>
              </div>

              <p className="text-xs text-gray-500 text-center">
                Join thousands of users who trust InkWave with their payments
              </p>

              <div className="text-center">
                <p className="text-xs text-gray-600">
                  Need help? <a href="/support" className="text-purple-400 hover:text-purple-300 underline">Contact Support</a>
                </p>
              </div>
            </motion.div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
