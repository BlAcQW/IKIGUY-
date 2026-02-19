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

interface PipelineCreationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const PipelineCreationModal = ({ isOpen, onClose, onSuccess }: PipelineCreationModalProps) => {
  const { user } = useBackendAuth();
  const { showSuccess, showError } = useNotification();

  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    model_type: 'tts',
    current_stage: 'data_acquisition',
    priority: 'medium',
    target_languages: '',
    framework: 'pytorch'
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!user) {
      showError('Please sign in to create pipelines');
      return;
    }

    try {
      setLoading(true);
      const token = localStorage.getItem('auth_access_token');

      const payload = {
        ...formData,
        target_languages: formData.target_languages.split(',').map(l => l.trim()).filter(l => l),
        is_active: true
      };

      const response = await fetch(`${API_BASE}/pipelines`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create pipeline');
      }

      showSuccess('Pipeline created successfully!');
      onClose();
      if (onSuccess) onSuccess();
    } catch (error: any) {
      console.error('Failed to create pipeline:', error);
      showError(error.message || 'Failed to create pipeline');
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
          <DialogTitle>Create Training Pipeline</DialogTitle>
          <DialogDescription>
            Set up a new ML training pipeline for African language models
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <Label htmlFor="name">Pipeline Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                placeholder="e.g., Yoruba ASR Training Pipeline"
                required
              />
            </div>

            <div className="col-span-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                placeholder="Brief description of the training pipeline..."
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
              <Label htmlFor="priority">Priority</Label>
              <Select value={formData.priority} onValueChange={(value) => handleChange('priority', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="current_stage">Starting Stage</Label>
              <Select value={formData.current_stage} onValueChange={(value) => handleChange('current_stage', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="data_acquisition">Data Acquisition</SelectItem>
                  <SelectItem value="preprocessing">Preprocessing</SelectItem>
                  <SelectItem value="training">Training</SelectItem>
                  <SelectItem value="evaluation">Evaluation</SelectItem>
                  <SelectItem value="deployment">Deployment</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="framework">Framework</Label>
              <Select value={formData.framework} onValueChange={(value) => handleChange('framework', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pytorch">PyTorch</SelectItem>
                  <SelectItem value="tensorflow">TensorFlow</SelectItem>
                  <SelectItem value="jax">JAX</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="col-span-2">
              <Label htmlFor="target_languages">Target Languages (comma-separated)</Label>
              <Input
                id="target_languages"
                value={formData.target_languages}
                onChange={(e) => handleChange('target_languages', e.target.value)}
                placeholder="e.g., yo, ha, ig"
              />
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
                  Creating...
                </>
              ) : (
                'Create Pipeline'
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
