import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Loader2 } from 'lucide-react';
import { useBackendAuth } from '@/contexts/BackendAuthContext';
import { useNotification } from '@/contexts/NotificationContext';

const API_BASE = 'https://language-community-api.ailabsafrica.com/api/v1';

interface ModelRegistrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const ModelRegistrationModal = ({ isOpen, onClose, onSuccess }: ModelRegistrationModalProps) => {
  const { user } = useBackendAuth();
  const { showSuccess, showError } = useNotification();

  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    model_type: 'tts',
    architecture: 'transformer',
    version: '1.0.0',
    primary_language: 'en',
    languages: 'en',
    storage_path: '',
    checkpoint_path: '',
    deployment_status: 'experimental',
    license: 'MIT',
    is_public: true
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!user) {
      showError('Please sign in to register models');
      return;
    }

    try {
      setLoading(true);
      const token = localStorage.getItem('auth_access_token');

      const payload = {
        ...formData,
        languages: formData.languages.split(',').map(l => l.trim()),
        is_multilingual: formData.languages.split(',').length > 1
      };

      const response = await fetch(`${API_BASE}/models`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to register model');
      }

      showSuccess('Model registered successfully!');
      onClose();
      if (onSuccess) onSuccess();
    } catch (error: any) {
      console.error('Failed to register model:', error);
      showError(error.message || 'Failed to register model');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Register New Model</DialogTitle>
          <DialogDescription>
            Register a trained ML model in the community registry
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <Label htmlFor="name">Model Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                placeholder="e.g., Yoruba TTS v1.0"
                required
              />
            </div>

            <div className="col-span-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                placeholder="Brief description of the model..."
                rows={2}
              />
            </div>

            <div>
              <Label htmlFor="model_type">Model Type *</Label>
              <Select value={formData.model_type} onValueChange={(value) => handleChange('model_type', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="tts">Text-to-Speech</SelectItem>
                  <SelectItem value="asr">Speech Recognition</SelectItem>
                  <SelectItem value="llm">Language Model</SelectItem>
                  <SelectItem value="nmt">Translation</SelectItem>
                  <SelectItem value="ner">Named Entity Recognition</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="architecture">Architecture *</Label>
              <Select value={formData.architecture} onValueChange={(value) => handleChange('architecture', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="transformer">Transformer</SelectItem>
                  <SelectItem value="melotts">MeloTTS</SelectItem>
                  <SelectItem value="styletts">StyleTTS</SelectItem>
                  <SelectItem value="whisper">Whisper</SelectItem>
                  <SelectItem value="llama">LLaMA</SelectItem>
                  <SelectItem value="custom">Custom</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="version">Version *</Label>
              <Input
                id="version"
                value={formData.version}
                onChange={(e) => handleChange('version', e.target.value)}
                placeholder="1.0.0"
                pattern="^\d+\.\d+\.\d+$"
                required
              />
            </div>

            <div>
              <Label htmlFor="languages">Languages (comma-separated) *</Label>
              <Input
                id="languages"
                value={formData.languages}
                onChange={(e) => handleChange('languages', e.target.value)}
                placeholder="e.g., yo, en, fr"
                required
              />
            </div>

            <div className="col-span-2">
              <Label htmlFor="storage_path">Storage Path *</Label>
              <Input
                id="storage_path"
                value={formData.storage_path}
                onChange={(e) => handleChange('storage_path', e.target.value)}
                placeholder="/storage/models/yoruba-tts-v1"
                required
              />
            </div>

            <div className="col-span-2">
              <Label htmlFor="checkpoint_path">Checkpoint Path *</Label>
              <Input
                id="checkpoint_path"
                value={formData.checkpoint_path}
                onChange={(e) => handleChange('checkpoint_path', e.target.value)}
                placeholder="/storage/checkpoints/model.ckpt"
                required
              />
            </div>

            <div>
              <Label htmlFor="deployment_status">Deployment Status</Label>
              <Select value={formData.deployment_status} onValueChange={(value) => handleChange('deployment_status', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="experimental">Experimental</SelectItem>
                  <SelectItem value="staging">Staging</SelectItem>
                  <SelectItem value="production">Production</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="license">License</Label>
              <Select value={formData.license} onValueChange={(value) => handleChange('license', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MIT">MIT</SelectItem>
                  <SelectItem value="Apache-2.0">Apache 2.0</SelectItem>
                  <SelectItem value="GPL-3.0">GPL 3.0</SelectItem>
                  <SelectItem value="BSD-3-Clause">BSD 3-Clause</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Registering...
                </>
              ) : (
                'Register Model'
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
