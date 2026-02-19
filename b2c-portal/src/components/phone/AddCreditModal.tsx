/**
 * Add Credit Modal Component
 * Allows adding credit to phone numbers with payment tracking
 */

import React, { useState } from 'react';
import { X, DollarSign, CreditCard } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import type { PhoneNumber } from '@/lib/phone-api-client';
import { addPhoneCredit } from '@/lib/phone-api-client';

interface AddCreditModalProps {
  isOpen: boolean;
  onClose: () => void;
  phone: PhoneNumber | null;
  onSuccess: () => void;
}

export const AddCreditModal: React.FC<AddCreditModalProps> = ({
  isOpen,
  onClose,
  phone,
  onSuccess
}) => {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    amount: '',
    payment_method: 'mobile_money',
    reference_number: '',
    notes: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!phone) return;

    const amount = parseFloat(formData.amount);
    if (isNaN(amount) || amount <= 0) {
      toast({
        title: 'Invalid Amount',
        description: 'Please enter a valid amount greater than 0',
        variant: 'destructive'
      });
      return;
    }

    try {
      setIsSubmitting(true);

      await addPhoneCredit(phone.id, {
        amount,
        payment_method: formData.payment_method,
        reference_number: formData.reference_number || undefined,
        notes: formData.notes || undefined
      });

      toast({
        title: 'Credit Added Successfully',
        description: `Added ${phone.currency} ${amount.toFixed(2)} to ${phone.number}`
      });

      // Reset form
      setFormData({
        amount: '',
        payment_method: 'mobile_money',
        reference_number: '',
        notes: ''
      });

      onSuccess();
      onClose();
    } catch (error: any) {
      toast({
        title: 'Failed to Add Credit',
        description: error.message,
        variant: 'destructive'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen || !phone) return null;

  const remainingMinutes = phone.cost_per_minute > 0
    ? phone.credit_balance / phone.cost_per_minute
    : 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card border border-border rounded-lg shadow-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div>
            <h2 className="text-lg font-semibold">Add Credit</h2>
            <p className="text-sm text-muted-foreground mt-1">{phone.number}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-accent rounded-md transition-colors"
            disabled={isSubmitting}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Current Balance Info */}
        <div className="p-4 bg-muted/50">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Current Balance</p>
              <p className="text-lg font-semibold">
                {phone.currency} {phone.credit_balance.toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Remaining Minutes</p>
              <p className="text-lg font-semibold">
                {remainingMinutes.toFixed(1)} min
              </p>
            </div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Amount */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Amount ({phone.currency}) *
            </label>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                className="w-full pl-10 pr-4 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="0.00"
                disabled={isSubmitting}
              />
            </div>
            {formData.amount && !isNaN(parseFloat(formData.amount)) && phone.cost_per_minute > 0 && (
              <p className="mt-1 text-sm text-muted-foreground">
                Will add ~{(parseFloat(formData.amount) / phone.cost_per_minute).toFixed(1)} minutes
              </p>
            )}
          </div>

          {/* Payment Method */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Payment Method *
            </label>
            <select
              value={formData.payment_method}
              onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
              className="w-full px-4 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              disabled={isSubmitting}
            >
              <option value="mobile_money">Mobile Money</option>
              <option value="bank_transfer">Bank Transfer</option>
              <option value="cash">Cash</option>
              <option value="credit_card">Credit Card</option>
              <option value="other">Other</option>
            </select>
          </div>

          {/* Reference Number */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Reference Number
            </label>
            <input
              type="text"
              value={formData.reference_number}
              onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })}
              className="w-full px-4 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Transaction reference (optional)"
              disabled={isSubmitting}
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Notes
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              rows={3}
              className="w-full px-4 py-2 border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary resize-none"
              placeholder="Additional notes (optional)"
              disabled={isSubmitting}
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 border border-border rounded-md hover:bg-accent transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Adding...
                </>
              ) : (
                <>
                  <CreditCard className="w-4 h-4 mr-2" />
                  Add Credit
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
