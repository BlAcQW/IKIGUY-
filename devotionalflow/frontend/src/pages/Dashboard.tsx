import { useState } from "react";
import { motion } from "framer-motion";
import {
  BookOpen,
  PenLine,
  Calendar,
  BarChart3,
  Settings,
  Bell,
  Search,
  Plus,
  ChevronDown,
  MoreHorizontal,
  Eye,
  Heart,
  MessageCircle,
  TrendingUp,
  Users,
  FileText,
  Menu,
  LogOut,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
  useSidebar,
  SidebarFooter,
} from "@/components/ui/sidebar";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

const menuItems = [
  { title: "Overview", url: "/dashboard", icon: BarChart3 },
  { title: "Author Dashboard", url: "/dashboard/author", icon: BookOpen },
  { title: "Compose", url: "/dashboard/compose", icon: PenLine },
  { title: "Calendar", url: "/dashboard/calendar", icon: Calendar },
  { title: "Devotionals", url: "/dashboard/devotionals", icon: FileText },
  { title: "Settings", url: "/dashboard/settings", icon: Settings },
];

const recentDevotionals = [
  {
    id: 1,
    title: "Walking in Divine Purpose",
    date: "Dec 9, 2024",
    status: "published",
    views: 1247,
    likes: 89,
    comments: 23,
  },
  {
    id: 2,
    title: "The Power of Prayer",
    date: "Dec 8, 2024",
    status: "published",
    views: 982,
    likes: 67,
    comments: 18,
  },
  {
    id: 3,
    title: "Finding Peace in Chaos",
    date: "Dec 10, 2024",
    status: "scheduled",
    views: 0,
    likes: 0,
    comments: 0,
  },
  {
    id: 4,
    title: "God's Unfailing Love",
    date: "Dec 7, 2024",
    status: "published",
    views: 1456,
    likes: 112,
    comments: 34,
  },
];

const stats = [
  { label: "Total Readers", value: "12,847", change: "+12%", icon: Users },
  { label: "Devotionals", value: "156", change: "+3", icon: FileText },
  { label: "Engagement", value: "8.4%", change: "+2.1%", icon: TrendingUp },
  { label: "This Week", value: "3,421", change: "+18%", icon: Eye },
];

function DashboardSidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <Sidebar className="border-r border-border bg-card">
      <div className="p-4 border-b border-border">
        <a href="/" className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-xl bg-secondary flex items-center justify-center">
            <BookOpen className="w-4 h-4 text-secondary-foreground" />
          </div>
          <span className="font-serif text-lg font-semibold text-foreground">
            FreshManna
          </span>
        </a>
      </div>
      
      <SidebarContent className="px-3 py-4">
        <SidebarGroup>
          <SidebarGroupLabel className="text-xs uppercase tracking-wider text-muted-foreground mb-2">
            Main Menu
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={item.url}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                          isActive
                            ? "bg-secondary/10 text-secondary font-medium"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground"
                        }`
                      }
                    >
                      <item.icon className="w-5 h-5" />
                      <span>{item.title}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <div className="mt-auto p-4 border-t border-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-secondary/20 flex items-center justify-center">
            <span className="font-semibold text-secondary">JS</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-foreground text-sm truncate">
              Pastor John Smith
            </p>
            <p className="text-xs text-muted-foreground truncate">
              john@church.org
            </p>
          </div>
          <Button variant="ghost" size="icon" className="shrink-0">
            <ChevronDown className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <SidebarFooter className="border-t border-border p-4">
        <Button
          variant="ghost"
          className="w-full justify-start text-destructive hover:text-destructive hover:bg-destructive/10"
          onClick={handleLogout}
        >
          <LogOut className="w-4 h-4 mr-2" />
          Log Out
        </Button>
      </SidebarFooter>
    </Sidebar>
  );
}

function DashboardContent() {
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
                placeholder="Search devotionals..."
                className="pl-9 w-64 h-9 bg-muted/50"
              />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-secondary rounded-full" />
            </Button>
            <Button variant="hero" size="sm" className="gap-2">
              <Plus className="w-4 h-4" />
              New Devotional
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
              Good morning, Pastor John
            </h1>
            <p className="text-muted-foreground">
              Here's what's happening with your ministry today.
            </p>
          </div>

          {/* Stats */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {stats.map((stat) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-card rounded-2xl p-5 border border-border shadow-soft"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-secondary/10 flex items-center justify-center">
                    <stat.icon className="w-5 h-5 text-secondary" />
                  </div>
                  <span className="text-xs font-medium text-accent bg-accent/10 px-2 py-1 rounded-full">
                    {stat.change}
                  </span>
                </div>
                <p className="font-serif text-2xl font-bold text-foreground">
                  {stat.value}
                </p>
                <p className="text-sm text-muted-foreground">{stat.label}</p>
              </motion.div>
            ))}
          </div>

          {/* Recent Devotionals */}
          <div className="bg-card rounded-2xl border border-border shadow-soft">
            <div className="flex items-center justify-between p-5 border-b border-border">
              <h2 className="font-serif text-xl font-semibold text-foreground">
                Recent Devotionals
              </h2>
              <Button variant="ghost" size="sm">
                View All
              </Button>
            </div>
            <div className="divide-y divide-border">
              {recentDevotionals.map((devotional) => (
                <div
                  key={devotional.id}
                  className="flex items-center gap-4 p-5 hover:bg-muted/30 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-foreground truncate">
                      {devotional.title}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {devotional.date}
                    </p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      devotional.status === "published"
                        ? "bg-accent/10 text-accent"
                        : "bg-secondary/10 text-secondary"
                    }`}
                  >
                    {devotional.status}
                  </span>
                  <div className="hidden sm:flex items-center gap-4 text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                      <Eye className="w-4 h-4" />
                      <span className="text-sm">{devotional.views}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Heart className="w-4 h-4" />
                      <span className="text-sm">{devotional.likes}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <MessageCircle className="w-4 h-4" />
                      <span className="text-sm">{devotional.comments}</span>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
}

const Dashboard = () => {
  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-background">
        <DashboardSidebar />
        <DashboardContent />
      </div>
    </SidebarProvider>
  );
};

export default Dashboard;
