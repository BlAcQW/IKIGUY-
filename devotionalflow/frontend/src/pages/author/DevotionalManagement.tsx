import { useState } from "react";
import { motion } from "framer-motion";
import {
  BookOpen,
  PenLine,
  Calendar,
  BarChart3,
  Settings,
  Menu,
  Search,
  Bell,
  Plus,
  MoreHorizontal,
  Eye,
  Heart,
  MessageCircle,
  Filter,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  Edit2,
  Trash2,
  Copy,
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
  SidebarFooter,
} from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { NavLink, useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

const menuItems = [
  { title: "Dashboard", url: "/dashboard", icon: BarChart3 },
  { title: "Devotionals", url: "/dashboard/devotionals", icon: FileText },
  { title: "Compose", url: "/dashboard/compose", icon: PenLine },
  { title: "Calendar", url: "/dashboard/calendar", icon: Calendar },
  { title: "Settings", url: "/dashboard/settings", icon: Settings },
];

interface Devotional {
  id: string;
  title: string;
  content?: string;
  excerpt?: string;
  status: "published" | "scheduled" | "draft";
  created_at?: string;
  published_at?: string;
  scheduled_for?: string;
  views?: number;
  likes: number;
  comments: number;
  reads?: number;
  category?: string;
}

function AuthorSidebar() {
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
            Author Panel
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={item.url}
                      end={item.url === "/dashboard"}
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
            <span className="font-semibold text-secondary">PC</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-foreground text-sm truncate">
              Pastor Chen
            </p>
            <p className="text-xs text-muted-foreground truncate">
              pastor@example.com
            </p>
          </div>
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

function DevotionalManagementContent() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch devotionals from API
  const { data: devotionalsData, isLoading } = useQuery({
    queryKey: ["author-devotionals", statusFilter === "all" ? null : statusFilter, searchQuery],
    queryFn: async () => {
      const response = await apiClient.client.get("/author/devotionals", {
        params: {
          status: statusFilter === "all" ? undefined : statusFilter,
          search: searchQuery || undefined,
          page: 1,
          page_size: 100,
        },
      });
      return response.data;
    },
  });

  const devotionals: Devotional[] = devotionalsData?.data?.devotionals || [];
  const totalDevotionals = devotionalsData?.data?.total || 0;

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.client.delete(`/devotionals/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["author-devotionals"] });
      toast({
        title: "Devotional deleted",
        description: "The devotional has been removed.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to delete devotional",
        variant: "destructive",
      });
    },
  });

  const handleDelete = (id: string) => {
    if (confirm("Are you sure you want to delete this devotional?")) {
      deleteMutation.mutate(id);
    }
  };

  const handleDuplicate = (devotional: Devotional) => {
    // Navigate to compose page with devotional data to duplicate
    navigate(`/dashboard/compose?duplicate=${devotional.id}`);
    toast({
      title: "Duplicating devotional",
      description: `Preparing to duplicate "${devotional.title}"`,
    });
  };

  const getStatusConfig = (status: string) => {
    switch (status) {
      case "published":
        return {
          icon: CheckCircle2,
          color: "text-accent bg-accent/10",
          label: "Published",
        };
      case "scheduled":
        return {
          icon: Clock,
          color: "text-secondary bg-secondary/10",
          label: "Scheduled",
        };
      case "draft":
        return {
          icon: FileText,
          color: "text-muted-foreground bg-muted",
          label: "Draft",
        };
      default:
        return {
          icon: XCircle,
          color: "text-muted-foreground bg-muted",
          label: status,
        };
    }
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
                placeholder="Search devotionals..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 w-64 h-9 bg-muted/50"
              />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="w-5 h-5" />
            </Button>
            <Button
              variant="hero"
              size="sm"
              className="gap-2"
              onClick={() => navigate("/dashboard/compose")}
            >
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
          {/* Header */}
          <div className="mb-6">
            <h1 className="font-serif text-3xl font-bold text-foreground mb-2">
              My Devotionals
            </h1>
            <p className="text-muted-foreground">
              Manage all your devotional content in one place
            </p>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-3 mb-6">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <Filter className="w-4 h-4 mr-2" />
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="published">Published</SelectItem>
                <SelectItem value="scheduled">Scheduled</SelectItem>
                <SelectItem value="draft">Drafts</SelectItem>
              </SelectContent>
            </Select>
            <div className="text-sm text-muted-foreground">
              {isLoading ? (
                "Loading..."
              ) : (
                <>
                  Showing {devotionals.length} of {totalDevotionals} devotionals
                </>
              )}
            </div>
          </div>

          {/* Devotionals Grid */}
          {isLoading ? (
            <div className="text-center py-12">
              <div className="inline-block w-8 h-8 border-4 border-secondary border-t-transparent rounded-full animate-spin" />
              <p className="mt-4 text-muted-foreground">Loading devotionals...</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {devotionals.map((devotional) => {
                const statusConfig = getStatusConfig(devotional.status);
                const excerpt = devotional.excerpt || 
                  (devotional.content ? devotional.content.substring(0, 150) + "..." : "");
                const date = devotional.published_at || devotional.scheduled_for || devotional.created_at;
                const views = devotional.views || devotional.reads || 0;
                
                return (
                  <motion.div
                    key={devotional.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-card rounded-2xl border border-border shadow-soft hover:shadow-elevated transition-all overflow-hidden"
                  >
                    <div className="p-6">
                      <div className="flex items-start justify-between gap-4 mb-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-2">
                            <span
                              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusConfig.color}`}
                            >
                              <statusConfig.icon className="w-3.5 h-3.5" />
                              {statusConfig.label}
                            </span>
                            {devotional.category && (
                              <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground">
                                {devotional.category}
                              </span>
                            )}
                          </div>
                          <h3 className="font-serif text-xl font-semibold text-foreground mb-2">
                            {devotional.title}
                          </h3>
                          {excerpt && (
                            <p className="text-sm text-muted-foreground line-clamp-2">
                              {excerpt}
                            </p>
                          )}
                        </div>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() =>
                                navigate(`/dashboard/compose/${devotional.id}`)
                              }
                            >
                              <Edit2 className="w-4 h-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleDuplicate(devotional)}
                            >
                              <Copy className="w-4 h-4 mr-2" />
                              Duplicate
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => navigate(`/devotional/${devotional.id}`)}
                            >
                              <Eye className="w-4 h-4 mr-2" />
                              Preview
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => handleDelete(devotional.id)}
                              className="text-destructive"
                              disabled={deleteMutation.isPending}
                            >
                              <Trash2 className="w-4 h-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>

                      <div className="flex items-center gap-6 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1.5">
                          <Calendar className="w-4 h-4" />
                          {date
                            ? devotional.status === "scheduled" && devotional.scheduled_for
                              ? `Scheduled for ${new Date(devotional.scheduled_for).toLocaleDateString()}`
                              : new Date(date).toLocaleDateString()
                            : "No date"}
                        </div>
                        {devotional.status === "published" && (
                          <>
                            {views > 0 && (
                              <div className="flex items-center gap-1.5">
                                <Eye className="w-4 h-4" />
                                {views.toLocaleString()} {devotional.reads ? "reads" : "views"}
                              </div>
                            )}
                            <div className="flex items-center gap-1.5">
                              <Heart className="w-4 h-4" />
                              {devotional.likes} likes
                            </div>
                            <div className="flex items-center gap-1.5">
                              <MessageCircle className="w-4 h-4" />
                              {devotional.comments} comments
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}

          {!isLoading && devotionals.length === 0 && (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="font-serif text-xl font-semibold text-foreground mb-2">
                No devotionals found
              </h3>
              <p className="text-muted-foreground mb-6">
                {searchQuery
                  ? "Try adjusting your search or filters"
                  : "Get started by creating your first devotional"}
              </p>
              {!searchQuery && (
                <Button
                  variant="hero"
                  onClick={() => navigate("/dashboard/compose")}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Devotional
                </Button>
              )}
            </div>
          )}
        </motion.div>
      </main>
    </div>
  );
}

const DevotionalManagement = () => {
  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-background">
        <AuthorSidebar />
        <DevotionalManagementContent />
      </div>
    </SidebarProvider>
  );
};

export default DevotionalManagement;
