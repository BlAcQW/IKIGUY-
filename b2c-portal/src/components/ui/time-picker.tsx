import React from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Clock } from 'lucide-react';

interface TimePickerProps {
  value?: string; // HH:MM format
  onChange: (value: string) => void;
  placeholder?: string;
  id?: string;
}

export const TimePicker: React.FC<TimePickerProps> = ({
  value = '',
  onChange,
  placeholder = 'Select time',
  id,
}) => {
  // Parse current value
  const [hours, minutes] = value ? value.split(':') : ['', ''];

  // Generate hours (00-23)
  const hoursOptions = Array.from({ length: 24 }, (_, i) => {
    const hour = i.toString().padStart(2, '0');
    return { value: hour, label: hour };
  });

  // Generate minutes (00, 15, 30, 45)
  const minutesOptions = [
    { value: '00', label: '00' },
    { value: '15', label: '15' },
    { value: '30', label: '30' },
    { value: '45', label: '45' },
  ];

  const handleHourChange = (newHour: string) => {
    const newMinutes = minutes || '00';
    onChange(`${newHour}:${newMinutes}`);
  };

  const handleMinuteChange = (newMinute: string) => {
    const newHour = hours || '00';
    onChange(`${newHour}:${newMinute}`);
  };

  const handleClear = () => {
    onChange('');
  };

  return (
    <div className="flex items-center gap-2" id={id}>
      <div className="flex items-center gap-1 flex-1 border border-gray-300 rounded-lg px-3 py-2 bg-white">
        <Clock className="h-4 w-4 text-gray-500 mr-2" />

        {/* Hours Select */}
        <Select value={hours} onValueChange={handleHourChange}>
          <SelectTrigger className="border-0 h-auto p-0 focus:ring-0 w-16">
            <SelectValue placeholder="HH" />
          </SelectTrigger>
          <SelectContent>
            {hoursOptions.map((hour) => (
              <SelectItem key={hour.value} value={hour.value}>
                {hour.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <span className="text-gray-600">:</span>

        {/* Minutes Select */}
        <Select value={minutes} onValueChange={handleMinuteChange}>
          <SelectTrigger className="border-0 h-auto p-0 focus:ring-0 w-16">
            <SelectValue placeholder="MM" />
          </SelectTrigger>
          <SelectContent>
            {minutesOptions.map((minute) => (
              <SelectItem key={minute.value} value={minute.value}>
                {minute.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {value && (
          <button
            type="button"
            onClick={handleClear}
            className="ml-auto text-gray-400 hover:text-gray-600 text-xs"
          >
            Clear
          </button>
        )}
      </div>

      {value && (
        <span className="text-sm text-gray-600 font-mono">{value}</span>
      )}
    </div>
  );
};
