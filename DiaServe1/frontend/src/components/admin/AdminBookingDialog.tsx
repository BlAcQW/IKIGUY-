/**
 * AdminBookingDialog Component
 *
 * Admin-only modal for manually creating bookings with optional availability override.
 *
 * Features:
 * - Property selector
 * - Contact information inputs
 * - Date/time picker
 * - Duration selector
 * - Booking type selector
 * - Agent selector (optional - auto-assign if empty)
 * - Override availability toggle
 * - Override reason (required if override enabled)
 */

import { useState, useEffect } from "react";
import { Calendar, Clock, User, Mail, Phone, MessageSquare, AlertTriangle, Users } from "lucide-react";
import { useAdminCreateBooking } from "../../hooks/use-bookings";
import { Button } from "../ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Switch } from "../ui/switch";
import { useToast } from "../ui/use-toast";
import { Alert, AlertDescription } from "../ui/alert";
import type { BookingType } from "../../lib/api/booking-api";

interface AdminBookingDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  properties?: Array<{ id: string; name: string }>;
  agents?: Array<{ id: string; first_name: string; last_name: string }>;
  onSuccess?: () => void;
}

export function AdminBookingDialog({
  open,
  onOpenChange,
  properties = [],
  agents = [],
  onSuccess,
}: AdminBookingDialogProps) {
  const { toast } = useToast();
  const createMutation = useAdminCreateBooking();

  // Form state
  const [propertyId, setPropertyId] = useState("");
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [scheduledDate, setScheduledDate] = useState("");
  const [scheduledTime, setScheduledTime] = useState("");
  const [duration, setDuration] = useState<number>(30);
  const [bookingType, setBookingType] = useState<BookingType>("in-person");
  const [agentId, setAgentId] = useState<string>("");
  const [notes, setNotes] = useState("");
  const [overrideAvailability, setOverrideAvailability] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");

  // Reset form when dialog opens/closes
  useEffect(() => {
    if (!open) {
      setPropertyId("");
      setContactName("");
      setContactEmail("");
      setContactPhone("");
      setScheduledDate("");
      setScheduledTime("");
      setDuration(30);
      setBookingType("in-person");
      setAgentId("");
      setNotes("");
      setOverrideAvailability(false);
      setOverrideReason("");
    }
  }, [open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!propertyId) {
      toast({
        title: "Validation Error",
        description: "Please select a property",
        variant: "destructive",
      });
      return;
    }

    if (!contactName) {
      toast({
        title: "Validation Error",
        description: "Please enter contact name",
        variant: "destructive",
      });
      return;
    }

    if (!contactEmail) {
      toast({
        title: "Validation Error",
        description: "Please enter email address",
        variant: "destructive",
      });
      return;
    }

    if (!scheduledDate || !scheduledTime) {
      toast({
        title: "Validation Error",
        description: "Please select date and time",
        variant: "destructive",
      });
      return;
    }

    if (overrideAvailability && !overrideReason.trim()) {
      toast({
        title: "Validation Error",
        description: "Override reason is required when bypassing availability check",
        variant: "destructive",
      });
      return;
    }

    // Combine date and time into ISO string
    const scheduledAt = new Date(`${scheduledDate}T${scheduledTime}`).toISOString();

    try {
      await createMutation.mutateAsync({
        booking: {
          property_id: propertyId,
          scheduled_at: scheduledAt,
          duration_minutes: duration,
          booking_type: bookingType,
          contact_name: contactName,
          contact_email: contactEmail,
          contact_phone: contactPhone,
          notes: notes || undefined,
          admin_override: overrideAvailability,
          admin_override_reason: overrideAvailability ? overrideReason : undefined,
        },
        overrideAvailability,
      });

      toast({
        title: "Success",
        description: "Booking created successfully",
      });

      onOpenChange(false);
      onSuccess?.();
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create booking",
        variant: "destructive",
      });
    }
  };

  const selectedProperty = properties.find((p) => p.id === propertyId);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Manual Booking Creation</DialogTitle>
          <DialogDescription>
            Create a booking on behalf of a customer. You can optionally override availability checks.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Property Selection */}
          <div className="space-y-2">
            <Label htmlFor="property">Property *</Label>
            <Select value={propertyId} onValueChange={setPropertyId}>
              <SelectTrigger id="property">
                <SelectValue placeholder="Select a property" />
              </SelectTrigger>
              <SelectContent>
                {properties.map((property) => (
                  <SelectItem key={property.id} value={property.id}>
                    {property.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Contact Information */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="contact-name">Contact Name *</Label>
              <div className="relative">
                <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="contact-name"
                  placeholder="John Doe"
                  value={contactName}
                  onChange={(e) => setContactName(e.target.value)}
                  className="pl-9"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="contact-email">Email *</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="contact-email"
                  type="email"
                  placeholder="john@example.com"
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                  className="pl-9"
                  required
                />
              </div>
            </div>

            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="contact-phone">Phone</Label>
              <div className="relative">
                <Phone className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="contact-phone"
                  type="tel"
                  placeholder="+1 (555) 000-0000"
                  value={contactPhone}
                  onChange={(e) => setContactPhone(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
          </div>

          {/* Date and Time */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="date">Date *</Label>
              <div className="relative">
                <Calendar className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="date"
                  type="date"
                  value={scheduledDate}
                  onChange={(e) => setScheduledDate(e.target.value)}
                  className="pl-9"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="time">Time *</Label>
              <div className="relative">
                <Clock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="time"
                  type="time"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                  className="pl-9"
                  required
                />
              </div>
            </div>
          </div>

          {/* Duration and Type */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="duration">Duration</Label>
              <Select value={String(duration)} onValueChange={(v) => setDuration(Number(v))}>
                <SelectTrigger id="duration">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="30">30 minutes</SelectItem>
                  <SelectItem value="60">1 hour</SelectItem>
                  <SelectItem value="90">1.5 hours</SelectItem>
                  <SelectItem value="120">2 hours</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="booking-type">Booking Type</Label>
              <Select value={bookingType} onValueChange={(v) => setBookingType(v as BookingType)}>
                <SelectTrigger id="booking-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="in-person">In-Person</SelectItem>
                  <SelectItem value="virtual">Virtual</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Agent Selection (Optional) */}
          <div className="space-y-2">
            <Label htmlFor="agent">Assign Agent (Optional)</Label>
            <Select value={agentId} onValueChange={setAgentId}>
              <SelectTrigger id="agent">
                <SelectValue placeholder="Auto-assign agent" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Auto-assign agent</SelectItem>
                {agents.map((agent) => (
                  <SelectItem key={agent.id} value={agent.id}>
                    {agent.first_name} {agent.last_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Override Availability */}
          <div className="space-y-4 rounded-lg border border-orange-200 bg-orange-50 p-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="override" className="text-base font-medium">
                  Override Availability Check
                </Label>
                <p className="text-sm text-muted-foreground">
                  Bypass availability validation to create booking even if slot is unavailable
                </p>
              </div>
              <Switch
                id="override"
                checked={overrideAvailability}
                onCheckedChange={setOverrideAvailability}
              />
            </div>

            {overrideAvailability && (
              <div className="space-y-2">
                <Alert variant="default" className="border-orange-300 bg-orange-100">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    You are creating a booking without checking availability. Please provide a reason.
                  </AlertDescription>
                </Alert>

                <div className="space-y-2">
                  <Label htmlFor="override-reason">Override Reason *</Label>
                  <Textarea
                    id="override-reason"
                    placeholder="Explain why you're bypassing the availability check..."
                    value={overrideReason}
                    onChange={(e) => setOverrideReason(e.target.value)}
                    rows={3}
                    required={overrideAvailability}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Notes */}
          <div className="space-y-2">
            <Label htmlFor="notes">Notes (Optional)</Label>
            <div className="relative">
              <MessageSquare className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Textarea
                id="notes"
                placeholder="Any special requests or notes..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                className="pl-9"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={createMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating..." : "Create Booking"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
