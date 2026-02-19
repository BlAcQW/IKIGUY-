/**
 * Category Browser Component
 * Horizontal scrollable category pills for quick browsing
 * Mobile-first design
 */

import { motion } from "framer-motion";
import { Heart, Sparkles, Flame, Mountain, HandHeart, Lightbulb, Shield, Sun, Smile, Music, Users, Zap } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { cn } from "@/lib/utils";

// Category configuration with icons and colors
const categoryConfig: Record<string, { icon: any; color: string; bgColor: string }> = {
  prayer: { icon: HandHeart, color: "text-blue-500", bgColor: "bg-blue-500/10" },
  faith: { icon: Sparkles, color: "text-purple-500", bgColor: "bg-purple-500/10" },
  hope: { icon: Sun, color: "text-yellow-500", bgColor: "bg-yellow-500/10" },
  love: { icon: Heart, color: "text-red-500", bgColor: "bg-red-500/10" },
  purpose: { icon: Mountain, color: "text-green-500", bgColor: "bg-green-500/10" },
  healing: { icon: Shield, color: "text-teal-500", bgColor: "bg-teal-500/10" },
  wisdom: { icon: Lightbulb, color: "text-secondary", bgColor: "bg-secondary/10" },
  peace: { icon: Flame, color: "text-pink-500", bgColor: "bg-pink-500/10" },
  joy: { icon: Smile, color: "text-amber-500", bgColor: "bg-amber-500/10" },
  grace: { icon: Zap, color: "text-indigo-500", bgColor: "bg-indigo-500/10" },
  worship: { icon: Music, color: "text-fuchsia-500", bgColor: "bg-fuchsia-500/10" },
  family: { icon: Users, color: "text-emerald-500", bgColor: "bg-emerald-500/10" },
};

const CategoryBrowser = () => {
  const navigate = useNavigate();

  // Fetch devotionals to get category counts
  const { data: categoryData, isLoading } = useQuery({
    queryKey: ['categoryBrowser'],
    queryFn: async () => {
      try {
        // Fetch all published devotionals to count categories
        const response = await apiClient.getDevotionals({
          status: 'published',
          page: 1,
          limit: 100, // Get enough to calculate stats
          sort_by: 'published_at',
          sort_order: 'desc'
        });

        // Count categories
        const categoryCounts: Record<string, number> = {};
        response.items?.forEach((dev: any) => {
          dev.categories?.forEach((cat: string) => {
            categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
          });
        });

        return categoryCounts;
      } catch (error) {
        console.error('Failed to fetch categories:', error);
        return {};
      }
    }
  });

  // Build categories array with real counts
  const categories = Object.keys(categoryConfig).map(catId => {
    const config = categoryConfig[catId];
    const count = categoryData?.[catId] || 0;
    return {
      id: catId,
      name: catId.charAt(0).toUpperCase() + catId.slice(1),
      ...config,
      count
    };
  }).filter(cat => cat.count > 0); // Only show categories with devotionals

  const handleCategoryClick = (categoryId: string) => {
    navigate(`/auth?category=${categoryId}`);
  };

  // Loading state
  if (isLoading) {
    return (
      <section className="py-6 md:py-10 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="mb-4">
            <div className="h-7 w-40 bg-muted rounded animate-pulse mb-2"></div>
            <div className="h-4 w-60 bg-muted rounded animate-pulse"></div>
          </div>
          <div className="flex gap-3 overflow-x-auto hide-scrollbar pb-2">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="min-w-[100px] h-[100px] bg-card rounded-2xl border border-border/50 animate-pulse"></div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  // No categories available
  if (categories.length === 0) {
    return null;
  }

  return (
    <section className="py-6 md:py-10 bg-muted/30">
      <div className="container mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="px-4 mb-4"
        >
          <h2 className="font-serif text-xl md:text-2xl font-bold text-foreground mb-1">
            Explore by Topic
          </h2>
          <p className="text-sm text-muted-foreground">
            Discover devotionals that speak to your heart
          </p>
        </motion.div>

        {/* Horizontal Scrollable Categories */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="overflow-x-auto hide-scrollbar"
        >
          <div className="flex gap-3 px-4 pb-2">
            {categories.map((category, index) => {
              const Icon = category.icon;
              return (
                <motion.button
                  key={category.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: index * 0.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleCategoryClick(category.id)}
                  className={cn(
                    "flex flex-col items-center justify-center min-w-[100px] h-[100px] rounded-2xl",
                    "border border-border/50 transition-all duration-200",
                    "hover:shadow-lg hover:scale-105 active:scale-95",
                    "bg-card"
                  )}
                >
                  <div className={cn(
                    "w-12 h-12 rounded-full flex items-center justify-center mb-2",
                    category.bgColor
                  )}>
                    <Icon className={cn("w-6 h-6", category.color)} />
                  </div>
                  <span className="text-sm font-medium text-foreground">
                    {category.name}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {category.count} posts
                  </span>
                </motion.button>
              );
            })}
          </div>
        </motion.div>

        {/* Mobile Scroll Hint */}
        <div className="flex justify-center mt-2 md:hidden">
          <div className="flex gap-1">
            <div className="w-6 h-0.5 bg-secondary/50 rounded-full" />
            <div className="w-6 h-0.5 bg-muted-foreground/20 rounded-full" />
            <div className="w-6 h-0.5 bg-muted-foreground/20 rounded-full" />
          </div>
        </div>
      </div>

      <style>{`
        .hide-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .hide-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </section>
  );
};

export default CategoryBrowser;
