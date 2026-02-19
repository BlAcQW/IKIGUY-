/**
 * Model Management Panel Component
 *
 * Interface for managing TTS models - list, switch, upload, and delete models.
 */

import React, { useState, useEffect } from 'react';
import { TTSProvider } from '../../config/tts-providers';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import {
  RefreshCw,
  Trash2,
  CheckCircle2,
  Circle,
  AlertCircle,
  Upload,
  Download
} from 'lucide-react';

interface Model {
  id: string;
  name: string;
  path: string;
  size: string;
  isActive: boolean;
  language?: string;
  description?: string;
  createdAt?: string;
}

interface ModelManagementPanelProps {
  provider: TTSProvider;
}

export const ModelManagementPanel: React.FC<ModelManagementPanelProps> = ({ provider }) => {
  const [models, setModels] = useState<Model[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  // Fetch available models for the provider
  const fetchModels = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${provider.endpoint}/models`);

      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.statusText}`);
      }

      const data = await response.json();
      setModels(data.models || []);

      // Set active model
      const activeModel = data.models?.find((m: Model) => m.isActive);
      if (activeModel) {
        setSelectedModel(activeModel.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch models');
      console.error('Error fetching models:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Switch to a different model
  const switchModel = async (modelId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${provider.endpoint}/models/switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId }),
      });

      if (!response.ok) {
        throw new Error(`Failed to switch model: ${response.statusText}`);
      }

      const data = await response.json();

      // Update models list to reflect new active model
      setModels(prevModels =>
        prevModels.map(m => ({
          ...m,
          isActive: m.id === modelId,
        }))
      );

      setSelectedModel(modelId);

      // Show success message
      alert(`Successfully switched to model: ${models.find(m => m.id === modelId)?.name}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to switch model');
      console.error('Error switching model:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Delete a model
  const deleteModel = async (modelId: string) => {
    if (!confirm('Are you sure you want to delete this model? This action cannot be undone.')) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${provider.endpoint}/models/${modelId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Failed to delete model: ${response.statusText}`);
      }

      // Remove model from list
      setModels(prevModels => prevModels.filter(m => m.id !== modelId));

      alert('Model deleted successfully');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete model');
      console.error('Error deleting model:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, [provider.id]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Model Management</h2>
          <p className="text-gray-600">
            Manage and switch between different {provider.name} models
          </p>
        </div>
        <Button onClick={fetchModels} disabled={isLoading} variant="outline">
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Error Display */}
      {error && (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-destructive mt-0.5" />
              <div>
                <h3 className="font-semibold text-destructive">Error</h3>
                <p className="text-sm text-destructive/90">{error}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Models List */}
      {isLoading && models.length === 0 ? (
        <div className="text-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-gray-600" />
          <p className="text-gray-600">Loading models...</p>
        </div>
      ) : models.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <Circle className="w-12 h-12 mx-auto mb-4 text-gray-600" />
              <h3 className="text-lg font-semibold mb-2">No Models Found</h3>
              <p className="text-gray-600">
                No models available for {provider.name}. Upload a model to get started.
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {models.map((model) => (
            <Card key={model.id} className={model.isActive ? 'border-primary' : ''}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="flex items-center gap-2">
                      {model.isActive ? (
                        <CheckCircle2 className="w-5 h-5 text-indigo-600" />
                      ) : (
                        <Circle className="w-5 h-5 text-gray-600" />
                      )}
                      {model.name}
                    </CardTitle>
                    <CardDescription className="mt-2">
                      {model.description || 'No description available'}
                    </CardDescription>
                  </div>
                  {model.isActive && (
                    <Badge variant="default" className="ml-2">
                      Active
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {/* Model Details */}
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Size:</span>
                      <span className="font-medium">{model.size}</span>
                    </div>
                    {model.language && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Language:</span>
                        <span className="font-medium">{model.language}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-gray-600">Path:</span>
                      <span className="font-mono text-xs truncate max-w-[150px]">
                        {model.path}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 pt-3 border-t">
                    {!model.isActive && (
                      <Button
                        onClick={() => switchModel(model.id)}
                        disabled={isLoading}
                        size="sm"
                        className="flex-1"
                      >
                        <CheckCircle2 className="w-4 h-4 mr-2" />
                        Activate
                      </Button>
                    )}
                    {!model.isActive && (
                      <Button
                        onClick={() => deleteModel(model.id)}
                        disabled={isLoading}
                        size="sm"
                        variant="destructive"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Upload Section (Placeholder) */}
      <Card>
        <CardHeader>
          <CardTitle>Upload New Model</CardTitle>
          <CardDescription>
            Upload a new fine-tuned model for {provider.name}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border-2 border-dashed rounded-lg p-12 text-center">
            <Upload className="w-12 h-12 mx-auto mb-4 text-gray-600" />
            <h3 className="text-lg font-semibold mb-2">Model Upload (Coming Soon)</h3>
            <p className="text-gray-600 mb-4">
              Upload functionality will be available in a future update.
              <br />
              For now, manually add models to: <code className="text-sm">/opt/kasaai/apps/voice-lab/models/</code>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
