/**
 * Discussions Page
 * Shows group discussions and community conversations
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { MessageCircle, Users, Plus, Search, BookOpen, Heart, Clock } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { logger } from '@/lib/logger';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AppHeader } from '@/components/navigation/AppHeader';
import { useAuth } from '@/contexts/AuthContext';
import { MainNavigation } from '@/components/navigation/MainNavigation';

interface Discussion {
  id: string;
  title: string;
  description: string;
  devotional_id?: string;
  devotional_title?: string;
  scripture_reference?: string;
  author_id: string;
  author_name: string;
  author_avatar?: string;
  participants_count: number;
  messages_count: number;
  last_activity_at: string;
  created_at: string;
  category?: string;
}

export default function Discussions() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch discussions
  const { data: discussionsData, isLoading } = useQuery({
    queryKey: ['discussions', searchQuery],
    queryFn: async () => {
      try {
        const response = await apiClient.client.get('/discussions', {
          params: {
            search: searchQuery || undefined,
            page: 1,
            page_size: 50,
          },
        });
        return response.data.items as Discussion[];
      } catch (error) {
        logger.error('Failed to fetch discussions:', error);
        return [];
      }
    },
  });

  const discussions = discussionsData || [];

  const formatTime = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getAuthorInitials = (name: string | undefined) => {
    if (!name || typeof name !== 'string') return 'U';
    return name
      .split(' ')
      .filter(n => n.length > 0)
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) || 'U';
  };

  return (
    <div className="min-h-screen bg-background">
      <MainNavigation />

      <div className="container mx-auto px-4 py-6 pb-20">
        {/* Header Section */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="font-serif text-3xl font-bold text-foreground mb-2">
                Group Discussions
              </h1>
              <p className="text-muted-foreground">
                Connect with others, share insights, and grow together
              </p>
            </div>
            {user && (
              <Button
                onClick={() => navigate('/discussions/new')}
                className="gap-2"
              >
                <Plus className="w-4 h-4" />
                New Discussion
              </Button>
            )}
          </div>

          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search discussions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Discussions List */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-4 border-secondary border-t-transparent rounded-full animate-spin" />
            <p className="mt-4 text-muted-foreground">Loading discussions...</p>
          </div>
        ) : !discussions || discussions.length === 0 ? (
          <div className="text-center py-16">
            <MessageCircle className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
            <h2 className="font-serif text-xl font-bold mb-2">No Discussions Yet</h2>
            <p className="text-muted-foreground mb-6">
              {searchQuery ? 'Try a different search' : 'Be the first to start a discussion!'}
            </p>
            {user && (
              <Button onClick={() => navigate('/discussions/new')} className="gap-2">
                <Plus className="w-4 h-4" />
                Start Discussion
              </Button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {discussions.map((discussion, index) => (
              <motion.div
                key={discussion.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className="bg-card rounded-2xl border border-border hover:shadow-lg transition-all cursor-pointer"
                onClick={() => navigate(`/discussions/${discussion.id}`)}
              >
                <div className="p-6">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {discussion.category && (
                          <span className="px-2 py-1 rounded-full bg-secondary/10 text-secondary text-xs font-medium">
                            {discussion.category}
                          </span>
                        )}
                        {discussion.scripture_reference && (
                          <span className="px-2 py-1 rounded-full bg-accent/10 text-accent text-xs font-medium flex items-center gap-1">
                            <BookOpen className="w-3 h-3" />
                            {discussion.scripture_reference}
                          </span>
                        )}
                      </div>
                      <h3 className="font-serif text-xl font-bold text-foreground mb-2">
                        {discussion.title}
                      </h3>
                      <p className="text-muted-foreground line-clamp-2">
                        {discussion.description}
                      </p>
                    </div>
                  </div>

                  {/* Related Devotional */}
                  {discussion.devotional_id && discussion.devotional_title && (
                    <div className="mb-3 p-3 bg-muted/30 rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Related Devotional</p>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/devotional/${discussion.devotional_id}`);
                        }}
                        className="text-sm font-medium text-secondary hover:underline"
                      >
                        {discussion.devotional_title}
                      </button>
                    </div>
                  )}

                  {/* Footer */}
                  <div className="flex items-center justify-between pt-4 border-t border-border">
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1.5">
                        <Users className="w-4 h-4" />
                        <span>{discussion.participants_count} participants</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <MessageCircle className="w-4 h-4" />
                        <span>{discussion.messages_count} messages</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-4 h-4" />
                        <span>{formatTime(discussion.last_activity_at)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-secondary/20 flex items-center justify-center">
                        <span className="text-xs font-semibold text-secondary">
                          {getAuthorInitials(discussion.author_name)}
                        </span>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-foreground">
                          {discussion.author_name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatTime(discussion.created_at)}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {/* Quick Navigation Cards */}
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
            onClick={() => navigate('/bookmarks')}
          >
            <Heart className="w-6 h-6 text-secondary mb-2" />
            <h3 className="font-medium text-foreground mb-1">Saved Items</h3>
            <p className="text-sm text-muted-foreground">View your bookmarks</p>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-card rounded-xl border border-border p-4 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => navigate('/today')}
          >
            <Clock className="w-6 h-6 text-secondary mb-2" />
            <h3 className="font-medium text-foreground mb-1">Today's Reading</h3>
            <p className="text-sm text-muted-foreground">Start your daily reading</p>
          </motion.div>
        </div>
      </div>

      {/* Bottom Navigation */}
    </div>
  );
}

