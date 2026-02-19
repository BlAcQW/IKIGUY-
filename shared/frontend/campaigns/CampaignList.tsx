/**
 * Unified Campaign List Component
 *
 * Multi-channel campaign list supporting Voice, SMS, WhatsApp, and Email campaigns.
 * Works with the centralized campaign router.
 *
 * Usage:
 * ```tsx
 * import { CampaignList } from '@shared/frontend/campaigns/CampaignList';
 *
 * <CampaignList
 *   apiBaseUrl="https://api.example.com"
 *   authToken={token}
 *   organizationId={orgId}
 *   onCampaignClick={(campaign) => handleView(campaign)}
 *   onLaunch={(id) => handleLaunch(id)}
 * />
 * ```
 */

import React, { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  BarChart3,
  Mail,
  MessageSquare,
  Phone,
  Send,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Plus,
  Filter
} from 'lucide-react';

// Types
export type CampaignType = 'voice' | 'sms' | 'whatsapp' | 'email';
export type CampaignStatus = 'draft' | 'scheduled' | 'running' | 'paused' | 'completed' | 'cancelled' | 'failed';

export interface Campaign {
  id: string;
  name: string;
  campaign_type: CampaignType;
  status: CampaignStatus;
  target_count: number;
  sent_count: number;
  delivered_count: number;
  failed_count: number;
  total_cost: number;
  currency: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface CampaignListProps {
  apiBaseUrl: string;
  authToken: string;
  organizationId?: string;
  onCampaignClick?: (campaign: Campaign) => void;
  onLaunch?: (campaignId: string) => void;
  onCreateNew?: () => void;
}

export const CampaignList: React.FC<CampaignListProps> = ({
  apiBaseUrl,
  authToken,
  organizationId,
  onCampaignClick,
  onLaunch,
  onCreateNew
}) => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<CampaignType | 'all'>('all');
  const [filterStatus, setFilterStatus] = useState<CampaignStatus | 'all'>('all');

  useEffect(() => {
    fetchCampaigns();
  }, [filterType, filterStatus]);

  const fetchCampaigns = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterType !== 'all') params.append('campaign_type', filterType);
      if (filterStatus !== 'all') params.append('status', filterStatus);

      const response = await fetch(
        `${apiBaseUrl}/api/v1/campaigns?${params.toString()}`,
        {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

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

  const handleLaunchCampaign = async (campaignId: string) => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/campaigns/${campaignId}/launch`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        fetchCampaigns();
        if (onLaunch) onLaunch(campaignId);
      }
    } catch (error) {
      console.error('Error launching campaign:', error);
    }
  };

  const handlePauseCampaign = async (campaignId: string) => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/campaigns/${campaignId}/pause`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        fetchCampaigns();
      }
    } catch (error) {
      console.error('Error pausing campaign:', error);
    }
  };

  const getCampaignTypeIcon = (type: CampaignType) => {
    switch (type) {
      case 'voice': return <Phone className="h-4 w-4" />;
      case 'sms': return <MessageSquare className="h-4 w-4" />;
      case 'whatsapp': return <Send className="h-4 w-4" />;
      case 'email': return <Mail className="h-4 w-4" />;
    }
  };

  const getCampaignTypeColor = (type: CampaignType) => {
    switch (type) {
      case 'voice': return 'bg-purple-100 text-purple-800';
      case 'sms': return 'bg-blue-100 text-blue-800';
      case 'whatsapp': return 'bg-green-100 text-green-800';
      case 'email': return 'bg-orange-100 text-orange-800';
    }
  };

  const getStatusBadge = (status: CampaignStatus) => {
    const badges = {
      draft: { icon: Clock, color: 'bg-gray-100 text-gray-800' },
      scheduled: { icon: Clock, color: 'bg-yellow-100 text-yellow-800' },
      running: { icon: Play, color: 'bg-blue-100 text-blue-800' },
      paused: { icon: Pause, color: 'bg-orange-100 text-orange-800' },
      completed: { icon: CheckCircle, color: 'bg-green-100 text-green-800' },
      cancelled: { icon: XCircle, color: 'bg-gray-100 text-gray-800' },
      failed: { icon: AlertCircle, color: 'bg-red-100 text-red-800' }
    };

    const badge = badges[status];
    const Icon = badge.icon;

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${badge.color}`}>
        <Icon className="h-3 w-3" />
        {status}
      </span>
    );
  };

  const calculateProgress = (campaign: Campaign) => {
    if (campaign.target_count === 0) return 0;
    return Math.round(((campaign.sent_count + campaign.failed_count) / campaign.target_count) * 100);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with Filters */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Filter className="h-5 w-5 text-gray-400" />

          {/* Type Filter */}
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as CampaignType | 'all')}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="all">All Types</option>
            <option value="voice">Voice</option>
            <option value="sms">SMS</option>
            <option value="whatsapp">WhatsApp</option>
            <option value="email">Email</option>
          </select>

          {/* Status Filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as CampaignStatus | 'all')}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="all">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        {onCreateNew && (
          <button
            onClick={onCreateNew}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" />
            Create Campaign
          </button>
        )}
      </div>

      {/* Campaign List */}
      <div className="bg-white shadow-sm rounded-lg overflow-hidden">
        {campaigns.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No campaigns found. Create your first campaign to get started!
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Campaign
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Progress
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cost
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {campaigns.map((campaign) => (
                <tr
                  key={campaign.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => onCampaignClick?.(campaign)}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col">
                      <div className="text-sm font-medium text-gray-900">
                        {campaign.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {new Date(campaign.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getCampaignTypeColor(campaign.campaign_type)}`}>
                      {getCampaignTypeIcon(campaign.campaign_type)}
                      {campaign.campaign_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(campaign.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${calculateProgress(campaign)}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-600 font-medium">
                          {calculateProgress(campaign)}%
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">
                        {campaign.sent_count + campaign.failed_count} / {campaign.target_count}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {campaign.currency} {campaign.total_cost.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                      {campaign.status === 'draft' && (
                        <button
                          onClick={() => handleLaunchCampaign(campaign.id)}
                          className="text-green-600 hover:text-green-900"
                          title="Launch Campaign"
                        >
                          <Play className="h-5 w-5" />
                        </button>
                      )}
                      {campaign.status === 'running' && (
                        <button
                          onClick={() => handlePauseCampaign(campaign.id)}
                          className="text-orange-600 hover:text-orange-900"
                          title="Pause Campaign"
                        >
                          <Pause className="h-5 w-5" />
                        </button>
                      )}
                      <button
                        onClick={() => onCampaignClick?.(campaign)}
                        className="text-indigo-600 hover:text-indigo-900"
                        title="View Analytics"
                      >
                        <BarChart3 className="h-5 w-5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default CampaignList;
