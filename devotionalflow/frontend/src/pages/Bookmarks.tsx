/**
 * Bookmarks Page
 * Shows user's saved/bookmarked devotionals and scriptures
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Bookmark, Loader2, LogIn, BookOpen, MessageCircle } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { AppHeader } from '@/components/navigation/AppHeader';
import { useAuth } from '@/contexts/AuthContext';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { getImageUrl } from '@/lib/image-utils';
import { SearchModal } from '@/components/search/SearchModal';
import { SwipeableListItem } from '@/components/mobile/SwipeableListItem';
import { useToast } from '@/hooks/use-toast';
import { logger } from '@/lib/logger';

interface BookmarkedDevotional {
  id: string;
  title: string;
  excerpt: string;
  cover_image_url?: string;
  published_at: string;
  reading_time_minutes: number;
  categories: string[];
}

interface BookmarkedScripture {
  id: string;
  reference: string;
  verse_text: string;
  translation: string;
  devotional_id?: string;
  devotional_title?: string;
  created_at: string;
}

export default function Bookmarks() {
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'devotionals' | 'scriptures'>('devotionals');
  const [showSearchModal, setShowSearchModal] = useState(false);

  // Fetch bookmarked devotionals
  const { data: devotionals, isLoading: isLoadingDevotionals } = useQuery({
    queryKey: ['bookmarked-devotionals'],
    queryFn: async () => {
      try {
        const response = await apiClient.getBookmarkedDevotionals();
        // Backend returns array directly, not wrapped in { items: [] }
        return (Array.isArray(response) ? response : []) as BookmarkedDevotional[];
      } catch (error) {
        logger.error('Failed to fetch bookmarked devotionals:', error);
        return [];
      }
    },
    enabled: !!user, // Only fetch if user is authenticated
  });

  // Fetch bookmarked scriptures
  const { data: scriptures, isLoading: isLoadingScriptures } = useQuery({
    queryKey: ['bookmarked-scriptures'],
    queryFn: async () => {
      try {
        const response = await apiClient.getBookmarkedScriptures();
        // Backend returns array directly, not wrapped in { items: [] }
        return (Array.isArray(response) ? response : []) as BookmarkedScripture[];
      } catch (error) {
        logger.error('Failed to fetch bookmarked scriptures:', error);
        return [];
      }
    },
    enabled: !!user, // Only fetch if user is authenticated
  });

  useEffect(() => {
    document.title = 'Saved Devotionals - Fresh Manna';
  }, []);

  // Unbookmark devotional mutation
  const unbookmarkDevotionalMutation = useMutation({
    mutationFn: async (devotionalId: string) => {
      return await apiClient.bookmarkDevotional(devotionalId); // Toggles bookmark state
    },
    onMutate: async (devotionalId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['bookmarked-devotionals'] });
      
      // Snapshot previous value
      const previousDevotionals = queryClient.getQueryData<BookmarkedDevotional[]>(['bookmarked-devotionals']);
      
      // Optimistically update - remove the devotional
      queryClient.setQueryData<BookmarkedDevotional[]>(['bookmarked-devotionals'], (old) =>
        old?.filter(d => d.id !== devotionalId) || []
      );
      
      return { previousDevotionals };
    },
    onError: (err, devotionalId, context) => {
      // Rollback on error
      if (context?.previousDevotionals) {
        queryClient.setQueryData(['bookmarked-devotionals'], context.previousDevotionals);
      }
      toast({
        title: "Error",
        description: "Failed to remove bookmark. Please try again.",
        variant: "destructive",
      });
    },
    onSuccess: () => {
      // Invalidate to ensure consistency
      queryClient.invalidateQueries({ queryKey: ['bookmarked-devotionals'] });
      queryClient.invalidateQueries({ queryKey: ['bookmarks'] });
      toast({
        title: "Removed",
        description: "Devotional removed from saved items",
      });
    },
  });

  // Unbookmark scripture mutation
  const unbookmarkScriptureMutation = useMutation({
    mutationFn: async (scriptureId: string) => {
      return await apiClient.unbookmarkScripture(scriptureId);
    },
    onMutate: async (scriptureId) => {
      await queryClient.cancelQueries({ queryKey: ['bookmarked-scriptures'] });
      const previousScriptures = queryClient.getQueryData<BookmarkedScripture[]>(['bookmarked-scriptures']);
      
      queryClient.setQueryData<BookmarkedScripture[]>(['bookmarked-scriptures'], (old) =>
        old?.filter(s => s.id !== scriptureId) || []
      );
      
      return { previousScriptures };
    },
    onError: (err, scriptureId, context) => {
      if (context?.previousScriptures) {
        queryClient.setQueryData(['bookmarked-scriptures'], context.previousScriptures);
      }
      toast({
        title: "Error",
        description: "Failed to remove bookmark. Please try again.",
        variant: "destructive",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookmarked-scriptures'] });
      toast({
        title: "Removed",
        description: "Scripture removed from saved items",
      });
    },
  });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const totalCount = (devotionals?.length || 0) + (scriptures?.length || 0);
  const isLoading = isLoadingDevotionals || isLoadingScriptures;

  // Show loading state while checking auth
  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center pb-20">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-secondary" />
          <p className="text-muted-foreground">Loading your saved items...</p>
        </div>
      </div>
    );
  }

  // Show sign-in prompt if not authenticated
  if (!user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center pb-20">
        <div className="text-center max-w-md px-4">
          <LogIn className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
          <h2 className="font-serif text-2xl font-bold mb-2">Sign In to View Saved</h2>
          <p className="text-muted-foreground mb-6">
            Sign in to save devotionals and access them anytime, anywhere.
          </p>
          <div className="flex gap-3 justify-center">
            <Button
              variant="hero"
              onClick={() => navigate('/login?redirect=/bookmarks')}
            >
              Sign In
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate('/signup?redirect=/bookmarks')}
            >
              Create Account
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20">
      {/* Header */}
      <AppHeader
        title="Saved"
        subtitle={
          totalCount > 0
            ? `${totalCount} saved item${totalCount !== 1 ? 's' : ''}`
            : 'No saved items yet'
        }
        showSearch={true}
        onSearch={() => setShowSearchModal(true)}
      />

      {/* Content */}
      <main className="container mx-auto px-4 py-6">
        {totalCount === 0 ? (
          <div className="text-center py-16">
            <Bookmark className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
            <h2 className="font-serif text-xl font-bold mb-2">No Saved Items</h2>
            <p className="text-muted-foreground mb-6">
              Start saving devotionals and scriptures to access them later
            </p>
            <div className="flex gap-3 justify-center">
              <Button
                variant="outline"
                onClick={() => navigate('/feed')}
              >
                Discover Devotionals
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate('/discussions')}
              >
                Join Discussions
              </Button>
            </div>
          </div>
        ) : (
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'devotionals' | 'scriptures')} className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-6">
              <TabsTrigger value="devotionals" className="gap-2">
                <BookOpen className="w-4 h-4" />
                Devotionals ({devotionals?.length || 0})
              </TabsTrigger>
              <TabsTrigger value="scriptures" className="gap-2">
                <Bookmark className="w-4 h-4" />
                Scriptures ({scriptures?.length || 0})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="devotionals" className="space-y-4">
              {!devotionals || devotionals.length === 0 ? (
                <div className="text-center py-12">
                  <BookOpen className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground mb-4">No saved devotionals yet</p>
                  <Button variant="outline" onClick={() => navigate('/feed')}>
                    Browse Devotionals
                  </Button>
                </div>
              ) : (
                devotionals.map((devotional, index) => (
                  <motion.div
                    key={devotional.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                  >
                    <SwipeableListItem
                      onDelete={() => unbookmarkDevotionalMutation.mutate(devotional.id)}
                      onClick={() => navigate(`/devotional/${devotional.id}`)}
                      className="bg-card rounded-2xl overflow-hidden border border-border hover:shadow-lg transition-shadow"
                    >
                      <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 p-3 sm:p-4">
                        {devotional.cover_image_url && (
                          <div className="w-full sm:w-24 h-36 sm:h-24 rounded-xl overflow-hidden flex-shrink-0">
                            <img
                              src={getImageUrl(devotional.cover_image_url) || ''}
                              alt={devotional.title}
                              className="w-full h-full object-cover"
                            />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          {devotional.categories && devotional.categories[0] && (
                            <span className="inline-block px-2 py-1 rounded-full bg-secondary/10 text-secondary text-xs font-medium mb-2">
                              {devotional.categories[0]}
                            </span>
                          )}
                          <h3 className="font-serif text-base sm:text-lg font-bold text-foreground mb-1 sm:mb-2 line-clamp-2">
                            {devotional.title}
                          </h3>
                          <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                            {devotional.excerpt}
                          </p>
                          <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs text-muted-foreground">
                            <span>{formatDate(devotional.published_at)}</span>
                            <span>•</span>
                            <span>{devotional.reading_time_minutes} min read</span>
                          </div>
                        </div>
                      </div>
                    </SwipeableListItem>
                  </motion.div>
                ))
              )}
            </TabsContent>

            <TabsContent value="scriptures" className="space-y-4">
              {!scriptures || scriptures.length === 0 ? (
                <div className="text-center py-12">
                  <Bookmark className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground mb-4">No saved scriptures yet</p>
                  <p className="text-sm text-muted-foreground mb-4">
                    Click the bookmark icon on any scripture reference in a devotional to save it
                  </p>
                  <Button variant="outline" onClick={() => navigate('/feed')}>
                    Read Devotionals
                  </Button>
                </div>
              ) : (
                scriptures.map((scripture, index) => (
                  <motion.div
                    key={scripture.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                  >
                    <SwipeableListItem
                      onDelete={() => unbookmarkScriptureMutation.mutate(scripture.id)}
                      className="bg-card rounded-2xl border border-border hover:shadow-lg transition-shadow"
                    >
                      <div className="p-4 sm:p-6">
                        <div className="bg-secondary/5 border-l-4 border-secondary rounded-r-xl p-3 sm:p-4 mb-4">
                          <p className="font-serif text-base sm:text-lg italic text-foreground/90 mb-2">
                            "{scripture.verse_text}"
                          </p>
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="text-sm text-secondary font-medium flex items-center gap-2">
                              <BookOpen className="w-4 h-4 flex-shrink-0" />
                              <span className="break-words">{scripture.reference}</span>
                              {scripture.translation && (
                                <span className="text-xs text-muted-foreground">
                                  ({scripture.translation})
                                </span>
                              )}
                            </p>
                          </div>
                        </div>
                        {scripture.devotional_id && scripture.devotional_title && (
                          <div className="mb-3 p-3 bg-muted/30 rounded-lg">
                            <p className="text-xs text-muted-foreground mb-1">From Devotional</p>
                            <button
                              onClick={() => navigate(`/devotional/${scripture.devotional_id}`)}
                              className="text-sm font-medium text-secondary hover:underline"
                            >
                              {scripture.devotional_title}
                            </button>
                          </div>
                        )}
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span>Saved {formatDate(scripture.created_at)}</span>
                        </div>
                      </div>
                    </SwipeableListItem>
                  </motion.div>
                ))
              )}
            </TabsContent>
          </Tabs>
        )}

        {/* Quick Navigation */}
        {totalCount > 0 && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-card rounded-xl border border-border p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => navigate('/feed')}
            >
              <BookOpen className="w-6 h-6 text-secondary mb-2" />
              <h3 className="font-medium text-foreground mb-1">Daily Devotionals</h3>
              <p className="text-sm text-muted-foreground">Read today's devotional</p>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25 }}
              className="bg-card rounded-xl border border-border p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => navigate('/discussions')}
            >
              <MessageCircle className="w-6 h-6 text-secondary mb-2" />
              <h3 className="font-medium text-foreground mb-1">Group Discussions</h3>
              <p className="text-sm text-muted-foreground">Join conversations</p>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-card rounded-xl border border-border p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => navigate('/today')}
            >
              <Bookmark className="w-6 h-6 text-secondary mb-2" />
              <h3 className="font-medium text-foreground mb-1">Today's Reading</h3>
              <p className="text-sm text-muted-foreground">Start your daily reading</p>
            </motion.div>
          </div>
        )}
      </main>

      {/* Bottom Navigation */}

      {/* Search Modal */}
      <SearchModal
        isOpen={showSearchModal}
        onClose={() => setShowSearchModal(false)}
      />
    </div>
  );
}
