import { useState, useEffect, useRef, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Heart,
  MessageCircle,
  Bookmark,
  Share2,
  Play,
  Pause,
  Volume2,
  BookOpen,
  ChevronDown,
  Send,
  MoreHorizontal,
  Sparkles,
  Edit,
  CheckCircle,
  Circle,
  Reply,
  Trash2,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { devotionalDB } from '@/lib/db';
import { useOfflineSync } from '@/hooks/useOfflineSync';
import { useAuth } from '@/contexts/AuthContext';
import { SwipeableDevotionalView } from '@/components/mobile/SwipeableDevotionalView';
import { useLongPress } from '@/hooks/useLongPress';
import { useToast } from '@/hooks/use-toast';
import { DevotionalCardSkeleton } from '@/components/loading/DevotionalCardSkeleton';
import { ShareSheet } from '@/components/social/ShareSheet';
import { ShareData } from '@/lib/share';
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AdminSidebar } from "@/components/admin/AdminSidebar";
import { getImageUrl } from '@/lib/image-utils';
import { ReadingSettings } from '@/components/reader/ReadingSettings';
import { logger } from '@/lib/logger';

interface DevotionalData {
  id: string;
  title: string;
  content: any[];
  excerpt: string;
  author_id: string;
  author_name: string;
  author_bio?: string;
  author_avatar?: string;
  cover_image_url?: string;
  audio_url?: string;
  reading_time_minutes: number;
  published_at: string;
  categories: string[];
  likes_count: number;
  comments_count: number;
  is_liked?: boolean;
  is_bookmarked?: boolean;
  is_read?: boolean;
  reading_progress?: number;
}

interface Comment {
  id: string;
  user_id: string;
  user_name: string;
  text: string;
  created_at: string;
  likes_count: number;
  is_liked?: boolean;
  replies?: Comment[];
}

const Devotional = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const { isOnline, queueAction } = useOfflineSync();
  const { user, isAdmin } = useAuth();
  const { toast } = useToast();

  const [isPlaying, setIsPlaying] = useState(searchParams.get('autoplay') === 'true');
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [showComments, setShowComments] = useState(window.location.hash === '#comments');
  const [showShareSheet, setShowShareSheet] = useState(false);
  const [shareSheetData, setShareSheetData] = useState<ShareData | null>(null);
  const [newComment, setNewComment] = useState("");
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [editingComment, setEditingComment] = useState<string | null>(null);
  const [editText, setEditText] = useState("");

  // Open comments when navigating with #comments hash
  useEffect(() => {
    if (window.location.hash === '#comments') {
      setShowComments(true);
    }
  }, [id]);

  // Update audio playback speed when changed
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackSpeed;
    }
  }, [playbackSpeed]);

  // Reading preferences from user or defaults
  const [fontSize, setFontSize] = useState<"small" | "medium" | "large">("medium");
  const [theme, setTheme] = useState<"light" | "sepia" | "dark">("light");
  const [lineHeight, setLineHeight] = useState<"compact" | "normal" | "relaxed">("normal");

  // Sync reading preferences from user profile when it loads/changes
  useEffect(() => {
    if (user?.reading_preferences) {
      setFontSize(user.reading_preferences.font_size || "medium");
      setTheme(user.reading_preferences.theme || "light");
      setLineHeight(user.reading_preferences.line_height || "normal");
    }
  }, [user]);

  const [readingProgress, setReadingProgress] = useState(0);
  const [bookmarkedScriptures, setBookmarkedScriptures] = useState<Set<string>>(new Set());

  const startTimeRef = useRef<number>(Date.now());
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const hasRestoredPosition = useRef(false);

  // Fetch devotional with offline fallback
  const { data: devotional, isLoading } = useQuery({
    queryKey: ['devotional', id],
    queryFn: async () => {
      if (!id) throw new Error('No devotional ID provided');

      try {
        const data = await apiClient.getDevotional(id);

        // Cache for offline
        await devotionalDB.cacheDevotional(data);

        return data as DevotionalData;
      } catch (error) {
        if (!isOnline) {
          // Fallback to cached version
          const cached = await devotionalDB.getCachedDevotional(id);
          if (cached) return cached as DevotionalData;
        }
        throw error;
      }
    },
    enabled: !!id,
  });

  // Fetch prev/next devotionals if part of a series
  const { data: seriesDevotionals } = useQuery({
    queryKey: ['series-devotionals', devotional?.series_id],
    queryFn: async () => {
      if (!devotional?.series_id) return null;
      try {
        return await apiClient.getSeriesDevotionals(devotional.series_id);
      } catch (error) {
        logger.error('Failed to fetch series devotionals:', error);
        return null;
      }
    },
    enabled: !!devotional?.series_id,
  });

  // Calculate prev/next IDs
  const prevId = useMemo(() => {
    if (!devotional || !seriesDevotionals) return undefined;
    const published = seriesDevotionals.filter((d: any) => d.status === 'published');
    const currentIndex = published.findIndex((d: any) => d.id === devotional.id);
    if (currentIndex > 0) {
      return published[currentIndex - 1].id;
    }
    return undefined;
  }, [devotional, seriesDevotionals]);

  const nextId = useMemo(() => {
    if (!devotional || !seriesDevotionals) return undefined;
    const published = seriesDevotionals.filter((d: any) => d.status === 'published');
    const currentIndex = published.findIndex((d: any) => d.id === devotional.id);
    if (currentIndex >= 0 && currentIndex < published.length - 1) {
      return published[currentIndex + 1].id;
    }
    return undefined;
  }, [devotional, seriesDevotionals]);

  // Fetch comments
  const { data: comments = [] } = useQuery({
    queryKey: ['comments', id],
    queryFn: async () => {
      if (!id) return [];
      const response = await apiClient.getComments(id);
      // Backend returns array directly, not wrapped in { items: [] }
      return Array.isArray(response) ? response : [];
    },
    enabled: !!id && showComments,
  });

  // Like mutation
  const likeMutation = useMutation({
    mutationFn: async () => {
      if (!user) {
        toast({
          title: "Sign in required",
          description: "Please sign in to like devotionals",
          action: (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/login?redirect=' + encodeURIComponent(window.location.pathname))}
            >
              Sign In
            </Button>
          ),
        });
        throw new Error('Authentication required');
      }
      if (!id) return;
      if (!isOnline) {
        await queueAction({ action: 'like', target_id: id });
        return;
      }
      return await apiClient.likeDevotional(id);
    },
    onMutate: async () => {
      if (!user) return;
      await queryClient.cancelQueries({ queryKey: ['devotional', id] });
      const previous = queryClient.getQueryData(['devotional', id]);

      queryClient.setQueryData(['devotional', id], (old: any) => ({
        ...old,
        likes_count: old.likes_count + (old.is_liked ? -1 : 1),
        is_liked: !old.is_liked,
      }));

      return { previous };
    },
    onError: (err, vars, context) => {
      if (err.message === 'Authentication required') return;
      queryClient.setQueryData(['devotional', id], context?.previous);
      toast({
        title: "Error",
        description: "Failed to like devotional",
        variant: "destructive"
      });
    },
    onSuccess: () => {
      // Invalidate all queries that might show this devotional
      queryClient.invalidateQueries({ queryKey: ['devotionals'] });
      queryClient.invalidateQueries({ queryKey: ['trendingDevotionals'] });
      queryClient.invalidateQueries({ queryKey: ['devotional', id] });
    }
  });

  // Bookmark mutation
  const bookmarkMutation = useMutation({
    mutationFn: async () => {
      if (!user) {
        toast({
          title: "Sign in required",
          description: "Please sign in to save devotionals",
          action: (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/login?redirect=' + encodeURIComponent(window.location.pathname))}
            >
              Sign In
            </Button>
          ),
        });
        throw new Error('Authentication required');
      }
      if (!id) return;
      if (!isOnline) {
        await queueAction({ action: 'bookmark', target_id: id });
        return;
      }
      return await apiClient.bookmarkDevotional(id);
    },
    onMutate: async () => {
      if (!user) return;
      await queryClient.cancelQueries({ queryKey: ['devotional', id] });
      const previous = queryClient.getQueryData(['devotional', id]);

      // Optimistically update the cache
      queryClient.setQueryData(['devotional', id], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          is_bookmarked: !old.is_bookmarked,
        };
      });

      return { previous };
    },
    onError: (err, vars, context) => {
      if (err.message === 'Authentication required') return;
      queryClient.setQueryData(['devotional', id], context?.previous);
      toast({
        title: "Error",
        description: "Failed to bookmark",
        variant: "destructive"
      });
    },
    onSuccess: (data) => {
      // Invalidate queries to refresh bookmarks list
      queryClient.invalidateQueries({ queryKey: ['bookmarked-devotionals'] });
      queryClient.invalidateQueries({ queryKey: ['bookmarks'] }); // For Profile page
      queryClient.invalidateQueries({ queryKey: ['devotional', id] });

      if (!isOnline) {
        toast({
          title: "Queued",
          description: "Bookmark will sync when online"
        });
      } else {
        // Use the response data to determine the new state
        const isBookmarked = data?.is_bookmarked ?? false;
        toast({
          title: isBookmarked ? "Bookmarked" : "Removed",
          description: isBookmarked
            ? "Added to your bookmarks"
            : "Removed from bookmarks"
        });
      }
    },
  });

  // Scripture bookmark mutation
  const scriptureBookmarkMutation = useMutation({
    mutationFn: async (scriptureData: { reference: string; verse_text?: string; translation?: string }) => {
      if (!user) {
        toast({
          title: "Sign in required",
          description: "Please sign in to save scriptures",
          action: (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/login?redirect=' + encodeURIComponent(window.location.pathname))}
            >
              Sign In
            </Button>
          ),
        });
        throw new Error('Authentication required');
      }
      if (!isOnline) {
        await queueAction({ 
          action: 'bookmark', 
          target_id: scriptureData.reference,
          payload: { type: 'scripture', ...scriptureData }
        });
        return;
      }
      return await apiClient.bookmarkScripture({
        ...scriptureData,
        devotional_id: id,
      });
    },
    onMutate: async (scriptureData) => {
      if (!user) return;
      const ref = scriptureData.reference;
      const isBookmarked = bookmarkedScriptures.has(ref);
      setBookmarkedScriptures(prev => {
        const next = new Set(prev);
        if (isBookmarked) {
          next.delete(ref);
        } else {
          next.add(ref);
        }
        return next;
      });
      return { previous: bookmarkedScriptures };
    },
    onError: (err, vars, context) => {
      if (err.message === 'Authentication required') return;
      setBookmarkedScriptures(context?.previous || new Set());
      toast({
        title: "Error",
        description: "Failed to bookmark scripture",
        variant: "destructive"
      });
    },
    onSuccess: (data, scriptureData) => {
      if (!isOnline) {
        toast({
          title: "Queued",
          description: "Scripture bookmark will sync when online"
        });
      } else {
        const isBookmarked = bookmarkedScriptures.has(scriptureData.reference);
        toast({
          title: isBookmarked ? "Bookmarked" : "Removed",
          description: isBookmarked
            ? "Scripture added to your bookmarks"
            : "Scripture removed from bookmarks"
        });
      }
    },
  });

  // Comment mutation with authentication check
  const commentMutation = useMutation({
    mutationFn: async ({ text, parent_comment_id }: { text: string; parent_comment_id?: string }) => {
      if (!user) {
        toast({
          title: "Sign in required",
          description: "Please sign in to comment",
          action: (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/login?redirect=' + encodeURIComponent(window.location.pathname))}
            >
              Sign In
            </Button>
          ),
        });
        throw new Error('Authentication required');
      }
      if (!id) return;
      if (!isOnline) {
        await queueAction({ action: 'comment', target_id: id, payload: { text, parent_comment_id } });
        return;
      }
      return await apiClient.createComment(id, { text, parent_comment_id });
    },
    onSuccess: () => {
      // Invalidate all queries to update comment counts everywhere
      queryClient.invalidateQueries({ queryKey: ['comments', id] });
      queryClient.invalidateQueries({ queryKey: ['devotional', id] });
      queryClient.invalidateQueries({ queryKey: ['devotionals'] });
      queryClient.invalidateQueries({ queryKey: ['trendingDevotionals'] });
      setNewComment("");
      setReplyingTo(null);
      if (!isOnline) {
        toast({
          title: "Queued",
          description: "Comment will post when online"
        });
      } else {
        toast({
          title: replyingTo ? "Reply posted" : "Comment posted",
          description: replyingTo ? "Your reply has been added successfully" : "Your comment has been added successfully"
        });
      }
    },
    onError: (err: any) => {
      if (err.message === 'Authentication required') return;
      toast({
        title: "Error",
        description: "Failed to post comment. Please try again.",
        variant: "destructive"
      });
    }
  });

  // Comment like mutation
  const commentLikeMutation = useMutation({
    mutationFn: async (commentId: string) => {
      if (!user) {
        toast({
          title: "Sign in required",
          description: "Please sign in to like comments",
          action: (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/login?redirect=' + encodeURIComponent(window.location.pathname))}
            >
              Sign In
            </Button>
          ),
        });
        throw new Error('Authentication required');
      }
      if (!isOnline) {
        await queueAction({ action: 'like_comment', target_id: commentId });
        return;
      }
      return await apiClient.likeComment(commentId);
    },
    onMutate: async (commentId) => {
      if (!user) return;
      await queryClient.cancelQueries({ queryKey: ['comments', id] });
      const previous = queryClient.getQueryData(['comments', id]);

      // Optimistically update the comment
      queryClient.setQueryData(['comments', id], (old: any) => {
        if (!Array.isArray(old)) return old;
        return old.map((comment: Comment) => {
          if (comment.id === commentId) {
            return {
              ...comment,
              likes_count: comment.likes_count + (comment.is_liked ? -1 : 1),
              is_liked: !comment.is_liked,
            };
          }
          return comment;
        });
      });

      return { previous };
    },
    onError: (err: any, commentId, context) => {
      if (err.message === 'Authentication required') return;
      queryClient.setQueryData(['comments', id], context?.previous);
      toast({
        title: "Error",
        description: "Failed to like comment",
        variant: "destructive"
      });
    },
    onSuccess: () => {
      // Invalidate to get fresh data
      queryClient.invalidateQueries({ queryKey: ['comments', id] });
      if (!isOnline) {
        toast({
          title: "Queued",
          description: "Like will sync when online"
        });
      }
    },
  });

  // Edit comment mutation
  const editCommentMutation = useMutation({
    mutationFn: async ({ commentId, text }: { commentId: string; text: string }) => {
      if (!user) throw new Error('Authentication required');
      return await apiClient.updateComment(commentId, { text });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', id] });
      setEditingComment(null);
      setEditText("");
      toast({
        title: "Comment updated",
        description: "Your comment has been updated successfully"
      });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to update comment",
        variant: "destructive"
      });
    }
  });

  // Delete comment mutation
  const deleteCommentMutation = useMutation({
    mutationFn: async (commentId: string) => {
      if (!user) throw new Error('Authentication required');
      return await apiClient.deleteComment(commentId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', id] });
      queryClient.invalidateQueries({ queryKey: ['devotional', id] });
      queryClient.invalidateQueries({ queryKey: ['devotionals'] });
      toast({
        title: "Comment deleted",
        description: "Your comment has been removed"
      });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to delete comment",
        variant: "destructive"
      });
    }
  });

  // Mark as read mutation
  const markAsReadMutation = useMutation({
    mutationFn: async () => {
      if (!user) {
        toast({
          title: "Sign in required",
          description: "Please sign in to track your reading",
          action: (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/login?redirect=' + encodeURIComponent(window.location.pathname))}
            >
              Sign In
            </Button>
          ),
        });
        throw new Error('Authentication required');
      }
      if (!id) return;
      if (!isOnline) {
        await queueAction({
          action: 'reading_progress',
          target_id: id,
          payload: { reading_progress: 100, time_spent_seconds: 0 }
        });
        return;
      }
      return await apiClient.markAsRead(id);
    },
    onMutate: async () => {
      if (!user) return;
      await queryClient.cancelQueries({ queryKey: ['devotional', id] });
      const previous = queryClient.getQueryData(['devotional', id]);

      queryClient.setQueryData(['devotional', id], (old: any) => ({
        ...old,
        is_read: true,
        reading_progress: 100,
      }));

      return { previous };
    },
    onError: (err: any, vars, context) => {
      if (err.message === 'Authentication required') return;
      queryClient.setQueryData(['devotional', id], context?.previous);
      toast({
        title: "Error",
        description: "Failed to mark as read",
        variant: "destructive"
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devotional', id] });
      queryClient.invalidateQueries({ queryKey: ['devotionals'] });
      queryClient.invalidateQueries({ queryKey: ['history'] });

      if (!isOnline) {
        toast({
          title: "Queued",
          description: "Will sync when online"
        });
      } else {
        toast({
          title: "Marked as read",
          description: "Added to your reading history"
        });
      }
    },
  });

  // Restore reading position on load
  useEffect(() => {
    if (!id || !devotional) return;

    const restorePosition = async () => {
      try {
        const cachedDevotional = await devotionalDB.getCachedDevotional(id);
        if (cachedDevotional?.reading_progress && cachedDevotional.reading_progress > 5 && cachedDevotional.reading_progress < 95) {
          // Wait a bit for content to render
          setTimeout(() => {
            if (scrollContainerRef.current) {
              const { scrollHeight, clientHeight } = scrollContainerRef.current;
              const targetScroll = (cachedDevotional.reading_progress / 100) * (scrollHeight - clientHeight);
              scrollContainerRef.current.scrollTo({
                top: targetScroll,
                behavior: 'smooth'
              });

              toast({
                title: "Continuing where you left off",
                description: `Restored to ${Math.round(cachedDevotional.reading_progress)}% progress`,
              });
            }
          }, 500);
        }
      } catch (error) {
        logger.error('Failed to restore reading position:', error);
      }
    };

    restorePosition();
  }, [id, devotional, toast]);

  // Track reading progress
  useEffect(() => {
    if (!id || !devotional) return;

    const handleScroll = () => {
      if (!scrollContainerRef.current) return;

      const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
      const progress = Math.min((scrollTop / (scrollHeight - clientHeight)) * 100, 100);
      setReadingProgress(progress);
    };

    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, [id, devotional]);

  // Track time spent and sync reading progress
  useEffect(() => {
    if (!id || !devotional) return;

    const interval = setInterval(async () => {
      const timeSpent = Math.floor((Date.now() - startTimeRef.current) / 1000);

      // Update IndexedDB
      await devotionalDB.updateReadingProgress(id, readingProgress);

      // Sync to server if online
      if (isOnline && readingProgress > 5) {
        try {
          await apiClient.trackReading(id, {
            reading_progress: readingProgress,
            time_spent_seconds: timeSpent,
          });
        } catch (error) {
          // Queue for later if fails
          await queueAction({
            action: 'reading_progress',
            target_id: id,
            payload: { reading_progress: readingProgress, time_spent_seconds: timeSpent }
          });
        }
      }
    }, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, [id, devotional, readingProgress, isOnline, queueAction]);

  // Restore scroll position from saved reading progress
  useEffect(() => {
    if (!devotional || !scrollContainerRef.current || hasRestoredPosition.current) return;

    const savedProgress = devotional.reading_progress || 0;

    // Only restore if there's meaningful progress (> 5%) and not already read
    if (savedProgress > 5 && savedProgress < 100) {
      const container = scrollContainerRef.current;
      const { scrollHeight, clientHeight } = container;
      const targetScrollTop = (savedProgress / 100) * (scrollHeight - clientHeight);

      // Smooth scroll to saved position after a short delay to ensure content is rendered
      setTimeout(() => {
        container.scrollTo({
          top: targetScrollTop,
          behavior: 'smooth'
        });

        toast({
          title: "Resumed reading",
          description: `Continuing from ${Math.round(savedProgress)}% progress`
        });
      }, 500);

      hasRestoredPosition.current = true;
    }
  }, [devotional, toast]);

  // Long-press for quick bookmark
  const longPressHandlers = useLongPress({
    onLongPress: () => {
      bookmarkMutation.mutate();
    },
    onClick: () => {
      // Regular click behavior
    },
  });

  const handleSubmitComment = () => {
    if (!newComment.trim()) return;
    commentMutation.mutate({
      text: newComment,
      parent_comment_id: replyingTo || undefined
    });
  };

  const handleShare = () => {
    if (!devotional) return;
    setShareSheetData({
      title: devotional.title,
      text: devotional.excerpt,
      url: window.location.href,
      imageUrl: devotional.cover_image_url,
    });
    setShowShareSheet(true);
  };

  const handleShareScripture = (scriptureBlock: any) => {
    const verseText = scriptureBlock.verse || scriptureBlock.text || '';
    const reference = scriptureBlock.reference || '';
    const shareText = `"${verseText}"\n\n${reference}`;
    const shareTitle = reference || 'Scripture';
    const shareUrl = devotional 
      ? `${window.location.origin}/devotional/${devotional.id}?verse=${encodeURIComponent(reference)}`
      : window.location.href;

    setShareSheetData({
      title: shareTitle,
      text: shareText,
      url: shareUrl,
      imageUrl: devotional?.cover_image_url,
    });
    setShowShareSheet(true);
  };

  const handleShareComplete = (platform: string) => {
    // Track share
    if (isOnline && devotional && shareSheetData) {
      // Check if it's a scripture share (has verse reference in URL)
      if (shareSheetData.url.includes('verse=')) {
        // Could track scripture shares separately if needed
        // For now, track as devotional share
        apiClient.shareDevotional(devotional.id, platform);
      } else {
        apiClient.shareDevotional(devotional.id, platform);
      }
    }
  };

  // Style mappings for reading preferences
  const getFontSizeClass = () => {
    switch (fontSize) {
      case "small": return "text-base";
      case "large": return "text-xl";
      default: return "text-lg";
    }
  };

  const getLineHeightClass = () => {
    switch (lineHeight) {
      case "compact": return "leading-snug";
      case "relaxed": return "leading-relaxed";
      default: return "leading-normal";
    }
  };

  const getThemeClasses = () => {
    switch (theme) {
      case "sepia": return "bg-[#f8f6f3] text-[#2a2a2a]";
      case "dark": return "bg-gray-900 text-gray-100";
      default: return "bg-white text-gray-900";
    }
  };

  const getHeaderThemeClasses = () => {
    switch (theme) {
      case "sepia": return "bg-[#f8f6f3]/95 border-[#e8e6e3]";
      case "dark": return "bg-gray-900/95 border-gray-700";
      default: return "bg-white/95 border-gray-200";
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatTime = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

    if (diffInHours < 1) return "Just now";
    if (diffInHours < 24) return `${diffInHours} hours ago`;
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays} days ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getAuthorInitials = (name: string | undefined) => {
    if (!name || typeof name !== 'string') return 'FM';  // Default: FreshManna
    return name
      .split(' ')
      .filter(n => n.length > 0)
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) || 'FM';
  };

  if (isLoading || !devotional) {
    return (
      <div className="min-h-screen bg-background">
        <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border">
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-between h-14">
              <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
                <ArrowLeft className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </header>
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-2xl mx-auto">
            <DevotionalCardSkeleton />
          </div>
        </main>
      </div>
    );
  }

  const content = (
    <SwipeableDevotionalView
      devotionalId={devotional.id}
      prevId={prevId}
      nextId={nextId}
    >
      <div
        className={`min-h-screen transition-colors ${getThemeClasses()}`}
        ref={scrollContainerRef}
        style={{ overflowY: 'auto' }}
      >
        {/* Header */}
        <header className={`sticky top-0 z-50 backdrop-blur-sm border-b transition-colors ${getHeaderThemeClasses()}`}>
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-between h-14">
              <div className="flex items-center gap-2">
                {isAdmin && <SidebarTrigger className="md:hidden" />}
                <Button variant="ghost" size="icon" onClick={() => navigate(-1)} aria-label="Go back">
                  <ArrowLeft className="w-5 h-5" />
                </Button>
              </div>
              <div className="flex items-center gap-2">
                {isAdmin && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => navigate(`/admin/compose?edit=${devotional.id}`)}
                    aria-label="Edit devotional"
                    title="Edit devotional"
                  >
                    <Edit className="w-5 h-5" />
                  </Button>
                )}
                {devotional.audio_url && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setIsPlaying(!isPlaying)}
                    aria-label={isPlaying ? "Pause audio" : "Play audio"}
                  >
                    {isPlaying ? (
                      <Pause className="w-5 h-5" />
                    ) : (
                      <Volume2 className="w-5 h-5" />
                    )}
                  </Button>
                )}
                <ReadingSettings
                  fontSize={fontSize}
                  theme={theme}
                  lineHeight={lineHeight}
                  onFontSizeChange={setFontSize}
                  onThemeChange={setTheme}
                  onLineHeightChange={setLineHeight}
                />
              </div>
            </div>
          </div>

          {/* Reading progress bar */}
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-muted">
            <motion.div
              className="h-full bg-secondary"
              initial={{ width: 0 }}
              animate={{ width: `${readingProgress}%` }}
              transition={{ duration: 0.1 }}
            />
          </div>
        </header>

        {/* Audio Player Bar */}
        <AnimatePresence>
          {isPlaying && devotional.audio_url && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="sticky top-14 z-40 bg-primary text-primary-foreground"
            >
              <div className="container mx-auto px-4 py-3">
                <div className="flex items-center gap-4">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-primary-foreground hover:bg-primary-foreground/10"
                    onClick={() => setIsPlaying(false)}
                    aria-label="Pause audio"
                  >
                    <Pause className="w-5 h-5" />
                  </Button>
                  <div className="flex-1">
                    <div className="h-1 bg-primary-foreground/20 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: "0%" }}
                        animate={{ width: "35%" }}
                        className="h-full bg-secondary"
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-primary-foreground hover:bg-primary-foreground/10 px-2 h-8 text-xs font-medium"
                      onClick={() => {
                        const speeds = [0.75, 1, 1.25, 1.5, 2];
                        const currentIndex = speeds.indexOf(playbackSpeed);
                        const nextIndex = (currentIndex + 1) % speeds.length;
                        setPlaybackSpeed(speeds[nextIndex]);
                      }}
                      aria-label={`Change playback speed. Current: ${playbackSpeed}x`}
                    >
                      {playbackSpeed}x
                    </Button>
                    <span className="text-sm text-primary-foreground/70">
                      1:45 / {devotional.reading_time_minutes}:00
                    </span>
                  </div>
                </div>
              </div>
              <audio
                ref={audioRef}
                src={devotional.audio_url}
                autoPlay={isPlaying}
                onEnded={() => setIsPlaying(false)}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Content */}
        <main className={`container mx-auto px-4 py-8 transition-colors ${getThemeClasses()}`}>
          <article className="max-w-2xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              {/* Cover Image */}
              {devotional.cover_image_url && (
                <div className="w-full h-64 md:h-96 rounded-3xl overflow-hidden mb-8">
                  <img
                    src={getImageUrl(devotional.cover_image_url) || ''}
                    alt={devotional.title}
                    className="w-full h-full object-cover"
                  />
                </div>
              )}

              {/* Meta */}
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-full bg-secondary/20 flex items-center justify-center">
                  <span className="font-semibold text-secondary">
                    {getAuthorInitials(devotional.author_name)}
                  </span>
                </div>
                <div>
                  <p className="font-medium text-foreground">
                    {devotional.author_name}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {formatDate(devotional.published_at)} · {devotional.reading_time_minutes} min read
                  </p>
                </div>
              </div>

              {/* Category */}
              {devotional.categories && devotional.categories[0] && (
                <span className="inline-block px-3 py-1 rounded-full bg-secondary/10 text-secondary text-sm font-medium mb-4">
                  {devotional.categories[0]}
                </span>
              )}

              {/* Title */}
              <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-8 leading-tight">
                {devotional.title}
              </h1>

              {/* AI Features */}
              {devotional.audio_url && (
                <div className="flex flex-wrap gap-2 mb-8">
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-2"
                    onClick={() => setIsPlaying(!isPlaying)}
                  >
                    <Play className="w-4 h-4" />
                    AI Voice
                  </Button>
                </div>
              )}

              {/* Body */}
              <div className={`space-y-6 ${getFontSizeClass()} ${getLineHeightClass()}`}>
                {devotional.content.map((block: any, index: number) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    {block.type === "paragraph" && (
                      <p>
                        {block.text}
                      </p>
                    )}
                    {block.type === "scripture" && (
                      <div className="bg-secondary/5 border-l-4 border-secondary rounded-r-xl p-6 my-8 group relative">
                        <p className="font-serif text-xl italic text-foreground/90 mb-3">
                          "{block.verse || block.text}"
                        </p>
                        {block.reference && (
                          <div className="flex items-center justify-between">
                            <p className="text-sm text-secondary font-medium flex items-center gap-2">
                              <BookOpen className="w-4 h-4" />
                              {block.reference}
                            </p>
                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={() => {
                                  scriptureBookmarkMutation.mutate({
                                    reference: block.reference,
                                    verse_text: block.verse || block.text,
                                    translation: block.translation || 'NIV',
                                  });
                                }}
                                aria-label={bookmarkedScriptures.has(block.reference) ? "Remove bookmark" : "Bookmark scripture"}
                                className={`p-2 rounded-lg hover:bg-secondary/10 ${
                                  bookmarkedScriptures.has(block.reference)
                                    ? "opacity-100 text-secondary"
                                    : "text-muted-foreground hover:text-secondary"
                                }`}
                                title={bookmarkedScriptures.has(block.reference) ? "Remove bookmark" : "Bookmark scripture"}
                              >
                                <Bookmark
                                  className={`w-4 h-4 ${
                                    bookmarkedScriptures.has(block.reference) ? "fill-secondary" : ""
                                  }`}
                                />
                              </button>
                              <button
                                onClick={() => handleShareScripture(block)}
                                aria-label="Share scripture"
                                className="p-2 rounded-lg hover:bg-secondary/10 text-muted-foreground hover:text-secondary transition-colors"
                                title="Share scripture"
                              >
                                <Share2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    {block.type === "prayer" && (
                      <div className="bg-accent/5 border border-accent/20 rounded-2xl p-6 my-8">
                        <p className="text-sm font-medium text-accent mb-2">
                          Prayer
                        </p>
                        <p className="italic text-foreground/90">{block.text}</p>
                      </div>
                    )}
                    {block.type === "heading" && (
                      <h2 className="text-2xl font-bold text-foreground mt-8 mb-4">
                        {block.text}
                      </h2>
                    )}
                  </motion.div>
                ))}
              </div>

              {/* Author Bio */}
              {devotional.author_bio && (
                <div className="mt-12 pt-8 border-t border-border">
                  <div className="flex items-start gap-4">
                    <div className="w-16 h-16 rounded-full bg-secondary/20 flex items-center justify-center shrink-0">
                      <span className="font-bold text-xl text-secondary">
                        {getAuthorInitials(devotional.author_name)}
                      </span>
                    </div>
                    <div>
                      <p className="text-lg font-semibold text-foreground">
                        {devotional.author_name}
                      </p>
                      <p className="text-muted-foreground mb-3">
                        {devotional.author_bio}
                      </p>
                      <Button variant="secondary" size="sm">
                        Follow
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {/* Quick Navigation */}
              <div className="mt-12 pt-8 border-t border-border">
                <h3 className="font-serif text-lg font-semibold text-foreground mb-4">
                  Explore More
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Button
                    variant="outline"
                    className="flex flex-col items-start h-auto p-4 gap-2"
                    onClick={() => navigate('/feed')}
                  >
                    <BookOpen className="w-5 h-5 text-secondary" />
                    <div className="text-left">
                      <p className="font-medium text-foreground">Daily Devotionals</p>
                      <p className="text-xs text-muted-foreground">Browse all devotionals</p>
                    </div>
                  </Button>
                  <Button
                    variant="outline"
                    className="flex flex-col items-start h-auto p-4 gap-2"
                    onClick={() => navigate('/discussions')}
                  >
                    <MessageCircle className="w-5 h-5 text-secondary" />
                    <div className="text-left">
                      <p className="font-medium text-foreground">Group Discussions</p>
                      <p className="text-xs text-muted-foreground">Join conversations</p>
                    </div>
                  </Button>
                  <Button
                    variant="outline"
                    className="flex flex-col items-start h-auto p-4 gap-2"
                    onClick={() => navigate('/bookmarks')}
                  >
                    <Bookmark className="w-5 h-5 text-secondary" />
                    <div className="text-left">
                      <p className="font-medium text-foreground">Saved Items</p>
                      <p className="text-xs text-muted-foreground">View your bookmarks</p>
                    </div>
                  </Button>
                </div>
              </div>
            </motion.div>
          </article>
        </main>

        {/* Floating Action Bar */}
        <div className="sticky bottom-0 bg-background/95 backdrop-blur-sm border-t border-border">
          <div className="container mx-auto px-4 py-3">
            <div className="max-w-2xl mx-auto flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => likeMutation.mutate()}
                  disabled={likeMutation.isPending}
                  className={`flex items-center gap-1.5 transition-all group ${
                    devotional.is_liked
                      ? "text-secondary"
                      : "text-muted-foreground hover:text-secondary"
                  } ${likeMutation.isPending ? "opacity-50" : ""}`}
                >
                  <motion.div
                    animate={devotional.is_liked ? {
                      scale: [1, 1.3, 1],
                    } : {}}
                    transition={{ duration: 0.3 }}
                  >
                    <Heart
                      className={`w-6 h-6 transition-all ${
                        devotional.is_liked ? "fill-secondary" : ""
                      } ${!devotional.is_liked ? "group-hover:scale-110" : ""}`}
                    />
                  </motion.div>
                  <span className="font-medium">
                    {devotional.likes_count}
                  </span>
                </button>
                <button
                  onClick={() => setShowComments(!showComments)}
                  className="flex items-center gap-1.5 text-muted-foreground hover:text-accent transition-colors"
                >
                  <MessageCircle className="w-6 h-6" />
                  <span className="font-medium">
                    {devotional.comments_count}
                  </span>
                </button>
                <button
                  {...longPressHandlers}
                  onClick={() => bookmarkMutation.mutate()}
                  disabled={bookmarkMutation.isPending}
                  className={`transition-colors ${
                    devotional.is_bookmarked
                      ? "text-secondary"
                      : "text-muted-foreground hover:text-secondary"
                  } ${bookmarkMutation.isPending ? "opacity-50 cursor-not-allowed" : ""}`}
                  title={devotional.is_bookmarked ? "Remove bookmark" : "Bookmark this devotional"}
                >
                  <Bookmark
                    className={`w-6 h-6 transition-all ${devotional.is_bookmarked ? "fill-secondary" : ""} ${
                      bookmarkMutation.isPending ? "animate-pulse" : ""
                    }`}
                  />
                </button>
                <button
                  onClick={() => markAsReadMutation.mutate()}
                  disabled={markAsReadMutation.isPending || devotional.is_read}
                  className={`transition-colors ${
                    devotional.is_read
                      ? "text-green-600"
                      : "text-muted-foreground hover:text-green-600"
                  } ${markAsReadMutation.isPending || devotional.is_read ? "opacity-50" : ""}`}
                  title={devotional.is_read ? "Marked as read" : "Mark as read"}
                >
                  {devotional.is_read ? (
                    <CheckCircle className="w-6 h-6 fill-green-600" />
                  ) : (
                    <Circle className="w-6 h-6" />
                  )}
                </button>
              </div>
              <Button variant="outline" size="sm" className="gap-2" onClick={handleShare}>
                <Share2 className="w-4 h-4" />
                Share
              </Button>
            </div>
          </div>
        </div>

        {/* Comments Sheet */}
        <AnimatePresence>
          {showComments && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-foreground/20 z-50"
                onClick={() => setShowComments(false)}
              />
              <motion.div
                initial={{ y: "100%" }}
                animate={{ y: 0 }}
                exit={{ y: "100%" }}
                transition={{ type: "spring", damping: 25 }}
                className="fixed bottom-0 left-0 right-0 z-50 bg-background rounded-t-3xl max-h-[80vh] overflow-hidden"
              >
                <div className="p-4 border-b border-border">
                  <div className="w-12 h-1 bg-muted rounded-full mx-auto mb-4" />
                  <div className="flex items-center justify-between">
                    <h3 className="font-serif text-lg font-semibold">
                      Comments ({devotional.comments_count})
                    </h3>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setShowComments(false)}
                    >
                      <ChevronDown className="w-5 h-5" />
                    </Button>
                  </div>
                </div>

                <div className="overflow-y-auto max-h-[50vh] p-4 space-y-4">
                  {comments.length === 0 ? (
                    <p className="text-center text-muted-foreground py-8">
                      No comments yet. Be the first to share your thoughts!
                    </p>
                  ) : (
                    comments.map((comment: Comment) => (
                      <div key={comment.id} className="space-y-2">
                        <div className="flex gap-3">
                          <div className="w-10 h-10 rounded-full bg-secondary/10 flex items-center justify-center shrink-0">
                            <span className="text-sm font-semibold text-secondary">
                              {getAuthorInitials(comment.user_name)}
                            </span>
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-foreground">
                                {comment.user_name}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {formatTime(comment.created_at)}
                              </span>
                            </div>

                            {editingComment === comment.id ? (
                              <div className="space-y-2">
                                <Textarea
                                  value={editText}
                                  onChange={(e) => setEditText(e.target.value)}
                                  className="min-h-[60px]"
                                  autoFocus
                                />
                                <div className="flex gap-2">
                                  <Button
                                    size="sm"
                                    onClick={() => {
                                      if (editText.trim()) {
                                        editCommentMutation.mutate({
                                          commentId: comment.id,
                                          text: editText
                                        });
                                      }
                                    }}
                                    disabled={!editText.trim() || editCommentMutation.isPending}
                                  >
                                    Save
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => {
                                      setEditingComment(null);
                                      setEditText("");
                                    }}
                                  >
                                    Cancel
                                  </Button>
                                </div>
                              </div>
                            ) : (
                              <>
                                <p className="text-foreground/90">{comment.text}</p>
                                <div className="flex items-center gap-3 mt-2">
                                  <button
                                    onClick={() => commentLikeMutation.mutate(comment.id)}
                                    disabled={commentLikeMutation.isPending}
                                    className={`flex items-center gap-1 transition-all group text-sm ${
                                      comment.is_liked
                                        ? "text-secondary"
                                        : "text-muted-foreground hover:text-secondary"
                                    } ${commentLikeMutation.isPending ? "opacity-50" : ""}`}
                                  >
                                    <motion.div
                                      animate={comment.is_liked ? {
                                        scale: [1, 1.2, 1],
                                      } : {}}
                                      transition={{ duration: 0.3 }}
                                    >
                                      <Heart
                                        className={`w-4 h-4 transition-all ${
                                          comment.is_liked ? "fill-secondary" : ""
                                        } ${!comment.is_liked ? "group-hover:scale-110" : ""}`}
                                      />
                                    </motion.div>
                                    <span className="font-medium">{comment.likes_count || 0}</span>
                                  </button>

                                  {user && (
                                    <button
                                      onClick={() => {
                                        setReplyingTo(comment.id);
                                        setNewComment(`@${comment.user_name} `);
                                      }}
                                      className="flex items-center gap-1 text-sm text-muted-foreground hover:text-accent transition-colors"
                                    >
                                      <Reply className="w-4 h-4" />
                                      <span>Reply</span>
                                    </button>
                                  )}

                                  {user && user.user_id === comment.user_id && (
                                    <>
                                      <button
                                        onClick={() => {
                                          setEditingComment(comment.id);
                                          setEditText(comment.text);
                                        }}
                                        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-accent transition-colors"
                                      >
                                        <Edit className="w-4 h-4" />
                                        <span>Edit</span>
                                      </button>
                                      <button
                                        onClick={() => {
                                          if (confirm("Are you sure you want to delete this comment?")) {
                                            deleteCommentMutation.mutate(comment.id);
                                          }
                                        }}
                                        disabled={deleteCommentMutation.isPending}
                                        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-destructive transition-colors"
                                      >
                                        <Trash2 className="w-4 h-4" />
                                        <span>Delete</span>
                                      </button>
                                    </>
                                  )}
                                </div>
                              </>
                            )}
                          </div>
                        </div>

                        {/* Display replies */}
                        {comment.replies && comment.replies.length > 0 && (
                          <div className="ml-12 space-y-2 border-l-2 border-border pl-4">
                            {comment.replies.map((reply: Comment) => (
                              <div key={reply.id} className="flex gap-3">
                                <div className="w-8 h-8 rounded-full bg-secondary/10 flex items-center justify-center shrink-0">
                                  <span className="text-xs font-semibold text-secondary">
                                    {getAuthorInitials(reply.user_name)}
                                  </span>
                                </div>
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className="font-medium text-sm text-foreground">
                                      {reply.user_name}
                                    </span>
                                    <span className="text-xs text-muted-foreground">
                                      {formatTime(reply.created_at)}
                                    </span>
                                  </div>
                                  <p className="text-sm text-foreground/90">{reply.text}</p>
                                  <div className="flex items-center gap-3 mt-1">
                                    <button
                                      onClick={() => commentLikeMutation.mutate(reply.id)}
                                      disabled={commentLikeMutation.isPending}
                                      className={`flex items-center gap-1 text-xs ${
                                        reply.is_liked
                                          ? "text-secondary"
                                          : "text-muted-foreground hover:text-secondary"
                                      }`}
                                    >
                                      <Heart
                                        className={`w-3 h-3 ${reply.is_liked ? "fill-secondary" : ""}`}
                                      />
                                      <span>{reply.likes_count || 0}</span>
                                    </button>

                                    {user && user.user_id === reply.user_id && (
                                      <button
                                        onClick={() => {
                                          if (confirm("Are you sure you want to delete this reply?")) {
                                            deleteCommentMutation.mutate(reply.id);
                                          }
                                        }}
                                        disabled={deleteCommentMutation.isPending}
                                        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-destructive transition-colors"
                                      >
                                        <Trash2 className="w-3 h-3" />
                                        <span>Delete</span>
                                      </button>
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>

                <div className="p-4 border-t border-border">
                  {user ? (
                    <div className="space-y-2">
                      {replyingTo && (
                        <div className="flex items-center justify-between text-sm text-muted-foreground bg-secondary/10 rounded px-3 py-2">
                          <span>Replying to comment...</span>
                          <button
                            onClick={() => {
                              setReplyingTo(null);
                              setNewComment("");
                            }}
                            className="text-muted-foreground hover:text-foreground"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                      <div className="flex gap-3">
                        <div className="w-10 h-10 rounded-full bg-secondary/20 flex items-center justify-center shrink-0">
                          <span className="text-sm font-semibold text-secondary">
                            {getAuthorInitials(user.name)}
                          </span>
                        </div>
                        <div className="flex-1 flex gap-2">
                          <Textarea
                            placeholder={replyingTo ? "Write a reply..." : "Add a comment..."}
                            value={newComment}
                            onChange={(e) => setNewComment(e.target.value)}
                            className="min-h-[44px] max-h-24 resize-none"
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSubmitComment();
                              }
                            }}
                          />
                          <Button
                            variant="hero"
                            size="icon"
                            disabled={!newComment.trim()}
                            onClick={handleSubmitComment}
                          >
                            <Send className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-6">
                      <p className="text-muted-foreground mb-4">
                        Sign in to share your thoughts and connect with others
                      </p>
                      <div className="flex gap-3 justify-center">
                        <Button
                          variant="hero"
                          onClick={() => navigate('/login?redirect=' + encodeURIComponent(window.location.pathname))}
                        >
                          Sign In
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => navigate('/signup?redirect=' + encodeURIComponent(window.location.pathname))}
                        >
                          Create Account
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Share Sheet */}
        {shareSheetData && (
          <ShareSheet
            isOpen={showShareSheet}
            onClose={() => {
              setShowShareSheet(false);
              setShareSheetData(null);
            }}
            shareData={shareSheetData}
            onShare={handleShareComplete}
          />
        )}
      </div>
    </SwipeableDevotionalView>
  );

  // Wrap with admin sidebar if user is admin
  if (isAdmin) {
    return (
      <SidebarProvider>
        <div className="min-h-screen flex w-full bg-background">
          <AdminSidebar />
          <div className="flex-1 overflow-auto">
            {content}
          </div>
        </div>
      </SidebarProvider>
    );
  }

  return content;
};

export default Devotional;
