/**
 * SMS Campaign Analytics Modal - Shared Component
 *
 * Reusable analytics dashboard for SMS campaigns across all apps.
 * Shows campaign overview, successful sends, failed messages, and all messages.
 *
 * Usage:
 * ```tsx
 * import { SMSCampaignAnalytics } from '@shared/frontend/sms-campaigns/SMS CampaignAnalytics';
 *
 * <SMSCampaignAnalytics
 *   campaign={selectedCampaign}
 *   isOpen={showModal}
 *   onClose={() => setShowModal(false)}
 *   apiBaseUrl="https://api.example.com"
 *   authToken={token}
 * />
 * ```
 */

import React, { useState, useEffect } from 'react';
import {
  X,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  AlertCircle,
  MessageSquare,
  Play,
  Pause,
  Edit,
  Copy
} from 'lucide-react';

// Types
export interface SMSCampaign {
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

export interface CampaignMessage {
  id: string;
  recipient_name: string;
  recipient_phone: string;
  recipient_email?: string;
  status: 'sent' | 'failed' | 'pending' | 'delivered';
  error_message?: string;
  sent_at?: string;
  failed_at?: string;
  delivered_at?: string;
  cost?: number;
}

export interface SMSCampaignAnalyticsProps {
  campaign: SMSCampaign | null;
  isOpen: boolean;
  onClose: () => void;
  apiBaseUrl: string;
  authToken: string;
  onAction?: (action: 'start' | 'pause' | 'edit' | 'duplicate', campaignId: string) => void;
}

type AnalyticsTab = 'overview' | 'successful' | 'failed' | 'all';

export const SMSCampaignAnalytics: React.FC<SMSCampaignAnalyticsProps> = ({
  campaign,
  isOpen,
  onClose,
  apiBaseUrl,
  authToken,
  onAction
}) => {
  const [activeTab, setActiveTab] = useState<AnalyticsTab>('overview');
  const [messages, setMessages] = useState<CampaignMessage[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch messages when tab changes
  useEffect(() => {
    if (isOpen && campaign && activeTab !== 'overview') {
      fetchMessages(activeTab);
    }
  }, [activeTab, isOpen, campaign?.id]);

  const fetchMessages = async (tab: AnalyticsTab) => {
    if (!campaign) return;

    setLoading(true);
    try {
      const statusMap: Record<string, string | undefined> = {
        'successful': 'sent',
        'failed': 'failed',
        'all': undefined
      };

      const status = statusMap[tab];
      const statusParam = status ? `?status=${status}&limit=1000` : '?limit=1000';

      const response = await fetch(
        `${apiBaseUrl}/sms-campaigns/${campaign.id}/messages${statusParam}`,
        {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const badges: Record<string, { bg: string; text: string; label: string }> = {
      draft: { bg: 'bg-gray-100', text: 'text-gray-700', label: 'Draft' },
      running: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Running' },
      paused: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Paused' },
      completed: { bg: 'bg-green-100', text: 'text-green-700', label: 'Completed' },
      failed: { bg: 'bg-red-100', text: 'text-red-700', label: 'Failed' },
      cancelled: { bg: 'bg-gray-100', text: 'text-gray-700', label: 'Cancelled' },
    };

    const badge = badges[status] || badges.draft;
    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  if (!isOpen || !campaign) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b bg-gradient-to-r from-indigo-600 to-purple-600">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <MessageSquare className="h-6 w-6 text-white" />
              <div>
                <h2 className="text-xl font-bold text-white">{campaign.name}</h2>
                <p className="text-indigo-100 text-sm">Campaign Analytics & Details</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 transition-colors"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b bg-gray-50">
          <div className="flex gap-1 px-6">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'overview'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('successful')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'successful'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <div className="flex items-center gap-2">
                Successful
                <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                  {campaign.progress.sent}
                </span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('failed')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'failed'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <div className="flex items-center gap-2">
                Failed
                <span className="px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded-full">
                  {campaign.progress.failed}
                </span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('all')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'all'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <div className="flex items-center gap-2">
                All Messages
                <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded-full">
                  {campaign.progress.total_recipients}
                </span>
              </div>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Status */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <label className="text-sm text-gray-500 font-medium">Status</label>
                  <div className="mt-2">{getStatusBadge(campaign.status)}</div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <label className="text-sm text-gray-500 font-medium">Provider</label>
                  <div className="mt-2 capitalize font-medium text-gray-900">
                    {campaign.sms_provider.replace('_', ' ')}
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
                      width: `${campaign.progress.total_recipients > 0
                        ? ((campaign.progress.sent + campaign.progress.failed) / campaign.progress.total_recipients) * 100
                        : 0}%`
                    }}
                  ></div>
                </div>
                <div className="grid grid-cols-4 gap-3">
                  <div className="bg-white p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-gray-900">{campaign.progress.total_recipients}</div>
                    <div className="text-xs text-gray-500 font-medium">Total</div>
                  </div>
                  <div className="bg-white p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-green-600">{campaign.progress.sent}</div>
                    <div className="text-xs text-gray-500 font-medium">Sent</div>
                  </div>
                  <div className="bg-white p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-red-600">{campaign.progress.failed}</div>
                    <div className="text-xs text-gray-500 font-medium">Failed</div>
                  </div>
                  <div className="bg-white p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-yellow-600">{campaign.progress.pending}</div>
                    <div className="text-xs text-gray-500 font-medium">Pending</div>
                  </div>
                </div>
              </div>

              {/* Message Template */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <label className="text-sm text-gray-700 font-semibold mb-2 block">Message Template</label>
                <div className="bg-white p-4 rounded border border-gray-200">
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{campaign.template_content}</p>
                </div>
              </div>

              {/* Cost and Timing */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <label className="text-sm text-gray-500 font-medium">Total Cost</label>
                  <div className="text-xl font-bold mt-2 text-gray-900">${campaign.total_cost.toFixed(2)}</div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <label className="text-sm text-gray-500 font-medium">Created</label>
                  <div className="mt-2 text-sm text-gray-700">
                    {new Date(campaign.created_at).toLocaleString()}
                  </div>
                </div>
                {campaign.started_at && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <label className="text-sm text-gray-500 font-medium">Started</label>
                    <div className="mt-2 text-sm text-gray-700">
                      {new Date(campaign.started_at).toLocaleString()}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Message Lists (Successful/Failed/All) */}
          {activeTab !== 'overview' && (
            <div>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="h-8 w-8 text-indigo-600 animate-spin" />
                </div>
              ) : messages.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <AlertCircle className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                  <p>No {activeTab} messages found</p>
                </div>
              ) : (
                <div className="overflow-hidden rounded-lg border border-gray-200">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Recipient</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Phone</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Status</th>
                        {activeTab === 'failed' && (
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Error</th>
                        )}
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Time</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {messages.map((msg, idx) => (
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
                          {activeTab === 'failed' && (
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
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t bg-gray-50 flex justify-between items-center">
          <div className="flex gap-2">
            {onAction && campaign.status === 'draft' && (
              <button
                onClick={() => onAction('start', campaign.id)}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                <Play className="h-4 w-4" />
                Start
              </button>
            )}
            {onAction && campaign.status === 'running' && (
              <button
                onClick={() => onAction('pause', campaign.id)}
                className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
              >
                <Pause className="h-4 w-4" />
                Pause
              </button>
            )}
            {onAction && campaign.status === 'paused' && (
              <button
                onClick={() => onAction('start', campaign.id)}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                <Play className="h-4 w-4" />
                Resume
              </button>
            )}
            {onAction && ['draft', 'paused', 'completed'].includes(campaign.status) && (
              <button
                onClick={() => onAction('edit', campaign.id)}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                <Edit className="h-4 w-4" />
                {campaign.status === 'completed' ? 'Duplicate & Edit' : 'Edit'}
              </button>
            )}
          </div>

          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default SMSCampaignAnalytics;
