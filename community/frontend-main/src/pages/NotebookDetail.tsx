import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Download, ThumbsUp, ThumbsDown, BookMarked, Eye,
  Calendar, User, Tag, Star, FileCode, MessageSquare, Share2,
  Loader2, AlertCircle, Code2, Play, Flag
} from 'lucide-react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { useBackendAuth } from '@/contexts/BackendAuthContext';
import { ReportModal } from '@/components/ReportModal';

interface NotebookUsageStats {
  downloads: number;
  views: number;
  forks: number;
  successful_runs: number;
  failed_runs: number;
  avg_execution_time?: number;
}

interface NotebookResponse {
  id: string;
  title: string;
  description: string;
  category: string;
  difficulty: string;
  language_codes: string[];
  tags: string[];
  is_public: boolean;
  license: string;
  author_name: string;
  current_version: string;
  file_size: number;
  upvotes: number;
  downvotes: number;
  rating: number;
  comment_count: number;
  usage_stats: NotebookUsageStats;
  created_at: string;
  updated_at: string;
  published_at?: string;
  user_vote?: 'upvote' | 'downvote';
  is_bookmarked: boolean;
  is_owner: boolean;
}

const API_BASE = 'https://language-community-api.ailabsafrica.com/api/v1';

const NotebookDetail: React.FC = () => {
  const { notebookId } = useParams<{ notebookId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useBackendAuth();

  const [notebook, setNotebook] = useState<NotebookResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [voting, setVoting] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [bookmarking, setBookmarking] = useState(false);
  const [comments, setComments] = useState<any[]>([]);
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [reportEntity, setReportEntity] = useState<{ type: string; id: string; title?: string } | null>(null);

  useEffect(() => {
    loadNotebook();
  }, [notebookId, user]);

  const loadNotebook = async () => {
    try {
      setLoading(true);
      setError(null);

      const headers: Record<string, string> = {};
      if (user) {
        headers['Authorization'] = `Bearer ${user.token}`;
      }

      const response = await fetch(`${API_BASE}/notebooks/${notebookId}`, { headers });

      if (!response.ok) {
        if (response.status === 404) {
          setError('Notebook not found');
        } else {
          setError('Failed to load notebook');
        }
        return;
      }

      const data = await response.json();
      setNotebook(data.data || data);
    } catch (error) {
      console.error('Error loading notebook:', error);
      setError('Failed to load notebook');
    } finally {
      setLoading(false);
    }
  };

  const loadComments = async () => {
    if (!notebookId) return;

    try {
      setCommentsLoading(true);
      const headers: Record<string, string> = {};
      if (user) {
        headers['Authorization'] = `Bearer ${user.token}`;
      }

      const response = await fetch(`${API_BASE}/notebooks/${notebookId}/comments`, { headers });

      if (response.ok) {
        const data = await response.json();
        setComments(data.data || data || []);
      }
    } catch (error) {
      console.error('Error loading comments:', error);
    } finally {
      setCommentsLoading(false);
    }
  };

  const handleSubmitComment = async () => {
    if (!user) {
      toast({
        title: 'Authentication Required',
        description: 'Please sign in to comment',
        variant: 'destructive'
      });
      return;
    }

    if (!newComment.trim()) {
      toast({
        title: 'Empty Comment',
        description: 'Please enter a comment',
        variant: 'destructive'
      });
      return;
    }

    try {
      setSubmittingComment(true);

      const response = await fetch(`${API_BASE}/notebooks/${notebookId}/comments`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: newComment })
      });

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Comment posted successfully'
        });
        setNewComment('');
        loadComments(); // Reload comments
      } else {
        throw new Error('Failed to post comment');
      }
    } catch (error) {
      console.error('Error posting comment:', error);
      toast({
        title: 'Error',
        description: 'Failed to post comment',
        variant: 'destructive'
      });
    } finally {
      setSubmittingComment(false);
    }
  };

  useEffect(() => {
    if (notebookId) {
      loadComments();
    }
  }, [notebookId]);

  const handleVote = async (voteType: 'upvote' | 'downvote') => {
    if (!user) {
      toast({
        title: 'Authentication Required',
        description: 'Please sign in to vote on notebooks',
        variant: 'destructive'
      });
      return;
    }

    try {
      setVoting(true);

      const response = await fetch(`${API_BASE}/notebooks/${notebookId}/vote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify({ vote_type: voteType })
      });

      if (!response.ok) {
        throw new Error('Failed to record vote');
      }

      // Reload notebook to get updated vote counts
      await loadNotebook();

      toast({
        title: 'Success',
        description: `Notebook ${voteType}d successfully`
      });
    } catch (error) {
      console.error('Vote error:', error);
      toast({
        title: 'Error',
        description: 'Failed to record vote',
        variant: 'destructive'
      });
    } finally {
      setVoting(false);
    }
  };

  const handleDownload = async () => {
    try {
      setDownloading(true);

      const headers: Record<string, string> = {};
      if (user) {
        headers['Authorization'] = `Bearer ${user.token}`;
      }

      const response = await fetch(`${API_BASE}/notebooks/${notebookId}/download`, { headers });

      if (!response.ok) {
        throw new Error('Failed to download notebook');
      }

      const data = await response.json();

      // Create blob and download
      const blob = new Blob([atob(data.content)], { type: data.content_type });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = data.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: 'Success',
        description: 'Notebook downloaded successfully'
      });
    } catch (error) {
      console.error('Download error:', error);
      toast({
        title: 'Error',
        description: 'Failed to download notebook',
        variant: 'destructive'
      });
    } finally {
      setDownloading(false);
    }
  };

  const handleBookmark = async () => {
    if (!user) {
      toast({
        title: 'Authentication Required',
        description: 'Please sign in to bookmark notebooks',
        variant: 'destructive'
      });
      return;
    }

    try {
      setBookmarking(true);

      const response = await fetch(`${API_BASE}/notebooks/${notebookId}/bookmark`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to toggle bookmark');
      }

      // Reload notebook to get updated bookmark status
      await loadNotebook();

      toast({
        title: 'Success',
        description: notebook?.is_bookmarked ? 'Bookmark removed' : 'Notebook bookmarked'
      });
    } catch (error) {
      console.error('Bookmark error:', error);
      toast({
        title: 'Error',
        description: 'Failed to bookmark notebook',
        variant: 'destructive'
      });
    } finally {
      setBookmarking(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getDifficultyColor = (difficulty: string): string => {
    const colors: Record<string, string> = {
      beginner: 'bg-green-100 text-green-800',
      intermediate: 'bg-blue-100 text-blue-800',
      advanced: 'bg-orange-100 text-orange-800',
      expert: 'bg-red-100 text-red-800'
    };
    return colors[difficulty] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <Navbar />
        <main className="flex-1 container mx-auto px-4 py-8">
          <div className="space-y-6">
            <Skeleton className="h-12 w-3/4" />
            <Skeleton className="h-32 w-full" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Skeleton className="h-64 md:col-span-2" />
              <Skeleton className="h-64" />
            </div>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (error || !notebook) {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <Navbar />
        <main className="flex-1 container mx-auto px-4 py-8">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error || 'Notebook not found'}</AlertDescription>
          </Alert>
          <Button
            variant="outline"
            onClick={() => navigate('/notebooks')}
            className="mt-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Notebooks
          </Button>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8">
        <Button
          variant="ghost"
          onClick={() => navigate('/notebooks')}
          className="mb-6"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Notebooks
        </Button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Header */}
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <FileCode className="h-8 w-8 text-primary" />
                      <Badge className={getDifficultyColor(notebook.difficulty)}>
                        {notebook.difficulty}
                      </Badge>
                      <Badge variant="outline" className="capitalize">
                        {notebook.category.replace(/_/g, ' ')}
                      </Badge>
                    </div>
                    <CardTitle className="text-3xl mb-2">{notebook.title}</CardTitle>
                    <CardDescription className="text-base">
                      {notebook.description}
                    </CardDescription>
                  </div>
                </div>

                <div className="flex items-center gap-4 mt-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4" />
                    <span>{notebook.author_name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    <span>Updated {formatDate(notebook.updated_at)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Code2 className="h-4 w-4" />
                    <span>v{notebook.current_version}</span>
                  </div>
                </div>
              </CardHeader>

              <CardContent>
                {/* Action Buttons */}
                <div className="flex flex-wrap gap-3 mb-6">
                  <Button onClick={handleDownload} disabled={downloading}>
                    {downloading ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Download className="mr-2 h-4 w-4" />
                    )}
                    Download
                  </Button>

                  <Button
                    variant={notebook.user_vote === 'upvote' ? 'default' : 'outline'}
                    onClick={() => handleVote('upvote')}
                    disabled={voting || !user}
                  >
                    <ThumbsUp className="mr-2 h-4 w-4" />
                    {notebook.upvotes}
                  </Button>

                  <Button
                    variant={notebook.user_vote === 'downvote' ? 'default' : 'outline'}
                    onClick={() => handleVote('downvote')}
                    disabled={voting || !user}
                  >
                    <ThumbsDown className="mr-2 h-4 w-4" />
                    {notebook.downvotes}
                  </Button>

                  <Button
                    variant={notebook.is_bookmarked ? 'default' : 'outline'}
                    onClick={handleBookmark}
                    disabled={bookmarking || !user}
                  >
                    <BookMarked className="mr-2 h-4 w-4" />
                    Bookmark
                  </Button>

                  <Button variant="outline">
                    <Share2 className="mr-2 h-4 w-4" />
                    Share
                  </Button>
                </div>

                <Separator className="my-6" />

                {/* Tags and Languages */}
                <div className="space-y-4">
                  {notebook.language_codes.length > 0 && (
                    <div>
                      <h3 className="text-sm font-semibold mb-2">Languages</h3>
                      <div className="flex flex-wrap gap-2">
                        {notebook.language_codes.map(code => (
                          <Badge key={code} variant="secondary">
                            {code}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {notebook.tags.length > 0 && (
                    <div>
                      <h3 className="text-sm font-semibold mb-2">Tags</h3>
                      <div className="flex flex-wrap gap-2">
                        {notebook.tags.map(tag => (
                          <Badge key={tag} variant="outline">
                            <Tag className="mr-1 h-3 w-3" />
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Comments Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Comments ({comments.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {/* Comment Input */}
                {user ? (
                  <div className="mb-6">
                    <textarea
                      className="w-full p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows={3}
                      placeholder="Add a comment..."
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      disabled={submittingComment}
                    />
                    <div className="flex justify-end mt-2">
                      <Button
                        onClick={handleSubmitComment}
                        disabled={submittingComment || !newComment.trim()}
                        size="sm"
                      >
                        {submittingComment ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Posting...
                          </>
                        ) : (
                          'Post Comment'
                        )}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="mb-6 p-4 bg-muted rounded-lg text-center">
                    <p className="text-sm text-muted-foreground">
                      Please sign in to comment
                    </p>
                  </div>
                )}

                {/* Comments List */}
                {commentsLoading ? (
                  <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="flex gap-3">
                        <Skeleton className="h-10 w-10 rounded-full" />
                        <div className="flex-1 space-y-2">
                          <Skeleton className="h-4 w-24" />
                          <Skeleton className="h-16 w-full" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : comments.length > 0 ? (
                  <div className="space-y-4">
                    {comments.map((comment, index) => (
                      <div key={comment.id || index} className="flex gap-3 p-3 rounded-lg bg-muted/30">
                        <div className="flex-shrink-0">
                          <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                            <User className="h-5 w-5 text-blue-600" />
                          </div>
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-sm">
                                {comment.author_name || comment.user_name || 'Anonymous'}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {comment.created_at ? new Date(comment.created_at).toLocaleDateString() : 'Recently'}
                              </span>
                            </div>
                            {user && (
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-7 w-7 p-0"
                                onClick={() => {
                                  setReportEntity({
                                    type: 'comment',
                                    id: comment.id,
                                    title: `Comment by ${comment.author_name || comment.user_name || 'Anonymous'}`
                                  });
                                  setReportModalOpen(true);
                                }}
                              >
                                <Flag className="h-3.5 w-3.5 text-muted-foreground hover:text-red-600" />
                              </Button>
                            )}
                          </div>
                          <p className="text-sm text-foreground">
                            {comment.content || comment.comment}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No comments yet</p>
                    <p className="text-sm">Be the first to comment!</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm">
                    <Star className="h-4 w-4 text-muted-foreground" />
                    <span>Rating</span>
                  </div>
                  <span className="font-semibold">{notebook.rating.toFixed(1)}</span>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm">
                    <Download className="h-4 w-4 text-muted-foreground" />
                    <span>Downloads</span>
                  </div>
                  <span className="font-semibold">{notebook.usage_stats.downloads}</span>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm">
                    <Eye className="h-4 w-4 text-muted-foreground" />
                    <span>Views</span>
                  </div>
                  <span className="font-semibold">{notebook.usage_stats.views}</span>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm">
                    <Play className="h-4 w-4 text-muted-foreground" />
                    <span>Successful Runs</span>
                  </div>
                  <span className="font-semibold">{notebook.usage_stats.successful_runs}</span>
                </div>
              </CardContent>
            </Card>

            {/* Details */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div>
                  <span className="text-muted-foreground">File Size</span>
                  <p className="font-semibold">{formatFileSize(notebook.file_size)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">License</span>
                  <p className="font-semibold">{notebook.license}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Created</span>
                  <p className="font-semibold">{formatDate(notebook.created_at)}</p>
                </div>
                {notebook.published_at && (
                  <div>
                    <span className="text-muted-foreground">Published</span>
                    <p className="font-semibold">{formatDate(notebook.published_at)}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      <Footer />

      {/* Report Modal */}
      {reportEntity && (
        <ReportModal
          open={reportModalOpen}
          onOpenChange={setReportModalOpen}
          entityType={reportEntity.type as 'submission' | 'comment' | 'notebook'}
          entityId={reportEntity.id}
          entityTitle={reportEntity.title}
        />
      )}
    </div>
  );
};

export default NotebookDetail;
