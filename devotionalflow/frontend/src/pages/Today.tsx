/**
 * Today Page
 * Shows today's devotional - the main landing page for authenticated users
 */

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Loader2, Calendar, Share2 } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { useState } from 'react';
import { ShareSheet } from '@/components/social/ShareSheet';
import { ShareData } from '@/lib/share';
import { AppHeader } from '@/components/navigation/AppHeader';
import { BottomNav } from '@/components/navigation/BottomNav';
import { getImageUrl } from '@/lib/image-utils';
import { SearchModal } from '@/components/search/SearchModal';

interface TodaysDevotional {
  id: string;
  title: string;
  excerpt: string;
  cover_image_url?: string;
  published_at: string;
  reading_time_minutes: number;
  categories: string[];
}

export default function Today() {
  const navigate = useNavigate();
  const [showShareSheet, setShowShareSheet] = useState(false);
  const [shareData, setShareData] = useState<ShareData | null>(null);
  const [showSearchModal, setShowSearchModal] = useState(false);

  // Fetch today's devotional with fallback to most recent
  const { data: devotional, isLoading, error } = useQuery({
    queryKey: ['today-devotional'],
    queryFn: async () => {
      try {
        const response = await apiClient.getTodaysDevotional();
        return response as TodaysDevotional;
      } catch (err: any) {
        // If no devotional specifically for today (404), show the most recent one
        if (err?.response?.status === 404) {
          try {
            const recent = await apiClient.getDevotionals({ page: 1, page_size: 1 });
            if (recent.items && recent.items.length > 0) {
              return recent.items[0] as TodaysDevotional;
            }
          } catch (fallbackErr) {
            console.error('Failed to fetch fallback devotional:', fallbackErr);
          }
        }
        throw err;
      }
    },
    retry: (failureCount, error: any) => {
      // Don't retry on 404 - we handle it in queryFn
      if (error?.response?.status === 404) {
        return false;
      }
      // Retry other errors up to 2 times
      return failureCount < 2;
    },
  });

  useEffect(() => {
    document.title = "Today's Devotional - Fresh Manna";
  }, []);

  const handleShare = () => {
    if (devotional) {
      setShareData({
        title: devotional.title,
        text: devotional.excerpt,
        url: `${window.location.origin}/devotional/${devotional.id}`,
        imageUrl: devotional.cover_image_url,
      });
      setShowShareSheet(true);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <AppHeader
          title="Today"
          subtitle={new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
          showSearch={true}
          showNotifications={false}
          onSearch={() => setShowSearchModal(true)}
        />
        <div className="flex items-center justify-center min-h-[calc(100vh-14rem)]">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-secondary" />
            <p className="text-muted-foreground">Loading today's devotional...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !devotional) {
    return (
      <div className="min-h-screen bg-background">
        <AppHeader
          title="Today"
          subtitle={new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
          showSearch={true}
          showNotifications={false}
          onSearch={() => setShowSearchModal(true)}
        />
        <div className="flex items-center justify-center min-h-[calc(100vh-14rem)] px-4">
          <div className="text-center max-w-md">
            <Calendar className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
            <h2 className="font-serif text-2xl font-bold mb-2">No Devotional Today</h2>
            <p className="text-muted-foreground mb-6">
              {error
                ? 'Failed to load today\'s devotional. Please try again later.'
                : 'There\'s no devotional scheduled for today. Check back tomorrow!'}
            </p>
            <Button
              variant="outline"
              onClick={() => navigate('/feed')}
            >
              Browse All Devotionals
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <AppHeader
        title="Today"
        subtitle={formatDate(devotional.published_at)}
        showSearch={true}
        showNotifications={false}
        onSearch={() => setShowSearchModal(true)}
      />

      {/* Content */}
      <main className="container mx-auto px-4 py-6 pb-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Cover Image */}
          {devotional.cover_image_url && (
            <div
              className="relative w-full aspect-video rounded-2xl overflow-hidden mb-6 cursor-pointer group"
              onClick={() => navigate(`/devotional/${devotional.id}`)}
            >
              <img
                src={getImageUrl(devotional.cover_image_url) || ''}
                alt={devotional.title}
                className="w-full h-full object-cover transition-transform group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/0 to-black/0" />
              {devotional.categories && devotional.categories[0] && (
                <span className="absolute top-4 left-4 px-3 py-1 rounded-full bg-white/90 backdrop-blur-sm text-sm font-medium text-foreground">
                  {devotional.categories[0]}
                </span>
              )}
            </div>
          )}

          {/* Title & Meta */}
          <div className="mb-6">
            <h2
              className="font-serif text-3xl md:text-4xl font-bold text-foreground mb-3 leading-tight cursor-pointer hover:text-secondary transition-colors"
              onClick={() => navigate(`/devotional/${devotional.id}`)}
            >
              {devotional.title}
            </h2>
            <p className="text-sm text-muted-foreground">
              {devotional.reading_time_minutes} min read
            </p>
          </div>

          {/* Excerpt */}
          <p className="text-lg text-foreground/90 leading-relaxed mb-8">
            {devotional.excerpt}
          </p>

          {/* Actions */}
          <div className="flex gap-3">
            <Button
              variant="hero"
              className="flex-1"
              onClick={() => navigate(`/devotional/${devotional.id}`)}
            >
              Read Today's Devotional
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={handleShare}
            >
              <Share2 className="w-5 h-5" />
            </Button>
          </div>

          {/* Inspiration Quote */}
          <div className="mt-12 p-6 bg-secondary/5 rounded-2xl border border-secondary/10">
            <p className="text-center italic text-foreground/80">
              "Start your day with Holy Spirit inspiration"
            </p>
          </div>
        </motion.div>
      </main>

      {/* Bottom Navigation */}
      <BottomNav />

      {/* Share Sheet */}
      {shareData && (
        <ShareSheet
          isOpen={showShareSheet}
          onClose={() => setShowShareSheet(false)}
          shareData={shareData}
        />
      )}

      {/* Search Modal */}
      <SearchModal
        isOpen={showSearchModal}
        onClose={() => setShowSearchModal(false)}
      />
    </div>
  );
}
