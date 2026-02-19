import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface ReportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  entityType: 'submission' | 'comment' | 'notebook';
  entityId: string;
  entityTitle?: string;
}

export function ReportModal({
  open,
  onOpenChange,
  entityType,
  entityId,
  entityTitle
}: ReportModalProps) {
  const { toast } = useToast();
  const [reason, setReason] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const reasons = [
    { value: 'spam', label: 'Spam or misleading' },
    { value: 'inappropriate', label: 'Inappropriate content' },
    { value: 'offensive', label: 'Offensive or abusive' },
    { value: 'copyright', label: 'Copyright violation' },
    { value: 'low_quality', label: 'Low quality' },
    { value: 'other', label: 'Other' }
  ];

  const handleSubmit = async () => {
    if (!reason) {
      toast({
        title: 'Reason required',
        description: 'Please select a reason for reporting',
        variant: 'destructive'
      });
      return;
    }

    try {
      setSubmitting(true);

      await apiClient.submitReport({
        entity_type: entityType,
        entity_id: entityId,
        reason: reason,
        description: description || undefined
      });

      toast({
        title: 'Report Submitted',
        description: 'Thank you for helping keep our community safe. Our moderation team will review this report.'
      });

      // Reset form and close modal
      setReason('');
      setDescription('');
      onOpenChange(false);

    } catch (error) {
      console.error('Failed to submit report:', error);
      toast({
        title: 'Submission Failed',
        description: 'Failed to submit report. Please try again.',
        variant: 'destructive'
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Reset form when modal is closed
  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      setReason('');
      setDescription('');
    }
    onOpenChange(newOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Report {entityType}</DialogTitle>
          <DialogDescription>
            Help us keep the community safe by reporting inappropriate content.
            {entityTitle && (
              <span className="block mt-2 text-sm font-medium text-foreground">
                Reporting: {entityTitle}
              </span>
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Reason selector */}
          <div className="space-y-2">
            <Label htmlFor="reason">Reason *</Label>
            <Select value={reason} onValueChange={setReason}>
              <SelectTrigger id="reason">
                <SelectValue placeholder="Select a reason" />
              </SelectTrigger>
              <SelectContent>
                {reasons.map((r) => (
                  <SelectItem key={r.value} value={r.value}>
                    {r.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Optional description */}
          <div className="space-y-2">
            <Label htmlFor="description">Additional details (optional)</Label>
            <Textarea
              id="description"
              placeholder="Provide any additional context that might help us review this report..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              maxLength={500}
            />
            <p className="text-xs text-muted-foreground">
              {description.length}/500 characters
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!reason || submitting}>
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Submitting...
              </>
            ) : (
              'Submit Report'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
