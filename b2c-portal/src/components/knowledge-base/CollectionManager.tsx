/**
 * CollectionManager Component
 * Advanced collection management interface for the Collections tab
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Plus,
  Edit,
  Trash2,
  Copy,
  FileText,
  Loader2,
  Database,
  BarChart3,
  Calendar,
  RefreshCw,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface Collection {
  collection_id: string;
  name: string;
  company_name: string;
  display_name: string;
  description?: string;
  industry?: string;
  document_count: number;
  total_chunks: number;
  total_size_bytes: number;
  created_at?: string;
  last_updated?: string;
  total_queries: number;
  avg_confidence?: number;
}

interface CollectionManagerProps {
  apiBaseUrl: string;
  onCollectionChange?: () => void;
}

const CollectionManager: React.FC<CollectionManagerProps> = ({
  apiBaseUrl,
  onCollectionChange,
}) => {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [duplicateDialogOpen, setDuplicateDialogOpen] = useState(false);
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isClearingCache, setIsClearingCache] = useState(false);
  const { toast } = useToast();

  // Form states
  const [createForm, setCreateForm] = useState({
    company_name: '',
    display_name: '',
    description: '',
    industry: '',
    default_category: 'general',
  });

  const [editForm, setEditForm] = useState({
    display_name: '',
    description: '',
    industry: '',
    default_category: '',
  });

  const [duplicateForm, setDuplicateForm] = useState({
    target_company_name: '',
    copy_documents: true,
  });

  // Fetch collections
  const fetchCollections = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/knowledge-base/collections`);
      const data = await response.json();

      if (data.success) {
        setCollections(data.collections || []);
      }
    } catch (error) {
      console.error('Error fetching collections:', error);
      toast({
        title: 'Failed to Load Collections',
        description: 'Could not fetch collections from server',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCollections();
  }, [apiBaseUrl]);

  // Handle create collection
  const handleCreate = async () => {
    if (!createForm.company_name || !createForm.display_name) {
      toast({
        title: 'Validation Error',
        description: 'Company name and display name are required',
        variant: 'destructive',
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(`${apiBaseUrl}/knowledge-base/collections/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(createForm),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to create collection');
      }

      toast({
        title: 'Collection Created',
        description: `"${createForm.display_name}" has been created successfully`,
      });

      setCreateDialogOpen(false);
      setCreateForm({
        company_name: '',
        display_name: '',
        description: '',
        industry: '',
        default_category: 'general',
      });

      fetchCollections();
      onCollectionChange?.();
    } catch (error) {
      console.error('Create error:', error);
      toast({
        title: 'Creation Failed',
        description: error instanceof Error ? error.message : 'Could not create collection',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle update collection
  const handleUpdate = async () => {
    if (!selectedCollection || !editForm.display_name) {
      toast({
        title: 'Validation Error',
        description: 'Display name is required',
        variant: 'destructive',
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(
        `${apiBaseUrl}/knowledge-base/collections/${selectedCollection.company_name}/update`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(editForm),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to update collection');
      }

      toast({
        title: 'Collection Updated',
        description: `"${editForm.display_name}" has been updated successfully`,
      });

      setEditDialogOpen(false);
      setSelectedCollection(null);

      fetchCollections();
      onCollectionChange?.();
    } catch (error) {
      console.error('Update error:', error);
      toast({
        title: 'Update Failed',
        description: error instanceof Error ? error.message : 'Could not update collection',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle delete collection
  const handleDelete = async () => {
    if (!selectedCollection) return;

    setIsSubmitting(true);
    try {
      const response = await fetch(`${apiBaseUrl}/knowledge-base/collections/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_name: selectedCollection.company_name,
          delete_query_metrics: false,
          confirmation: 'DELETE',
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to delete collection');
      }

      toast({
        title: 'Collection Deleted',
        description: `"${selectedCollection.display_name}" has been deleted (${data.documents_deleted} documents)`,
      });

      setDeleteDialogOpen(false);
      setSelectedCollection(null);

      fetchCollections();
      onCollectionChange?.();
    } catch (error) {
      console.error('Delete error:', error);
      toast({
        title: 'Deletion Failed',
        description: error instanceof Error ? error.message : 'Could not delete collection',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle duplicate collection
  const handleDuplicate = async () => {
    if (!selectedCollection || !duplicateForm.target_company_name) {
      toast({
        title: 'Validation Error',
        description: 'Target company name is required',
        variant: 'destructive',
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(`${apiBaseUrl}/knowledge-base/collections/duplicate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_company_name: selectedCollection.company_name,
          target_company_name: duplicateForm.target_company_name,
          copy_documents: duplicateForm.copy_documents,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to duplicate collection');
      }

      toast({
        title: 'Collection Duplicated',
        description: `Collection duplicated successfully. ${duplicateForm.copy_documents ? 'Document copying in progress.' : ''}`,
      });

      setDuplicateDialogOpen(false);
      setSelectedCollection(null);
      setDuplicateForm({ target_company_name: '', copy_documents: true });

      fetchCollections();
      onCollectionChange?.();
    } catch (error) {
      console.error('Duplicate error:', error);
      toast({
        title: 'Duplication Failed',
        description: error instanceof Error ? error.message : 'Could not duplicate collection',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Open edit dialog
  const openEditDialog = (collection: Collection) => {
    setSelectedCollection(collection);
    setEditForm({
      display_name: collection.display_name,
      description: collection.description || '',
      industry: collection.industry || '',
      default_category: 'general',
    });
    setEditDialogOpen(true);
  };

  // Open duplicate dialog
  const openDuplicateDialog = (collection: Collection) => {
    setSelectedCollection(collection);
    setDuplicateForm({
      target_company_name: `${collection.company_name}_copy`,
      copy_documents: true,
    });
    setDuplicateDialogOpen(true);
  };

  // Open delete dialog
  const openDeleteDialog = (collection: Collection) => {
    setSelectedCollection(collection);
    setDeleteDialogOpen(true);
  };

  // Handle cache clearing
  const handleClearCache = async (collection: Collection) => {
    setIsClearingCache(true);
    try {
      const response = await fetch(
        `${apiBaseUrl}/knowledge-base/${collection.company_name}/precompute/cache`,
        {
          method: 'DELETE',
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to clear cache');
      }

      toast({
        title: 'Cache Cleared',
        description: `Cache cleared for "${collection.display_name}". ${data.queries_deleted || 0} cached queries removed.`,
      });
    } catch (error) {
      console.error('Cache clear error:', error);
      toast({
        title: 'Cache Clear Failed',
        description: error instanceof Error ? error.message : 'Could not clear cache',
        variant: 'destructive',
      });
    } finally {
      setIsClearingCache(false);
    }
  };

  // Format date
  const formatDate = (dateStr?: string): string => {
    if (!dateStr) return 'N/A';
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return 'N/A';
    }
  };

  // Format number
  const formatNumber = (num: number): string => {
    return num.toLocaleString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold">Collection Management</h2>
          <p className="text-gray-600 mt-1">
            Create, update, and manage your knowledge base collections
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Collection
        </Button>
      </div>

      {/* Collections Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Collections</CardTitle>
          <CardDescription>
            Manage all knowledge base collections in your organization
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
            </div>
          ) : collections.length === 0 ? (
            <div className="text-center py-12">
              <Database className="h-12 w-12 text-gray-600/50 mx-auto mb-4" />
              <p className="text-gray-600 font-medium">No collections yet</p>
              <p className="text-sm text-gray-600/70 mt-1">
                Create your first collection to get started
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Industry</TableHead>
                  <TableHead className="text-right">Documents</TableHead>
                  <TableHead className="text-right">Chunks</TableHead>
                  <TableHead className="text-right">Queries</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {collections.map((collection) => (
                  <TableRow key={collection.collection_id}>
                    <TableCell>
                      <div>
                        <div className="font-semibold">{collection.display_name}</div>
                        <div className="text-xs text-gray-600">
                          {collection.company_name}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {collection.industry ? (
                        <Badge variant="secondary">{collection.industry}</Badge>
                      ) : (
                        <span className="text-gray-600 text-sm">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <FileText className="h-3 w-3 text-gray-600" />
                        {formatNumber(collection.document_count)}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      {formatNumber(collection.total_chunks)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <BarChart3 className="h-3 w-3 text-gray-600" />
                        {formatNumber(collection.total_queries)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-sm text-gray-600">
                        <Calendar className="h-3 w-3" />
                        {formatDate(collection.created_at)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleClearCache(collection)}
                          title="Clear Cache"
                          disabled={isClearingCache}
                        >
                          <RefreshCw className={`h-4 w-4 ${isClearingCache ? 'animate-spin' : ''}`} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openEditDialog(collection)}
                          title="Edit Collection"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openDuplicateDialog(collection)}
                          title="Duplicate Collection"
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openDeleteDialog(collection)}
                          title="Delete Collection"
                          className="text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create Collection Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="sm:max-w-[550px]">
          <DialogHeader>
            <DialogTitle>Create New Collection</DialogTitle>
            <DialogDescription>
              Create a new knowledge base collection for organizing documents
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="create-company-name">
                Company Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="create-company-name"
                placeholder="e.g., acme_corp_support"
                value={createForm.company_name}
                onChange={(e) =>
                  setCreateForm({ ...createForm, company_name: e.target.value })
                }
              />
              <p className="text-xs text-gray-600">
                Unique identifier (lowercase, underscores only)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="create-display-name">
                Display Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="create-display-name"
                placeholder="e.g., Acme Corp Support"
                value={createForm.display_name}
                onChange={(e) =>
                  setCreateForm({ ...createForm, display_name: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="create-industry">Industry</Label>
              <Input
                id="create-industry"
                placeholder="e.g., Healthcare, Finance, Retail"
                value={createForm.industry}
                onChange={(e) => setCreateForm({ ...createForm, industry: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="create-description">Description</Label>
              <Textarea
                id="create-description"
                placeholder="Describe the purpose of this collection..."
                rows={3}
                value={createForm.description}
                onChange={(e) =>
                  setCreateForm({ ...createForm, description: e.target.value })
                }
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCreateDialogOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Collection
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Collection Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="sm:max-w-[550px]">
          <DialogHeader>
            <DialogTitle>Edit Collection</DialogTitle>
            <DialogDescription>
              Update collection metadata and settings
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-display-name">
                Display Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="edit-display-name"
                value={editForm.display_name}
                onChange={(e) => setEditForm({ ...editForm, display_name: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-industry">Industry</Label>
              <Input
                id="edit-industry"
                value={editForm.industry}
                onChange={(e) => setEditForm({ ...editForm, industry: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-description">Description</Label>
              <Textarea
                id="edit-description"
                rows={3}
                value={editForm.description}
                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setEditDialogOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button onClick={handleUpdate} disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Updating...
                </>
              ) : (
                'Save Changes'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Duplicate Collection Dialog */}
      <Dialog open={duplicateDialogOpen} onOpenChange={setDuplicateDialogOpen}>
        <DialogContent className="sm:max-w-[550px]">
          <DialogHeader>
            <DialogTitle>Duplicate Collection</DialogTitle>
            <DialogDescription>
              Create a copy of "{selectedCollection?.display_name}"
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="duplicate-target">
                Target Company Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="duplicate-target"
                value={duplicateForm.target_company_name}
                onChange={(e) =>
                  setDuplicateForm({ ...duplicateForm, target_company_name: e.target.value })
                }
                placeholder="e.g., acme_corp_support_v2"
              />
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="copy-documents"
                checked={duplicateForm.copy_documents}
                onChange={(e) =>
                  setDuplicateForm({ ...duplicateForm, copy_documents: e.target.checked })
                }
                className="h-4 w-4"
              />
              <Label htmlFor="copy-documents">Copy all documents</Label>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDuplicateDialogOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button onClick={handleDuplicate} disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Duplicating...
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-2" />
                  Duplicate
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Collection Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Collection?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete "{selectedCollection?.display_name}" and all its:
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>{formatNumber(selectedCollection?.document_count || 0)} documents</li>
                <li>{formatNumber(selectedCollection?.total_chunks || 0)} vector embeddings</li>
                <li>Query metrics and analytics data</li>
              </ul>
              <p className="mt-3 font-semibold text-destructive">
                This action cannot be undone!
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isSubmitting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={isSubmitting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                <>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Collection
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default CollectionManager;
