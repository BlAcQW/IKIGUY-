/**
 * Post-Signup Affiliate Join Prompt
 * 
 * Shows a prompt to newly registered users asking if they want to join
 * the affiliate program after successful signup.
 */

import React, { useState } from 'react';
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
import { getReferralCode } from '@/lib/referral-tracking';
import { Award, CheckCircle, Info, X, Gift } from 'lucide-react';

interface PostSignupAffiliatePromptProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  userId: string;
  organizationId: string;
}

export const PostSignupAffiliatePrompt: React.FC<PostSignupAffiliatePromptProps> = ({
  open,
  onOpenChange,
  userId,
  organizationId,
}) => {
  const [isJoining, setIsJoining] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();
  const navigate = useNavigate();
  const referralCode = getReferralCode();

  const handleJoin = async () => {
    setIsJoining(true);
    setError(null);

    try {
      const profile = await affiliateApi.joinProgram(
        referralCode ? { upline_referral_code: referralCode } : undefined
      );

      toast({
        title: 'Welcome to the affiliate program!',
        description: `Your referral code is: ${profile.referral_code}. Start sharing to earn commissions!`,
      });

      // Close dialog and navigate to dashboard
      onOpenChange(false);
      navigate('/affiliates/dashboard');
    } catch (error: any) {
      console.error('Failed to join affiliate program:', error);
      const errorMessage =
        error.response?.data?.detail || error.message || 'Failed to join program';
      setError(errorMessage);

      // If user is already enrolled, just close
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
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-green-100 rounded-full">
              <Award className="h-6 w-6 text-green-600" />
            </div>
            <DialogTitle className="text-xl">Join Our Affiliate Program?</DialogTitle>
          </div>
          <DialogDescription className="text-base pt-2">
            Great! Your account has been created. Would you like to join our affiliate program
            and start earning commissions by referring others?
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Benefits */}
          <div className="bg-green-50 rounded-lg p-4 space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold text-green-900">
              <Gift className="h-4 w-4" />
              <span>What you'll get:</span>
            </div>
            <ul className="list-disc list-inside space-y-1 text-sm text-green-800 ml-6">
              <li>Earn 15% on direct referrals</li>
              <li>Earn 8% on tier 2 referrals</li>
              <li>Earn 3% on tier 3 referrals</li>
              <li>Get your own unique referral code</li>
              <li>Real-time tracking dashboard</li>
            </ul>
          </div>

          {/* Referral Code Info */}
          {referralCode && (
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-1">
                  <p className="font-semibold">You were referred by: {referralCode}</p>
                  <p className="text-sm">
                    By joining, you'll be linked to this affiliate and can start earning
                    from your own referrals too!
                  </p>
                </div>
              </AlertDescription>
            </Alert>
          )}

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


