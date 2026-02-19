/**
 * BookingActionLogsDialog Component
 *
 * Admin-only modal for viewing audit trail of admin actions on a booking.
 *
 * Features:
 * - Timeline view of all admin actions
 * - Color-coded action types with badges
 * - Relative and absolute timestamps
 * - Action details (formatted JSON or key points)
 * - Empty state for bookings without admin actions
 */

import { formatDistanceToNow } from "date-fns";
import {
  Clock,
  User,
  FileEdit,
  Users,
  CheckCircle,
  XCircle,
  AlertCircle,
  Activity,
} from "lucide-react";
import { useBookingActionLogs } from "../../hooks/use-bookings";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Badge } from "../ui/badge";
import { ScrollArea } from "../ui/scroll-area";
import { Skeleton } from "../ui/skeleton";
import { Alert, AlertDescription } from "../ui/alert";
import type { ActionLog } from "../../lib/api/booking-api";

interface BookingActionLogsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  bookingId?: string;
}

export function BookingActionLogsDialog({
  open,
  onOpenChange,
  bookingId,
}: BookingActionLogsDialogProps) {
  const { data: logs, isLoading, error } = useBookingActionLogs(bookingId || "", !!bookingId);

  const getActionIcon = (actionType: string) => {
    if (actionType.includes("approve") || actionType.includes("confirm")) {
      return <CheckCircle className="h-4 w-4" />;
    }
    if (actionType.includes("reject") || actionType.includes("cancel")) {
      return <XCircle className="h-4 w-4" />;
    }
    if (actionType.includes("reassign")) {
      return <Users className="h-4 w-4" />;
    }
    if (actionType.includes("manual_create") || actionType.includes("override")) {
      return <FileEdit className="h-4 w-4" />;
    }
    return <Activity className="h-4 w-4" />;
  };

  const getActionBadgeVariant = (actionType: string): "default" | "secondary" | "destructive" | "outline" => {
    if (actionType.includes("approve") || actionType.includes("confirm")) {
      return "default";
    }
    if (actionType.includes("reject") || actionType.includes("cancel")) {
      return "destructive";
    }
    if (actionType.includes("reassign")) {
      return "secondary";
    }
    return "outline";
  };

  const formatActionType = (actionType: string): string => {
    return actionType
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const formatActionDetails = (log: ActionLog): string[] => {
    const details: string[] = [];

    if (log.details.override_availability) {
      details.push(`Override: ${log.details.override_availability ? "Yes" : "No"}`);
    }

    if (log.details.old_agent_id && log.details.new_agent_id) {
      details.push(`From: ${log.details.old_agent_id}`);
      details.push(`To: ${log.details.new_agent_id}`);
    }

    if (log.details.reason) {
      details.push(`Reason: ${log.details.reason}`);
    }

    if (log.details.booking_count) {
      details.push(`Affected bookings: ${log.details.booking_count}`);
    }

    return details;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Booking Action History</DialogTitle>
          <DialogDescription>
            Complete audit trail of all admin actions performed on this booking.
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="h-[500px] pr-4">
          {isLoading && (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex gap-4">
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Failed to load action logs: {error instanceof Error ? error.message : "Unknown error"}
              </AlertDescription>
            </Alert>
          )}

          {!isLoading && !error && logs && logs.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="rounded-full bg-muted p-4 mb-4">
                <Activity className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold mb-2">No Admin Actions</h3>
              <p className="text-sm text-muted-foreground max-w-sm">
                This booking has no recorded admin actions. All admin operations will be logged here.
              </p>
            </div>
          )}

          {!isLoading && !error && logs && logs.length > 0 && (
            <div className="space-y-6">
              {logs.map((log, index) => (
                <div key={log.id} className="relative">
                  {/* Timeline connector */}
                  {index < logs.length - 1 && (
                    <div className="absolute left-5 top-12 bottom-0 w-0.5 bg-border" />
                  )}

                  <div className="flex gap-4">
                    {/* Icon */}
                    <div className={`
                      flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center
                      ${getActionBadgeVariant(log.action_type) === "default" ? "bg-green-100 text-green-700" :
                        getActionBadgeVariant(log.action_type) === "destructive" ? "bg-red-100 text-red-700" :
                        getActionBadgeVariant(log.action_type) === "secondary" ? "bg-blue-100 text-blue-700" :
                        "bg-gray-100 text-gray-700"}
                    `}>
                      {getActionIcon(log.action_type)}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <div>
                          <Badge variant={getActionBadgeVariant(log.action_type)} className="mb-1">
                            {formatActionType(log.action_type)}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <span title={new Date(log.timestamp).toLocaleString()}>
                            {formatDistanceToNow(new Date(log.timestamp), { addSuffix: true })}
                          </span>
                        </div>
                      </div>

                      {/* Admin info */}
                      <div className="flex items-center gap-1 text-sm text-muted-foreground mb-2">
                        <User className="h-3 w-3" />
                        <span>{log.admin_email}</span>
                      </div>

                      {/* Action details */}
                      {formatActionDetails(log).length > 0 && (
                        <div className="rounded-lg border bg-muted/50 p-3 text-sm space-y-1">
                          {formatActionDetails(log).map((detail, i) => (
                            <p key={i} className="text-muted-foreground">{detail}</p>
                          ))}
                        </div>
                      )}

                      {/* Absolute timestamp */}
                      <p className="text-xs text-muted-foreground mt-2">
                        {new Date(log.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
