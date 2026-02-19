import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  BookOpen,
  Heart,
  Eye,
  MessageSquare,
  Share2,
  TrendingUp,
  Target,
  Award,
  BarChart3,
  Calendar,
  FileText,
  Edit,
  Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { useNavigate } from "react-router-dom";
import { logger } from '@/lib/logger';

interface AuthorStats {
  total_devotionals: number;
  published_count: number;
  draft_count: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  avg_engagement_rate: number;
  devotionals_this_month: number;
}

interface Milestone {
  id: string;
  title: string;
  description: string;
  target: number;
  current: number;
  achieved: boolean;
  icon: string;
}

interface BestPerforming {
  devotional_id: string;
  title: string;
  view_count: number;
  like_count: number;
  comment_count: number;
  engagement_rate: number;
}

function StatCard({ label, value, icon: Icon, color = "secondary", trend, loading }: any) {
  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-3">
            <Skeleton className="w-10 h-10 rounded-xl" />
            {trend && <Skeleton className="w-16 h-6 rounded-full" />}
          </div>
          <Skeleton className="h-8 w-24 mb-2" />
          <Skeleton className="h-4 w-20" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-3">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center ${
              color === "secondary" ? "bg-secondary/10" : "bg-accent/10"
            }`}
          >
            <Icon
              className={`w-5 h-5 ${
                color === "secondary" ? "text-secondary" : "text-accent"
              }`}
            />
          </div>
          {trend && (
            <span className="text-xs font-medium text-accent bg-accent/10 px-2 py-1 rounded-full">
              {trend}
            </span>
          )}
        </div>
        <p className="font-serif text-2xl font-bold text-foreground">
          {typeof value === "number" ? value.toLocaleString() : value}
        </p>
        <p className="text-sm text-muted-foreground">{label}</p>
      </CardContent>
    </Card>
  );
}

function MilestoneCard({ milestone }: { milestone: Milestone }) {
  const progress = Math.min((milestone.current / milestone.target) * 100, 100);

  const icons: Record<string, any> = {
    devotionals: FileText,
    views: Eye,
    likes: Heart,
    engagement: TrendingUp,
  };

  const Icon = icons[milestone.icon] || Award;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card rounded-xl p-5 border border-border"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
            milestone.achieved ? "bg-accent/10" : "bg-muted"
          }`}>
            <Icon className={`w-5 h-5 ${
              milestone.achieved ? "text-accent" : "text-muted-foreground"
            }`} />
          </div>
          <div>
            <p className="font-medium text-foreground">{milestone.title}</p>
            <p className="text-xs text-muted-foreground">{milestone.description}</p>
          </div>
        </div>
        {milestone.achieved && (
          <Award className="w-5 h-5 text-accent" />
        )}
      </div>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">
            {milestone.current} / {milestone.target}
          </span>
          <span className="font-medium text-foreground">{Math.round(progress)}%</span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>
    </motion.div>
  );
}

const AuthorDashboard = () => {
  const { toast } = useToast();
  const navigate = useNavigate();
  const [stats, setStats] = useState<AuthorStats | null>(null);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [bestPerforming, setBestPerforming] = useState<BestPerforming[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);

      const [statsData, milestonesData, performanceData] = await Promise.all([
        apiClient.getAuthorStats(),
        apiClient.getAuthorMilestones(),
        apiClient.getAuthorPerformance(30),
      ]);

      setStats(statsData);
      setMilestones(milestonesData.milestones || []);
      setBestPerforming(performanceData.best_performing || []);
    } catch (error: any) {
      logger.error("Failed to fetch author dashboard:", error);
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to load dashboard data",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const statCards = stats ? [
    {
      label: "Total Devotionals",
      value: stats.total_devotionals,
      icon: FileText,
      color: "secondary",
      trend: `+${stats.devotionals_this_month} this month`,
    },
    {
      label: "Total Views",
      value: stats.total_views,
      icon: Eye,
      color: "accent",
    },
    {
      label: "Total Likes",
      value: stats.total_likes,
      icon: Heart,
      color: "secondary",
    },
    {
      label: "Total Comments",
      value: stats.total_comments,
      icon: MessageSquare,
      color: "accent",
    },
    {
      label: "Total Shares",
      value: stats.total_shares,
      icon: Share2,
      color: "secondary",
    },
    {
      label: "Avg Engagement",
      value: `${stats.avg_engagement_rate.toFixed(1)}%`,
      icon: TrendingUp,
      color: "accent",
    },
    {
      label: "Published",
      value: stats.published_count,
      icon: BookOpen,
      color: "secondary",
    },
    {
      label: "Drafts",
      value: stats.draft_count,
      icon: Edit,
      color: "accent",
    },
  ] : [];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-card border-b border-border">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-serif text-3xl font-bold text-foreground mb-2">
                Author Dashboard
              </h1>
              <p className="text-muted-foreground">
                Your devotional writing journey and impact
              </p>
            </div>
            <Button onClick={() => navigate("/compose")} className="gap-2">
              <Plus className="w-4 h-4" />
              New Devotional
            </Button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="container mx-auto px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Stats Grid */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <StatCard key={i} loading={true} />
              ))
            ) : (
              statCards.map((stat, index) => (
                <StatCard key={index} {...stat} />
              ))
            )}
          </div>

          <div className="grid lg:grid-cols-2 gap-6 mb-8">
            {/* Milestones */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-secondary" />
                  Milestones & Achievements
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {loading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-24 w-full rounded-xl" />
                  ))
                ) : milestones.length > 0 ? (
                  milestones.slice(0, 4).map((milestone) => (
                    <MilestoneCard key={milestone.id} milestone={milestone} />
                  ))
                ) : (
                  <p className="text-center text-muted-foreground py-8">
                    Keep writing to unlock milestones!
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Best Performing */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-accent" />
                  Best Performing Devotionals
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="space-y-3">
                    {Array.from({ length: 3 }).map((_, i) => (
                      <Skeleton key={i} className="h-20 w-full rounded-lg" />
                    ))}
                  </div>
                ) : bestPerforming.length > 0 ? (
                  <div className="space-y-3">
                    {bestPerforming.slice(0, 5).map((devotional, index) => (
                      <motion.div
                        key={devotional.devotional_id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="bg-muted/50 rounded-lg p-4 hover:bg-muted transition-colors cursor-pointer"
                        onClick={() => navigate(`/devotional/${devotional.devotional_id}`)}
                      >
                        <h4 className="font-medium text-foreground mb-2 line-clamp-1">
                          {devotional.title}
                        </h4>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Eye className="w-3 h-3" />
                            {devotional.view_count.toLocaleString()}
                          </span>
                          <span className="flex items-center gap-1">
                            <Heart className="w-3 h-3" />
                            {devotional.like_count.toLocaleString()}
                          </span>
                          <span className="flex items-center gap-1">
                            <MessageSquare className="w-3 h-3" />
                            {devotional.comment_count.toLocaleString()}
                          </span>
                          <span className="ml-auto font-medium text-accent">
                            {devotional.engagement_rate.toFixed(1)}% engagement
                          </span>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-muted-foreground py-8">
                    No devotionals published yet
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Button
                  variant="outline"
                  className="h-auto py-6 flex-col gap-2"
                  onClick={() => navigate("/compose")}
                >
                  <Plus className="w-6 h-6" />
                  <span>Write New Devotional</span>
                </Button>
                <Button
                  variant="outline"
                  className="h-auto py-6 flex-col gap-2"
                  onClick={() => navigate("/author/devotionals")}
                >
                  <FileText className="w-6 h-6" />
                  <span>Manage Devotionals</span>
                </Button>
                <Button
                  variant="outline"
                  className="h-auto py-6 flex-col gap-2"
                  onClick={() => navigate("/calendar")}
                >
                  <Calendar className="w-6 h-6" />
                  <span>View Calendar</span>
                </Button>
                <Button
                  variant="outline"
                  className="h-auto py-6 flex-col gap-2"
                  onClick={() => navigate("/analytics")}
                >
                  <BarChart3 className="w-6 h-6" />
                  <span>View Analytics</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </main>
    </div>
  );
};

export default AuthorDashboard;
