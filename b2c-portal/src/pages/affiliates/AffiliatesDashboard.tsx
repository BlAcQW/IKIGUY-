import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { affiliateApi, AffiliateProfile, AffiliateStats as AffiliateStatsType } from '@/lib/core-api';
import AffiliateStats from '@/components/affiliates/AffiliateStats';
import ReferralLinkGenerator from '@/components/affiliates/ReferralLinkGenerator';
import CommissionTable from '@/components/affiliates/CommissionTable';
import ReferralTable from '@/components/affiliates/ReferralTable';
import PayoutRequestForm from '@/components/affiliates/PayoutRequestForm';
import NetworkTreeView from '@/components/affiliates/NetworkTreeView';
import LeaderboardTable from '@/components/affiliates/LeaderboardTable';
import AnalyticsDashboard from '@/components/affiliates/AnalyticsDashboard';
import CampaignsDashboard from '@/components/affiliates/CampaignsDashboard';
import CreateCampaignWizard from '@/components/affiliates/CreateCampaignWizard';
import PayoutSettingsPanel from '@/components/affiliates/PayoutSettingsPanel';
import {
  Users,
  DollarSign,
  TrendingUp,
  Award,
  AlertCircle,
  Info,
  ExternalLink,
  Trophy,
  BarChart3,
  Megaphone
} from 'lucide-react';

const AffiliatesDashboard: React.FC = () => {
  const [profile, setProfile] = useState<AffiliateProfile | null>(null);
  const [stats, setStats] = useState<AffiliateStatsType | null>(null);
  const [referralUrl, setReferralUrl] = useState<{ base_url: string; full_url: string } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [showCampaignWizard, setShowCampaignWizard] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    loadAffiliateData();
  }, []);

  const loadAffiliateData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [profileData, statsData, referralCodeData] = await Promise.all([
        affiliateApi.getProfile(),
        affiliateApi.getStats(),
        affiliateApi.getReferralCode()
      ]);
      setProfile(profileData);
      setStats(statsData);
      setReferralUrl({
        base_url: referralCodeData.base_url,
        full_url: referralCodeData.full_url
      });
    } catch (error: any) {
      console.error('Failed to load affiliate data:', error);

      // Check if user is not enrolled
      if (error.response?.status === 404) {
        setError('not_enrolled');
      } else {
        setError(error.message || 'Failed to load affiliate dashboard');
        toast({
          title: 'Error loading data',
          description: error.message || 'Please try again',
          variant: 'destructive'
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handlePayoutSuccess = () => {
    // Reload stats after successful payout
    loadAffiliateData();
    setActiveTab('overview');
    toast({
      title: 'Payout Requested',
      description: 'Your payout request has been submitted successfully'
    });
  };

  // Not enrolled view
  if (error === 'not_enrolled') {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Card className="border-2 border-blue-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-2xl">
              <Award className="h-6 w-6 text-blue-600" />
              Join Our Affiliate Program
            </CardTitle>
            <CardDescription className="text-base">
              Earn money by referring new users to KasaAI
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                You haven't joined the affiliate program yet. Sign up now to start earning commissions!
              </AlertDescription>
            </Alert>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-green-50 rounded-lg p-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600 mb-2">15%</div>
                  <p className="text-sm font-medium">Direct Referrals</p>
                  <p className="text-xs text-muted-foreground mt-1">Tier 1 Commission</p>
                </div>
              </div>
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600 mb-2">8%</div>
                  <p className="text-sm font-medium">Sub-Affiliates</p>
                  <p className="text-xs text-muted-foreground mt-1">Tier 2 Commission</p>
                </div>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600 mb-2">3%</div>
                  <p className="text-sm font-medium">3rd Level</p>
                  <p className="text-xs text-muted-foreground mt-1">Tier 3 Commission</p>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="font-semibold text-lg">Program Benefits:</h3>
              <ul className="space-y-2">
                <li className="flex items-start gap-2">
                  <div className="h-5 w-5 rounded-full bg-green-100 flex items-center justify-center shrink-0 mt-0.5">
                    <span className="text-green-600 text-xs">✓</span>
                  </div>
                  <span className="text-sm">Earn up to 26% commission on every sale from your network</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="h-5 w-5 rounded-full bg-green-100 flex items-center justify-center shrink-0 mt-0.5">
                    <span className="text-green-600 text-xs">✓</span>
                  </div>
                  <span className="text-sm">Multi-level marketing: earn from 3 tiers of referrals</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="h-5 w-5 rounded-full bg-green-100 flex items-center justify-center shrink-0 mt-0.5">
                    <span className="text-green-600 text-xs">✓</span>
                  </div>
                  <span className="text-sm">Multiple payout options: wallet credit, mobile money, bank transfer, PayPal</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="h-5 w-5 rounded-full bg-green-100 flex items-center justify-center shrink-0 mt-0.5">
                    <span className="text-green-600 text-xs">✓</span>
                  </div>
                  <span className="text-sm">Real-time tracking and analytics dashboard</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="h-5 w-5 rounded-full bg-green-100 flex items-center justify-center shrink-0 mt-0.5">
                    <span className="text-green-600 text-xs">✓</span>
                  </div>
                  <span className="text-sm">Custom tracking links with UTM parameters</span>
                </li>
              </ul>
            </div>

            <Button
              size="lg"
              className="w-full"
              onClick={() => navigate('/affiliates/join')}
            >
              Join Affiliate Program
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Loading view
  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="space-y-6">
          <div className="h-12 bg-gray-200 rounded animate-pulse w-64" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded animate-pulse" />
            ))}
          </div>
          <div className="h-96 bg-gray-200 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  // Error view
  if (error && error !== 'not_enrolled') {
    return (
      <div className="container mx-auto px-4 py-8 max-w-2xl">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error}
          </AlertDescription>
        </Alert>
        <Button onClick={loadAffiliateData} className="mt-4">
          Try Again
        </Button>
      </div>
    );
  }

  // Main dashboard view
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Affiliate Dashboard</h1>
        <p className="text-muted-foreground">
          Manage your affiliate network and track your earnings
        </p>
      </div>

      {/* Quick Actions */}
      <div className="mb-6 flex gap-3">
        <Button
          variant="outline"
          onClick={() => setActiveTab('referrals')}
          className="flex items-center gap-2"
        >
          <Users className="h-4 w-4" />
          View Referrals
        </Button>
        <Button
          variant="outline"
          onClick={() => setActiveTab('commissions')}
          className="flex items-center gap-2"
        >
          <DollarSign className="h-4 w-4" />
          View Commissions
        </Button>
        <Button
          variant="outline"
          onClick={() => setActiveTab('payout')}
          className="flex items-center gap-2"
        >
          <TrendingUp className="h-4 w-4" />
          Request Payout
        </Button>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-8">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
          <TabsTrigger value="referrals">Referrals</TabsTrigger>
          <TabsTrigger value="commissions">Commissions</TabsTrigger>
          <TabsTrigger value="network">Network</TabsTrigger>
          <TabsTrigger value="leaderboard">Leaderboard</TabsTrigger>
          <TabsTrigger value="payout">Payout</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
          {/* Stats */}
          {stats && <AffiliateStats stats={stats} isLoading={false} />}

          {/* Referral Link */}
          {profile && referralUrl && (
            <ReferralLinkGenerator
              referralCode={profile.referral_code}
              baseUrl={referralUrl.base_url}
            />
          )}

          {/* Recent Activity */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Recent Referrals</CardTitle>
                <CardDescription>Your latest referrals this month</CardDescription>
              </CardHeader>
              <CardContent>
                <ReferralTable organizationId={profile?.organization_id} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Recent Commissions</CardTitle>
                <CardDescription>Your latest commission earnings</CardDescription>
              </CardHeader>
              <CardContent>
                <CommissionTable organizationId={profile?.organization_id} userId={profile?.user_id} />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6 mt-6">
          <AnalyticsDashboard />
        </TabsContent>

        <TabsContent value="campaigns" className="space-y-6 mt-6">
          {showCampaignWizard ? (
            <CreateCampaignWizard
              onClose={() => {
                setShowCampaignWizard(false);
                setActiveTab('campaigns');
              }}
              onSuccess={() => {
                setShowCampaignWizard(false);
                setActiveTab('campaigns');
              }}
            />
          ) : (
            <CampaignsDashboard
              onCreateCampaign={() => setShowCampaignWizard(true)}
            />
          )}
        </TabsContent>

        <TabsContent value="referrals" className="space-y-6 mt-6">
          <ReferralTable organizationId={profile?.organization_id} />
        </TabsContent>

        <TabsContent value="commissions" className="space-y-6 mt-6">
          <CommissionTable organizationId={profile?.organization_id} userId={profile?.user_id} />
        </TabsContent>

        <TabsContent value="network" className="space-y-6 mt-6">
          <NetworkTreeView organizationId={profile?.organization_id} />
        </TabsContent>

        <TabsContent value="leaderboard" className="space-y-6 mt-6">
          <LeaderboardTable limit={100} />
        </TabsContent>

        <TabsContent value="payout" className="space-y-6 mt-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <div>
              <PayoutRequestForm onSuccess={handlePayoutSuccess} />
            </div>
            <div>
              {profile && (
                <PayoutSettingsPanel
                  profile={profile}
                  onUpdate={loadAffiliateData}
                />
              )}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AffiliatesDashboard;
