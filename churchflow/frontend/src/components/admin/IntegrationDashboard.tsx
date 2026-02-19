/**
 * Integration Dashboard Component
 *
 * Displays overview of all integrations with health status
 */

import React from 'react';
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { IntegrationDashboard as IDashboard, IntegrationHealth, IntegrationType } from '../../hooks/useIntegrations';

interface IntegrationDashboardProps {
  dashboard: IDashboard;
  onConfigure: (integrationType: IntegrationType) => void;
}

const IntegrationDashboard: React.FC<IntegrationDashboardProps> = ({
  dashboard,
  onConfigure,
}) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircleIcon className="w-6 h-6 text-green-500" />;
      case 'inactive':
        return <ClockIcon className="w-6 h-6 text-gray-400" />;
      case 'error':
        return <XCircleIcon className="w-6 h-6 text-red-500" />;
      case 'pending_auth':
        return <ExclamationTriangleIcon className="w-6 h-6 text-yellow-500" />;
      default:
        return <ClockIcon className="w-6 h-6 text-gray-400" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return 'Active';
      case 'inactive':
        return 'Inactive';
      case 'error':
        return 'Error';
      case 'pending_auth':
        return 'Pending Auth';
      default:
        return 'Unknown';
    }
  };

  const getIntegrationTitle = (type: IntegrationType) => {
    switch (type) {
      case 'google_calendar':
        return 'Google Calendar';
      case 'zapier':
        return 'Zapier Webhooks';
      case 'email_campaign':
        return 'Email Campaigns';
      case 'stripe_billing':
        return 'Stripe Billing';
      default:
        return type;
    }
  };

  const getIntegrationDescription = (type: IntegrationType) => {
    switch (type) {
      case 'google_calendar':
        return 'Sync conferences to Google Calendar automatically';
      case 'zapier':
        return 'Connect to 5000+ apps via workflow automation';
      case 'email_campaign':
        return 'Send email campaigns to members and attendees';
      case 'stripe_billing':
        return 'Accept payments and manage subscriptions';
      default:
        return '';
    }
  };

  const formatLastSync = (lastSyncAt?: string) => {
    if (!lastSyncAt) return 'Never';
    const date = new Date(lastSyncAt);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  // Find integration health or create placeholder
  const getIntegrationHealth = (type: IntegrationType): IntegrationHealth | null => {
    return dashboard.integrations.find(i => i.integration_type === type) || null;
  };

  const allIntegrationTypes: IntegrationType[] = [
    'google_calendar',
    'zapier',
    'email_campaign',
    'stripe_billing',
  ];

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <CheckCircleIcon className="w-8 h-8 text-green-600" />
            <div>
              <p className="text-2xl font-bold text-green-900">{dashboard.total_active_integrations}</p>
              <p className="text-sm text-green-700">Active Integrations</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <ClockIcon className="w-8 h-8 text-gray-600" />
            <div>
              <p className="text-2xl font-bold text-gray-900">{dashboard.total_inactive_integrations}</p>
              <p className="text-sm text-gray-700">Inactive</p>
            </div>
          </div>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <XCircleIcon className="w-8 h-8 text-red-600" />
            <div>
              <p className="text-2xl font-bold text-red-900">{dashboard.total_error_integrations}</p>
              <p className="text-sm text-red-700">Errors</p>
            </div>
          </div>
        </div>
      </div>

      {/* Integration Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {allIntegrationTypes.map((type) => {
          const health = getIntegrationHealth(type);
          const isConfigured = !!health;

          return (
            <div
              key={type}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {getIntegrationTitle(type)}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {getIntegrationDescription(type)}
                  </p>
                </div>
                {isConfigured && getStatusIcon(health.status)}
              </div>

              {/* Stats (if configured) */}
              {isConfigured && (
                <div className="space-y-2 mb-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Status:</span>
                    <span className={`font-medium ${
                      health.status === 'active' ? 'text-green-600' :
                      health.status === 'error' ? 'text-red-600' :
                      'text-gray-600'
                    }`}>
                      {getStatusText(health.status)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Last Sync:</span>
                    <span className="text-gray-900">{formatLastSync(health.last_sync_at)}</span>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Success Rate:</span>
                    <span className="text-gray-900">
                      {(health.success_rate * 100).toFixed(1)}%
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Total Syncs:</span>
                    <span className="text-gray-900">{health.total_syncs}</span>
                  </div>

                  {health.error_message && (
                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                      {health.error_message}
                    </div>
                  )}
                </div>
              )}

              {/* Actions */}
              <button
                onClick={() => onConfigure(type)}
                className={`w-full px-4 py-2 rounded-lg font-medium transition-colors ${
                  isConfigured
                    ? 'bg-blue-50 text-blue-700 hover:bg-blue-100'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {isConfigured ? 'Configure' : 'Set Up'}
              </button>
            </div>
          );
        })}
      </div>

      {/* Last Updated */}
      <div className="text-center text-sm text-gray-500">
        Last updated: {new Date(dashboard.last_updated).toLocaleString()}
      </div>
    </div>
  );
};

export default IntegrationDashboard;
