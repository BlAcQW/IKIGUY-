import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { affiliateApi } from '@/lib/core-api';
import {
  Trophy,
  Medal,
  Award,
  TrendingUp,
  Users,
  DollarSign,
  Crown,
  Star
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface LeaderboardEntry {
  rank: number;
  user_id: string;
  name?: string;
  email?: string;
  referral_code: string;
  tier_level: number;
  total_earnings: number;
  total_referrals: number;
  total_sales: number;
  direct_referrals: number;
  joined_at?: string;
}

interface LeaderboardTableProps {
  limit?: number;
}

const LeaderboardTable: React.FC<LeaderboardTableProps> = ({ limit = 100 }) => {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [myRank, setMyRank] = useState<LeaderboardEntry | null>(null);
  const [period, setPeriod] = useState('all_time');
  const [metric, setMetric] = useState('earnings');
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadLeaderboard();
    loadMyRank();
  }, [period, metric]);

  const loadLeaderboard = async () => {
    setIsLoading(true);
    try {
      const data = await affiliateApi.getLeaderboard(period, metric, limit);
      setLeaderboard(data.leaderboard || []);
    } catch (error) {
      console.error('Failed to load leaderboard:', error);
      toast({
        title: 'Error loading leaderboard',
        description: error instanceof Error ? error.message : 'Please try again',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadMyRank = async () => {
    try {
      const rank = await affiliateApi.getMyRank(metric);
      setMyRank(rank);
    } catch (error) {
      console.error('Failed to load my rank:', error);
    }
  };

  const getRankIcon = (rank: number) => {
    if (rank === 1) return <Crown className="h-5 w-5 text-yellow-500" />;
    if (rank === 2) return <Medal className="h-5 w-5 text-gray-400" />;
    if (rank === 3) return <Medal className="h-5 w-5 text-amber-600" />;
    if (rank <= 10) return <Star className="h-5 w-5 text-blue-500" />;
    return <Award className="h-5 w-5 text-gray-400" />;
  };

  const getRankBadge = (rank: number) => {
    if (rank === 1) return <Badge className="bg-yellow-500">🏆 Champion</Badge>;
    if (rank === 2) return <Badge className="bg-gray-400">🥈 2nd Place</Badge>;
    if (rank === 3) return <Badge className="bg-amber-600">🥉 3rd Place</Badge>;
    if (rank <= 10) return <Badge variant="secondary">Top 10</Badge>;
    return null;
  };

  const formatValue = (value: number, type: string) => {
    if (type === 'earnings' || type === 'sales') {
      return `$${value.toFixed(2)}`;
    }
    return value.toString();
  };

  const getMetricValue = (entry: LeaderboardEntry) => {
    switch (metric) {
      case 'earnings':
        return entry.total_earnings;
      case 'referrals':
        return entry.total_referrals;
      case 'sales':
        return entry.total_sales;
      default:
        return entry.total_earnings;
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Leaderboard</CardTitle>
          <CardDescription>Loading rankings...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded animate-pulse" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5 text-yellow-500" />
              Affiliate Leaderboard
            </CardTitle>
            <CardDescription>Top performing affiliates in your organization</CardDescription>
          </div>
          <div className="flex gap-2">
            <Select value={metric} onValueChange={setMetric}>
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="earnings">By Earnings</SelectItem>
                <SelectItem value="referrals">By Referrals</SelectItem>
                <SelectItem value="sales">By Sales</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* My Rank Card */}
        {myRank && (
          <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {getRankIcon(myRank.rank)}
                <div>
                  <p className="font-semibold">Your Rank</p>
                  <p className="text-sm text-muted-foreground">
                    #{myRank.rank} out of all affiliates
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold">{formatValue(getMetricValue(myRank), metric)}</p>
                <p className="text-sm text-muted-foreground capitalize">{metric}</p>
              </div>
            </div>
          </div>
        )}

        {/* Leaderboard Table */}
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-3 font-semibold text-sm">Rank</th>
                <th className="text-left p-3 font-semibold text-sm">Affiliate</th>
                <th className="text-right p-3 font-semibold text-sm">
                  {metric === 'earnings' && <><DollarSign className="inline h-4 w-4" /> Earnings</>}
                  {metric === 'referrals' && <><Users className="inline h-4 w-4" /> Referrals</>}
                  {metric === 'sales' && <><TrendingUp className="inline h-4 w-4" /> Sales</>}
                </th>
                <th className="text-center p-3 font-semibold text-sm">Tier</th>
                <th className="text-center p-3 font-semibold text-sm">Status</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((entry, index) => (
                <tr
                  key={entry.user_id}
                  className={`border-t hover:bg-gray-50 ${
                    entry.rank <= 3 ? 'bg-yellow-50' : ''
                  }`}
                >
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      {getRankIcon(entry.rank)}
                      <span className="font-bold text-lg">#{entry.rank}</span>
                    </div>
                  </td>
                  <td className="p-3">
                    <div>
                      <p className="font-medium">
                        {entry.name || entry.email || `Affiliate ${entry.referral_code}`}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Code: {entry.referral_code}
                      </p>
                    </div>
                  </td>
                  <td className="p-3 text-right">
                    <span className="text-lg font-semibold">
                      {formatValue(getMetricValue(entry), metric)}
                    </span>
                  </td>
                  <td className="p-3 text-center">
                    <Badge variant="outline">Tier {entry.tier_level}</Badge>
                  </td>
                  <td className="p-3 text-center">
                    {getRankBadge(entry.rank)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {leaderboard.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            <Trophy className="h-12 w-12 mx-auto mb-3 opacity-20" />
            <p>No leaderboard data available yet.</p>
            <p className="text-sm">Start referring users to climb the ranks!</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default LeaderboardTable;
