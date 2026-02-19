import React, { useState, useCallback, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Upload,
  FileText,
  Database,
  Plus,
  X,
  Eye,
  Search,
  Loader2,
  AlertCircle,
  CheckCircle,
  Download,
  Tag,
  Edit,
  List,
  BarChart3
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import DocumentBrowser from '@/components/knowledge-base/DocumentBrowser';
import DocumentViewer from '@/components/knowledge-base/DocumentViewer';
import DocumentEditor from '@/components/knowledge-base/DocumentEditor';
import RAGAnalyticsDashboard from '@/components/knowledge-base/RAGAnalyticsDashboard';
import { KnowledgeDocument } from '@/components/knowledge-base/types';

interface KnowledgeBaseDocument {
  id?: string;
  title: string;
  content: string;
  category: string;
  source?: string;
  tags: string[];
  metadata?: Record<string, any>;
}

interface KnowledgeBaseStepProps {
  config: {
    companyInfo: {
      name: string;
      description: string;
      url: string;
    };
    knowledgeBase?: KnowledgeBaseDocument[];
  };
  setConfig: (updater: (prev: any) => any) => void;
  apiBaseUrl: string;
}

const KnowledgeBaseStep: React.FC<KnowledgeBaseStepProps> = ({
  config,
  setConfig,
  apiBaseUrl
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string>('');
  const [queryText, setQueryText] = useState('');
  const [queryResult, setQueryResult] = useState<any>(null);
  const [selectedDocument, setSelectedDocument] = useState<KnowledgeBaseDocument | null>(null);
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  // New state for document viewer and editor
  const [viewingDocument, setViewingDocument] = useState<KnowledgeDocument | null>(null);
  const [editingDocument, setEditingDocument] = useState<KnowledgeDocument | null>(null);
  const [refreshBrowser, setRefreshBrowser] = useState(0);

  // Manual document form state
  const [manualDoc, setManualDoc] = useState({
    title: '',
    content: '',
    category: 'general',
    tags: ''
  });

  const knowledgeBase = config.knowledgeBase || [];

  const handleFileUpload = useCallback(async (files: FileList) => {
    if (!files.length) return;

    setIsUploading(true);
    setUploadProgress('Preparing upload...');

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        setUploadProgress(`Uploading ${file.name}...`);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('company_name', config.companyInfo.name || 'Unknown Company');
        formData.append('category', 'document');
        formData.append('tags', 'uploaded');

        const response = await fetch(`${apiBaseUrl}/knowledge-base/upload`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Failed to upload ${file.name}`);
        }

        const result = await response.json();

        // Create document object from upload result
        const newDocument: KnowledgeBaseDocument = {
          id: result.document_id,
          title: result.filename,
          content: result.content_preview,
          category: 'document',
          source: `file_upload:${file.name}`,
          tags: ['uploaded'],
          metadata: {
            filename: file.name,
            word_count: result.word_count,
            upload_date: new Date().toISOString()
          }
        };

        // Add to knowledge base
        setConfig(prev => ({
          ...prev,
          knowledgeBase: [...(prev.knowledgeBase || []), newDocument]
        }));

        toast({
          title: "Document Uploaded",
          description: `${file.name} uploaded successfully (${result.word_count} words)`,
        });
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast({
        title: "Upload Failed",
        description: error instanceof Error ? error.message : "Failed to upload documents",
        variant: "destructive"
      });
    } finally {
      setIsUploading(false);
      setUploadProgress('');
    }
  }, [config.companyInfo.name, apiBaseUrl, setConfig, toast]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files);
    }
  }, [handleFileUpload]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleManualDocumentAdd = useCallback(async () => {
    if (!manualDoc.title || !manualDoc.content) {
      toast({
        title: "Missing Information",
        description: "Please provide both title and content for the document",
        variant: "destructive"
      });
      return;
    }

    try {
      const response = await fetch(`${apiBaseUrl}/knowledge-base/documents?company_name=${encodeURIComponent(config.companyInfo.name || 'Unknown Company')}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: manualDoc.title,
          content: manualDoc.content,
          category: manualDoc.category,
          tags: manualDoc.tags.split(',').map(tag => tag.trim()).filter(Boolean),
          source: 'manual_entry'
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to add document');
      }

      const result = await response.json();

      // Create document object
      const newDocument: KnowledgeBaseDocument = {
        id: result.document_id,
        title: manualDoc.title,
        content: manualDoc.content,
        category: manualDoc.category,
        source: 'manual_entry',
        tags: manualDoc.tags.split(',').map(tag => tag.trim()).filter(Boolean),
        metadata: {
          word_count: result.word_count,
          created_date: new Date().toISOString()
        }
      };

      // Add to knowledge base
      setConfig(prev => ({
        ...prev,
        knowledgeBase: [...(prev.knowledgeBase || []), newDocument]
      }));

      // Reset form
      setManualDoc({
        title: '',
        content: '',
        category: 'general',
        tags: ''
      });

      toast({
        title: "Document Added",
        description: `"${manualDoc.title}" added successfully`,
      });

    } catch (error) {
      console.error('Add document error:', error);
      toast({
        title: "Failed to Add Document",
        description: error instanceof Error ? error.message : "Could not add document",
        variant: "destructive"
      });
    }
  }, [manualDoc, config.companyInfo.name, apiBaseUrl, setConfig, toast]);

  const handleRemoveDocument = useCallback((documentId: string) => {
    setConfig(prev => ({
      ...prev,
      knowledgeBase: (prev.knowledgeBase || []).filter(doc => doc.id !== documentId)
    }));

    toast({
      title: "Document Removed",
      description: "Document removed from knowledge base",
    });
  }, [setConfig, toast]);

  const handleTestQuery = useCallback(async () => {
    if (!queryText.trim()) {
      toast({
        title: "Empty Query",
        description: "Please enter a question to test",
        variant: "destructive"
      });
      return;
    }

    setIsQuerying(true);
    setQueryResult(null);

    try {
      const response = await fetch(`${apiBaseUrl}/knowledge-base/${encodeURIComponent(config.companyInfo.name || 'Unknown Company')}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: queryText,
          company_name: config.companyInfo.name || 'Unknown Company'
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to query knowledge base');
      }

      const result = await response.json();
      setQueryResult(result);

      if (result.success) {
        toast({
          title: "Query Successful",
          description: `Response generated with ${result.confidence_score}% confidence`,
        });
      }

    } catch (error) {
      console.error('Query error:', error);
      toast({
        title: "Query Failed",
        description: error instanceof Error ? error.message : "Could not process query",
        variant: "destructive"
      });
    } finally {
      setIsQuerying(false);
    }
  }, [queryText, config.companyInfo.name, apiBaseUrl, toast]);

  const handleInitializeKnowledgeBase = useCallback(async () => {
    if (knowledgeBase.length === 0) {
      toast({
        title: "No Documents",
        description: "Please add documents before initializing the knowledge base",
        variant: "destructive"
      });
      return;
    }

    setIsInitializing(true);

    try {
      const response = await fetch(`${apiBaseUrl}/knowledge-base/${encodeURIComponent(config.companyInfo.name || 'Unknown Company')}/initialize`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          company_name: config.companyInfo.name || 'Unknown Company',
          documents: knowledgeBase
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to initialize knowledge base');
      }

      const result = await response.json();

      toast({
        title: "Knowledge Base Initialized",
        description: `Successfully processed ${knowledgeBase.length} documents`,
      });

    } catch (error) {
      console.error('Initialize error:', error);
      toast({
        title: "Initialization Failed",
        description: error instanceof Error ? error.message : "Could not initialize knowledge base",
        variant: "destructive"
      });
    } finally {
      setIsInitializing(false);
    }
  }, [knowledgeBase, config.companyInfo.name, apiBaseUrl, toast]);

  // New handlers for document operations
  const handleViewDocument = useCallback((doc: KnowledgeDocument) => {
    setViewingDocument(doc);
  }, []);

  const handleEditDocument = useCallback((doc: KnowledgeDocument) => {
    setEditingDocument(doc);
    setViewingDocument(null); // Close viewer if open
  }, []);

  const handleDeleteDocument = useCallback(async (docId: string) => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/knowledge-base/documents/${docId}?company_name=${encodeURIComponent(config.companyInfo.name || 'Unknown Company')}`,
        {
          method: 'DELETE',
        }
      );

      if (!response.ok) {
        throw new Error('Failed to delete document');
      }

      toast({
        title: "Document Deleted",
        description: "Document removed from knowledge base",
      });

      // Refresh browser
      setRefreshBrowser(prev => prev + 1);
    } catch (error) {
      console.error('Delete error:', error);
      toast({
        title: "Delete Failed",
        description: error instanceof Error ? error.message : "Could not delete document",
        variant: "destructive"
      });
    }
  }, [apiBaseUrl, config.companyInfo.name, toast]);

  const handleSaveDocument = useCallback((doc: KnowledgeDocument) => {
    setEditingDocument(null);
    setRefreshBrowser(prev => prev + 1);
    toast({
      title: "Document Saved",
      description: "Changes have been saved successfully",
    });
  }, [toast]);

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2">
        <Database className="h-5 w-5 text-blue-600" />
        <h3 className="text-lg font-medium">Knowledge Base Management</h3>
      </div>

      <p className="text-sm text-gray-600">
        Add documents and information that your AI assistant can use to answer customer questions accurately.
      </p>

      <Tabs defaultValue="browse" className="w-full">
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
          <TabsTrigger value="manage">
            <Database className="h-4 w-4 mr-2" />
            Manage ({knowledgeBase.length})
          </TabsTrigger>
          <TabsTrigger value="test">
            <Search className="h-4 w-4 mr-2" />
            Test Queries
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <BarChart3 className="h-4 w-4 mr-2" />
            Analytics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="browse" className="space-y-4">
          <DocumentBrowser
            companyName={config.companyInfo.name || 'Unknown Company'}
            apiBaseUrl={apiBaseUrl}
            onViewDocument={handleViewDocument}
            onEditDocument={handleEditDocument}
            onDeleteDocument={handleDeleteDocument}
            key={refreshBrowser} // Force refresh when documents change
          />
        </TabsContent>

        <TabsContent value="upload" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Document Upload</CardTitle>
              <CardDescription>
                Upload PDF, Word, or text documents to add to your knowledge base.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                } ${isUploading ? 'opacity-50' : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
              >
                {isUploading ? (
                  <div className="flex flex-col items-center space-y-2">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                    <p className="text-sm text-gray-600">{uploadProgress}</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center space-y-4">
                    <Upload className="h-12 w-12 text-gray-400" />
                    <div>
                      <p className="text-lg font-medium">Drop files here or click to browse</p>
                      <p className="text-sm text-gray-500">
                        Supports PDF, Word (.docx), and text files (max 10MB each)
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => fileInputRef.current?.click()}
                    >
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
                    onChange={(e) => setManualDoc(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="e.g., Company Policies, FAQ, Product Info"
                  />
                </div>
                <div>
                  <Label htmlFor="manual-category">Category</Label>
                  <Input
                    id="manual-category"
                    value={manualDoc.category}
                    onChange={(e) => setManualDoc(prev => ({ ...prev, category: e.target.value }))}
                    placeholder="e.g., policies, faq, products"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="manual-content">Content</Label>
                <Textarea
                  id="manual-content"
                  value={manualDoc.content}
                  onChange={(e) => setManualDoc(prev => ({ ...prev, content: e.target.value }))}
                  placeholder="Enter the document content here..."
                  rows={8}
                />
              </div>

              <div>
                <Label htmlFor="manual-tags">Tags (comma-separated)</Label>
                <Input
                  id="manual-tags"
                  value={manualDoc.tags}
                  onChange={(e) => setManualDoc(prev => ({ ...prev, tags: e.target.value }))}
                  placeholder="e.g., important, customer-facing, policies"
                />
              </div>

              <Button
                onClick={handleManualDocumentAdd}
                disabled={!manualDoc.title || !manualDoc.content}
                className="w-full"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Document
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="manage" className="space-y-4">
          <div className="flex justify-between items-center">
            <h4 className="font-medium">Documents in Knowledge Base</h4>
            {knowledgeBase.length > 0 && (
              <Button
                onClick={handleInitializeKnowledgeBase}
                disabled={isInitializing}
                variant="outline"
              >
                {isInitializing ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <CheckCircle className="h-4 w-4 mr-2" />
                )}
                Initialize Knowledge Base
              </Button>
            )}
          </div>

          {knowledgeBase.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No documents added yet</p>
                <p className="text-sm text-gray-400">Upload files or add manual entries to get started</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {knowledgeBase.map((doc, index) => (
                <Card key={doc.id || index}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h5 className="font-medium">{doc.title}</h5>
                        <p className="text-sm text-gray-600 mt-1">
                          {doc.content.length > 100
                            ? `${doc.content.substring(0, 100)}...`
                            : doc.content
                          }
                        </p>
                        <div className="flex items-center space-x-4 mt-2">
                          <Badge variant="outline">{doc.category}</Badge>
                          {doc.tags.map((tag, tagIndex) => (
                            <Badge key={tagIndex} variant="secondary" className="text-xs">
                              <Tag className="h-3 w-3 mr-1" />
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedDocument(doc);
                            setShowDocumentModal(true);
                          }}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => doc.id && handleRemoveDocument(doc.id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="test" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Test Knowledge Base Queries</CardTitle>
              <CardDescription>
                Test how your AI assistant will respond to customer questions using the knowledge base.
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
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center space-x-2 mb-3">
                      {queryResult.success ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : (
                        <AlertCircle className="h-5 w-5 text-red-600" />
                      )}
                      <span className="font-medium">
                        {queryResult.success ? 'Response Generated' : 'Query Failed'}
                      </span>
                      {queryResult.confidence_score && (
                        <Badge variant="outline">
                          {queryResult.confidence_score}% confidence
                        </Badge>
                      )}
                    </div>
                    <div className="bg-gray-50 p-3 rounded">
                      <p className="text-sm">{queryResult.response}</p>
                    </div>
                    {queryResult.requires_escalation && (
                      <div className="mt-2 text-sm text-amber-600">
                        ⚠️ This query would be escalated to human support
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <RAGAnalyticsDashboard
            companyName={config.companyInfo.name || 'Unknown Company'}
            apiBaseUrl={apiBaseUrl}
          />
        </TabsContent>
      </Tabs>

      {/* Document Viewer Modal */}
      {viewingDocument && (
        <DocumentViewer
          document={viewingDocument}
          apiBaseUrl={apiBaseUrl}
          onEdit={handleEditDocument}
          onDelete={handleDeleteDocument}
          onClose={() => setViewingDocument(null)}
        />
      )}

      {/* Document Editor Modal */}
      {editingDocument && (
        <DocumentEditor
          document={editingDocument}
          apiBaseUrl={apiBaseUrl}
          onSave={handleSaveDocument}
          onCancel={() => setEditingDocument(null)}
        />
      )}
    </div>
  );
};

export default KnowledgeBaseStep;