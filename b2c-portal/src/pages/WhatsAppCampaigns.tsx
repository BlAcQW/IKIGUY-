import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { useOrganization } from '@/contexts/OrganizationContext';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  MessageCircle,
  Plus,
  Search,
  Play,
  Pause,
  XCircle,
  Eye,
  Trash2,
  RefreshCw,
  BarChart3,
  CheckCircle2,
  AlertCircle,
  Clock,
  Image,
  Video,
  FileText,
  Music,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  getWhatsAppCampaigns,
  getWhatsAppCampaign,
  deleteWhatsAppCampaign,
  startWhatsAppCampaign,
  pauseWhatsAppCampaign,
  cancelWhatsAppCampaign,
  getWhatsAppCampaignAnalytics,
  syncWhatsAppTemplates,
  WhatsAppCampaign,
  WhatsAppCampaignAnalytics,
  getCampaignStatusColor,
  formatCampaignStatus,
  calculateProgressPercentage,
  formatCost,
} from '@/lib/whatsapp-campaigns-api';

interface WhatsAppCampaignStats {
  total_campaigns: number;
  active_campaigns: number;
  total_messages_sent: number;
  total_cost: number;
}

const WhatsAppCampaigns: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { currentOrganization } = useOrganization();

  // State
  const [campaigns, setCampaigns] = useState<WhatsAppCampaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [refreshing, setRefreshing] = useState(false);

  // Dialog states
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);
  const [showAnalyticsDialog, setShowAnalyticsDialog] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState<WhatsAppCampaign | null>(null);
  const [campaignAnalytics, setCampaignAnalytics] = useState<WhatsAppCampaignAnalytics | null>(null);

  // Stats
  const [stats, setStats] = useState<WhatsAppCampaignStats>({
    total_campaigns: 0,
    active_campaigns: 0,
    total_messages_sent: 0,
    total_cost: 0,
  });

  // Fetch campaigns
  const fetchCampaigns = async () => {
    try {
      const params = statusFilter !== 'all' ? { status: statusFilter } : {};
      const response = await getWhatsAppCampaigns(params);
      setCampaigns(response.campaigns);

      // Calculate stats
      const stats: WhatsAppCampaignStats = {
        total_campaigns: response.total,
        active_campaigns: response.campaigns.filter(c => c.status === 'running').length,
        total_messages_sent: response.campaigns.reduce((sum, c) => sum + c.progress.sent, 0),
        total_cost: response.campaigns.reduce((sum, c) => sum + c.total_cost, 0),
      };
      setStats(stats);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to fetch WhatsApp campaigns',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (currentOrganization) {
      fetchCampaigns();
      // Auto-refresh every 10 seconds for running campaigns
      const interval = setInterval(() => {
        if (campaigns.some(c => c.status === 'running')) {
          fetchCampaigns();
        }
      }, 10000);
      return () => clearInterval(interval);
    }
  }, [currentOrganization, statusFilter]);

  // Handle refresh
  const handleRefresh = () => {
    setRefreshing(true);
    fetchCampaigns();
  };

  // Handle sync templates
  const handleSyncTemplates = async () => {
    try {
      const result = await syncWhatsAppTemplates();
      toast({
        title: 'Success',
        description: `Synced ${result.count} templates from WhatsApp`,
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to sync templates',
        variant: 'destructive',
      });
    }
  };

  // Handle view details
  const handleViewDetails = async (campaign: WhatsAppCampaign) => {
    setSelectedCampaign(campaign);
    setShowDetailsDialog(true);
  };

  // Handle view analytics
  const handleViewAnalytics = async (campaign: WhatsAppCampaign) => {
    try {
      const analytics = await getWhatsAppCampaignAnalytics(campaign.id);
      setCampaignAnalytics(analytics);
      setSelectedCampaign(campaign);
      setShowAnalyticsDialog(true);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to fetch analytics',
        variant: 'destructive',
      });
    }
  };

  // Handle start campaign
  const handleStartCampaign = async (campaignId: string) => {
    try {
      await startWhatsAppCampaign(campaignId);
      toast({
        title: 'Success',
        description: 'Campaign started successfully',
      });
      fetchCampaigns();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to start campaign',
        variant: 'destructive',
      });
    }
  };

  // Handle pause campaign
  const handlePauseCampaign = async (campaignId: string) => {
    try {
      await pauseWhatsAppCampaign(campaignId);
      toast({
        title: 'Success',
        description: 'Campaign paused successfully',
      });
      fetchCampaigns();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to pause campaign',
        variant: 'destructive',
      });
    }
  };

  // Handle cancel campaign
  const handleCancelCampaign = async (campaignId: string) => {
    if (!confirm('Are you sure you want to cancel this campaign?')) return;

    try {
      await cancelWhatsAppCampaign(campaignId);
      toast({
        title: 'Success',
        description: 'Campaign cancelled successfully',
      });
      fetchCampaigns();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to cancel campaign',
        variant: 'destructive',
      });
    }
  };

  // Handle delete campaign
  const handleDeleteCampaign = async (campaignId: string) => {
    if (!confirm('Are you sure you want to delete this campaign? This action cannot be undone.')) return;

    try {
      await deleteWhatsAppCampaign(campaignId);
      toast({
        title: 'Success',
        description: 'Campaign deleted successfully',
      });
      fetchCampaigns();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete campaign',
        variant: 'destructive',
      });
    }
  };

  // Filter campaigns
  const filteredCampaigns = campaigns.filter(campaign =>
    campaign.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get media icon
  const getMediaIcon = (mediaType?: string) => {
    switch (mediaType) {
      case 'image':
        return <Image className="h-4 w-4" />;
      case 'video':
        return <Video className="h-4 w-4" />;
      case 'audio':
        return <Music className="h-4 w-4" />;
      case 'document':
        return <FileText className="h-4 w-4" />;
      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <DashboardSidebar />

      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
                  <MessageCircle className="h-8 w-8 text-green-600" />
                  WhatsApp Campaigns
                </h1>
                <p className="text-gray-600 mt-1">
                  Create and manage WhatsApp Business API campaigns
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={handleSyncTemplates}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Sync Templates
                </Button>
                <Button
                  onClick={() => navigate('/whatsapp-campaigns/create')}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create Campaign
                </Button>
              </div>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Total Campaigns
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stats.total_campaigns}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Active Campaigns
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-green-600">{stats.active_campaigns}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Messages Sent
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stats.total_messages_sent.toLocaleString()}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Total Cost
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{formatCost(stats.total_cost)}</div>
              </CardContent>
            </Card>
          </div>

          {/* Filters */}
          <Card className="mb-6">
            <CardContent className="pt-6">
              <div className="flex gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                      placeholder="Search campaigns..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Filter by status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="draft">Draft</SelectItem>
                    <SelectItem value="running">Running</SelectItem>
                    <SelectItem value="paused">Paused</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
                <Button
                  variant="outline"
                  onClick={handleRefresh}
                  disabled={refreshing}
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Campaigns Table */}
          <Card>
            <CardHeader>
              <CardTitle>Campaigns</CardTitle>
              <CardDescription>
                {filteredCampaigns.length} campaign{filteredCampaigns.length !== 1 ? 's' : ''}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-12">
                  <RefreshCw className="h-8 w-8 animate-spin mx-auto text-gray-400" />
                  <p className="text-gray-600 mt-2">Loading campaigns...</p>
                </div>
              ) : filteredCampaigns.length === 0 ? (
                <div className="text-center py-12">
                  <MessageCircle className="h-12 w-12 mx-auto text-gray-400" />
                  <p className="text-gray-600 mt-2">No campaigns found</p>
                  <Button className="mt-4" onClick={() => navigate('/whatsapp-campaigns/create')}>
                    Create Your First Campaign
                  </Button>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Campaign</TableHead>
                      <TableHead>Template</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Progress</TableHead>
                      <TableHead>Cost</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredCampaigns.map((campaign) => {
                      const progress = calculateProgressPercentage(campaign);

                      return (
                        <TableRow key={campaign.id}>
                          <TableCell>
                            <div>
                              <div className="font-medium">{campaign.name}</div>
                              <div className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                                {campaign.config.enable_media && (
                                  <span className="flex items-center gap-1">
                                    {getMediaIcon(campaign.config.media_type)}
                                    <span className="text-xs">Media</span>
                                  </span>
                                )}
                                {campaign.config.enable_buttons && (
                                  <span className="text-xs ml-2">
                                    {campaign.config.buttons.length} Button{campaign.config.buttons.length !== 1 ? 's' : ''}
                                  </span>
                                )}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="text-sm">{campaign.template_name || 'N/A'}</div>
                          </TableCell>
                          <TableCell>
                            <Badge className={getCampaignStatusColor(campaign.status)}>
                              {formatCampaignStatus(campaign.status)}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="space-y-1">
                              <div className="flex items-center justify-between text-sm">
                                <span>{campaign.progress.sent} / {campaign.progress.total_recipients}</span>
                                <span className="text-gray-500">{progress}%</span>
                              </div>
                              <Progress value={progress} className="h-2" />
                              <div className="flex gap-2 text-xs text-gray-500">
                                <span className="flex items-center gap-1">
                                  <CheckCircle2 className="h-3 w-3 text-green-600" />
                                  {campaign.progress.delivered}
                                </span>
                                <span className="flex items-center gap-1">
                                  <Eye className="h-3 w-3 text-blue-600" />
                                  {campaign.progress.read}
                                </span>
                                <span className="flex items-center gap-1">
                                  <AlertCircle className="h-3 w-3 text-red-600" />
                                  {campaign.progress.failed}
                                </span>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="text-sm font-medium">{formatCost(campaign.total_cost)}</div>
                          </TableCell>
                          <TableCell>
                            <div className="text-sm text-gray-600">
                              {new Date(campaign.created_at).toLocaleDateString()}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-2">
                              {campaign.status === 'draft' && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleStartCampaign(campaign.id)}
                                >
                                  <Play className="h-4 w-4" />
                                </Button>
                              )}
                              {campaign.status === 'running' && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handlePauseCampaign(campaign.id)}
                                >
                                  <Pause className="h-4 w-4" />
                                </Button>
                              )}
                              {campaign.status === 'paused' && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleStartCampaign(campaign.id)}
                                >
                                  <Play className="h-4 w-4" />
                                </Button>
                              )}
                              {(campaign.status === 'running' || campaign.status === 'paused') && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleCancelCampaign(campaign.id)}
                                >
                                  <XCircle className="h-4 w-4" />
                                </Button>
                              )}
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleViewAnalytics(campaign)}
                              >
                                <BarChart3 className="h-4 w-4" />
                              </Button>
                              {campaign.status !== 'running' && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleDeleteCampaign(campaign.id)}
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Analytics Dialog */}
      {showAnalyticsDialog && campaignAnalytics && selectedCampaign && (
        <Dialog open={showAnalyticsDialog} onOpenChange={setShowAnalyticsDialog}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Campaign Analytics</DialogTitle>
              <DialogDescription>{selectedCampaign.name}</DialogDescription>
            </DialogHeader>

            <div className="space-y-6">
              {/* Progress Section */}
              <div>
                <h3 className="font-semibold mb-3">Delivery Progress</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-600">Total Recipients</div>
                    <div className="text-2xl font-bold">{campaignAnalytics.progress.total}</div>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <div className="text-sm text-gray-600">Sent</div>
                    <div className="text-2xl font-bold text-green-600">{campaignAnalytics.progress.sent}</div>
                  </div>
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <div className="text-sm text-gray-600">Delivered</div>
                    <div className="text-2xl font-bold text-blue-600">{campaignAnalytics.progress.delivered}</div>
                  </div>
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <div className="text-sm text-gray-600">Read</div>
                    <div className="text-2xl font-bold text-purple-600">{campaignAnalytics.progress.read}</div>
                  </div>
                </div>
              </div>

              {/* Rates Section */}
              <div>
                <h3 className="font-semibold mb-3">Performance Metrics</h3>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Success Rate</span>
                    <span className="font-semibold">{campaignAnalytics.progress.success_rate.toFixed(1)}%</span>
                  </div>
                  <Progress value={campaignAnalytics.progress.success_rate} className="h-2" />

                  <div className="flex justify-between items-center mt-4">
                    <span className="text-sm text-gray-600">Delivery Rate</span>
                    <span className="font-semibold">{campaignAnalytics.progress.delivery_rate.toFixed(1)}%</span>
                  </div>
                  <Progress value={campaignAnalytics.progress.delivery_rate} className="h-2" />

                  <div className="flex justify-between items-center mt-4">
                    <span className="text-sm text-gray-600">Read Rate</span>
                    <span className="font-semibold">{campaignAnalytics.progress.read_rate.toFixed(1)}%</span>
                  </div>
                  <Progress value={campaignAnalytics.progress.read_rate} className="h-2" />
                </div>
              </div>

              {/* Cost Section */}
              <div>
                <h3 className="font-semibold mb-3">Cost Analysis</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-600">Total Cost</div>
                    <div className="text-2xl font-bold">{formatCost(campaignAnalytics.cost.total)}</div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-600">Average per Message</div>
                    <div className="text-2xl font-bold">{formatCost(campaignAnalytics.cost.average)}</div>
                  </div>
                </div>
              </div>

              {/* Timing Section */}
              {campaignAnalytics.timing.started_at && (
                <div>
                  <h3 className="font-semibold mb-3">Timeline</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Started</span>
                      <span>{new Date(campaignAnalytics.timing.started_at).toLocaleString()}</span>
                    </div>
                    {campaignAnalytics.timing.completed_at && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Completed</span>
                          <span>{new Date(campaignAnalytics.timing.completed_at).toLocaleString()}</span>
                        </div>
                        {campaignAnalytics.timing.duration_seconds && (
                          <div className="flex justify-between">
                            <span className="text-gray-600">Duration</span>
                            <span>{Math.round(campaignAnalytics.timing.duration_seconds / 60)} minutes</span>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAnalyticsDialog(false)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default WhatsAppCampaigns;
