import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { affiliateApi } from '@/lib/core-api';
import { getReferralCode } from '@/lib/referral-tracking';
import {
  Award,
  DollarSign,
  Users,
  TrendingUp,
  Shield,
  Zap,
  Globe,
  CheckCircle,
  AlertCircle,
  Info,
  Gift
} from 'lucide-react';

const AffiliatesJoin: React.FC = () => {
  const [referralCode, setReferralCode] = useState('');
  const [agreed, setAgreed] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasReferralFromCookie, setHasReferralFromCookie] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();

  // Auto-populate referral code from cookie on mount
  // Also check if user is already an affiliate and redirect to dashboard
  useEffect(() => {
    const cookieReferralCode = getReferralCode();
    if (cookieReferralCode) {
      setReferralCode(cookieReferralCode);
      setHasReferralFromCookie(true);
    }

    // Check if user is already an affiliate
    const checkExistingAffiliate = async () => {
      try {
        const profile = await affiliateApi.getProfile();
        // User is already an affiliate, redirect to dashboard
        navigate('/affiliates/dashboard', { replace: true });
      } catch (error: any) {
        // If 404, user is not an affiliate, stay on join page
        if (error.response?.status !== 404) {
          console.error('Error checking affiliate status:', error);
        }
      }
    };

    checkExistingAffiliate();
  }, [navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!agreed) {
      setError('Please agree to the terms and conditions');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const profile = await affiliateApi.joinProgram(
        referralCode ? { upline_referral_code: referralCode } : undefined
      );

      toast({
        title: 'Welcome to the affiliate program!',
        description: `Your referral code is: ${profile.referral_code}`
      });

      // Navigate to dashboard
      navigate('/affiliates/dashboard');
    } catch (error: any) {
      console.error('Failed to join affiliate program:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to join program');
      toast({
        title: 'Failed to join program',
        description: error.response?.data?.detail || error.message || 'Please try again',
        variant: 'destructive'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const features = [
    {
      icon: <DollarSign className="h-6 w-6 text-green-600" />,
      title: 'Multi-Tier Commissions',
      description: 'Earn 15% on direct referrals, 8% on tier 2, and 3% on tier 3'
    },
    {
      icon: <Users className="h-6 w-6 text-blue-600" />,
      title: 'Unlimited Referrals',
      description: 'No limits on how many people you can refer or how much you can earn'
    },
    {
      icon: <TrendingUp className="h-6 w-6 text-purple-600" />,
      title: 'Real-Time Tracking',
      description: 'Monitor your earnings, referrals, and network growth in real-time'
    },
    {
      icon: <Shield className="h-6 w-6 text-orange-600" />,
      title: 'Secure Payouts',
      description: 'Multiple payout options including wallet credit, mobile money, and bank transfer'
    },
    {
      icon: <Zap className="h-6 w-6 text-yellow-600" />,
      title: 'Instant Activation',
      description: 'Start sharing your link immediately after signup'
    },
    {
      icon: <Globe className="h-6 w-6 text-indigo-600" />,
      title: 'Marketing Tools',
      description: 'Custom tracking links, social media sharing, and performance analytics'
    }
  ];

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold mb-3 flex items-center justify-center gap-3">
          <Award className="h-10 w-10 text-blue-600" />
          Join Our Affiliate Program
        </h1>
        <p className="text-lg text-muted-foreground">
          Start earning money by referring new users to KasaAI
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column - Features */}
        <div className="space-y-6">
          {/* Commission Structure */}
          <Card>
            <CardHeader>
              <CardTitle>Commission Structure</CardTitle>
              <CardDescription>
                Earn from up to 3 tiers of referrals in your network
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-green-900">Tier 1 - Direct Referrals</span>
                  <span className="text-2xl font-bold text-green-600">15%</span>
                </div>
                <p className="text-sm text-green-800">
                  Users who sign up using your referral link
                </p>
              </div>

              <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-blue-900">Tier 2 - Sub-Affiliates</span>
                  <span className="text-2xl font-bold text-blue-600">8%</span>
                </div>
                <p className="text-sm text-blue-800">
                  Users referred by your direct referrals
                </p>
              </div>

              <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-purple-900">Tier 3 - Extended Network</span>
                  <span className="text-2xl font-bold text-purple-600">3%</span>
                </div>
                <p className="text-sm text-purple-800">
                  Users referred by your tier 2 affiliates
                </p>
              </div>

              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  <strong>Example:</strong> If a tier 3 user purchases $100, you earn $3, your tier 2 affiliate earns $8, and your direct referral earns $15.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>

          {/* Features Grid */}
          <Card>
            <CardHeader>
              <CardTitle>Program Benefits</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-4">
                {features.map((feature, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <div className="shrink-0">{feature.icon}</div>
                    <div>
                      <h3 className="font-semibold mb-1">{feature.title}</h3>
                      <p className="text-sm text-muted-foreground">{feature.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Signup Form */}
        <div>
          <Card className="sticky top-8">
            <CardHeader>
              <CardTitle>Sign Up Now</CardTitle>
              <CardDescription>
                Join the affiliate program and start earning today
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Referral Code (Optional) */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="referralCode">
                      Referral Code <span className="text-muted-foreground">(Optional)</span>
                    </Label>
                    {hasReferralFromCookie && (
                      <Badge variant="secondary" className="flex items-center gap-1">
                        <Gift className="h-3 w-3" />
                        Auto-filled
                      </Badge>
                    )}
                  </div>
                  <Input
                    id="referralCode"
                    value={referralCode}
                    onChange={(e) => {
                      setReferralCode(e.target.value.toUpperCase());
                      setHasReferralFromCookie(false);
                    }}
                    placeholder="Enter referral code if you have one"
                    className="uppercase font-mono"
                  />
                  <p className="text-xs text-muted-foreground">
                    {hasReferralFromCookie
                      ? 'We detected a referral link you clicked. This code will credit the person who referred you.'
                      : 'If you were referred by someone, enter their code to credit them'}
                  </p>
                </div>

                {/* How it Works */}
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>
                    <div className="space-y-2 text-sm">
                      <p><strong>How it works:</strong></p>
                      <ol className="list-decimal list-inside space-y-1 ml-2">
                        <li>Join the program and get your unique referral code</li>
                        <li>Share your referral link with friends and on social media</li>
                        <li>Earn commissions when they sign up and make purchases</li>
                        <li>Request payouts anytime (minimum varies by method)</li>
                      </ol>
                    </div>
                  </AlertDescription>
                </Alert>

                {/* Terms and Conditions */}
                <div className="flex items-start gap-2">
                  <Checkbox
                    id="terms"
                    checked={agreed}
                    onCheckedChange={(checked) => setAgreed(checked as boolean)}
                  />
                  <label htmlFor="terms" className="text-sm cursor-pointer">
                    I agree to the{' '}
                    <a href="#" className="text-blue-600 hover:underline">
                      Affiliate Program Terms and Conditions
                    </a>{' '}
                    and understand that commissions are only earned on completed purchases.
                  </label>
                </div>

                {/* Error Message */}
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {/* Submit Button */}
                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  disabled={isSubmitting || !agreed}
                >
                  {isSubmitting ? 'Joining...' : 'Join Affiliate Program'}
                </Button>

                {/* Additional Info */}
                <div className="text-center text-sm text-muted-foreground">
                  Already an affiliate?{' '}
                  <Button
                    variant="link"
                    className="p-0 h-auto"
                    onClick={() => navigate('/affiliates/dashboard')}
                  >
                    Go to Dashboard
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Payout Methods */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="text-base">Payout Options</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span>💳 Wallet Credit</span>
                  <span className="text-muted-foreground">Free • Instant</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>📱 Mobile Money</span>
                  <span className="text-muted-foreground">2.5% • 1-2 days</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>🏦 Bank Transfer</span>
                  <span className="text-muted-foreground">$5 • 2-5 days</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>💰 PayPal</span>
                  <span className="text-muted-foreground">2.9% + $0.30 • 1-2 days</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AffiliatesJoin;
