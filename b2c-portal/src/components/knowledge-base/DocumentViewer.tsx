import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  FileText,
  Edit,
  Trash2,
  Download,
  Tag,
  Calendar,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  Archive,
  Eye,
  History,
  BarChart3,
  X,
  ExternalLink,
  Loader2,
} from 'lucide-react';
import { KnowledgeDocument, DocumentVersion } from './types';
import { useToast } from '@/hooks/use-toast';

interface DocumentViewerProps {
  document: KnowledgeDocument;
  apiBaseUrl: string;
  onEdit?: (doc: KnowledgeDocument) => void;
  onDelete?: (docId: string) => void;
  onClose?: () => void;
}

const DocumentViewer: React.FC<DocumentViewerProps> = ({
  document,
  apiBaseUrl,
  onEdit,
  onDelete,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState('content');
  const { toast } = useToast();

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

  // Handle download
  const handleDownload = () => {
    const blob = new Blob([document.content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = window.document.createElement('a');
    a.href = url;
    a.download = `${document.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.txt`;
    window.document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    window.document.body.removeChild(a);

    toast({
      title: 'Download Started',
      description: `Downloading "${document.title}"`,
    });
  };

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Format relative time
  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    return `${Math.floor(diffDays / 365)} years ago`;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <FileText className="h-6 w-6 text-blue-600" />
              <h2 className="text-2xl font-semibold">{document.title}</h2>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status={document.status} />
              <Badge variant="outline">{document.category}</Badge>
              {document.tags.map((tag, idx) => (
                <Badge key={idx} variant="secondary" className="text-xs">
                  <Tag className="h-3 w-3 mr-1" />
                  {tag}
                </Badge>
              ))}
            </div>
          </div>

          <div className="flex gap-2 ml-4">
            {onEdit && (
              <Button size="sm" variant="outline" onClick={() => onEdit(document)}>
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </Button>
            )}
            <Button size="sm" variant="outline" onClick={handleDownload}>
              <Download className="h-4 w-4 mr-2" />
              Download
            </Button>
            {onDelete && (
              <Button
                size="sm"
                variant="destructive"
                onClick={() => {
                  if (confirm('Are you sure you want to delete this document?')) {
                    onDelete(document.id);
                    onClose?.();
                  }
                }}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </Button>
            )}
            {onClose && (
              <Button size="sm" variant="ghost" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="content">
                <Eye className="h-4 w-4 mr-2" />
                Content
              </TabsTrigger>
              <TabsTrigger value="metadata">
                <FileText className="h-4 w-4 mr-2" />
                Metadata
              </TabsTrigger>
              <TabsTrigger value="history">
                <History className="h-4 w-4 mr-2" />
                History ({document.versions.length})
              </TabsTrigger>
              <TabsTrigger value="analytics">
                <BarChart3 className="h-4 w-4 mr-2" />
                Analytics
              </TabsTrigger>
            </TabsList>

            {/* Content Tab */}
            <TabsContent value="content" className="mt-4">
              <Card>
                <CardContent className="p-6">
                  <div className="prose max-w-none">
                    <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                      {document.content}
                    </pre>
                  </div>
                </CardContent>
              </Card>

              {document.source_uri && (
                <Card className="mt-4">
                  <CardHeader>
                    <CardTitle className="text-sm">Source</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <a
                      href={document.source_uri}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline flex items-center gap-2"
                    >
                      {document.source_uri}
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Metadata Tab */}
            <TabsContent value="metadata" className="mt-4">
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Document Information</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <p className="text-xs text-gray-500">Document ID</p>
                      <p className="text-sm font-mono">{document.id}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Company</p>
                      <p className="text-sm">{document.company_name}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Collection</p>
                      <p className="text-sm font-mono">{document.collection_name}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Source</p>
                      <p className="text-sm">{document.source.replace(/_/g, ' ')}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Version</p>
                      <p className="text-sm">v{document.current_version}</p>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Statistics</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <p className="text-xs text-gray-500">Word Count</p>
                      <p className="text-sm">{document.metadata.word_count?.toLocaleString() || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Character Count</p>
                      <p className="text-sm">{document.metadata.character_count?.toLocaleString() || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Chunks</p>
                      <p className="text-sm">{document.metadata.chunk_count || 'Not yet chunked'}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Query Count</p>
                      <p className="text-sm">{document.metadata.query_count || 0}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Reference Count</p>
                      <p className="text-sm">{document.metadata.reference_count || 0}</p>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Timestamps</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <p className="text-xs text-gray-500">Created</p>
                      <p className="text-sm">{formatDate(document.created_at)}</p>
                      <p className="text-xs text-gray-400">{formatRelativeTime(document.created_at)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Last Updated</p>
                      <p className="text-sm">{formatDate(document.updated_at)}</p>
                      <p className="text-xs text-gray-400">{formatRelativeTime(document.updated_at)}</p>
                    </div>
                    {document.indexed_at && (
                      <div>
                        <p className="text-xs text-gray-500">Indexed</p>
                        <p className="text-sm">{formatDate(document.indexed_at)}</p>
                        <p className="text-xs text-gray-400">{formatRelativeTime(document.indexed_at)}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Vector Store</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <p className="text-xs text-gray-500">Embedding Dimension</p>
                      <p className="text-sm">{document.embedding_dimension}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Vector IDs</p>
                      <p className="text-sm">{document.vector_ids.length} vectors</p>
                    </div>
                    {document.metadata.embedding_model && (
                      <div>
                        <p className="text-xs text-gray-500">Embedding Model</p>
                        <p className="text-sm">{document.metadata.embedding_model}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* History Tab */}
            <TabsContent value="history" className="mt-4">
              {document.versions.length === 0 ? (
                <Card>
                  <CardContent className="p-12 text-center">
                    <History className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">No version history available</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-4">
                  {document.versions
                    .sort((a, b) => b.version_number - a.version_number)
                    .map((version: DocumentVersion) => (
                      <Card key={version.version_id}>
                        <CardHeader>
                          <div className="flex items-center justify-between">
                            <CardTitle className="text-sm">
                              Version {version.version_number}
                            </CardTitle>
                            <span className="text-xs text-gray-500">
                              {formatDate(version.created_at)}
                            </span>
                          </div>
                          {version.change_reason && (
                            <CardDescription>{version.change_reason}</CardDescription>
                          )}
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div>
                              <p className="text-xs text-gray-500">Title</p>
                              <p className="text-sm">{version.title}</p>
                            </div>
                            {version.changed_by && (
                              <div>
                                <p className="text-xs text-gray-500">Changed By</p>
                                <p className="text-sm">{version.changed_by}</p>
                              </div>
                            )}
                            <div>
                              <p className="text-xs text-gray-500">Content Preview</p>
                              <p className="text-sm text-gray-600">
                                {version.content.substring(0, 150)}
                                {version.content.length > 150 ? '...' : ''}
                              </p>
                            </div>
                            <div className="flex flex-wrap gap-1 mt-2">
                              <Badge variant="outline">{version.category}</Badge>
                              {version.tags.map((tag, idx) => (
                                <Badge key={idx} variant="secondary" className="text-xs">
                                  {tag}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                </div>
              )}
            </TabsContent>

            {/* Analytics Tab */}
            <TabsContent value="analytics" className="mt-4">
              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Usage</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">
                      {document.metadata.query_count || 0}
                    </div>
                    <p className="text-xs text-gray-500 mt-1">Total Queries</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">References</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">
                      {document.metadata.reference_count || 0}
                    </div>
                    <p className="text-xs text-gray-500 mt-1">Times Referenced</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Confidence</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">
                      {document.metadata.confidence_avg
                        ? `${(document.metadata.confidence_avg * 100).toFixed(1)}%`
                        : 'N/A'}
                    </div>
                    <p className="text-xs text-gray-500 mt-1">Average Confidence</p>
                  </CardContent>
                </Card>

                {document.metadata.last_queried_at && (
                  <Card className="col-span-3">
                    <CardHeader>
                      <CardTitle className="text-sm">Last Activity</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm">
                        Last queried {formatRelativeTime(document.metadata.last_queried_at)}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {formatDate(document.metadata.last_queried_at)}
                      </p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default DocumentViewer;
