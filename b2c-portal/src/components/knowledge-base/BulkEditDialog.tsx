/**
 * BulkEditDialog Component
 * Unified dialog for bulk editing tags, category, and status for multiple documents
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, Tag, FolderOpen, AlertCircle, X, Plus } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface BulkEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  apiBaseUrl: string;
  companyName: string;
  selectedDocumentIds: string[];
  onSuccess?: () => void;
}

const BulkEditDialog: React.FC<BulkEditDialogProps> = ({
  open,
  onOpenChange,
  apiBaseUrl,
  companyName,
  selectedDocumentIds,
  onSuccess,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  // Tag operations
  const [tagOperation, setTagOperation] = useState<'add' | 'remove' | 'replace'>('add');
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>([]);

  // Category operation
  const [newCategory, setNewCategory] = useState('');

  // Status operation
  const [newStatus, setNewStatus] = useState('');

  // Add tag to list
  const handleAddTag = () => {
    const trimmed = tagInput.trim();
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed]);
      setTagInput('');
    }
  };

  // Remove tag from list
  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((t) => t !== tagToRemove));
  };

  // Handle bulk update
  const handleBulkUpdate = async () => {
    // Validate at least one operation
    const hasTagOperation = tags.length > 0;
    const hasCategoryOperation = newCategory.trim() !== '';
    const hasStatusOperation = newStatus !== '';

    if (!hasTagOperation && !hasCategoryOperation && !hasStatusOperation) {
      toast({
        title: 'No Changes',
        description: 'Please specify at least one update operation',
        variant: 'destructive',
      });
      return;
    }

    setIsSubmitting(true);

    try {
      // Build request body
      const requestBody: any = {
        company_name: companyName,
        document_ids: selectedDocumentIds,
      };

      // Add tag operations
      if (hasTagOperation) {
        if (tagOperation === 'add') {
          requestBody.add_tags = tags;
        } else if (tagOperation === 'remove') {
          requestBody.remove_tags = tags;
        } else if (tagOperation === 'replace') {
          requestBody.replace_tags = tags;
        }
      }

      // Add category operation
      if (hasCategoryOperation) {
        requestBody.set_category = newCategory.trim();
      }

      // Add status operation
      if (hasStatusOperation) {
        requestBody.set_status = newStatus;
      }

      const response = await fetch(`${apiBaseUrl}/knowledge-base/documents/bulk-update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to update documents');
      }

      toast({
        title: 'Bulk Update Complete',
        description: `Updated ${data.updated_count} document${data.updated_count !== 1 ? 's' : ''}${
          data.failed_count > 0 ? `. Failed: ${data.failed_count}` : ''
        }`,
      });

      // Reset form
      setTags([]);
      setTagInput('');
      setNewCategory('');
      setNewStatus('');

      onSuccess?.();
      onOpenChange(false);
    } catch (error) {
      console.error('Bulk update error:', error);
      toast({
        title: 'Update Failed',
        description: error instanceof Error ? error.message : 'Could not update documents',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle>Bulk Edit Documents</DialogTitle>
          <DialogDescription>
            Edit {selectedDocumentIds.length} selected document{selectedDocumentIds.length !== 1 ? 's' : ''}
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="tags" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="tags">
              <Tag className="h-4 w-4 mr-2" />
              Tags
            </TabsTrigger>
            <TabsTrigger value="category">
              <FolderOpen className="h-4 w-4 mr-2" />
              Category
            </TabsTrigger>
            <TabsTrigger value="status">
              <AlertCircle className="h-4 w-4 mr-2" />
              Status
            </TabsTrigger>
          </TabsList>

          {/* Tags Tab */}
          <TabsContent value="tags" className="space-y-4">
            <div className="space-y-3">
              <Label>Tag Operation</Label>
              <Select value={tagOperation} onValueChange={(v: any) => setTagOperation(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="add">Add tags</SelectItem>
                  <SelectItem value="remove">Remove tags</SelectItem>
                  <SelectItem value="replace">Replace all tags</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <Label>
                {tagOperation === 'add'
                  ? 'Tags to Add'
                  : tagOperation === 'remove'
                  ? 'Tags to Remove'
                  : 'New Tags'}
              </Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Enter tag name..."
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddTag();
                    }
                  }}
                />
                <Button type="button" variant="outline" onClick={handleAddTag}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>

              {tags.length > 0 && (
                <div className="flex flex-wrap gap-2 p-3 bg-muted rounded-md">
                  {tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="gap-1">
                      {tag}
                      <X
                        className="h-3 w-3 cursor-pointer hover:text-destructive"
                        onClick={() => handleRemoveTag(tag)}
                      />
                    </Badge>
                  ))}
                </div>
              )}

              <p className="text-xs text-gray-600">
                {tagOperation === 'add' && 'Tags will be added to existing tags on each document'}
                {tagOperation === 'remove' && 'Specified tags will be removed from documents'}
                {tagOperation === 'replace' && 'All existing tags will be replaced with these tags'}
              </p>
            </div>
          </TabsContent>

          {/* Category Tab */}
          <TabsContent value="category" className="space-y-4">
            <div className="space-y-3">
              <Label htmlFor="bulk-category">New Category</Label>
              <Input
                id="bulk-category"
                placeholder="e.g., policies, procedures, guides"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
              />
              <p className="text-xs text-gray-600">
                All selected documents will be assigned this category
              </p>
            </div>

            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-amber-900">
                  <p className="font-medium">This will overwrite existing categories</p>
                  <p className="mt-1">The current category for each document will be replaced</p>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Status Tab */}
          <TabsContent value="status" className="space-y-4">
            <div className="space-y-3">
              <Label htmlFor="bulk-status">New Status</Label>
              <Select value={newStatus} onValueChange={setNewStatus}>
                <SelectTrigger>
                  <SelectValue placeholder="Select status..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="processing">Processing</SelectItem>
                  <SelectItem value="indexed">Indexed</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                  <SelectItem value="archived">Archived</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-600">
                All selected documents will be assigned this status
              </p>
            </div>

            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-blue-900">
                  <p className="font-medium">Status affects document availability</p>
                  <p className="mt-1">
                    Only 'indexed' documents are available for RAG queries. Use with caution.
                  </p>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button onClick={handleBulkUpdate} disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Updating...
              </>
            ) : (
              `Update ${selectedDocumentIds.length} Document${selectedDocumentIds.length !== 1 ? 's' : ''}`
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default BulkEditDialog;
