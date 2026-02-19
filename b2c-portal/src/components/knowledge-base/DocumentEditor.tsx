import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  X,
  Save,
  Loader2,
  AlertCircle,
  Tag,
  FileText,
  Edit,
  History,
} from 'lucide-react';
import { KnowledgeDocument } from './types';
import { useToast } from '@/hooks/use-toast';

interface DocumentEditorProps {
  document: KnowledgeDocument;
  apiBaseUrl: string;
  onSave?: (doc: KnowledgeDocument) => void;
  onCancel?: () => void;
}

const DocumentEditor: React.FC<DocumentEditorProps> = ({
  document,
  apiBaseUrl,
  onSave,
  onCancel,
}) => {
  const [isSaving, setIsSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const { toast } = useToast();

  // Form state
  const [formData, setFormData] = useState({
    title: document.title,
    content: document.content,
    category: document.category,
    tags: document.tags.join(', '),
    is_active: document.is_active,
    is_archived: document.is_archived,
    change_reason: '',
  });

  // Character counts
  const [titleCount, setTitleCount] = useState(document.title.length);
  const [contentWordCount, setContentWordCount] = useState(
    document.content.split(/\s+/).filter(Boolean).length
  );
  const [contentCharCount, setContentCharCount] = useState(document.content.length);

  // Update counts when content changes
  useEffect(() => {
    setTitleCount(formData.title.length);
    setContentWordCount(formData.content.split(/\s+/).filter(Boolean).length);
    setContentCharCount(formData.content.length);
  }, [formData.title, formData.content]);

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    } else if (formData.title.length > 500) {
      newErrors.title = 'Title must be 500 characters or less';
    }

    if (!formData.content.trim()) {
      newErrors.content = 'Content is required';
    } else if (formData.content.length < 10) {
      newErrors.content = 'Content must be at least 10 characters';
    }

    if (!formData.category.trim()) {
      newErrors.category = 'Category is required';
    }

    if (!formData.change_reason.trim()) {
      newErrors.change_reason = 'Please provide a reason for this change';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle save
  const handleSave = async () => {
    if (!validateForm()) {
      toast({
        title: 'Validation Error',
        description: 'Please fix the errors before saving',
        variant: 'destructive',
      });
      return;
    }

    setIsSaving(true);

    try {
      // Parse tags
      const tags = formData.tags
        .split(',')
        .map(tag => tag.trim())
        .filter(Boolean);

      // Prepare update payload
      const updatePayload = {
        title: formData.title,
        content: formData.content,
        category: formData.category,
        tags: tags,
        is_active: formData.is_active,
        is_archived: formData.is_archived,
        change_reason: formData.change_reason,
        updated_by: 'user', // TODO: Replace with actual user ID from auth context
      };

      const response = await fetch(
        `${apiBaseUrl}/knowledge-base/documents/${document.id}?company_name=${encodeURIComponent(document.company_name)}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updatePayload),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to update document');
      }

      const data = await response.json();

      if (data.success) {
        toast({
          title: 'Document Updated',
          description: `"${formData.title}" has been updated successfully`,
        });

        // Call onSave callback with updated document
        if (onSave && data.document) {
          onSave(data.document);
        }
      } else {
        throw new Error(data.message || 'Failed to update document');
      }
    } catch (error) {
      console.error('Save error:', error);
      toast({
        title: 'Save Failed',
        description: error instanceof Error ? error.message : 'Could not save document',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  // Handle input change
  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  // Check if form has changes
  const hasChanges = () => {
    const currentTags = formData.tags
      .split(',')
      .map(tag => tag.trim())
      .filter(Boolean)
      .sort()
      .join(',');
    const originalTags = document.tags.sort().join(',');

    return (
      formData.title !== document.title ||
      formData.content !== document.content ||
      formData.category !== document.category ||
      currentTags !== originalTags ||
      formData.is_active !== document.is_active ||
      formData.is_archived !== document.is_archived
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <Edit className="h-6 w-6 text-blue-600" />
            <div>
              <h2 className="text-2xl font-semibold">Edit Document</h2>
              <p className="text-sm text-gray-500 mt-1">
                Version {document.current_version} • Last updated {new Date(document.updated_at).toLocaleDateString()}
              </p>
            </div>
          </div>

          <Button size="sm" variant="ghost" onClick={onCancel}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Form */}
        <div className="flex-1 overflow-auto p-6">
          <div className="space-y-6">
            {/* Title */}
            <div>
              <Label htmlFor="title">
                Document Title <span className="text-red-500">*</span>
              </Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) => handleChange('title', e.target.value)}
                placeholder="Enter document title"
                className={errors.title ? 'border-red-500' : ''}
              />
              <div className="flex justify-between mt-1">
                {errors.title ? (
                  <p className="text-sm text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {errors.title}
                  </p>
                ) : (
                  <p className="text-xs text-gray-500">Enter a clear, descriptive title</p>
                )}
                <p className="text-xs text-gray-400">{titleCount}/500</p>
              </div>
            </div>

            {/* Category and Status */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="category">
                  Category <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="category"
                  value={formData.category}
                  onChange={(e) => handleChange('category', e.target.value)}
                  placeholder="e.g., policies, faq, products"
                  className={errors.category ? 'border-red-500' : ''}
                />
                {errors.category && (
                  <p className="text-sm text-red-500 mt-1 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {errors.category}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label>Status</Label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => handleChange('is_active', e.target.checked)}
                    />
                    <span className="text-sm">Active</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.is_archived}
                      onChange={(e) => handleChange('is_archived', e.target.checked)}
                    />
                    <span className="text-sm">Archived</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Tags */}
            <div>
              <Label htmlFor="tags">
                Tags <Tag className="h-3 w-3 inline ml-1" />
              </Label>
              <Input
                id="tags"
                value={formData.tags}
                onChange={(e) => handleChange('tags', e.target.value)}
                placeholder="Enter tags separated by commas"
              />
              <p className="text-xs text-gray-500 mt-1">
                Separate multiple tags with commas (e.g., important, customer-facing, policies)
              </p>
              {formData.tags && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {formData.tags
                    .split(',')
                    .map(tag => tag.trim())
                    .filter(Boolean)
                    .map((tag, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                </div>
              )}
            </div>

            {/* Content */}
            <div>
              <Label htmlFor="content">
                Content <span className="text-red-500">*</span>
              </Label>
              <Textarea
                id="content"
                value={formData.content}
                onChange={(e) => handleChange('content', e.target.value)}
                placeholder="Enter document content..."
                rows={15}
                className={errors.content ? 'border-red-500' : ''}
              />
              <div className="flex justify-between mt-1">
                {errors.content ? (
                  <p className="text-sm text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {errors.content}
                  </p>
                ) : (
                  <p className="text-xs text-gray-500">
                    {contentWordCount} words, {contentCharCount} characters
                  </p>
                )}
              </div>
            </div>

            {/* Change Reason */}
            <Card className="bg-yellow-50 border-yellow-200">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <History className="h-4 w-4" />
                  Change Reason <span className="text-red-500">*</span>
                </CardTitle>
                <CardDescription>
                  This will be saved in the document's version history
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Textarea
                  value={formData.change_reason}
                  onChange={(e) => handleChange('change_reason', e.target.value)}
                  placeholder="Briefly describe what changed and why..."
                  rows={3}
                  className={errors.change_reason ? 'border-red-500 bg-white' : 'bg-white'}
                />
                {errors.change_reason && (
                  <p className="text-sm text-red-500 mt-2 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {errors.change_reason}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Info Card */}
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="p-4">
                <div className="flex items-start gap-2">
                  <FileText className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div className="text-sm text-blue-900">
                    <p className="font-medium">Version History</p>
                    <p className="text-blue-700 mt-1">
                      Saving this document will create version {document.current_version + 1} and trigger
                      re-indexing in the knowledge base. The previous version will be preserved in the
                      history.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t bg-gray-50">
          <div className="text-sm text-gray-600">
            {hasChanges() ? (
              <span className="text-orange-600 font-medium">Unsaved changes</span>
            ) : (
              <span>No changes</span>
            )}
          </div>

          <div className="flex gap-3">
            <Button variant="outline" onClick={onCancel} disabled={isSaving}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={isSaving || !hasChanges()}>
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save Changes
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentEditor;
