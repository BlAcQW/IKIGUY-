import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Users,
  FileText,
  TrendingUp,
  Shield,
  Menu,
  Search,
  Bell,
  Activity,
  UserPlus,
  Heart,
  MessageSquare,
  Eye,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { AdminSidebar } from "@/components/admin/AdminSidebar";
import { apiClient } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";

interface DashboardStats {
  total_users: number;
  total_authors: number;
  total_devotionals: number;
  published_devotionals: number;
  draft_devotionals: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  new_users_this_month: number;
  new_devotionals_this_month: number;
}

interface RecentActivity {
  id: string;
  type: string;
  description: string;
  user_name?: string;
  devotional_title?: string;
  timestamp: string;
}

function StatCard({ label, value, change, icon: Icon, color, loading }: any) {
  if (loading) {
    return (
      <div className="bg-card rounded-2xl p-5 border border-border shadow-soft">
        <div className="flex items-center justify-between mb-3">
          <Skeleton className="w-10 h-10 rounded-xl" />
          <Skeleton className="w-16 h-6 rounded-full" />
        </div>
        <Skeleton className="h-8 w-24 mb-2" />
        <Skeleton className="h-4 w-20" />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card rounded-2xl p-5 border border-border shadow-soft"
    >
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
        {change && (
          <span className="text-xs font-medium text-accent bg-accent/10 px-2 py-1 rounded-full">
            {change}
          </span>
        )}
      </div>
      <p className="font-serif text-2xl font-bold text-foreground">
        {typeof value === 'number' ? value.toLocaleString() : (value ?? '0')}
      </p>
      <p className="text-sm text-muted-foreground">{label}</p>
    </motion.div>
  );
}

function AdminDashboardContent() {
  const { toast } = useToast();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [activityLoading, setActivityLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setActivityLoading(true);

      // Fetch stats and recent activity in parallel
      const [statsData, activityData] = await Promise.all([
        apiClient.getAdminStats(),
        apiClient.getRecentActivity(10),
      ]);

      setStats(statsData);
      setRecentActivity(activityData.activities || []);
    } catch (error: any) {
      console.error("Failed to fetch dashboard data:", error);
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to load dashboard data",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setActivityLoading(false);
    }
  };

  const statCards = stats ? [
    {
      label: "Total Users",
      value: stats.total_users,
      change: `+${stats.new_users_this_month} this month`,
      icon: Users,
      color: "secondary",
    },
    {
      label: "Total Views",
      value: stats.total_views,
      change: null,
      icon: Eye,
      color: "accent",
    },
    {
      label: "Authors",
      value: stats.total_authors,
      change: null,
      icon: Shield,
      color: "secondary",
    },
    {
      label: "Devotionals",
      value: stats.total_devotionals,
      change: `+${stats.new_devotionals_this_month} this month`,
      icon: FileText,
      color: "accent",
    },
    {
      label: "Total Likes",
      value: stats.total_likes,
      change: null,
      icon: Heart,
      color: "secondary",
    },
    {
      label: "Total Comments",
      value: stats.total_comments,
      change: null,
      icon: MessageSquare,
      color: "accent",
    },
    {
      label: "Published",
      value: stats.published_devotionals,
      change: null,
      icon: TrendingUp,
      color: "secondary",
    },
    {
      label: "Drafts",
      value: stats.draft_devotionals,
      change: null,
      icon: FileText,
      color: "accent",
    },
  ] : [];

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "user_registered":
        return UserPlus;
      case "devotional_published":
        return FileText;
      case "devotional_created":
        return FileText;
      default:
        return Activity;
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case "user_registered":
        return "bg-secondary/10 text-secondary";
      case "devotional_published":
        return "bg-accent/10 text-accent";
      case "devotional_created":
        return "bg-primary/10 text-primary";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
    return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
  };

  return (
    <div className="flex-1 overflow-auto">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm border-b border-border">
        <div className="flex items-center justify-between px-6 h-16">
          <div className="flex items-center gap-4">
            <SidebarTrigger className="lg:hidden">
              <Menu className="w-5 h-5" />
            </SidebarTrigger>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search users, content..."
                className="pl-9 w-64 h-9 bg-muted/50"
              />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-secondary rounded-full" />
            </Button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Welcome */}
          <div className="mb-8">
            <h1 className="font-serif text-3xl font-bold text-foreground mb-2">
              Admin Dashboard
            </h1>
            <p className="text-muted-foreground">
              Platform metrics and activity powered by the Holy Spirit
            </p>
          </div>

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

          {/* Recent Activity */}
          <div className="bg-card rounded-2xl border border-border shadow-soft">
            <div className="flex items-center justify-between p-5 border-b border-border">
              <h2 className="font-serif text-xl font-semibold text-foreground">
                Recent Activity
              </h2>
              <Button variant="ghost" size="sm" onClick={fetchDashboardData}>
                Refresh
              </Button>
            </div>
            <div className="divide-y divide-border">
              {activityLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-4 p-5">
                    <Skeleton className="w-10 h-10 rounded-full" />
                    <div className="flex-1">
                      <Skeleton className="h-4 w-3/4 mb-2" />
                      <Skeleton className="h-3 w-1/4" />
                    </div>
                  </div>
                ))
              ) : recentActivity.length > 0 ? (
                recentActivity.map((activity) => {
                  const Icon = getActivityIcon(activity.type);
                  return (
                    <div
                      key={activity.id}
                      className="flex items-center gap-4 p-5 hover:bg-muted/30 transition-colors"
                    >
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center ${getActivityColor(
                          activity.type
                        )}`}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-foreground">
                          {activity.description}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatTimestamp(activity.timestamp)}
                        </p>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="p-8 text-center text-muted-foreground">
                  No recent activity
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
}

const AdminDashboardEnhanced = () => {
  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-background">
        <AdminSidebar />
        <AdminDashboardContent />
      </div>
    </SidebarProvider>
  );
};

export default AdminDashboardEnhanced;
