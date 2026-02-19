import React from 'react';
import { Button } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Server, RefreshCw } from 'lucide-react';

export type TelephonyProvider = 'asterisk' | 'freeswitch';

interface TelephonyProviderInfo {
  id: TelephonyProvider;
  name: string;
  description: string;
  icon: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  features: string[];
}

interface TelephonyProviderSidebarProps {
  selectedProvider: TelephonyProvider;
  onSelectProvider: (provider: TelephonyProvider) => void;
  providers: TelephonyProviderInfo[];
  onRefresh?: () => void;
}

export const TelephonyProviderSidebar: React.FC<TelephonyProviderSidebarProps> = ({
  selectedProvider,
  onSelectProvider,
  providers,
  onRefresh,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'unhealthy':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Server className="h-5 w-5 text-gray-600" />
            <h2 className="font-semibold text-gray-900">SIP Providers</h2>
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-1 hover:bg-gray-100 rounded"
              title="Refresh providers"
            >
              <RefreshCw className="h-4 w-4 text-gray-500" />
            </button>
          )}
        </div>
        <p className="text-xs text-gray-500">
          Select a SIP/PBX provider to manage
        </p>
      </div>

      {/* Provider List */}
      <div className="flex-1 overflow-y-auto p-2">
        <div className="space-y-1">
          {providers.map((provider) => (
            <button
              key={provider.id}
              onClick={() => onSelectProvider(provider.id)}
              className={`w-full text-left p-3 rounded-lg transition-all ${
                selectedProvider === provider.id
                  ? 'bg-indigo-50 border-2 border-indigo-200 shadow-sm'
                  : 'border-2 border-transparent hover:bg-gray-50'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{provider.icon}</span>
                  <div>
                    <div className="font-semibold text-sm text-gray-900">
                      {provider.name}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {provider.description}
                    </div>
                  </div>
                </div>
              </div>

              {/* Status */}
              <div className="flex items-center gap-2 mt-2">
                <div
                  className={`w-2 h-2 rounded-full ${getStatusColor(provider.status)}`}
                />
                <span className="text-xs text-gray-600 capitalize">
                  {provider.status}
                </span>
              </div>

              {/* Features */}
              {provider.features.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {provider.features.slice(0, 2).map((feature, index) => (
                    <Badge
                      key={index}
                      variant="outline"
                      className="text-xs px-1.5 py-0 h-5"
                    >
                      {feature}
                    </Badge>
                  ))}
                  {provider.features.length > 2 && (
                    <Badge variant="outline" className="text-xs px-1.5 py-0 h-5">
                      +{provider.features.length - 2}
                    </Badge>
                  )}
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="text-xs text-gray-500">
          <div className="flex items-center justify-between mb-1">
            <span>Providers:</span>
            <span className="font-semibold">{providers.length}</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Active:</span>
            <span className="font-semibold text-green-600">
              {providers.filter((p) => p.status === 'healthy').length}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
