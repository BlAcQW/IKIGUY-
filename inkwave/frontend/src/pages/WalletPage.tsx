/**
 * WalletPage
 * Wallet management and top-up
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Wallet,
  Plus,
  History,
  TrendingUp,
  Headphones,
  Mic,
  CreditCard,
  ArrowUpCircle,
  ArrowDownCircle,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  Clock,
  DollarSign,
  CheckCircle,
  XCircle,
  Loader2,
  X
} from 'lucide-react';
import { useWalletStore } from '../store/walletStore';
import { TOPUP_PACKAGES, PRICING } from '../config/constants';
import toast from 'react-hot-toast';
import PaymentOptionsModal from '../components/PaymentOptionsModal';
import { api } from '../lib/api';

// Payment result interface
interface PaymentResult {
  success: boolean;
  status: 'completed' | 'declined' | 'pending' | 'error' | 'cancelled';
  message: string;
  transaction?: {
    order_id: string;
    transaction_id?: string;
    amount?: number;
    currency?: string;
    payment_method?: string;
    date_processed?: string;
    card_last4?: string;
    card_type?: string;
    status_message?: string;
  };
}

// Mock usage data
const MOCK_USAGE = {
  narration: { minutes: 120, cost: 240 }, // 2 hours
  voiceQA: { questions: 15, cost: 60 },
  total: 300,
};

// Payment Result Modal Component
function PaymentResultModal({
  isOpen,
  onClose,
  result,
  isLoading
}: {
  isOpen: boolean;
  onClose: () => void;
  result: PaymentResult | null;
  isLoading: boolean;
}) {
  if (!isOpen) return null;

  const getStatusIcon = () => {
    if (isLoading) return <Loader2 className="h-16 w-16 text-purple-400 animate-spin" />;
    if (result?.status === 'completed') return <CheckCircle className="h-16 w-16 text-green-400" />;
    if (result?.status === 'pending') return <Clock className="h-16 w-16 text-yellow-400" />;
    return <XCircle className="h-16 w-16 text-red-400" />;
  };

  const getStatusColor = () => {
    if (result?.status === 'completed') return 'from-green-500/20 to-emerald-500/20 border-green-500/30';
    if (result?.status === 'pending') return 'from-yellow-500/20 to-orange-500/20 border-yellow-500/30';
    return 'from-red-500/20 to-pink-500/20 border-red-500/30';
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className={`bg-gradient-to-br ${isLoading ? 'from-purple-500/20 to-pink-500/20 border-purple-500/30' : getStatusColor()} border rounded-2xl p-8 max-w-md w-full shadow-2xl`}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Close button */}
          {!isLoading && (
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
            >
              <X className="h-6 w-6" />
            </button>
          )}

          {/* Status Icon */}
          <div className="flex justify-center mb-6">
            {getStatusIcon()}
          </div>

          {/* Title */}
          <h2 className="text-2xl font-bold text-white text-center mb-2">
            {isLoading ? 'Verifying Payment...' :
              result?.status === 'completed' ? 'Payment Successful!' :
              result?.status === 'pending' ? 'Payment Pending' :
              result?.status === 'cancelled' ? 'Payment Cancelled' :
              'Payment Failed'}
          </h2>

          {/* Message */}
          <p className="text-gray-400 text-center mb-6">
            {isLoading ? 'Please wait while we confirm your payment...' : result?.message}
          </p>

          {/* Transaction Details */}
          {result?.transaction && result.status === 'completed' && (
            <div className="bg-gray-800/50 rounded-xl p-4 space-y-3 mb-6">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">Transaction Details</h3>

              {result.transaction.amount && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Amount</span>
                  <span className="text-white font-semibold">
                    {result.transaction.currency || 'GHS'} {result.transaction.amount}
                  </span>
                </div>
              )}

              {result.transaction.transaction_id && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Transaction ID</span>
                  <span className="text-white font-mono text-sm">
                    {result.transaction.transaction_id}
                  </span>
                </div>
              )}

              {result.transaction.payment_method && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Payment Method</span>
                  <span className="text-white capitalize">
                    {result.transaction.payment_method}
                  </span>
                </div>
              )}

              {result.transaction.card_last4 && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Card</span>
                  <span className="text-white">
                    {result.transaction.card_type || 'Card'} ending in {result.transaction.card_last4}
                  </span>
                </div>
              )}

              {result.transaction.date_processed && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Date</span>
                  <span className="text-white text-sm">
                    {new Date(result.transaction.date_processed).toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Action Button */}
          {!isLoading && (
            <button
              onClick={onClose}
              className={`w-full py-3 rounded-xl font-semibold transition-all ${
                result?.status === 'completed'
                  ? 'bg-green-500 hover:bg-green-600 text-white'
                  : 'bg-gray-700 hover:bg-gray-600 text-white'
              }`}
            >
              {result?.status === 'completed' ? 'Continue' : 'Close'}
            </button>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

export default function WalletPage() {
	useEffect(() => {
		document.title = 'Wallet - InkWave';
	}, []);

  const { balance, fetchBalance, transactions, fetchTransactions } = useWalletStore();
  const [selectedPackage, setSelectedPackage] = useState<number | null>(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedAmount, setSelectedAmount] = useState<number>(0);
  const [showAllTransactions, setShowAllTransactions] = useState(false);
  const [loadingTransactions, setLoadingTransactions] = useState(true);

  // Payment result modal state
  const [showPaymentResult, setShowPaymentResult] = useState(false);
  const [paymentResult, setPaymentResult] = useState<PaymentResult | null>(null);
  const [verifyingPayment, setVerifyingPayment] = useState(false);

  useEffect(() => {
    fetchBalance();
    // Fetch transactions on mount
    const loadTransactions = async () => {
      setLoadingTransactions(true);
      await fetchTransactions(50); // Fetch up to 50 transactions
      setLoadingTransactions(false);
    };
    loadTransactions();
  }, [fetchBalance, fetchTransactions]);

  // Check for payment callback in URL (handles ExpressPay redirect)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const paymentStatus = params.get('payment');
    const orderId = params.get('order-id') || params.get('order_id');
    const token = params.get('token');
    const amount = params.get('amount');
    const txId = params.get('tx_id');
    const reason = params.get('reason');

    // Handle ExpressPay callback with order-id and token
    if (orderId && token) {
      handleExpressPayCallback(orderId, token);
      return;
    }

    // Handle simple status callbacks (Stripe/Paystack)
    if (paymentStatus === 'success') {
      // Show success modal with available details
      setPaymentResult({
        success: true,
        status: 'completed',
        message: 'Payment completed successfully! Your wallet has been credited.',
        transaction: {
          order_id: orderId || 'N/A',
          transaction_id: txId || undefined,
          amount: amount ? parseFloat(amount) : undefined,
        }
      });
      setShowPaymentResult(true);
      fetchBalance();
      fetchTransactions(50);
      // Clean up URL
      window.history.replaceState({}, '', '/wallet');
    } else if (paymentStatus === 'cancelled') {
      setPaymentResult({
        success: false,
        status: 'cancelled',
        message: 'Payment was cancelled. No charges were made.',
      });
      setShowPaymentResult(true);
      window.history.replaceState({}, '', '/wallet');
    } else if (paymentStatus === 'error' || paymentStatus === 'declined' || paymentStatus === 'failed') {
      setPaymentResult({
        success: false,
        status: paymentStatus as 'error' | 'declined',
        message: reason ? decodeURIComponent(reason) : 'Payment could not be completed. Please try again.',
      });
      setShowPaymentResult(true);
      window.history.replaceState({}, '', '/wallet');
    } else if (paymentStatus === 'pending') {
      setPaymentResult({
        success: false,
        status: 'pending',
        message: 'Payment is being processed. We will notify you once confirmed.',
      });
      setShowPaymentResult(true);
      window.history.replaceState({}, '', '/wallet');
    }
  }, [fetchBalance, fetchTransactions]);

  // Handle ExpressPay callback verification
  const handleExpressPayCallback = async (orderId: string, token: string) => {
    setShowPaymentResult(true);
    setVerifyingPayment(true);

    try {
      const response = await api.wallet.getPaymentCallback(orderId, token);
      const data = response.data;

      setPaymentResult({
        success: data.success,
        status: data.status,
        message: data.message,
        transaction: data.transaction,
      });

      if (data.success) {
        fetchBalance();
        fetchTransactions(50);
      }
    } catch (error: any) {
      console.error('Payment verification failed:', error);
      setPaymentResult({
        success: false,
        status: 'error',
        message: error.response?.data?.detail || 'Failed to verify payment. Please contact support.',
      });
    } finally {
      setVerifyingPayment(false);
      // Clean up URL
      window.history.replaceState({}, '', '/wallet');
    }
  };

  // Close payment result modal
  const handleClosePaymentResult = () => {
    setShowPaymentResult(false);
    setPaymentResult(null);
  };

  const balanceInCurrency = (balance / 100).toFixed(2);

  const handleTopUp = (pkg: typeof TOPUP_PACKAGES[0]) => {
    setSelectedPackage(pkg.amount);
    setSelectedAmount(pkg.amount);
    setShowPaymentModal(true);
  };

  const handlePaymentSuccess = () => {
    fetchBalance();
    fetchTransactions(50); // Refresh transactions after payment
    setSelectedPackage(null);
    setSelectedAmount(0);
  };

  // Helper function to get transaction icon
  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'credit':
        return <ArrowUpCircle className="h-5 w-5 text-green-400" />;
      case 'debit':
        return <ArrowDownCircle className="h-5 w-5 text-red-400" />;
      case 'refund':
        return <RotateCcw className="h-5 w-5 text-blue-400" />;
      default:
        return <DollarSign className="h-5 w-5 text-gray-400" />;
    }
  };

  // Helper function to get transaction color
  const getTransactionColor = (type: string) => {
    switch (type) {
      case 'credit':
        return 'text-green-400';
      case 'debit':
        return 'text-red-400';
      case 'refund':
        return 'text-blue-400';
      default:
        return 'text-gray-400';
    }
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Get transactions to display (limited or all)
  const displayedTransactions = showAllTransactions
    ? transactions
    : transactions.slice(0, 5);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen bg-gray-950 py-12 px-4"
    >
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Wallet</h1>
          <p className="text-gray-400">
            Manage your credits and track your usage
          </p>
        </div>

        {/* Balance Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30 rounded-2xl p-8"
        >
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
            <div>
              <p className="text-gray-400 mb-2">Current Balance</p>
              <div className="flex items-center space-x-3">
                <Wallet className="h-10 w-10 text-purple-400" />
                <p className="text-5xl font-bold text-white">
                  GH₵{balanceInCurrency}
                </p>
              </div>
              <p className="text-gray-400 mt-2">{balance} credits</p>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-800/50 rounded-lg p-3">
                <div className="flex items-center space-x-2 mb-1">
                  <Headphones className="h-4 w-4 text-purple-400" />
                  <p className="text-xs text-gray-400">Narration</p>
                </div>
                <p className="text-lg font-bold text-white">
                  ~{Math.floor(balance / (PRICING.NARRATION_PER_MINUTE * 100))}m
                </p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <div className="flex items-center space-x-2 mb-1">
                  <Mic className="h-4 w-4 text-pink-400" />
                  <p className="text-xs text-gray-400">Voice Q&A</p>
                </div>
                <p className="text-lg font-bold text-white">
                  ~{Math.floor(balance / (PRICING.VOICE_QA_AVERAGE * 100))}x
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Usage Breakdown */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center space-x-2">
            <TrendingUp className="h-6 w-6" />
            <span>This Month's Usage</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-800 rounded-xl p-6">
              <div className="flex items-center space-x-3 mb-3">
                <div className="p-2 bg-purple-500/20 rounded-lg">
                  <Headphones className="h-5 w-5 text-purple-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Audio Narration</p>
                  <p className="text-2xl font-bold text-white">
                    {MOCK_USAGE.narration.minutes}m
                  </p>
                </div>
              </div>
              <p className="text-xs text-gray-500">
                {MOCK_USAGE.narration.cost} credits spent
              </p>
            </div>

            <div className="bg-gray-800 rounded-xl p-6">
              <div className="flex items-center space-x-3 mb-3">
                <div className="p-2 bg-pink-500/20 rounded-lg">
                  <Mic className="h-5 w-5 text-pink-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Voice Q&A</p>
                  <p className="text-2xl font-bold text-white">
                    {MOCK_USAGE.voiceQA.questions}
                  </p>
                </div>
              </div>
              <p className="text-xs text-gray-500">
                {MOCK_USAGE.voiceQA.cost} credits spent
              </p>
            </div>

            <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-xl p-6">
              <div className="flex items-center space-x-3 mb-3">
                <div className="p-2 bg-purple-500/20 rounded-lg">
                  <Wallet className="h-5 w-5 text-purple-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Total Spent</p>
                  <p className="text-2xl font-bold text-white">
                    GH₵{(MOCK_USAGE.total / 100).toFixed(2)}
                  </p>
                </div>
              </div>
              <p className="text-xs text-gray-500">
                {MOCK_USAGE.total} credits
              </p>
            </div>
          </div>
        </motion.div>

        {/* Top-up Packages */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="relative"
        >
          {/* Prominent section header with gradient background */}
          <div className="bg-gradient-to-r from-purple-500/10 via-pink-500/10 to-purple-500/10 rounded-2xl p-6 mb-6 border border-purple-500/20">
            <h2 className="text-3xl font-bold text-white mb-2 flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-br from-purple-500/30 to-pink-500/30 rounded-xl">
                <Plus className="h-8 w-8 text-purple-400" />
              </div>
              <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                Top Up Credits
              </span>
            </h2>
            <p className="text-gray-400 text-sm ml-14">
              Choose a package below to add credits to your wallet instantly
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {TOPUP_PACKAGES.map((pkg, index) => (
              <motion.div
                key={pkg.amount}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.3 + index * 0.1 }}
                whileHover={{ scale: 1.05, y: -5 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleTopUp(pkg)}
                className={`bg-gray-800 rounded-xl p-6 border-2 transition-all duration-300 cursor-pointer relative overflow-hidden group ${
                  pkg.popular
                    ? 'border-purple-500 shadow-lg shadow-purple-500/20 hover:shadow-xl hover:shadow-purple-500/30'
                    : selectedPackage === pkg.amount
                    ? 'border-pink-500 shadow-lg shadow-pink-500/20'
                    : 'border-gray-700 hover:border-purple-400 hover:shadow-lg hover:shadow-purple-500/10'
                }`}
              >
                {/* Animated gradient background on hover */}
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/0 to-pink-500/0 group-hover:from-purple-500/10 group-hover:to-pink-500/10 transition-all duration-300"></div>

                {/* Content */}
                <div className="relative z-10">
                  {pkg.popular && (
                    <span className="inline-block px-3 py-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs font-semibold rounded-full mb-3 shadow-lg">
                      MOST POPULAR
                    </span>
                  )}
                  <p className="text-4xl font-bold text-white mb-2 group-hover:text-purple-300 transition-colors">
                    GH₵{pkg.amount}
                  </p>
                  <p className="text-gray-400 mb-2">
                    {pkg.credits} credits
                    {pkg.bonus > 0 && (
                      <span className="text-purple-400 font-semibold"> + {pkg.bonus} bonus</span>
                    )}
                  </p>
                  <div className="pt-3 border-t border-gray-700 mt-3">
                    <p className="text-xs text-gray-500">
                      ≈ {Math.floor(pkg.credits / (PRICING.NARRATION_PER_MINUTE * 100))}m narration
                      <span className="text-gray-600"> or </span>
                      {Math.floor(pkg.credits / (PRICING.VOICE_QA_AVERAGE * 100))} Q&A
                    </p>
                  </div>

                  {/* Click to continue indicator */}
                  <div className="mt-4 pt-3 border-t border-gray-700 opacity-0 group-hover:opacity-100 transition-opacity">
                    <p className="text-xs text-purple-400 font-semibold text-center">
                      Click to choose payment method →
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
          {/* Enhanced payment info banner */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="mt-6 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 border border-blue-500/30 rounded-xl p-5"
          >
            <div className="flex items-start space-x-3">
              <div className="p-2 bg-blue-500/20 rounded-lg flex-shrink-0">
                <CreditCard className="h-5 w-5 text-blue-400" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-blue-300 mb-1">
                  Secure & Flexible Payments
                </p>
                <p className="text-xs text-gray-400">
                  Choose between <span className="text-blue-400 font-semibold">Paystack</span> (recommended for Africa - supports cards, mobile money, bank transfers) or <span className="text-purple-400 font-semibold">Stripe</span> (global payments - supports cards, Apple Pay, Google Pay). All transactions are encrypted and PCI-compliant.
                </p>
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* Payment Options Modal */}
        <PaymentOptionsModal
          isOpen={showPaymentModal}
          onClose={() => setShowPaymentModal(false)}
          amount={selectedAmount}
          onSuccess={handlePaymentSuccess}
        />

        {/* Payment Result Modal */}
        <PaymentResultModal
          isOpen={showPaymentResult}
          onClose={handleClosePaymentResult}
          result={paymentResult}
          isLoading={verifyingPayment}
        />

        {/* Transaction History */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center space-x-2">
            <History className="h-6 w-6" />
            <span>Recent Transactions</span>
          </h2>
          <div className="bg-gray-800 rounded-xl overflow-hidden">
            {loadingTransactions ? (
              // Loading state
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
                <p className="text-gray-400">Loading transactions...</p>
              </div>
            ) : transactions.length === 0 ? (
              // Empty state
              <div className="p-8 text-center">
                <History className="h-16 w-16 text-gray-700 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-400 mb-2">
                  No transactions yet
                </h3>
                <p className="text-sm text-gray-500 max-w-sm mx-auto">
                  Your transaction history will appear here once you start using
                  credits or top up your wallet.
                </p>
              </div>
            ) : (
              // Transaction list
              <div>
                <AnimatePresence>
                  {displayedTransactions.map((tx, index) => (
                    <motion.div
                      key={tx.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ delay: index * 0.05 }}
                      className={`p-4 flex items-center justify-between hover:bg-gray-700/50 transition-colors ${
                        index !== displayedTransactions.length - 1 ? 'border-b border-gray-700' : ''
                      }`}
                    >
                      <div className="flex items-center space-x-4">
                        <div className="p-2 bg-gray-700 rounded-lg">
                          {getTransactionIcon(tx.type)}
                        </div>
                        <div>
                          <p className="text-white font-medium">{tx.description}</p>
                          <div className="flex items-center space-x-2 text-xs text-gray-500">
                            <Clock className="h-3 w-3" />
                            <span>{formatDate(tx.created_at)}</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`font-bold ${getTransactionColor(tx.type)}`}>
                          {tx.type === 'credit' || tx.type === 'refund' ? '+' : '-'}
                          GH₵{(Math.abs(tx.amount) / 100).toFixed(2)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {tx.type === 'credit' || tx.type === 'refund' ? '+' : '-'}
                          {Math.abs(tx.amount).toFixed(0)} credits
                        </p>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>

                {/* Show more/less button */}
                {transactions.length > 5 && (
                  <button
                    onClick={() => setShowAllTransactions(!showAllTransactions)}
                    className="w-full p-4 flex items-center justify-center space-x-2 text-purple-400 hover:text-purple-300 hover:bg-gray-700/50 transition-colors border-t border-gray-700"
                  >
                    {showAllTransactions ? (
                      <>
                        <ChevronUp className="h-4 w-4" />
                        <span>Show less</span>
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-4 w-4" />
                        <span>Show all {transactions.length} transactions</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            )}
          </div>
        </motion.div>

        {/* Pricing Info */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="bg-gray-800/50 rounded-xl p-6"
        >
          <h3 className="text-lg font-semibold text-white mb-4">
            💡 How Credits Work
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-400 mb-1">
                <span className="text-white font-semibold">Audio Narration:</span>
              </p>
              <p className="text-gray-500">
                {PRICING.NARRATION_PER_MINUTE * 100} credits per minute
                (GH₵{PRICING.NARRATION_PER_MINUTE}/min)
              </p>
            </div>
            <div>
              <p className="text-gray-400 mb-1">
                <span className="text-white font-semibold">Voice Q&A:</span>
              </p>
              <p className="text-gray-500">
                ~{PRICING.VOICE_QA_AVERAGE * 100} credits per question
                (~GH₵{PRICING.VOICE_QA_AVERAGE}/question)
              </p>
            </div>
          </div>
          <p className="text-xs text-gray-600 mt-4">
            * Voice Q&A costs vary based on question length and answer complexity.
            100 credits = GH₵1
          </p>
        </motion.div>
      </div>
    </motion.div>
  );
}
