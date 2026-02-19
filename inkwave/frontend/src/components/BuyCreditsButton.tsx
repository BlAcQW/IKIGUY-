/**
 * BuyCreditsButton
 * In-player button to quickly access credits/wallet functionality
 * Shows balance and opens payment modal for quick top-ups
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wallet, Plus, AlertCircle, ChevronDown, X } from 'lucide-react';
import { useWalletStore } from '../store/walletStore';
import PaymentOptionsModal from './PaymentOptionsModal';
import { TOPUP_PACKAGES, WALLET } from '../config/constants';

interface BuyCreditsButtonProps {
  /** Compact mode for smaller displays */
  compact?: boolean;
  /** Show as icon only (no balance text) */
  iconOnly?: boolean;
  /** Custom class name */
  className?: string;
}

export default function BuyCreditsButton({
  compact = false,
  iconOnly = false,
  className = '',
}: BuyCreditsButtonProps) {
  const { balance, fetchBalance } = useWalletStore();
  const [showQuickMenu, setShowQuickMenu] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedAmount, setSelectedAmount] = useState(10); // Default to popular package

  const isLowBalance = balance < WALLET.LOW_BALANCE_THRESHOLD;
  const balanceInCurrency = (balance / 100).toFixed(2);

  const handleQuickTopUp = (amount: number) => {
    setSelectedAmount(amount);
    setShowQuickMenu(false);
    setShowPaymentModal(true);
  };

  const handlePaymentSuccess = () => {
    fetchBalance();
    setShowPaymentModal(false);
  };

  // Icon only mode (for very compact layouts)
  if (iconOnly) {
    return (
      <>
        <button
          onClick={() => setShowQuickMenu(!showQuickMenu)}
          className={`relative p-2 rounded-full transition-all ${
            isLowBalance
              ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
              : 'bg-purple-500/20 text-purple-400 hover:bg-purple-500/30'
          } ${className}`}
          title={`Balance: GH₵${balanceInCurrency}`}
        >
          <Wallet className="h-5 w-5" />
          {isLowBalance && (
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse" />
          )}
        </button>

        {/* Quick Menu Dropdown */}
        <AnimatePresence>
          {showQuickMenu && (
            <QuickTopUpMenu
              onClose={() => setShowQuickMenu(false)}
              onSelectAmount={handleQuickTopUp}
              balance={balance}
              balanceInCurrency={balanceInCurrency}
              isLowBalance={isLowBalance}
            />
          )}
        </AnimatePresence>

        <PaymentOptionsModal
          isOpen={showPaymentModal}
          onClose={() => setShowPaymentModal(false)}
          amount={selectedAmount}
          onSuccess={handlePaymentSuccess}
        />
      </>
    );
  }

  // Compact mode (balance + icon)
  if (compact) {
    return (
      <>
        <button
          onClick={() => setShowQuickMenu(!showQuickMenu)}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg transition-all text-sm ${
            isLowBalance
              ? 'bg-red-500/20 border border-red-500/30 text-red-400 hover:bg-red-500/30'
              : 'bg-purple-500/20 border border-purple-500/30 text-purple-300 hover:bg-purple-500/30'
          } ${className}`}
        >
          <Wallet className="h-4 w-4" />
          <span className="font-medium">GH₵{balanceInCurrency}</span>
          {isLowBalance && <AlertCircle className="h-3 w-3" />}
          <ChevronDown className="h-3 w-3" />
        </button>

        {/* Quick Menu Dropdown */}
        <AnimatePresence>
          {showQuickMenu && (
            <QuickTopUpMenu
              onClose={() => setShowQuickMenu(false)}
              onSelectAmount={handleQuickTopUp}
              balance={balance}
              balanceInCurrency={balanceInCurrency}
              isLowBalance={isLowBalance}
            />
          )}
        </AnimatePresence>

        <PaymentOptionsModal
          isOpen={showPaymentModal}
          onClose={() => setShowPaymentModal(false)}
          amount={selectedAmount}
          onSuccess={handlePaymentSuccess}
        />
      </>
    );
  }

  // Full mode (with "Top Up" text)
  return (
    <>
      <div className="relative">
        <button
          onClick={() => setShowQuickMenu(!showQuickMenu)}
          className={`flex items-center gap-2 px-3 py-2 rounded-xl transition-all ${
            isLowBalance
              ? 'bg-red-500/20 border border-red-500/30 text-red-400 hover:bg-red-500/30'
              : 'bg-purple-500/20 border border-purple-500/30 text-purple-300 hover:bg-purple-500/30'
          } ${className}`}
        >
          <Wallet className="h-5 w-5" />
          <div className="text-left">
            <p className="text-xs opacity-70">Balance</p>
            <p className="font-semibold">GH₵{balanceInCurrency}</p>
          </div>
          <Plus className="h-4 w-4 ml-1" />
        </button>

        {/* Quick Menu Dropdown */}
        <AnimatePresence>
          {showQuickMenu && (
            <QuickTopUpMenu
              onClose={() => setShowQuickMenu(false)}
              onSelectAmount={handleQuickTopUp}
              balance={balance}
              balanceInCurrency={balanceInCurrency}
              isLowBalance={isLowBalance}
              position="bottom"
            />
          )}
        </AnimatePresence>
      </div>

      <PaymentOptionsModal
        isOpen={showPaymentModal}
        onClose={() => setShowPaymentModal(false)}
        amount={selectedAmount}
        onSuccess={handlePaymentSuccess}
      />
    </>
  );
}

// Quick Top Up Menu Component
function QuickTopUpMenu({
  onClose,
  onSelectAmount,
  balance,
  balanceInCurrency,
  isLowBalance,
  position = 'center',
}: {
  onClose: () => void;
  onSelectAmount: (amount: number) => void;
  balance: number;
  balanceInCurrency: string;
  isLowBalance: boolean;
  position?: 'bottom' | 'center';
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.9, opacity: 0, y: 20 }}
        className="bg-gray-800 border border-gray-700 rounded-2xl p-5 w-full max-w-sm shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className={`p-2 rounded-lg ${isLowBalance ? 'bg-red-500/20' : 'bg-purple-500/20'}`}>
              <Wallet className={`h-5 w-5 ${isLowBalance ? 'text-red-400' : 'text-purple-400'}`} />
            </div>
            <div>
              <p className="text-xs text-gray-400">Current Balance</p>
              <p className={`font-bold text-lg ${isLowBalance ? 'text-red-400' : 'text-white'}`}>
                GH₵{balanceInCurrency}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-gray-700 rounded-full transition"
          >
            <X className="h-5 w-5 text-gray-400" />
          </button>
        </div>

        {/* Low Balance Warning */}
        {isLowBalance && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-4 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0" />
            <p className="text-xs text-red-300">
              Low balance! Top up to continue listening.
            </p>
          </div>
        )}

        {/* Quick Top Up Options */}
        <div className="space-y-2">
          <p className="text-xs text-gray-400 mb-2">Quick Top Up</p>
          <div className="grid grid-cols-2 gap-2">
            {TOPUP_PACKAGES.map((pkg) => (
              <button
                key={pkg.amount}
                onClick={() => onSelectAmount(pkg.amount)}
                className={`relative p-3 rounded-xl border-2 transition-all hover:scale-[1.02] ${
                  pkg.popular
                    ? 'border-purple-500 bg-purple-500/10 hover:bg-purple-500/20'
                    : 'border-gray-700 bg-gray-800/50 hover:border-purple-400 hover:bg-gray-700/50'
                }`}
              >
                {pkg.popular && (
                  <span className="absolute -top-2 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-purple-500 text-[10px] font-bold text-white rounded-full">
                    POPULAR
                  </span>
                )}
                <p className="font-bold text-white text-lg">GH₵{pkg.amount}</p>
                <p className="text-xs text-gray-400">{pkg.credits} credits</p>
                {pkg.bonus > 0 && (
                  <p className="text-xs text-purple-400">+{pkg.bonus} bonus</p>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Info Text */}
        <p className="text-[10px] text-gray-500 text-center mt-4">
          Secure payment via Paystack, Stripe, or ExpressPay
        </p>
      </motion.div>
    </motion.div>
  );
}
