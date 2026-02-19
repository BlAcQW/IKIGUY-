import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { API_ENDPOINTS, apiRequest } from '@/config/api';
import { toast } from '@/components/ui/use-toast';
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  Activity,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
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
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface FraudCheck {
  id: string;
  transaction_id: string;
  wallet_id: string;
  user_id: string;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  triggered_rules: string[];
  decision: 'allow' | 'review' | 'block';
  action_taken: 'none' | 'flagged' | 'blocked' | 'approved';
  requires_review: boolean;
  status: 'pending' | 'reviewed' | 'resolved';
  created_at: string;
  metadata?: any;
}

interface FraudStats {
  pending_review: number;
  by_decision: Record<string, any>;
  by_risk_level: Record<string, any>;
  top_triggered_rules: Array<{ _id: string; count: number }>;
}

interface FraudRule {
  id: string;
  name: string;
  description: string;
  rule_type: string;
  condition: any;
  risk_score: number;
  action: string;
  is_active: boolean;
}

export default function FraudDetection() {
  const [reviewQueue, setReviewQueue] = useState<FraudCheck[]>([]);
  const [stats, setStats] = useState<FraudStats | null>(null);
  const [rules, setRules] = useState<FraudRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCheck, setSelectedCheck] = useState<FraudCheck | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [actionType, setActionType] = useState<'approve' | 'reject'>('approve');
  const [processing, setProcessing] = useState(false);
  const [notes, setNotes] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);

      const [queueRes, statsRes, rulesRes] = await Promise.all([
        apiRequest(`${API_ENDPOINTS.admin.base}/fraud/review-queue?limit=50`, {
          method: 'GET'
        }),
        apiRequest(`${API_ENDPOINTS.admin.base}/fraud/statistics?days=30`, {
          method: 'GET'
        }),
        apiRequest(`${API_ENDPOINTS.admin.base}/fraud/rules`, {
          method: 'GET'
        })
      ]);

      setReviewQueue(queueRes.checks || []);
      setStats(statsRes.statistics || null);
      setRules(rulesRes.rules || []);
    } catch (error) {
      console.error('Error loading fraud detection data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load fraud detection data',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedCheck) return;

    try {
      setProcessing(true);

      await apiRequest(`${API_ENDPOINTS.admin.base}/fraud/approve/${selectedCheck.id}`, {
        method: 'POST',
        body: { notes: notes || undefined }
      });

      toast({
        title: 'Transaction Approved',
        description: 'The flagged transaction has been approved'
      });

      setDialogOpen(false);
      setSelectedCheck(null);
      setNotes('');

      // Reload data
      await loadData();
    } catch (error: any) {
      console.error('Error approving transaction:', error);
      toast({
        title: 'Approval Failed',
        description: error.message || 'Failed to approve transaction',
        variant: 'destructive'
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!selectedCheck || !rejectionReason) {
      toast({
        title: 'Rejection Reason Required',
        description: 'Please provide a reason for rejecting this transaction',
        variant: 'destructive'
      });
      return;
    }

    try {
      setProcessing(true);

      await apiRequest(`${API_ENDPOINTS.admin.base}/fraud/reject/${selectedCheck.id}`, {
        method: 'POST',
        body: {
          reason: rejectionReason,
          notes: notes || undefined
        }
      });

      toast({
        title: 'Transaction Rejected',
        description: 'The flagged transaction has been rejected'
      });

      setDialogOpen(false);
      setSelectedCheck(null);
      setNotes('');
      setRejectionReason('');

      // Reload data
      await loadData();
    } catch (error: any) {
      console.error('Error rejecting transaction:', error);
      toast({
        title: 'Rejection Failed',
        description: error.message || 'Failed to reject transaction',
        variant: 'destructive'
      });
    } finally {
      setProcessing(false);
    }
  };

  const openDialog = (check: FraudCheck, action: 'approve' | 'reject') => {
    setSelectedCheck(check);
    setActionType(action);
    setNotes('');
    setRejectionReason('');
    setDialogOpen(true);
  };

  useEffect(() => {
    loadData();
  }, []);

  const getRiskBadge = (level: string) => {
    const variants = {
      low: { variant: 'default' as const, color: 'text-green-700 bg-green-100' },
      medium: { variant: 'secondary' as const, color: 'text-yellow-700 bg-yellow-100' },
      high: { variant: 'destructive' as const, color: 'text-orange-700 bg-orange-100' },
      critical: { variant: 'destructive' as const, color: 'text-red-700 bg-red-100' }
    };

    const config = variants[level as keyof typeof variants] || variants.low;

    return (
      <Badge className={config.color}>
        {level.toUpperCase()}
      </Badge>
    );
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
            <Shield className="h-8 w-8" />
            Fraud Detection
          </h1>
          <p className="text-gray-600 mt-2">
            Monitor and review transactions flagged by fraud detection rules
          </p>
        </div>

        <Button onClick={loadData} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <Tabs defaultValue="review" className="space-y-6">
        <TabsList>
          <TabsTrigger value="review">Review Queue</TabsTrigger>
          <TabsTrigger value="stats">Statistics</TabsTrigger>
          <TabsTrigger value="rules">Rules</TabsTrigger>
        </TabsList>

        {/* Review Queue Tab */}
        <TabsContent value="review" className="space-y-4">
          {stats && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Pending Reviews</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-orange-600">
                  {stats.pending_review}
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  Transactions awaiting manual review
                </p>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Review Queue</CardTitle>
              <CardDescription>Transactions flagged for fraud review</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
                </div>
              ) : reviewQueue.length === 0 ? (
                <div className="text-center py-12">
                  <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <p className="text-gray-600">No transactions pending review</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Transaction ID</TableHead>
                      <TableHead>User</TableHead>
                      <TableHead>Risk Score</TableHead>
                      <TableHead>Risk Level</TableHead>
                      <TableHead>Triggered Rules</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {reviewQueue.map((check) => (
                      <TableRow key={check.id}>
                        <TableCell className="font-mono text-sm">
                          {check.transaction_id.substring(0, 12)}...
                        </TableCell>
                        <TableCell className="font-mono text-sm">
                          {check.user_id.substring(0, 12)}...
                        </TableCell>
                        <TableCell>
                          <span className="font-bold">{check.risk_score.toFixed(1)}</span>
                        </TableCell>
                        <TableCell>{getRiskBadge(check.risk_level)}</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {check.triggered_rules.slice(0, 2).map((rule, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {rule}
                              </Badge>
                            ))}
                            {check.triggered_rules.length > 2 && (
                              <Badge variant="outline" className="text-xs">
                                +{check.triggered_rules.length - 2}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">
                          {formatDate(check.created_at)}
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => openDialog(check, 'approve')}
                              className="text-green-600 hover:text-green-700"
                            >
                              <CheckCircle className="h-4 w-4 mr-1" />
                              Approve
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => openDialog(check, 'reject')}
                              className="text-red-600 hover:text-red-700"
                            >
                              <XCircle className="h-4 w-4 mr-1" />
                              Reject
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Statistics Tab */}
        <TabsContent value="stats" className="space-y-4">
          {stats && (
            <>
              <div className="grid gap-4 md:grid-cols-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
                    <Clock className="h-4 w-4 text-orange-600" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats.pending_review}</div>
                  </CardContent>
                </Card>

                {Object.entries(stats.by_risk_level).map(([level, data]: [string, any]) => (
                  <Card key={level}>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium capitalize">{level} Risk</CardTitle>
                      <AlertTriangle className="h-4 w-4" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{data.count}</div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Most Triggered Rules</CardTitle>
                  <CardDescription>Top fraud detection rules (last 30 days)</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {stats.top_triggered_rules.map((rule) => (
                      <div key={rule._id} className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="font-medium">{rule._id}</p>
                        </div>
                        <Badge variant="secondary">{rule.count} triggers</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Rules Tab */}
        <TabsContent value="rules" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Fraud Detection Rules</CardTitle>
              <CardDescription>Active fraud detection rules and their configurations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {rules.map((rule) => (
                  <Card key={rule.id}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">{rule.name}</CardTitle>
                        <Badge variant={rule.is_active ? 'default' : 'secondary'}>
                          {rule.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                      <CardDescription>{rule.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-gray-600">Risk Score</p>
                          <p className="font-bold">{rule.risk_score}</p>
                        </div>
                        <div>
                          <p className="text-gray-600">Action</p>
                          <p className="font-bold capitalize">{rule.action}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Review Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {actionType === 'approve' ? 'Approve Transaction' : 'Reject Transaction'}
            </DialogTitle>
            <DialogDescription>
              {actionType === 'approve'
                ? 'Approve this flagged transaction and allow it to proceed'
                : 'Reject this flagged transaction and block it permanently'}
            </DialogDescription>
          </DialogHeader>

          {selectedCheck && (
            <div className="space-y-4 py-4">
              <div className="bg-gray-50 p-3 rounded-md space-y-2 text-sm">
                <p><span className="font-medium">Transaction:</span> {selectedCheck.transaction_id}</p>
                <p><span className="font-medium">Risk Score:</span> {selectedCheck.risk_score}</p>
                <p><span className="font-medium">Risk Level:</span> {getRiskBadge(selectedCheck.risk_level)}</p>
                <p><span className="font-medium">Triggered Rules:</span></p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {selectedCheck.triggered_rules.map((rule, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      {rule}
                    </Badge>
                  ))}
                </div>
              </div>

              {actionType === 'reject' && (
                <div className="space-y-2">
                  <Label htmlFor="rejection-reason">Rejection Reason *</Label>
                  <Input
                    id="rejection-reason"
                    placeholder="Why are you rejecting this transaction?"
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="review-notes">Notes (Optional)</Label>
                <Textarea
                  id="review-notes"
                  placeholder="Add any additional notes..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDialogOpen(false)}
              disabled={processing}
            >
              Cancel
            </Button>
            <Button
              onClick={actionType === 'approve' ? handleApprove : handleReject}
              disabled={processing || (actionType === 'reject' && !rejectionReason)}
              variant={actionType === 'approve' ? 'default' : 'destructive'}
            >
              {processing ? 'Processing...' : actionType === 'approve' ? 'Approve' : 'Reject'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
