/**
 * Wallet Store (Zustand)
 * Manages wallet balance and transactions
 */

import { create } from 'zustand';
import { api } from '../lib/api';
import toast from 'react-hot-toast';
import { WALLET } from '../config/constants';

interface Transaction {
  id: string;
  type: 'credit' | 'debit' | 'refund';
  amount: number;
  balance_after: number;
  description: string;
  created_at: string;
  metadata?: any;
}

interface WalletState {
  balance: number;
  currency: string;
  loading: boolean;
  transactions: Transaction[];

  // Computed
  isLowBalance: boolean;
  balanceInDollars: number;

  // Actions
  fetchBalance: () => Promise<void>;
  fetchTransactions: (limit?: number) => Promise<void>;
  topup: (amount: number, gateway: 'stripe' | 'paystack', email?: string) => Promise<{ success: boolean; url?: string }>;
  refresh: () => Promise<void>;
}

export const useWalletStore = create<WalletState>((set, get) => ({
  balance: 200, // $2.00 default (200 credits = $2)
  currency: 'USD',
  loading: false,
  transactions: [],

  get isLowBalance() {
    return get().balance < WALLET.LOW_BALANCE_THRESHOLD;
  },

  get balanceInDollars() {
    return get().balance / 100; // Convert credits to dollars
  },

  fetchBalance: async () => {
    try {
      set({ loading: true });
      const response = await api.wallet.get();
      set({
        balance: response.data.balance || 200,
        currency: response.data.currency || 'USD',
        loading: false,
      });
    } catch (error) {
      console.error('Failed to fetch wallet balance:', error);
      // Default to $2 on error
      set({
        balance: 200,
        currency: 'USD',
        loading: false,
      });
    }
  },

  fetchTransactions: async (limit = 20) => {
    try {
      const response = await api.wallet.transactions(limit);
      // Backend returns { user_id, transactions, total, limit, skip }
      const data = response.data;
      const transactions = data.transactions || data || [];

      set({ transactions });
    } catch (error: any) {
      // Silently fail if wallet endpoint not implemented
      if (error.response?.status === 500 || error.response?.status === 503) {
        console.warn('Wallet transactions service not available');
        set({ transactions: [] });
      } else {
        console.error('Failed to fetch transactions:', error);
        // Don't show toast error for missing wallet service
      }
    }
  },

  topup: async (amount: number, gateway: 'stripe' | 'paystack', email?: string) => {
    if (amount < WALLET.MIN_TOPUP || amount > WALLET.MAX_TOPUP) {
      toast.error(`Top-up amount must be between $${WALLET.MIN_TOPUP} and $${WALLET.MAX_TOPUP}`);
      return { success: false };
    }

    set({ loading: true });

    try {
      let response;

      if (gateway === 'stripe') {
        // Use new Stripe payment initiation endpoint
        const currentUrl = window.location.origin;
        const successUrl = `${currentUrl}/wallet?payment=success`;
        const cancelUrl = `${currentUrl}/wallet?payment=cancelled`;

        response = await api.wallet.initiateStripeTopup(amount, successUrl, cancelUrl);
      } else {
        // Use new Paystack payment initiation endpoint
        const callbackUrl = `${window.location.origin}/wallet?payment=success`;
        response = await api.wallet.initiatePaystackTopup(amount, callbackUrl);
      }

      const data = response.data;

      set({ loading: false });

      // Redirect to payment page
      if (data.success && data.payment_url) {
        toast.success('Redirecting to payment page...');
        window.location.href = data.payment_url;
        return { success: true, url: data.payment_url };
      } else {
        toast.error(data.error || 'Failed to initiate payment');
        return { success: false };
      }
    } catch (error: any) {
      console.error('Top-up failed:', error);
      const errorMessage = error.response?.data?.detail || error.response?.data?.error || 'Top-up failed';
      toast.error(errorMessage);
      set({ loading: false });
      return { success: false };
    }
  },

  refresh: async () => {
    await Promise.all([
      get().fetchBalance(),
      get().fetchTransactions(),
    ]);
  },
}));
