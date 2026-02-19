/**
 * Groups Page
 * Browse and discover Bible study groups
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Users, Plus, Search, Lock, Globe, BookOpen, MessageCircle, UserPlus, Heart, Baby, UserCheck, Sparkles } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { MainNavigation } from '@/components/navigation/MainNavigation';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';

interface Group {
  id: string;
  name: string;
  description?: string;
  is_public: boolean;
  creator_id: string;
  creator_name: string;
  devotional_id?: string;
  discussion_topic?: string;
  members_count: number;
  messages_count: number;
  members: Array<{
    user_id: string;
    name: string;
    avatar_url?: string;
    role: string;
    joined_at: string;
  }>;
  created_at: string;
}

type GroupCategory = 'all' | 'young-adult' | 'single' | 'married' | 'parents';

const groupCategories = [
  { id: 'all' as GroupCategory, label: 'All Groups', icon: Users },
  { id: 'young-adult' as GroupCategory, label: 'Young Adult', icon: Sparkles, description: 'Connect with others in their 20s and grow together' },
  { id: 'single' as GroupCategory, label: 'Single', icon: UserCheck, description: 'Meet new people and experience life together' },
  { id: 'married' as GroupCategory, label: 'Married', icon: Heart, description: 'Connect with other couples in your stage of life' },
  { id: 'parents' as GroupCategory, label: 'Parents', icon: Baby, description: 'Find resources and connect with other parents' },
];

export default function Groups() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPublic, setFilterPublic] = useState<boolean | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<GroupCategory>('all');

  // Fetch groups
  const { data: groupsData, isLoading, refetch } = useQuery({
    queryKey: ['groups', searchQuery, filterPublic],
    queryFn: async () => {
      try {
        const params: any = {
          page: 1,
          page_size: 50, // Get more to filter by category client-side
        };
        if (searchQuery) params.search = searchQuery;
        if (filterPublic !== null) params.is_public = filterPublic;
        
        const response = await apiClient.listGroups(params);
        return response;
      } catch (error) {
        console.error('Failed to fetch groups:', error);
        return { items: [], total: 0, page: 1, page_size: 20, total_pages: 0 };
      }
    },
  });

  const allGroups = groupsData?.items || [];

  const handleJoinGroup = async (groupId: string) => {
    if (!user) {
      toast({
        title: "Sign in required",
        description: "Please sign in to join groups",
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
      return;
    }

    try {
      await apiClient.joinGroup(groupId);
      toast({
        title: "Joined group!",
        description: "You're now a member of this group",
      });
      refetch();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to join group",
        variant: "destructive"
      });
    }
  };

  const isMember = (group: Group) => {
    if (!user) return false;
    return group.members.some(m => m.user_id === user.id);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) return 'Today';
    if (diffInDays === 1) return 'Yesterday';
    if (diffInDays < 7) return `${diffInDays} days ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // Filter groups by category and search query
  const filteredGroups = allGroups.filter((group: Group) => {
    // Apply search query filter
    if (searchQuery) {
      const searchLower = searchQuery.toLowerCase();
      const nameMatch = group.name.toLowerCase().includes(searchLower);
      const descMatch = (group.description || '').toLowerCase().includes(searchLower);
      if (!nameMatch && !descMatch) return false;
    }
    
    // Apply category filter
    if (selectedCategory === 'all') return true;
    
    const nameLower = group.name.toLowerCase();
    const descLower = (group.description || '').toLowerCase();
    
    // Simple keyword matching - in production, groups would have a category field
    if (selectedCategory === 'young-adult') {
      return nameLower.includes('young') || nameLower.includes('20s') || nameLower.includes('twenties') ||
             descLower.includes('young') || descLower.includes('20s') || descLower.includes('twenties');
    }
    if (selectedCategory === 'single') {
      return nameLower.includes('single') || descLower.includes('single');
    }
    if (selectedCategory === 'married') {
      return nameLower.includes('married') || nameLower.includes('couple') || 
             descLower.includes('married') || descLower.includes('couple');
    }
    if (selectedCategory === 'parents') {
      return nameLower.includes('parent') || nameLower.includes('family') || 
             descLower.includes('parent') || descLower.includes('family');
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-background">
      <MainNavigation />

      <div className="container mx-auto px-4 py-4 md:py-6 pb-20">
        {/* Header */}
        <div className="mb-6 md:mb-8">
          <div className="mb-4 md:mb-6">
            <div className="flex items-start justify-between gap-3 mb-3">
              <h1 className="text-2xl md:text-4xl font-bold text-foreground leading-tight">
                Connect with others like you
              </h1>
              {user && (
                <Button
                  onClick={() => navigate('/groups/new')}
                  className="gap-1.5 md:gap-2 bg-primary hover:bg-primary/90 shrink-0"
                  size="sm"
                >
                  <Plus className="w-4 h-4 md:w-5 md:h-5" />
                  <span className="hidden sm:inline">Create Group</span>
                  <span className="sm:hidden">Create</span>
                </Button>
              )}
            </div>
            <p className="text-muted-foreground text-sm md:text-lg">
              Life is better connected. Find a group that fits your stage of life.
            </p>
          </div>

          {/* Category Tabs - Mobile Optimized */}
          <div className="mb-4 md:mb-6 -mx-4 md:mx-0">
            <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-2 px-4 md:px-0 md:flex-wrap">
              {groupCategories.map((category) => {
                const Icon = category.icon;
                const isSelected = selectedCategory === category.id;
                return (
                  <button
                    key={category.id}
                    onClick={() => setSelectedCategory(category.id)}
                    className={`flex items-center gap-1.5 md:gap-2 px-3 md:px-4 py-2 md:py-2.5 rounded-lg font-medium text-sm md:text-base transition-all whitespace-nowrap shrink-0 ${
                      isSelected
                        ? 'bg-primary text-primary-foreground shadow-md'
                        : 'bg-muted text-muted-foreground hover:bg-muted/80'
                    }`}
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    <span>{category.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Search and Filters */}
          <div className="space-y-3 mb-4 md:mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search groups..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 h-10 md:h-11"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={filterPublic === null ? "default" : "outline"}
                size="sm"
                onClick={() => setFilterPublic(null)}
                className="flex-1 sm:flex-initial"
              >
                All
              </Button>
              <Button
                variant={filterPublic === true ? "default" : "outline"}
                size="sm"
                onClick={() => setFilterPublic(true)}
                className="flex-1 sm:flex-initial gap-1.5 md:gap-2"
              >
                <Globe className="w-4 h-4" />
                <span className="hidden xs:inline">Public</span>
              </Button>
              <Button
                variant={filterPublic === false ? "default" : "outline"}
                size="sm"
                onClick={() => setFilterPublic(false)}
                className="flex-1 sm:flex-initial gap-1.5 md:gap-2"
              >
                <Lock className="w-4 h-4" />
                <span className="hidden xs:inline">Private</span>
              </Button>
            </div>
          </div>
        </div>

        {/* Category Description */}
        {selectedCategory !== 'all' && (
          <div className="mb-6 p-4 bg-primary/5 rounded-xl border border-primary/20">
            <p className="text-foreground">
              {groupCategories.find(c => c.id === selectedCategory)?.description}
            </p>
          </div>
        )}

        {/* Groups List */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            <p className="mt-4 text-sm md:text-base text-muted-foreground">Loading groups...</p>
          </div>
        ) : filteredGroups.length === 0 ? (
          <div className="text-center py-12 md:py-16 px-4">
            <Users className="w-12 h-12 md:w-16 md:h-16 mx-auto mb-4 text-muted-foreground" />
            <h2 className="text-lg md:text-xl font-bold mb-2">No Groups Found</h2>
            <p className="text-sm md:text-base text-muted-foreground mb-6">
              {searchQuery || selectedCategory !== 'all'
                ? 'Try a different search or category'
                : 'Be the first to create a group!'}
            </p>
            {user && (
              <Button
                onClick={() => navigate('/groups/new')}
                className="gap-2 bg-primary hover:bg-primary/90"
                size="sm"
              >
                <Plus className="w-4 h-4" />
                Create Group
              </Button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
            {filteredGroups.map((group: Group, index: number) => {
              const member = isMember(group);
              return (
                <motion.div
                  key={group.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  className="bg-card rounded-xl border border-border hover:shadow-lg hover:border-primary/50 transition-all cursor-pointer overflow-hidden"
                  onClick={() => navigate(`/groups/${group.id}`)}
                >
                  <div className="p-4 md:p-6">
                    {/* Header */}
                    <div className="mb-3">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        {group.is_public ? (
                          <Globe className="w-3.5 h-3.5 md:w-4 md:h-4 text-muted-foreground" />
                        ) : (
                          <Lock className="w-3.5 h-3.5 md:w-4 md:h-4 text-muted-foreground" />
                        )}
                        <span className="text-xs text-muted-foreground">
                          {group.is_public ? 'Public' : 'Private'}
                        </span>
                        {group.discussion_topic && (
                          <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-medium">
                            {group.discussion_topic}
                          </span>
                        )}
                      </div>
                      <h3 className="text-lg md:text-xl font-bold text-foreground mb-2 leading-tight">
                        {group.name}
                      </h3>
                      {group.description && (
                        <p className="text-sm md:text-base text-muted-foreground line-clamp-2 mb-3">
                          {group.description}
                        </p>
                      )}
                    </div>

                    {/* Stats */}
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-xs md:text-sm text-muted-foreground mb-4">
                      <div className="flex items-center gap-1">
                        <Users className="w-3.5 h-3.5 md:w-4 md:h-4" />
                        <span>{group.members_count}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <MessageCircle className="w-3.5 h-3.5 md:w-4 md:h-4" />
                        <span>{group.messages_count}</span>
                      </div>
                      <div className="text-xs">
                        {formatDate(group.created_at)}
                      </div>
                    </div>

                    {/* Creator */}
                    <div className="flex items-center justify-between pt-3 md:pt-4 border-t border-border gap-3">
                      <div className="flex items-center gap-2 min-w-0">
                        <div className="w-7 h-7 md:w-8 md:h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                          <span className="text-xs font-semibold text-primary">
                            {group.creator_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                          </span>
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-foreground truncate">
                            {group.creator_name}
                          </p>
                          <p className="text-xs text-muted-foreground">Creator</p>
                        </div>
                      </div>
                      <Button
                        variant={member ? "outline" : "default"}
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (!user) {
                            // Prompt unauthenticated users to sign in
                            handleJoinGroup(group.id);
                          } else if (member) {
                            navigate(`/groups/${group.id}`);
                          } else {
                            handleJoinGroup(group.id);
                          }
                        }}
                        className={`gap-1.5 shrink-0 text-xs md:text-sm ${member ? '' : 'bg-primary hover:bg-primary/90'}`}
                      >
                        {member ? (
                          <>
                            <BookOpen className="w-3.5 h-3.5 md:w-4 md:h-4" />
                            <span className="hidden sm:inline">View</span>
                          </>
                        ) : (
                          <>
                            <UserPlus className="w-3.5 h-3.5 md:w-4 md:h-4" />
                            <span className="hidden sm:inline">Join</span>
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}

        {/* Quick Actions */}
        {user && filteredGroups.length > 0 && (
          <div className="mt-8 text-center">
            <Button
              variant="outline"
              onClick={() => navigate('/groups/new')}
              className="gap-2"
            >
              <Plus className="w-4 h-4" />
              Create Your Own Group
            </Button>
          </div>
        )}
      </div>

    </div>
  );
}

