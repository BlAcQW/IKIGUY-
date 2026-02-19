/**
 * useReferralTracking Hook
 *
 * React hook for managing referral tracking throughout the application.
 * Handles:
 * - Automatic tracking on page load
 * - Referral data persistence
 * - Attribution after signup
 */

import { useEffect, useCallback } from 'react';
import { trackReferralClick, getReferralData, attributeSignup } from '@/lib/referral-tracking';

/**
 * Hook to track referral clicks automatically on page load
 */
export function useReferralTracking() {
  useEffect(() => {
    // Track referral on initial page load
    trackReferralClick().catch(error => {
      console.error('[useReferralTracking] Error:', error);
    });
  }, []);

  // Return referral data for use in components
  return {
    referralData: getReferralData()
  };
}

/**
 * Hook to handle signup attribution
 */
export function useSignupAttribution() {
  const handleAttributeSignup = useCallback(async (
    userId: string,
    organizationId: string
  ): Promise<boolean> => {
    try {
      const success = await attributeSignup(userId, organizationId);
      return success;
    } catch (error) {
      console.error('[useSignupAttribution] Error:', error);
      return false;
    }
  }, []);

  return {
    attributeSignup: handleAttributeSignup
  };
}
