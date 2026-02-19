import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import { affiliateApi, Referral } from '@/lib/core-api';
import {
  Users,
  ChevronLeft,
  ChevronRight,
  Search,
  Calendar,
  DollarSign,
  TrendingUp,
  Mail
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface ReferralTableProps {
  organizationId?: string;
}

const ReferralTable: React.FC<ReferralTableProps> = ({ organizationId }) => {
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [tierFilter, setTierFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [limit] = useState(10);
  const { toast } = useToast();

  useEffect(() => {
    loadReferrals();
  }, [currentPage, tierFilter]);

  const loadReferrals = async () => {
    setIsLoading(true);
    try {
      const tier = tierFilter === 'all' ? undefined : parseInt(tierFilter);
      const offset = (currentPage - 1) * limit;

      const response = await affiliateApi.getReferrals(tier, limit, offset);
      setReferrals(response.items);
      setTotalCount(response.total);
    } catch (error) {
      console.error('Failed to load referrals:', error);
      toast({
        title: 'Error loading referrals',
        description: error instanceof Error ? error.message : 'Please try again',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: 'default' | 'secondary' | 'outline', className: string }> = {
      active: { variant: 'default', className: 'bg-green-100 text-green-800' },
      inactive: { variant: 'secondary', className: 'bg-gray-100 text-gray-800' },
      suspended: { variant: 'outline', className: 'bg-red-100 text-red-800' }
    };

    const config = variants[status] || { variant: 'outline' as const, className: '' };
    return (
      <Badge variant={config.variant} className={config.className}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const getTierBadge = (tier: number) => {
    const tierConfig: Record<number, { label: string, className: string }> = {
      1: { label: 'Direct', className: 'bg-green-600 text-white' },
      2: { label: 'Tier 2', className: 'bg-blue-600 text-white' },
      3: { label: 'Tier 3', className: 'bg-purple-600 text-white' }
    };

    const config = tierConfig[tier] || { label: `Tier ${tier}`, className: '' };
    return (
      <Badge className={config.className}>
        {config.label}
      </Badge>
    );
  };

  const getPerformanceBadge = (totalSpent: number) => {
    if (totalSpent >= 1000) {
      return <Badge className="bg-yellow-600 text-white">⭐ High Value</Badge>;
    } else if (totalSpent >= 100) {
      return <Badge className="bg-blue-600 text-white">Active</Badge>;
    } else if (totalSpent > 0) {
      return <Badge variant="secondary">Converted</Badge>;
    } else {
      return <Badge variant="outline">New</Badge>;
    }
  };

  const filteredReferrals = referrals.filter(referral => {
    // Filter by status
    if (statusFilter !== 'all' && referral.status !== statusFilter) {
      return false;
    }

    // Filter by search query (email or name)
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        referral.referred_user_email?.toLowerCase().includes(query) ||
        referral.referred_user_id?.toLowerCase().includes(query)
      );
    }

    return true;
  });

  const totalPages = Math.ceil(totalCount / limit);

  const calculateTotalValue = () => {
    return filteredReferrals.reduce((sum, ref) => sum + ref.total_spent, 0);
  };

  const calculateTotalCommissions = () => {
    return filteredReferrals.reduce((sum, ref) => sum + ref.total_commissions_earned, 0);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-blue-600" />
              Your Referrals
            </CardTitle>
            <CardDescription>
              Manage and track all users you've referred to the platform
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Referrals</p>
                <p className="text-2xl font-bold">{totalCount}</p>
              </div>
              <Users className="h-8 w-8 text-blue-600" />
            </div>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Value</p>
                <p className="text-2xl font-bold">{formatCurrency(calculateTotalValue())}</p>
              </div>
              <DollarSign className="h-8 w-8 text-green-600" />
            </div>
          </div>
          <div className="bg-purple-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Earned</p>
                <p className="text-2xl font-bold">{formatCurrency(calculateTotalCommissions())}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-600" />
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4 mb-4">
          <div className="flex-1">
            <Label htmlFor="search" className="sr-only">Search</Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                id="search"
                placeholder="Search by email or user ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <div className="w-full md:w-48">
            <Label htmlFor="tier-filter" className="sr-only">Tier</Label>
            <Select value={tierFilter} onValueChange={setTierFilter}>
              <SelectTrigger id="tier-filter">
                <SelectValue placeholder="All tiers" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Tiers</SelectItem>
                <SelectItem value="1">Direct Referrals</SelectItem>
                <SelectItem value="2">Tier 2</SelectItem>
                <SelectItem value="3">Tier 3</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="w-full md:w-48">
            <Label htmlFor="status-filter" className="sr-only">Status</Label>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger id="status-filter">
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
                <SelectItem value="suspended">Suspended</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
            ))}
          </div>
        ) : filteredReferrals.length === 0 ? (
          <div className="text-center py-12">
            <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No referrals yet</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Start sharing your referral link to build your network
            </p>
          </div>
        ) : (
          <>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>Tier</TableHead>
                    <TableHead>Joined</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Total Spent</TableHead>
                    <TableHead>Commissions</TableHead>
                    <TableHead>Performance</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredReferrals.map((referral) => (
                    <TableRow key={referral.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                            <Mail className="h-4 w-4 text-blue-600" />
                          </div>
                          <div>
                            <p className="font-medium text-sm">
                              {referral.referred_user_email || 'Unknown User'}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              ID: {referral.referred_user_id?.substring(0, 8)}...
                            </p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        {getTierBadge(referral.tier_level)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm">
                            {formatDate(referral.joined_at)}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(referral.status)}
                      </TableCell>
                      <TableCell>
                        <span className="font-semibold">
                          {formatCurrency(referral.total_spent)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="font-semibold text-green-600">
                          {formatCurrency(referral.total_commissions_earned)}
                        </span>
                      </TableCell>
                      <TableCell>
                        {getPerformanceBadge(referral.total_spent)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-muted-foreground">
                  Showing {((currentPage - 1) * limit) + 1} to {Math.min(currentPage * limit, totalCount)} of {totalCount} referrals
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </Button>
                  <div className="flex items-center gap-1">
                    {[...Array(Math.min(5, totalPages))].map((_, i) => {
                      const pageNum = i + 1;
                      return (
                        <Button
                          key={pageNum}
                          variant={currentPage === pageNum ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setCurrentPage(pageNum)}
                          className="w-8 h-8 p-0"
                        >
                          {pageNum}
                        </Button>
                      );
                    })}
                    {totalPages > 5 && (
                      <>
                        <span className="px-2">...</span>
                        <Button
                          variant={currentPage === totalPages ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setCurrentPage(totalPages)}
                          className="w-8 h-8 p-0"
                        >
                          {totalPages}
                        </Button>
                      </>
                    )}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                  >
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default ReferralTable;
