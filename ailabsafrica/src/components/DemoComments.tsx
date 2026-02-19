import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { Star, MessageCircle, ThumbsUp, ThumbsDown, Flag, Check, X, Reply, MoreHorizontal } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface DemoComment {
  comment_id: string;
  user_name: string;
  user_email?: string;
  rating?: number;
  comment_text: string;
  created_at: string;
  replies: DemoReply[];
}

interface DemoReply {
  id: string;
  reply_text: string;
  is_public: boolean;
  created_at: string;
  user_id?: string;
}

interface CommentStats {
  total_comments: number;
  approved_comments: number;
  average_rating: number;
  rating_distribution: {
    '1': number;
    '2': number;
    '3': number;
    '4': number;
    '5': number;
  };
}

interface DemoCommentsProps {
  demoId: string;
  assistantName: string;
  assistantType: string;
  onCommentChange?: () => void;
}

const DemoComments: React.FC<DemoCommentsProps> = ({
  demoId,
  assistantName,
  assistantType,
  onCommentChange
}) => {
  const [comments, setComments] = useState<DemoComment[]>([]);
  const [stats, setStats] = useState<CommentStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCommentForm, setShowCommentForm] = useState(false);
  const [showStats, setShowStats] = useState(false);
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [moderatingComment, setModeratingComment] = useState<string | null>(null);
  
  // Form states
  const [formData, setFormData] = useState({
    user_name: '',
    user_email: '',
    rating: 0,
    comment_text: ''
  });
  
  const [replyText, setReplyText] = useState('');
  const [isPublicReply, setIsPublicReply] = useState(true);
  
  const { toast } = useToast();
  const { user } = useAuth();

  // Fetch comments and stats
  const fetchComments = async () => {
    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('demo-comments?action=get_comments', {
        body: { demo_id: demoId }
      });

      if (error) throw error;
      setComments(data.comments || []);
    } catch (error) {
      console.error('Error fetching comments:', error);
      toast({
        title: "Error",
        description: "Failed to load comments",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const { data, error } = await supabase.functions.invoke('demo-comments?action=get_comment_stats', {
        body: { demo_id: demoId }
      });

      if (error) throw error;
      setStats(data.stats);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  useEffect(() => {
    fetchComments();
    fetchStats();
  }, [demoId]);

  // Submit comment
  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.user_name.trim() || !formData.comment_text.trim()) {
      toast({
        title: "Validation Error",
        description: "Name and comment are required",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('demo-comments?action=create_comment', {
        body: {
          demo_id: demoId,
          user_name: formData.user_name.trim(),
          user_email: formData.user_email.trim() || undefined,
          rating: formData.rating || undefined,
          comment_text: formData.comment_text.trim(),
          user_agent: navigator.userAgent
        }
      });

      if (error) throw error;

      toast({
        title: "Success",
        description: data.message || "Comment submitted successfully",
      });

      // Reset form
      setFormData({
        user_name: '',
        user_email: '',
        rating: 0,
        comment_text: ''
      });
      setShowCommentForm(false);

      // Refresh comments and stats
      await fetchComments();
      await fetchStats();
      
      if (onCommentChange) {
        onCommentChange();
      }
    } catch (error) {
      console.error('Error submitting comment:', error);
      toast({
        title: "Error",
        description: "Failed to submit comment",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  // Add reply
  const handleAddReply = async (commentId: string) => {
    if (!replyText.trim()) {
      toast({
        title: "Validation Error",
        description: "Reply text is required",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('demo-comments', {
        body: {
          action: 'add_reply',
          comment_id: commentId,
          reply_text: replyText.trim(),
          is_public: isPublicReply
        }
      });

      if (error) throw error;

      toast({
        title: "Success",
        description: "Reply added successfully",
      });

      setReplyText('');
      setReplyingTo(null);
      await fetchComments();
    } catch (error) {
      console.error('Error adding reply:', error);
      toast({
        title: "Error",
        description: "Failed to add reply",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  // Moderate comment
  const handleModerateComment = async (commentId: string, action: 'approve' | 'flag', flaggedReason?: string) => {
    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('demo-comments', {
        body: {
          action: action === 'approve' ? 'approve_comment' : 'flag_comment',
          comment_id: commentId,
          ...(action === 'approve' ? { is_approved: true } : { is_flagged: true, flagged_reason: flaggedReason })
        }
      });

      if (error) throw error;

      toast({
        title: "Success",
        description: data.message,
      });

      setModeratingComment(null);
      await fetchComments();
      await fetchStats();
    } catch (error) {
      console.error('Error moderating comment:', error);
      toast({
        title: "Error",
        description: "Failed to moderate comment",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  // Render star rating
  const renderStars = (rating: number, interactive = false, onRatingChange?: (rating: number) => void) => {
    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => interactive && onRatingChange?.(star)}
            className={`${interactive ? 'cursor-pointer hover:scale-110' : 'cursor-default'} transition-transform`}
            disabled={!interactive}
          >
            <Star
              className={`w-4 h-4 ${
                star <= rating
                  ? 'fill-yellow-400 text-yellow-400'
                  : 'text-gray-300'
              }`}
            />
          </button>
        ))}
      </div>
    );
  };

  // Render comment
  const renderComment = (comment: DemoComment) => (
    <Card key={comment.comment_id} className="mb-4">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground text-sm font-medium">
              {comment.user_name.charAt(0).toUpperCase()}
            </div>
            <div>
              <div className="font-medium">{comment.user_name}</div>
              <div className="text-sm text-muted-foreground">
                {formatDistanceToNow(new Date(comment.created_at), { addSuffix: true })}
              </div>
            </div>
          </div>
          
          {user && (
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="ghost" size="sm" className="px-2 py-1">
                  <MoreHorizontal className="w-3 h-3" />
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Moderate Comment</DialogTitle>
                  <DialogDescription>
                    Manage this comment's visibility and status.
                  </DialogDescription>
                </DialogHeader>
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleModerateComment(comment.comment_id, 'approve')}
                    className="flex-1"
                  >
                    <Check className="w-4 h-4 mr-2" />
                    Approve
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={() => handleModerateComment(comment.comment_id, 'flag', 'Inappropriate content')}
                    className="flex-1"
                  >
                    <Flag className="w-4 h-4 mr-2" />
                    Flag
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </div>

        {comment.rating && (
          <div className="mb-3">
            {renderStars(comment.rating)}
          </div>
        )}

        <p className="text-sm mb-3">{comment.comment_text}</p>

        {/* Replies */}
        {comment.replies && comment.replies.length > 0 && (
          <div className="ml-6 border-l-2 border-muted pl-4 space-y-3">
            {comment.replies.map((reply) => (
              <div key={reply.id} className="flex items-start gap-2">
                <div className="w-6 h-6 bg-secondary rounded-full flex items-center justify-center text-secondary-foreground text-xs">
                  {reply.user_id ? 'U' : 'A'}
                </div>
                <div className="flex-1">
                  <div className="text-xs text-muted-foreground mb-1">
                    {reply.user_id ? 'User' : 'Admin'} • {formatDistanceToNow(new Date(reply.created_at), { addSuffix: true })}
                  </div>
                  <p className="text-sm">{reply.reply_text}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Reply form */}
        {replyingTo === comment.comment_id && (
          <div className="mt-4 p-4 bg-muted rounded-lg">
            <div className="flex items-center gap-2 mb-3">
              <input
                type="checkbox"
                id={`public-${comment.comment_id}`}
                checked={isPublicReply}
                onChange={(e) => setIsPublicReply(e.target.checked)}
                className="rounded"
              />
              <Label htmlFor={`public-${comment.comment_id}`} className="text-sm">
                Make reply public
              </Label>
            </div>
            <Textarea
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              placeholder="Write your reply..."
              className="mb-3"
            />
            <div className="flex gap-2">
              <Button
                onClick={() => handleAddReply(comment.comment_id)}
                disabled={loading}
                size="sm"
              >
                <Reply className="w-4 h-4 mr-2" />
                Reply
              </Button>
              <Button
                variant="outline"
                onClick={() => setReplyingTo(null)}
                size="sm"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {/* Reply button */}
        {user && replyingTo !== comment.comment_id && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setReplyingTo(comment.comment_id)}
            className="mt-2"
          >
            <Reply className="w-4 h-4 mr-2" />
            Reply
          </Button>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Comments & Feedback</h3>
          <p className="text-sm text-muted-foreground">
            Share your thoughts about this {assistantType} demo
          </p>
        </div>
        
        <div className="flex gap-2">
          {stats && (
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="px-2 py-1 text-xs">
                  <MessageCircle className="w-3 h-3 mr-1" />
                  <span className="hidden sm:inline">Stats ({stats.approved_comments})</span>
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Comment Statistics</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold">{stats.total_comments}</div>
                      <div className="text-sm text-muted-foreground">Total Comments</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">{stats.approved_comments}</div>
                      <div className="text-sm text-muted-foreground">Approved</div>
                    </div>
                  </div>
                  
                  {stats.average_rating > 0 && (
                    <div className="text-center">
                      <div className="text-2xl font-bold">{stats.average_rating.toFixed(1)}</div>
                      <div className="text-sm text-muted-foreground mb-2">Average Rating</div>
                      {renderStars(Math.round(stats.average_rating))}
                    </div>
                  )}
                  
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Rating Distribution</div>
                    {[5, 4, 3, 2, 1].map((rating) => (
                      <div key={rating} className="flex items-center gap-2">
                        <span className="text-sm w-4">{rating}★</span>
                        <div className="flex-1 bg-muted rounded-full h-2">
                          <div
                            className="bg-yellow-400 h-2 rounded-full"
                            style={{
                              width: `${stats.total_comments > 0 ? (stats.rating_distribution[rating as keyof typeof stats.rating_distribution] / stats.total_comments) * 100 : 0}%`
                            }}
                          />
                        </div>
                        <span className="text-sm text-muted-foreground w-8">
                          {stats.rating_distribution[rating as keyof typeof stats.rating_distribution]}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          )}
          
          <Button onClick={() => setShowCommentForm(true)} size="sm" className="px-2 py-1 text-xs">
            <MessageCircle className="w-3 h-3 mr-1" />
            <span className="hidden sm:inline">Add Comment</span>
          </Button>
        </div>
      </div>

      {/* Comment Form Dialog */}
      <Dialog open={showCommentForm} onOpenChange={setShowCommentForm}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add Your Comment</DialogTitle>
            <DialogDescription>
              Share your feedback about the {assistantName} demo
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmitComment} className="space-y-4">
            <div>
              <Label htmlFor="user_name">Name *</Label>
              <Input
                id="user_name"
                value={formData.user_name}
                onChange={(e) => setFormData({ ...formData, user_name: e.target.value })}
                placeholder="Your name"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="user_email">Email (optional)</Label>
              <Input
                id="user_email"
                type="email"
                value={formData.user_email}
                onChange={(e) => setFormData({ ...formData, user_email: e.target.value })}
                placeholder="your.email@example.com"
              />
            </div>
            
            <div>
              <Label>Rating (optional)</Label>
              <div className="mt-2">
                {renderStars(formData.rating, true, (rating) => 
                  setFormData({ ...formData, rating })
                )}
              </div>
            </div>
            
            <div>
              <Label htmlFor="comment_text">Comment *</Label>
              <Textarea
                id="comment_text"
                value={formData.comment_text}
                onChange={(e) => setFormData({ ...formData, comment_text: e.target.value })}
                placeholder="Share your thoughts about this demo..."
                rows={4}
                required
              />
            </div>
            
            <div className="flex gap-2">
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? 'Submitting...' : 'Submit Comment'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCommentForm(false)}
              >
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Comments List */}
      <div className="space-y-4">
        {loading && comments.length === 0 ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="text-muted-foreground mt-2">Loading comments...</p>
          </div>
        ) : comments.length === 0 ? (
          <Card>
            <CardContent className="pt-6 text-center">
              <MessageCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h4 className="text-lg font-medium mb-2">No comments yet</h4>
              <p className="text-muted-foreground mb-4">
                Be the first to share your thoughts about this demo!
              </p>
              <Button onClick={() => setShowCommentForm(true)} size="sm" className="px-3 py-1 text-xs">
                Add First Comment
              </Button>
            </CardContent>
          </Card>
        ) : (
          comments.map(renderComment)
        )}
      </div>
    </div>
  );
};

export default DemoComments;
