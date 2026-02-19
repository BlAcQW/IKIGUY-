import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  DollarSign,
  Users,
  TrendingUp,
  Clock,
  Award,
  Target
} from 'lucide-react';
import { AffiliateStats as AffiliateStatsType } from '@/lib/core-api';

interface AffiliateStatsProps {
  stats: AffiliateStatsType;
  isLoading?: boolean;
}

const AffiliateStats: React.FC<AffiliateStatsProps> = ({ stats, isLoading }) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-24 bg-gray-200 rounded" />
              <div className="h-4 w-4 bg-gray-200 rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-32 bg-gray-200 rounded mb-2" />
              <div className="h-3 w-20 bg-gray-200 rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Earned',
      value: formatCurrency(stats.total_earned),
      description: `${formatCurrency(stats.this_month_earnings)} this month`,
      icon: DollarSign,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      trend: stats.this_month_earnings > stats.last_month_earnings ? 'up' : 'down'
    },
    {
      title: 'Pending Commissions',
      value: formatCurrency(stats.pending_commissions),
      description: 'Available for payout',
      icon: Clock,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100'
    },
    {
      title: 'Total Referrals',
      value: stats.total_referrals.toString(),
      description: `${stats.direct_referrals} direct, ${stats.tier2_referrals + stats.tier3_referrals} sub-affiliates`,
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    {
      title: 'Conversion Rate',
      value: formatPercent(stats.conversion_rate),
      description: `Avg ${formatCurrency(stats.average_commission_per_referral)}/referral`,
      icon: Target,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100'
    }
  ];

  return (
    <div className="space-y-4">
      {/* Main Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {stat.description}
              </p>
              {stat.trend && (
                <div className="flex items-center mt-2">
                  <TrendingUp
                    className={`h-3 w-3 mr-1 ${
                      stat.trend === 'up' ? 'text-green-600' : 'text-red-600 rotate-180'
                    }`}
                  />
                  <span className={`text-xs ${
                    stat.trend === 'up' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {stat.trend === 'up' ? 'Increased' : 'Decreased'} from last month
                  </span>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Network Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Award className="h-5 w-5 text-yellow-600" />
            Network Breakdown
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="default" className="bg-green-600">Tier 1</Badge>
                <span className="text-sm font-medium">Direct Referrals</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold">{stats.direct_referrals}</span>
                <span className="text-xs text-muted-foreground">15% commission</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="bg-blue-600 text-white">Tier 2</Badge>
                <span className="text-sm font-medium">Sub-Affiliates</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold">{stats.tier2_referrals}</span>
                <span className="text-xs text-muted-foreground">8% commission</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="border-purple-600 text-purple-600">Tier 3</Badge>
                <span className="text-sm font-medium">Sub-Sub-Affiliates</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold">{stats.tier3_referrals}</span>
                <span className="text-xs text-muted-foreground">3% commission</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Total Network Sales</span>
              <span className="text-lg font-bold text-green-600">
                {formatCurrency(stats.total_sales)}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Insights */}
      {stats.last_referral_at && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Activity</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span>Last Referral</span>
                <span className="font-medium text-foreground">
                  {new Date(stats.last_referral_at).toLocaleDateString()}
                </span>
              </div>
              {stats.last_commission_at && (
                <div className="flex items-center justify-between">
                  <span>Last Commission</span>
                  <span className="font-medium text-foreground">
                    {new Date(stats.last_commission_at).toLocaleDateString()}
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between">
                <span>Total Paid Out</span>
                <span className="font-medium text-green-600">
                  {formatCurrency(stats.total_paid)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AffiliateStats;
