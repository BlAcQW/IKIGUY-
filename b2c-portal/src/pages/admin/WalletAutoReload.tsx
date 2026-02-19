import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { API_ENDPOINTS, apiRequest } from '@/config/api';
import { toast } from '@/components/ui/use-toast';
import {
  Wallet,
  RefreshCw,
  Clock,
  DollarSign,
  TrendingUp,
  Activity,
  CheckCircle,
  AlertCircle,
  Users,
  Zap
} from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';

interface AutoReloadStats {
  job_id: string;
  scheduled: boolean;
  next_run_time: string | null;
  statistics: {
    total_wallets: number;
    auto_reload_enabled_count: number;
    auto_reload_enabled_percentage: number;
    wallets_below_threshold: number;
    total_pending_reload_amount: number;
  };
}

interface ReloadResult {
  wallet_id: string;
  user_id: string;
  transaction_id: string;
  amount: number;
  currency: string;
  status: string;
  balance_before: number;
  payment_method: string;
}

interface TaskSummary {
  success: boolean;
  task_name: string;
  completed_at: string;
  summary: {
    wallets_checked: number;
    successful_reloads: number;
    failed_reloads: number;
    total_amount_reloaded: number;
  };
  results: ReloadResult[];
  errors: Array<{
    wallet_id: string;
    user_id: string;
    error: string;
  }>;
}

export default function WalletAutoReload() {
  const [stats, setStats] = useState<AutoReloadStats | null>(null);
  const [lastRunSummary, setLastRunSummary] = useState<TaskSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);

      const statsRes = await apiRequest(`${API_ENDPOINTS.admin.base}/wallet/auto-reload-status`, {
        method: 'GET'
      });

      setStats(statsRes);

      // Try to load last run summary if available
      try {
        const summaryRes = await apiRequest(`${API_ENDPOINTS.admin.base}/wallet/auto-reload-last-run`, {
          method: 'GET'
        });
        setLastRunSummary(summaryRes);
      } catch (error) {
        // Last run summary might not be available
        console.log('Last run summary not available');
      }
    } catch (error) {
      console.error('Error loading auto-reload data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load auto-reload data',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerNow = async () => {
    try {
      setTriggering(true);

      const result: TaskSummary = await apiRequest(`${API_ENDPOINTS.admin.base}/wallet/auto-reload-now`, {
        method: 'POST'
      });

      if (result.success) {
        toast({
          title: 'Auto-Reload Triggered',
          description: `Checked ${result.summary.wallets_checked} wallets, successfully reloaded ${result.summary.successful_reloads}`
        });

        setLastRunSummary(result);

        // Reload stats
        await loadData();
      }
    } catch (error: any) {
      console.error('Error triggering auto-reload:', error);
      toast({
        title: 'Trigger Failed',
        description: error.message || 'Failed to trigger auto-reload',
        variant: 'destructive'
      });
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground flex items-center gap-2">
            <Zap className="h-8 w-8 text-yellow-600" />
            Wallet Auto-Reload
          </h1>
          <p className="text-gray-600 mt-2">
            Monitor automatic wallet reloading and trigger manual reloads
          </p>
        </div>

        <div className="flex gap-2">
          <Button onClick={loadData} disabled={loading} variant="outline">
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={handleTriggerNow} disabled={triggering}>
            <Zap className={`h-4 w-4 mr-2 ${triggering ? 'animate-pulse' : ''}`} />
            {triggering ? 'Triggering...' : 'Trigger Now'}
          </Button>
        </div>
      </div>

      {/* Status Overview */}
      {stats && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Auto-Reload Job Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Job Status</span>
                  <Badge variant={stats.scheduled ? 'default' : 'destructive'}>
                    {stats.scheduled ? 'Scheduled' : 'Not Scheduled'}
                  </Badge>
                </div>

                {stats.scheduled && stats.next_run_time && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Next Run</span>
                    <span className="font-medium flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {formatDate(stats.next_run_time)}
                    </span>
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Run Interval</span>
                  <span className="font-medium">Every 5 minutes</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Statistics Cards */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Wallets</CardTitle>
                <Users className="h-4 w-4 text-gray-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.statistics.total_wallets}</div>
                <p className="text-xs text-gray-600 mt-1">Active wallets</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Auto-Reload Enabled</CardTitle>
                <Zap className="h-4 w-4 text-yellow-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.statistics.auto_reload_enabled_count}</div>
                <Progress
                  value={stats.statistics.auto_reload_enabled_percentage}
                  className="mt-2"
                />
                <p className="text-xs text-gray-600 mt-1">
                  {stats.statistics.auto_reload_enabled_percentage.toFixed(1)}% of all wallets
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Below Threshold</CardTitle>
                <AlertCircle className="h-4 w-4 text-orange-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.statistics.wallets_below_threshold}</div>
                <p className="text-xs text-gray-600 mt-1">Need reload</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Pending Reload Amount</CardTitle>
                <DollarSign className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatCurrency(stats.statistics.total_pending_reload_amount)}
                </div>
                <p className="text-xs text-gray-600 mt-1">Total to reload</p>
              </CardContent>
            </Card>
          </div>
        </>
      )}

      {/* Last Run Summary */}
      {lastRunSummary && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Last Auto-Reload Run
            </CardTitle>
            <CardDescription>
              Completed at {formatDate(lastRunSummary.completed_at)}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Summary Stats */}
              <div className="grid gap-4 md:grid-cols-4">
                <div>
                  <p className="text-sm text-gray-600">Wallets Checked</p>
                  <p className="text-2xl font-bold">{lastRunSummary.summary.wallets_checked}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Successful Reloads</p>
                  <p className="text-2xl font-bold text-green-600">
                    {lastRunSummary.summary.successful_reloads}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Failed Reloads</p>
                  <p className="text-2xl font-bold text-red-600">
                    {lastRunSummary.summary.failed_reloads}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Amount Reloaded</p>
                  <p className="text-2xl font-bold">
                    {formatCurrency(lastRunSummary.summary.total_amount_reloaded)}
                  </p>
                </div>
              </div>

              {/* Successful Reloads */}
              {lastRunSummary.results.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    Successful Reloads
                  </h3>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Wallet ID</TableHead>
                        <TableHead>Amount</TableHead>
                        <TableHead>Balance Before</TableHead>
                        <TableHead>Payment Method</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {lastRunSummary.results.map((result, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="font-mono text-sm">
                            {result.wallet_id.substring(0, 12)}...
                          </TableCell>
                          <TableCell className="font-bold">
                            {formatCurrency(result.amount)} {result.currency}
                          </TableCell>
                          <TableCell>
                            {formatCurrency(result.balance_before)}
                          </TableCell>
                          <TableCell>{result.payment_method}</TableCell>
                          <TableCell>
                            <Badge variant="default">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              {result.status}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              {/* Errors */}
              {lastRunSummary.errors.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <AlertCircle className="h-5 w-5 text-red-600" />
                    Errors ({lastRunSummary.errors.length})
                  </h3>
                  <div className="space-y-2">
                    {lastRunSummary.errors.map((error, idx) => (
                      <Card key={idx} className="border-red-200">
                        <CardContent className="pt-4">
                          <div className="flex items-start gap-3">
                            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
                            <div className="flex-1">
                              <p className="font-medium">Wallet: {error.wallet_id.substring(0, 16)}...</p>
                              <p className="text-sm text-gray-600 mt-1">{error.error}</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* Success Message */}
              {lastRunSummary.results.length === 0 && lastRunSummary.errors.length === 0 && (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <p className="text-gray-600">
                    No wallets required reloading during the last run
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* No Last Run Data */}
      {!lastRunSummary && !loading && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">
                No auto-reload runs recorded yet. Trigger a manual run to see results.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
