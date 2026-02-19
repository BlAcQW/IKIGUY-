import { useState, useEffect } from "react";
import { Calendar as CalendarIcon, Clock } from "lucide-react";
import { format } from "date-fns";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

interface DateTimePickerProps {
  value?: Date;
  onChange: (date: Date | undefined) => void;
  disabled?: boolean;
  minDate?: Date;
  placeholder?: string;
}

export function DateTimePicker({
  value,
  onChange,
  disabled = false,
  minDate,
  placeholder = "Pick a date and time",
}: DateTimePickerProps) {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(value);
  const [hours, setHours] = useState<string>("12");
  const [minutes, setMinutes] = useState<string>("00");
  const [period, setPeriod] = useState<"AM" | "PM">("PM");
  const [isOpen, setIsOpen] = useState(false);

  // Initialize time from value
  useEffect(() => {
    if (value) {
      setSelectedDate(value);
      const h = value.getHours();
      const m = value.getMinutes();

      // Convert to 12-hour format
      if (h === 0) {
        setHours("12");
        setPeriod("AM");
      } else if (h < 12) {
        setHours(h.toString());
        setPeriod("AM");
      } else if (h === 12) {
        setHours("12");
        setPeriod("PM");
      } else {
        setHours((h - 12).toString());
        setPeriod("PM");
      }

      setMinutes(m.toString().padStart(2, "0"));
    } else {
      // Reset when value is cleared
      setSelectedDate(undefined);
      setHours("12");
      setMinutes("00");
      setPeriod("PM");
    }
  }, [value]);

  const handleDateSelect = (date: Date | undefined) => {
    if (!date) {
      setSelectedDate(undefined);
      onChange(undefined);
      return;
    }

    // Create a new date object to avoid reference issues
    const newDate = new Date(date);
    
    // If this is the first date selection or we're changing the date (not just time)
    const isNewDate = !selectedDate || selectedDate.toDateString() !== newDate.toDateString();
    
    if (isNewDate) {
      // Initialize time based on whether it's today or a future date
      const now = new Date();
      const isToday = newDate.toDateString() === now.toDateString();
      
      if (isToday && minDate) {
        // If selecting today and there's a minDate, use current time + 1 hour or minDate time (whichever is later)
        const minTime = minDate.getTime();
        const nowTime = now.getTime();
        if (nowTime >= minTime) {
          // Use current time + 1 hour to ensure it's in the future
          newDate.setHours(now.getHours());
          newDate.setMinutes(now.getMinutes() + 30); // Add 30 minutes
          if (newDate.getMinutes() >= 60) {
            newDate.setHours(newDate.getHours() + 1);
            newDate.setMinutes(newDate.getMinutes() - 60);
          }
        } else {
          newDate.setHours(minDate.getHours());
          newDate.setMinutes(minDate.getMinutes() + 30);
          if (newDate.getMinutes() >= 60) {
            newDate.setHours(newDate.getHours() + 1);
            newDate.setMinutes(newDate.getMinutes() - 60);
          }
        }
      } else {
        // Default to 8:00 AM for future dates
        newDate.setHours(8);
        newDate.setMinutes(0);
      }
      
      // Update time inputs to match the new date's time
      const h = newDate.getHours();
      const m = newDate.getMinutes();
      if (h === 0) {
        setHours("12");
        setPeriod("AM");
      } else if (h < 12) {
        setHours(h.toString());
        setPeriod("AM");
      } else if (h === 12) {
        setHours("12");
        setPeriod("PM");
      } else {
        setHours((h - 12).toString());
        setPeriod("PM");
      }
      setMinutes(m.toString().padStart(2, "0"));
    }

    setSelectedDate(newDate);
    updateDateTime(newDate, hours, minutes, period);
  };

  const updateDateTime = (
    date: Date,
    h: string,
    m: string,
    p: "AM" | "PM"
  ) => {
    const newDate = new Date(date);
    let hour24 = parseInt(h) || 12;

    // Convert to 24-hour format
    if (p === "AM") {
      if (hour24 === 12) hour24 = 0;
    } else {
      if (hour24 !== 12) hour24 += 12;
    }

    newDate.setHours(hour24);
    newDate.setMinutes(parseInt(m) || 0);
    newDate.setSeconds(0);
    newDate.setMilliseconds(0);

    onChange(newDate);
  };

  const handleHoursChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value.replace(/\D/g, "");
    if (val) {
      const num = parseInt(val);
      if (num > 12) val = "12";
      if (num < 1) val = "1";
    }
    setHours(val);
    if (selectedDate && val) {
      updateDateTime(selectedDate, val, minutes, period);
    }
  };

  const handleMinutesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value.replace(/\D/g, "");
    if (val) {
      const num = parseInt(val);
      if (num > 59) val = "59";
    }
    setMinutes(val.padStart(2, "0"));
    if (selectedDate && val) {
      updateDateTime(selectedDate, hours, val.padStart(2, "0"), period);
    }
  };

  const togglePeriod = () => {
    const newPeriod = period === "AM" ? "PM" : "AM";
    setPeriod(newPeriod);
    if (selectedDate) {
      updateDateTime(selectedDate, hours, minutes, newPeriod);
    }
  };

  const formatDisplayDate = () => {
    if (!value) return placeholder;

    try {
      return format(value, "PPP 'at' h:mm a");
    } catch {
      return placeholder;
    }
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen} modal={false}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          disabled={disabled}
          className={cn(
            "w-full justify-start text-left font-normal h-12",
            !value && "text-muted-foreground"
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {formatDisplayDate()}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start" sideOffset={4}>
        <div className="p-3">
          <Calendar
            mode="single"
            selected={selectedDate}
            onSelect={handleDateSelect}
            disabled={(date) => {
              if (minDate) {
                // Compare dates only (ignore time)
                const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
                const minDateOnly = new Date(minDate.getFullYear(), minDate.getMonth(), minDate.getDate());
                return dateOnly < minDateOnly;
              }
              return false;
            }}
            initialFocus
          />

          <div className="mt-3 pt-3 border-t border-border">
            <Label className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Time
            </Label>
            <div className="flex items-center gap-2">
              <div className="flex-1">
                <Input
                  type="text"
                  placeholder="HH"
                  value={hours}
                  onChange={handleHoursChange}
                  onBlur={() => {
                    if (!hours) setHours("12");
                  }}
                  className="text-center h-10"
                  maxLength={2}
                />
              </div>
              <span className="text-lg font-semibold">:</span>
              <div className="flex-1">
                <Input
                  type="text"
                  placeholder="MM"
                  value={minutes}
                  onChange={handleMinutesChange}
                  onBlur={() => {
                    if (!minutes) setMinutes("00");
                  }}
                  className="text-center h-10"
                  maxLength={2}
                />
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={togglePeriod}
                className="px-3 h-10 font-semibold"
              >
                {period}
              </Button>
            </div>
          </div>

          <div className="mt-3 flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setSelectedDate(undefined);
                onChange(undefined);
                setIsOpen(false);
              }}
              className="flex-1"
            >
              Clear
            </Button>
            <Button
              type="button"
              variant="default"
              size="sm"
              onClick={() => setIsOpen(false)}
              className="flex-1"
              disabled={!selectedDate}
            >
              Done
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
