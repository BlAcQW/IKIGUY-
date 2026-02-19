/**
 * Google Calendar Settings Component
 *
 * Configuration form for Google Calendar integration
 */

import React, { useState } from 'react';
import {
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  CloudArrowUpIcon,
} from '@heroicons/react/24/outline';
import {
  GoogleCalendarConfig,
  useIntegrationConfig,
  useConfigureGoogleCalendar,
  useTestGoogleCalendar,
  useBatchSyncConferences,
} from '../../hooks/useIntegrations';

interface GoogleCalendarSettingsProps {
  token: string;
  organizationId: string;
  onClose: () => void;
}

const GoogleCalendarSettings: React.FC<GoogleCalendarSettingsProps> = ({
  token,
  organizationId,
  onClose,
}) => {
  const { data: existingConfig, isLoading } = useIntegrationConfig(
    token,
    organizationId,
    'google_calendar'
  );

  const configureCalendar = useConfigureGoogleCalendar(token, organizationId);
  const testConnection = useTestGoogleCalendar(token, organizationId);
  const batchSync = useBatchSyncConferences(token, organizationId);

  const [config, setConfig] = useState<GoogleCalendarConfig>({
    calendar_id: 'primary',
    auto_sync_events: true,
    two_way_sync: false,
    sync_interval_minutes: 30,
    include_registration_count: true,
  });

  const [credentials, setCredentials] = useState<Record<string, any> | null>(null);
  const [credentialsFile, setCredentialsFile] = useState<string>('');
  const [testResult, setTestResult] = useState<any>(null);

  React.useEffect(() => {
    if (existingConfig?.google_calendar) {
      setConfig(existingConfig.google_calendar);
    }
  }, [existingConfig]);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setCredentialsFile(file.name);

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const json = JSON.parse(e.target?.result as string);
        setCredentials(json);
      } catch (error) {
        alert('Invalid JSON file');
      }
    };
    reader.readAsText(file);
  };

  const handleSave = async () => {
    if (!credentials && !existingConfig) {
      alert('Please upload service account credentials');
      return;
    }

    try {
      await configureCalendar.mutateAsync({
        config,
        credentials: credentials || existingConfig!.google_calendar!.credentials_json!,
      });
      alert('Google Calendar integration configured successfully!');
      onClose();
    } catch (error: any) {
      alert(`Failed to configure: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleTest = async () => {
    try {
      const result = await testConnection.mutateAsync();
      setTestResult(result);
    } catch (error: any) {
      setTestResult({
        success: false,
        error: error.response?.data?.detail || error.message,
      });
    }
  };

  const handleBatchSync = async () => {
    if (!confirm('Sync all conferences to Google Calendar? This may take a few moments.')) {
      return;
    }

    try {
      const result = await batchSync.mutateAsync(50);
      alert(`Batch sync complete!\n${result.summary.successful} successful, ${result.summary.failed} failed`);
    } catch (error: any) {
      alert(`Batch sync failed: ${error.response?.data?.detail || error.message}`);
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
        <h2 className="text-2xl font-bold text-gray-900">Google Calendar Integration</h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      </div>

      {/* Service Account Credentials */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Service Account Credentials
        </label>
        <div className="mt-1 flex items-center gap-4">
          <label className="flex-1 flex items-center justify-center px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-blue-500 transition-colors">
            <CloudArrowUpIcon className="w-5 h-5 text-gray-400 mr-2" />
            <span className="text-sm text-gray-600">
              {credentialsFile || (existingConfig ? 'Credentials configured' : 'Upload JSON file')}
            </span>
            <input
              type="file"
              accept=".json"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
        </div>
        <p className="text-xs text-gray-500">
          Download from Google Cloud Console → Service Accounts
        </p>
      </div>

      {/* Calendar ID */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Calendar ID
        </label>
        <input
          type="text"
          value={config.calendar_id}
          onChange={(e) => setConfig({ ...config, calendar_id: e.target.value })}
          placeholder="primary"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <p className="text-xs text-gray-500">
          Use "primary" for main calendar or specific calendar ID
        </p>
      </div>

      {/* Auto Sync */}
      <div className="flex items-center justify-between">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Auto-Sync Events
          </label>
          <p className="text-xs text-gray-500">
            Automatically sync new conferences to calendar
          </p>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={config.auto_sync_events}
            onChange={(e) => setConfig({ ...config, auto_sync_events: e.target.checked })}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
        </label>
      </div>

      {/* Two-Way Sync */}
      <div className="flex items-center justify-between">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Two-Way Sync
          </label>
          <p className="text-xs text-gray-500">
            Sync calendar changes back to ChurchFlow (coming soon)
          </p>
        </div>
        <label className="relative inline-flex items-center cursor-pointer opacity-50">
          <input
            type="checkbox"
            checked={config.two_way_sync}
            onChange={(e) => setConfig({ ...config, two_way_sync: e.target.checked })}
            disabled
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-gray-200 rounded-full peer-checked:bg-blue-600"></div>
        </label>
      </div>

      {/* Sync Interval */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Sync Interval (minutes)
        </label>
        <input
          type="number"
          min="5"
          max="1440"
          value={config.sync_interval_minutes}
          onChange={(e) => setConfig({ ...config, sync_interval_minutes: parseInt(e.target.value) })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Include Registration Count */}
      <div className="flex items-center justify-between">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Include Registration Count
          </label>
          <p className="text-xs text-gray-500">
            Show registration count in event description
          </p>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={config.include_registration_count}
            onChange={(e) => setConfig({ ...config, include_registration_count: e.target.checked })}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
        </label>
      </div>

      {/* Test Connection */}
      {existingConfig && (
        <div className="space-y-2">
          <button
            onClick={handleTest}
            disabled={testConnection.isPending}
            className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {testConnection.isPending ? (
              <ArrowPathIcon className="w-5 h-5 animate-spin" />
            ) : (
              <>Test Connection</>
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
                    <span className="text-sm text-green-800">{testResult.message}</span>
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
      )}

      {/* Batch Sync */}
      {existingConfig && (
        <button
          onClick={handleBatchSync}
          disabled={batchSync.isPending}
          className="w-full px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {batchSync.isPending ? (
            <>
              <ArrowPathIcon className="w-5 h-5 animate-spin" />
              Syncing...
            </>
          ) : (
            <>Batch Sync All Conferences</>
          )}
        </button>
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
          disabled={configureCalendar.isPending}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {configureCalendar.isPending ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>
    </div>
  );
};

export default GoogleCalendarSettings;
