/**
 * API Keys Management Page
 *
 * Allows users to create, view, and revoke API keys for programmatic access.
 *
 * Created: 2025-10-27
 * Sprint 5: Analytics & Ecosystem (Phase 8)
 */

import React, { useState } from 'react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { useAPIKeys, APIKeyWithSecret } from '@/hooks/useAPIKeys';
import {
  Key,
  Plus,
  Trash2,
  Copy,
  Check,
  Eye,
  EyeOff,
  Calendar,
  Activity,
  AlertCircle,
  Shield,
  Clock,
} from 'lucide-react';

interface APIKeysProps {}

const APIKeys: React.FC<APIKeysProps> = () => {
  const { keys, isLoading, error, createKey, revokeKey } = useAPIKeys();

  // Create key modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [keyName, setKeyName] = useState('');
  const [selectedScopes, setSelectedScopes] = useState<string[]>(['tts:synthesize']);
  const [rateLimit, setRateLimit] = useState(100);
  const [expiresInDays, setExpiresInDays] = useState<number | undefined>(undefined);

  // New key display
  const [newKey, setNewKey] = useState<APIKeyWithSecret | null>(null);
  const [showNewKeyModal, setShowNewKeyModal] = useState(false);
  const [copied, setCopied] = useState(false);

  // Delete confirmation
  const [deleteKeyId, setDeleteKeyId] = useState<string | null>(null);

  // Available scopes
  const availableScopes = [
    { id: 'tts:synthesize', name: 'Synthesize Speech', description: 'Generate speech from text' },
    { id: 'tts:clone', name: 'Voice Cloning', description: 'Use voice cloning features' },
    { id: 'tts:history', name: 'History Access', description: 'Access synthesis history' },
    { id: 'tts:estimate', name: 'Cost Estimation', description: 'Estimate synthesis costs' },
    { id: 'tts:providers', name: 'List Providers', description: 'List available TTS providers' },
    { id: 'tts:voices', name: 'List Voices', description: 'List available voices' },
  ];

  /**
   * Handle create API key
   */
  const handleCreateKey = async () => {
    if (!keyName.trim()) {
      alert('Please enter a name for the API key');
      return;
    }

    if (selectedScopes.length === 0) {
      alert('Please select at least one scope');
      return;
    }

    const key = await createKey({
      name: keyName,
      scopes: selectedScopes,
      rate_limit: rateLimit,
      expires_in_days: expiresInDays,
    });

    if (key) {
      setNewKey(key);
      setShowCreateModal(false);
      setShowNewKeyModal(true);

      // Reset form
      setKeyName('');
      setSelectedScopes(['tts:synthesize']);
      setRateLimit(100);
      setExpiresInDays(undefined);
    }
  };

  /**
   * Handle copy API key
   */
  const handleCopyKey = () => {
    if (newKey) {
      navigator.clipboard.writeText(newKey.api_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  /**
   * Handle revoke key
   */
  const handleRevokeKey = async () => {
    if (!deleteKeyId) return;

    const success = await revokeKey(deleteKeyId);
    if (success) {
      setDeleteKeyId(null);
    }
  };

  /**
   * Toggle scope selection
   */
  const toggleScope = (scopeId: string) => {
    if (selectedScopes.includes(scopeId)) {
      setSelectedScopes(selectedScopes.filter(s => s !== scopeId));
    } else {
      setSelectedScopes([...selectedScopes, scopeId]);
    }
  };

  /**
   * Format date
   */
  const formatDate = (dateString?: string): string => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex h-screen bg-background text-foreground">
      <DashboardSidebar />
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Header */}
        <div className="bg-card border-b border-border px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Key className="h-6 w-6 text-indigo-600" />
              <h1 className="text-2xl font-bold text-foreground">API Keys</h1>
            </div>

            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Create API Key</span>
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 max-w-7xl mx-auto px-6 py-8 w-full">
          {/* Info Banner */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-start space-x-3">
              <Shield className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-blue-900 mb-1">
                  Programmatic Access
                </h3>
                <p className="text-sm text-blue-800">
                  API keys allow you to access KasaAI services programmatically. Each key has specific permissions (scopes) and rate limits.
                  <strong className="block mt-1">⚠️ Important: API keys are only shown once at creation. Store them securely!</strong>
                </p>
              </div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center space-x-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
              <div className="text-sm text-red-800">{error}</div>
            </div>
          )}

          {/* Loading State */}
          {isLoading && keys.length === 0 && (
            <div className="flex items-center justify-center py-20">
              <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && keys.length === 0 && (
            <div className="flex items-center justify-center py-20">
              <div className="text-center max-w-md">
                <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Key className="w-10 h-10 text-gray-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">No API Keys Yet</h3>
                <p className="text-gray-600 mb-6">
                  Create your first API key to start accessing KasaAI services programmatically.
                </p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Create Your First API Key
                </button>
              </div>
            </div>
          )}

          {/* API Keys Table */}
          {!isLoading && keys.length > 0 && (
            <div className="bg-card rounded-lg border border-border overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-muted border-b border-border">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Name
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Key
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Scopes
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Usage
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Last Used
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {keys.map((key) => (
                      <tr key={key.id} className={`hover:bg-muted/50 transition-colors ${key.revoked ? 'opacity-50' : ''}`}>
                        <td className="px-4 py-3">
                          <div className="flex flex-col">
                            <span className="text-sm font-medium text-foreground">{key.name}</span>
                            {key.revoked && (
                              <span className="text-xs text-red-600 mt-1">Revoked</span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono text-gray-800">
                            {key.key_prefix}
                          </code>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-1">
                            {key.scopes.slice(0, 2).map((scope) => (
                              <span
                                key={scope}
                                className="px-2 py-0.5 bg-indigo-100 text-indigo-800 text-xs rounded"
                              >
                                {scope.split(':')[1]}
                              </span>
                            ))}
                            {key.scopes.length > 2 && (
                              <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                                +{key.scopes.length - 2} more
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center space-x-1 text-sm text-foreground">
                            <Activity className="w-3 h-3" />
                            <span>{key.request_count.toLocaleString()}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-muted-foreground">
                          {formatDate(key.last_used_at)}
                        </td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => setDeleteKeyId(key.id)}
                            disabled={key.revoked}
                            className="p-2 bg-red-100 text-red-600 rounded-md hover:bg-red-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Revoke API key"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Create API Key Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <h2 className="text-2xl font-bold text-foreground mb-6">Create New API Key</h2>

                {/* Key Name */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Key Name
                  </label>
                  <input
                    type="text"
                    value={keyName}
                    onChange={(e) => setKeyName(e.target.value)}
                    placeholder="e.g., Production, Development, Testing"
                    className="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-background text-foreground"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    A descriptive name to help you identify this key
                  </p>
                </div>

                {/* Scopes */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Permissions (Scopes)
                  </label>
                  <div className="space-y-2">
                    {availableScopes.map((scope) => (
                      <div
                        key={scope.id}
                        onClick={() => toggleScope(scope.id)}
                        className={`p-3 border-2 rounded-lg cursor-pointer transition-all ${
                          selectedScopes.includes(scope.id)
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-border bg-background hover:border-gray-300'
                        }`}
                      >
                        <div className="flex items-start">
                          <input
                            type="checkbox"
                            checked={selectedScopes.includes(scope.id)}
                            onChange={() => toggleScope(scope.id)}
                            className="mt-1 mr-3"
                          />
                          <div className="flex-1">
                            <div className="font-medium text-sm text-foreground">{scope.name}</div>
                            <div className="text-xs text-muted-foreground mt-0.5">{scope.description}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Rate Limit */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Rate Limit (requests per minute)
                  </label>
                  <input
                    type="number"
                    value={rateLimit}
                    onChange={(e) => setRateLimit(parseInt(e.target.value))}
                    min={1}
                    max={1000}
                    className="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-background text-foreground"
                  />
                </div>

                {/* Expiration */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Expiration (optional)
                  </label>
                  <select
                    value={expiresInDays || ''}
                    onChange={(e) => setExpiresInDays(e.target.value ? parseInt(e.target.value) : undefined)}
                    className="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-background text-foreground"
                  >
                    <option value="">Never expires</option>
                    <option value="7">7 days</option>
                    <option value="30">30 days</option>
                    <option value="90">90 days</option>
                    <option value="365">1 year</option>
                  </select>
                </div>

                {/* Actions */}
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 text-sm font-medium text-foreground bg-muted hover:bg-muted/80 rounded-md transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateKey}
                    className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md transition-colors"
                  >
                    Create API Key
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* New API Key Modal */}
        {showNewKeyModal && newKey && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card rounded-lg shadow-xl max-w-2xl w-full">
              <div className="p-6">
                <div className="flex items-start gap-4 mb-6">
                  <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                    <Check className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="flex-1">
                    <h2 className="text-2xl font-bold text-foreground mb-2">
                      API Key Created Successfully!
                    </h2>
                    <p className="text-sm text-muted-foreground">
                      Make sure to copy your API key now. You won't be able to see it again!
                    </p>
                  </div>
                </div>

                {/* API Key Display */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Your API Key
                  </label>
                  <div className="flex items-center space-x-2">
                    <code className="flex-1 px-4 py-3 bg-gray-100 border border-gray-300 rounded-lg font-mono text-sm text-gray-900 break-all">
                      {newKey.api_key}
                    </code>
                    <button
                      onClick={handleCopyKey}
                      className="px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center space-x-2"
                    >
                      {copied ? (
                        <>
                          <Check className="w-4 h-4" />
                          <span>Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Key Details */}
                <div className="bg-muted rounded-lg p-4 mb-6">
                  <h3 className="font-semibold text-sm text-foreground mb-3">Key Details</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Name:</span>
                      <span className="font-medium text-foreground">{newKey.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Rate Limit:</span>
                      <span className="font-medium text-foreground">{newKey.rate_limit} req/min</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Scopes:</span>
                      <span className="font-medium text-foreground">{newKey.scopes.length} permissions</span>
                    </div>
                  </div>
                </div>

                {/* Warning */}
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
                  <div className="flex items-start space-x-3">
                    <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-amber-800">
                      <strong>Important Security Notice:</strong> Store this API key securely. It provides access to your account and should be treated like a password.
                    </div>
                  </div>
                </div>

                {/* Close Button */}
                <div className="flex justify-end">
                  <button
                    onClick={() => {
                      setShowNewKeyModal(false);
                      setNewKey(null);
                    }}
                    className="px-6 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md transition-colors"
                  >
                    Done
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {deleteKeyId && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-card rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                  <Trash2 className="w-5 h-5 text-red-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-foreground mb-2">
                    Revoke API Key?
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    This will permanently revoke this API key. Any applications using this key will no longer be able to access your account. This action cannot be undone.
                  </p>
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setDeleteKeyId(null)}
                  className="px-4 py-2 text-sm font-medium text-foreground bg-muted hover:bg-muted/80 rounded-md transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleRevokeKey}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors flex items-center gap-2"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Revoke Key</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default APIKeys;
