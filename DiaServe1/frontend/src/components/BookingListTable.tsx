/**
 * BookingListTable Component
 *
 * Displays list of bookings with status badges and actions.
 */

import { useState } from "react";
import {
  Calendar,
  Clock,
  User,
  MapPin,
  MoreVertical,
  CheckCircle,
  XCircle,
  Edit,
  Star,
} from "lucide-react";
import { useBookings, useCancelBooking, useConfirmBooking } from "../hooks/use-bookings";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Skeleton } from "./ui/skeleton";
import { useToast } from "./ui/use-toast";
import type { BookingStatus, BookingFilters } from "../lib/api/booking-api";

interface BookingListTableProps {
  filters?: BookingFilters;
  onEditBooking?: (bookingId: string) => void;
  onViewDetails?: (bookingId: string) => void;
}

export function BookingListTable({
  filters,
  onEditBooking,
  onViewDetails,
}: BookingListTableProps) {
  const { toast } = useToast();
  const { data, isLoading, error } = useBookings(filters);
  const cancelMutation = useCancelBooking();
  const confirmMutation = useConfirmBooking();

  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const handleCancel = async (bookingId: string) => {
    if (!confirm("Are you sure you want to cancel this booking?")) return;

    setActionLoading(bookingId);
    try {
      await cancelMutation.mutateAsync(bookingId);
      toast({
        title: "Success",
        description: "Booking cancelled successfully",
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to cancel booking",
        variant: "destructive",
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleConfirm = async (bookingId: string) => {
    setActionLoading(bookingId);
    try {
      await confirmMutation.mutateAsync(bookingId);
      toast({
        title: "Success",
        description: "Booking confirmed successfully",
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to confirm booking",
        variant: "destructive",
      });
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusBadge = (status: BookingStatus) => {
    const variants: Record<BookingStatus, { variant: any; label: string }> = {
      requested: { variant: "secondary", label: "Requested" },
      confirmed: { variant: "default", label: "Confirmed" },
      rescheduled: { variant: "outline", label: "Rescheduled" },
      completed: { variant: "success", label: "Completed" },
      cancelled: { variant: "destructive", label: "Cancelled" },
      "no-show": { variant: "warning", label: "No Show" },
    };

    const config = variants[status] || variants.requested;
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  const formatDuration = (minutes: number) => {
    if (minutes < 60) return `${minutes}min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`;
  };

  if (error) {
    return (
      <div className="text-center py-12 text-red-600">
        <p>Failed to load bookings</p>
        <p className="text-sm text-gray-500">{error.message}</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    );
  }

  if (!data || data.bookings.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <Calendar className="h-12 w-12 mx-auto mb-4 opacity-20" />
        <p className="text-lg font-medium">No bookings found</p>
        <p className="text-sm">
          {filters ? "Try adjusting your filters" : "Create your first booking to get started"}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Property</TableHead>
              <TableHead>Contact</TableHead>
              <TableHead>Scheduled</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Rating</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.bookings.map((booking) => (
              <TableRow key={booking.id}>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-gray-400" />
                    <span className="font-medium">Property #{booking.property_id.slice(-6)}</span>
                  </div>
                </TableCell>

                <TableCell>
                  <div>
                    <div className="flex items-center gap-2">
                      <User className="h-4 w-4 text-gray-400" />
                      <span className="font-medium">{booking.contact_name}</span>
                    </div>
                    {booking.contact_email && (
                      <div className="text-sm text-gray-500">{booking.contact_email}</div>
                    )}
                  </div>
                </TableCell>

                <TableCell>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-gray-400" />
                    <span className="text-sm">{formatDateTime(booking.scheduled_at)}</span>
                  </div>
                </TableCell>

                <TableCell>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-gray-400" />
                    <span className="text-sm">{formatDuration(booking.duration_minutes)}</span>
                  </div>
                </TableCell>

                <TableCell>
                  <Badge variant="outline">
                    {booking.booking_type === "in-person" ? "In-Person" : "Virtual"}
                  </Badge>
                </TableCell>

                <TableCell>{getStatusBadge(booking.status)}</TableCell>

                <TableCell>
                  {booking.rating ? (
                    <div className="flex items-center gap-1">
                      <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                      <span className="text-sm font-medium">{booking.rating}</span>
                    </div>
                  ) : (
                    <span className="text-sm text-gray-400">-</span>
                  )}
                </TableCell>

                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={actionLoading === booking.id}
                      >
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => onViewDetails?.(booking.id)}>
                        View Details
                      </DropdownMenuItem>

                      {booking.status === "requested" && (
                        <>
                          <DropdownMenuItem onClick={() => handleConfirm(booking.id)}>
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Confirm
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => onEditBooking?.(booking.id)}>
                            <Edit className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                        </>
                      )}

                      {["requested", "confirmed"].includes(booking.status) && (
                        <DropdownMenuItem
                          onClick={() => handleCancel(booking.id)}
                          className="text-red-600"
                        >
                          <XCircle className="h-4 w-4 mr-2" />
                          Cancel
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination Info */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <div>
          Showing <span className="font-medium">{data.bookings.length}</span> of{" "}
          <span className="font-medium">{data.total}</span> bookings
        </div>
        {data.total > data.limit && (
          <div>
            Page {Math.floor(data.offset / data.limit) + 1} of{" "}
            {Math.ceil(data.total / data.limit)}
          </div>
        )}
      </div>
    </div>
  );
}
