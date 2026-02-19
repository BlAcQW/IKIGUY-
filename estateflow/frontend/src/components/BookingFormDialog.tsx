/**
 * BookingFormDialog Component
 *
 * Modal for creating and editing property tour bookings.
 */

import { useState, useEffect } from "react";
import { Calendar, Clock, User, Mail, Phone, MessageSquare } from "lucide-react";
import { useCreateBooking, useUpdateBooking } from "../hooks/use-bookings";
import { Button } from "./ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { useToast } from "./ui/use-toast";
import { BookingCalendar } from "./BookingCalendar";
import type { Booking, BookingType } from "../lib/api/booking-api";

interface BookingFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  propertyId: string;
  propertyName: string;
  booking?: Booking;
  onSuccess?: () => void;
}

export function BookingFormDialog({
  open,
  onOpenChange,
  propertyId,
  propertyName,
  booking,
  onSuccess,
}: BookingFormDialogProps) {
  const { toast } = useToast();
  const createMutation = useCreateBooking();
  const updateMutation = useUpdateBooking();

  // Form state
  const [selectedSlot, setSelectedSlot] = useState<string>("");
  const [endTime, setEndTime] = useState<string>("");
  const [bookingType, setBookingType] = useState<BookingType>("in-person");
  const [duration, setDuration] = useState<number>(30);
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [notes, setNotes] = useState("");
  const [showCalendar, setShowCalendar] = useState(true);

  // Initialize form with booking data if editing
  useEffect(() => {
    if (booking) {
      setSelectedSlot(booking.scheduled_at);
      setBookingType(booking.booking_type);
      setDuration(booking.duration_minutes);
      setContactName(booking.contact_name);
      setContactEmail(booking.contact_email || "");
      setContactPhone(booking.contact_phone || "");
      setNotes(booking.notes || "");
      setShowCalendar(false);
    } else {
      // Reset form
      setSelectedSlot("");
      setEndTime("");
      setBookingType("in-person");
      setDuration(30);
      setContactName("");
      setContactEmail("");
      setContactPhone("");
      setNotes("");
      setShowCalendar(true);
    }
  }, [booking, open]);

  const handleSelectSlot = (startTime: string, endTime: string) => {
    setSelectedSlot(startTime);
    setEndTime(endTime);
    setShowCalendar(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedSlot) {
      toast({
        title: "Error",
        description: "Please select a time slot",
        variant: "destructive",
      });
      return;
    }

    if (!contactName) {
      toast({
        title: "Error",
        description: "Please enter contact name",
        variant: "destructive",
      });
      return;
    }

    if (!contactEmail) {
      toast({
        title: "Error",
        description: "Please enter email address",
        variant: "destructive",
      });
      return;
    }

    if (!contactPhone) {
      toast({
        title: "Error",
        description: "Please enter phone number",
        variant: "destructive",
      });
      return;
    }

    try {
      if (booking) {
        // Update existing booking
        await updateMutation.mutateAsync({
          bookingId: booking.id,
          updates: {
            scheduled_at: selectedSlot,
            duration_minutes: duration,
            notes,
          },
        });

        toast({
          title: "Success",
          description: "Booking updated successfully",
        });
      } else {
        // Create new booking
        await createMutation.mutateAsync({
          property_id: propertyId,
          scheduled_at: selectedSlot,
          duration_minutes: duration,
          booking_type: bookingType,
          contact_name: contactName,
          contact_email: contactEmail || undefined,
          contact_phone: contactPhone || undefined,
          notes: notes || undefined,
        });

        toast({
          title: "Success",
          description: "Booking created successfully",
        });
      }

      onSuccess?.();
      onOpenChange(false);
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to save booking",
        variant: "destructive",
      });
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {booking ? "Edit Booking" : "Schedule Property Tour"}
          </DialogTitle>
          <DialogDescription>
            Book a tour for <span className="font-medium">{propertyName}</span>
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Calendar Section */}
          {showCalendar ? (
            <BookingCalendar
              propertyId={propertyId}
              onSelectSlot={handleSelectSlot}
              selectedSlot={selectedSlot}
              durationMinutes={duration}
            />
          ) : (
            <div className="border rounded-lg p-4 bg-blue-50">
              <div className="flex items-start justify-between">
                <div>
                  <Label className="text-sm text-gray-600">Selected Time</Label>
                  <p className="font-medium mt-1 flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    {formatDateTime(selectedSlot)}
                  </p>
                  <p className="text-sm text-gray-600 mt-1 flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    {duration} minutes
                  </p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCalendar(true)}
                >
                  Change Time
                </Button>
              </div>
            </div>
          )}

          {/* Booking Details */}
          {!showCalendar && (
            <div className="space-y-4">
              {/* Booking Type */}
              {!booking && (
                <div>
                  <Label htmlFor="booking-type">Tour Type</Label>
                  <Select
                    value={bookingType}
                    onValueChange={(value) => setBookingType(value as BookingType)}
                  >
                    <SelectTrigger id="booking-type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="in-person">In-Person Tour</SelectItem>
                      <SelectItem value="virtual">Virtual Tour</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Duration */}
              <div>
                <Label htmlFor="duration">Duration</Label>
                <Select
                  value={String(duration)}
                  onValueChange={(value) => setDuration(parseInt(value))}
                >
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

              {/* Contact Information */}
              {!booking && (
                <>
                  <div>
                    <Label htmlFor="contact-name">
                      <User className="h-4 w-4 inline mr-1" />
                      Contact Name *
                    </Label>
                    <Input
                      id="contact-name"
                      value={contactName}
                      onChange={(e) => setContactName(e.target.value)}
                      placeholder="John Doe"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="contact-email">
                      <Mail className="h-4 w-4 inline mr-1" />
                      Email *
                    </Label>
                    <Input
                      id="contact-email"
                      type="email"
                      value={contactEmail}
                      onChange={(e) => setContactEmail(e.target.value)}
                      placeholder="john@example.com"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="contact-phone">
                      <Phone className="h-4 w-4 inline mr-1" />
                      Phone *
                    </Label>
                    <Input
                      id="contact-phone"
                      type="tel"
                      value={contactPhone}
                      onChange={(e) => setContactPhone(e.target.value)}
                      placeholder="+233 24 123 4567"
                      required
                    />
                  </div>
                </>
              )}

              {/* Notes */}
              <div>
                <Label htmlFor="notes">
                  <MessageSquare className="h-4 w-4 inline mr-1" />
                  Notes (Optional)
                </Label>
                <Textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Any special requests or questions..."
                  rows={3}
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading || showCalendar}>
              {isLoading
                ? "Saving..."
                : booking
                ? "Update Booking"
                : "Create Booking"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
