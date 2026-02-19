import React, { useState, useEffect, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/lib/api-client';
import { useOrganization } from '@/contexts/OrganizationContext';
import { useCampaignSSE } from '@kasaai/shared-frontend/hooks';
import { API_BASE_URL } from '@/config/api-config';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  MessageSquare,
  Plus,
  Search,
  Play,
  Pause,
  XCircle,
  Eye,
  Edit,
  Trash2,
  Users,
  Send,
  BarChart3,
  Clock,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Copy,
  X
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
import { API_BASE_URL } from '@/config/api-config';


interface SMSCampaign {
  id: string;
  name: string;
  organization_id: string;
  user_id: string;
  template_content: string;
  audience_id: string | null;
  status: 'draft' | 'scheduled' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  progress: {
    total_recipients: number;
    sent: number;
    delivered: number;
    failed: number;
    pending: number;
  };
  config: {
    send_rate_per_second: number;
    batch_size: number;
    retry_failed: boolean;
    max_retries: number;
    sender_id: string | null;
    scheduled_time: string | null;
  };
  total_cost: number;
  sms_provider: string;
  // Historical tracking (persists across restarts)
  total_messages_sent_all_time: number;
  total_cost_all_time: number;
  total_runs: number;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

interface Audience {
  id: string;
  name: string;
  size: number;
  status: string;
}

interface TemplatePreview {
  rendered_content: string;
  placeholders: string[];
  character_count: number;
  segment_count: number;
}

interface SMSCampaignStats {
  total_campaigns: number;
  active_campaigns: number;
  total_messages_sent: number;
  total_cost: number;
}

const SMSCampaigns: React.FC = () => {
  const { toast } = useToast();
  const { currentOrganization } = useOrganization();

  // State
  const [campaigns, setCampaigns] = useState<SMSCampaign[]>([]);
  const [audiences, setAudiences] = useState<Audience[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState<SMSCampaign | null>(null);
  const [editCampaignId, setEditCampaignId] = useState<string>('');

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    template_content: '',
    audience_id: '',
    sender_id: 'IMPACT2025',  // Default sender ID
    send_rate: '1',
    sms_provider: 'arkesel',  // Default to Arkesel
    excluded_phone_numbers: ''  // Phone number exclusion (one per line)
  });

  // Recipient preview state
  const [recipientCount, setRecipientCount] = useState<number | null>(null);
  const [sampleRecipients, setSampleRecipients] = useState<Array<{name: string, phone: string}>>([]);
  const [fetchingCount, setFetchingCount] = useState(false);
  const [showAllRecipientsModal, setShowAllRecipientsModal] = useState(false);
  const [allRecipients, setAllRecipients] = useState<Array<{name: string, phone: string}>>([]);
  const [loadingAllRecipients, setLoadingAllRecipients] = useState(false);
  const [templatePreview, setTemplatePreview] = useState<TemplatePreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // Stats
  const [stats, setStats] = useState<SMSCampaignStats>({
    total_campaigns: 0,
    active_campaigns: 0,
    total_messages_sent: 0,
    total_cost: 0
  });

  // Message analytics state
  const [messages, setMessages] = useState<any[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [messagesPage, setMessagesPage] = useState(1);
  const [messagesLimit] = useState(100);

  // Fetch campaigns
  const fetchCampaigns = async () => {
    setLoading(true);
    try {
      const response = await api.get<{ campaigns: SMSCampaign[], total: number }>('/sms-campaigns/');
      setCampaigns(response.campaigns || []);

      // Calculate stats (defensive: handle missing progress)
      const activeCampaigns = response.campaigns.filter(c => c.status === 'running').length;
      const totalSent = response.campaigns.reduce((sum, c) => sum + (c.progress?.sent || 0), 0);
      const totalCost = response.campaigns.reduce((sum, c) => sum + c.total_cost, 0);

      setStats({
        total_campaigns: response.campaigns.length,
        active_campaigns: activeCampaigns,
        total_messages_sent: totalSent,
        total_cost: totalCost
      });
    } catch (error) {
      console.error('Error fetching campaigns:', error);
      toast({
        title: "Failed to load campaigns",
        description: "Please check your connection and try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  // Fetch audiences for dropdown
  const fetchAudiences = async () => {
    try {
      const response = await api.get<Audience[]>('/audiences/');
      setAudiences(response || []);
    } catch (error) {
      console.error('Error fetching audiences:', error);
    }
  };

  // Fetch messages for a campaign
  const fetchMessages = async (campaignId: string, page: number = 1, status?: string) => {
    setMessagesLoading(true);
    try {
      const statusParam = status ? `&status=${status}` : '';
      const response = await api.get<{messages: any[], total: number}>(
        `/sms-campaigns/${campaignId}/messages?page=${page}&limit=${messagesLimit}${statusParam}`
      );
      setMessages(response.messages || []);
    } catch (error) {
      console.error('Error fetching messages:', error);
      toast({
        title: "Failed to load messages",
        description: "Could not fetch campaign messages.",
        variant: "destructive"
      });
    } finally {
      setMessagesLoading(false);
    }
  };

  // Fetch recipient count and sample
  const fetchRecipientCount = async () => {
    if (!formData.audience_id) {
      setRecipientCount(null);
      setSampleRecipients([]);
      return;
    }

    setFetchingCount(true);
    try {
      const params = new URLSearchParams({
        audience_id: formData.audience_id
      });

      // Add excluded numbers if any
      if (formData.excluded_phone_numbers) {
        const excludedNumbers = formData.excluded_phone_numbers
          .split('\n')
          .map(line => line.trim())
          .filter(line => line.length > 0);
        excludedNumbers.forEach(num => params.append('excluded_phone_numbers', num));
      }

      const response = await api.get<{count: number, sample_recipients: Array<{name: string, phone: string}>}>(
        `/sms-campaigns/count-recipients?${params.toString()}`
      );

      setRecipientCount(response.count || 0);
      setSampleRecipients(response.sample_recipients || []);
    } catch (error) {
      console.error('Error fetching recipient count:', error);
      setRecipientCount(null);
      setSampleRecipients([]);
    } finally {
      setFetchingCount(false);
    }
  };

  // Fetch all recipients for preview modal
  const fetchAllRecipients = async () => {
    if (!formData.audience_id) return;

    setLoadingAllRecipients(true);
    try {
      const params = new URLSearchParams({
        audience_id: formData.audience_id
      });

      // Add excluded numbers if any
      if (formData.excluded_phone_numbers) {
        const excludedNumbers = formData.excluded_phone_numbers
          .split('\n')
          .map(line => line.trim())
          .filter(line => line.length > 0);
        excludedNumbers.forEach(num => params.append('excluded_phone_numbers', num));
      }

      const response = await api.get<{recipients: Array<{name: string, phone: string}>}>(
        `/sms-campaigns/preview-recipients?${params.toString()}`
      );

      setAllRecipients(response.recipients || []);
      setShowAllRecipientsModal(true);
    } catch (error) {
      console.error('Error fetching all recipients:', error);
      toast({
        title: "Failed to load recipients",
        description: "Could not fetch recipient list.",
        variant: "destructive"
      });
    } finally {
      setLoadingAllRecipients(false);
    }
  };

  useEffect(() => {
    if (currentOrganization) {
      fetchCampaigns();
      fetchAudiences();
    }
  }, [currentOrganization]);

  // Fetch recipient count when audience or exclusions change
  useEffect(() => {
    if (formData.audience_id) {
      fetchRecipientCount();
    }
  }, [formData.audience_id, formData.excluded_phone_numbers]);

  // Real-time campaign updates via SSE (replaces polling)
  const handleCampaignUpdate = useCallback((update: any) => {
    setCampaigns(prevCampaigns =>
      prevCampaigns.map(campaign => {
        if (campaign.id === update.id) {
          // Defensive: Ensure progress exists with default values
          const updateProgress = update.progress || {
            total_recipients: campaign.progress.total_recipients,
            sent: campaign.progress.sent,
            delivered: campaign.progress.delivered,
            failed: campaign.progress.failed,
            pending: campaign.progress.pending
          };

          // Defensive: Ensure status exists with fallback
          const updateStatus = update.status || campaign.status;

          // Only update if data actually changed to prevent unnecessary re-renders
          const hasChanged =
            campaign.status !== updateStatus ||
            campaign.progress.sent !== updateProgress.sent ||
            campaign.progress.failed !== updateProgress.failed ||
            campaign.progress.pending !== updateProgress.pending;

          if (!hasChanged) return campaign;

          // Merge the update with existing campaign data
          return {
            ...campaign,
            status: updateStatus,
            progress: updateProgress,
            total_cost: update.total_cost ?? campaign.total_cost,
            error_message: update.error_message ?? campaign.error_message
          };
        }
        return campaign;
      })
    );

    // Update stats when campaign data changes (defensive: handle missing progress)
    setCampaigns(prevCampaigns => {
      const activeCampaigns = prevCampaigns.filter(c => c.status === 'running').length;
      const totalSent = prevCampaigns.reduce((sum, c) => sum + (c.progress?.sent || 0), 0);
      const totalCost = prevCampaigns.reduce((sum, c) => sum + c.total_cost, 0);

      setStats({
        total_campaigns: prevCampaigns.length,
        active_campaigns: activeCampaigns,
        total_messages_sent: totalSent,
        total_cost: totalCost
      });

      return prevCampaigns;
    });
  }, []);

  // Get auth token from localStorage
  const authToken = localStorage.getItem('access_token');

  // Use SSE for real-time updates (shared service)
  const { activeConnections } = useCampaignSSE(
    campaigns,
    handleCampaignUpdate,
    authToken,
    API_BASE_URL
  );

  // Filter campaigns
  const filteredCampaigns = campaigns.filter(campaign => {
    const matchesSearch = campaign.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || campaign.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Preview template
  const previewTemplate = async () => {
    if (!formData.template_content) return;

    setPreviewLoading(true);
    try {
      const response = await api.post<TemplatePreview>('/sms-campaigns/template/preview', {
        template_content: formData.template_content,
        sample_data: { name: 'John Doe', phone: '+1234567890' }
      });
      setTemplatePreview(response);
    } catch (error) {
      console.error('Error previewing template:', error);
    } finally {
      setPreviewLoading(false);
    }
  };

  // Create campaign
  const handleCreateCampaign = async () => {
    if (!formData.name || !formData.template_content) {
      toast({
        title: "Missing required fields",
        description: "Please fill in campaign name and message template.",
        variant: "destructive"
      });
      return;
    }

    try {
      // Parse excluded phone numbers
      const excludedNumbers = formData.excluded_phone_numbers
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);

      const payload = {
        name: formData.name,
        template_content: formData.template_content,
        audience_id: formData.audience_id || null,
        excluded_phone_numbers: excludedNumbers.length > 0 ? excludedNumbers : [],
        config: {
          send_rate_per_second: parseFloat(formData.send_rate),
          sender_id: formData.sender_id || null
        },
        sms_provider: formData.sms_provider
      };

      const response = await api.post<SMSCampaign>('/sms-campaigns/', payload);
      const campaignId = response.id;

      // Auto-prepare messages after creation
      try {
        await api.post(`/sms-campaigns/${campaignId}/prepare`);
        toast({
          title: "Campaign created",
          description: "Your SMS campaign has been created and messages are prepared."
        });
      } catch (prepareError) {
        console.error('Error preparing messages:', prepareError);
        toast({
          title: "Campaign created",
          description: "Campaign created but message preparation failed. You can retry from the campaign details.",
          variant: "default"
        });
      }

      setShowCreateDialog(false);
      setFormData({
        name: '',
        template_content: '',
        audience_id: '',
        sender_id: 'IMPACT2025',
        send_rate: '1',
        sms_provider: 'arkesel',
        excluded_phone_numbers: ''
      });
      setTemplatePreview(null);
      setRecipientCount(null);
      setSampleRecipients([]);
      fetchCampaigns();
    } catch (error) {
      console.error('Error creating campaign:', error);
      toast({
        title: "Failed to create campaign",
        description: "Please try again.",
        variant: "destructive"
      });
    }
  };

  // Start campaign
  const handleStartCampaign = async (campaignId: string) => {
    try {
      await api.post(`/sms-campaigns/${campaignId}/start`);
      toast({
        title: "Campaign started",
        description: "Your SMS campaign is now running."
      });
      fetchCampaigns();
    } catch (error) {
      console.error('Error starting campaign:', error);
      toast({
        title: "Failed to start campaign",
        description: "Please try again.",
        variant: "destructive"
      });
    }
  };

  // Duplicate campaign (for completed/failed campaigns)
  const handleDuplicateCampaignAction = async (campaignId: string) => {
    try {
      const response = await api.post<SMSCampaign>(`/sms-campaigns/${campaignId}/duplicate`);
      toast({
        title: "Campaign duplicated",
        description: `"${response.name}" is ready to send.`
      });
      fetchCampaigns();
    } catch (error) {
      console.error('Error duplicating campaign:', error);
      toast({
        title: "Failed to duplicate campaign",
        description: "Please try again.",
        variant: "destructive"
      });
    }
  };

  // Pause campaign
  const handlePauseCampaign = async (campaignId: string) => {
    try {
      await api.post(`/sms-campaigns/${campaignId}/pause`);
      toast({
        title: "Campaign paused",
        description: "Your SMS campaign has been paused."
      });
      fetchCampaigns();
    } catch (error) {
      console.error('Error pausing campaign:', error);
      toast({
        title: "Failed to pause campaign",
        variant: "destructive"
      });
    }
  };

  // Cancel campaign
  const handleCancelCampaign = async (campaignId: string) => {
    try {
      await api.post(`/sms-campaigns/${campaignId}/cancel`);
      toast({
        title: "Campaign cancelled",
        description: "Your SMS campaign has been cancelled."
      });
      fetchCampaigns();
    } catch (error) {
      console.error('Error cancelling campaign:', error);
      toast({
        title: "Failed to cancel campaign",
        variant: "destructive"
      });
    }
  };

  // Retry failed messages
  const handleRetryFailedMessages = async (campaignId: string) => {
    try {
      const response = await api.post<{ success: boolean; retried_count: number; message: string }>(
        `/sms-campaigns/${campaignId}/retry-failed`
      );

      toast({
        title: "Failed messages retried",
        description: response.retried_count > 0
          ? `${response.retried_count} failed message(s) have been reset to pending and will be retried when you resume the campaign.`
          : "No failed messages found to retry.",
      });

      fetchCampaigns();

      // Refresh selected campaign if in details view
      if (selectedCampaign && selectedCampaign.id === campaignId) {
        const updatedCampaign = await api.get<SMSCampaign>(`/sms-campaigns/${campaignId}`);
        setSelectedCampaign(updatedCampaign);
      }
    } catch (error) {
      console.error('Error retrying failed messages:', error);
      toast({
        title: "Failed to retry messages",
        description: "Please try again later.",
        variant: "destructive"
      });
    }
  };

  // Delete campaign
  const handleDeleteCampaign = async (campaignId: string) => {
    try {
      await api.delete(`/sms-campaigns/${campaignId}`);
      toast({
        title: "Campaign deleted",
        description: "Your SMS campaign has been deleted."
      });
      fetchCampaigns();
    } catch (error) {
      console.error('Error deleting campaign:', error);
      toast({
        title: "Failed to delete campaign",
        variant: "destructive"
      });
    }
  };

  // Edit campaign - open dialog with pre-filled data
  const handleEditCampaign = (campaign: SMSCampaign) => {
    setEditCampaignId(campaign.id);
    setFormData({
      name: campaign.name,
      template_content: campaign.template_content,
      audience_id: campaign.audience_id || '',
      sender_id: campaign.config.sender_id || 'IMPACT2025',
      send_rate: campaign.config.send_rate_per_second?.toString() || '1',
      sms_provider: campaign.sms_provider,
      excluded_phone_numbers: (campaign as any).excluded_phone_numbers?.join('\n') || ''
    });
    setShowEditDialog(true);
  };

  // Duplicate campaign - open create dialog with pre-filled data
  const handleDuplicateCampaign = (campaign: SMSCampaign) => {
    setFormData({
      name: `${campaign.name} (Copy)`,
      template_content: campaign.template_content,
      audience_id: campaign.audience_id || '',
      sender_id: campaign.config.sender_id || 'IMPACT2025',
      send_rate: campaign.config.send_rate_per_second?.toString() || '1',
      sms_provider: campaign.sms_provider,
      excluded_phone_numbers: (campaign as any).excluded_phone_numbers?.join('\n') || ''
    });
    setShowCreateDialog(true);
    toast({
      title: "Campaign duplicated",
      description: "Pre-filled with original campaign data. Click 'Create Campaign' to save."
    });
  };

  // Update campaign
  const handleUpdateCampaign = async () => {
    if (!formData.name || !formData.template_content) {
      toast({
        title: "Missing required fields",
        description: "Please fill in campaign name and message template.",
        variant: "destructive"
      });
      return;
    }

    try {
      // Parse excluded phone numbers
      const excludedNumbers = formData.excluded_phone_numbers
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);

      const payload = {
        name: formData.name,
        template_content: formData.template_content,
        audience_id: formData.audience_id || null,
        excluded_phone_numbers: excludedNumbers.length > 0 ? excludedNumbers : [],
        config: {
          send_rate_per_second: parseFloat(formData.send_rate),
          sender_id: formData.sender_id || null
        }
      };

      await api.put(`/sms-campaigns/${editCampaignId}`, payload);

      // Re-prepare messages after update
      try {
        await api.post(`/sms-campaigns/${editCampaignId}/prepare`);
        toast({
          title: "Campaign updated",
          description: "Your SMS campaign has been updated and messages are re-prepared."
        });
      } catch (prepareError) {
        console.error('Error preparing messages:', prepareError);
        toast({
          title: "Campaign updated",
          description: "Campaign updated but message preparation failed. You can retry from the campaign details.",
          variant: "default"
        });
      }

      setShowEditDialog(false);
      setFormData({
        name: '',
        template_content: '',
        audience_id: '',
        sender_id: '',
        send_rate: '1',
        sms_provider: 'hubtel'
      });
      setEditCampaignId('');
      setTemplatePreview(null);
      fetchCampaigns();
    } catch (error) {
      console.error('Error updating campaign:', error);
      toast({
        title: "Failed to update campaign",
        description: "Please try again.",
        variant: "destructive"
      });
    }
  };

  // Status badge
  const getStatusBadge = (status: string | undefined) => {
    // Defensive: handle undefined or null status
    const safeStatus = status || 'draft';

    const statusConfig: Record<string, { color: string; icon: React.ReactNode }> = {
      draft: { color: 'bg-gray-100 text-gray-800', icon: <Edit className="h-3 w-3" /> },
      scheduled: { color: 'bg-blue-100 text-blue-800', icon: <Clock className="h-3 w-3" /> },
      running: { color: 'bg-green-100 text-green-800', icon: <Play className="h-3 w-3" /> },
      paused: { color: 'bg-yellow-100 text-yellow-800', icon: <Pause className="h-3 w-3" /> },
      completed: { color: 'bg-emerald-100 text-emerald-800', icon: <CheckCircle2 className="h-3 w-3" /> },
      failed: { color: 'bg-red-100 text-red-800', icon: <AlertCircle className="h-3 w-3" /> },
      cancelled: { color: 'bg-gray-100 text-gray-800', icon: <XCircle className="h-3 w-3" /> }
    };

    const config = statusConfig[safeStatus] || statusConfig.draft;
    return (
      <Badge className={`${config.color} gap-1`}>
        {config.icon}
        {safeStatus.charAt(0).toUpperCase() + safeStatus.slice(1)}
      </Badge>
    );
  };

  const getAudienceName = (audienceId: string | null) => {
    if (!audienceId) return 'No audience';
    const audience = audiences.find(a => a.id === audienceId);
    return audience ? audience.name : 'Unknown';
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-background">
        <DashboardSidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-gray-600">Loading SMS campaigns...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-background">
      <DashboardSidebar />

      <div className="flex-1 overflow-auto">
        <div className="container mx-auto p-6 pb-12 max-w-7xl">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">SMS Campaigns</h1>
              <p className="text-gray-600">
                Create and manage bulk SMS campaigns with audience targeting
              </p>
            </div>

            <Button
              className="gap-2"
              onClick={() => setShowCreateDialog(true)}
            >
              <Plus className="h-4 w-4" />
              Create Campaign
            </Button>
          </div>

          {/* Stats Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Campaigns</CardTitle>
                <MessageSquare className="h-4 w-4 text-gray-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_campaigns}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Campaigns</CardTitle>
                <Play className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.active_campaigns}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Messages Sent</CardTitle>
                <Send className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_messages_sent.toLocaleString()}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
                <BarChart3 className="h-4 w-4 text-purple-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">${stats.total_cost.toFixed(2)}</div>
              </CardContent>
            </Card>
          </div>

          {/* Search and Filters */}
          <div className="flex items-center gap-4 mb-6">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-600 h-4 w-4" />
              <Input
                placeholder="Search campaigns..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="running">Running</SelectItem>
                <SelectItem value="paused">Paused</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={fetchCampaigns}>
              <RefreshCw className="h-4 w-4" />
            </Button>
            {activeConnections > 0 && (
              <div className="flex items-center gap-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>{activeConnections} live update{activeConnections > 1 ? 's' : ''}</span>
              </div>
            )}
          </div>

          {/* Campaigns Table */}
          {filteredCampaigns.length === 0 ? (
            <Card className="p-8 text-center">
              <div className="mx-auto w-12 h-12 bg-muted rounded-lg flex items-center justify-center mb-4">
                <MessageSquare className="h-6 w-6 text-gray-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">No SMS campaigns yet</h3>
              <p className="text-gray-600 mb-4">
                Create your first SMS campaign to start reaching your audience.
              </p>
              <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
                <Plus className="h-4 w-4" />
                Create First Campaign
              </Button>
            </Card>
          ) : (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Campaign</TableHead>
                    <TableHead>Audience</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Progress</TableHead>
                    <TableHead>Sent</TableHead>
                    <TableHead>Cost</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredCampaigns.map((campaign) => (
                    <TableRow
                      key={campaign.id}
                      className="cursor-pointer hover:bg-gray-50"
                      onClick={() => {
                        setSelectedCampaign(campaign);
                        setShowDetailsDialog(true);
                      }}
                    >
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <MessageSquare className="h-4 w-4 text-indigo-600" />
                          <div>
                            <div className="font-medium">{campaign.name}</div>
                            <div className="text-xs text-gray-500 truncate max-w-[200px]">
                              {campaign.template_content.substring(0, 50)}...
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1.5">
                          <Users className="h-3.5 w-3.5 text-gray-400" />
                          <span className="text-sm text-gray-700">{getAudienceName(campaign.audience_id)}</span>
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(campaign.status)}</TableCell>
                      <TableCell>
                        <div className="w-24">
                          <Progress
                            value={(campaign.progress?.total_recipients || 0) > 0
                              ? (((campaign.progress?.sent || 0) + (campaign.progress?.failed || 0)) / (campaign.progress?.total_recipients || 1)) * 100
                              : 0
                            }
                            className="h-2"
                          />
                          <span className="text-xs text-gray-500">
                            {campaign.progress?.sent || 0}/{campaign.progress?.total_recipients || 0}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <span className="text-green-600">{campaign.progress?.sent || 0}</span>
                          {(campaign.progress?.failed || 0) > 0 && (
                            <span className="text-red-600 ml-1">({campaign.progress?.failed || 0} failed)</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>${campaign.total_cost.toFixed(2)}</TableCell>
                      <TableCell className="text-sm text-gray-600">
                        {new Date(campaign.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-end gap-2">
                          {/* Edit button - only show for draft and paused */}
                          {['draft', 'paused'].includes(campaign.status) && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEditCampaign(campaign);
                              }}
                              className="bg-blue-50 text-blue-600 border-blue-200 hover:bg-blue-100"
                              title="Edit campaign"
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          )}

                          {campaign.status === 'draft' && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleStartCampaign(campaign.id);
                              }}
                              className="bg-green-50 text-green-600 border-green-200 hover:bg-green-100"
                              title="Start campaign"
                            >
                              <Play className="h-4 w-4" />
                            </Button>
                          )}

                          {campaign.status === 'running' && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handlePauseCampaign(campaign.id);
                              }}
                              className="bg-yellow-50 text-yellow-600 border-yellow-200 hover:bg-yellow-100"
                              title="Pause campaign"
                            >
                              <Pause className="h-4 w-4" />
                            </Button>
                          )}

                          {campaign.status === 'paused' && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleStartCampaign(campaign.id);
                              }}
                              className="bg-green-50 text-green-600 border-green-200 hover:bg-green-100"
                              title="Resume campaign"
                            >
                              <Play className="h-4 w-4" />
                            </Button>
                          )}

                          {/* Retry Failed Messages Button */}
                          {(campaign.progress?.failed || 0) > 0 && ['draft', 'paused', 'completed', 'failed'].includes(campaign.status) && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleRetryFailedMessages(campaign.id);
                              }}
                              className="bg-orange-50 text-orange-600 border-orange-200 hover:bg-orange-100"
                              title={`Retry ${campaign.progress.failed} failed message(s)`}
                            >
                              <RefreshCw className="h-4 w-4" />
                            </Button>
                          )}

                          {/* Run Again Button - Completed/Failed/Cancelled */}
                          {['completed', 'failed', 'cancelled'].includes(campaign.status) && (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={async (e) => {
                                  e.stopPropagation();
                                  // Restart the campaign (archives old messages, resets, re-prepares, and starts)
                                  try {
                                    await api.post(`/sms-campaigns/${campaign.id}/restart`);
                                    toast({ title: 'Campaign restarted successfully!' });
                                    fetchCampaigns(); // Refresh the list
                                  } catch (error: any) {
                                    const errorMessage = error?.message || 'Unknown error occurred';
                                    let description = errorMessage;

                                    // Add helpful guidance based on error type
                                    if (errorMessage.toLowerCase().includes('draft')) {
                                      description += '\n\n💡 Tip: Use "Edit Campaign" to configure the campaign, then "Start Campaign" instead.';
                                    } else if (errorMessage.toLowerCase().includes('no contacts') || errorMessage.toLowerCase().includes('audience has no contacts')) {
                                      description += '\n\n💡 Tip: Add contacts to the audience before restarting.';
                                    } else if (errorMessage.toLowerCase().includes('no audience')) {
                                      description += '\n\n💡 Tip: Edit the campaign to select an audience.';
                                    }

                                    toast({
                                      title: 'Failed to restart campaign',
                                      description: description,
                                      variant: 'destructive',
                                      duration: 7000  // Longer duration for actionable messages
                                    });
                                    console.error('Error restarting campaign:', error);
                                  }
                                }}
                                className="bg-green-50 text-green-600 border-green-200 hover:bg-green-100"
                                title="Run again (Duplicate & Start)"
                              >
                                <Play className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDuplicateCampaignAction(campaign.id);
                                }}
                                className="bg-purple-50 text-purple-600 border-purple-200 hover:bg-purple-100"
                                title="Duplicate campaign (Edit before sending)"
                              >
                                <Copy className="h-4 w-4" />
                              </Button>
                            </>
                          )}

                          {/* Start Button for DRAFT campaigns with prepared messages */}
                          {campaign.status === 'draft' && (campaign.progress?.total_recipients || 0) > 0 && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleStartCampaign(campaign.id);
                              }}
                              className="bg-green-50 text-green-600 border-green-200 hover:bg-green-100"
                              title="Start campaign"
                            >
                              <Play className="h-4 w-4" />
                            </Button>
                          )}

                          {/* Edit Button for DRAFT campaigns */}
                          {campaign.status === 'draft' && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEditCampaign(campaign);
                              }}
                              className="bg-blue-50 text-blue-600 border-blue-200 hover:bg-blue-100"
                              title="Edit campaign"
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          )}

                          {/* Delete Button for DRAFT/PAUSED campaigns */}
                          {['draft', 'paused'].includes(campaign.status) && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteCampaign(campaign.id);
                              }}
                              className="bg-red-50 text-red-600 border-red-200 hover:bg-red-100"
                              title="Delete campaign"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </div>

        {/* Create Campaign Dialog */}
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Create SMS Campaign
              </DialogTitle>
              <DialogDescription>
                Create a new bulk SMS campaign with message templates
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              {/* Campaign Name */}
              <div className="space-y-2">
                <Label htmlFor="name">Campaign Name *</Label>
                <Input
                  id="name"
                  placeholder="e.g., Black Friday Sale"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>

              {/* Audience Selection */}
              <div className="space-y-2">
                <Label htmlFor="audience">Select Audience</Label>
                <Select
                  value={formData.audience_id}
                  onValueChange={(value) => setFormData({ ...formData, audience_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose an audience (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    {audiences.map((audience) => (
                      <SelectItem key={audience.id} value={audience.id}>
                        <div className="flex items-center gap-2">
                          <Users className="h-4 w-4" />
                          {audience.name} ({audience.size} contacts)
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500">
                  Or you can upload contacts when starting the campaign
                </p>
              </div>

              {/* Message Template */}
              <div className="space-y-2">
                <Label htmlFor="template">Message Template *</Label>
                <Textarea
                  id="template"
                  placeholder="Hello {{name}}, your appointment is confirmed for tomorrow. Reply STOP to unsubscribe."
                  value={formData.template_content}
                  onChange={(e) => setFormData({ ...formData, template_content: e.target.value })}
                  rows={4}
                />
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <p className="text-xs text-gray-500">
                      Use {'{{placeholder}}'} for dynamic content. E.g., {'{{name}}'}, {'{{phone}}'}
                    </p>
                    <p className="text-xs font-medium text-gray-700">
                      {formData.template_content.length}/160 ({Math.ceil(formData.template_content.length / 160) || 1} SMS)
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={previewTemplate}
                    disabled={previewLoading}
                  >
                    {previewLoading ? 'Loading...' : 'Preview'}
                  </Button>
                </div>
              </div>

              {/* Template Preview */}
              {templatePreview && (
                <Card className="bg-gray-50">
                  <CardContent className="pt-4">
                    <h4 className="font-medium mb-2">Preview</h4>
                    <p className="text-sm mb-2">{templatePreview.rendered_content}</p>
                    <div className="flex gap-4 text-xs text-gray-500">
                      <span>Characters: {templatePreview.character_count}</span>
                      <span>SMS Segments: {templatePreview.segment_count}</span>
                      <span>Placeholders: {templatePreview.placeholders.join(', ') || 'None'}</span>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Advanced Settings */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="sender_id">Sender ID</Label>
                  <Select
                    value={formData.sender_id}
                    onValueChange={(value) => setFormData({ ...formData, sender_id: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="IMPACT2025">IMPACT2025 (Default)</SelectItem>
                      <SelectItem value="CHURCHFLOW">CHURCHFLOW</SelectItem>
                      <SelectItem value="REVIVAL25">REVIVAL25</SelectItem>
                      <SelectItem value="AWAKENING">AWAKENING</SelectItem>
                      <SelectItem value="KASAAI">KASAAI</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    Alphanumeric sender ID (max 11 chars). Must be registered with Arkesel.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="send_rate">Send Rate (msg/sec)</Label>
                  <Select
                    value={formData.send_rate}
                    onValueChange={(value) => setFormData({ ...formData, send_rate: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="0.5">0.5/sec (Slow)</SelectItem>
                      <SelectItem value="1">1/sec (Normal)</SelectItem>
                      <SelectItem value="2">2/sec (Fast)</SelectItem>
                      <SelectItem value="5">5/sec (Very Fast)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* SMS Provider */}
              <div className="space-y-2">
                <Label htmlFor="provider">SMS Provider</Label>
                <Select
                  value={formData.sms_provider}
                  onValueChange={(value) => setFormData({ ...formData, sms_provider: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="arkesel">Arkesel (Ghana) - Default</SelectItem>
                    <SelectItem value="hubtel">Hubtel (Ghana)</SelectItem>
                    <SelectItem value="custom_http">Custom HTTP/API</SelectItem>
                    <SelectItem value="twilio">Twilio</SelectItem>
                    <SelectItem value="messagebird">MessageBird</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Arkesel is the default recommended provider for Ghana. Supports alphanumeric sender IDs.
                </p>
              </div>
            </div>

            {/* Recipient Preview Section */}
            {formData.audience_id && (
              <Card className="bg-blue-50 border-blue-200">
                <CardContent className="pt-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium text-sm">Recipient Preview</h4>
                      {fetchingCount ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      ) : (
                        <span className="text-lg font-bold text-blue-600">
                          {recipientCount !== null ? recipientCount : 0} recipients
                        </span>
                      )}
                    </div>

                    {sampleRecipients.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs text-gray-600 mb-1">Sample recipients:</p>
                        <div className="space-y-1">
                          {sampleRecipients.map((recipient, idx) => (
                            <div key={idx} className="text-xs flex items-center gap-2 bg-white px-2 py-1 rounded">
                              <Users className="h-3 w-3 text-gray-400" />
                              <span className="font-medium">{recipient.name}</span>
                              <span className="text-gray-500">•</span>
                              <span className="text-gray-600 font-mono">{recipient.phone}</span>
                            </div>
                          ))}
                        </div>
                        {recipientCount && recipientCount > 5 && (
                          <Button
                            variant="link"
                            size="sm"
                            onClick={fetchAllRecipients}
                            disabled={loadingAllRecipients}
                            className="mt-1 h-auto p-0 text-blue-600"
                          >
                            {loadingAllRecipients ? 'Loading...' : `View all ${recipientCount} recipients`}
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Phone Number Exclusion */}
            <div className="space-y-2">
              <Label htmlFor="excluded">Exclude Phone Numbers (Optional)</Label>
              <Textarea
                id="excluded"
                placeholder="+233244123456&#10;+233501234567&#10;One per line"
                value={formData.excluded_phone_numbers}
                onChange={(e) => setFormData({ ...formData, excluded_phone_numbers: e.target.value })}
                rows={3}
              />
              <p className="text-xs text-muted-foreground">
                Enter phone numbers to exclude from this campaign (one per line). Useful for opt-outs or testing.
              </p>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateCampaign}>
                Create Campaign
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit Campaign Dialog */}
        <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Edit className="h-5 w-5" />
                Edit SMS Campaign
              </DialogTitle>
              <DialogDescription>
                Update your SMS campaign details and message template
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              {/* Campaign Name */}
              <div className="space-y-2">
                <Label htmlFor="edit-name">Campaign Name *</Label>
                <Input
                  id="edit-name"
                  placeholder="e.g., Black Friday Sale"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>

              {/* Audience Selection */}
              <div className="space-y-2">
                <Label htmlFor="edit-audience">Select Audience</Label>
                <Select
                  value={formData.audience_id}
                  onValueChange={(value) => setFormData({ ...formData, audience_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose an audience (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    {audiences.map((audience) => (
                      <SelectItem key={audience.id} value={audience.id}>
                        <div className="flex items-center gap-2">
                          <Users className="h-4 w-4" />
                          {audience.name} ({audience.size} contacts)
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Message Template */}
              <div className="space-y-2">
                <Label htmlFor="edit-template">Message Template *</Label>
                <Textarea
                  id="edit-template"
                  placeholder="Hello {{name}}, your appointment is confirmed for tomorrow. Reply STOP to unsubscribe."
                  value={formData.template_content}
                  onChange={(e) => setFormData({ ...formData, template_content: e.target.value })}
                  rows={4}
                />
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <p className="text-xs text-gray-500">
                      Use {'{{placeholder}}'} for dynamic content. E.g., {'{{name}}'}, {'{{phone}}'}
                    </p>
                    <p className="text-xs font-medium text-gray-700">
                      {formData.template_content.length}/160 ({Math.ceil(formData.template_content.length / 160) || 1} SMS)
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={previewTemplate}
                    disabled={previewLoading}
                  >
                    {previewLoading ? 'Loading...' : 'Preview'}
                  </Button>
                </div>
              </div>

              {/* Template Preview */}
              {templatePreview && (
                <Card className="bg-gray-50">
                  <CardContent className="pt-4">
                    <h4 className="font-medium mb-2">Preview</h4>
                    <p className="text-sm mb-2">{templatePreview.rendered_content}</p>
                    <div className="flex gap-4 text-xs text-gray-500">
                      <span>Characters: {templatePreview.character_count}</span>
                      <span>SMS Segments: {templatePreview.segment_count}</span>
                      <span>Placeholders: {templatePreview.placeholders.join(', ') || 'None'}</span>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Advanced Settings */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-sender_id">Sender ID (optional)</Label>
                  <Input
                    id="edit-sender_id"
                    placeholder="e.g., +12025551234"
                    value={formData.sender_id}
                    onChange={(e) => setFormData({ ...formData, sender_id: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="edit-send_rate">Send Rate (msg/sec)</Label>
                  <Select
                    value={formData.send_rate}
                    onValueChange={(value) => setFormData({ ...formData, send_rate: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="0.5">0.5/sec (Slow)</SelectItem>
                      <SelectItem value="1">1/sec (Normal)</SelectItem>
                      <SelectItem value="2">2/sec (Fast)</SelectItem>
                      <SelectItem value="5">5/sec (Very Fast)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => {
                setShowEditDialog(false);
                setFormData({
                  name: '',
                  template_content: '',
                  audience_id: '',
                  sender_id: '',
                  send_rate: '1',
                  sms_provider: 'hubtel'
                });
                setEditCampaignId('');
                setTemplatePreview(null);
              }}>
                Cancel
              </Button>
              <Button onClick={handleUpdateCampaign}>
                Update Campaign
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Campaign Details Dialog - Professional Modal */}
        {showDetailsDialog && selectedCampaign && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">

              {/* Header - Gradient */}
              <div className="p-6 border-b bg-gradient-to-r from-purple-600 via-indigo-600 to-pink-600">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <MessageSquare className="h-6 w-6 text-white" />
                    <div>
                      <h2 className="text-xl font-bold text-white">{selectedCampaign.name}</h2>
                      <p className="text-purple-100 text-sm">Campaign Analytics & Details</p>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setShowDetailsDialog(false);
                      setSelectedCampaign(null);
                    }}
                    className="text-white hover:text-gray-200 transition-colors p-1 rounded-lg hover:bg-white/10"
                  >
                    <X className="h-6 w-6" />
                  </button>
                </div>
              </div>

              {/* Content Area - Scrollable */}
              <div className="flex-1 overflow-y-auto p-6">
                <Tabs defaultValue="overview" className="w-full">
                  <TabsList className="grid w-full grid-cols-5 mb-6">
                    <TabsTrigger value="overview" className="gap-2">
                      <BarChart3 className="h-4 w-4" />
                      Overview
                    </TabsTrigger>
                    <TabsTrigger value="history" className="gap-2">
                      <Clock className="h-4 w-4" />
                      History
                    </TabsTrigger>
                    <TabsTrigger value="successful" onClick={() => fetchMessages(selectedCampaign.id, 1, 'sent')} className="gap-2">
                      <CheckCircle2 className="h-4 w-4" />
                      <span className="hidden sm:inline">Successful</span>
                      <Badge variant="secondary" className="ml-1">{selectedCampaign.progress?.sent || 0}</Badge>
                    </TabsTrigger>
                    <TabsTrigger value="failed" onClick={() => fetchMessages(selectedCampaign.id, 1, 'failed')} className="gap-2">
                      <AlertCircle className="h-4 w-4" />
                      <span className="hidden sm:inline">Failed</span>
                      <Badge variant="secondary" className="ml-1">{selectedCampaign.progress?.failed || 0}</Badge>
                    </TabsTrigger>
                    <TabsTrigger value="all" onClick={() => fetchMessages(selectedCampaign.id, 1)} className="gap-2">
                      <MessageSquare className="h-4 w-4" />
                      <span className="hidden sm:inline">All</span>
                      <Badge variant="secondary" className="ml-1">{selectedCampaign.progress?.total_recipients || 0}</Badge>
                    </TabsTrigger>
                  </TabsList>

                  {/* Overview Tab */}
                  <TabsContent value="overview" className="space-y-6">
                  {/* Status and Progress */}
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-600">Status</label>
                      <div className="mt-1">{getStatusBadge(selectedCampaign.status)}</div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Provider</label>
                      <div className="mt-1 capitalize">{selectedCampaign.sms_provider}</div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Audience</label>
                      <div className="mt-1 flex items-center gap-1.5">
                        <Users className="h-3.5 w-3.5 text-gray-400" />
                        <span className="text-sm text-gray-700">{getAudienceName(selectedCampaign.audience_id)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div>
                    <label className="text-sm font-medium text-gray-600">Progress</label>
                    <Progress
                      value={(selectedCampaign.progress?.total_recipients || 0) > 0
                        ? (((selectedCampaign.progress?.sent || 0) + (selectedCampaign.progress?.failed || 0)) / (selectedCampaign.progress?.total_recipients || 1)) * 100
                        : 0
                      }
                      className="h-3 mt-2"
                    />
                    <div className="grid grid-cols-4 gap-2 mt-2 text-sm">
                      <div className="text-center">
                        <div className="font-semibold">{selectedCampaign.progress?.total_recipients || 0}</div>
                        <div className="text-gray-500">Total</div>
                      </div>
                      <div className="text-center">
                        <div className="font-semibold text-green-600">{selectedCampaign.progress?.sent || 0}</div>
                        <div className="text-gray-500">Sent</div>
                      </div>
                      <div className="text-center">
                        <div className="font-semibold text-red-600">{selectedCampaign.progress?.failed || 0}</div>
                        <div className="text-gray-500">Failed</div>
                      </div>
                      <div className="text-center">
                        <div className="font-semibold text-yellow-600">{selectedCampaign.progress?.pending || 0}</div>
                        <div className="text-gray-500">Pending</div>
                      </div>
                    </div>
                  </div>

                  {/* Message Template */}
                  <div>
                    <label className="text-sm font-medium text-gray-600">Message Template</label>
                    <Card className="mt-2 bg-gray-50">
                      <CardContent className="pt-4">
                        <p className="text-sm whitespace-pre-wrap">{selectedCampaign.template_content}</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Cost and Timing */}
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-600">Total Cost</label>
                      <div className="text-lg font-semibold mt-1">${selectedCampaign.total_cost.toFixed(2)}</div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Created</label>
                      <div className="mt-1">{new Date(selectedCampaign.created_at).toLocaleString()}</div>
                    </div>
                    {selectedCampaign.started_at && (
                      <div>
                        <label className="text-sm font-medium text-gray-600">Started</label>
                        <div className="mt-1">{new Date(selectedCampaign.started_at).toLocaleString()}</div>
                      </div>
                    )}
                  </div>

                  {/* Error Message */}
                  {selectedCampaign.error_message && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                      <div className="flex items-center gap-2 text-red-600">
                        <AlertCircle className="h-4 w-4" />
                        <span className="font-medium">Error</span>
                      </div>
                      <p className="text-sm text-red-600 mt-1">{selectedCampaign.error_message}</p>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2">
                    {selectedCampaign.status === 'draft' && (
                      <Button onClick={() => handleStartCampaign(selectedCampaign.id)} className="gap-2">
                        <Play className="h-4 w-4" />
                        Start Campaign
                      </Button>
                    )}
                    {selectedCampaign.status === 'running' && (
                      <Button onClick={() => handlePauseCampaign(selectedCampaign.id)} variant="outline" className="gap-2">
                        <Pause className="h-4 w-4" />
                        Pause
                      </Button>
                    )}
                    {selectedCampaign.status === 'paused' && (
                      <Button onClick={() => handleStartCampaign(selectedCampaign.id)} className="gap-2">
                        <Play className="h-4 w-4" />
                        Resume
                      </Button>
                    )}
                    {['running', 'paused'].includes(selectedCampaign.status) && (
                      <Button onClick={() => handleCancelCampaign(selectedCampaign.id)} variant="destructive" className="gap-2">
                        <XCircle className="h-4 w-4" />
                        Cancel
                      </Button>
                    )}
                  </div>
                </TabsContent>

                {/* History Tab - Cumulative Metrics */}
                <TabsContent value="history" className="space-y-6">
                  <div className="space-y-6">
                    {/* Cumulative Stats Header */}
                    <div className="text-center pb-4 border-b">
                      <h3 className="text-lg font-semibold text-gray-900">Campaign History</h3>
                      <p className="text-sm text-gray-500 mt-1">Cumulative metrics across all runs</p>
                    </div>

                    {/* Current Run vs All-Time Comparison */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Current Run Card */}
                      <Card className="border-2 border-blue-200 bg-blue-50">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-base flex items-center gap-2 text-blue-900">
                            <BarChart3 className="h-4 w-4" />
                            Current Run
                          </CardTitle>
                          <CardDescription className="text-blue-700">
                            This execution only
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <div>
                            <div className="text-sm text-blue-700 mb-1">Messages Sent</div>
                            <div className="text-2xl font-bold text-blue-900">{(selectedCampaign.progress?.sent || 0).toLocaleString()}</div>
                          </div>
                          <div>
                            <div className="text-sm text-blue-700 mb-1">Total Cost</div>
                            <div className="text-2xl font-bold text-blue-900">${selectedCampaign.total_cost.toFixed(2)}</div>
                          </div>
                          <div className="pt-2 border-t border-blue-200">
                            <div className="text-xs text-blue-600">
                              Success Rate: {(selectedCampaign.progress?.sent || 0) > 0
                                ? (((selectedCampaign.progress?.sent || 0) / ((selectedCampaign.progress?.sent || 0) + (selectedCampaign.progress?.failed || 0))) * 100).toFixed(1)
                                : 0}%
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      {/* All-Time Card */}
                      <Card className="border-2 border-purple-200 bg-purple-50">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-base flex items-center gap-2 text-purple-900">
                            <Clock className="h-4 w-4" />
                            All-Time Total
                          </CardTitle>
                          <CardDescription className="text-purple-700">
                            Across {selectedCampaign.total_runs || 0} run{selectedCampaign.total_runs !== 1 ? 's' : ''}
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <div>
                            <div className="text-sm text-purple-700 mb-1">Total Messages Sent</div>
                            <div className="text-2xl font-bold text-purple-900">{(selectedCampaign.total_messages_sent_all_time || 0).toLocaleString()}</div>
                          </div>
                          <div>
                            <div className="text-sm text-purple-700 mb-1">Total Cost</div>
                            <div className="text-2xl font-bold text-purple-900">${(selectedCampaign.total_cost_all_time || 0).toFixed(2)}</div>
                          </div>
                          <div className="pt-2 border-t border-purple-200">
                            <div className="text-xs text-purple-600">
                              Avg Cost per Message: ${selectedCampaign.total_messages_sent_all_time > 0
                                ? (selectedCampaign.total_cost_all_time / selectedCampaign.total_messages_sent_all_time).toFixed(4)
                                : '0.0000'}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>

                    {/* Run Statistics */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Run Statistics</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-3 gap-4 text-center">
                          <div className="p-4 bg-gray-50 rounded-lg">
                            <div className="text-2xl font-bold text-gray-900">{selectedCampaign.total_runs || 0}</div>
                            <div className="text-sm text-gray-600 mt-1">Total Runs</div>
                          </div>
                          <div className="p-4 bg-gray-50 rounded-lg">
                            <div className="text-2xl font-bold text-gray-900">
                              {selectedCampaign.total_runs > 0
                                ? Math.round((selectedCampaign.total_messages_sent_all_time || 0) / selectedCampaign.total_runs).toLocaleString()
                                : 0}
                            </div>
                            <div className="text-sm text-gray-600 mt-1">Avg Messages/Run</div>
                          </div>
                          <div className="p-4 bg-gray-50 rounded-lg">
                            <div className="text-2xl font-bold text-gray-900">
                              ${selectedCampaign.total_runs > 0
                                ? ((selectedCampaign.total_cost_all_time || 0) / selectedCampaign.total_runs).toFixed(2)
                                : '0.00'}
                            </div>
                            <div className="text-sm text-gray-600 mt-1">Avg Cost/Run</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Timeline Info */}
                    <Card className="bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200">
                      <CardContent className="pt-6">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <div className="text-gray-600 mb-1">Campaign Created</div>
                            <div className="font-medium text-gray-900">{new Date(selectedCampaign.created_at).toLocaleDateString()}</div>
                          </div>
                          <div>
                            <div className="text-gray-600 mb-1">Last Updated</div>
                            <div className="font-medium text-gray-900">{new Date(selectedCampaign.updated_at).toLocaleDateString()}</div>
                          </div>
                          {selectedCampaign.started_at && (
                            <div>
                              <div className="text-gray-600 mb-1">Last Started</div>
                              <div className="font-medium text-gray-900">{new Date(selectedCampaign.started_at).toLocaleString()}</div>
                            </div>
                          )}
                          {selectedCampaign.completed_at && (
                            <div>
                              <div className="text-gray-600 mb-1">Last Completed</div>
                              <div className="font-medium text-gray-900">{new Date(selectedCampaign.completed_at).toLocaleString()}</div>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>

                    {/* Info Note */}
                    {selectedCampaign.total_runs === 0 && (
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="flex items-start gap-3">
                          <Clock className="h-5 w-5 text-blue-600 mt-0.5" />
                          <div>
                            <div className="font-medium text-blue-900">No History Yet</div>
                            <p className="text-sm text-blue-700 mt-1">
                              This campaign hasn't been run yet. Historical metrics will appear here after the first successful run.
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </TabsContent>

                {/* Successful Messages Tab */}
                <TabsContent value="successful" className="space-y-4 mt-4">
                  {messagesLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                  ) : messages.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <CheckCircle2 className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                      <p>No successful messages</p>
                    </div>
                  ) : (
                    <Card>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Recipient</TableHead>
                            <TableHead>Phone</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Sent At</TableHead>
                            <TableHead>Cost</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {messages.map((message, idx) => (
                            <TableRow key={message.id || idx}>
                              <TableCell>{message.recipient_name || 'Unknown'}</TableCell>
                              <TableCell className="font-mono text-xs">{message.recipient_phone}</TableCell>
                              <TableCell>
                                <Badge className="bg-green-100 text-green-800">
                                  {message.status}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-xs">
                                {message.sent_at ? new Date(message.sent_at).toLocaleString() : 'N/A'}
                              </TableCell>
                              <TableCell>${(message.cost || 0).toFixed(4)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </Card>
                  )}
                </TabsContent>

                {/* Failed Messages Tab */}
                <TabsContent value="failed" className="space-y-4 mt-4">
                  {messagesLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                  ) : messages.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <AlertCircle className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                      <p>No failed messages</p>
                    </div>
                  ) : (
                    <Card>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Recipient</TableHead>
                            <TableHead>Phone</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Failed At</TableHead>
                            <TableHead>Error Message</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {messages.map((message, idx) => (
                            <TableRow key={message.id || idx}>
                              <TableCell>{message.recipient_name || 'Unknown'}</TableCell>
                              <TableCell className="font-mono text-xs">{message.recipient_phone}</TableCell>
                              <TableCell>
                                <Badge className="bg-red-100 text-red-800">
                                  {message.status}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-xs">
                                {message.failed_at ? new Date(message.failed_at).toLocaleString() : 'N/A'}
                              </TableCell>
                              <TableCell className="max-w-xs truncate text-xs text-red-600">
                                {message.error_message || 'Unknown error'}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </Card>
                  )}
                </TabsContent>

                {/* All Messages Tab */}
                <TabsContent value="all" className="space-y-4 mt-4">
                  {messagesLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                  ) : messages.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <MessageSquare className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                      <p>No messages found</p>
                    </div>
                  ) : (
                    <Card>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Recipient</TableHead>
                            <TableHead>Phone</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Sent/Failed At</TableHead>
                            <TableHead>Cost</TableHead>
                            <TableHead>Error</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {messages.map((message, idx) => (
                            <TableRow key={message.id || idx}>
                              <TableCell>{message.recipient_name || 'Unknown'}</TableCell>
                              <TableCell className="font-mono text-xs">{message.recipient_phone}</TableCell>
                              <TableCell>
                                <Badge className={
                                  message.status === 'sent' || message.status === 'delivered'
                                    ? 'bg-green-100 text-green-800'
                                    : message.status === 'failed'
                                    ? 'bg-red-100 text-red-800'
                                    : 'bg-yellow-100 text-yellow-800'
                                }>
                                  {message.status}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-xs">
                                {message.sent_at ? new Date(message.sent_at).toLocaleString() :
                                 message.failed_at ? new Date(message.failed_at).toLocaleString() : 'N/A'}
                              </TableCell>
                              <TableCell>${(message.cost || 0).toFixed(4)}</TableCell>
                              <TableCell className="max-w-xs truncate text-xs text-red-600">
                                {message.error_message || '-'}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </Card>
                  )}
                </TabsContent>
              </Tabs>
            </div>

            {/* Footer - Action Buttons */}
            <div className="border-t bg-gray-50 px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                {/* Edit Button - Only for Draft and Paused */}
                {['draft', 'paused'].includes(selectedCampaign.status) && (
                  <button
                    onClick={() => {
                      setShowDetailsDialog(false);
                      handleEditCampaign(selectedCampaign);
                    }}
                    className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm"
                  >
                    <Edit className="h-4 w-4" />
                    Edit Campaign
                  </button>
                )}

                {/* Start Button - Draft with messages prepared */}
                {selectedCampaign.status === 'draft' && (selectedCampaign.progress?.total_recipients || 0) > 0 && (
                  <button
                    onClick={() => {
                      setShowDetailsDialog(false);
                      handleStartCampaign(selectedCampaign.id);
                    }}
                    className="flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium shadow-sm"
                  >
                    <Play className="h-4 w-4" />
                    Start Campaign
                  </button>
                )}

                {/* Warning for DRAFT without messages */}
                {selectedCampaign.status === 'draft' && (selectedCampaign.progress?.total_recipients || 0) === 0 && (
                  <div className="flex items-center gap-2 px-4 py-2.5 bg-yellow-50 text-yellow-700 rounded-lg border border-yellow-200">
                    <AlertCircle className="h-4 w-4" />
                    <span className="text-sm">No messages prepared. Edit campaign to add an audience.</span>
                  </div>
                )}

                {/* Pause Button - Running */}
                {selectedCampaign.status === 'running' && (
                  <button
                    onClick={() => {
                      setShowDetailsDialog(false);
                      handlePauseCampaign(selectedCampaign.id);
                    }}
                    className="flex items-center gap-2 px-4 py-2.5 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors font-medium shadow-sm"
                  >
                    <Pause className="h-4 w-4" />
                    Pause Campaign
                  </button>
                )}

                {/* Resume Button - Paused */}
                {selectedCampaign.status === 'paused' && (
                  <button
                    onClick={() => {
                      setShowDetailsDialog(false);
                      handleStartCampaign(selectedCampaign.id);
                    }}
                    className="flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium shadow-sm"
                  >
                    <Play className="h-4 w-4" />
                    Resume Campaign
                  </button>
                )}

                {/* Retry Failed Messages Button */}
                {(selectedCampaign.progress?.failed || 0) > 0 && ['draft', 'paused', 'completed', 'failed'].includes(selectedCampaign.status) && (
                  <button
                    onClick={() => {
                      handleRetryFailedMessages(selectedCampaign.id);
                    }}
                    className="flex items-center gap-2 px-4 py-2.5 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors font-medium shadow-sm"
                    title={`Retry ${selectedCampaign.progress.failed} failed message(s)`}
                  >
                    <RefreshCw className="h-4 w-4" />
                    Retry Failed ({selectedCampaign.progress.failed})
                  </button>
                )}

                {/* Run Again & Duplicate Buttons - Completed/Failed/Cancelled */}
                {['completed', 'failed', 'cancelled'].includes(selectedCampaign.status) && (
                  <>
                    <button
                      onClick={async () => {
                        setShowDetailsDialog(false);
                        // Restart the campaign (archives old messages, resets, re-prepares, and starts)
                        try {
                          await api.post(`/sms-campaigns/${selectedCampaign.id}/restart`);
                          toast({ title: 'Campaign restarted successfully!' });
                          fetchCampaigns(); // Refresh the list
                        } catch (error: any) {
                          const errorMessage = error?.message || 'Unknown error occurred';
                          let description = errorMessage;

                          // Add helpful guidance based on error type
                          if (errorMessage.toLowerCase().includes('draft')) {
                            description += '\n\n💡 Tip: Use "Edit Campaign" to configure the campaign, then "Start Campaign" instead.';
                          } else if (errorMessage.toLowerCase().includes('no contacts') || errorMessage.toLowerCase().includes('audience has no contacts')) {
                            description += '\n\n💡 Tip: Add contacts to the audience before restarting.';
                          } else if (errorMessage.toLowerCase().includes('no audience')) {
                            description += '\n\n💡 Tip: Edit the campaign to select an audience.';
                          }

                          toast({
                            title: 'Failed to restart campaign',
                            description: description,
                            variant: 'destructive',
                            duration: 7000  // Longer duration for actionable messages
                          });
                          console.error('Error restarting campaign:', error);
                        }
                      }}
                      className="flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium shadow-sm"
                    >
                      <Play className="h-4 w-4" />
                      Run Again
                    </button>
                    <button
                      onClick={() => {
                        setShowDetailsDialog(false);
                        handleDuplicateCampaignAction(selectedCampaign.id);
                      }}
                      className="flex items-center gap-2 px-4 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium shadow-sm"
                    >
                      <Copy className="h-4 w-4" />
                      Duplicate & Edit
                    </button>
                  </>
                )}

                {/* Cancel Button - Running/Paused */}
                {['running', 'paused'].includes(selectedCampaign.status) && (
                  <button
                    onClick={() => {
                      setShowDetailsDialog(false);
                      handleCancelCampaign(selectedCampaign.id);
                    }}
                    className="flex items-center gap-2 px-4 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium shadow-sm"
                  >
                    <XCircle className="h-4 w-4" />
                    Cancel Campaign
                  </button>
                )}
              </div>

              {/* Close Button */}
              <button
                onClick={() => {
                  setShowDetailsDialog(false);
                  setSelectedCampaign(null);
                }}
                className="px-6 py-2.5 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
        )}

        {/* View All Recipients Modal */}
        <Dialog open={showAllRecipientsModal} onOpenChange={setShowAllRecipientsModal}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                All Recipients ({allRecipients.length})
              </DialogTitle>
              <DialogDescription>
                Complete list of recipients for this campaign
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-2">
              {allRecipients.map((recipient, idx) => (
                <div key={idx} className="flex items-center gap-3 p-2 bg-gray-50 rounded hover:bg-gray-100">
                  <span className="text-sm font-mono text-gray-500 w-8">{idx + 1}.</span>
                  <Users className="h-4 w-4 text-gray-400" />
                  <div className="flex-1">
                    <div className="font-medium text-sm">{recipient.name}</div>
                    <div className="text-xs text-gray-600 font-mono">{recipient.phone}</div>
                  </div>
                </div>
              ))}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAllRecipientsModal(false)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default SMSCampaigns;
