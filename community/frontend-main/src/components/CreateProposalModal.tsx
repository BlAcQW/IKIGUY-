import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, FileText, Eye } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface CreateProposalModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function CreateProposalModal({
  open,
  onOpenChange,
  onSuccess
}: CreateProposalModalProps) {
  const { toast } = useToast();
  const [creating, setCreating] = useState(false);
  const [activeTab, setActiveTab] = useState('edit');

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '',
    duration: '7'
  });

  const categories = [
    { value: 'language_addition', label: 'Language Addition' },
    { value: 'policy_change', label: 'Policy Change' },
    { value: 'feature_request', label: 'Feature Request' },
    { value: 'resource_allocation', label: 'Resource Allocation' },
    { value: 'other', label: 'Other' }
  ];

  const durations = [
    { value: '3', label: '3 Days' },
    { value: '7', label: '7 Days' },
    { value: '14', label: '14 Days' },
    { value: '30', label: '30 Days' }
  ];

  const handleSubmit = async () => {
    // Validation
    if (!formData.title.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Title is required',
        variant: 'destructive'
      });
      return;
    }

    if (formData.title.length > 100) {
      toast({
        title: 'Validation Error',
        description: 'Title must be 100 characters or less',
        variant: 'destructive'
      });
      return;
    }

    if (!formData.description.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Description is required',
        variant: 'destructive'
      });
      return;
    }

    if (formData.description.length < 50) {
      toast({
        title: 'Validation Error',
        description: 'Description must be at least 50 characters',
        variant: 'destructive'
      });
      return;
    }

    if (formData.description.length > 2000) {
      toast({
        title: 'Validation Error',
        description: 'Description must be 2000 characters or less',
        variant: 'destructive'
      });
      return;
    }

    if (!formData.category) {
      toast({
        title: 'Validation Error',
        description: 'Category is required',
        variant: 'destructive'
      });
      return;
    }

    try {
      setCreating(true);

      await apiClient.createCommunityProposal({
        title: formData.title,
        description: formData.description,
        category: formData.category,
        duration_days: parseInt(formData.duration)
      });

      toast({
        title: 'Proposal Created',
        description: 'Your proposal has been submitted to the community for voting'
      });

      // Reset form
      setFormData({
        title: '',
        description: '',
        category: '',
        duration: '7'
      });
      setActiveTab('edit');

      onOpenChange(false);
      if (onSuccess) onSuccess();
    } catch (error) {
      console.error('Failed to create proposal:', error);
      toast({
        title: 'Creation Failed',
        description: error instanceof Error ? error.message : 'Failed to create proposal. Please try again.',
        variant: 'destructive'
      });
    } finally {
      setCreating(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      title: '',
      description: '',
      category: '',
      duration: '7'
    });
    setActiveTab('edit');
    onOpenChange(false);
  };

  // Simple markdown-like preview (basic formatting)
  const renderPreview = (text: string) => {
    return text
      .split('\n\n')
      .map((para, i) => (
        <p key={i} className="mb-4 last:mb-0">
          {para}
        </p>
      ));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Community Proposal</DialogTitle>
          <DialogDescription>
            Submit a proposal for the community to vote on. All proposals require majority support to pass.
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="edit">
              <FileText className="h-4 w-4 mr-2" />
              Edit
            </TabsTrigger>
            <TabsTrigger value="preview">
              <Eye className="h-4 w-4 mr-2" />
              Preview
            </TabsTrigger>
          </TabsList>

          <TabsContent value="edit" className="space-y-4 mt-4">
            {/* Title */}
            <div className="space-y-2">
              <Label htmlFor="title">
                Title * <span className="text-xs text-muted-foreground">({formData.title.length}/100)</span>
              </Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="Summarize your proposal in a clear, concise title"
                maxLength={100}
              />
            </div>

            {/* Category */}
            <div className="space-y-2">
              <Label htmlFor="category">Category *</Label>
              <Select value={formData.category} onValueChange={(value) => setFormData({ ...formData, category: value })}>
                <SelectTrigger id="category">
                  <SelectValue placeholder="Select proposal category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((cat) => (
                    <SelectItem key={cat.value} value={cat.value}>
                      {cat.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">
                Description * <span className="text-xs text-muted-foreground">({formData.description.length}/2000, min 50)</span>
              </Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Provide a detailed description of your proposal. What problem does it solve? What are the benefits? Are there any potential drawbacks?"
                rows={10}
                maxLength={2000}
              />
              <p className="text-xs text-muted-foreground">
                Tip: Use paragraphs to organize your thoughts. Leave blank lines between paragraphs.
              </p>
            </div>

            {/* Duration */}
            <div className="space-y-2">
              <Label htmlFor="duration">Voting Duration *</Label>
              <Select value={formData.duration} onValueChange={(value) => setFormData({ ...formData, duration: value })}>
                <SelectTrigger id="duration">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {durations.map((dur) => (
                    <SelectItem key={dur.value} value={dur.value}>
                      {dur.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                How long should the community have to vote on this proposal?
              </p>
            </div>
          </TabsContent>

          <TabsContent value="preview" className="mt-4">
            <div className="border rounded-lg p-6 bg-muted/30 min-h-[400px]">
              {formData.title || formData.description ? (
                <>
                  <h2 className="text-2xl font-bold mb-4">{formData.title || 'Untitled Proposal'}</h2>
                  {formData.category && (
                    <div className="mb-4">
                      <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                        {categories.find(c => c.value === formData.category)?.label}
                      </span>
                    </div>
                  )}
                  <div className="prose prose-sm max-w-none">
                    {formData.description ? (
                      renderPreview(formData.description)
                    ) : (
                      <p className="text-muted-foreground italic">No description provided</p>
                    )}
                  </div>
                  <div className="mt-6 pt-4 border-t text-sm text-muted-foreground">
                    Voting period: {durations.find(d => d.value === formData.duration)?.label}
                  </div>
                </>
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  <p>Preview will appear here as you type...</p>
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel} disabled={creating}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={creating || !formData.title || !formData.description || !formData.category}
          >
            {creating ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              'Submit Proposal'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
