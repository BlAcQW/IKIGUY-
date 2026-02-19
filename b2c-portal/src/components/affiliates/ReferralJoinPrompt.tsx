/**
 * Referral Join Prompt Component
 * 
 * Shows a prompt to existing logged-in users when they click on a referral link,
 * asking if they want to join the affiliate program with the referral code.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { affiliateApi } from '@/lib/core-api';
import { getReferralCode, clearReferralData } from '@/lib/referral-tracking';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import { Award, CheckCircle, Info, Gift } from 'lucide-react';

interface ReferralJoinPromptProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  referralCode: string;
}

export const ReferralJoinPrompt: React.FC<ReferralJoinPromptProps> = ({
  open,
  onOpenChange,
  referralCode,
}) => {
  const [isJoining, setIsJoining] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleJoin = async () => {
    setIsJoining(true);
    setError(null);

    try {
      const profile = await affiliateApi.joinProgram({
        upline_referral_code: referralCode,
      });

      toast({
        title: 'Welcome to the affiliate program!',
        description: `Your referral code is: ${profile.referral_code}. Start sharing to earn commissions!`,
      });

      // Clear referral data since we've used it
      clearReferralData();

      // Close dialog and navigate to dashboard
      onOpenChange(false);
      navigate('/affiliates/dashboard');
    } catch (error: any) {
      console.error('Failed to join affiliate program:', error);
      const errorMessage =
        error.response?.data?.detail || error.message || 'Failed to join program';
      setError(errorMessage);

      // If user is already enrolled, just close and navigate
      if (error.response?.status === 400 && errorMessage.includes('already enrolled')) {
        onOpenChange(false);
        navigate('/affiliates/dashboard');
      }
    } finally {
      setIsJoining(false);
    }
  };

  const handleDismiss = () => {
    onOpenChange(false);
    // Keep referral data in cookie in case they want to join later
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-blue-100 rounded-full">
              <Gift className="h-6 w-6 text-blue-600" />
            </div>
            <DialogTitle className="text-xl">Join Our Affiliate Program?</DialogTitle>
          </div>
          <DialogDescription className="text-base pt-2">
            You clicked on a referral link! Would you like to join our affiliate program
            and start earning commissions by referring others?
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Referral Code Info */}
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              <div className="space-y-1">
                <p className="font-semibold">Referral Code: {referralCode}</p>
                <p className="text-sm">
                  By joining, you'll be linked to this affiliate and can start earning
                  from your own referrals too!
                </p>
              </div>
            </AlertDescription>
          </Alert>

          {/* Benefits */}
          <div className="bg-blue-50 rounded-lg p-4 space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold text-blue-900">
              <Award className="h-4 w-4" />
              <span>What you'll get:</span>
            </div>
            <ul className="list-disc list-inside space-y-1 text-sm text-blue-800 ml-6">
              <li>Earn 15% on direct referrals</li>
              <li>Earn 8% on tier 2 referrals</li>
              <li>Earn 3% on tier 3 referrals</li>
              <li>Get your own unique referral code</li>
              <li>Real-time tracking dashboard</li>
            </ul>
          </div>

          {/* Error Message */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            onClick={handleDismiss}
            disabled={isJoining}
            className="w-full sm:w-auto"
          >
            Maybe Later
          </Button>
          <Button
            onClick={handleJoin}
            disabled={isJoining}
            className="w-full sm:w-auto"
          >
            {isJoining ? (
              <>
                <span className="animate-spin mr-2">⏳</span>
                Joining...
              </>
            ) : (
              <>
                <CheckCircle className="h-4 w-4 mr-2" />
                Join Now
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

/**
 * Hook to manage referral join prompt for logged-in users
 */
export function useReferralJoinPrompt() {
  const [showPrompt, setShowPrompt] = useState(false);
  const [referralCode, setReferralCode] = useState<string | null>(null);
  const [hasChecked, setHasChecked] = useState(false);
  const { isAuthenticated, isLoading: authLoading } = useMongoAuth();

  useEffect(() => {
    const checkAndShowPrompt = async () => {
      // Only check once per session and wait for auth to be ready
      if (hasChecked || authLoading) return;

      // Only show prompt for logged-in users
      if (!isAuthenticated) {
        setHasChecked(true);
        return;
      }

      try {
        // Check if there's a referral code in cookie
        const code = getReferralCode();
        
        if (code) {
          // Check if user is already an affiliate
          try {
            await affiliateApi.getProfile();
            // User is already an affiliate, don't show prompt
            setHasChecked(true);
            return;
          } catch (error: any) {
            // If 404, user is not an affiliate - show prompt
            if (error.response?.status === 404) {
              setReferralCode(code);
              setShowPrompt(true);
              setHasChecked(true);
            } else {
              // Other errors, don't show prompt
              setHasChecked(true);
            }
          }
        } else {
          // No referral code, don't show prompt
          setHasChecked(true);
        }
      } catch (error) {
        console.error('[ReferralJoinPrompt] Error checking affiliate status:', error);
        setHasChecked(true);
      }
    };

    // Small delay to ensure auth state is ready
    const timer = setTimeout(checkAndShowPrompt, 1500);
    return () => clearTimeout(timer);
  }, [hasChecked, isAuthenticated, authLoading]);

  return {
    showPrompt,
    referralCode,
    setShowPrompt,
  };
}

