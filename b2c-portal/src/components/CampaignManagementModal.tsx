import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { TimePicker } from '@/components/ui/time-picker';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
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
  Loader2,
  Users,
  Phone,
  Clock,
  RotateCw,
  Play,
  Pause,
  Square,
  TrendingUp,
  RefreshCw,
  AlertCircle,
  Plus,
  Trash2,
  Edit,
  Repeat
} from 'lucide-react';
import { toast } from 'sonner';

interface Audience {
  id: string;
  name: string;
  size: number;
  created_at: string;
}

interface CampaignConfig {
  call_delay_seconds: number;
  batch_interval_seconds?: number;
  max_retries: number;
  retry_on_no_answer: boolean;
  max_concurrent_calls: number;
  start_time?: string;  // HH:MM format in UTC
  pause_time?: string;  // HH:MM format in UTC
  auto_start?: boolean;  // Auto-start campaign at start_time
  use_asterisk?: boolean;  // Use Asterisk instead of VAPI for calls
}

interface CampaignProgress {
  total_contacts: number;
  triggered: number;
  completed: number;
  called: number;
  successful: number;
  failed: number;
  pending: number;
  no_answer: number;
  conversion_count: number;
  current_contact_index: number;
}

interface Campaign {
  id: string;
  automation_id: string;
  automation_name: string;
  audience_id: string;
  audience_name: string;
  user_id: string;
  phone_id?: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed';
  progress: CampaignProgress;
  config: CampaignConfig;
  total_cost: number;
  total_vapi_cost_usd?: number;
  total_phone_cost_ghc?: number;
  avg_call_duration: number;
  created_at: string;
  updated_at: string;
  started_at?: string;
  paused_at?: string;
  completed_at?: string;
  error_message?: string;
  recently_called_numbers?: Array<{
    phone: string;
    name?: string;
    call_record_id?: string;
    called_at: string;
    timestamp: number;
  }>;
}

interface CampaignManagementModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  automationId: string;
  automationName: string;
  onCampaignCreated?: () => void;
}

const CampaignManagementModal: React.FC<CampaignManagementModalProps> = ({
  open,
  onOpenChange,
  automationId,
  automationName,
  onCampaignCreated,
}) => {
  const [audiences, setAudiences] = useState<Audience[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [phoneNumbers, setPhoneNumbers] = useState<Array<{id: string, number: string, name?: string}>>([]);
  const [selectedAudienceId, setSelectedAudienceId] = useState<string>('');
  const [selectedPhoneId, setSelectedPhoneId] = useState<string>('');
  const [config, setConfig] = useState<CampaignConfig>({
    call_delay_seconds: 30,
    batch_interval_seconds: 10,
    max_retries: 2,
    retry_on_no_answer: true,
    max_concurrent_calls: 5,
    auto_start: false,
  });
  const [loading, setLoading] = useState(false);
  const [fetchingAudiences, setFetchingAudiences] = useState(false);
  const [fetchingCampaigns, setFetchingCampaigns] = useState(false);
  const [fetchingPhones, setFetchingPhones] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('campaigns');
  const [editingCampaign, setEditingCampaign] = useState<Campaign | null>(null);
  const [editConfig, setEditConfig] = useState<CampaignConfig | null>(null);
  const [selectedEditPhoneId, setSelectedEditPhoneId] = useState<string>('');
  const [deleteConfirmation, setDeleteConfirmation] = useState<{
    isOpen: boolean;
    campaignId: string | null;
    campaignName: string | null;
  }>({ isOpen: false, campaignId: null, campaignName: null });
  const [summaryCampaign, setSummaryCampaign] = useState<Campaign | null>(null);
  const [fetchingSummary, setFetchingSummary] = useState(false);
  const [campaignCalls, setCampaignCalls] = useState<any[]>([]);
  const [fetchingCalls, setFetchingCalls] = useState(false);
  const [callsPage, setCallsPage] = useState(1);
  const [callsTotal, setCallsTotal] = useState(0);
  const [callsLimit] = useState(100);

  const API_URL = import.meta.env.VITE_API_URL || 'https://flow-api.ailabsafrica.com';

  const getAuthHeaders = () => {
    const token = localStorage.getItem('mongo_access_token');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Add organization header if available
    const currentOrgId = localStorage.getItem('kasaai_current_organization_id');
    if (currentOrgId) {
      headers['X-Organization-ID'] = currentOrgId;
    }

    return headers;
  };

  useEffect(() => {
    if (open) {
      fetchAudiences();
      fetchCampaigns();
      fetchPhoneNumbers();
    }
  }, [open]);

  // Track previous campaign statuses to detect completion
  const [previousCampaignStatuses, setPreviousCampaignStatuses] = useState<Record<string, string>>({});

  // Auto-refresh campaigns when there are running campaigns
  useEffect(() => {
    if (!open) return;

    const hasRunningCampaigns = campaigns.some(c => c.status === 'running');
    if (!hasRunningCampaigns) return;

    // Refresh every 3 seconds when campaigns are running (silent mode to avoid error toasts)
    const interval = setInterval(() => {
      fetchCampaigns(true);
    }, 3000);

    return () => clearInterval(interval);
  }, [open, campaigns]);

  // Detect when campaigns complete and show summary
  useEffect(() => {
    if (!open || campaigns.length === 0) return;

    campaigns.forEach(campaign => {
      const previousStatus = previousCampaignStatuses[campaign.id];
      const currentStatus = campaign.status;

      // If campaign just completed, show summary
      if (previousStatus === 'running' && currentStatus === 'completed') {
        setSummaryCampaign(campaign);
      }
    });

    // Update previous statuses
    const newStatuses: Record<string, string> = {};
    campaigns.forEach(c => {
      newStatuses[c.id] = c.status;
    });
    setPreviousCampaignStatuses(newStatuses);
  }, [campaigns, open]);

  const fetchPhoneNumbers = async () => {
    setFetchingPhones(true);
    try {
      const response = await fetch(`${API_URL}/api/vapi/phone-numbers`, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) throw new Error('Failed to fetch phone numbers');

      const data = await response.json();
      const phones = Array.isArray(data) ? data : (data.phoneNumbers || []);
      setPhoneNumbers(phones);

      // Auto-select first phone if available
      if (phones.length > 0 && !selectedPhoneId) {
        setSelectedPhoneId(phones[0].id);
      }
    } catch (error) {
      console.error('Error fetching phone numbers:', error);
      toast.error('Failed to load phone numbers');
    } finally {
      setFetchingPhones(false);
    }
  };

  const fetchAudiences = async () => {
    setFetchingAudiences(true);
    try {
      const response = await fetch(`${API_URL}/audiences`, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) throw new Error('Failed to fetch audiences');

      const data = await response.json();
      setAudiences(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching audiences:', error);
      toast.error('Failed to load audiences');
    } finally {
      setFetchingAudiences(false);
    }
  };

  const fetchCampaigns = async (silent = false) => {
    if (!silent) setFetchingCampaigns(true);
    try {
      const response = await fetch(
        `${API_URL}/automation-configs/${automationId}/campaigns`,
        { headers: getAuthHeaders() }
      );

      if (!response.ok) throw new Error('Failed to fetch campaigns');

      const data = await response.json();
      setCampaigns(Array.isArray(data) ? data : []);
    } catch (error) {
      // Only log and show toast for non-silent (user-initiated) fetches
      // Silent fetches are auto-refresh polling where transient errors are expected
      if (!silent) {
        console.error('Error fetching campaigns:', error);
        toast.error('Failed to load campaigns');
      }
    } finally {
      if (!silent) setFetchingCampaigns(false);
    }
  };

  const handleCreateCampaign = async () => {
    if (!selectedAudienceId) {
      toast.error('Please select an audience');
      return;
    }

    if (!selectedPhoneId) {
      toast.error('Please select a phone number');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/automation-configs/${automationId}/campaigns`,
        {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({
            automation_id: automationId,
            audience_id: selectedAudienceId,
            phone_id: selectedPhoneId,
            config,
          }),
        }
      );

      if (!response.ok) throw new Error('Failed to create campaign');

      await response.json();
      toast.success('Campaign created successfully!');
      setSelectedAudienceId('');
      setActiveTab('campaigns'); // Switch to campaigns tab
      fetchCampaigns(); // Refresh campaigns list
      onCampaignCreated?.();
    } catch (error) {
      console.error('Error creating campaign:', error);
      toast.error('Failed to create campaign');
    } finally {
      setLoading(false);
    }
  };

  const handleCampaignAction = async (action: string, campaignId: string) => {
    setActionLoading(campaignId);
    try {
      const endpoint = `${API_URL}/automation-configs/${automationId}/campaigns/${campaignId}/${action}`;
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to ${action} campaign`);
      }

      toast.success(`Campaign ${action}ed successfully`);
      await fetchCampaigns();
    } catch (error: any) {
      console.error(`Error ${action}ing campaign:`, error);
      toast.error(error.message || `Failed to ${action} campaign`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRetryMissed = async (campaignId: string) => {
    setActionLoading(`retry-${campaignId}`);
    try {
      const endpoint = `${API_URL}/automation-configs/${automationId}/campaigns/${campaignId}/retry-missed`;
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to retry missed calls');
      }

      const data = await response.json();
      const retryCount = data.retry_count || 0;
      toast.success(`Retrying ${retryCount} missed call${retryCount !== 1 ? 's' : ''}`);
      await fetchCampaigns();
    } catch (error: any) {
      console.error('Error retrying missed calls:', error);
      toast.error(error.message || 'Failed to retry missed calls');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteCampaign = async () => {
    if (!deleteConfirmation.campaignId) return;

    setActionLoading(deleteConfirmation.campaignId);
    try {
      const response = await fetch(
        `${API_URL}/automation-configs/${automationId}/campaigns/${deleteConfirmation.campaignId}`,
        {
          method: 'DELETE',
          headers: getAuthHeaders(),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to delete campaign');
      }

      toast.success('Campaign deleted successfully');
      await fetchCampaigns();
      setDeleteConfirmation({ isOpen: false, campaignId: null, campaignName: null });
    } catch (error: any) {
      console.error('Error deleting campaign:', error);
      toast.error(error.message || 'Failed to delete campaign');
    } finally {
      setActionLoading(null);
    }
  };

  const handleEditCampaign = (campaign: Campaign) => {
    setEditingCampaign(campaign);
    // Ensure boolean fields are explicitly set to avoid undefined issues
    setEditConfig({
      ...campaign.config,
      auto_start: campaign.config.auto_start ?? false,
      retry_on_no_answer: campaign.config.retry_on_no_answer ?? true,
      use_asterisk: campaign.config.use_asterisk ?? false,
    });
    setSelectedEditPhoneId(campaign.phone_id || '');
    setActiveTab('edit');
  };

  const handleUpdateCampaign = async () => {
    if (!editingCampaign || !editConfig) return;

    if (!selectedEditPhoneId) {
      toast.error('Please select a phone number');
      return;
    }

    setLoading(true);
    try {
      // Send config fields + phone_id as flat object
      const updatePayload = {
        ...editConfig,
        phone_id: selectedEditPhoneId,
      };

      const response = await fetch(
        `${API_URL}/automation-configs/${automationId}/campaigns/${editingCampaign.id}`,
        {
          method: 'PUT',
          headers: getAuthHeaders(),
          body: JSON.stringify(updatePayload),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to update campaign');
      }

      toast.success('Campaign updated successfully!');
      setEditingCampaign(null);
      setEditConfig(null);
      setSelectedEditPhoneId('');
      setActiveTab('campaigns');
      fetchCampaigns();
    } catch (error: any) {
      console.error('Error updating campaign:', error);
      toast.error(error.message || 'Failed to update campaign');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { className: 'bg-yellow-100 text-yellow-800 border-yellow-200', label: 'Pending' },
      running: { className: 'bg-green-100 text-green-800 border-green-200', label: 'Running' },
      paused: { className: 'bg-orange-100 text-orange-800 border-orange-200', label: 'Paused' },
      completed: { className: 'bg-blue-100 text-blue-800 border-blue-200', label: 'Completed' },
      failed: { className: 'bg-red-100 text-red-800 border-red-200', label: 'Failed' },
    };
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    return <Badge className={config.className}>{config.label}</Badge>;
  };

  const getActionButtons = (campaign: Campaign) => {
    const isLoading = actionLoading === campaign.id;

    return (
      <div className="flex gap-2">
        {campaign.status === 'pending' && (
          <Button
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              handleCampaignAction('start', campaign.id);
            }}
            disabled={isLoading}
            className="gap-1"
          >
            {isLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
            Start
          </Button>
        )}

        {campaign.status === 'running' && (
          <Button
            size="sm"
            variant="outline"
            onClick={(e) => {
              e.stopPropagation();
              handleCampaignAction('pause', campaign.id);
            }}
            disabled={isLoading}
            className="gap-1"
          >
            {isLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Pause className="h-3 w-3" />}
            Pause
          </Button>
        )}

        {campaign.status === 'paused' && (
          <Button
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              handleCampaignAction('resume', campaign.id);
            }}
            disabled={isLoading}
            className="gap-1"
          >
            {isLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
            Resume
          </Button>
        )}

        {campaign.status === 'completed' && (
          <Button
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              handleCampaignAction('start', campaign.id);
            }}
            disabled={isLoading}
            className="gap-1"
          >
            {isLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <RefreshCw className="h-3 w-3" />}
            Replay
          </Button>
        )}

        {/* Retry Missed button - show for completed or paused campaigns */}
        {(campaign.status === 'completed' || campaign.status === 'paused') && (
          <Button
            size="sm"
            variant="outline"
            onClick={(e) => {
              e.stopPropagation();
              handleRetryMissed(campaign.id);
            }}
            disabled={isLoading || actionLoading === `retry-${campaign.id}`}
            className="gap-1"
          >
            {actionLoading === `retry-${campaign.id}` ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Repeat className="h-3 w-3" />
            )}
            Retry Missed
          </Button>
        )}

        {/* Edit button - only show for paused, pending, or completed campaigns */}
        {campaign.status !== 'running' && (
          <Button
            size="sm"
            variant="outline"
            onClick={(e) => {
              e.stopPropagation();
              handleEditCampaign(campaign);
            }}
            disabled={isLoading}
            className="gap-1"
          >
            <Edit className="h-3 w-3" />
          </Button>
        )}

        {/* Delete button - only show for non-running campaigns */}
        {campaign.status !== 'running' && (
          <Button
            size="sm"
            variant="destructive"
            onClick={(e) => {
              e.stopPropagation();
              setDeleteConfirmation({
                isOpen: true,
                campaignId: campaign.id,
                campaignName: campaign.audience_name,
              });
            }}
            disabled={isLoading}
            className="gap-1"
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        )}
      </div>
    );
  };

  const calculateProgress = (progress: CampaignProgress) => {
    if (progress.total_contacts === 0) return 0;
    return Math.round((progress.called / progress.total_contacts) * 100);
  };

  const calculateSuccessRate = (progress: CampaignProgress) => {
    if (progress.called === 0) return 0;
    return Math.round((progress.successful / progress.called) * 100);
  };

  const selectedAudience = audiences.find((a) => a.id === selectedAudienceId);
  const contactCount = selectedAudience?.size || 0;
  const estimatedDuration = contactCount * (60 + config.call_delay_seconds);
  const estimatedMinutes = Math.ceil(estimatedDuration / 60);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[900px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle>Manage Campaigns</DialogTitle>
              <DialogDescription>
                Create and manage campaigns for <span className="font-medium">{automationName}</span>
              </DialogDescription>
            </div>
            <Button onClick={fetchCampaigns} variant="outline" size="sm" className="gap-2">
              <RefreshCw className={`h-4 w-4 ${fetchingCampaigns ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="campaigns" className="gap-2">
              <Users className="h-4 w-4" />
              Campaigns ({campaigns.length})
            </TabsTrigger>
            <TabsTrigger value="create" className="gap-2">
              <Plus className="h-4 w-4" />
              Create New
            </TabsTrigger>
            {editingCampaign && (
              <TabsTrigger value="edit" className="gap-2">
                <Edit className="h-4 w-4" />
                Edit Campaign
              </TabsTrigger>
            )}
          </TabsList>

          {/* Existing Campaigns Tab */}
          <TabsContent value="campaigns" className="space-y-4 mt-4">
            {fetchingCampaigns ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
              </div>
            ) : campaigns.length === 0 ? (
              <div className="text-center py-8">
                <AlertCircle className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Campaigns Yet</h3>
                <p className="text-gray-600 mb-4">
                  Create your first campaign by selecting an audience.
                </p>
                <Button onClick={() => setActiveTab('create')} className="gap-2">
                  <Plus className="h-4 w-4" />
                  Create Campaign
                </Button>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Audience</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Progress</TableHead>
                    <TableHead>Success</TableHead>
                    <TableHead>Cost</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {campaigns.map((campaign) => {
                    const progress = calculateProgress(campaign.progress);
                    const successRate = calculateSuccessRate(campaign.progress);

                    return (
                      <TableRow 
                        key={campaign.id}
                        className="cursor-pointer hover:bg-gray-50 transition-colors"
                        onClick={async (e) => {
                          // Only open modal if click is not on action buttons
                          const target = e.target as HTMLElement;
                          if (!target.closest('button') && !target.closest('[role="button"]')) {
                            setSummaryCampaign(campaign);
                            // Fetch campaign calls when opening summary
                            setFetchingCalls(true);
                            setCallsPage(1);
                            try {
                              const response = await fetch(
                                `${API_URL}/automation-configs/${automationId}/campaigns/${campaign.id}/calls?page=1&limit=${callsLimit}`,
                                { headers: getAuthHeaders() }
                              );
                              if (response.ok) {
                                const data = await response.json();
                                setCampaignCalls(data.calls || []);
                                setCallsTotal(data.pagination?.total || 0);
                              }
                            } catch (error) {
                              console.error('Error fetching campaign calls:', error);
                            } finally {
                              setFetchingCalls(false);
                            }
                          }
                        }}
                      >
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Users className="h-4 w-4 text-gray-600" />
                            <div>
                              <div className="font-medium">{campaign.audience_name}</div>
                              <div className="text-xs text-gray-600">
                                {campaign.progress.total_contacts} contacts
                              </div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {getStatusBadge(campaign.status)}
                            {campaign.config?.use_asterisk && (
                              <Badge variant="outline" className="text-xs bg-purple-50 text-purple-700 border-purple-200">
                                Asterisk
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="space-y-1 min-w-[160px]">
                            <div className="flex items-center justify-between text-xs">
                              <span>{campaign.progress.called} / {campaign.progress.total_contacts}</span>
                              <span className="font-medium">{progress}%</span>
                            </div>
                            <Progress value={progress} className="h-2" />
                            {campaign.status === 'running' && (
                              <div className="flex gap-2 text-xs text-gray-600 mt-1">
                                <span title="Calls triggered">
                                  🚀 {campaign.progress.triggered || 0}
                                </span>
                                <span title="Calls completed">
                                  ✅ {campaign.progress.completed || 0}
                                </span>
                                <span title="Successful calls">
                                  ✓ {campaign.progress.successful || 0}
                                </span>
                                <span title="Failed calls">
                                  ✗ {campaign.progress.failed || 0}
                                </span>
                              </div>
                            )}
                            {campaign.status === 'running' && campaign.recently_called_numbers && campaign.recently_called_numbers.length > 0 && (
                              <div className="mt-2 text-xs">
                                <div className="font-medium text-gray-700 mb-1">Recently Called:</div>
                                <div className="flex flex-wrap gap-1">
                                  {campaign.recently_called_numbers.slice(-5).map((called, idx) => (
                                    <span
                                      key={idx}
                                      className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs"
                                      title={called.name ? `${called.name} - ${called.phone}` : called.phone}
                                    >
                                      {called.phone.slice(-4)}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <TrendingUp className="h-3 w-3 text-gray-600" />
                            <span className="text-sm font-medium">{successRate}%</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm space-y-0.5">
                            <div>${(campaign.total_vapi_cost_usd ?? campaign.total_cost).toFixed(2)}</div>
                            {campaign.total_phone_cost_ghc !== undefined && campaign.total_phone_cost_ghc > 0 && (
                              <div className="text-xs text-gray-500">{campaign.total_phone_cost_ghc.toFixed(2)} GHC</div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell 
                          className="text-right"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div onClick={(e) => e.stopPropagation()}>
                            {getActionButtons(campaign)}
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </TabsContent>

          {/* Create New Campaign Tab */}
          <TabsContent value="create" className="space-y-4 mt-4">
            {/* Audience Selection */}
            <div className="space-y-2">
              <Label htmlFor="audience">Audience</Label>
              <Select value={selectedAudienceId} onValueChange={setSelectedAudienceId}>
                <SelectTrigger id="audience" disabled={fetchingAudiences}>
                  <SelectValue
                    placeholder={fetchingAudiences ? 'Loading audiences...' : 'Select an audience'}
                  />
                </SelectTrigger>
                <SelectContent>
                  {audiences.map((audience) => (
                    <SelectItem key={audience.id} value={audience.id}>
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4" />
                        <span>{audience.name}</span>
                        <span className="text-gray-600 text-xs">
                          ({audience.size || 0} contacts)
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedAudience && (
                <p className="text-sm text-gray-600">
                  {contactCount} contacts will be called with {config.max_concurrent_calls} concurrent call(s)
                </p>
              )}
            </div>

            {/* Phone Number Selection */}
            <div className="space-y-2">
              <Label htmlFor="phone">VAPI Phone Number</Label>
              <Select value={selectedPhoneId} onValueChange={setSelectedPhoneId}>
                <SelectTrigger id="phone" disabled={fetchingPhones}>
                  <SelectValue
                    placeholder={fetchingPhones ? 'Loading phone numbers...' : 'Select a phone number'}
                  />
                </SelectTrigger>
                <SelectContent>
                  {phoneNumbers.map((phone) => (
                    <SelectItem key={phone.id} value={phone.id}>
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4" />
                        <span>{phone.number}</span>
                        {phone.name && (
                          <span className="text-gray-600 text-xs">({phone.name})</span>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Campaign Configuration */}
            <div className="space-y-3 rounded-lg border p-3">
              <h4 className="text-sm font-medium">Campaign Settings</h4>

              <div className="space-y-2">
                <Label htmlFor="concurrent-calls" className="flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  Max Concurrent Calls
                </Label>
                <Input
                  id="concurrent-calls"
                  type="number"
                  min="1"
                  max="50"
                  value={config.max_concurrent_calls}
                  onChange={(e) =>
                    setConfig({ ...config, max_concurrent_calls: parseInt(e.target.value) || 5 })
                  }
                />
                <p className="text-xs text-gray-600">
                  Number of calls to trigger simultaneously (e.g., 5 = 5 concurrent calls)
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="call-delay" className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Delay Between Calls (seconds)
                </Label>
                <Input
                  id="call-delay"
                  type="number"
                  min="10"
                  max="300"
                  value={config.call_delay_seconds}
                  onChange={(e) =>
                    setConfig({ ...config, call_delay_seconds: parseInt(e.target.value) || 30 })
                  }
                />
                <p className="text-xs text-gray-600">
                  Delay between individual calls within a batch
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="batch-interval" className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Batch Interval (seconds)
                </Label>
                <Input
                  id="batch-interval"
                  type="number"
                  min="5"
                  max="300"
                  value={config.batch_interval_seconds || 10}
                  onChange={(e) =>
                    setConfig({ ...config, batch_interval_seconds: parseInt(e.target.value) || 10 })
                  }
                />
                <p className="text-xs text-gray-600">
                  Wait time between batches of concurrent calls (e.g., wait 10s before next batch of 5 calls)
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="max-retries" className="flex items-center gap-2">
                  <RotateCw className="h-4 w-4" />
                  Maximum Retries
                </Label>
                <Input
                  id="max-retries"
                  type="number"
                  min="0"
                  max="5"
                  value={config.max_retries}
                  onChange={(e) =>
                    setConfig({ ...config, max_retries: parseInt(e.target.value) || 2 })
                  }
                />
              </div>

              <div className="border-t pt-3 mt-3">
                <h5 className="text-sm font-medium mb-3">Calling Time Window (UTC)</h5>
                <p className="text-xs text-gray-600 mb-3">
                  Campaign will automatically pause at pause time and resume at start time to avoid calling too early or too late.
                </p>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label htmlFor="start-time">
                      Start Time (UTC)
                    </Label>
                    <TimePicker
                      id="start-time"
                      value={config.start_time || ''}
                      onChange={(time) => {
                        setConfig({ ...config, start_time: time || undefined });
                      }}
                      placeholder="Select start time"
                    />
                    <p className="text-xs text-gray-600">
                      Campaign will resume at this time daily
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="pause-time">
                      Pause Time (UTC)
                    </Label>
                    <TimePicker
                      id="pause-time"
                      value={config.pause_time || ''}
                      onChange={(time) => {
                        setConfig({ ...config, pause_time: time || undefined });
                      }}
                      placeholder="Select pause time"
                    />
                    <p className="text-xs text-gray-600">
                      Campaign will pause at this time daily
                    </p>
                  </div>
                </div>

                {/* Auto Start Checkbox */}
                <div className="mt-3 pt-3 border-t">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="auto-start"
                      checked={config.auto_start === true}
                      onCheckedChange={(checked) => {
                        setConfig({ ...config, auto_start: checked === true });
                      }}
                    />
                    <Label htmlFor="auto-start" className="text-sm font-medium cursor-pointer">
                      Auto-start campaign at start time
                    </Label>
                  </div>
                  <p className="text-xs text-gray-600 ml-6 mt-1">
                    When enabled, the campaign will automatically start when the start time is reached
                  </p>
                </div>

                {/* Use Asterisk Checkbox */}
                <div className="mt-3 pt-3 border-t">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="use-asterisk"
                      checked={config.use_asterisk || false}
                      onCheckedChange={(checked) => {
                        setConfig({ ...config, use_asterisk: checked === true });
                      }}
                    />
                    <Label htmlFor="use-asterisk" className="text-sm font-medium cursor-pointer">
                      Use Asterisk (Self-hosted calls)
                    </Label>
                    {config.use_asterisk && (
                      <Badge variant="secondary" className="ml-2 text-xs bg-green-100 text-green-800">
                        $0 TTS/ASR
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-gray-600 ml-6 mt-1">
                    Route calls through our Asterisk server with local TTS/ASR providers instead of VAPI.
                    {config.use_asterisk && " Uses Kokoro TTS, Faster Whisper ASR, and your configured LLM."}
                  </p>
                </div>
              </div>
            </div>

            {/* Estimated Duration */}
            {selectedAudience && (
              <div className="rounded-lg bg-muted p-3">
                <div className="flex items-center gap-2 text-sm">
                  <Phone className="h-4 w-4" />
                  <span className="font-medium">Estimated Duration:</span>
                  <span className="text-gray-600">
                    {estimatedMinutes < 60
                      ? `${estimatedMinutes} minutes`
                      : `${Math.floor(estimatedMinutes / 60)}h ${estimatedMinutes % 60}m`}
                  </span>
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  Based on avg. 60s call + {config.call_delay_seconds}s delay per contact
                </p>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-4">
              <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
                Cancel
              </Button>
              <Button onClick={handleCreateCampaign} disabled={loading || !selectedAudienceId}>
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Plus className="mr-2 h-4 w-4" />
                    Create Campaign
                  </>
                )}
              </Button>
            </div>
          </TabsContent>

          {/* Edit Campaign Tab */}
          {editingCampaign && editConfig && (
            <TabsContent value="edit" className="space-y-4 mt-4">
              <div className="rounded-lg border p-4 mb-4 bg-muted">
                <p className="text-sm font-medium">Editing: {editingCampaign.audience_name}</p>
                <p className="text-xs text-gray-600 mt-1">
                  Campaign must be paused before editing configuration
                </p>
              </div>

              {/* Phone Number Selection */}
              <div className="space-y-2">
                <Label htmlFor="edit-phone">VAPI Phone Number</Label>
                <Select value={selectedEditPhoneId} onValueChange={setSelectedEditPhoneId}>
                  <SelectTrigger id="edit-phone" disabled={fetchingPhones}>
                    <SelectValue
                      placeholder={fetchingPhones ? 'Loading phone numbers...' : 'Select a phone number'}
                    />
                  </SelectTrigger>
                  <SelectContent>
                    {phoneNumbers.map((phone) => (
                      <SelectItem key={phone.id} value={phone.id}>
                        <div className="flex items-center gap-2">
                          <Phone className="h-4 w-4" />
                          <span>{phone.number}</span>
                          {phone.name && (
                            <span className="text-gray-600 text-xs">({phone.name})</span>
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Campaign Configuration */}
              <div className="space-y-3 rounded-lg border p-3">
                <h4 className="text-sm font-medium">Campaign Settings</h4>

                <div className="space-y-2">
                  <Label htmlFor="edit-concurrent-calls" className="flex items-center gap-2">
                    <Phone className="h-4 w-4" />
                    Max Concurrent Calls
                  </Label>
                  <Input
                    id="edit-concurrent-calls"
                    type="number"
                    min="1"
                    max="50"
                    value={editConfig.max_concurrent_calls}
                    onChange={(e) =>
                      setEditConfig({ ...editConfig, max_concurrent_calls: parseInt(e.target.value) || 5 })
                    }
                  />
                  <p className="text-xs text-gray-600">
                    Number of calls to trigger simultaneously (e.g., 5 = 5 concurrent calls)
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="edit-call-delay" className="flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    Delay Between Calls (seconds)
                  </Label>
                  <Input
                    id="edit-call-delay"
                    type="number"
                    min="10"
                    max="300"
                    value={editConfig.call_delay_seconds}
                    onChange={(e) =>
                      setEditConfig({ ...editConfig, call_delay_seconds: parseInt(e.target.value) || 30 })
                    }
                  />
                  <p className="text-xs text-gray-600">
                    Delay between individual calls within a batch
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="edit-batch-interval" className="flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    Batch Interval (seconds)
                  </Label>
                  <Input
                    id="edit-batch-interval"
                    type="number"
                    min="5"
                    max="300"
                    value={editConfig.batch_interval_seconds || 10}
                    onChange={(e) =>
                      setEditConfig({ ...editConfig, batch_interval_seconds: parseInt(e.target.value) || 10 })
                    }
                  />
                  <p className="text-xs text-gray-600">
                    Wait time between batches of concurrent calls
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="edit-max-retries" className="flex items-center gap-2">
                    <RotateCw className="h-4 w-4" />
                    Maximum Retries
                  </Label>
                  <Input
                    id="edit-max-retries"
                    type="number"
                    min="0"
                    max="5"
                    value={editConfig.max_retries}
                    onChange={(e) =>
                      setEditConfig({ ...editConfig, max_retries: parseInt(e.target.value) || 2 })
                    }
                  />
                </div>

                <div className="border-t pt-3 mt-3">
                  <h5 className="text-sm font-medium mb-3">Calling Time Window (UTC)</h5>
                  <p className="text-xs text-gray-600 mb-3">
                    Campaign will automatically pause at pause time and resume at start time to avoid calling too early or too late.
                  </p>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label htmlFor="edit-start-time">
                        Start Time (UTC)
                      </Label>
                      <TimePicker
                        id="edit-start-time"
                        value={editConfig.start_time || ''}
                        onChange={(time) => {
                          setEditConfig({ ...editConfig, start_time: time || undefined });
                        }}
                        placeholder="Select start time"
                      />
                      <p className="text-xs text-gray-600">
                        Campaign will resume at this time daily
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="edit-pause-time">
                        Pause Time (UTC)
                      </Label>
                      <TimePicker
                        id="edit-pause-time"
                        value={editConfig.pause_time || ''}
                        onChange={(time) => {
                          setEditConfig({ ...editConfig, pause_time: time || undefined });
                        }}
                        placeholder="Select pause time"
                      />
                      <p className="text-xs text-gray-600">
                        Campaign will pause at this time daily
                      </p>
                    </div>
                  </div>

                  {/* Auto Start Checkbox */}
                  <div className="mt-3 pt-3 border-t">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="edit-auto-start"
                        checked={editConfig.auto_start === true}
                        onCheckedChange={(checked) => {
                          setEditConfig({ ...editConfig, auto_start: checked === true });
                        }}
                      />
                      <Label htmlFor="edit-auto-start" className="text-sm font-medium cursor-pointer">
                        Auto-start campaign at start time
                      </Label>
                    </div>
                    <p className="text-xs text-gray-600 ml-6 mt-1">
                      When enabled, the campaign will automatically start when the start time is reached
                    </p>
                  </div>

                  {/* Use Asterisk Checkbox */}
                  <div className="mt-3 pt-3 border-t">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="edit-use-asterisk"
                        checked={editConfig.use_asterisk || false}
                        onCheckedChange={(checked) => {
                          setEditConfig({ ...editConfig, use_asterisk: checked === true });
                        }}
                      />
                      <Label htmlFor="edit-use-asterisk" className="text-sm font-medium cursor-pointer">
                        Use Asterisk (Self-hosted calls)
                      </Label>
                      {editConfig.use_asterisk && (
                        <Badge variant="secondary" className="ml-2 text-xs bg-green-100 text-green-800">
                          $0 TTS/ASR
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 ml-6 mt-1">
                      Route calls through our Asterisk server with local TTS/ASR providers instead of VAPI.
                      {editConfig.use_asterisk && " Uses Kokoro TTS, Faster Whisper ASR, and your configured LLM."}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button
                  variant="outline"
                  onClick={() => {
                    setEditingCampaign(null);
                    setEditConfig(null);
                    setActiveTab('campaigns');
                  }}
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button onClick={handleUpdateCampaign} disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Updating...
                    </>
                  ) : (
                    <>
                      <Edit className="mr-2 h-4 w-4" />
                      Update Campaign
                    </>
                  )}
                </Button>
              </div>
            </TabsContent>
          )}
        </Tabs>
      </DialogContent>

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        open={deleteConfirmation.isOpen}
        onOpenChange={(open) =>
          !open && setDeleteConfirmation({ isOpen: false, campaignId: null, campaignName: null })
        }
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Campaign</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the campaign for{' '}
              <span className="font-semibold">{deleteConfirmation.campaignName}</span>?
              <br />
              <br />
              This action cannot be undone. All campaign data, progress, and analytics will be permanently
              deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              onClick={() =>
                setDeleteConfirmation({ isOpen: false, campaignId: null, campaignName: null })
              }
            >
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteCampaign}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete Campaign
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Campaign Summary Modal */}
      <Dialog open={!!summaryCampaign} onOpenChange={(open) => !open && setSummaryCampaign(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
              Campaign Summary: {summaryCampaign?.audience_name}
            </DialogTitle>
            <DialogDescription>
              Complete performance metrics and analytics for this campaign
            </DialogDescription>
          </DialogHeader>

          {summaryCampaign && (
            <div className="space-y-6 mt-4">
              {/* Overview Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-sm text-gray-600">Total Contacts</div>
                  <div className="text-2xl font-bold text-blue-600">{summaryCampaign.progress.total_contacts}</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="text-sm text-gray-600">Successful</div>
                  <div className="text-2xl font-bold text-green-600">{summaryCampaign.progress.successful}</div>
                </div>
                <div className="bg-red-50 p-4 rounded-lg">
                  <div className="text-sm text-gray-600">Failed</div>
                  <div className="text-2xl font-bold text-red-600">{summaryCampaign.progress.failed}</div>
                </div>
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <div className="text-sm text-gray-600">No Answer</div>
                  <div className="text-2xl font-bold text-yellow-600">{summaryCampaign.progress.no_answer}</div>
                </div>
              </div>

              {/* Progress */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Progress</span>
                  <span className="font-medium">
                    {summaryCampaign.progress.called} / {summaryCampaign.progress.total_contacts} calls
                  </span>
                </div>
                <Progress 
                  value={(summaryCampaign.progress.called / summaryCampaign.progress.total_contacts) * 100} 
                  className="h-3"
                />
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-2 gap-4">
                <div className="border rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">VAPI Cost (USD)</div>
                  <div className="text-xl font-bold">${(summaryCampaign.total_vapi_cost_usd ?? summaryCampaign.total_cost).toFixed(2)}</div>
                </div>
                <div className="border rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Phone Cost (GHC)</div>
                  <div className="text-xl font-bold">{(summaryCampaign.total_phone_cost_ghc ?? 0).toFixed(2)} GHC</div>
                </div>
                <div className="border rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Avg Call Duration</div>
                  <div className="text-xl font-bold">
                    {Math.round(summaryCampaign.avg_call_duration)}s
                  </div>
                </div>
                <div className="border rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Success Rate</div>
                  <div className="text-xl font-bold">
                    {summaryCampaign.progress.called > 0
                      ? ((summaryCampaign.progress.successful / summaryCampaign.progress.called) * 100).toFixed(1)
                      : 0}%
                  </div>
                </div>
              </div>

              {/* Status Badge */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Status:</span>
                {getStatusBadge(summaryCampaign.status)}
              </div>

              {/* Resumption Info */}
              <div className="border rounded-lg p-4 bg-blue-50">
                <div className="text-sm font-medium text-gray-700 mb-2">Resume Information</div>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>Current Position: Contact {summaryCampaign.progress.current_contact_index + 1} of {summaryCampaign.progress.total_contacts}</div>
                  <div>When resumed, campaign will continue from contact index {summaryCampaign.progress.current_contact_index}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {summaryCampaign.progress.called} calls completed, {summaryCampaign.progress.total_contacts - summaryCampaign.progress.called} remaining
                  </div>
                </div>
              </div>

              {/* Timestamps */}
              <div className="space-y-1 text-sm text-gray-600">
                {summaryCampaign.started_at && (
                  <div>Started: {new Date(summaryCampaign.started_at).toLocaleString()}</div>
                )}
                {summaryCampaign.paused_at && (
                  <div>Paused: {new Date(summaryCampaign.paused_at).toLocaleString()}</div>
                )}
                {summaryCampaign.completed_at && (
                  <div>Completed: {new Date(summaryCampaign.completed_at).toLocaleString()}</div>
                )}
              </div>

              {/* Campaign Calls List */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Call History ({callsTotal} total)</h3>
                  {fetchingCalls && <Loader2 className="h-4 w-4 animate-spin" />}
                </div>
                
                {campaignCalls.length === 0 && !fetchingCalls ? (
                  <div className="text-center py-8 text-gray-500">
                    No calls found
                  </div>
                ) : (
                  <div className="border rounded-lg max-h-[400px] overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-4 py-2 text-left">#</th>
                          <th className="px-4 py-2 text-left">Contact</th>
                          <th className="px-4 py-2 text-left">Phone</th>
                          <th className="px-4 py-2 text-left">Status</th>
                          <th className="px-4 py-2 text-left">Duration</th>
                          <th className="px-4 py-2 text-left">Cost</th>
                          <th className="px-4 py-2 text-left">Called At</th>
                        </tr>
                      </thead>
                      <tbody>
                        {campaignCalls.map((call, idx) => (
                          <tr key={call.id || idx} className="border-t hover:bg-gray-50">
                            <td className="px-4 py-2">{call.contact_index !== undefined ? call.contact_index + 1 : idx + 1}</td>
                            <td className="px-4 py-2">
                              {call.contact?.name || call.contact?.contact?.name || 'Unknown'}
                            </td>
                            <td className="px-4 py-2 font-mono text-xs">
                              {call.contact?.phone || call.contact?.contact?.phone || 'N/A'}
                            </td>
                            <td className="px-4 py-2">
                              <span className={`px-2 py-1 rounded text-xs ${
                                call.status === 'completed' ? 'bg-green-100 text-green-800' :
                                call.status === 'failed' ? 'bg-red-100 text-red-800' :
                                call.status === 'no_answer' ? 'bg-yellow-100 text-yellow-800' :
                                call.status === 'calling' ? 'bg-blue-100 text-blue-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {call.status || 'pending'}
                              </span>
                            </td>
                            <td className="px-4 py-2">
                              {call.duration ? `${call.duration}s` : 'N/A'}
                            </td>
                            <td className="px-4 py-2">
                              {call.cost ? `$${call.cost.toFixed(4)}` : 'N/A'}
                            </td>
                            <td className="px-4 py-2 text-xs text-gray-600">
                              {call.called_at ? new Date(call.called_at).toLocaleString() : 
                               call.created_at ? new Date(call.created_at).toLocaleString() : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Pagination */}
                {callsTotal > callsLimit && (
                  <div className="flex items-center justify-between pt-2">
                    <div className="text-sm text-gray-600">
                      Showing {((callsPage - 1) * callsLimit) + 1} - {Math.min(callsPage * callsLimit, callsTotal)} of {callsTotal}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={async () => {
                          if (callsPage > 1 && summaryCampaign) {
                            const newPage = callsPage - 1;
                            setCallsPage(newPage);
                            setFetchingCalls(true);
                            try {
                              const response = await fetch(
                                `${API_URL}/automation-configs/${automationId}/campaigns/${summaryCampaign.id}/calls?page=${newPage}&limit=${callsLimit}`,
                                { headers: getAuthHeaders() }
                              );
                              if (response.ok) {
                                const data = await response.json();
                                setCampaignCalls(data.calls || []);
                              }
                            } catch (error) {
                              console.error('Error fetching campaign calls:', error);
                            } finally {
                              setFetchingCalls(false);
                            }
                          }
                        }}
                        disabled={callsPage === 1 || fetchingCalls}
                      >
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={async () => {
                          if (callsPage * callsLimit < callsTotal && summaryCampaign) {
                            const newPage = callsPage + 1;
                            setCallsPage(newPage);
                            setFetchingCalls(true);
                            try {
                              const response = await fetch(
                                `${API_URL}/automation-configs/${automationId}/campaigns/${summaryCampaign.id}/calls?page=${newPage}&limit=${callsLimit}`,
                                { headers: getAuthHeaders() }
                              );
                              if (response.ok) {
                                const data = await response.json();
                                setCampaignCalls(data.calls || []);
                              }
                            } catch (error) {
                              console.error('Error fetching campaign calls:', error);
                            } finally {
                              setFetchingCalls(false);
                            }
                          }
                        }}
                        disabled={callsPage * callsLimit >= callsTotal || fetchingCalls}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2 mt-6">
            <Button variant="outline" onClick={() => setSummaryCampaign(null)}>
              Close
            </Button>
            {summaryCampaign && (
              <Button
                onClick={async () => {
                  setFetchingSummary(true);
                  try {
                    const response = await fetch(
                      `${API_URL}/automation-configs/${automationId}/campaigns/${summaryCampaign.id}/analytics`,
                      { headers: getAuthHeaders() }
                    );
                    if (response.ok) {
                      const analytics = await response.json();
                      toast.success('Analytics loaded! Check the detailed view.');
                      console.log('Campaign Analytics:', analytics);
                    }
                  } catch (error) {
                    console.error('Error fetching analytics:', error);
                  } finally {
                    setFetchingSummary(false);
                  }
                }}
                disabled={fetchingSummary}
              >
                {fetchingSummary ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Loading...
                  </>
                ) : (
                  <>
                    <TrendingUp className="mr-2 h-4 w-4" />
                    View Detailed Analytics
                  </>
                )}
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </Dialog>
  );
};

export default CampaignManagementModal;
