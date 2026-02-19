/**
 * Zapier Webhook Settings Component
 *
 * Configuration form for Zapier webhook integration
 */

import React, { useState } from 'react';
import {
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import {
  ZapierWebhookConfig,
  WebhookEventType,
  useIntegrationConfig,
  useConfigureZapierWebhook,
  useTestZapierWebhook,
  useWebhookStats,
  useWebhookDeliveries,
} from '../../hooks/useIntegrations';

interface ZapierWebhookSettingsProps {
  token: string;
  organizationId: string;
  onClose: () => void;
}

const WEBHOOK_EVENTS: { value: WebhookEventType; label: string; description: string }[] = [
  { value: 'conference.created', label: 'Conference Created', description: 'New conference added' },
  { value: 'conference.updated', label: 'Conference Updated', description: 'Conference details changed' },
  { value: 'conference.deleted', label: 'Conference Deleted', description: 'Conference removed' },
  { value: 'registration.created', label: 'Registration Created', description: 'New registration received' },
  { value: 'registration.updated', label: 'Registration Updated', description: 'Registration details changed' },
  { value: 'registration.checked_in', label: 'Registration Checked In', description: 'Attendee checked in' },
  { value: 'payment.received', label: 'Payment Received', description: 'Payment processed' },
  { value: 'sms.sent', label: 'SMS Sent', description: 'SMS message delivered' },
  { value: 'email.sent', label: 'Email Sent', description: 'Email delivered' },
];

const ZapierWebhookSettings: React.FC<ZapierWebhookSettingsProps> = ({
  token,
  organizationId,
  onClose,
}) => {
  const { data: existingConfig, isLoading } = useIntegrationConfig(
    token,
    organizationId,
    'zapier'
  );

  const configureWebhook = useConfigureZapierWebhook(token, organizationId);
  const testWebhook = useTestZapierWebhook(token, organizationId);

  const [config, setConfig] = useState<ZapierWebhookConfig>({
    webhook_url: '',
    enabled_events: [],
    secret_key: '',
    retry_on_failure: true,
    max_retries: 3,
    timeout_seconds: 30,
  });

  const [testResult, setTestResult] = useState<any>(null);
  const [showStats, setShowStats] = useState(false);

  const { data: statsData } = useWebhookStats(
    token,
    organizationId,
    existingConfig?.zapier_webhook?.webhook_url,
    7
  );

  const { data: deliveries } = useWebhookDeliveries(
    token,
    organizationId,
    {
      webhook_url: existingConfig?.zapier_webhook?.webhook_url,
      limit: 10,
    }
  );

  React.useEffect(() => {
    if (existingConfig?.zapier_webhook) {
      setConfig(existingConfig.zapier_webhook);
    }
  }, [existingConfig]);

  const handleEventToggle = (eventType: WebhookEventType) => {
    setConfig({
      ...config,
      enabled_events: config.enabled_events.includes(eventType)
        ? config.enabled_events.filter(e => e !== eventType)
        : [...config.enabled_events, eventType],
    });
  };

  const handleSave = async () => {
    if (!config.webhook_url) {
      alert('Please enter a webhook URL');
      return;
    }

    if (config.enabled_events.length === 0) {
      alert('Please select at least one event type');
      return;
    }

    try {
      await configureWebhook.mutateAsync(config);
      alert('Zapier webhook configured successfully!');
      onClose();
    } catch (error: any) {
      alert(`Failed to configure: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleTest = async () => {
    if (!config.webhook_url) {
      alert('Please enter a webhook URL');
      return;
    }

    try {
      const result = await testWebhook.mutateAsync(config.webhook_url);
      setTestResult(result);
    } catch (error: any) {
      setTestResult({
        success: false,
        error: error.response?.data?.detail || error.message,
      });
    }
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Zapier Webhook Integration</h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      </div>

      {/* Webhook URL */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Webhook URL
        </label>
        <input
          type="url"
          value={config.webhook_url}
          onChange={(e) => setConfig({ ...config, webhook_url: e.target.value })}
          placeholder="https://hooks.zapier.com/hooks/catch/..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <p className="text-xs text-gray-500">
          Get this URL from your Zapier webhook trigger
        </p>
      </div>

      {/* Event Types */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Events to Trigger
        </label>
        <div className="space-y-2 max-h-64 overflow-y-auto border border-gray-200 rounded-lg p-3">
          {WEBHOOK_EVENTS.map((event) => (
            <label
              key={event.value}
              className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded cursor-pointer"
            >
              <input
                type="checkbox"
                checked={config.enabled_events.includes(event.value)}
                onChange={() => handleEventToggle(event.value)}
                className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900">{event.label}</div>
                <div className="text-xs text-gray-500">{event.description}</div>
              </div>
            </label>
          ))}
        </div>
        <p className="text-xs text-gray-500">
          Selected: {config.enabled_events.length} event{config.enabled_events.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Secret Key */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Secret Key (Optional)
        </label>
        <input
          type="password"
          value={config.secret_key || ''}
          onChange={(e) => setConfig({ ...config, secret_key: e.target.value })}
          placeholder="Enter secret key for HMAC verification"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <p className="text-xs text-gray-500">
          Used to verify webhook authenticity with HMAC signature
        </p>
      </div>

      {/* Retry Settings */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Max Retries
          </label>
          <input
            type="number"
            min="0"
            max="10"
            value={config.max_retries}
            onChange={(e) => setConfig({ ...config, max_retries: parseInt(e.target.value) })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Timeout (seconds)
          </label>
          <input
            type="number"
            min="5"
            max="120"
            value={config.timeout_seconds}
            onChange={(e) => setConfig({ ...config, timeout_seconds: parseInt(e.target.value) })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Retry on Failure */}
      <div className="flex items-center justify-between">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Retry on Failure
          </label>
          <p className="text-xs text-gray-500">
            Automatically retry failed webhook deliveries
          </p>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={config.retry_on_failure}
            onChange={(e) => setConfig({ ...config, retry_on_failure: e.target.checked })}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
        </label>
      </div>

      {/* Test Webhook */}
      <div className="space-y-2">
        <button
          onClick={handleTest}
          disabled={testWebhook.isPending || !config.webhook_url}
          className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {testWebhook.isPending ? (
            <ArrowPathIcon className="w-5 h-5 animate-spin" />
          ) : (
            <>Send Test Webhook</>
          )}
        </button>

        {testResult && (
          <div className={`p-3 rounded-lg ${
            testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}>
            <div className="flex items-center gap-2">
              {testResult.success ? (
                <>
                  <CheckCircleIcon className="w-5 h-5 text-green-600" />
                  <span className="text-sm text-green-800">Test successful!</span>
                </>
              ) : (
                <>
                  <XCircleIcon className="w-5 h-5 text-red-600" />
                  <span className="text-sm text-red-800">{testResult.error}</span>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Stats (if configured) */}
      {existingConfig && statsData && (
        <div className="border-t pt-4">
          <button
            onClick={() => setShowStats(!showStats)}
            className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            <ChartBarIcon className="w-5 h-5" />
            Webhook Statistics (Last 7 Days)
          </button>

          {showStats && (
            <div className="mt-3 grid grid-cols-2 gap-3">
              <div className="bg-blue-50 p-3 rounded-lg">
                <div className="text-2xl font-bold text-blue-900">{statsData.stats.total_deliveries}</div>
                <div className="text-xs text-blue-700">Total Deliveries</div>
              </div>
              <div className="bg-green-50 p-3 rounded-lg">
                <div className="text-2xl font-bold text-green-900">{(statsData.stats.success_rate * 100).toFixed(1)}%</div>
                <div className="text-xs text-green-700">Success Rate</div>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">{statsData.stats.successful_deliveries}</div>
                <div className="text-xs text-gray-700">Successful</div>
              </div>
              <div className="bg-red-50 p-3 rounded-lg">
                <div className="text-2xl font-bold text-red-900">{statsData.stats.failed_deliveries}</div>
                <div className="text-xs text-red-700">Failed</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={onClose}
          className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={configureWebhook.isPending}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {configureWebhook.isPending ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>
    </div>
  );
};

export default ZapierWebhookSettings;
