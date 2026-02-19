import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Search, Filter, BookOpen, Clock, Heart, Eye } from "lucide-react";
import { MainNavigation } from "@/components/navigation/MainNavigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface Devotional {
  id: string;
  title: string;
  slug: string;
  author_name: string;
  category: string;
  excerpt?: string;
  featured_image_url?: string;
  published_at: string;
  views_count: number;
  likes_count: number;
  reading_time_minutes?: number;
}

export default function Browse() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [devotionals, setDevotionals] = useState<Devotional[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("published_at");
  const [dateFilter, setDateFilter] = useState<string>("all"); // all, last_30_days, this_week

  useEffect(() => {
    loadDevotionals();
  }, [selectedCategory, sortBy, dateFilter]);

  const loadDevotionals = async () => {
    setLoading(true);
    try {
      // Calculate days parameter based on date filter
      let daysParam: number | undefined;
      if (dateFilter === 'this_week') {
        daysParam = 7;
      } else if (dateFilter === 'last_30_days') {
        daysParam = 30;
      }
      // If dateFilter === 'all', daysParam stays undefined

      const response = await apiClient.getDevotionals({
        status: 'published',
        category: selectedCategory === 'all' ? undefined : selectedCategory,
        sort_by: sortBy as any,
        sort_order: 'desc',
        limit: 50,
        days: daysParam, // Pass date filter to backend
      });

      // Backend now handles date filtering, so we can use items directly
      setDevotionals(response.items);
    } catch (error) {
      console.error('Failed to load devotionals:', error);
      toast({
        title: "Error",
        description: "Failed to load devotionals",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const filteredDevotionals = devotionals.filter(dev =>
    dev.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    dev.author_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const categories = ["all", "Faith", "Prayer", "Hope", "Love", "Worship", "Grace", "Peace"];

  const calculateReadTime = (content: any[]): number => {
    if (!content || !Array.isArray(content)) return 5;
    const totalWords = content.reduce((count, block) => {
      if (block && typeof block.text === 'string') {
        return count + block.text.split(/\s+/).length;
      }
      return count;
    }, 0);
    return Math.max(1, Math.ceil(totalWords / 200));
  };

  return (
    <div className="min-h-screen bg-background">
      <MainNavigation />

      <div className="container py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-serif font-bold text-foreground mb-2">
            Browse Devotionals
          </h1>
          <p className="text-muted-foreground">
            Discover spiritual nourishment for your daily journey
          </p>
        </motion.div>

        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8 space-y-4"
        >
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search by title or author..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 h-12"
            />
          </div>

          {/* Category Pills */}
          <div className="flex flex-wrap gap-2">
            {categories.map((category) => (
              <Button
                key={category}
                variant={selectedCategory === category ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedCategory(category)}
              >
                {category === 'all' ? 'All Categories' : category}
              </Button>
            ))}
          </div>

          {/* Filters Row */}
          <div className="flex flex-wrap items-center gap-4">
            {/* Date Filter */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Show:</span>
              <Select value={dateFilter} onValueChange={setDateFilter}>
                <SelectTrigger className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Time</SelectItem>
                  <SelectItem value="this_week">This Week</SelectItem>
                  <SelectItem value="last_30_days">Last 30 Days</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Sort Options */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Sort by:</span>
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="published_at">Latest</SelectItem>
                  <SelectItem value="views_count">Popular</SelectItem>
                  <SelectItem value="likes_count">Trending</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </motion.div>

        {/* Results Count */}
        <div className="mb-6">
          <p className="text-sm text-muted-foreground">
            {filteredDevotionals.length} {filteredDevotionals.length === 1 ? 'devotional' : 'devotionals'} found
          </p>
        </div>

        {/* Devotionals Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <Card key={i} className="overflow-hidden">
                <div className="h-48 bg-muted animate-pulse" />
                <CardContent className="p-6">
                  <div className="h-4 bg-muted rounded animate-pulse mb-2" />
                  <div className="h-4 bg-muted rounded animate-pulse w-2/3" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : filteredDevotionals.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">No devotionals found</h3>
            <p className="text-muted-foreground">Try adjusting your search or filters</p>
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {filteredDevotionals.map((devotional, index) => (
              <motion.div
                key={devotional.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card
                  className="overflow-hidden hover:shadow-lg transition-shadow cursor-pointer group"
                  onClick={() => navigate(`/devotional/${devotional.id}`)}
                >
                  {/* Image */}
                  {devotional.featured_image_url ? (
                    <div className="h-48 overflow-hidden">
                      <img
                        src={devotional.featured_image_url}
                        alt={devotional.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                      />
                    </div>
                  ) : (
                    <div className="h-48 bg-gradient-to-br from-secondary to-secondary/50 flex items-center justify-center">
                      <BookOpen className="w-12 h-12 text-secondary-foreground/50" />
                    </div>
                  )}

                  <CardContent className="p-6">
                    {/* Category Badge */}
                    <Badge variant="secondary" className="mb-3">
                      {devotional.category || 'Devotional'}
                    </Badge>

                    {/* Title */}
                    <h3 className="font-serif font-bold text-xl text-foreground mb-2 line-clamp-2 group-hover:text-primary transition-colors">
                      {devotional.title}
                    </h3>

                    {/* Author */}
                    <p className="text-sm text-muted-foreground mb-4">
                      by {devotional.author_name || 'FreshManna Team'}
                    </p>

                    {/* Meta Info */}
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        <span>{devotional.reading_time_minutes || 5} min</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Eye className="w-4 h-4" />
                        <span>{devotional.views_count || 0}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Heart className="w-4 h-4" />
                        <span>{devotional.likes_count || 0}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
}
