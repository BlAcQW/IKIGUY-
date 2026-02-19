/**
 * Today's Featured Devotional Component
 * Shows the featured devotional for today with full content preview
 * Mobile-first design for landing page
 */

import { motion } from "framer-motion";
import { Heart, MessageCircle, Bookmark, Share2, Clock, User, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";

const TodaysFeaturedDevotional = () => {
  const navigate = useNavigate();

  // Fetch latest published devotional
  const { data: devotionalData, isLoading } = useQuery({
    queryKey: ['featuredDevotional'],
    queryFn: async () => {
      try {
        const response = await apiClient.getDevotionals({
          status: 'published',
          page: 1,
          limit: 1,
          sort_by: 'published_at',
          sort_order: 'desc'
        });
        return response.items?.[0] || null;
      } catch (error) {
        console.error('Failed to fetch devotional:', error);
        return null;
      }
    }
  });

  // Transform API data to component format
  const devotional = devotionalData ? {
    id: devotionalData.id,
    title: devotionalData.title,
    content: getFirstParagraph(devotionalData.content),
    scripture: getScriptureBlock(devotionalData.content),
    author: {
      name: devotionalData.author_name || "FreshManna Team",
      avatar: devotionalData.author_avatar || null
    },
    category: devotionalData.categories?.[0] || "Faith",
    readingTime: calculateReadingTime(devotionalData.content),
    date: new Date().toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    }),
    stats: {
      likes: devotionalData.likes_count || 0,
      comments: devotionalData.comments_count || 0,
      shares: devotionalData.shares_count || 0
    },
    cover_image: devotionalData.cover_image_url || null
  } : null;

  // Loading state
  if (isLoading || !devotional) {
    return (
      <section className="py-8 md:py-16 bg-background">
        <div className="container mx-auto px-4">
          <div className="bg-card rounded-2xl shadow-elevated border border-border/50 overflow-hidden p-6">
            <div className="animate-pulse space-y-4">
              <div className="h-8 bg-muted rounded w-3/4"></div>
              <div className="h-4 bg-muted rounded w-full"></div>
              <div className="h-4 bg-muted rounded w-5/6"></div>
              <div className="h-32 bg-muted rounded w-full"></div>
            </div>
          </div>
        </div>
      </section>
    );
  }

  const handleReadMore = () => {
    if (devotional?.id) {
      navigate(`/devotional/${devotional.id}`);
    }
  };

  return (
    <section className="py-8 md:py-16 bg-background">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mb-6"
        >
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-serif text-2xl md:text-3xl font-bold text-foreground">
              Today's Devotional
            </h2>
            <span className="text-sm text-muted-foreground">{devotional.date}</span>
          </div>
          <p className="text-sm md:text-base text-muted-foreground">
            Start your day with fresh inspiration from the Holy Spirit
          </p>
        </motion.div>

        {/* Devotional Card */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="bg-card rounded-2xl shadow-elevated border border-border/50 overflow-hidden"
        >
          {/* Card Header */}
          <div className="px-4 md:px-6 py-4 border-b border-border/50">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <h3 className="font-serif text-xl md:text-2xl font-bold text-foreground mb-2 line-clamp-2">
                  {devotional.title}
                </h3>
                <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <User className="w-4 h-4" />
                    <span>{devotional.author.name}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <span>{devotional.readingTime} min read</span>
                  </div>
                  <span className="inline-block px-2 py-0.5 rounded-full bg-secondary/10 text-secondary text-xs font-medium">
                    {devotional.category}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Content Preview */}
          <div className="px-4 md:px-6 py-6">
            <div className="prose prose-sm md:prose-base max-w-none">
              <p className="text-foreground/90 leading-relaxed mb-4">
                {devotional.content}
              </p>

              {/* Scripture Block */}
              {devotional.scripture && (
                <div className="bg-secondary/5 border-l-4 border-secondary rounded-r-lg p-4 my-4">
                  <p className="font-serif text-base md:text-lg italic text-foreground/90 mb-2">
                    "{devotional.scripture.text}"
                  </p>
                  <p className="text-sm text-secondary font-medium">
                    — {devotional.scripture.reference}
                  </p>
                </div>
              )}
            </div>

            {/* Read More CTA - Mobile optimized */}
            <div className="mt-6">
              <Button
                onClick={handleReadMore}
                variant="default"
                size="lg"
                className="w-full md:w-auto gap-2"
              >
                Read Full Devotional
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Footer Engagement */}
          <div className="px-4 md:px-6 py-4 bg-muted/30 border-t border-border/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4 md:gap-6">
                <button
                  onClick={handleReadMore}
                  className="flex items-center gap-1.5 text-muted-foreground hover:text-secondary transition-colors group"
                >
                  <Heart className="w-5 h-5 group-hover:scale-110 transition-transform" />
                  <span className="text-sm font-medium">{devotional.stats.likes}</span>
                </button>
                <button
                  onClick={handleReadMore}
                  className="flex items-center gap-1.5 text-muted-foreground hover:text-accent transition-colors group"
                >
                  <MessageCircle className="w-5 h-5 group-hover:scale-110 transition-transform" />
                  <span className="text-sm font-medium">{devotional.stats.comments}</span>
                </button>
                <button
                  onClick={handleReadMore}
                  className="text-muted-foreground hover:text-secondary transition-colors"
                >
                  <Bookmark className="w-5 h-5" />
                </button>
              </div>
              <button
                onClick={handleReadMore}
                className="flex items-center gap-1.5 text-muted-foreground hover:text-accent transition-colors"
              >
                <Share2 className="w-5 h-5" />
                <span className="text-sm font-medium hidden md:inline">{devotional.stats.shares}</span>
              </button>
            </div>
          </div>

          {/* Sign Up Banner */}
          <div className="px-4 md:px-6 py-3 bg-secondary/5 border-t border-secondary/20">
            <p className="text-center text-sm text-foreground/80">
              <button
                onClick={handleReadMore}
                className="font-medium text-secondary hover:underline"
              >
                Sign up free
              </button>
              {" "}to save favorites, track your streak, and join the community
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

// Helper functions
function getFirstParagraph(content: any[]): string {
  if (!content || content.length === 0) return "Read today's devotional...";
  const firstPara = content.find((block: any) => block && block.type === 'paragraph');
  return firstPara?.text || "Read today's devotional...";
}

function getScriptureBlock(content: any[]): { text: string; reference: string } | null {
  if (!content || content.length === 0) return null;
  const scriptureBlock = content.find((block: any) => block && block.type === 'scripture');
  if (scriptureBlock) {
    return {
      text: scriptureBlock.text || "",
      reference: scriptureBlock.scripture_reference || ""
    };
  }
  return null;
}

function calculateReadingTime(content: any[]): number {
  if (!content || !Array.isArray(content) || content.length === 0) return 5;
  const totalWords = content.reduce((count: number, block: any) => {
    // Skip invalid blocks or blocks without text
    if (!block || typeof block !== 'object') return count;
    if (typeof block.text !== 'string' || !block.text) return count;

    return count + block.text.split(/\s+/).filter(word => word.length > 0).length;
  }, 0);
  return Math.max(1, Math.ceil(totalWords / 200)); // 200 words per minute
}

export default TodaysFeaturedDevotional;
