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
import { affiliateApi, CommissionRecord } from '@/lib/core-api';
import {
  DollarSign,
  ChevronLeft,
  ChevronRight,
  Filter,
  Download,
  Search,
  Calendar
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface CommissionTableProps {
  organizationId?: string;
  userId?: string;
}

const CommissionTable: React.FC<CommissionTableProps> = ({ organizationId, userId }) => {
  const [commissions, setCommissions] = useState<CommissionRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [tierFilter, setTierFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [limit] = useState(10);
  const { toast } = useToast();

  useEffect(() => {
    loadCommissions();
  }, [statusFilter, currentPage]);

  const loadCommissions = async () => {
    setIsLoading(true);
    try {
      const status = statusFilter === 'all' ? undefined : statusFilter;
      const offset = (currentPage - 1) * limit;

      const response = await affiliateApi.getCommissions(status, limit, offset);
      setCommissions(response.items);
      setTotalCount(response.total);
    } catch (error) {
      console.error('Failed to load commissions:', error);
      toast({
        title: 'Error loading commissions',
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
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline', className: string }> = {
      pending: { variant: 'secondary', className: 'bg-yellow-100 text-yellow-800' },
      approved: { variant: 'default', className: 'bg-green-100 text-green-800' },
      paid: { variant: 'default', className: 'bg-blue-100 text-blue-800' },
      cancelled: { variant: 'destructive', className: 'bg-red-100 text-red-800' }
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
      1: { label: 'Tier 1', className: 'bg-green-600 text-white' },
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

  const filteredCommissions = commissions.filter(commission => {
    // Filter by tier
    if (tierFilter !== 'all' && commission.tier_level.toString() !== tierFilter) {
      return false;
    }

    // Filter by search query (transaction ID or referral user email)
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        commission.transaction_id?.toLowerCase().includes(query) ||
        commission.referral_user_id?.toLowerCase().includes(query)
      );
    }

    return true;
  });

  const totalPages = Math.ceil(totalCount / limit);

  const exportToCSV = () => {
    // Prepare CSV data
    const headers = ['Date', 'Transaction ID', 'Tier', 'Amount', 'Rate', 'Status'];
    const rows = filteredCommissions.map(c => [
      formatDate(c.created_at),
      c.transaction_id || '',
      c.tier_level,
      c.commission_amount,
      c.commission_rate,
      c.status
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    // Download
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `commissions_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    toast({
      title: 'Export successful',
      description: 'Commission data exported to CSV'
    });
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-green-600" />
              Commission History
            </CardTitle>
            <CardDescription>
              Track all your commission earnings and their status
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={exportToCSV}
            className="flex items-center gap-2"
          >
            <Download className="h-4 w-4" />
            Export CSV
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4 mb-4">
          <div className="flex-1">
            <Label htmlFor="search" className="sr-only">Search</Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                id="search"
                placeholder="Search by transaction ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <div className="w-full md:w-48">
            <Label htmlFor="status-filter" className="sr-only">Status</Label>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger id="status-filter">
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="paid">Paid</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="w-full md:w-48">
            <Label htmlFor="tier-filter" className="sr-only">Tier</Label>
            <Select value={tierFilter} onValueChange={setTierFilter}>
              <SelectTrigger id="tier-filter">
                <SelectValue placeholder="All tiers" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Tiers</SelectItem>
                <SelectItem value="1">Tier 1 (15%)</SelectItem>
                <SelectItem value="2">Tier 2 (8%)</SelectItem>
                <SelectItem value="3">Tier 3 (3%)</SelectItem>
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
        ) : filteredCommissions.length === 0 ? (
          <div className="text-center py-12">
            <DollarSign className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No commissions yet</h3>
            <p className="text-sm text-muted-foreground">
              Commissions will appear here when your referrals make purchases
            </p>
          </div>
        ) : (
          <>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Transaction</TableHead>
                    <TableHead>Tier</TableHead>
                    <TableHead>Sale Amount</TableHead>
                    <TableHead>Rate</TableHead>
                    <TableHead>Commission</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredCommissions.map((commission) => (
                    <TableRow key={commission.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm">
                            {formatDate(commission.created_at)}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                          {commission.transaction_id?.substring(0, 8) || 'N/A'}...
                        </code>
                      </TableCell>
                      <TableCell>
                        {getTierBadge(commission.tier_level)}
                      </TableCell>
                      <TableCell>
                        {formatCurrency(commission.sale_amount)}
                      </TableCell>
                      <TableCell>
                        <span className="text-sm font-medium">
                          {(commission.commission_rate * 100).toFixed(1)}%
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="font-semibold text-green-600">
                          {formatCurrency(commission.commission_amount)}
                        </span>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(commission.status)}
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
                  Showing {((currentPage - 1) * limit) + 1} to {Math.min(currentPage * limit, totalCount)} of {totalCount} commissions
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

export default CommissionTable;
