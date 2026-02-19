/**
 * Trending Devotionals Component
 * Shows popular devotionals this week with social proof
 * Mobile-first compact card design
 */

import { motion } from "framer-motion";
import { TrendingUp, Clock, Users, MessageCircle, Heart } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";

const TrendingDevotionals = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { toast } = useToast();

  // Fetch trending devotionals (most viewed/liked)
  const { data: devotionalsData, isLoading } = useQuery({
    queryKey: ['trendingDevotionals'],
    queryFn: async () => {
      try {
        const response = await apiClient.getDevotionals({
          status: 'published',
          page: 1,
          limit: 4,
          sort_by: 'views_count',
          sort_order: 'desc'
        });
        return response.items || [];
      } catch (error) {
        console.error('Failed to fetch trending devotionals:', error);
        return [];
      }
    }
  });

  // Transform API data to component format
  const trendingDevotionals = devotionalsData?.map((dev: any, index: number) => ({
    id: dev.id,
    title: dev.title,
    excerpt: getExcerpt(dev.content),
    category: dev.categories?.[0] || "Faith",
    readingTime: calculateReadingTime(dev.content),
    stats: {
      readers: dev.views_count || 0,
      likes: dev.likes_count || 0,
      comments: dev.comments_count || 0
    },
    is_liked: dev.is_liked || false,
    trending: index < 3 // First 3 are marked as "Hot"
  })) || [];

  // Like mutation with authentication check
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
              onClick={() => navigate('/auth?devotional=' + devotionalId)}
            >
              Sign In
            </Button>
          ),
        });
        throw new Error('Authentication required');
      }
      return await apiClient.likeDevotional(devotionalId);
    },
    onMutate: async (devotionalId) => {
      if (!user) return;

      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['trendingDevotionals'] });

      // Snapshot previous value
      const previousData = queryClient.getQueryData(['trendingDevotionals']);

      // Optimistically update the cache
      queryClient.setQueryData(['trendingDevotionals'], (old: any[]) =>
        old?.map(dev =>
          dev.id === devotionalId
            ? {
                ...dev,
                likes_count: dev.likes_count + (dev.is_liked ? -1 : 1),
                is_liked: !dev.is_liked
              }
            : dev
        )
      );

      return { previousData };
    },
    onError: (err: any, devotionalId, context) => {
      if (err.message === 'Authentication required') return;

      // Rollback on error
      queryClient.setQueryData(['trendingDevotionals'], context?.previousData);
      toast({
        title: "Error",
        description: "Failed to like devotional. Please try again.",
        variant: "destructive"
      });
    },
    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['devotionals'] });
      queryClient.invalidateQueries({ queryKey: ['devotional'] });
    }
  });

  // Loading state
  if (isLoading) {
    return (
      <section className="py-8 md:py-12 bg-background">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-card rounded-xl border border-border/50 p-4">
                <div className="animate-pulse space-y-3">
                  <div className="h-4 bg-muted rounded w-3/4"></div>
                  <div className="h-3 bg-muted rounded w-full"></div>
                  <div className="h-3 bg-muted rounded w-5/6"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  const handleDevotionalClick = (id: string) => {
    navigate(`/auth?devotional=${id}`);
  };

  return (
    <section className="py-8 md:py-12 bg-background">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mb-6"
        >
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-secondary" />
            <h2 className="font-serif text-xl md:text-2xl font-bold text-foreground">
              Trending This Week
            </h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Join thousands of believers reading these devotionals
          </p>
        </motion.div>

        {/* Trending Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {trendingDevotionals.map((devotional, index) => (
            <motion.button
              key={devotional.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => handleDevotionalClick(devotional.id)}
              className={cn(
                "bg-card rounded-xl border border-border/50 overflow-hidden",
                "transition-all duration-200 hover:shadow-lg hover:border-secondary/30",
                "text-left group"
              )}
            >
              <div className="p-4">
                {/* Header */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-serif text-base md:text-lg font-bold text-foreground mb-1 line-clamp-2 group-hover:text-secondary transition-colors">
                      {devotional.title}
                    </h3>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span className="inline-flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {devotional.readingTime} min
                      </span>
                      <span>•</span>
                      <span className="px-2 py-0.5 rounded-full bg-secondary/10 text-secondary font-medium">
                        {devotional.category}
                      </span>
                    </div>
                  </div>
                  {devotional.trending && (
                    <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-accent/10 text-accent">
                      <TrendingUp className="w-3 h-3" />
                      <span className="text-xs font-medium">Hot</span>
                    </div>
                  )}
                </div>

                {/* Excerpt */}
                <p className="text-sm text-foreground/80 line-clamp-2 mb-4">
                  {devotional.excerpt}
                </p>

                {/* Stats */}
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1.5">
                    <Users className="w-4 h-4" />
                    <span className="font-medium">{devotional.stats.readers}</span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      likeMutation.mutate(devotional.id);
                    }}
                    className={cn(
                      "flex items-center gap-1.5 transition-colors",
                      devotional.is_liked
                        ? "text-secondary"
                        : "hover:text-secondary"
                    )}
                  >
                    <Heart className={cn("w-4 h-4", devotional.is_liked && "fill-secondary")} />
                    <span>{devotional.stats.likes}</span>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/devotional/${devotional.id}#comments`);
                    }}
                    className="flex items-center gap-1.5 hover:text-accent transition-colors"
                  >
                    <MessageCircle className="w-4 h-4" />
                    <span>{devotional.stats.comments}</span>
                  </button>
                </div>
              </div>

              {/* Footer Gradient */}
              <div className="h-1 bg-gradient-to-r from-secondary/20 via-accent/20 to-secondary/20" />
            </motion.button>
          ))}
        </div>

        {/* View All CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-6 text-center"
        >
          <button
            onClick={() => navigate('/auth')}
            className="text-secondary font-medium hover:underline text-sm md:text-base"
          >
            Explore all devotionals →
          </button>
        </motion.div>
      </div>
    </section>
  );
};

// Helper functions
function getExcerpt(content: any[]): string {
  if (!content || content.length === 0) return "Read this devotional...";
  const firstPara = content.find((block: any) => block && block.type === 'paragraph');
  const text = firstPara?.text || "Read this devotional...";
  return text.length > 150 ? text.substring(0, 150) + "..." : text;
}

function calculateReadingTime(content: any[]): number {
  if (!content || !Array.isArray(content) || content.length === 0) return 4;
  const totalWords = content.reduce((count: number, block: any) => {
    // Skip invalid blocks or blocks without text
    if (!block || typeof block !== 'object') return count;
    if (typeof block.text !== 'string' || !block.text) return count;

    return count + block.text.split(/\s+/).filter(word => word.length > 0).length;
  }, 0);
  return Math.max(1, Math.ceil(totalWords / 200)); // 200 words per minute
}

export default TrendingDevotionals;
