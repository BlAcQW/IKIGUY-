/**
 * Provider Management Page.
 *
 * Admin interface to configure and manage AI service providers:
 * - STT (Speech-to-Text): OpenAI Whisper, Google, etc.
 * - TTS (Text-to-Speech): OpenAI, ElevenLabs, etc.
 * - LLM (Language Models): Gemini, OpenAI, etc.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Settings,
  Check,
  X,
  Star,
  DollarSign,
  Cpu,
  Mic,
  Volume2,
  Brain,
  TrendingUp,
  Info,
  Save,
  RefreshCw
} from 'lucide-react';
import { api } from '../lib/api';

interface Provider {
  provider_type: string;
  provider_id: string;
  name: string;
  model?: string;
  voice?: string;
  enabled: boolean;
  is_default: boolean;
  status: 'active' | 'error' | 'disabled';
  cost_info: {
    per_minute_usd?: number;
    per_1k_chars_usd?: number;
    per_query_usd?: number;
  };
}

interface ProviderComparison {
  stt_providers: Array<{
    provider_id: string;
    usage_count: number;
    avg_accuracy: number;
    avg_latency_ms: number;
    total_cost_usd: number;
  }>;
  tts_providers: Array<{
    provider_id: string;
    usage_count: number;
    avg_quality_score: number;
    avg_latency_ms: number;
    total_cost_usd: number;
  }>;
  llm_providers: Array<{
    provider_id: string;
    usage_count: number;
    avg_confidence: number;
    avg_latency_ms: number;
    total_cost_usd: number;
  }>;
}

export default function ProviderManagementPage() {
  useEffect(() => {
    document.title = 'Provider Management - InkWave';
  }, []);

  const [providers, setProviders] = useState<Provider[]>([]);
  const [comparison, setComparison] = useState<ProviderComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedType, setSelectedType] = useState<string>('all');

  useEffect(() => {
    loadProviders();
    loadComparison();
  }, []);

  const loadProviders = async () => {
    try {
      const response = await api.admin.listProviders();
      setProviders(response.data);
    } catch (error) {
      console.error('Failed to load providers:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadComparison = async () => {
    try {
      const response = await api.admin.getProviderComparison();
      setComparison(response.data);
    } catch (error) {
      console.error('Failed to load comparison:', error);
    }
  };

  const toggleProvider = async (provider: Provider) => {
    setSaving(true);
    try {
      await api.admin.updateProvider({
        provider_type: provider.provider_type,
        provider_id: provider.provider_id,
        enabled: !provider.enabled,
        is_default: provider.is_default,
        model: provider.model,
        voice: provider.voice
      });
      await loadProviders();
    } catch (error) {
      console.error('Failed to update provider:', error);
    } finally {
      setSaving(false);
    }
  };

  const setDefaultProvider = async (provider: Provider) => {
    setSaving(true);
    try {
      // First, unset all defaults of same type
      const sameTypeProviders = providers.filter(
        p => p.provider_type === provider.provider_type
      );

      for (const p of sameTypeProviders) {
        if (p.provider_id !== provider.provider_id && p.is_default) {
          await api.admin.updateProvider({
            provider_type: p.provider_type,
            provider_id: p.provider_id,
            enabled: p.enabled,
            is_default: false,
            model: p.model,
            voice: p.voice
          });
        }
      }

      // Set new default
      await api.admin.updateProvider({
        provider_type: provider.provider_type,
        provider_id: provider.provider_id,
        enabled: true, // Auto-enable when setting as default
        is_default: true,
        model: provider.model,
        voice: provider.voice
      });

      await loadProviders();
    } catch (error) {
      console.error('Failed to set default provider:', error);
    } finally {
      setSaving(false);
    }
  };

  const filteredProviders = selectedType === 'all'
    ? providers
    : providers.filter(p => p.provider_type === selectedType);

  const getProviderIcon = (type: string) => {
    switch (type) {
      case 'stt':
        return Mic;
      case 'tts':
        return Volume2;
      case 'llm':
        return Brain;
      default:
        return Cpu;
    }
  };

  const getProviderTypeLabel = (type: string) => {
    switch (type) {
      case 'stt':
        return 'Speech-to-Text';
      case 'tts':
        return 'Text-to-Speech';
      case 'llm':
        return 'Language Model';
      default:
        return type.toUpperCase();
    }
  };

  const getCostDisplay = (provider: Provider) => {
    if (provider.cost_info.per_minute_usd) {
      return `$${provider.cost_info.per_minute_usd.toFixed(3)}/min`;
    }
    if (provider.cost_info.per_1k_chars_usd) {
      return `$${provider.cost_info.per_1k_chars_usd.toFixed(3)}/1k chars`;
    }
    if (provider.cost_info.per_query_usd) {
      return `$${provider.cost_info.per_query_usd.toFixed(4)}/query`;
    }
    return 'N/A';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <div className="border-b border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/admin"
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-6 h-6 text-gray-400" />
              </Link>
              <div>
                <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                  <Cpu className="w-8 h-8 text-cyan-400" />
                  Provider Management
                </h1>
                <p className="text-gray-400 mt-1">
                  Configure AI service providers and monitor performance
                </p>
              </div>
            </div>
            <button
              onClick={loadProviders}
              disabled={loading}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          {['all', 'stt', 'tts', 'llm'].map((type) => (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                selectedType === type
                  ? 'bg-cyan-600 text-white'
                  : 'bg-gray-800/50 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {type === 'all' ? 'All Providers' : getProviderTypeLabel(type)}
            </button>
          ))}
        </div>

        {/* Providers Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6 animate-pulse"
              >
                <div className="h-32 bg-gray-700 rounded"></div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {filteredProviders.map((provider, index) => {
              const Icon = getProviderIcon(provider.provider_type);

              return (
                <motion.div
                  key={`${provider.provider_type}-${provider.provider_id}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`bg-gray-800/50 backdrop-blur-sm border rounded-xl p-6 transition-all ${
                    provider.enabled
                      ? 'border-cyan-500/50'
                      : 'border-gray-700'
                  }`}
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                        provider.enabled
                          ? 'bg-cyan-500/20'
                          : 'bg-gray-700'
                      }`}>
                        <Icon className={`w-6 h-6 ${
                          provider.enabled ? 'text-cyan-400' : 'text-gray-500'
                        }`} />
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-white">
                          {provider.name}
                        </h3>
                        <p className="text-xs text-gray-400">
                          {getProviderTypeLabel(provider.provider_type)}
                        </p>
                      </div>
                    </div>

                    {provider.is_default && (
                      <div className="px-2 py-1 bg-yellow-500/20 rounded-full flex items-center gap-1">
                        <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                        <span className="text-xs text-yellow-400 font-semibold">Default</span>
                      </div>
                    )}
                  </div>

                  {/* Details */}
                  <div className="space-y-2 mb-4">
                    {provider.model && (
                      <div className="flex items-center gap-2 text-sm">
                        <Settings className="w-4 h-4 text-gray-500" />
                        <span className="text-gray-400">Model:</span>
                        <span className="text-white font-mono text-xs">
                          {provider.model}
                        </span>
                      </div>
                    )}
                    {provider.voice && (
                      <div className="flex items-center gap-2 text-sm">
                        <Volume2 className="w-4 h-4 text-gray-500" />
                        <span className="text-gray-400">Voice:</span>
                        <span className="text-white font-mono text-xs">
                          {provider.voice}
                        </span>
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-sm">
                      <DollarSign className="w-4 h-4 text-gray-500" />
                      <span className="text-gray-400">Cost:</span>
                      <span className="text-green-400 font-semibold">
                        {getCostDisplay(provider)}
                      </span>
                    </div>
                  </div>

                  {/* Status Badge */}
                  <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-semibold mb-4 ${
                    provider.status === 'active'
                      ? 'bg-green-500/20 text-green-400'
                      : provider.status === 'error'
                      ? 'bg-red-500/20 text-red-400'
                      : 'bg-gray-700 text-gray-400'
                  }`}>
                    {provider.status === 'active' && <Check className="w-4 h-4" />}
                    {provider.status === 'error' && <X className="w-4 h-4" />}
                    {provider.status.charAt(0).toUpperCase() + provider.status.slice(1)}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => toggleProvider(provider)}
                      disabled={saving}
                      className={`flex-1 px-4 py-2 rounded-lg font-semibold transition-all disabled:opacity-50 ${
                        provider.enabled
                          ? 'bg-red-600 hover:bg-red-700 text-white'
                          : 'bg-green-600 hover:bg-green-700 text-white'
                      }`}
                    >
                      {provider.enabled ? 'Disable' : 'Enable'}
                    </button>
                    {!provider.is_default && provider.enabled && (
                      <button
                        onClick={() => setDefaultProvider(provider)}
                        disabled={saving}
                        className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg font-semibold transition-all disabled:opacity-50"
                        title="Set as default"
                      >
                        <Star className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}

        {/* Performance Comparison */}
        {comparison && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6 mt-8"
          >
            <div className="flex items-center gap-3 mb-6">
              <TrendingUp className="w-6 h-6 text-cyan-400" />
              <h2 className="text-xl font-bold text-white">Performance Comparison</h2>
            </div>

            {/* STT Comparison */}
            {comparison.stt_providers.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  <Mic className="w-5 h-5 text-cyan-400" />
                  Speech-to-Text Providers
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-left text-gray-400 text-sm border-b border-gray-700">
                        <th className="pb-3">Provider</th>
                        <th className="pb-3">Usage</th>
                        <th className="pb-3">Accuracy</th>
                        <th className="pb-3">Latency</th>
                        <th className="pb-3">Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparison.stt_providers.map((provider) => (
                        <tr
                          key={provider.provider_id}
                          className="text-white border-b border-gray-700/50"
                        >
                          <td className="py-3 font-semibold">{provider.provider_id}</td>
                          <td className="py-3">{provider.usage_count}</td>
                          <td className="py-3">
                            <span className="text-green-400">
                              {(provider.avg_accuracy * 100).toFixed(1)}%
                            </span>
                          </td>
                          <td className="py-3">{provider.avg_latency_ms}ms</td>
                          <td className="py-3 text-yellow-400">
                            ${provider.total_cost_usd.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TTS Comparison */}
            {comparison.tts_providers.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  <Volume2 className="w-5 h-5 text-cyan-400" />
                  Text-to-Speech Providers
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-left text-gray-400 text-sm border-b border-gray-700">
                        <th className="pb-3">Provider</th>
                        <th className="pb-3">Usage</th>
                        <th className="pb-3">Quality</th>
                        <th className="pb-3">Latency</th>
                        <th className="pb-3">Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparison.tts_providers.map((provider) => (
                        <tr
                          key={provider.provider_id}
                          className="text-white border-b border-gray-700/50"
                        >
                          <td className="py-3 font-semibold">{provider.provider_id}</td>
                          <td className="py-3">{provider.usage_count}</td>
                          <td className="py-3">
                            <span className="text-green-400">
                              {(provider.avg_quality_score * 100).toFixed(1)}%
                            </span>
                          </td>
                          <td className="py-3">{provider.avg_latency_ms}ms</td>
                          <td className="py-3 text-yellow-400">
                            ${provider.total_cost_usd.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* LLM Comparison */}
            {comparison.llm_providers.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  <Brain className="w-5 h-5 text-cyan-400" />
                  Language Model Providers
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-left text-gray-400 text-sm border-b border-gray-700">
                        <th className="pb-3">Provider</th>
                        <th className="pb-3">Usage</th>
                        <th className="pb-3">Confidence</th>
                        <th className="pb-3">Latency</th>
                        <th className="pb-3">Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparison.llm_providers.map((provider) => (
                        <tr
                          key={provider.provider_id}
                          className="text-white border-b border-gray-700/50"
                        >
                          <td className="py-3 font-semibold">{provider.provider_id}</td>
                          <td className="py-3">{provider.usage_count}</td>
                          <td className="py-3">
                            <span className="text-green-400">
                              {(provider.avg_confidence * 100).toFixed(1)}%
                            </span>
                          </td>
                          <td className="py-3">{provider.avg_latency_ms}ms</td>
                          <td className="py-3 text-yellow-400">
                            ${provider.total_cost_usd.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Info Box */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-cyan-900/20 border border-cyan-500/30 rounded-xl p-6 mt-6"
        >
          <div className="flex gap-4">
            <Info className="w-6 h-6 text-cyan-400 flex-shrink-0 mt-1" />
            <div>
              <h3 className="text-lg font-bold text-white mb-2">Provider Configuration</h3>
              <ul className="text-gray-300 space-y-2 text-sm">
                <li>• Default providers are used for all new requests</li>
                <li>• Only one provider per type can be set as default</li>
                <li>• Disabled providers will not be used in the system</li>
                <li>• Costs are estimated based on provider pricing</li>
                <li>• Performance metrics update in real-time</li>
              </ul>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
