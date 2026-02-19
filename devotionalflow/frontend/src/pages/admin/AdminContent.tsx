import { useState, useEffect, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Bell,
  MoreVertical,
  Eye,
  Edit,
  Trash2,
  CheckCircle,
  Clock,
  Download,
  FileText,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { AdminSidebar } from "@/components/admin/AdminSidebar";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import { useNavigate } from "react-router-dom";
import { logger } from "@/lib/logger";

interface DevotionalItem {
  id: string;
  title: string;
  author: string;
  status: 'draft' | 'scheduled' | 'published';
  views: number;
  likes: number;
  comments: number;
  created_at: string;
  published_at?: string;
}

export default function AdminContent() {
  const { toast } = useToast();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [devotionals, setDevotionals] = useState<DevotionalItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isDeleting, setIsDeleting] = useState(false);
  const [sortBy, setSortBy] = useState<'created_at' | 'published_at' | 'views_count' | 'likes_count' | 'title'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Infinite scroll state
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [totalItems, setTotalItems] = useState(0);
  const pageSize = 20; // Fixed page size for infinite scroll

  // Ref for intersection observer
  const loadMoreRef = useRef<HTMLDivElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  // Initial load when filters change
  useEffect(() => {
    // Reset and load from beginning
    setDevotionals([]);
    setCurrentPage(1);
    setHasMore(true);
    loadDevotionals(1, true);
  }, [statusFilter, sortBy, sortOrder]);

  const loadDevotionals = useCallback(async (page: number, isInitial: boolean = false) => {
    if (isInitial) {
      setLoading(true);
    } else {
      setLoadingMore(true);
    }

    try {
      // Backend only supports: created_at, published_at, views_count, likes_count
      // For 'title' sorting, we'll do it client-side
      const backendSortBy = sortBy === 'title' ? 'created_at' : sortBy;

      const response = await apiClient.getDevotionals({
        status: statusFilter === "all" ? undefined : (statusFilter as any),
        page: page,
        limit: pageSize,
        sort_by: backendSortBy,
        sort_order: sortOrder,
        search: searchQuery || undefined,
      });

      let items: DevotionalItem[] = response.items.map((item: any) => ({
        id: item.id,
        title: item.title,
        author: item.author_name || 'Unknown',
        status: item.status,
        views: item.views_count || 0,
        likes: item.likes_count || 0,
        comments: item.comments_count || 0,
        created_at: item.created_at,
        published_at: item.published_at,
      }));

      // Apply client-side sorting for 'title'
      if (sortBy === 'title') {
        items = items.sort((a, b) => {
          const comparison = a.title.localeCompare(b.title);
          return sortOrder === 'asc' ? comparison : -comparison;
        });
      }

      if (isInitial) {
        setDevotionals(items);
      } else {
        // Append to existing items for infinite scroll
        setDevotionals(prev => [...prev, ...items]);
      }

      setTotalItems(response.total || 0);

      // Check if there are more items to load
      const totalPages = response.total_pages || 1;
      setHasMore(page < totalPages);

    } catch (error: any) {
      logger.error('Failed to load devotionals:', error);

      // Check if it's an authentication error
      if (error.response?.status === 401) {
        toast({
          title: "Session Expired",
          description: "Please log in again to continue",
          variant: "destructive",
        });
        // Redirect will happen automatically via API client
      } else if (error.code === 'ECONNABORTED' || error.message?.includes('aborted')) {
        // Request was aborted, likely due to auth redirect - don't show error
        logger.debug('Request aborted - likely due to authentication redirect');
      } else {
        toast({
          title: "Error",
          description: error.response?.data?.detail || "Failed to load devotionals",
          variant: "destructive",
        });
      }
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [statusFilter, pageSize, toast, sortBy, sortOrder, searchQuery]);

  // Load more when user scrolls to bottom
  const loadMore = useCallback(() => {
    if (!loadingMore && !loading && hasMore) {
      const nextPage = currentPage + 1;
      setCurrentPage(nextPage);
      loadDevotionals(nextPage, false);
    }
  }, [currentPage, hasMore, loading, loadingMore, loadDevotionals]);

  // Set up intersection observer for infinite scroll
  useEffect(() => {
    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading && !loadingMore) {
          loadMore();
        }
      },
      { threshold: 0.1 }
    );

    if (loadMoreRef.current) {
      observerRef.current.observe(loadMoreRef.current);
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [hasMore, loading, loadingMore, loadMore]);

  const handleDeleteDevotional = async (id: string) => {
    if (!confirm("Are you sure you want to delete this devotional?")) return;

    setIsDeleting(true);
    try {
      await apiClient.deleteDevotional(id);

      toast({
        title: "Devotional deleted",
        description: "The devotional has been deleted successfully.",
      });

      // Small delay to ensure deletion propagates on backend
      await new Promise(resolve => setTimeout(resolve, 300));

      // Reload from beginning to ensure pagination consistency
      setDevotionals([]);
      setCurrentPage(1);
      setHasMore(true);
      setSelectedIds(new Set()); // Clear selection
      loadDevotionals(1, true);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete devotional",
        variant: "destructive",
      });
      // Reload on error to get correct state
      setDevotionals([]);
      setCurrentPage(1);
      setHasMore(true);
      loadDevotionals(1, true);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) {
      toast({
        title: "No selection",
        description: "Please select devotionals to delete",
        variant: "destructive",
      });
      return;
    }

    if (!confirm(`Are you sure you want to delete ${selectedIds.size} devotional(s)?`)) {
      return;
    }

    setIsDeleting(true);
    try {
      const response = await apiClient.client.post('/devotionals/bulk-delete', {
        devotional_ids: Array.from(selectedIds),
      });

      const result = response.data;

      // Clear selection
      setSelectedIds(new Set());

      toast({
        title: "Bulk delete completed",
        description: `${result.deleted_count} devotional(s) deleted successfully.${
          result.failed_ids.length > 0 ? ` ${result.failed_ids.length} failed.` : ''
        }`,
      });

      // Small delay to ensure deletions propagate on backend
      await new Promise(resolve => setTimeout(resolve, 300));

      // Reload from beginning to ensure pagination consistency
      setDevotionals([]);
      setCurrentPage(1);
      setHasMore(true);
      loadDevotionals(1, true);
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to delete devotionals",
        variant: "destructive",
      });
      // Reload on error to get correct state
      setDevotionals([]);
      setCurrentPage(1);
      setHasMore(true);
      loadDevotionals(1, true);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(new Set(filteredDevotionals.map(d => d.id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleSelectOne = (id: string, checked: boolean) => {
    const newSelected = new Set(selectedIds);
    if (checked) {
      newSelected.add(id);
    } else {
      newSelected.delete(id);
    }
    setSelectedIds(newSelected);
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, any> = {
      published: { variant: "default", icon: CheckCircle, color: "text-green-500" },
      scheduled: { variant: "secondary", icon: Clock, color: "text-blue-500" },
      draft: { variant: "outline", icon: Edit, color: "text-gray-500" },
    };

    const config = variants[status] || variants.draft;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="gap-1">
        <Icon className={`w-3 h-3 ${config.color}`} />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  // Client-side filtering is now handled by API, but we keep this for immediate UI feedback
  // Memoized to prevent recalculation on every render
  const filteredDevotionals = useMemo(() => {
    if (!searchQuery) return devotionals;
    return devotionals.filter(dev =>
      dev.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      dev.author.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [devotionals, searchQuery]);

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-background">
        <AdminSidebar />

        <div className="flex-1 overflow-auto">
          {/* Header */}
          <header className="sticky top-0 z-10 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60">
            <div className="flex h-16 items-center gap-4 px-6">
              <SidebarTrigger className="md:hidden" />
              <div className="flex-1">
                <h1 className="text-xl font-serif font-bold text-foreground">Content Management</h1>
                <p className="text-sm text-muted-foreground">Manage all devotionals on the platform</p>
              </div>
              <Button variant="outline" size="icon">
                <Bell className="w-4 h-4" />
              </Button>
            </div>
          </header>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-card rounded-xl border border-border p-6"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">
                      {statusFilter === "all" ? "Total Devotionals" : `${statusFilter.charAt(0).toUpperCase() + statusFilter.slice(1)} Devotionals`}
                    </p>
                    <h3 className="text-2xl font-bold text-foreground mt-1">
                      {totalItems}
                    </h3>
                  </div>
                  <FileText className="w-8 h-8 text-secondary" />
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="bg-card rounded-xl border border-border p-6"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Loaded</p>
                    <h3 className="text-2xl font-bold text-foreground mt-1">
                      {devotionals.length}
                    </h3>
                  </div>
                  <CheckCircle className="w-8 h-8 text-green-500" />
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-card rounded-xl border border-border p-6"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Progress</p>
                    <h3 className="text-2xl font-bold text-foreground mt-1">
                      {totalItems > 0 ? Math.round((devotionals.length / totalItems) * 100) : 0}%
                    </h3>
                  </div>
                  <Clock className="w-8 h-8 text-blue-500" />
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-card rounded-xl border border-border p-6"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Selected</p>
                    <h3 className="text-2xl font-bold text-foreground mt-1">
                      {selectedIds.size}
                    </h3>
                  </div>
                  <Edit className="w-8 h-8 text-gray-500" />
                </div>
              </motion.div>
            </div>

            {/* Filters & Search */}
            <div className="bg-card rounded-xl border border-border p-4">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Search devotionals by title or author..."
                    value={searchQuery}
                    onChange={(e) => {
                      const value = e.target.value;
                      setSearchQuery(value);
                      // Debounce search - reload after user stops typing
                      if (searchTimeoutRef.current) {
                        clearTimeout(searchTimeoutRef.current);
                      }
                      searchTimeoutRef.current = setTimeout(() => {
                        setDevotionals([]);
                        setCurrentPage(1);
                        setHasMore(true);
                        loadDevotionals(1, true);
                      }, 500);
                    }}
                    className="pl-10"
                  />
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-full md:w-48">
                    <SelectValue placeholder="Filter by status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="published">Published</SelectItem>
                    <SelectItem value="scheduled">Scheduled</SelectItem>
                    <SelectItem value="draft">Draft</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={sortBy} onValueChange={(v) => setSortBy(v as any)}>
                  <SelectTrigger className="w-full md:w-40">
                    <SelectValue placeholder="Sort by" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="created_at">Created Date</SelectItem>
                    <SelectItem value="published_at">Published Date</SelectItem>
                    <SelectItem value="views_count">Views</SelectItem>
                    <SelectItem value="likes_count">Likes</SelectItem>
                    <SelectItem value="title">Title</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={sortOrder} onValueChange={(v) => setSortOrder(v as any)}>
                  <SelectTrigger className="w-full md:w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="desc">Descending</SelectItem>
                    <SelectItem value="asc">Ascending</SelectItem>
                  </SelectContent>
                </Select>
                {selectedIds.size > 0 && (
                  <Button
                    variant="destructive"
                    onClick={handleBulkDelete}
                    disabled={isDeleting}
                  >
                    {isDeleting ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4 mr-2" />
                    )}
                    {isDeleting ? "Deleting..." : `Delete Selected (${selectedIds.size})`}
                  </Button>
                )}
                <Button variant="outline">
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </Button>
              </div>
            </div>

            {/* Devotionals Table */}
            <div className="bg-card rounded-xl border border-border overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        checked={filteredDevotionals.length > 0 && selectedIds.size === filteredDevotionals.length}
                        onCheckedChange={handleSelectAll}
                        aria-label="Select all"
                      />
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => {
                        if (sortBy === 'title') {
                          setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                        } else {
                          setSortBy('title');
                          setSortOrder('asc');
                        }
                      }}
                    >
                      Title {sortBy === 'title' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </TableHead>
                    <TableHead>Author</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead 
                      className="text-right cursor-pointer hover:bg-muted/50"
                      onClick={() => {
                        if (sortBy === 'views_count') {
                          setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                        } else {
                          setSortBy('views_count');
                          setSortOrder('desc');
                        }
                      }}
                    >
                      Views {sortBy === 'views_count' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </TableHead>
                    <TableHead 
                      className="text-right cursor-pointer hover:bg-muted/50"
                      onClick={() => {
                        if (sortBy === 'likes_count') {
                          setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                        } else {
                          setSortBy('likes_count');
                          setSortOrder('desc');
                        }
                      }}
                    >
                      Likes {sortBy === 'likes_count' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </TableHead>
                    <TableHead className="text-right">Comments</TableHead>
                    <TableHead 
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => {
                        if (sortBy === 'created_at') {
                          setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                        } else {
                          setSortBy('created_at');
                          setSortOrder('desc');
                        }
                      }}
                    >
                      Created {sortBy === 'created_at' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                        Loading devotionals...
                      </TableCell>
                    </TableRow>
                  ) : filteredDevotionals.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                        No devotionals found
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredDevotionals.map((devotional) => (
                      <TableRow
                        key={devotional.id}
                        className="cursor-pointer hover:bg-muted/50 transition-colors"
                        onClick={() => navigate(`/devotional/${devotional.id}`)}
                      >
                        <TableCell onClick={(e) => e.stopPropagation()}>
                          <Checkbox
                            checked={selectedIds.has(devotional.id)}
                            onCheckedChange={(checked) => handleSelectOne(devotional.id, checked as boolean)}
                            aria-label={`Select ${devotional.title}`}
                          />
                        </TableCell>
                        <TableCell className="font-medium max-w-xs truncate">
                          {devotional.title}
                        </TableCell>
                        <TableCell>{devotional.author}</TableCell>
                        <TableCell>{getStatusBadge(devotional.status)}</TableCell>
                        <TableCell className="text-right">{devotional.views.toLocaleString()}</TableCell>
                        <TableCell className="text-right">{devotional.likes.toLocaleString()}</TableCell>
                        <TableCell className="text-right">{devotional.comments.toLocaleString()}</TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {new Date(devotional.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreVertical className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuLabel>Actions</DropdownMenuLabel>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem onClick={() => navigate(`/devotional/${devotional.id}`)}>
                                <Eye className="w-4 h-4 mr-2" />
                                View
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <Edit className="w-4 h-4 mr-2" />
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                className="text-destructive"
                                onClick={() => handleDeleteDevotional(devotional.id)}
                                disabled={isDeleting}
                              >
                                {isDeleting ? (
                                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                ) : (
                                  <Trash2 className="w-4 h-4 mr-2" />
                                )}
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Infinite Scroll Loading Indicator */}
            {!loading && devotionals.length > 0 && (
              <div ref={loadMoreRef} className="flex justify-center py-8">
                {loadingMore ? (
                  <div className="flex flex-col items-center gap-3">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    <p className="text-sm text-muted-foreground">Loading more devotionals...</p>
                  </div>
                ) : hasMore ? (
                  <div className="text-sm text-muted-foreground">
                    Scroll down to load more
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-2 text-center">
                    <CheckCircle className="w-8 h-8 text-green-500" />
                    <p className="text-sm font-medium text-foreground">All devotionals loaded</p>
                    <p className="text-xs text-muted-foreground">
                      Showing all {devotionals.length} of {totalItems} devotionals
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </SidebarProvider>
  );
}
