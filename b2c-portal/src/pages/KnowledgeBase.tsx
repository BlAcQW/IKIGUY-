/**
 * Standalone Knowledge Base Management Page
 * Provides full document management, analytics, and RAG testing capabilities
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Upload,
  FileText,
  Database,
  Plus,
  Search,
  Loader2,
  AlertCircle,
  CheckCircle,
  Tag,
  List,
  BarChart3,
  BookOpen,
  Sparkles,
  Settings,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import { useOrganization } from '@/contexts/OrganizationContext';
import DocumentBrowser from '@/components/knowledge-base/DocumentBrowser';
import DocumentViewer from '@/components/knowledge-base/DocumentViewer';
import DocumentEditor from '@/components/knowledge-base/DocumentEditor';
import RAGAnalyticsDashboard from '@/components/knowledge-base/RAGAnalyticsDashboard';
import CollectionSidebar from '@/components/knowledge-base/CollectionSidebar';
import CollectionManager from '@/components/knowledge-base/CollectionManager';
import { KnowledgeDocument } from '@/components/knowledge-base/types';

// Get API base URL from environment or default
const API_BASE_URL = import.meta.env.VITE_CORE_API_URL || 'https://flow-api.ailabsafrica.com';

interface KnowledgeBaseDocument {
  id?: string;
  title: string;
  content: string;
  category: string;
  source?: string;
  tags: string[];
  metadata?: Record<string, any>;
}

const KnowledgeBasePage: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string>('');
  const [queryText, setQueryText] = useState('');
  const [queryResult, setQueryResult] = useState<any>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const { getAccessToken } = useMongoAuth();
  const { currentOrganization } = useOrganization();

  // Document viewer/editor state
  const [viewingDocument, setViewingDocument] = useState<KnowledgeDocument | null>(null);
  const [editingDocument, setEditingDocument] = useState<KnowledgeDocument | null>(null);
  const [refreshBrowser, setRefreshBrowser] = useState(0);

  // Manual document form state
  const [manualDoc, setManualDoc] = useState({
    title: '',
    content: '',
    category: 'general',
    tags: '',
  });

  // Collection selector state
  const [collections, setCollections] = useState<Array<{ name: string; display_name: string; document_count: number }>>([]);
  const [selectedCollection, setSelectedCollection] = useState<string>('');
  const [loadingCollections, setLoadingCollections] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('browse');
  const [showCreateCollectionDialog, setShowCreateCollectionDialog] = useState(false);

  // Company name extracted from selected collection
  const companyName = selectedCollection.replace('helpdesk_', '');

  // Fetch available collections on mount and when organization changes
  useEffect(() => {
    const fetchCollections = async () => {
      try {
        const token = getAccessToken();
        if (!token) {
          throw new Error('No authentication token available');
        }

        const headers: Record<string, string> = {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        };

        // Add organization context if available
        if (currentOrganization?.id) {
          headers['X-Organization-ID'] = currentOrganization.id;
        }

        const response = await fetch(`${API_BASE_URL}/knowledge-base/collections`, {
          headers,
        });

        if (!response.ok) throw new Error('Failed to fetch collections');

        const data = await response.json();
        setCollections(data.collections || []);

        // Set default selected collection (first one with documents, or first one overall)
        if (data.collections && data.collections.length > 0) {
          const collectionWithDocs = data.collections.find((c: any) => c.document_count > 0);
          setSelectedCollection(collectionWithDocs?.name || data.collections[0].name);
        }
      } catch (error) {
        console.error('Error fetching collections:', error);
        toast({
          title: 'Failed to Load Collections',
          description: error instanceof Error ? error.message : 'Could not fetch knowledge base collections',
          variant: 'destructive',
        });
      } finally {
        setLoadingCollections(false);
      }
    };

    fetchCollections();
  }, [toast, getAccessToken, currentOrganization]);

  // File upload handler
  const handleFileUpload = useCallback(
    async (files: FileList) => {
      if (!files.length) return;

      setIsUploading(true);
      setUploadProgress('Preparing upload...');

      try {
        for (let i = 0; i < files.length; i++) {
          const file = files[i];
          setUploadProgress(`Uploading ${file.name}...`);

          const formData = new FormData();
          formData.append('file', file);
          formData.append('company_name', companyName);
          formData.append('category', 'document');
          formData.append('tags', 'uploaded');

          // Build headers with authentication
          const headers: Record<string, string> = {};

          const token = getAccessToken();
          if (token) {
            headers['Authorization'] = `Bearer ${token}`;
          }

          if (currentOrganization?.id) {
            headers['X-Organization-ID'] = currentOrganization.id;
          }

          const response = await fetch(`${API_BASE_URL}/knowledge-base/upload`, {
            method: 'POST',
            headers,
            body: formData,
          });

          if (!response.ok) {
            throw new Error(`Failed to upload ${file.name}`);
          }

          const result = await response.json();

          toast({
            title: 'Document Uploaded',
            description: `${file.name} uploaded successfully (${result.word_count} words)`,
          });
        }

        // Refresh browser to show new documents
        setRefreshBrowser((prev) => prev + 1);
      } catch (error) {
        console.error('Upload error:', error);
        toast({
          title: 'Upload Failed',
          description: error instanceof Error ? error.message : 'Failed to upload documents',
          variant: 'destructive',
        });
      } finally {
        setIsUploading(false);
        setUploadProgress('');
      }
    },
    [companyName, toast]
  );

  // Drag and drop handlers
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFileUpload(files);
      }
    },
    [handleFileUpload]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  // Manual document add handler
  const handleManualDocumentAdd = useCallback(async () => {
    if (!manualDoc.title || !manualDoc.content) {
      toast({
        title: 'Missing Information',
        description: 'Please provide both title and content for the document',
        variant: 'destructive',
      });
      return;
    }

    try {
      // Build headers with authentication
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      const token = getAccessToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      if (currentOrganization?.id) {
        headers['X-Organization-ID'] = currentOrganization.id;
      }

      const response = await fetch(
        `${API_BASE_URL}/knowledge-base/documents?company_name=${encodeURIComponent(companyName)}`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({
            title: manualDoc.title,
            content: manualDoc.content,
            category: manualDoc.category,
            tags: manualDoc.tags
              .split(',')
              .map((tag) => tag.trim())
              .filter(Boolean),
            source: 'manual_entry',
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to add document');
      }

      const result = await response.json();

      // Reset form
      setManualDoc({
        title: '',
        content: '',
        category: 'general',
        tags: '',
      });

      toast({
        title: 'Document Added',
        description: `"${manualDoc.title}" added successfully`,
      });

      // Refresh browser
      setRefreshBrowser((prev) => prev + 1);
    } catch (error) {
      console.error('Add document error:', error);
      toast({
        title: 'Failed to Add Document',
        description: error instanceof Error ? error.message : 'Could not add document',
        variant: 'destructive',
      });
    }
  }, [manualDoc, companyName, toast]);

  // Test query handler
  const handleTestQuery = useCallback(async () => {
    if (!queryText.trim()) {
      toast({
        title: 'Empty Query',
        description: 'Please enter a question to test',
        variant: 'destructive',
      });
      return;
    }

    setIsQuerying(true);
    setQueryResult(null);

    try {
      // Build headers with authentication
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      const token = getAccessToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      if (currentOrganization?.id) {
        headers['X-Organization-ID'] = currentOrganization.id;
      }

      const response = await fetch(
        `${API_BASE_URL}/knowledge-base/${encodeURIComponent(companyName)}/query`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({
            query: queryText,
            company_name: companyName,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to query knowledge base');
      }

      const result = await response.json();
      setQueryResult(result);

      if (result.success) {
        toast({
          title: 'Query Successful',
          description: `Response generated with ${(result.confidence_score * 100).toFixed(1)}% confidence`,
        });
      }
    } catch (error) {
      console.error('Query error:', error);
      toast({
        title: 'Query Failed',
        description: error instanceof Error ? error.message : 'Could not process query',
        variant: 'destructive',
      });
    } finally {
      setIsQuerying(false);
    }
  }, [queryText, companyName, toast]);

  // Document operation handlers
  const handleViewDocument = useCallback((doc: KnowledgeDocument) => {
    setViewingDocument(doc);
  }, []);

  const handleEditDocument = useCallback((doc: KnowledgeDocument) => {
    setEditingDocument(doc);
    setViewingDocument(null);
  }, []);

  const handleDeleteDocument = useCallback(
    async (docId: string) => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/knowledge-base/documents/${docId}?company_name=${encodeURIComponent(companyName)}`,
          {
            method: 'DELETE',
          }
        );

        if (!response.ok) {
          throw new Error('Failed to delete document');
        }

        toast({
          title: 'Document Deleted',
          description: 'Document removed from knowledge base',
        });

        setRefreshBrowser((prev) => prev + 1);
      } catch (error) {
        console.error('Delete error:', error);
        toast({
          title: 'Delete Failed',
          description: error instanceof Error ? error.message : 'Could not delete document',
          variant: 'destructive',
        });
      }
    },
    [companyName, toast]
  );

  const handleSaveDocument = useCallback(
    (doc: KnowledgeDocument) => {
      setEditingDocument(null);
      setRefreshBrowser((prev) => prev + 1);
      toast({
        title: 'Document Saved',
        description: 'Changes have been saved successfully',
      });
    },
    [toast]
  );

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      <DashboardSidebar />

      {/* Collection Sidebar */}
      <CollectionSidebar
        apiBaseUrl={API_BASE_URL}
        selectedCollection={selectedCollection}
        onSelectCollection={(companyName) => {
          setSelectedCollection(`helpdesk_${companyName}`);
          setActiveTab('browse');
        }}
        onManageCollections={() => setActiveTab('collections')}
        onCreateCollection={() => {
          setActiveTab('collections');
          // Trigger create dialog via a small delay
          setTimeout(() => setShowCreateCollectionDialog(true), 100);
        }}
      />

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-3 text-gray-900 dark:text-gray-100">
                <BookOpen className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
                Knowledge Base
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Manage documents and configure your AI-powered knowledge base for intelligent responses
              </p>
            </div>
          </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="browse">
            <List className="h-4 w-4 mr-2" />
            Browse
          </TabsTrigger>
          <TabsTrigger value="upload">
            <Upload className="h-4 w-4 mr-2" />
            Upload
          </TabsTrigger>
          <TabsTrigger value="manual">
            <Plus className="h-4 w-4 mr-2" />
            Manual Entry
          </TabsTrigger>
          <TabsTrigger value="test">
            <Sparkles className="h-4 w-4 mr-2" />
            Test RAG
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <BarChart3 className="h-4 w-4 mr-2" />
            Analytics
          </TabsTrigger>
          <TabsTrigger value="collections">
            <Settings className="h-4 w-4 mr-2" />
            Collections
          </TabsTrigger>
        </TabsList>

        {/* Browse Tab */}
        <TabsContent value="browse" className="space-y-4">
          <DocumentBrowser
            companyName={companyName}
            apiBaseUrl={API_BASE_URL}
            authToken={getAccessToken() || undefined}
            organizationId={currentOrganization?.id}
            onViewDocument={handleViewDocument}
            onEditDocument={handleEditDocument}
            onDeleteDocument={handleDeleteDocument}
            key={refreshBrowser}
          />
        </TabsContent>

        {/* Upload Tab */}
        <TabsContent value="upload" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Document Upload</CardTitle>
              <CardDescription>
                Upload PDF, Word, or text documents to add to your knowledge base.
                Maximum file size: 10MB per file.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                  dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                } ${isUploading ? 'opacity-50' : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
              >
                {isUploading ? (
                  <div className="flex flex-col items-center space-y-3">
                    <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
                    <p className="text-sm text-gray-600">{uploadProgress}</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center space-y-4">
                    <Upload className="h-16 w-16 text-gray-400" />
                    <div>
                      <p className="text-xl font-medium">Drop files here or click to browse</p>
                      <p className="text-sm text-gray-500 mt-2">
                        Supports PDF, Word (.docx), TXT, and Markdown files (max 10MB each)
                      </p>
                    </div>
                    <Button variant="outline" onClick={() => fileInputRef.current?.click()}>
                      <Upload className="h-4 w-4 mr-2" />
                      Choose Files
                    </Button>
                  </div>
                )}
              </div>

              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.docx,.doc,.txt,.md"
                className="hidden"
                onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Manual Entry Tab */}
        <TabsContent value="manual" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Manual Document Entry</CardTitle>
              <CardDescription>
                Add knowledge directly by typing or pasting content.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="manual-title">Document Title</Label>
                  <Input
                    id="manual-title"
                    value={manualDoc.title}
                    onChange={(e) => setManualDoc((prev) => ({ ...prev, title: e.target.value }))}
                    placeholder="e.g., Company Policies, FAQ, Product Info"
                  />
                </div>
                <div>
                  <Label htmlFor="manual-category">Category</Label>
                  <Input
                    id="manual-category"
                    value={manualDoc.category}
                    onChange={(e) =>
                      setManualDoc((prev) => ({ ...prev, category: e.target.value }))
                    }
                    placeholder="e.g., policies, faq, products"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="manual-content">Content</Label>
                <Textarea
                  id="manual-content"
                  value={manualDoc.content}
                  onChange={(e) => setManualDoc((prev) => ({ ...prev, content: e.target.value }))}
                  placeholder="Enter the document content here..."
                  rows={12}
                />
              </div>

              <div>
                <Label htmlFor="manual-tags">Tags (comma-separated)</Label>
                <Input
                  id="manual-tags"
                  value={manualDoc.tags}
                  onChange={(e) => setManualDoc((prev) => ({ ...prev, tags: e.target.value }))}
                  placeholder="e.g., important, customer-facing, policies"
                />
              </div>

              <Button
                onClick={handleManualDocumentAdd}
                disabled={!manualDoc.title || !manualDoc.content}
                className="w-full"
                size="lg"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Document
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Test RAG Tab */}
        <TabsContent value="test" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-blue-600" />
                Test Knowledge Base Queries
              </CardTitle>
              <CardDescription>
                Test how your AI assistant will respond to customer questions using the RAG system.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="test-query">Test Question</Label>
                <div className="flex space-x-2">
                  <Input
                    id="test-query"
                    value={queryText}
                    onChange={(e) => setQueryText(e.target.value)}
                    placeholder="Ask a question that customers might ask..."
                    onKeyPress={(e) => e.key === 'Enter' && handleTestQuery()}
                  />
                  <Button onClick={handleTestQuery} disabled={isQuerying}>
                    {isQuerying ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Search className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>

              {queryResult && (
                <Card className="border-2">
                  <CardContent className="p-6">
                    <div className="flex items-center space-x-2 mb-4">
                      {queryResult.success ? (
                        <CheckCircle className="h-6 w-6 text-green-600" />
                      ) : (
                        <AlertCircle className="h-6 w-6 text-red-600" />
                      )}
                      <span className="font-semibold text-lg">
                        {queryResult.success ? 'Response Generated' : 'Query Failed'}
                      </span>
                      {queryResult.confidence_score && (
                        <Badge variant="outline" className="ml-auto">
                          {(queryResult.confidence_score * 100).toFixed(1)}% confidence
                        </Badge>
                      )}
                    </div>

                    <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg mb-4">
                      <p className="text-sm leading-relaxed text-gray-900 dark:text-gray-100">{queryResult.response}</p>
                    </div>

                    {queryResult.sources_used && queryResult.sources_used.length > 0 && (
                      <div className="border-t pt-4">
                        <p className="text-sm font-medium mb-2">Sources Used:</p>
                        <div className="flex flex-wrap gap-2">
                          {queryResult.sources_used.map((source: string, idx: number) => (
                            <Badge key={idx} variant="secondary">
                              <FileText className="h-3 w-3 mr-1" />
                              {source}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {queryResult.requires_escalation && (
                      <div className="mt-4 p-3 bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-800 rounded-lg">
                        <p className="text-sm text-amber-900 dark:text-amber-200">
                          ⚠️ This query would be escalated to human support
                          {queryResult.escalation_reason && `: ${queryResult.escalation_reason}`}
                        </p>
                      </div>
                    )}

                    {queryResult.processing_time && (
                      <div className="mt-4 text-xs text-gray-500 dark:text-gray-400">
                        Processing time: {queryResult.processing_time.toFixed(2)}s
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-4">
          <RAGAnalyticsDashboard
            companyName={companyName}
            apiBaseUrl={API_BASE_URL}
            authToken={getAccessToken() || undefined}
            organizationId={currentOrganization?.id}
          />
        </TabsContent>

        {/* Collections Tab */}
        <TabsContent value="collections" className="space-y-4">
          <CollectionManager
            apiBaseUrl={API_BASE_URL}
            onCollectionChange={() => {
              // Refresh collections list when changes occur
              setLoadingCollections(true);
              fetch(`${API_BASE_URL}/knowledge-base/collections`)
                .then(res => res.json())
                .then(data => {
                  if (data.success) {
                    setCollections(data.collections || []);
                  }
                })
                .finally(() => setLoadingCollections(false));
            }}
          />
        </TabsContent>
      </Tabs>

      {/* Document Viewer Modal */}
      {viewingDocument && (
        <DocumentViewer
          document={viewingDocument}
          apiBaseUrl={API_BASE_URL}
          onEdit={handleEditDocument}
          onDelete={handleDeleteDocument}
          onClose={() => setViewingDocument(null)}
        />
      )}

      {/* Document Editor Modal */}
      {editingDocument && (
        <DocumentEditor
          document={editingDocument}
          apiBaseUrl={API_BASE_URL}
          onSave={handleSaveDocument}
          onCancel={() => setEditingDocument(null)}
        />
      )}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeBasePage;
