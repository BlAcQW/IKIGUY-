/**
 * SMS Campaigns Page for ChurchFlow
 *
 * Allows church admins to create and manage bulk SMS campaigns
 * for member communication.
 *
 * URL: /admin/sms-campaigns
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MessageSquare,
  Plus,
  Search,
  Play,
  Pause,
  XCircle,
  Eye,
  Trash2,
  Users,
  Send,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Church,
  Edit,
  Copy,
  X
} from 'lucide-react';
import { API_BASE_URL } from '../config';
import ConfirmDialog from '../components/ConfirmDialog';

interface SMSCampaign {
  id: string;
  name: string;
  template_content: string;
  status: 'draft' | 'scheduled' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  progress: {
    total_recipients: number;
    sent: number;
    delivered: number;
    failed: number;
    pending: number;
  };
  total_cost: number;
  sms_provider: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

interface Conference {
  id: string;
  name: string;
}

interface Branch {
  id: string;
  name: string;
}

interface Session {
  id: string;
  name: string;
  day_label: string;
  day_number: number;
}

const SMSCampaigns = () => {
  const navigate = useNavigate();

  // Get token from localStorage
  const token = localStorage.getItem('access_token');

  // State
  const [campaigns, setCampaigns] = useState<SMSCampaign[]>([]);
  const [conferences, setConferences] = useState<Conference[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Dialog states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState<SMSCampaign | null>(null);
  const [editingCampaign, setEditingCampaign] = useState<SMSCampaign | null>(null);
  const [analyticsTab, setAnalyticsTab] = useState<'overview' | 'successful' | 'failed' | 'all'>('overview');
  const [campaignMessages, setCampaignMessages] = useState<any[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  // Delete confirmation dialog state
  const [deleteDialog, setDeleteDialog] = useState<{
    isOpen: boolean;
    campaignId: string | null;
    campaignName: string;
    isLoading: boolean;
  }>({ isOpen: false, campaignId: null, campaignName: '', isLoading: false });

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    template_content: '',
    audience_type: 'all',
    conference_id: '',
    branch_ids: [] as string[],  // Changed from branch_id to branch_ids (array)
    session_ids: [] as string[],
    manual_contacts: '',
    sender_id: 'IMPACT2025',
    send_rate: '1',
    sms_provider: 'arkesel'
  });

  // Recipient count state
  const [recipientCount, setRecipientCount] = useState<number | null>(null);
  const [fetchingCount, setFetchingCount] = useState(false);
  const [sampleRecipients, setSampleRecipients] = useState<Array<{name: string, phone: string}>>([]);
  const [showAllRecipientsModal, setShowAllRecipientsModal] = useState(false);
  const [allRecipients, setAllRecipients] = useState<Array<{name: string, phone: string}>>([]);
  const [loadingAllRecipients, setLoadingAllRecipients] = useState(false);

  // Branch search filter
  const [branchSearch, setBranchSearch] = useState('');

  // Session search filter
  const [sessionSearch, setSessionSearch] = useState('');

  // Fetch messages when analytics tab changes
  useEffect(() => {
    if (showDetailsModal && selectedCampaign && analyticsTab !== 'overview') {
      const statusMap = {
        'successful': 'sent',
        'failed': 'failed',
        'all': undefined
      };
      fetchCampaignMessages(selectedCampaign.id, statusMap[analyticsTab as keyof typeof statusMap]);
    }
  }, [analyticsTab, showDetailsModal, selectedCampaign?.id]);

  // Fetch campaigns
  const fetchCampaigns = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/sms-campaigns/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setCampaigns(data.campaigns || []);
      }
    } catch (error) {
      console.error('Error fetching campaigns:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch conferences
  const fetchConferences = async () => {
    try {
      const confResponse = await fetch(`${API_BASE_URL}/conferences`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (confResponse.ok) {
        const data = await confResponse.json();
        // Conferences API returns array directly
        const conferencesArray = Array.isArray(data) ? data : [];
        setConferences(conferencesArray);
        console.log('Loaded conferences:', conferencesArray.length);
      } else {
        console.error('Failed to fetch conferences:', confResponse.status);
      }
    } catch (error) {
      console.error('Error fetching conferences:', error);
    }
  };

  // Fetch branches (only when needed for branch/session targeting)
  const fetchBranches = async () => {
    // Don't fetch if already loaded
    if (branches.length > 0) {
      console.log('Branches already loaded, skipping fetch');
      return;
    }

    try {
      console.log('Fetching branches...');
      const branchResponse = await fetch(`${API_BASE_URL}/branches`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (branchResponse.ok) {
        const data = await branchResponse.json();
        // Branches API returns array directly
        const branchesArray = Array.isArray(data) ? data : [];
        setBranches(branchesArray);
        console.log('Loaded branches:', branchesArray.length);
      } else {
        console.error('Failed to fetch branches:', branchResponse.status);
      }
    } catch (error) {
      console.error('Error fetching branches:', error);
    }
  };

  useEffect(() => {
    if (token) {
      fetchCampaigns();
      fetchConferences(); // Only fetch conferences on initial load
    }
  }, [token]);

  // Fetch branches when audience type requires them
  useEffect(() => {
    if (token && (formData.audience_type === 'branch' || formData.audience_type === 'session' || formData.audience_type === 'checked_in')) {
      fetchBranches();
    }
  }, [formData.audience_type, token]);

  // Fetch sessions when conference is selected and audience type is session or checked_in
  useEffect(() => {
    if (
      formData.conference_id &&
      (formData.audience_type === 'session' || formData.audience_type === 'checked_in')
    ) {
      fetchSessions(formData.conference_id);
    }
  }, [formData.conference_id, formData.audience_type]);

  // Fetch sessions for a conference
  const fetchSessions = async (conferenceId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/conferences/${conferenceId}/sessions`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        // Backend returns { sessions: [...], total, conference_id }
        setSessions((data.sessions || data || []) as Session[]);
      }
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  };

  // Filter campaigns
  const filteredCampaigns = campaigns.filter(campaign => {
    const matchesSearch = campaign.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || campaign.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Open edit modal
  const openEditModal = async (campaign: SMSCampaign) => {
    setEditingCampaign(campaign);

    // Fetch full campaign details including targeting info
    try {
      const response = await fetch(`${API_BASE_URL}/sms-campaigns/${campaign.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const fullCampaign = await response.json();

        // Populate form with campaign data
        setFormData({
          name: fullCampaign.name,
          template_content: fullCampaign.template_content,
          audience_type: fullCampaign.audience_type || 'all',
          conference_id: fullCampaign.conference_id || '',
          branch_ids: fullCampaign.branch_ids || (fullCampaign.branch_id ? [fullCampaign.branch_id] : []),
          session_ids: fullCampaign.session_ids || [],
          manual_contacts: fullCampaign.manual_contacts
            ? fullCampaign.manual_contacts.map((c: any) => `${c.phone}${c.name ? `,${c.name}` : ''}`).join('\n')
            : '',
          sender_id: fullCampaign.config?.sender_id || '',
          send_rate: fullCampaign.config?.send_rate_per_second?.toString() || '1',
          sms_provider: fullCampaign.sms_provider || 'arkesel'
        });

        setShowCreateModal(true);
      }
    } catch (error) {
      console.error('Error fetching campaign details:', error);
      alert('Failed to load campaign details');
    }
  };

  // Create or update campaign
  const handleSaveCampaign = async () => {
    if (!formData.name || !formData.template_content) {
      alert('Please fill in campaign name and message template.');
      return;
    }

    try {
      // Parse manual contacts (one per line, optional "phone,name" format)
      let manual_contacts: { phone: string; name?: string }[] | null = null;
      if (formData.audience_type === 'manual') {
        const lines = formData.manual_contacts
          .split('\n')
          .map((l) => l.trim())
          .filter((l) => l.length > 0);

        if (lines.length === 0) {
          alert('Please enter at least one phone number for manual contacts.');
          return;
        }

        manual_contacts = lines.map((line) => {
          const [phone, ...rest] = line.split(',');
          const name = rest.join(',').trim() || undefined;
          return { phone: phone.trim(), name };
        });
      }

      const payload = {
        name: formData.name,
        template_content: formData.template_content,
        audience_type: formData.audience_type,
        conference_id: formData.conference_id || null,
        branch_ids: formData.branch_ids?.length > 0 ? formData.branch_ids : null,
        session_ids: formData.session_ids?.length > 0 ? formData.session_ids : null,
        manual_contacts,
        config: {
          send_rate_per_second: parseFloat(formData.send_rate),
          sender_id: formData.sender_id || null
        },
        sms_provider: formData.sms_provider
      };

      const isEditing = !!editingCampaign;
      const url = isEditing
        ? `${API_BASE_URL}/sms-campaigns/${editingCampaign.id}`
        : `${API_BASE_URL}/sms-campaigns/`;
      const method = isEditing ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setShowCreateModal(false);
        setEditingCampaign(null);
        setFormData({
          name: '',
          template_content: '',
          audience_type: 'all',
          conference_id: '',
          branch_ids: [],
          session_ids: [],
          manual_contacts: '',
          sender_id: 'IMPACT2025',
          send_rate: '1',
          sms_provider: 'arkesel'
        });
        fetchCampaigns();
      } else {
        const error = await response.json();
        alert(error.detail || `Failed to ${isEditing ? 'update' : 'create'} campaign`);
      }
    } catch (error) {
      console.error(`Error ${editingCampaign ? 'updating' : 'creating'} campaign:`, error);
      alert(`Failed to ${editingCampaign ? 'update' : 'create'} campaign`);
    }
  };

  // Prepare campaign
  const handlePrepareCampaign = async (campaignId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/sms-campaigns/${campaignId}/prepare`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Prepared ${data.message_count} messages`);
        fetchCampaigns();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to prepare campaign');
      }
    } catch (error) {
      console.error('Error preparing campaign:', error);
    }
  };

  // Fetch campaign messages
  const fetchCampaignMessages = async (campaignId: string, status?: string) => {
    setMessagesLoading(true);
    try {
      const statusParam = status ? `?status=${status}&limit=1000` : '?limit=1000';
      const response = await fetch(`${API_BASE_URL}/sms-campaigns/${campaignId}/messages${statusParam}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch campaign messages');
      }

      const data = await response.json();
      setCampaignMessages(data.messages || []);
    } catch (error) {
      console.error('Error fetching messages:', error);
      setCampaignMessages([]);
    } finally {
      setMessagesLoading(false);
    }
  };

  // Start campaign
  const handleStartCampaign = async (campaignId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/sms-campaigns/${campaignId}/start`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        fetchCampaigns();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to start campaign');
      }
    } catch (error) {
      console.error('Error starting campaign:', error);
    }
  };

  // Pause campaign
  const handlePauseCampaign = async (campaignId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/sms-campaigns/${campaignId}/pause`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        fetchCampaigns();
      }
    } catch (error) {
      console.error('Error pausing campaign:', error);
    }
  };

  // Cancel campaign
  const handleCancelCampaign = async (campaignId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/sms-campaigns/${campaignId}/cancel`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        fetchCampaigns();
      }
    } catch (error) {
      console.error('Error cancelling campaign:', error);
    }
  };

  // Open delete confirmation dialog
  const openDeleteDialog = (campaign: SMSCampaign) => {
    setDeleteDialog({
      isOpen: true,
      campaignId: campaign.id,
      campaignName: campaign.name,
      isLoading: false,
    });
  };

  // Handle confirmed delete
  const handleDeleteCampaign = async () => {
    if (!deleteDialog.campaignId) return;

    setDeleteDialog(prev => ({ ...prev, isLoading: true }));

    try {
      const response = await fetch(`${API_BASE_URL}/sms-campaigns/${deleteDialog.campaignId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        setDeleteDialog({ isOpen: false, campaignId: null, campaignName: '', isLoading: false });
        fetchCampaigns();
      } else {
        setDeleteDialog(prev => ({ ...prev, isLoading: false }));
      }
    } catch (error) {
      console.error('Error deleting campaign:', error);
      setDeleteDialog(prev => ({ ...prev, isLoading: false }));
    }
  };

  // Duplicate campaign (run again)
  const handleDuplicateCampaign = async (campaignId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/sms-campaigns/${campaignId}/duplicate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const newCampaign = await response.json();
        alert(`Campaign duplicated! "${newCampaign.name}" is ready to send.`);
        fetchCampaigns();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to duplicate campaign');
      }
    } catch (error) {
      console.error('Error duplicating campaign:', error);
      alert('Failed to duplicate campaign');
    }
  };

  // Fetch recipient count based on audience selection
  const fetchRecipientCount = async () => {
    if (!showCreateModal) return;

    setFetchingCount(true);

    try {
      // Count manual contacts from textarea
      if (formData.audience_type === 'manual') {
        const lines = formData.manual_contacts
          .split('\n')
          .map((l) => l.trim())
          .filter((l) => l.length > 0);
        setRecipientCount(lines.length);
        setFetchingCount(false);
        return;
      }

      // Build query params based on audience type
      const params = new URLSearchParams();
      params.append('audience_type', formData.audience_type);
      if (formData.conference_id) params.append('conference_id', formData.conference_id);
      if (formData.branch_ids?.length > 0) {
        formData.branch_ids.forEach(id => params.append('branch_ids', id));
      }
      if (formData.session_ids?.length > 0) {
        formData.session_ids.forEach(id => params.append('session_ids', id));
      }

      const response = await fetch(`${API_BASE_URL}/sms-campaigns/count-recipients?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setRecipientCount(data.count || 0);
        setSampleRecipients(data.sample || []);
      } else {
        setRecipientCount(null);
        setSampleRecipients([]);
      }
    } catch (error) {
      console.error('Error fetching recipient count:', error);
      setRecipientCount(null);
    } finally {
      setFetchingCount(false);
    }
  };

  // Fetch all recipients for preview
  const fetchAllRecipients = async () => {
    setLoadingAllRecipients(true);
    setShowAllRecipientsModal(true);

    try {
      // Build query params based on audience type
      const params = new URLSearchParams();
      params.append('audience_type', formData.audience_type);
      if (formData.conference_id) params.append('conference_id', formData.conference_id);
      if (formData.branch_ids?.length > 0) {
        formData.branch_ids.forEach(id => params.append('branch_ids', id));
      }
      if (formData.session_ids?.length > 0) {
        formData.session_ids.forEach(id => params.append('session_ids', id));
      }

      const response = await fetch(`${API_BASE_URL}/sms-campaigns/preview-recipients?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAllRecipients(data.recipients || []);
      } else {
        setAllRecipients([]);
        alert('Failed to load recipients');
      }
    } catch (error) {
      console.error('Error fetching all recipients:', error);
      setAllRecipients([]);
      alert('Failed to load recipients');
    } finally {
      setLoadingAllRecipients(false);
    }
  };

  // Fetch recipient count when audience selection changes
  useEffect(() => {
    if (showCreateModal) {
      fetchRecipientCount();
    } else {
      setRecipientCount(null);
      setSampleRecipients([]);
    }
  }, [
    showCreateModal,
    formData.audience_type,
    formData.conference_id,
    formData.branch_ids,
    formData.session_ids,
    formData.manual_contacts
  ]);

  // Status badge
  const getStatusBadge = (status: string) => {
    const statusStyles: Record<string, string> = {
      draft: 'bg-gray-100 text-gray-800',
      scheduled: 'bg-blue-100 text-blue-800',
      running: 'bg-green-100 text-green-800',
      paused: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-emerald-100 text-emerald-800',
      failed: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-800'
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusStyles[status] || statusStyles.draft}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <MessageSquare className="h-6 w-6 text-indigo-600" />
              SMS Campaigns
            </h1>
            <p className="text-gray-600 mt-1">
              Send bulk SMS messages to church members
            </p>
          </div>

          <button
            onClick={() => {
              setEditingCampaign(null);
              setFormData({
                name: '',
                template_content: '',
                audience_type: 'all',
                conference_id: '',
                branch_ids: [],
                session_ids: [],
                manual_contacts: '',
                sender_id: '',
                send_rate: '1',
                sms_provider: 'arkesel'
              });
              setShowCreateModal(true);
            }}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" />
            Create Campaign
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-500 text-sm">Total Campaigns</span>
              <MessageSquare className="h-5 w-5 text-gray-400" />
            </div>
            <div className="text-2xl font-bold mt-2">{campaigns.length}</div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-500 text-sm">Active</span>
              <Play className="h-5 w-5 text-green-500" />
            </div>
            <div className="text-2xl font-bold mt-2">
              {campaigns.filter(c => c.status === 'running').length}
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-500 text-sm">Messages Sent</span>
              <Send className="h-5 w-5 text-blue-500" />
            </div>
            <div className="text-2xl font-bold mt-2">
              {campaigns.reduce((sum, c) => sum + c.progress.sent, 0).toLocaleString()}
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-500 text-sm">Total Cost</span>
              <Church className="h-5 w-5 text-purple-500" />
            </div>
            <div className="text-2xl font-bold mt-2">
              ${campaigns.reduce((sum, c) => sum + c.total_cost, 0).toFixed(2)}
            </div>
          </div>
        </div>

        {/* Search and Filter */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <input
              type="text"
              placeholder="Search campaigns..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">All Status</option>
            <option value="draft">Draft</option>
            <option value="running">Running</option>
            <option value="paused">Paused</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>

          <button
            onClick={fetchCampaigns}
            className="p-2 border border-gray-200 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw className="h-5 w-5 text-gray-600" />
          </button>
        </div>

        {/* Campaigns List */}
        {filteredCampaigns.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-8 text-center">
            <MessageSquare className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No SMS campaigns yet</h3>
            <p className="text-gray-500 mb-4">
              Create your first campaign to start communicating with members.
            </p>
            <button
              onClick={() => {
                setEditingCampaign(null);
                setFormData({
                  name: '',
                  template_content: '',
                  audience_type: 'all',
                  conference_id: '',
                  branch_ids: [],
                  session_ids: [],
                  manual_contacts: '',
                  sender_id: '',
                  send_rate: '1',
                  sms_provider: 'arkesel'
                });
                setShowCreateModal(true);
              }}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              <Plus className="h-4 w-4" />
              Create First Campaign
            </button>
          </div>
        ) : (
          <>
            {/* Desktop Table View */}
            <div className="hidden md:block bg-white rounded-lg shadow-sm overflow-hidden">
              <table className="w-full">
                <thead className="bg-gradient-to-r from-purple-50 to-blue-50 border-b-2 border-purple-200">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Campaign</th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Progress</th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Sent</th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Cost</th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Created</th>
                    <th className="px-6 py-4 text-right text-xs font-bold text-purple-900 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredCampaigns.map((campaign) => (
                    <tr
                      key={campaign.id}
                      className="hover:bg-gradient-to-r hover:from-purple-50 hover:to-blue-50 transition-all duration-200 cursor-pointer group"
                      onClick={() => {
                        setSelectedCampaign(campaign);
                        setShowDetailsModal(true);
                      }}
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <MessageSquare className="h-5 w-5 text-indigo-600" />
                          <div>
                            <div className="font-medium text-gray-900">{campaign.name}</div>
                            <div className="text-xs text-gray-500 truncate max-w-[200px]">
                              {campaign.template_content.substring(0, 50)}...
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">{getStatusBadge(campaign.status)}</td>
                      <td className="px-6 py-4">
                        <div className="w-24">
                          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-indigo-600 rounded-full"
                              style={{
                                width: `${campaign.progress.total_recipients > 0
                                  ? ((campaign.progress.sent + campaign.progress.failed) / campaign.progress.total_recipients) * 100
                                  : 0}%`
                              }}
                            ></div>
                          </div>
                          <span className="text-xs text-gray-500 mt-1 block">
                            {campaign.progress.sent}/{campaign.progress.total_recipients}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-green-600 font-medium">{campaign.progress.sent}</span>
                        {campaign.progress.failed > 0 && (
                          <span className="text-red-600 text-xs ml-1">({campaign.progress.failed} failed)</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-gray-600">${campaign.total_cost.toFixed(2)}</td>
                      <td className="px-6 py-4 text-gray-500 text-sm">
                        {new Date(campaign.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-end gap-1">
                          {/* Edit button - for draft/paused (edit in place) or completed/failed/cancelled (duplicate & edit) */}
                          {['draft', 'paused', 'completed', 'failed', 'cancelled'].includes(campaign.status) && (
                            <button
                              onClick={() => {
                                if (['completed', 'failed', 'cancelled'].includes(campaign.status)) {
                                  // For completed/failed/cancelled: duplicate first, then edit
                                  handleDuplicateCampaign(campaign.id);
                                } else {
                                  // For draft/paused: edit in place
                                  openEditModal(campaign);
                                }
                              }}
                              className="p-2 text-indigo-500 hover:text-indigo-700 hover:bg-indigo-50 rounded"
                              title={['completed', 'failed', 'cancelled'].includes(campaign.status) ? 'Duplicate & Edit' : 'Edit Campaign'}
                            >
                              <Edit className="h-4 w-4" />
                            </button>
                          )}

                          {/* Play/Run Again button for draft, paused, completed, failed, cancelled */}
                          {campaign.status === 'draft' && (
                            <button
                              onClick={() => handleStartCampaign(campaign.id)}
                              className="p-2 text-green-500 hover:text-green-700 hover:bg-green-50 rounded"
                              title="Start Campaign"
                            >
                              <Play className="h-4 w-4" />
                            </button>
                          )}

                          {campaign.status === 'paused' && (
                            <button
                              onClick={() => handleStartCampaign(campaign.id)}
                              className="p-2 text-green-500 hover:text-green-700 hover:bg-green-50 rounded"
                              title="Resume Campaign"
                            >
                              <Play className="h-4 w-4" />
                            </button>
                          )}

                          {['completed', 'failed', 'cancelled'].includes(campaign.status) && (
                            <button
                              onClick={async () => {
                                const newCampaign = await fetch(`${API_BASE_URL}/sms-campaigns/${campaign.id}/duplicate`, {
                                  method: 'POST',
                                  headers: { 'Authorization': `Bearer ${token}` }
                                });
                                if (newCampaign.ok) {
                                  const duplicated = await newCampaign.json();
                                  // Start the duplicated campaign immediately
                                  await handleStartCampaign(duplicated.id);
                                }
                              }}
                              className="p-2 text-green-500 hover:text-green-700 hover:bg-green-50 rounded"
                              title="Run Again (Duplicate & Start)"
                            >
                              <Play className="h-4 w-4" />
                            </button>
                          )}

                          {campaign.status === 'running' && (
                            <button
                              onClick={() => handlePauseCampaign(campaign.id)}
                              className="p-2 text-yellow-500 hover:text-yellow-700 hover:bg-yellow-50 rounded"
                              title="Pause Campaign"
                            >
                              <Pause className="h-4 w-4" />
                            </button>
                          )}

                          {['draft', 'paused'].includes(campaign.status) && (
                            <button
                              onClick={() => openDeleteDialog(campaign)}
                              className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded"
                              title="Delete"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Card View */}
            <div className="md:hidden space-y-3">
              {filteredCampaigns.map((campaign) => (
                <div
                  key={campaign.id}
                  className="bg-white rounded-lg p-4 border shadow-sm"
                  onClick={() => {
                    setSelectedCampaign(campaign);
                    setShowDetailsModal(true);
                  }}
                >
                  {/* Header */}
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      <MessageSquare className="h-5 w-5 text-indigo-600 flex-shrink-0 mt-0.5" />
                      <div className="min-w-0 flex-1">
                        <h3 className="font-medium text-gray-900 truncate">{campaign.name}</h3>
                        <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                          {campaign.template_content.substring(0, 60)}...
                        </p>
                      </div>
                    </div>
                    {getStatusBadge(campaign.status)}
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-3">
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-indigo-600 rounded-full transition-all"
                        style={{
                          width: `${campaign.progress.total_recipients > 0
                            ? ((campaign.progress.sent + campaign.progress.failed) / campaign.progress.total_recipients) * 100
                            : 0}%`
                        }}
                      ></div>
                    </div>
                    <div className="flex justify-between items-center mt-1 text-xs text-gray-500">
                      <span>{campaign.progress.sent}/{campaign.progress.total_recipients} sent</span>
                      <span>{Math.round(campaign.progress.total_recipients > 0
                        ? ((campaign.progress.sent + campaign.progress.failed) / campaign.progress.total_recipients) * 100
                        : 0)}%</span>
                    </div>
                  </div>

                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 gap-3 mb-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Sent:</span>
                      <span className="font-medium text-green-600">{campaign.progress.sent}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Failed:</span>
                      <span className="font-medium text-red-600">{campaign.progress.failed}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Cost:</span>
                      <span className="font-medium text-gray-900">${campaign.total_cost.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Created:</span>
                      <span className="font-medium text-gray-900">
                        {new Date(campaign.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-3 border-t" onClick={(e) => e.stopPropagation()}>
                    {['draft', 'paused', 'completed', 'failed', 'cancelled'].includes(campaign.status) && (
                      <button
                        onClick={() => {
                          if (['completed', 'failed', 'cancelled'].includes(campaign.status)) {
                            handleDuplicateCampaign(campaign.id);
                          } else {
                            openEditModal(campaign);
                          }
                        }}
                        className="flex-1 min-h-[44px] flex items-center justify-center gap-2 px-3 py-2 text-sm text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors touch-manipulation"
                      >
                        <Edit className="h-4 w-4" />
                        <span>{['completed', 'failed', 'cancelled'].includes(campaign.status) ? 'Duplicate' : 'Edit'}</span>
                      </button>
                    )}

                    {(campaign.status === 'draft' || campaign.status === 'paused') && (
                      <button
                        onClick={() => handleStartCampaign(campaign.id)}
                        className="flex-1 min-h-[44px] flex items-center justify-center gap-2 px-3 py-2 text-sm text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors touch-manipulation"
                      >
                        <Play className="h-4 w-4" />
                        <span>{campaign.status === 'draft' ? 'Start' : 'Resume'}</span>
                      </button>
                    )}

                    {['completed', 'failed', 'cancelled'].includes(campaign.status) && (
                      <button
                        onClick={async () => {
                          const newCampaign = await fetch(`${API_BASE_URL}/sms-campaigns/${campaign.id}/duplicate`, {
                            method: 'POST',
                            headers: { 'Authorization': `Bearer ${token}` }
                          });
                          if (newCampaign.ok) {
                            const duplicated = await newCampaign.json();
                            await handleStartCampaign(duplicated.id);
                          }
                        }}
                        className="flex-1 min-h-[44px] flex items-center justify-center gap-2 px-3 py-2 text-sm text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors touch-manipulation"
                      >
                        <Play className="h-4 w-4" />
                        <span>Run Again</span>
                      </button>
                    )}

                    {campaign.status === 'running' && (
                      <button
                        onClick={() => handlePauseCampaign(campaign.id)}
                        className="flex-1 min-h-[44px] flex items-center justify-center gap-2 px-3 py-2 text-sm text-white bg-yellow-600 rounded-lg hover:bg-yellow-700 transition-colors touch-manipulation"
                      >
                        <Pause className="h-4 w-4" />
                        <span>Pause</span>
                      </button>
                    )}

                    {['draft', 'paused'].includes(campaign.status) && (
                      <button
                        onClick={() => openDeleteDialog(campaign)}
                        className="min-h-[44px] min-w-[44px] flex items-center justify-center px-3 py-2 text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors touch-manipulation"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Create Campaign Modal */}
      {showCreateModal && (
        <div
          className="fixed inset-0 bg-gradient-to-br from-gray-900/80 to-gray-950/90 backdrop-blur-sm flex items-end sm:items-center justify-center z-50 p-0 sm:p-4 animate-in fade-in duration-200"
          onClick={() => setShowCreateModal(false)}
        >
          <div
            className="bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl w-full sm:max-w-2xl h-full sm:h-auto sm:max-h-[90vh] overflow-hidden animate-in slide-in-from-bottom-4 duration-300"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header with Gradient */}
            <div className="relative bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 px-6 py-8">
              <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48cGF0dGVybiBpZD0iZ3JpZCIgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIj48cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLW9wYWNpdHk9IjAuMSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-20"></div>
              <div className="relative flex items-center gap-4">
                <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
                  <MessageSquare className="h-7 w-7 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white">
                    {editingCampaign ? 'Edit SMS Campaign' : 'Create SMS Campaign'}
                  </h2>
                  <p className="text-indigo-100 text-sm mt-1">
                    {editingCampaign ? 'Update campaign details and re-prepare messages' : 'Send targeted messages to your members'}
                  </p>
                </div>
              </div>
            </div>

            <div className="overflow-y-auto max-h-[calc(100vh-240px)] sm:max-h-[calc(90vh-180px)] px-4 sm:px-6 py-4 space-y-4">
              {/* Campaign Name */}
              <div className="group">
                <label className="block text-xs font-semibold text-gray-700 mb-1.5 flex items-center gap-1.5">
                  Campaign Name
                  <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Sunday Service Reminder"
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                />
              </div>

              {/* Audience Type */}
              <div className="group">
                <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                  Target Audience
                </label>
                <div className="relative">
                  <select
                    value={formData.audience_type}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        audience_type: e.target.value,
                        session_ids: [],
                      })
                    }
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all appearance-none bg-white cursor-pointer"
                  >
                    <option value="all">🌍 All Members</option>
                    <option value="conference">📋 Conference Registrants (All)</option>
                    <option value="checked_in">✅ Conference Registrants (Checked In Only)</option>
                    <option value="session">🎯 Session Attendees (Checked Into Sessions)</option>
                    <option value="branch">🏛️ Branch Members</option>
                    <option value="manual">✍️ Manual / Test Contacts</option>
                  </select>
                  <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
                {/* Recipient Count Display */}
                {recipientCount !== null && (
                  <div className="mt-2">
                    <div className="flex items-center gap-2 text-sm">
                      <Users className="h-4 w-4 text-indigo-600" />
                      <span className="font-medium text-indigo-600">
                        {recipientCount} {recipientCount === 1 ? 'recipient' : 'recipients'} will receive this message
                      </span>
                    </div>
                    {/* Sample Recipients Preview */}
                    {sampleRecipients.length > 0 && (
                      <div className="mt-2 pl-6">
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-xs text-gray-600">First {sampleRecipients.length} recipients:</p>
                          {recipientCount && recipientCount > 5 && (
                            <button
                              type="button"
                              onClick={fetchAllRecipients}
                              className="text-xs text-indigo-600 hover:text-indigo-800 font-medium underline"
                            >
                              View all {recipientCount}
                            </button>
                          )}
                        </div>
                        <ul className="text-xs text-gray-700 space-y-0.5">
                          {sampleRecipients.map((recipient, idx) => (
                            <li key={idx} className="flex items-center gap-2">
                              <span className="w-4 h-4 flex items-center justify-center bg-indigo-100 text-indigo-600 rounded-full text-[10px] font-semibold">
                                {idx + 1}
                              </span>
                              <span className="font-medium">{recipient.name}</span>
                              <span className="text-gray-500">•</span>
                              <span className="text-gray-600">{recipient.phone}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
                {fetchingCount && (
                  <div className="mt-2 flex items-center gap-2 text-sm text-gray-500">
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Counting recipients...</span>
                  </div>
                )}
              </div>

              {/* Conference Selection */}
              {(formData.audience_type === 'conference' || formData.audience_type === 'checked_in' || formData.audience_type === 'session') && (
                <div className="group">
                  <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                    Select Conference
                    {conferences.length > 0 && (
                      <span className="text-xs text-gray-500 ml-2">({conferences.length} available)</span>
                    )}
                  </label>
                  <select
                    value={formData.conference_id}
                    onChange={(e) => setFormData({ ...formData, conference_id: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  >
                    <option value="">
                      {conferences.length === 0 ? 'Loading conferences...' : 'Choose a conference...'}
                    </option>
                    {conferences.map((conf) => (
                      <option key={conf.id} value={conf.id}>{conf.name}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* Session Selection */}
              {formData.audience_type === 'session' && formData.conference_id && (
                <div className="group">
                  <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                    Select Sessions
                    <span className="text-xs text-gray-500 ml-2">(Select one or more)</span>
                  </label>
                  <div className="space-y-2">
                    {/* Search Filter */}
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                      <input
                        type="text"
                        placeholder="Search sessions..."
                        value={sessionSearch}
                        onChange={(e) => setSessionSearch(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    {/* Session List */}
                    <div className="border border-gray-300 rounded-lg p-2.5 max-h-48 overflow-y-auto space-y-1.5">
                      {sessions.length === 0 ? (
                        <p className="text-xs text-gray-500">No sessions found for this conference</p>
                      ) : (
                        sessions
                          .filter((session) =>
                            `${session.day_label} ${session.name}`.toLowerCase().includes(sessionSearch.toLowerCase())
                          )
                          .map((session) => (
                            <label key={session.id} className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 px-2 py-1 rounded transition-colors">
                              <input
                                type="checkbox"
                                checked={formData.session_ids?.includes(session.id) || false}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setFormData({ ...formData, session_ids: [...(formData.session_ids || []), session.id] });
                                  } else {
                                    setFormData({ ...formData, session_ids: (formData.session_ids || []).filter(id => id !== session.id) });
                                  }
                                }}
                                className="w-3.5 h-3.5 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500"
                              />
                              <span className="text-xs text-gray-700">
                                {session.day_label} - {session.name}
                              </span>
                            </label>
                          ))
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Branch Selection */}
              {formData.audience_type === 'branch' && (
                <div className="group">
                  <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                    Select Branches
                    <span className="text-xs text-gray-500 ml-2">(Select one or more)</span>
                  </label>
                  <div className="space-y-2">
                    {/* Search Filter */}
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                      <input
                        type="text"
                        placeholder="Search branches..."
                        value={branchSearch}
                        onChange={(e) => setBranchSearch(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    {/* Branch List */}
                    <div className="border border-gray-300 rounded-lg p-2.5 max-h-48 overflow-y-auto space-y-1.5">
                      {branches.length === 0 ? (
                        <p className="text-xs text-gray-500">No branches found</p>
                      ) : (
                        branches
                          .filter((branch) =>
                            branch.name.toLowerCase().includes(branchSearch.toLowerCase())
                          )
                          .map((branch) => (
                            <label
                              key={branch.id}
                              className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 px-2 py-1 rounded transition-colors"
                            >
                              <input
                                type="checkbox"
                                checked={formData.branch_ids?.includes(branch.id) || false}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setFormData({
                                      ...formData,
                                      branch_ids: [...(formData.branch_ids || []), branch.id],
                                    });
                                  } else {
                                    setFormData({
                                      ...formData,
                                      branch_ids: (formData.branch_ids || []).filter((id) => id !== branch.id),
                                    });
                                  }
                                }}
                                className="w-3.5 h-3.5 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500"
                              />
                              <span className="text-xs text-gray-700">{branch.name}</span>
                            </label>
                          ))
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Message Template */}
              <div className="group">
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold text-gray-700 flex items-center gap-1.5">
                    Message Template
                    <span className="text-red-500">*</span>
                  </label>
                  <span className={`text-xs font-medium ${formData.template_content.length > 160 ? 'text-red-600' : 'text-gray-500'}`}>
                    {formData.template_content.length}/160
                  </span>
                </div>
                <textarea
                  value={formData.template_content}
                  onChange={(e) => setFormData({ ...formData, template_content: e.target.value })}
                  placeholder="Dear {{name}}, you are reminded of tomorrow's service at 9am. God bless you!"
                  rows={3}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all resize-none"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Use {'{{name}}'}, {'{{phone}}'} for personalization. Max 160 chars per SMS segment.
                  {formData.template_content.length > 160 && (
                    <span className="text-red-600 font-medium ml-1">
                      ({Math.ceil(formData.template_content.length / 160)} SMS segments)
                    </span>
                  )}
                </p>
              </div>

              {/* Sender ID */}
              <div className="group">
                <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                  Sender ID
                  <span className="text-xs text-gray-500 ml-2 font-normal">(Max 11 characters)</span>
                </label>
                <div className="flex gap-2">
                  <select
                    value={formData.sender_id}
                    onChange={(e) => setFormData({ ...formData, sender_id: e.target.value })}
                    className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  >
                    <option value="IMPACT2025">IMPACT2025</option>
                    <option value="CHURCHFLOW">CHURCHFLOW</option>
                    <option value="REVIVAL25">REVIVAL25</option>
                    <option value="AWAKENING">AWAKENING</option>
                    <option value="custom">Custom...</option>
                  </select>
                  {formData.sender_id === 'custom' && (
                    <input
                      type="text"
                      maxLength={11}
                      placeholder="Custom sender ID"
                      onChange={(e) => setFormData({ ...formData, sender_id: e.target.value.toUpperCase() })}
                      className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all uppercase"
                    />
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  The name that appears as the sender. Arkesel allows any alphanumeric sender ID (up to 11 chars).
                </p>
              </div>

              {/* SMS Provider */}
              <div className="group">
                <label className="block text-xs font-semibold text-gray-700 mb-1.5">SMS Provider</label>
                <select
                  value={formData.sms_provider}
                  onChange={(e) => setFormData({ ...formData, sms_provider: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                >
                  <option value="arkesel">Arkesel (Ghana - Default)</option>
                  <option value="hubtel">Hubtel (Ghana)</option>
                  <option value="custom_http">Custom HTTP/API</option>
                  <option value="twilio">Twilio</option>
                  <option value="messagebird">MessageBird</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Arkesel is the default provider and matches session SMS. Ghana providers (Arkesel, Hubtel) are recommended for local delivery.
                </p>
              </div>

              {/* Send Rate */}
              <div className="group">
                <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                  Send Rate (messages per second)
                  <span className="text-xs text-gray-500 ml-2 font-normal">(0.1 - 10)</span>
                </label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    min="0.1"
                    max="10"
                    step="0.1"
                    value={formData.send_rate}
                    onChange={(e) => {
                      const value = parseFloat(e.target.value);
                      if (value >= 0.1 && value <= 10) {
                        setFormData({ ...formData, send_rate: e.target.value });
                      }
                    }}
                    className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  />
                  <select
                    value={formData.send_rate}
                    onChange={(e) => setFormData({ ...formData, send_rate: e.target.value })}
                    className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  >
                    <option value="0.5">0.5 - Very Slow (30/min)</option>
                    <option value="1">1 - Conservative (60/min)</option>
                    <option value="2">2 - Recommended (120/min)</option>
                    <option value="3">3 - Standard (180/min)</option>
                    <option value="5">5 - Fast (300/min)</option>
                    <option value="8">8 - High Volume (480/min)</option>
                    <option value="10">10 - Maximum (600/min)</option>
                  </select>
                </div>
                <div className="mt-2 space-y-1">
                  <p className="text-xs text-gray-600">
                    <span className="font-semibold">How many SMS per second to send:</span>
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                    <div className="bg-green-50 border border-green-200 rounded px-2 py-1.5">
                      <span className="font-semibold text-green-800">1-2 SMS/sec:</span>
                      <span className="text-green-700 block">Safe for testing & first campaigns</span>
                    </div>
                    <div className="bg-blue-50 border border-blue-200 rounded px-2 py-1.5">
                      <span className="font-semibold text-blue-800">3-5 SMS/sec:</span>
                      <span className="text-blue-700 block">Standard production rate</span>
                    </div>
                    <div className="bg-orange-50 border border-orange-200 rounded px-2 py-1.5">
                      <span className="font-semibold text-orange-800">8-10 SMS/sec:</span>
                      <span className="text-orange-700 block">High volume (test first!)</span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1.5">
                    Higher rates send faster but may trigger provider throttling. Start with 1-2 for new campaigns.
                  </p>
                </div>
              </div>

              {/* Manual Contacts (for testing) */}
              {formData.audience_type === 'manual' && (
                <div className="group">
                  <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                    Manual Contacts (one per line)
                  </label>
                  <textarea
                    value={formData.manual_contacts}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        manual_contacts: e.target.value,
                      })
                    }
                    placeholder={`Example:\n0244123456, John Doe\n+233244123456, Jane\n0244000000`}
                    rows={3}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all resize-none"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Use this for test sends or small manual groups. Format each line as
                    <span className="font-mono"> phone</span> or
                    <span className="font-mono"> phone,name</span>.
                  </p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="sticky bottom-0 bg-gradient-to-t from-gray-50 to-white border-t border-gray-200 px-4 sm:px-6 py-4 flex flex-col sm:flex-row justify-between items-stretch sm:items-center gap-3">
              <p className="text-xs text-gray-500 text-center sm:text-left">
                All fields marked with <span className="text-red-500">*</span> are required
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingCampaign(null);
                  }}
                  className="flex-1 sm:flex-none min-h-[44px] px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 font-medium touch-manipulation"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveCampaign}
                  className="flex-1 sm:flex-none min-h-[44px] px-4 py-2 text-sm bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 font-medium shadow-md shadow-indigo-500/30 hover:shadow-lg hover:shadow-indigo-500/40 flex items-center justify-center gap-2 touch-manipulation"
                >
                  <Send className="w-4 h-4" />
                  <span>{editingCampaign ? 'Update Campaign' : 'Create Campaign'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Campaign Analytics Modal */}
      {showDetailsModal && selectedCampaign && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4">
          <div className="bg-white rounded-t-2xl sm:rounded-lg w-full sm:max-w-5xl h-full sm:h-auto sm:max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="p-6 border-b bg-gradient-to-r from-indigo-600 to-purple-600">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <MessageSquare className="h-6 w-6 text-white" />
                  <div>
                    <h2 className="text-xl font-bold text-white">{selectedCampaign.name}</h2>
                    <p className="text-indigo-100 text-sm">Campaign Analytics & Details</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setShowDetailsModal(false);
                    setSelectedCampaign(null);
                    setAnalyticsTab('overview');
                  }}
                  className="text-white hover:text-gray-200"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
            </div>

            {/* Tabs */}
            <div className="border-b bg-gray-50 overflow-x-auto">
              <div className="flex gap-1 px-4 sm:px-6 min-w-max">
                <button
                  onClick={() => setAnalyticsTab('overview')}
                  className={`px-3 sm:px-4 py-3 text-xs sm:text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                    analyticsTab === 'overview'
                      ? 'border-indigo-600 text-indigo-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Overview
                </button>
                <button
                  onClick={() => setAnalyticsTab('successful')}
                  className={`px-3 sm:px-4 py-3 text-xs sm:text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                    analyticsTab === 'successful'
                      ? 'border-indigo-600 text-indigo-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="hidden sm:inline">Successful</span>
                    <span className="sm:hidden">Sent</span>
                    <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                      {selectedCampaign.progress.sent}
                    </span>
                  </div>
                </button>
                <button
                  onClick={() => setAnalyticsTab('failed')}
                  className={`px-3 sm:px-4 py-3 text-xs sm:text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                    analyticsTab === 'failed'
                      ? 'border-indigo-600 text-indigo-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    Failed
                    <span className="px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded-full">
                      {selectedCampaign.progress.failed}
                    </span>
                  </div>
                </button>
                <button
                  onClick={() => setAnalyticsTab('all')}
                  className={`px-3 sm:px-4 py-3 text-xs sm:text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                    analyticsTab === 'all'
                      ? 'border-indigo-600 text-indigo-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="hidden sm:inline">All Messages</span>
                    <span className="sm:hidden">All</span>
                    <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded-full">
                      {selectedCampaign.progress.total_recipients}
                    </span>
                  </div>
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6">
              {/* Overview Tab */}
              {analyticsTab === 'overview' && (
                <div className="space-y-6">
                  {/* Status and Progress */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <label className="text-sm text-gray-500 font-medium">Status</label>
                      <div className="mt-2">{getStatusBadge(selectedCampaign.status)}</div>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <label className="text-sm text-gray-500 font-medium">Provider</label>
                      <div className="mt-2 capitalize font-medium text-gray-900">
                        {selectedCampaign.sms_provider.replace('_', ' ')}
                      </div>
                    </div>
                  </div>

                  {/* Progress */}
                  <div className="bg-gradient-to-br from-indigo-50 to-purple-50 p-6 rounded-lg">
                    <label className="text-sm text-gray-700 font-semibold mb-3 block">Campaign Progress</label>
                    <div className="h-4 bg-white rounded-full overflow-hidden shadow-inner mb-4">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                        style={{
                          width: `${selectedCampaign.progress.total_recipients > 0
                            ? ((selectedCampaign.progress.sent + selectedCampaign.progress.failed) / selectedCampaign.progress.total_recipients) * 100
                            : 0}%`
                        }}
                      ></div>
                    </div>
                    <div className="grid grid-cols-4 gap-3">
                      <div className="bg-white p-3 rounded-lg text-center">
                        <div className="text-2xl font-bold text-gray-900">{selectedCampaign.progress.total_recipients}</div>
                        <div className="text-xs text-gray-500 font-medium">Total</div>
                      </div>
                      <div className="bg-white p-3 rounded-lg text-center">
                        <div className="text-2xl font-bold text-green-600">{selectedCampaign.progress.sent}</div>
                        <div className="text-xs text-gray-500 font-medium">Sent</div>
                      </div>
                      <div className="bg-white p-3 rounded-lg text-center">
                        <div className="text-2xl font-bold text-red-600">{selectedCampaign.progress.failed}</div>
                        <div className="text-xs text-gray-500 font-medium">Failed</div>
                      </div>
                      <div className="bg-white p-3 rounded-lg text-center">
                        <div className="text-2xl font-bold text-yellow-600">{selectedCampaign.progress.pending}</div>
                        <div className="text-xs text-gray-500 font-medium">Pending</div>
                      </div>
                    </div>
                  </div>

                  {/* Message Template */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <label className="text-sm text-gray-700 font-semibold mb-2 block">Message Template</label>
                    <div className="bg-white p-4 rounded border border-gray-200">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{selectedCampaign.template_content}</p>
                    </div>
                  </div>

                  {/* Cost and Timing */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <label className="text-sm text-gray-500 font-medium">Total Cost</label>
                      <div className="text-xl font-bold mt-2 text-gray-900">${selectedCampaign.total_cost.toFixed(2)}</div>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <label className="text-sm text-gray-500 font-medium">Created</label>
                      <div className="mt-2 text-sm text-gray-700">
                        {new Date(selectedCampaign.created_at).toLocaleString()}
                      </div>
                    </div>
                    {selectedCampaign.started_at && (
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <label className="text-sm text-gray-500 font-medium">Started</label>
                        <div className="mt-2 text-sm text-gray-700">
                          {new Date(selectedCampaign.started_at).toLocaleString()}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Successful/Failed/All Messages Tabs */}
              {analyticsTab !== 'overview' && (
                <div>
                  {messagesLoading ? (
                    <div className="flex items-center justify-center py-12">
                      <RefreshCw className="h-8 w-8 text-indigo-600 animate-spin" />
                    </div>
                  ) : campaignMessages.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                      <AlertCircle className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                      <p>No {analyticsTab} messages found</p>
                    </div>
                  ) : (
                    <>
                      {/* Desktop Table View */}
                      <div className="hidden md:block overflow-hidden rounded-lg border border-gray-200">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gradient-to-r from-purple-50 to-blue-50 border-b-2 border-purple-200">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Recipient</th>
                              <th className="px-4 py-3 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Phone</th>
                              <th className="px-4 py-3 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Status</th>
                              {analyticsTab === 'failed' && (
                                <th className="px-4 py-3 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Error</th>
                              )}
                              <th className="px-4 py-3 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Time</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-100">
                            {campaignMessages.map((msg, idx) => (
                              <tr key={msg.id || idx} className="hover:bg-gray-50">
                                <td className="px-4 py-3 text-sm">
                                  <div className="font-medium text-gray-900">{msg.recipient_name || 'Unknown'}</div>
                                  {msg.recipient_email && (
                                    <div className="text-xs text-gray-500">{msg.recipient_email}</div>
                                  )}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-700">{msg.recipient_phone}</td>
                                <td className="px-4 py-3 text-sm">
                                  {msg.status === 'sent' && (
                                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                                      <CheckCircle className="h-3 w-3 mr-1" />
                                      Sent
                                    </span>
                                  )}
                                  {msg.status === 'failed' && (
                                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
                                      <XCircle className="h-3 w-3 mr-1" />
                                      Failed
                                    </span>
                                  )}
                                  {msg.status === 'pending' && (
                                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700">
                                      <Clock className="h-3 w-3 mr-1" />
                                      Pending
                                    </span>
                                  )}
                                  {msg.status === 'delivered' && (
                                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                                      <CheckCircle className="h-3 w-3 mr-1" />
                                      Delivered
                                    </span>
                                  )}
                                </td>
                                {analyticsTab === 'failed' && (
                                  <td className="px-4 py-3 text-sm text-red-600">
                                    <div className="max-w-xs truncate" title={msg.error_message}>
                                      {msg.error_message || 'Unknown error'}
                                    </div>
                                  </td>
                                )}
                                <td className="px-4 py-3 text-sm text-gray-500">
                                  {msg.sent_at && new Date(msg.sent_at).toLocaleString()}
                                  {msg.failed_at && new Date(msg.failed_at).toLocaleString()}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {/* Mobile Card View */}
                      <div className="md:hidden space-y-3">
                        {campaignMessages.map((msg, idx) => (
                          <div key={msg.id || idx} className="bg-white rounded-lg p-4 border shadow-sm">
                            {/* Header */}
                            <div className="flex justify-between items-start mb-3">
                              <div className="flex-1 min-w-0">
                                <h4 className="font-medium text-gray-900 truncate">{msg.recipient_name || 'Unknown'}</h4>
                                <p className="text-sm text-gray-600 mt-0.5">{msg.recipient_phone}</p>
                                {msg.recipient_email && (
                                  <p className="text-xs text-gray-500 mt-0.5">{msg.recipient_email}</p>
                                )}
                              </div>
                              <div className="ml-2 flex-shrink-0">
                                {msg.status === 'sent' && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                                    <CheckCircle className="h-3 w-3 mr-1" />
                                    Sent
                                  </span>
                                )}
                                {msg.status === 'failed' && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
                                    <XCircle className="h-3 w-3 mr-1" />
                                    Failed
                                  </span>
                                )}
                                {msg.status === 'pending' && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700">
                                    <Clock className="h-3 w-3 mr-1" />
                                    Pending
                                  </span>
                                )}
                                {msg.status === 'delivered' && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                                    <CheckCircle className="h-3 w-3 mr-1" />
                                    Delivered
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Details */}
                            <div className="space-y-2 text-sm pt-3 border-t">
                              {analyticsTab === 'failed' && msg.error_message && (
                                <div>
                                  <span className="text-gray-500">Error:</span>
                                  <p className="text-red-600 mt-1">{msg.error_message}</p>
                                </div>
                              )}
                              <div className="flex justify-between">
                                <span className="text-gray-500">Time:</span>
                                <span className="text-gray-900">
                                  {msg.sent_at && new Date(msg.sent_at).toLocaleString('en-US', {
                                    month: 'short',
                                    day: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                  {msg.failed_at && new Date(msg.failed_at).toLocaleString('en-US', {
                                    month: 'short',
                                    day: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>

            {/* Footer Actions */}
            <div className="p-4 sm:p-6 border-t bg-gray-50 flex flex-col sm:flex-row justify-between items-stretch sm:items-center gap-3">
              <div className="flex flex-wrap gap-2">
                {['draft', 'paused', 'completed', 'failed', 'cancelled'].includes(selectedCampaign.status) && (
                  <button
                    onClick={() => {
                      setShowDetailsModal(false);
                      if (['completed', 'failed', 'cancelled'].includes(selectedCampaign.status)) {
                        handleDuplicateCampaign(selectedCampaign.id);
                      } else {
                        openEditModal(selectedCampaign);
                      }
                    }}
                    className="flex items-center justify-center gap-2 min-h-[44px] px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 touch-manipulation"
                  >
                    <Edit className="h-4 w-4" />
                    <span className="hidden sm:inline">{['completed', 'failed', 'cancelled'].includes(selectedCampaign.status) ? 'Duplicate & Edit' : 'Edit Campaign'}</span>
                    <span className="sm:hidden">Edit</span>
                  </button>
                )}

                {selectedCampaign.status === 'draft' && (
                  <button
                    onClick={() => {
                      setShowDetailsModal(false);
                      handleStartCampaign(selectedCampaign.id);
                    }}
                    className="flex items-center justify-center gap-2 min-h-[44px] px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 touch-manipulation"
                  >
                    <Play className="h-4 w-4" />
                    <span>Start</span>
                  </button>
                )}

                {selectedCampaign.status === 'running' && (
                  <button
                    onClick={() => {
                      setShowDetailsModal(false);
                      handlePauseCampaign(selectedCampaign.id);
                    }}
                    className="flex items-center justify-center gap-2 min-h-[44px] px-4 py-2 text-sm bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 touch-manipulation"
                  >
                    <Pause className="h-4 w-4" />
                    <span>Pause</span>
                  </button>
                )}

                {selectedCampaign.status === 'paused' && (
                  <button
                    onClick={() => {
                      setShowDetailsModal(false);
                      handleStartCampaign(selectedCampaign.id);
                    }}
                    className="flex items-center justify-center gap-2 min-h-[44px] px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 touch-manipulation"
                  >
                    <Play className="h-4 w-4" />
                    <span>Resume</span>
                  </button>
                )}

                {['completed', 'failed', 'cancelled'].includes(selectedCampaign.status) && (
                  <button
                    onClick={async () => {
                      setShowDetailsModal(false);
                      const newCampaignResponse = await fetch(`${API_BASE_URL}/sms-campaigns/${selectedCampaign.id}/duplicate`, {
                        method: 'POST',
                        headers: { 'Authorization': `Bearer ${token}` }
                      });
                      if (newCampaignResponse.ok) {
                        const duplicated = await newCampaignResponse.json();
                        // Start the duplicated campaign immediately
                        await handleStartCampaign(duplicated.id);
                      }
                    }}
                    className="flex items-center justify-center gap-2 min-h-[44px] px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 touch-manipulation"
                  >
                    <Play className="h-4 w-4" />
                    <span>Run Again</span>
                  </button>
                )}
              </div>

              <button
                onClick={() => {
                  setShowDetailsModal(false);
                  setSelectedCampaign(null);
                  setAnalyticsTab('overview');
                }}
                className="w-full sm:w-auto min-h-[44px] px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 touch-manipulation"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View All Recipients Modal */}
      {showAllRecipientsModal && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[60] p-4"
          onClick={() => setShowAllRecipientsModal(false)}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="bg-indigo-600 px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Users className="h-6 w-6 text-white" />
                <h3 className="text-lg font-semibold text-white">
                  All Recipients ({allRecipients.length})
                </h3>
              </div>
              <button
                onClick={() => setShowAllRecipientsModal(false)}
                className="text-white hover:text-gray-200"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
              {loadingAllRecipients ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="h-8 w-8 text-indigo-600 animate-spin" />
                  <span className="ml-3 text-gray-600">Loading recipients...</span>
                </div>
              ) : allRecipients.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  No recipients found
                </div>
              ) : (
                <div className="space-y-2">
                  {allRecipients.map((recipient, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      <span className="w-8 h-8 flex items-center justify-center bg-indigo-100 text-indigo-600 rounded-full text-sm font-semibold flex-shrink-0">
                        {idx + 1}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">{recipient.name}</p>
                        <p className="text-sm text-gray-600">{recipient.phone}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="bg-gray-50 px-6 py-4 flex justify-end border-t">
              <button
                onClick={() => setShowAllRecipientsModal(false)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, campaignId: null, campaignName: '', isLoading: false })}
        onConfirm={handleDeleteCampaign}
        title="Delete SMS Campaign"
        message="Are you sure you want to delete this SMS campaign? This action cannot be undone."
        itemName={deleteDialog.campaignName}
        confirmText="Delete Campaign"
        cancelText="Keep Campaign"
        variant="danger"
        isLoading={deleteDialog.isLoading}
      />
    </div>
  );
};

export default SMSCampaigns;
