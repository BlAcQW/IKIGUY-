/**
 * ASR Provider Settings Panel
 *
 * Displays detailed provider information, capabilities, and health check.
 * Extracted from ASRLab.tsx for better modularity.
 */

import React, { useState } from 'react';
import { useToast } from '@/hooks/use-toast';
import { getStatusStyle } from '@/lib/status-utils';

interface ASRProvider {
  id: string;
  name: string;
  description: string;
  status: 'online' | 'offline' | 'building' | 'degraded';
  endpoint: string;
  languages: number;
  modelSize?: string;
  latency?: string;
  capabilities: {
    realtime: boolean;
    multiLanguage: boolean;
    diarization: boolean;
    timestamps: boolean;
    wordLevelTimestamps: boolean;
    punctuation: boolean;
  };
}

interface ProviderSettingsProps {
  provider: ASRProvider;
  onCheckHealth: () => Promise<boolean>;
}

export const ProviderSettings: React.FC<ProviderSettingsProps> = ({
  provider,
  onCheckHealth,
}) => {
  const { toast } = useToast();
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);

  const handleHealthCheck = async () => {
    setIsCheckingHealth(true);
    try {
      const healthy = await onCheckHealth();
      toast({
        title: healthy ? '✓ Provider is healthy' : '✗ Provider not responding',
        description: healthy
          ? `${provider.name} is operational and ready to use.`
          : 'Please check provider status or try again later.',
        variant: healthy ? 'default' : 'destructive',
      });
    } catch (error) {
      toast({
        title: 'Health check failed',
        description: error instanceof Error ? error.message : 'Unknown error occurred',
        variant: 'destructive',
      });
    } finally {
      setIsCheckingHealth(false);
    }
  };

  const statusStyle = getStatusStyle(provider.status);

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Provider Settings</h2>

      {/* Provider Info */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{provider.name}</h3>
          <p className="text-gray-600">{provider.description}</p>
        </div>

        <div className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div>
            <p className="text-sm text-gray-500">Status</p>
            <p className="font-medium text-gray-900">
              {statusStyle.dot} {statusStyle.label}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Endpoint</p>
            <p className="font-mono text-sm text-gray-900 truncate">{provider.endpoint}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Languages</p>
            <p className="font-medium text-gray-900">{provider.languages} supported</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Model Size</p>
            <p className="font-mono text-sm text-gray-900">{provider.modelSize || 'N/A'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Latency</p>
            <p className="font-mono text-sm text-gray-900">{provider.latency || 'N/A'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Provider ID</p>
            <p className="font-mono text-sm text-gray-900">{provider.id}</p>
          </div>
        </div>

        {/* Capabilities */}
        <div className="pt-4 border-t">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Capabilities</h4>
          <div className="grid grid-cols-2 gap-2">
            <CapabilityBadge
              enabled={provider.capabilities?.realtime ?? false}
              label="Real-time"
            />
            <CapabilityBadge
              enabled={provider.capabilities?.multiLanguage ?? false}
              label="Multi-Language"
            />
            <CapabilityBadge
              enabled={provider.capabilities?.diarization ?? false}
              label="Speaker Diarization"
            />
            <CapabilityBadge
              enabled={provider.capabilities?.timestamps ?? false}
              label="Timestamps"
            />
            <CapabilityBadge
              enabled={provider.capabilities?.wordLevelTimestamps ?? false}
              label="Word-level Timestamps"
            />
            <CapabilityBadge
              enabled={provider.capabilities?.punctuation ?? false}
              label="Punctuation"
            />
          </div>
        </div>

        {/* Health Check */}
        <div className="pt-4 border-t">
          <button
            onClick={handleHealthCheck}
            disabled={isCheckingHealth}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
          >
            {isCheckingHealth ? (
              <>
                <span className="inline-block animate-spin mr-2">⏳</span>
                Checking...
              </>
            ) : (
              'Run Health Check'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * Capability Badge Component
 *
 * Displays a capability as enabled/disabled with visual styling.
 */
interface CapabilityBadgeProps {
  enabled: boolean;
  label: string;
}

const CapabilityBadge: React.FC<CapabilityBadgeProps> = ({ enabled, label }) => {
  return (
    <div
      className={`
        flex items-center space-x-2 px-3 py-2 rounded-lg
        ${enabled ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-400'}
      `}
    >
      <span>{enabled ? '✓' : '✗'}</span>
      <span className="text-sm">{label}</span>
    </div>
  );
};
