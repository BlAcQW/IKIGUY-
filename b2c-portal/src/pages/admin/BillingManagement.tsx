import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { API_ENDPOINTS, apiRequest } from '@/config/api';
import { toast } from '@/components/ui/use-toast';
import {
  DollarSign,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Calendar,
  TrendingUp,
  FileText,
  Filter
} from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

interface BillingRecord {
  id: string;
  organization_id: string;
  organization_name?: string;
  automation_config_id: string;
  automation_name?: string;
  period_start: string;
  period_end: string;
  total_calls: number;
  total_cost: number;
  cost_breakdown: {
    telephony_cost: number;
    transcription_cost: number;
    llm_cost: number;
    tts_cost: number;
    vapi_cost: number;
  };
  status: 'pending' | 'billed' | 'paid';
  invoice_sent_at?: string;
  paid_at?: string;
  notes?: string;
  created_at: string;
}

interface BillingStats {
  total_pending: number;
  total_billed: number;
  total_paid: number;
  pending_amount: number;
  billed_amount: number;
  paid_amount: number;
}

interface SyncResult {
  success: boolean;
  summary?: {
    total_automations: number;
    total_calls_synced: number;
    total_billing_records: number;
    total_amount: number;
  };
  error?: string;
}

export default function BillingManagement() {
  const [records, setRecords] = useState<BillingRecord[]>([]);
  const [stats, setStats] = useState<BillingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedRecord, setSelectedRecord] = useState<BillingRecord | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [newStatus, setNewStatus] = useState<'pending' | 'billed' | 'paid'>('billed');
  const [notes, setNotes] = useState('');

  const loadBillingData = async () => {
    try {
      setLoading(true);

      // Load billing records and stats
      const [recordsRes, statsRes] = await Promise.all([
        apiRequest(API_ENDPOINTS.internal.billingRecords, {
          method: 'GET',
          params: statusFilter !== 'all' ? { status: statusFilter } : undefined
        }),
        apiRequest(API_ENDPOINTS.internal.billingStats, {
          method: 'GET'
        })
      ]);

      setRecords(recordsRes.records || []);
      setStats(statsRes.stats || null);
    } catch (error) {
      console.error('Error loading billing data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load billing data',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSyncNow = async () => {
    try {
      setSyncing(true);

      const result: SyncResult = await apiRequest(`${API_ENDPOINTS.admin.base}/billing/sync-now`, {
        method: 'POST'
      });

      if (result.success) {
        toast({
          title: 'Billing Sync Complete',
          description: `Synced ${result.summary?.total_calls_synced || 0} calls, created ${result.summary?.total_billing_records || 0} billing records`
        });

        // Reload billing data
        await loadBillingData();
      }
    } catch (error: any) {
      console.error('Error syncing billing:', error);
      toast({
        title: 'Sync Failed',
        description: error.message || 'Failed to sync billing data',
        variant: 'destructive'
      });
    } finally {
      setSyncing(false);
    }
  };

  const handleUpdateStatus = async () => {
    if (!selectedRecord) return;

    try {
      setUpdatingStatus(true);

      await apiRequest(`${API_ENDPOINTS.internal.billingRecords}/${selectedRecord.id}`, {
        method: 'PATCH',
        body: {
          status: newStatus,
          notes: notes || undefined
        }
      });

      toast({
        title: 'Status Updated',
        description: `Billing record marked as ${newStatus}`
      });

      setDialogOpen(false);
      setSelectedRecord(null);
      setNotes('');

      // Reload data
      await loadBillingData();
    } catch (error: any) {
      console.error('Error updating status:', error);
      toast({
        title: 'Update Failed',
        description: error.message || 'Failed to update status',
        variant: 'destructive'
      });
    } finally {
      setUpdatingStatus(false);
    }
  };

  const openUpdateDialog = (record: BillingRecord) => {
    setSelectedRecord(record);
    setNewStatus(record.status === 'pending' ? 'billed' : 'paid');
    setNotes(record.notes || '');
    setDialogOpen(true);
  };

  useEffect(() => {
    loadBillingData();
  }, [statusFilter]);

  const getStatusBadge = (status: string) => {
    const variants = {
      pending: { variant: 'outline' as const, icon: Clock, text: 'Pending' },
      billed: { variant: 'secondary' as const, icon: FileText, text: 'Billed' },
      paid: { variant: 'default' as const, icon: CheckCircle, text: 'Paid' }
    };

    const config = variants[status as keyof typeof variants] || variants.pending;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="gap-1">
        <Icon className="h-3 w-3" />
        {config.text}
      </Badge>
    );
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Billing Management</h1>
          <p className="text-gray-600 mt-2">
            Manage billing records, sync VAPI calls, and track payment status
          </p>
        </div>

        <Button onClick={handleSyncNow} disabled={syncing}>
          <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Syncing...' : 'Sync Now'}
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending Bills</CardTitle>
              <Clock className="h-4 w-4 text-orange-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(stats.pending_amount)}</div>
              <p className="text-xs text-gray-600 mt-1">
                {stats.total_pending} billing records
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Billed</CardTitle>
              <FileText className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(stats.billed_amount)}</div>
              <p className="text-xs text-gray-600 mt-1">
                {stats.total_billed} invoices sent
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Paid</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(stats.paid_amount)}</div>
              <p className="text-xs text-gray-600 mt-1">
                {stats.total_paid} payments received
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Billing Records Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Billing Records</CardTitle>
              <CardDescription>View and manage billing records across all organizations</CardDescription>
            </div>

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Records</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="billed">Billed</SelectItem>
                <SelectItem value="paid">Paid</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : records.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No billing records found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Organization</TableHead>
                  <TableHead>Automation</TableHead>
                  <TableHead>Period</TableHead>
                  <TableHead>Calls</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {records.map((record) => (
                  <TableRow key={record.id}>
                    <TableCell className="font-medium">
                      {record.organization_name || record.organization_id}
                    </TableCell>
                    <TableCell>
                      {record.automation_name || record.automation_config_id}
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {formatDate(record.period_start)} - {formatDate(record.period_end)}
                      </div>
                    </TableCell>
                    <TableCell>{record.total_calls}</TableCell>
                    <TableCell className="font-mono">
                      {formatCurrency(record.total_cost)}
                    </TableCell>
                    <TableCell>{getStatusBadge(record.status)}</TableCell>
                    <TableCell>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openUpdateDialog(record)}
                        disabled={record.status === 'paid'}
                      >
                        Update
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Update Status Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Update Billing Status</DialogTitle>
            <DialogDescription>
              Change the status of this billing record
            </DialogDescription>
          </DialogHeader>

          {selectedRecord && (
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Current Status</Label>
                <div>{getStatusBadge(selectedRecord.status)}</div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-status">New Status</Label>
                <Select
                  value={newStatus}
                  onValueChange={(value: any) => setNewStatus(value)}
                >
                  <SelectTrigger id="new-status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {selectedRecord.status === 'pending' && (
                      <SelectItem value="billed">Mark as Billed</SelectItem>
                    )}
                    {(selectedRecord.status === 'pending' || selectedRecord.status === 'billed') && (
                      <SelectItem value="paid">Mark as Paid</SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="notes">Notes (Optional)</Label>
                <Textarea
                  id="notes"
                  placeholder="Add any notes about this status change..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                />
              </div>

              <div className="bg-gray-50 p-3 rounded-md text-sm">
                <p className="font-medium mb-1">Billing Details:</p>
                <p>Period: {formatDate(selectedRecord.period_start)} - {formatDate(selectedRecord.period_end)}</p>
                <p>Total Calls: {selectedRecord.total_calls}</p>
                <p>Amount: {formatCurrency(selectedRecord.total_cost)}</p>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDialogOpen(false)}
              disabled={updatingStatus}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpdateStatus}
              disabled={updatingStatus}
            >
              {updatingStatus ? 'Updating...' : 'Update Status'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
