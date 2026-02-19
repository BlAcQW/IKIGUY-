/**
 * BookingCalendar Component
 *
 * Displays available time slots for property bookings.
 */

import { useState, useMemo } from "react";
import { Calendar } from "lucide-react";
import { usePropertyAvailability } from "../hooks/use-bookings";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Skeleton } from "./ui/skeleton";

interface BookingCalendarProps {
  propertyId: string;
  onSelectSlot?: (startTime: string, endTime: string) => void;
  selectedSlot?: string;
  durationMinutes?: number;
}

export function BookingCalendar({
  propertyId,
  onSelectSlot,
  selectedSlot,
  durationMinutes = 30,
}: BookingCalendarProps) {
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());

  // Calculate date range (selected date + 7 days)
  const startDate = useMemo(() => {
    const date = new Date(selectedDate);
    date.setHours(0, 0, 0, 0);
    return date.toISOString();
  }, [selectedDate]);

  const endDate = useMemo(() => {
    const date = new Date(selectedDate);
    date.setDate(date.getDate() + 7);
    date.setHours(23, 59, 59, 999);
    return date.toISOString();
  }, [selectedDate]);

  // Fetch availability
  const { data, isLoading, error } = usePropertyAvailability(
    propertyId,
    startDate,
    endDate,
    durationMinutes,
    !!propertyId
  );

  // Group slots by date
  const slotsByDate = useMemo(() => {
    if (!data?.slots) return {};

    const grouped: Record<string, typeof data.slots> = {};
    data.slots.forEach((slot) => {
      const date = new Date(slot.start_time).toLocaleDateString();
      if (!grouped[date]) {
        grouped[date] = [];
      }
      grouped[date].push(slot);
    });

    return grouped;
  }, [data]);

  // Navigate to previous week
  const handlePreviousWeek = () => {
    const newDate = new Date(selectedDate);
    newDate.setDate(newDate.getDate() - 7);
    setSelectedDate(newDate);
  };

  // Navigate to next week
  const handleNextWeek = () => {
    const newDate = new Date(selectedDate);
    newDate.setDate(newDate.getDate() + 7);
    setSelectedDate(newDate);
  };

  // Format time for display
  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
  };

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-red-600">
            <p>Failed to load availability</p>
            <p className="text-sm text-gray-500">{error.message}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Available Time Slots
            </CardTitle>
            <CardDescription>
              Select a time to schedule your property tour
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handlePreviousWeek}>
              Previous Week
            </Button>
            <Button variant="outline" size="sm" onClick={handleNextWeek}>
              Next Week
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-32" />
                <div className="grid grid-cols-4 gap-2">
                  {[1, 2, 3, 4].map((j) => (
                    <Skeleton key={j} className="h-10" />
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-6">
            {Object.keys(slotsByDate).length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Calendar className="h-12 w-12 mx-auto mb-2 opacity-20" />
                <p>No available slots for this period</p>
                <p className="text-sm">Try selecting a different week</p>
              </div>
            ) : (
              Object.entries(slotsByDate).map(([date, slots]) => (
                <div key={date}>
                  <h3 className="font-medium text-sm text-gray-700 mb-2">
                    {formatDate(slots[0].start_time)}
                  </h3>
                  <div className="grid grid-cols-4 gap-2">
                    {slots.map((slot) => {
                      const isSelected = selectedSlot === slot.start_time;
                      const isAvailable = slot.available;

                      return (
                        <Button
                          key={slot.start_time}
                          variant={isSelected ? "default" : "outline"}
                          size="sm"
                          disabled={!isAvailable}
                          onClick={() => onSelectSlot?.(slot.start_time, slot.end_time)}
                          className="relative"
                        >
                          <span className="text-xs">
                            {formatTime(slot.start_time)}
                          </span>
                          {!isAvailable && (
                            <Badge
                              variant="secondary"
                              className="absolute -top-1 -right-1 text-xs px-1"
                            >
                              Booked
                            </Badge>
                          )}
                        </Button>
                      );
                    })}
                  </div>
                </div>
              ))
            )}

            {/* Legend */}
            <div className="flex items-center gap-4 text-xs text-gray-500 pt-4 border-t">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded border-2 border-blue-600" />
                <span>Available</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded bg-blue-600" />
                <span>Selected</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded border-2 border-gray-300 bg-gray-100" />
                <span>Booked</span>
              </div>
            </div>

            {/* Summary */}
            {data && (
              <div className="text-sm text-gray-500 pt-2">
                Showing{" "}
                <span className="font-medium">
                  {data.slots.filter((s) => s.available).length}
                </span>{" "}
                available slots out of{" "}
                <span className="font-medium">{data.slots.length}</span> total
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
