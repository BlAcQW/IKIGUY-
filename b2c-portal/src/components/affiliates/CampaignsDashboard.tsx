import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { Plus, Calendar, TrendingUp, Target, Award, Play, Pause, Trash2, Edit } from 'lucide-react';
import { affiliateApi } from '@/lib/core-api';

interface Campaign {
  id: string;
  name: string;
  description?: string;
  campaign_code: string;
  start_date: string;
  end_date: string;
  bonus_rate: number;
  target_referrals?: number;
  target_sales?: number;
  prize?: string;
  status: 'draft' | 'active' | 'paused' | 'completed' | 'cancelled';
  total_clicks: number;
  total_conversions: number;
  total_sales: number;
  total_bonus_earned: number;
  is_ongoing?: boolean;
  conversion_rate?: number;
}

interface CampaignsDashboardProps {
  onCreateCampaign: () => void;
}

const CampaignsDashboard: React.FC<CampaignsDashboardProps> = ({ onCreateCampaign }) => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const { toast } = useToast();

  useEffect(() => {
    loadCampaigns();
  }, [selectedStatus]);

  const loadCampaigns = async () => {
    setIsLoading(true);
    try {
      const statusFilter = selectedStatus === 'all' ? undefined : selectedStatus;
      const data = await affiliateApi.getCampaigns(statusFilter);
      setCampaigns(data || []);
    } catch (error: any) {
      toast({
        title: 'Error loading campaigns',
        description: error.message || 'Failed to load campaigns',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline', label: string }> = {
      draft: { variant: 'secondary', label: 'Draft' },
      active: { variant: 'default', label: 'Active' },
      paused: { variant: 'outline', label: 'Paused' },
      completed: { variant: 'secondary', label: 'Completed' },
      cancelled: { variant: 'destructive', label: 'Cancelled' }
    };
    const config = variants[status] || variants.draft;
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const activeCampaigns = campaigns.filter(c => c.status === 'active');
  const totalBonusEarned = campaigns.reduce((sum, c) => sum + c.total_bonus_earned, 0);
  const totalCampaignSales = campaigns.reduce((sum, c) => sum + c.total_sales, 0);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with stats */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Referral Campaigns</h2>
          <p className="text-muted-foreground">Create time-limited promotions to boost referrals</p>
        </div>
        <Button onClick={onCreateCampaign}>
          <Plus className="mr-2 h-4 w-4" />
          Create Campaign
        </Button>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Play className="h-4 w-4 text-green-500" />
              Active Campaigns
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeCampaigns.length}</div>
            <p className="text-xs text-muted-foreground">Currently running</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-blue-500" />
              Campaign Sales
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalCampaignSales)}</div>
            <p className="text-xs text-muted-foreground">Total from campaigns</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Award className="h-4 w-4 text-yellow-500" />
              Bonus Earned
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalBonusEarned)}</div>
            <p className="text-xs text-muted-foreground">Extra commission</p>
          </CardContent>
        </Card>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 border-b">
        {['all', 'active', 'draft', 'completed', 'paused'].map((status) => (
          <button
            key={status}
            onClick={() => setSelectedStatus(status)}
            className={`px-4 py-2 border-b-2 transition-colors ${
              selectedStatus === status
                ? 'border-indigo-600 text-indigo-600 font-medium'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </button>
        ))}
      </div>

      {/* Campaigns list */}
      {campaigns.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Target className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No campaigns yet</h3>
            <p className="text-muted-foreground mb-4 text-center max-w-md">
              Create your first referral campaign to offer bonus commissions and boost your affiliate performance
            </p>
            <Button onClick={onCreateCampaign}>
              <Plus className="mr-2 h-4 w-4" />
              Create Your First Campaign
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {campaigns.map((campaign) => (
            <Card key={campaign.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <CardTitle className="text-xl">{campaign.name}</CardTitle>
                      {getStatusBadge(campaign.status)}
                      {campaign.is_ongoing && (
                        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                          Live Now
                        </Badge>
                      )}
                    </div>
                    {campaign.description && (
                      <CardDescription>{campaign.description}</CardDescription>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-4 w-4" />
                        {formatDate(campaign.start_date)} - {formatDate(campaign.end_date)}
                      </div>
                      <div className="flex items-center gap-1">
                        <TrendingUp className="h-4 w-4" />
                        +{(campaign.bonus_rate * 100).toFixed(1)}% Bonus
                      </div>
                      <code className="px-2 py-1 bg-gray-100 rounded text-xs">
                        {campaign.campaign_code}
                      </code>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="icon">
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon">
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Clicks</p>
                    <p className="text-lg font-semibold">{campaign.total_clicks}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Conversions</p>
                    <p className="text-lg font-semibold">{campaign.total_conversions}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Sales</p>
                    <p className="text-lg font-semibold">{formatCurrency(campaign.total_sales)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Bonus Earned</p>
                    <p className="text-lg font-semibold text-green-600">
                      {formatCurrency(campaign.total_bonus_earned)}
                    </p>
                  </div>
                </div>

                {/* Progress towards goals */}
                {(campaign.target_referrals || campaign.target_sales) && (
                  <div className="mt-4 pt-4 border-t">
                    <p className="text-sm font-medium mb-2">Goals Progress</p>
                    <div className="space-y-2">
                      {campaign.target_referrals && (
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Referrals: {campaign.total_conversions} / {campaign.target_referrals}</span>
                            <span>{Math.round((campaign.total_conversions / campaign.target_referrals) * 100)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-indigo-600 h-2 rounded-full transition-all"
                              style={{ width: `${Math.min((campaign.total_conversions / campaign.target_referrals) * 100, 100)}%` }}
                            />
                          </div>
                        </div>
                      )}
                      {campaign.target_sales && (
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Sales: {formatCurrency(campaign.total_sales)} / {formatCurrency(campaign.target_sales)}</span>
                            <span>{Math.round((campaign.total_sales / campaign.target_sales) * 100)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-green-600 h-2 rounded-full transition-all"
                              style={{ width: `${Math.min((campaign.total_sales / campaign.target_sales) * 100, 100)}%` }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                    {campaign.prize && (
                      <div className="mt-2 flex items-center gap-2 text-sm">
                        <Award className="h-4 w-4 text-yellow-500" />
                        <span className="font-medium">Prize: {campaign.prize}</span>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default CampaignsDashboard;
