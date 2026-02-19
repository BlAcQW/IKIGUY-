import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface SubmissionEditModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  submission: any; // The submission to edit
  onSuccess?: () => void;
}

export function SubmissionEditModal({
  open,
  onOpenChange,
  submission,
  onSuccess
}: SubmissionEditModalProps) {
  const { toast } = useToast();
  const [updating, setUpdating] = useState(false);

  // Form state based on submission type
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    content: '',
    url: '',
    language_code: '',
    tags: '',
    category: ''
  });

  // Initialize form with submission data
  useEffect(() => {
    if (submission && open) {
      setFormData({
        title: submission.title || '',
        description: submission.description || '',
        content: submission.content || '',
        url: submission.url || '',
        language_code: submission.language_code || '',
        tags: Array.isArray(submission.tags) ? submission.tags.join(', ') : (submission.tags || ''),
        category: submission.category || submission.submission_type || ''
      });
    }
  }, [submission, open]);

  const submissionType = submission?.type || submission?.submission_type || 'text';

  const handleUpdate = async () => {
    // Validate required fields
    if (!formData.title?.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Title is required',
        variant: 'destructive'
      });
      return;
    }

    if (submissionType === 'text' && !formData.content?.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Content is required for text submissions',
        variant: 'destructive'
      });
      return;
    }

    if (submissionType === 'link' && !formData.url?.trim()) {
      toast({
        title: 'Validation Error',
        description: 'URL is required for link submissions',
        variant: 'destructive'
      });
      return;
    }

    try {
      setUpdating(true);

      // Prepare update payload
      const updates: any = {
        title: formData.title,
        description: formData.description,
        language_code: formData.language_code,
      };

      // Add tags if provided
      if (formData.tags) {
        updates.tags = formData.tags.split(',').map((tag: string) => tag.trim()).filter(Boolean);
      }

      // Add type-specific fields
      if (submissionType === 'text') {
        updates.content = formData.content;
        if (formData.category) updates.category = formData.category;
      } else if (submissionType === 'link') {
        updates.url = formData.url;
      }

      await apiClient.updateSubmission(submission.id, updates);

      toast({
        title: 'Success',
        description: 'Submission updated successfully'
      });

      onOpenChange(false);
      if (onSuccess) onSuccess();
    } catch (error) {
      console.error('Failed to update submission:', error);
      toast({
        title: 'Update Failed',
        description: error instanceof Error ? error.message : 'Failed to update submission',
        variant: 'destructive'
      });
    } finally {
      setUpdating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Submission</DialogTitle>
          <DialogDescription>
            Update your {submissionType} submission. Note: Audio files cannot be changed after upload.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Title *</Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="Enter submission title"
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Provide additional context or details"
              rows={3}
            />
          </div>

          {/* Language Code */}
          <div className="space-y-2">
            <Label htmlFor="language_code">Language Code</Label>
            <Input
              id="language_code"
              value={formData.language_code}
              onChange={(e) => setFormData({ ...formData, language_code: e.target.value })}
              placeholder="e.g., swa, hau, yor"
            />
          </div>

          {/* Text Content (for text submissions) */}
          {submissionType === 'text' && (
            <>
              <div className="space-y-2">
                <Label htmlFor="content">Content *</Label>
                <Textarea
                  id="content"
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  placeholder="Enter your text content"
                  rows={6}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="category">Category</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) => setFormData({ ...formData, category: value })}
                >
                  <SelectTrigger id="category">
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="story">Story</SelectItem>
                    <SelectItem value="proverb">Proverb</SelectItem>
                    <SelectItem value="poem">Poem</SelectItem>
                    <SelectItem value="conversation">Conversation</SelectItem>
                    <SelectItem value="news">News</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </>
          )}

          {/* URL (for link submissions) */}
          {submissionType === 'link' && (
            <div className="space-y-2">
              <Label htmlFor="url">URL *</Label>
              <Input
                id="url"
                type="url"
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                placeholder="https://example.com/resource"
              />
            </div>
          )}

          {/* Tags */}
          <div className="space-y-2">
            <Label htmlFor="tags">Tags (comma-separated)</Label>
            <Input
              id="tags"
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
              placeholder="tag1, tag2, tag3"
            />
          </div>

          {/* Audio note */}
          {submissionType === 'audio' && (
            <div className="p-3 bg-muted rounded-lg text-sm text-muted-foreground">
              <p>Note: Audio files cannot be modified. You can only update the title, description, and metadata.</p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={updating}>
            Cancel
          </Button>
          <Button onClick={handleUpdate} disabled={updating}>
            {updating ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Updating...
              </>
            ) : (
              'Update Submission'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
