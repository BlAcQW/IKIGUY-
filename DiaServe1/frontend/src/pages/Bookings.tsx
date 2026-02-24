import { useState, useMemo, useEffect } from "react";
import {
  Calendar,
  Plus,
  Clock,
  User,
  Building2,
  MoreHorizontal,
  ChevronLeft,
  ChevronRight,
  Filter,
  X,
  Loader2,
  CheckSquare,
  Square,
  CheckCircle,
  XCircle,
  Users,
  FileText,
  Shield,
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useBookings, useCompleteBooking } from "@/hooks/use-bookings";
import { BookingStatus, BookingType, Booking } from "@/lib/api/booking-api";
import { format, isToday, isTomorrow, isThisWeek, isThisMonth, startOfDay, endOfDay } from "date-fns";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/components/ui/use-toast";
import { AdminBookingDialog } from "@/components/admin/AdminBookingDialog";
import { AgentReassignDialog } from "@/components/admin/AgentReassignDialog";
import { BookingActionLogsDialog } from "@/components/admin/BookingActionLogsDialog";
import { useAdminBulkAction } from "@/hooks/use-bookings";

export default function Bookings() {
  const { toast } = useToast();
  const { user } = useAuth(); // Use auth hook
  const [statusFilter, setStatusFilter] = useState<BookingStatus | "all">("all");
  const [typeFilter, setTypeFilter] = useState<BookingType | "all">("all");
  const [dateFilter, setDateFilter] = useState<"all" | "today" | "week" | "month">("all");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // Admin state
  const [isAdmin, setIsAdmin] = useState(false);
  const [selectedBookings, setSelectedBookings] = useState<Set<string>>(new Set());
  const [showAdminDialog, setShowAdminDialog] = useState(false);
  const [showReassignDialog, setShowReassignDialog] = useState(false);
  const [showActionLogsDialog, setShowActionLogsDialog] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState<Booking | undefined>();

  // Admin bulk action mutation
  const bulkActionMutation = useAdminBulkAction();

  // Complete booking mutation
  const completeBookingMutation = useCompleteBooking();

  // Check if user is admin
  useEffect(() => {
    if (user) {
      const isAdminUser =
        user.email === "admin@ailabsafrica.com" ||
        (user as any).user_metadata?.role === "admin" ||
        (user as any).app_metadata?.role === "admin" ||
        (user as any).role === "admin"; // Check for role directly
      setIsAdmin(!!isAdminUser);
    }
  }, [user]);

  // Build filters for API call
  const filters = useMemo(() => {
    const baseFilters: any = {
      limit: itemsPerPage,
      offset: (currentPage - 1) * itemsPerPage,
    };

    if (statusFilter !== "all") {
      baseFilters.status = statusFilter;
    }

    if (dateFilter === "today") {
      baseFilters.start_date = format(startOfDay(new Date()), "yyyy-MM-dd'T'HH:mm:ss");
      baseFilters.end_date = format(endOfDay(new Date()), "yyyy-MM-dd'T'HH:mm:ss");
    } else if (dateFilter === "week") {
      baseFilters.start_date = format(new Date(), "yyyy-MM-dd'T'HH:mm:ss");
      const weekEnd = new Date();
      weekEnd.setDate(weekEnd.getDate() + 7);
      baseFilters.end_date = format(weekEnd, "yyyy-MM-dd'T'HH:mm:ss");
    } else if (dateFilter === "month") {
      baseFilters.start_date = format(new Date(), "yyyy-MM-dd'T'HH:mm:ss");
      const monthEnd = new Date();
      monthEnd.setMonth(monthEnd.getMonth() + 1);
      baseFilters.end_date = format(monthEnd, "yyyy-MM-dd'T'HH:mm:ss");
    }

    return baseFilters;
  }, [statusFilter, dateFilter, currentPage]);

  // Fetch bookings with filters
  const { data, isLoading, error } = useBookings(filters);

  // Filter by type on client side (since API doesn't support it directly)
  const filteredBookings = useMemo(() => {
    if (!data?.bookings) return [];
    if (typeFilter === "all") return data.bookings;
    return data.bookings.filter((b) => b.booking_type === typeFilter);
  }, [data?.bookings, typeFilter]);

  // Calculate stats from real data
  const stats = useMemo(() => {
    if (!data?.bookings) {
      return [
        { name: "Today's Bookings", value: "0" },
        { name: "This Week", value: "0" },
        { name: "Pending Confirmation", value: "0" },
        { name: "Completed This Month", value: "0" },
      ];
    }

    const today = data.bookings.filter((b) => isToday(new Date(b.scheduled_at)));
    const thisWeek = data.bookings.filter((b) => isThisWeek(new Date(b.scheduled_at)));
    const pending = data.bookings.filter((b) => b.status === "requested");
    const completed = data.bookings.filter(
      (b) => b.status === "completed" && isThisMonth(new Date(b.completed_at || b.updated_at))
    );

    // Admin-specific stats
    if (isAdmin) {
      const overriddenToday = data.bookings.filter(
        (b) => b.admin_override && isToday(new Date(b.created_at))
      );

      return [
        { name: "Today's Bookings", value: today.length.toString() },
        { name: "This Week", value: thisWeek.length.toString() },
        { name: "Pending Admin Action", value: pending.length.toString(), icon: Shield },
        { name: "Overridden Today", value: overriddenToday.length.toString(), icon: Shield },
      ];
    }

    return [
      { name: "Today's Bookings", value: today.length.toString() },
      { name: "This Week", value: thisWeek.length.toString() },
      { name: "Pending Confirmation", value: pending.length.toString() },
      { name: "Completed This Month", value: completed.length.toString() },
    ];
  }, [data?.bookings, isAdmin]);

  const getStatusColor = (status: BookingStatus) => {
    switch (status) {
      case "confirmed":
        return "soft-success";
      case "requested":
        return "soft-warning";
      case "cancelled":
        return "soft-destructive";
      case "completed":
        return "soft";
      case "no-show":
        return "soft-destructive";
      default:
        return "soft";
    }
  };

  const getTypeColor = (type: BookingType) => {
    switch (type) {
      case "in-person":
        return "soft";
      case "virtual":
        return "soft-success";
      default:
        return "soft";
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    if (isToday(date)) return "Today";
    if (isTomorrow(date)) return "Tomorrow";
    return format(date, "MMM d");
  };

  const formatTime = (dateString: string, durationMinutes: number) => {
    const start = new Date(dateString);
    const end = new Date(start.getTime() + durationMinutes * 60000);
    return `${format(start, "h:mm a")} - ${format(end, "h:mm a")}`;
  };

  const hasActiveFilters = statusFilter !== "all" || typeFilter !== "all" || dateFilter !== "all";

  const clearFilters = () => {
    setStatusFilter("all");
    setTypeFilter("all");
    setDateFilter("all");
    setCurrentPage(1);
  };

  // Admin functions
  const handleSelectAll = () => {
    if (selectedBookings.size === filteredBookings.length) {
      // Deselect all
      setSelectedBookings(new Set());
    } else {
      // Select all
      setSelectedBookings(new Set(filteredBookings.map((b) => b.id)));
    }
  };

  const handleSelectBooking = (bookingId: string) => {
    const newSelected = new Set(selectedBookings);
    if (newSelected.has(bookingId)) {
      newSelected.delete(bookingId);
    } else {
      newSelected.add(bookingId);
    }
    setSelectedBookings(newSelected);
  };

  const handleBulkAction = async (action: "approve" | "reschedule" | "cancel") => {
    if (selectedBookings.size === 0) {
      toast({
        title: "No bookings selected",
        description: "Please select at least one booking to perform this action.",
        variant: "destructive",
      });
      return;
    }

    try {
      const result = await bulkActionMutation.mutateAsync({
        booking_ids: Array.from(selectedBookings),
        action,
        reason: `Bulk ${action} action from admin dashboard`,
      });

      toast({
        title: "Success",
        description: result.message,
      });

      // Clear selection
      setSelectedBookings(new Set());
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to perform bulk action",
        variant: "destructive",
      });
    }
  };

  const handleReassignAgent = (booking: Booking) => {
    setSelectedBooking(booking);
    setShowReassignDialog(true);
  };

  const handleViewActionLogs = (booking: Booking) => {
    setSelectedBooking(booking);
    setShowActionLogsDialog(true);
  };

  const handleCompleteBooking = async (booking: Booking) => {
    try {
      await completeBookingMutation.mutateAsync({ bookingId: booking.id });
      toast({
        title: "Success",
        description: `Tour for ${booking.contact_name} marked as complete.`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to complete booking",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen">
      <Header
        title="Bookings"
        subtitle="Manage property tours and appointments"
        actions={
          isAdmin ? (
            <Button variant="gradient" className="gap-2" onClick={() => setShowAdminDialog(true)}>
              <Plus className="h-4 w-4" />
              Manual Create Booking
            </Button>
          ) : (
            <Button variant="gradient" className="gap-2">
              <Plus className="h-4 w-4" />
              New Booking
            </Button>
          )
        }
      />

      <div className="p-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {stats.map((stat, index) => (
            <Card
              key={stat.name}
              variant="elevated"
              className="group overflow-hidden animate-scale-in hover:border-primary/30"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 group-hover:from-primary/30 group-hover:to-secondary/30 transition-all duration-200 shadow-inner-soft">
                    {stat.icon ? (
                      <stat.icon className="h-6 w-6 text-primary" />
                    ) : (
                      <Calendar className="h-6 w-6 text-primary" />
                    )}
                  </div>
                </div>
                <p className="text-3xl font-bold text-foreground mb-1">{stat.value}</p>
                <p className="text-sm text-muted-foreground">{stat.name}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Bulk Action Toolbar (Admin Only) */}
        {isAdmin && selectedBookings.size > 0 && (
          <Card variant="elevated" className="border-primary/50 bg-primary/5">
            <CardContent className="p-4">
              <div className="flex items-center justify-between gap-4 flex-wrap">
                <div className="flex items-center gap-2">
                  <CheckSquare className="h-5 w-5 text-primary" />
                  <span className="font-medium">
                    {selectedBookings.size} booking{selectedBookings.size !== 1 ? "s" : ""} selected
                  </span>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => handleBulkAction("approve")}
                    disabled={bulkActionMutation.isPending}
                    className="gap-1"
                  >
                    <CheckCircle className="h-4 w-4" />
                    Approve Selected
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleBulkAction("reschedule")}
                    disabled={bulkActionMutation.isPending}
                    className="gap-1 border-warning text-warning hover:bg-warning/10"
                  >
                    <Clock className="h-4 w-4" />
                    Reschedule Selected
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleBulkAction("cancel")}
                    disabled={bulkActionMutation.isPending}
                    className="gap-1"
                  >
                    <X className="h-4 w-4" />
                    Cancel Selected
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedBookings(new Set())}
                    className="gap-1"
                  >
                    Clear Selection
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Filters */}
        <Card variant="elevated">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">Filters:</span>
              </div>

              {/* Select All Checkbox (Admin Only) */}
              {isAdmin && filteredBookings.length > 0 && (
                <>
                  <div className="flex items-center gap-2">
                    <Checkbox
                      checked={
                        selectedBookings.size === filteredBookings.length && filteredBookings.length > 0
                      }
                      onCheckedChange={handleSelectAll}
                    />
                    <span className="text-sm">Select All</span>
                  </div>
                  <div className="h-4 w-px bg-border" />
                </>
              )}

              {/* Date Filter */}
              <div className="flex gap-2">
                <Button
                  variant={dateFilter === "all" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setDateFilter("all")}
                >
                  All
                </Button>
                <Button
                  variant={dateFilter === "today" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setDateFilter("today")}
                >
                  Today
                </Button>
                <Button
                  variant={dateFilter === "week" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setDateFilter("week")}
                >
                  This Week
                </Button>
                <Button
                  variant={dateFilter === "month" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setDateFilter("month")}
                >
                  This Month
                </Button>
              </div>

              <div className="h-4 w-px bg-border" />

              {/* Status Filter */}
              <div className="flex gap-2">
                <Button
                  variant={statusFilter === "all" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setStatusFilter("all")}
                >
                  All Status
                </Button>
                <Button
                  variant={statusFilter === "requested" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setStatusFilter("requested")}
                >
                  Requested
                </Button>
                <Button
                  variant={statusFilter === "confirmed" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setStatusFilter("confirmed")}
                >
                  Confirmed
                </Button>
                <Button
                  variant={statusFilter === "completed" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setStatusFilter("completed")}
                >
                  Completed
                </Button>
              </div>

              <div className="h-4 w-px bg-border" />

              {/* Type Filter */}
              <div className="flex gap-2">
                <Button
                  variant={typeFilter === "all" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setTypeFilter("all")}
                >
                  All Types
                </Button>
                <Button
                  variant={typeFilter === "in-person" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setTypeFilter("in-person")}
                >
                  In-Person
                </Button>
                <Button
                  variant={typeFilter === "virtual" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setTypeFilter("virtual")}
                >
                  Virtual
                </Button>
              </div>

              {hasActiveFilters && (
                <>
                  <div className="h-4 w-px bg-border" />
                  <Button variant="ghost" size="sm" onClick={clearFilters} className="gap-1">
                    <X className="h-3 w-3" />
                    Clear Filters
                  </Button>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Bookings List */}
        <Card variant="elevated" className="animate-slide-up-fade">
          <CardHeader>
            <CardTitle>
              {dateFilter === "today"
                ? "Today's Bookings"
                : dateFilter === "week"
                  ? "This Week's Bookings"
                  : dateFilter === "month"
                    ? "This Month's Bookings"
                    : "All Bookings"}
            </CardTitle>
            <CardDescription>
              {isLoading
                ? "Loading..."
                : error
                  ? "Error loading bookings"
                  : `Showing ${filteredBookings.length} of ${data?.total || 0} bookings`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
            ) : error ? (
              <div className="text-center py-8 text-destructive">
                Failed to load bookings. Please try again.
              </div>
            ) : filteredBookings.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No bookings found. {hasActiveFilters && "Try adjusting your filters."}
              </div>
            ) : (
              <>
                {filteredBookings.map((booking, index) => (
                  <div
                    key={booking.id}
                    className="flex items-center gap-4 p-4 rounded-xl border border-border hover:bg-secondary/50 hover:border-primary/30 transition-all duration-200 group animate-slide-up-fade"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    {/* Admin Checkbox */}
                    {isAdmin && (
                      <Checkbox
                        checked={selectedBookings.has(booking.id)}
                        onCheckedChange={() => handleSelectBooking(booking.id)}
                      />
                    )}

                    <div className="flex h-14 w-14 flex-col items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 text-primary shadow-inner-soft group-hover:from-primary/30 group-hover:to-secondary/30 transition-all">
                      <Calendar className="h-5 w-5" />
                      <span className="text-xs font-medium mt-0.5">
                        {formatDate(booking.scheduled_at)}
                      </span>
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="font-medium text-foreground">
                          {booking.booking_type === "in-person" ? "Property Tour" : "Virtual Tour"}
                        </h4>
                        <Badge variant={getTypeColor(booking.booking_type) as any}>
                          {booking.booking_type}
                        </Badge>
                        <Badge variant={getStatusColor(booking.status) as any}>
                          {booking.status}
                        </Badge>
                        {booking.admin_override && (
                          <Badge variant="outline" className="gap-1">
                            <Shield className="h-3 w-3" />
                            Override
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground flex-wrap">
                        <span className="flex items-center gap-1">
                          <User className="h-3.5 w-3.5" />
                          {booking.contact_name}
                        </span>
                        <span className="flex items-center gap-1">
                          <Building2 className="h-3.5 w-3.5" />
                          {booking.property_name || `Property #${booking.property_id.slice(-6)}`}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5" />
                          {formatTime(booking.scheduled_at, booking.duration_minutes)}
                        </span>
                        {booking.contact_phone && (
                          <span className="flex items-center gap-1">
                            📱 {booking.contact_phone}
                          </span>
                        )}
                        {booking.contact_email && (
                          <span className="flex items-center gap-1">
                            ✉️ {booking.contact_email}
                          </span>
                        )}
                      </div>
                      {booking.notes && (
                        <div className="mt-2 text-sm text-muted-foreground">
                          <span className="font-medium">Notes:</span> {booking.notes}
                        </div>
                      )}
                    </div>

                    {/* Action Menu */}
                    {isAdmin ? (
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon-sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleReassignAgent(booking)}>
                            <Users className="h-4 w-4 mr-2" />
                            Reassign Agent
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleViewActionLogs(booking)}>
                            <FileText className="h-4 w-4 mr-2" />
                            View Action Logs
                          </DropdownMenuItem>
                          {booking.status === "requested" && (
                            <DropdownMenuItem
                              onClick={() =>
                                handleBulkAction("approve")
                              }
                            >
                              <CheckCircle className="h-4 w-4 mr-2" />
                              Override & Confirm
                            </DropdownMenuItem>
                          )}
                          {booking.status === "confirmed" && (
                            <DropdownMenuItem onClick={() => handleCompleteBooking(booking)}>
                              <CheckCircle className="h-4 w-4 mr-2" />
                              Mark as Complete
                            </DropdownMenuItem>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    ) : (
                      <Button variant="ghost" size="icon-sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                ))}

                {/* Pagination */}
                {data && data.total > itemsPerPage && (
                  <div className="flex items-center justify-between pt-4 border-t">
                    <p className="text-sm text-muted-foreground">
                      Showing {(currentPage - 1) * itemsPerPage + 1} to{" "}
                      {Math.min(currentPage * itemsPerPage, data.total)} of {data.total} bookings
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                      >
                        <ChevronLeft className="h-4 w-4" />
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage((p) => p + 1)}
                        disabled={currentPage * itemsPerPage >= data.total}
                      >
                        Next
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Admin Dialogs */}
      {isAdmin && (
        <>
          <AdminBookingDialog
            open={showAdminDialog}
            onOpenChange={setShowAdminDialog}
            properties={[]} // TODO: Fetch properties
            agents={[]} // TODO: Fetch agents
            onSuccess={() => {
              // Refresh bookings list
              window.location.reload();
            }}
          />

          <AgentReassignDialog
            open={showReassignDialog}
            onOpenChange={setShowReassignDialog}
            booking={selectedBooking}
            agents={[]} // TODO: Fetch agents
            onSuccess={() => {
              setSelectedBooking(undefined);
              window.location.reload();
            }}
          />

          <BookingActionLogsDialog
            open={showActionLogsDialog}
            onOpenChange={setShowActionLogsDialog}
            bookingId={selectedBooking?.id}
          />
        </>
      )}
    </div>
  );
}
