/**
 * Unified Campaign Analytics Component
 *
 * Analytics dashboard for all campaign types (Voice, SMS, WhatsApp, Email).
 * Works with the centralized campaign router.
 *
 * Usage:
 * ```tsx
 * import { CampaignAnalytics } from '@shared/frontend/campaigns/CampaignAnalytics';
 *
 * <CampaignAnalytics
 *   campaignId={selectedCampaignId}
 *   apiBaseUrl="https://api.example.com"
 *   authToken={token}
 *   isOpen={showModal}
 *   onClose={() => setShowModal(false)}
 * />
 * ```
 */

import React, { useState, useEffect } from 'react';
import {
  X,
  TrendingUp,
  CheckCircle,
  XCircle,
  Clock,
  DollarSign,
  Users,
  Mail,
  MessageSquare,
  Phone,
  Send,
  Eye,
  MousePointer
} from 'lucide-react';

// Types
export interface CampaignAnalytics {
  campaign_id: string;
  campaign_name: string;
  campaign_type: 'voice' | 'sms' | 'whatsapp' | 'email';
  status: string;
  total_recipients: number;
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  failed: number;
  pending: number;
  delivery_rate: number;
  open_rate: number;
  click_rate: number;
  failure_rate: number;
  total_cost: number;
  cost_per_delivery: number;
  currency: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
}

export interface CampaignAnalyticsProps {
  campaignId: string;
  apiBaseUrl: string;
  authToken: string;
  isOpen: boolean;
  onClose: () => void;
}

export const CampaignAnalytics: React.FC<CampaignAnalyticsProps> = ({
  campaignId,
  apiBaseUrl,
  authToken,
  isOpen,
  onClose
}) => {
  const [analytics, setAnalytics] = useState<CampaignAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOpen && campaignId) {
      fetchAnalytics();
    }
  }, [isOpen, campaignId]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/campaigns/${campaignId}/analytics`,
        {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCampaignTypeIcon = (type: string) => {
    switch (type) {
      case 'voice': return <Phone className="h-5 w-5" />;
      case 'sms': return <MessageSquare className="h-5 w-5" />;
      case 'whatsapp': return <Send className="h-5 w-5" />;
      case 'email': return <Mail className="h-5 w-5" />;
      default: return <MessageSquare className="h-5 w-5" />;
    }
  };

  const getCampaignTypeColor = (type: string) => {
    switch (type) {
      case 'voice': return 'from-purple-500 to-purple-600';
      case 'sms': return 'from-blue-500 to-blue-600';
      case 'whatsapp': return 'from-green-500 to-green-600';
      case 'email': return 'from-orange-500 to-orange-600';
      default: return 'from-gray-500 to-gray-600';
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className={`bg-gradient-to-r ${analytics ? getCampaignTypeColor(analytics.campaign_type) : 'from-gray-500 to-gray-600'} text-white p-6`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {analytics && getCampaignTypeIcon(analytics.campaign_type)}
              <div>
                <h2 className="text-2xl font-bold">{analytics?.campaign_name || 'Campaign Analytics'}</h2>
                <p className="text-white/90 text-sm mt-1">
                  {analytics?.campaign_type.toUpperCase()} Campaign • {analytics?.status}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-full transition-colors"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
          ) : analytics ? (
            <div className="space-y-6">
              {/* Key Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard
                  icon={<Users className="h-6 w-6" />}
                  label="Total Recipients"
                  value={analytics.total_recipients.toLocaleString()}
                  color="bg-blue-500"
                />
                <MetricCard
                  icon={<CheckCircle className="h-6 w-6" />}
                  label="Delivered"
                  value={analytics.delivered.toLocaleString()}
                  subtitle={`${analytics.delivery_rate.toFixed(1)}% delivery rate`}
                  color="bg-green-500"
                />
                <MetricCard
                  icon={<XCircle className="h-6 w-6" />}
                  label="Failed"
                  value={analytics.failed.toLocaleString()}
                  subtitle={`${analytics.failure_rate.toFixed(1)}% failure rate`}
                  color="bg-red-500"
                />
                <MetricCard
                  icon={<DollarSign className="h-6 w-6" />}
                  label="Total Cost"
                  value={`${analytics.currency} ${analytics.total_cost.toFixed(2)}`}
                  subtitle={`${analytics.currency} ${analytics.cost_per_delivery.toFixed(4)} per delivery`}
                  color="bg-purple-500"
                />
              </div>

              {/* Engagement Metrics (for Email/WhatsApp) */}
              {(analytics.campaign_type === 'email' || analytics.campaign_type === 'whatsapp') && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <MetricCard
                    icon={<Eye className="h-6 w-6" />}
                    label="Opened"
                    value={analytics.opened.toLocaleString()}
                    subtitle={`${analytics.open_rate.toFixed(1)}% open rate`}
                    color="bg-indigo-500"
                  />
                  <MetricCard
                    icon={<MousePointer className="h-6 w-6" />}
                    label="Clicked"
                    value={analytics.clicked.toLocaleString()}
                    subtitle={`${analytics.click_rate.toFixed(1)}% click rate`}
                    color="bg-pink-500"
                  />
                  <MetricCard
                    icon={<TrendingUp className="h-6 w-6" />}
                    label="Engagement"
                    value={`${((analytics.opened / analytics.delivered) * 100).toFixed(1)}%`}
                    subtitle="Overall engagement"
                    color="bg-orange-500"
                  />
                </div>
              )}

              {/* Progress Bar */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Campaign Progress</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Sent</span>
                    <span className="font-medium">{analytics.sent} ({((analytics.sent / analytics.total_recipients) * 100).toFixed(1)}%)</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-green-500 h-3 rounded-full transition-all duration-300"
                      style={{ width: `${(analytics.delivered / analytics.total_recipients) * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Delivered: {analytics.delivered}</span>
                    <span>Failed: {analytics.failed}</span>
                    <span>Pending: {analytics.pending}</span>
                  </div>
                </div>
              </div>

              {/* Timing Information */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-gray-600 mb-2">
                    <Clock className="h-4 w-4" />
                    <span className="text-sm font-medium">Started</span>
                  </div>
                  <p className="text-lg font-semibold text-gray-900">
                    {analytics.started_at
                      ? new Date(analytics.started_at).toLocaleString()
                      : 'Not started'}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-gray-600 mb-2">
                    <CheckCircle className="h-4 w-4" />
                    <span className="text-sm font-medium">Completed</span>
                  </div>
                  <p className="text-lg font-semibold text-gray-900">
                    {analytics.completed_at
                      ? new Date(analytics.completed_at).toLocaleString()
                      : 'In progress'}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-gray-600 mb-2">
                    <TrendingUp className="h-4 w-4" />
                    <span className="text-sm font-medium">Duration</span>
                  </div>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatDuration(analytics.duration_seconds)}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              No analytics data available
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Helper component for metric cards
interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  subtitle?: string;
  color: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ icon, label, value, subtitle, color }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-center gap-3">
        <div className={`${color} text-white p-3 rounded-lg`}>
          {icon}
        </div>
        <div className="flex-1">
          <p className="text-sm text-gray-600">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
      </div>
    </div>
  );
};

export default CampaignAnalytics;
