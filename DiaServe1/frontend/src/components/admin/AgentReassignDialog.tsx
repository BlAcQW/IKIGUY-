/**
 * AgentReassignDialog Component
 *
 * Admin-only modal for reassigning bookings to different agents.
 *
 * Features:
 * - Display current agent information
 * - Agent dropdown selector
 * - Reassignment reason textarea
 * - Confirm/Cancel actions
 */

import { useState, useEffect } from "react";
import { Users, AlertCircle } from "lucide-react";
import { useAdminReassignAgent } from "../../hooks/use-bookings";
import { Button } from "../ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Label } from "../ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { useToast } from "../ui/use-toast";
import { Alert, AlertDescription } from "../ui/alert";
import type { Booking } from "../../lib/api/booking-api";

interface AgentReassignDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  booking?: Booking;
  agents?: Array<{ id: string; first_name: string; last_name: string; email: string }>;
  onSuccess?: () => void;
}

export function AgentReassignDialog({
  open,
  onOpenChange,
  booking,
  agents = [],
  onSuccess,
}: AgentReassignDialogProps) {
  const { toast } = useToast();
  const reassignMutation = useAdminReassignAgent();

  // Form state
  const [newAgentId, setNewAgentId] = useState("");

  // Reset form when dialog opens/closes
  useEffect(() => {
    if (!open) {
      setNewAgentId("");
    }
  }, [open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!booking) {
      toast({
        title: "Error",
        description: "No booking selected",
        variant: "destructive",
      });
      return;
    }

    if (!newAgentId) {
      toast({
        title: "Validation Error",
        description: "Please select a new agent",
        variant: "destructive",
      });
      return;
    }

    if (newAgentId === booking.agent_id) {
      toast({
        title: "Validation Error",
        description: "Selected agent is already assigned to this booking",
        variant: "destructive",
      });
      return;
    }

    try {
      await reassignMutation.mutateAsync({
        bookingId: booking.id,
        newAgentId,
      });

      toast({
        title: "Success",
        description: "Agent reassigned successfully",
      });

      onOpenChange(false);
      onSuccess?.();
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to reassign agent",
        variant: "destructive",
      });
    }
  };

  const currentAgent = agents.find((a) => a.id === booking?.agent_id);
  const newAgent = agents.find((a) => a.id === newAgentId);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Reassign Agent</DialogTitle>
          <DialogDescription>
            Change the agent assigned to this booking.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Current Agent Info */}
          {booking && (
            <div className="rounded-lg border bg-muted p-4">
              <h4 className="text-sm font-medium mb-2">Current Assignment</h4>
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-sm">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  {currentAgent ? (
                    <span>
                      {currentAgent.first_name} {currentAgent.last_name}
                    </span>
                  ) : (
                    <span className="text-muted-foreground">
                      {booking.agent_id ? `Agent ID: ${booking.agent_id}` : "No agent assigned"}
                    </span>
                  )}
                </div>
                {currentAgent && (
                  <p className="text-xs text-muted-foreground pl-6">{currentAgent.email}</p>
                )}
              </div>
            </div>
          )}

          {/* New Agent Selection */}
          <div className="space-y-2">
            <Label htmlFor="new-agent">New Agent *</Label>
            <Select value={newAgentId} onValueChange={setNewAgentId}>
              <SelectTrigger id="new-agent">
                <SelectValue placeholder="Select a new agent" />
              </SelectTrigger>
              <SelectContent>
                {agents.map((agent) => (
                  <SelectItem
                    key={agent.id}
                    value={agent.id}
                    disabled={agent.id === booking?.agent_id}
                  >
                    {agent.first_name} {agent.last_name}
                    {agent.id === booking?.agent_id && " (Current)"}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Warning if reassigning */}
          {newAgentId && newAgent && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                This booking will be reassigned to <strong>{newAgent.first_name} {newAgent.last_name}</strong>.
                The agent will be notified of the change.
              </AlertDescription>
            </Alert>
          )}

          {/* Booking Details */}
          {booking && (
            <div className="rounded-lg border bg-muted/50 p-3 text-sm space-y-1">
              <p>
                <strong>Booking:</strong> {new Date(booking.scheduled_at).toLocaleString()}
              </p>
              <p>
                <strong>Contact:</strong> {booking.contact_name}
              </p>
              <p>
                <strong>Status:</strong>{" "}
                <span className="capitalize">{booking.status.replace("-", " ")}</span>
              </p>
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={reassignMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={reassignMutation.isPending}>
              {reassignMutation.isPending ? "Reassigning..." : "Reassign Agent"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
