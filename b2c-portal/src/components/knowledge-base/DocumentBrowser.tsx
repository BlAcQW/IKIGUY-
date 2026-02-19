import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import { Checkbox } from '@/components/ui/checkbox';
import {
  FileText,
  Search,
  Filter,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Eye,
  Edit,
  Trash2,
  Download,
  Tag,
  Calendar,
  CheckCircle,
  Clock,
  AlertCircle,
  XCircle,
  Archive,
  FileDown,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import ExportDialog from './ExportDialog';
import BulkEditDialog from './BulkEditDialog';

interface DocumentMetadata {
  word_count?: number;
  character_count?: number;
  chunk_count?: number;
  filename?: string;
  query_count?: number;
  reference_count?: number;
}

interface Document {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  status: 'pending' | 'processing' | 'indexed' | 'failed' | 'archived';
  source: string;
  created_at: string;
  updated_at: string;
  indexed_at?: string;
  metadata: DocumentMetadata;
  is_active: boolean;
  is_archived: boolean;
}

interface DocumentBrowserProps {
  companyName: string;
  apiBaseUrl: string;
  authToken?: string;
  organizationId?: string;
  onViewDocument?: (doc: Document) => void;
  onEditDocument?: (doc: Document) => void;
  onDeleteDocument?: (docId: string) => void;
}

const DocumentBrowser: React.FC<DocumentBrowserProps> = ({
  companyName,
  apiBaseUrl,
  authToken,
  organizationId,
  onViewDocument,
  onEditDocument,
  onDeleteDocument,
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set());
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [bulkEditDialogOpen, setBulkEditDialogOpen] = useState(false);
  const { toast } = useToast();

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [tagsFilter, setTagsFilter] = useState<string>('');
  const [showArchived, setShowArchived] = useState(false);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Fetch documents
  const fetchDocuments = useCallback(async () => {
    // Don't fetch if companyName is empty
    if (!companyName || companyName.trim() === '') {
      setLoading(false);
      setDocuments([]);
      setTotalPages(1);
      setTotalCount(0);
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString(),
        sort_by: sortBy,
        sort_order: sortOrder,
      });

      if (searchQuery) params.append('search_query', searchQuery);
      if (categoryFilter) params.append('category', categoryFilter);
      if (statusFilter) params.append('status', statusFilter);
      if (tagsFilter) params.append('tags', tagsFilter);
      if (showArchived) params.append('is_archived', 'true');

      // Build headers with authentication
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      if (organizationId) {
        headers['X-Organization-ID'] = organizationId;
      }

      const response = await fetch(
        `${apiBaseUrl}/knowledge-base/${encodeURIComponent(companyName)}/documents?${params}`,
        {
          method: 'GET',
          headers,
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch documents');
      }

      const data = await response.json();

      if (data.success) {
        setDocuments(data.documents);
        setTotalPages(data.total_pages);
        setTotalCount(data.total_count);
      } else {
        throw new Error(data.message || 'Failed to load documents');
      }
    } catch (error) {
      console.error('Fetch documents error:', error);
      toast({
        title: 'Failed to Load Documents',
        description: error instanceof Error ? error.message : 'Could not load documents',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [companyName, apiBaseUrl, authToken, organizationId, currentPage, searchQuery, categoryFilter, statusFilter, tagsFilter, showArchived, sortBy, sortOrder, toast]);

  // Reset to page 1 when company changes
  useEffect(() => {
    setCurrentPage(1);
    setDocuments([]);
    setSelectedDocs(new Set());
  }, [companyName]);

  // Load documents on mount and when filters change
  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Handle bulk selection
  const toggleSelectAll = () => {
    if (selectedDocs.size === documents.length) {
      setSelectedDocs(new Set());
    } else {
      setSelectedDocs(new Set(documents.map(doc => doc.id)));
    }
  };

  const toggleSelectDoc = (docId: string) => {
    const newSelected = new Set(selectedDocs);
    if (newSelected.has(docId)) {
      newSelected.delete(docId);
    } else {
      newSelected.add(docId);
    }
    setSelectedDocs(newSelected);
  };

  // Handle bulk delete
  const handleBulkDelete = async () => {
    if (selectedDocs.size === 0) {
      toast({
        title: 'No Documents Selected',
        description: 'Please select documents to delete',
        variant: 'destructive',
      });
      return;
    }

    if (!confirm(`Are you sure you want to delete ${selectedDocs.size} document(s)?`)) {
      return;
    }

    try {
      const response = await fetch(`${apiBaseUrl}/knowledge-base/documents/bulk-delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_name: companyName,
          document_ids: Array.from(selectedDocs),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to delete documents');
      }

      const data = await response.json();

      toast({
        title: 'Bulk Delete Complete',
        description: `Deleted ${data.deleted_count} document(s). Failed: ${data.failed_count}`,
      });

      setSelectedDocs(new Set());
      fetchDocuments();
    } catch (error) {
      console.error('Bulk delete error:', error);
      toast({
        title: 'Bulk Delete Failed',
        description: error instanceof Error ? error.message : 'Could not delete documents',
        variant: 'destructive',
      });
    }
  };

  // Status badge component
  const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
    const statusConfig = {
      pending: { icon: Clock, color: 'bg-yellow-100 text-yellow-800', label: 'Pending' },
      processing: { icon: Loader2, color: 'bg-blue-100 text-blue-800', label: 'Processing' },
      indexed: { icon: CheckCircle, color: 'bg-green-100 text-green-800', label: 'Indexed' },
      failed: { icon: XCircle, color: 'bg-red-100 text-red-800', label: 'Failed' },
      archived: { icon: Archive, color: 'bg-gray-100 text-gray-800', label: 'Archived' },
    };

    const config = statusConfig[status as keyof typeof statusConfig];
    const Icon = config.icon;

    return (
      <Badge className={`${config.color} flex items-center gap-1`} variant="outline">
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Document Browser</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Browse and manage {totalCount} document{totalCount !== 1 ? 's' : ''} in your knowledge base
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => setExportDialogOpen(true)}>
            <FileDown className="h-4 w-4 mr-2" />
            Export
          </Button>
          {selectedDocs.size > 0 && (
            <>
              <Button variant="outline" onClick={() => setBulkEditDialogOpen(true)}>
                <Edit className="h-4 w-4 mr-2" />
                Edit {selectedDocs.size} Selected
              </Button>
              <Button variant="destructive" onClick={handleBulkDelete}>
                <Trash2 className="h-4 w-4 mr-2" />
                Delete {selectedDocs.size} Selected
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters & Search
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search */}
          <div>
            <Label htmlFor="search">Search Documents</Label>
            <div className="flex gap-2">
              <Input
                id="search"
                placeholder="Search by title or content..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <Button onClick={() => fetchDocuments()}>
                <Search className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Filter Row */}
          <div className="grid grid-cols-4 gap-4">
            <div>
              <Label htmlFor="category">Category</Label>
              <Input
                id="category"
                placeholder="e.g., policies"
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="status">Status</Label>
              <Select value={statusFilter || "all"} onValueChange={(v) => setStatusFilter(v === "all" ? "" : v)}>
                <SelectTrigger>
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="processing">Processing</SelectItem>
                  <SelectItem value="indexed">Indexed</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                  <SelectItem value="archived">Archived</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="sort">Sort By</Label>
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="created_at">Created Date</SelectItem>
                  <SelectItem value="updated_at">Updated Date</SelectItem>
                  <SelectItem value="title">Title</SelectItem>
                  <SelectItem value="category">Category</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="order">Order</Label>
              <Select value={sortOrder} onValueChange={(v) => setSortOrder(v as 'asc' | 'desc')}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="desc">Newest First</SelectItem>
                  <SelectItem value="asc">Oldest First</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Additional Filters */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Checkbox
                id="show-archived"
                checked={showArchived}
                onCheckedChange={(checked) => setShowArchived(checked as boolean)}
              />
              <Label htmlFor="show-archived">Show Archived</Label>
            </div>
            <Button variant="outline" size="sm" onClick={() => {
              setSearchQuery('');
              setCategoryFilter('');
              setStatusFilter('');
              setTagsFilter('');
              setShowArchived(false);
              setCurrentPage(1);
            }}>
              Clear Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Documents List */}
      {loading ? (
        <Card>
          <CardContent className="p-12 flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </CardContent>
        </Card>
      ) : documents.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <FileText className="h-12 w-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400 font-medium">No documents found</p>
            <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">Try adjusting your filters or add new documents</p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-6">
            {/* Bulk select header */}
            <div className="flex items-center gap-2 pb-4 border-b dark:border-gray-700 mb-4">
              <Checkbox
                checked={selectedDocs.size === documents.length && documents.length > 0}
                onCheckedChange={toggleSelectAll}
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {selectedDocs.size > 0 ? `${selectedDocs.size} selected` : 'Select all'}
              </span>
            </div>

            {/* Document list */}
            <div className="space-y-4">
              {documents.map((doc) => (
                <div key={doc.id} className="flex items-start gap-4 p-4 border dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                  <Checkbox
                    checked={selectedDocs.has(doc.id)}
                    onCheckedChange={() => toggleSelectDoc(doc.id)}
                  />

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-semibold text-lg truncate text-gray-900 dark:text-gray-100">{doc.title}</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">{doc.content}</p>

                        <div className="flex flex-wrap items-center gap-2 mt-3">
                          <StatusBadge status={doc.status} />
                          <Badge variant="outline">{doc.category}</Badge>
                          {doc.tags.map((tag, idx) => (
                            <Badge key={idx} variant="secondary" className="text-xs">
                              <Tag className="h-3 w-3 mr-1" />
                              {tag}
                            </Badge>
                          ))}
                        </div>

                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {new Date(doc.created_at).toLocaleDateString()}
                          </span>
                          {doc.metadata.word_count && (
                            <span>{doc.metadata.word_count} words</span>
                          )}
                          {doc.metadata.query_count !== undefined && (
                            <span>{doc.metadata.query_count} queries</span>
                          )}
                        </div>
                      </div>

                      <div className="flex gap-2 ml-4">
                        {onViewDocument && (
                          <Button size="sm" variant="outline" onClick={() => onViewDocument(doc)} title="View Document">
                            <Eye className="h-4 w-4" />
                          </Button>
                        )}
                        {onEditDocument && (
                          <Button size="sm" variant="outline" onClick={() => onEditDocument(doc)} title="Edit Document">
                            <Edit className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedDocs(new Set([doc.id]));
                            setExportDialogOpen(true);
                          }}
                          title="Export Document"
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                        {onDeleteDocument && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              if (confirm('Are you sure you want to delete this document?')) {
                                onDeleteDocument(doc.id);
                                fetchDocuments();
                              }
                            }}
                            title="Delete Document"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Page {currentPage} of {totalPages} ({totalCount} total documents)
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage(currentPage - 1)}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage(currentPage + 1)}
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Export Dialog */}
      <ExportDialog
        open={exportDialogOpen}
        onOpenChange={setExportDialogOpen}
        apiBaseUrl={apiBaseUrl}
        companyName={companyName}
        selectedDocumentIds={Array.from(selectedDocs)}
        currentFilters={{
          category: categoryFilter,
          tags: tagsFilter,
          status: statusFilter,
          searchQuery: searchQuery,
        }}
        totalDocuments={totalCount}
        filteredDocuments={documents.length}
      />

      {/* Bulk Edit Dialog */}
      <BulkEditDialog
        open={bulkEditDialogOpen}
        onOpenChange={setBulkEditDialogOpen}
        apiBaseUrl={apiBaseUrl}
        companyName={companyName}
        selectedDocumentIds={Array.from(selectedDocs)}
        onSuccess={() => {
          // Refresh documents after bulk update
          fetchDocuments();
          // Clear selection
          setSelectedDocs(new Set());
        }}
      />
    </div>
  );
};

export default DocumentBrowser;
