import { useState, useMemo, useCallback } from "react";
import { motion } from "framer-motion";
import {
  BookOpen,
  Heart,
  MessageCircle,
  Bookmark,
  Share2,
  Play,
  ChevronRight,
  Sparkles,
  CheckCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { devotionalDB } from '@/lib/db';
import { useOfflineSync } from '@/hooks/useOfflineSync';
import { useAuth } from '@/contexts/AuthContext';
import { PullToRefresh } from '@/components/mobile/PullToRefresh';
import { FeedSkeleton } from '@/components/loading/DevotionalCardSkeleton';
import { useToast } from '@/hooks/use-toast';
import { MainNavigation } from "@/components/navigation/MainNavigation";
import { getImageUrl } from '@/lib/image-utils';

interface Devotional {
  id: string;
  title: string;
  content: any[];
  excerpt: string;
  author_id: string;
  author_name: string;
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

const Feed = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isOnline, queueAction } = useOfflineSync();
  const { user } = useAuth();
  const { toast } = useToast();

  const [searchQuery, setSearchQuery] = useState("");

  // Fetch today's devotional separately
  const { data: todayDevotional } = useQuery({
    queryKey: ['today-devotional'],
    queryFn: async () => {
      try {
        return await apiClient.getTodaysDevotional();
      } catch (error) {
        // If no devotional for today (404), return null
        return null;
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !searchQuery, // Only fetch when not searching
  });

  // Fetch recent devotionals with offline fallback
  const { data: devotionals, isLoading, refetch } = useQuery({
    queryKey: ['devotionals', searchQuery],
    queryFn: async () => {
      try {
        const params = searchQuery ? { search: searchQuery } : {};
        const response = await apiClient.getDevotionals(params);

        // Cache devotionals for offline
        if (response.items && Array.isArray(response.items)) {
          for (const devotional of response.items) {
            await devotionalDB.cacheDevotional(devotional);
          }
          // Clean up old devotionals (keep last 100)
          await devotionalDB.clearOldDevotionals(100);
        }

        return response.items || [];
      } catch (error) {
        if (!isOnline) {
          // Fallback to cached data
          const cached = await devotionalDB.getCachedDevotionals();
          return cached.reverse(); // Most recent first
        }
        throw error;
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Like mutation with optimistic updates and authentication check
  const likeMutation = useMutation({
    mutationFn: async (devotionalId: string) => {
      if (!user) {
        toast({
          title: "Sign in required",
          description: "Please sign in to like devotionals",
          action: (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/auth?redirect=' + encodeURIComponent(window.location.pathname))}
            >
              Sign In
            </Button>
          ),
        });
        throw new Error('Authentication required');
      }
      if (!isOnline) {
        await queueAction({ action: 'like', target_id: devotionalId });
        return;
      }
      return await apiClient.likeDevotional(devotionalId);
    },
    onMutate: async (devotionalId) => {
      if (!user) return; // Skip optimistic update if not authenticated

      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['devotionals'] });

      // Snapshot previous value
      const previousData = queryClient.getQueryData(['devotionals']);

      // Optimistically update
      queryClient.setQueryData(['devotionals'], (old: any[]) =>
        old?.map(d =>
          d.id === devotionalId
            ? { ...d, likes_count: d.likes_count + (d.is_liked ? -1 : 1), is_liked: !d.is_liked }
            : d
        )
      );

      return { previousData };
    },
    onError: (err: any, devotionalId, context) => {
      if (err.message === 'Authentication required') return; // Don't rollback or show error for auth issues

      // Rollback on error
      queryClient.setQueryData(['devotionals'], context?.previousData);
      toast({
        title: "Error",
        description: "Failed to like devotional. Please try again.",
        variant: "destructive"
      });
    },
    onSuccess: () => {
      // Invalidate all queries that might show devotionals
      queryClient.invalidateQueries({ queryKey: ['trendingDevotionals'] });
      queryClient.invalidateQueries({ queryKey: ['devotional'] });

      if (!isOnline) {
        toast({
          title: "Queued",
          description: "Like will sync when you're back online"
        });
      }
    }
  });

  // Bookmark mutation with optimistic updates and authentication check
  const bookmarkMutation = useMutation({
    mutationFn: async (devotionalId: string) => {
      if (!user) {
        toast({
          title: "Sign in required",
          description: "Please sign in to bookmark devotionals",
          action: (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/auth?redirect=' + encodeURIComponent(window.location.pathname))}
            >
              Sign In
            </Button>
          ),
        });
        throw new Error('Authentication required');
      }
      if (!isOnline) {
        await queueAction({ action: 'bookmark', target_id: devotionalId });
        return;
      }
      return await apiClient.bookmarkDevotional(devotionalId);
    },
    onMutate: async (devotionalId) => {
      if (!user) return; // Skip optimistic update if not authenticated

      await queryClient.cancelQueries({ queryKey: ['devotionals'] });
      const previousData = queryClient.getQueryData(['devotionals']);

      queryClient.setQueryData(['devotionals'], (old: any[]) =>
        old?.map(d =>
          d.id === devotionalId
            ? { ...d, is_bookmarked: !d.is_bookmarked }
            : d
        )
      );

      return { previousData };
    },
    onError: (err: any, devotionalId, context) => {
      if (err.message === 'Authentication required') return; // Don't rollback or show error for auth issues

      queryClient.setQueryData(['devotionals'], context?.previousData);
      toast({
        title: "Error",
        description: "Failed to bookmark. Please try again.",
        variant: "destructive"
      });
    },
    onSuccess: (data, devotionalId) => {
      // Invalidate queries to refresh bookmarks list
      queryClient.invalidateQueries({ queryKey: ['bookmarked-devotionals'] });
      queryClient.invalidateQueries({ queryKey: ['bookmarks'] }); // For Profile page

      if (!isOnline) {
        toast({
          title: "Queued",
          description: "Bookmark will sync when you're back online"
        });
      }
    }
  });

  const handleRefresh = async () => {
    await refetch();
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Query will automatically refetch when searchQuery changes
  };

  const formatDate = useCallback((dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

    if (diffInDays === 0) return "Today";
    if (diffInDays === 1) return "Yesterday";
    if (diffInDays < 7) return `${diffInDays} days ago`;

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }, []);

  const getAuthorInitials = useCallback((name: string | undefined) => {
    if (!name || typeof name !== 'string') return 'FM';  // Default: FreshManna
    return name
      .split(' ')
      .filter(n => n.length > 0)
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) || 'FM';
  }, []);

  // If searching or no today's devotional, show all recent devotionals
  // Otherwise, filter out today's devotional from recent list
  const recentDevotionals = useMemo(() => {
    return todayDevotional && !searchQuery
      ? devotionals?.filter(d => d.id !== todayDevotional.id) || []
      : devotionals || [];
  }, [todayDevotional, searchQuery, devotionals]);

  return (
    <div className="min-h-screen bg-background">
      <MainNavigation />

      <PullToRefresh onRefresh={handleRefresh}>
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-3xl mx-auto">
            {isLoading ? (
              <FeedSkeleton count={4} />
            ) : !devotionals || devotionals.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-12"
              >
                <BookOpen className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                <h2 className="font-serif text-2xl font-bold text-foreground mb-2">
                  No devotionals found
                </h2>
                <p className="text-muted-foreground mb-6">
                  {searchQuery ? "Try a different search" : "Check back later for new content"}
                </p>
                {searchQuery && (
                  <Button onClick={() => setSearchQuery("")} variant="outline">
                    Clear Search
                  </Button>
                )}
              </motion.div>
            ) : (
              <>
                {/* Today's Devotional - Only show if not searching */}
                {todayDevotional && !searchQuery && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="mb-12"
                  >
                    <div className="flex items-center gap-2 mb-4">
                      <Sparkles className="w-5 h-5 text-secondary" />
                      <span className="text-sm font-medium text-secondary">
                        Today's Devotional
                      </span>
                    </div>

                    <article
                      className="bg-card rounded-3xl border border-border shadow-soft overflow-hidden cursor-pointer hover:shadow-elevated transition-shadow"
                      onClick={() => navigate(`/devotional/${todayDevotional.id}`)}
                    >
                      <div className="p-6 md:p-8">
                        {/* Meta */}
                        <div className="flex items-center gap-3 mb-4">
                          <div className="w-10 h-10 rounded-full bg-secondary/20 flex items-center justify-center">
                            <span className="font-semibold text-secondary text-sm">
                              {getAuthorInitials(todayDevotional.author_name)}
                            </span>
                          </div>
                          <div>
                            <p className="font-medium text-foreground">
                              {todayDevotional.author_name}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              {formatDate(todayDevotional.published_at)} · {todayDevotional.reading_time_minutes} min read
                            </p>
                          </div>
                        </div>

                        {/* Content */}
                        {todayDevotional.categories && todayDevotional.categories[0] && (
                          <span className="inline-block px-3 py-1 rounded-full bg-secondary/10 text-secondary text-xs font-medium mb-3">
                            {todayDevotional.categories[0]}
                          </span>
                        )}
                        <h2 className="font-serif text-2xl md:text-3xl font-bold text-foreground mb-3">
                          {todayDevotional.title}
                        </h2>
                        <p className="text-muted-foreground leading-relaxed mb-4">
                          {todayDevotional.excerpt}
                        </p>

                        {/* Scripture Tag - extract from content if available */}
                        {todayDevotional.content?.[0]?.scripture && (
                          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-secondary/5 rounded-lg text-sm text-secondary">
                            <BookOpen className="w-4 h-4" />
                            {todayDevotional.content[0].scripture}
                          </div>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="px-6 md:px-8 py-4 bg-muted/30 border-t border-border flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              likeMutation.mutate(todayDevotional.id);
                            }}
                            aria-label={todayDevotional.is_liked ? "Unlike devotional" : "Like devotional"}
                            className={`flex items-center gap-1.5 transition-colors ${
                              todayDevotional.is_liked
                                ? "text-secondary"
                                : "text-muted-foreground hover:text-secondary"
                            }`}
                          >
                            <Heart
                              className={`w-5 h-5 ${todayDevotional.is_liked ? "fill-secondary" : ""}`}
                            />
                            <span className="text-sm font-medium">
                              {todayDevotional.likes_count}
                            </span>
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/devotional/${todayDevotional.id}#comments`);
                            }}
                            className="flex items-center gap-1.5 text-muted-foreground hover:text-accent transition-colors"
                          >
                            <MessageCircle className="w-5 h-5" />
                            <span className="text-sm font-medium">
                              {todayDevotional.comments_count}
                            </span>
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              bookmarkMutation.mutate(todayDevotional.id);
                            }}
                            aria-label={todayDevotional.is_bookmarked ? "Remove bookmark" : "Bookmark devotional"}
                            className={`transition-colors ${
                              todayDevotional.is_bookmarked
                                ? "text-secondary"
                                : "text-muted-foreground hover:text-secondary"
                            }`}
                          >
                            <Bookmark
                              className={`w-5 h-5 ${
                                todayDevotional.is_bookmarked ? "fill-secondary" : ""
                              }`}
                            />
                          </button>
                        </div>
                        <div className="flex items-center gap-2">
                          {todayDevotional.audio_url && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/devotional/${todayDevotional.id}?autoplay=true`);
                              }}
                            >
                              <Play className="w-4 h-4 mr-1.5" />
                              Listen
                            </Button>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              // Share functionality - will implement with Web Share API
                              if (navigator.share) {
                                navigator.share({
                                  title: todayDevotional.title,
                                  text: todayDevotional.excerpt,
                                  url: window.location.origin + `/devotional/${todayDevotional.id}`
                                });
                              }
                            }}
                            aria-label="Share devotional"
                            className="text-muted-foreground hover:text-accent transition-colors"
                          >
                            <Share2 className="w-5 h-5" />
                          </button>
                        </div>
                      </div>
                    </article>
                  </motion.div>
                )}

                {/* Recent Devotionals */}
                {recentDevotionals.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.1 }}
                  >
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="font-serif text-xl font-bold text-foreground">
                        {searchQuery ? "Search Results" : todayDevotional ? "Recent Devotionals" : "Latest Devotionals"}
                      </h2>
                      {!searchQuery && (
                        <Button variant="ghost" size="sm" className="gap-1">
                          View All
                          <ChevronRight className="w-4 h-4" />
                        </Button>
                      )}
                    </div>

                    <div className="space-y-4">
                      {recentDevotionals.map((devotional, index) => (
                        <motion.article
                          key={devotional.id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.3, delay: index * 0.1 }}
                          onClick={() => navigate(`/devotional/${devotional.id}`)}
                          className="flex items-center gap-4 p-4 bg-card rounded-2xl border border-border hover:shadow-soft transition-all cursor-pointer group"
                        >
                          {devotional.cover_image_url ? (
                            <div className="w-20 h-20 rounded-xl overflow-hidden shrink-0">
                              <img
                                src={getImageUrl(devotional.cover_image_url) || ''}
                                alt={devotional.title}
                                className="w-full h-full object-cover"
                              />
                            </div>
                          ) : (
                            <div className="w-12 h-12 rounded-xl bg-secondary/10 flex items-center justify-center shrink-0">
                              <span className="font-semibold text-secondary">
                                {getAuthorInitials(devotional.author_name)}
                              </span>
                            </div>
                          )}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              {devotional.categories && devotional.categories[0] && (
                                <span className="text-xs px-2 py-0.5 bg-muted rounded-full text-muted-foreground">
                                  {devotional.categories[0]}
                                </span>
                              )}
                              <span className="text-xs text-muted-foreground">
                                {formatDate(devotional.published_at)}
                              </span>
                              {devotional.is_read && (
                                <span className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900 rounded-full text-green-700 dark:text-green-300 flex items-center gap-1">
                                  <CheckCircle className="w-3 h-3" />
                                  Read
                                </span>
                              )}
                            </div>
                            <h3 className="font-medium text-foreground truncate group-hover:text-secondary transition-colors">
                              {devotional.title}
                            </h3>
                            <p className="text-sm text-muted-foreground">
                              by {devotional.author_name}
                            </p>
                          </div>
                          <div className="flex items-center gap-1.5 text-muted-foreground">
                            <Heart className="w-4 h-4" />
                            <span className="text-sm">{devotional.likes_count}</span>
                          </div>
                        </motion.article>
                      ))}
                    </div>
                  </motion.div>
                )}
              </>
            )}
          </div>
        </main>
      </PullToRefresh>
    </div>
  );
};

export default Feed;
