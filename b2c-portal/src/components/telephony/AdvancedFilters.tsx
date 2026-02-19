import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { Filter, X, Calendar as CalendarIcon } from 'lucide-react';
import { format } from 'date-fns';

export interface FilterOptions {
  startDate?: Date;
  endDate?: Date;
  direction?: 'inbound' | 'outbound' | 'all';
  status?: 'completed' | 'failed' | 'busy' | 'no-answer' | 'all';
  minDuration?: number;
  maxDuration?: number;
  fromNumber?: string;
  toNumber?: string;
}

interface AdvancedFiltersProps {
  onFilterChange: (filters: FilterOptions) => void;
  onReset: () => void;
}

export const AdvancedFilters: React.FC<AdvancedFiltersProps> = ({
  onFilterChange,
  onReset,
}) => {
  const [filters, setFilters] = useState<FilterOptions>({
    direction: 'all',
    status: 'all',
  });
  const [isOpen, setIsOpen] = useState(false);

  const handleFilterUpdate = (key: keyof FilterOptions, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
  };

  const applyFilters = () => {
    onFilterChange(filters);
    setIsOpen(false);
  };

  const resetFilters = () => {
    const defaultFilters: FilterOptions = {
      direction: 'all',
      status: 'all',
    };
    setFilters(defaultFilters);
    onReset();
    setIsOpen(false);
  };

  const hasActiveFilters = () => {
    return (
      filters.startDate ||
      filters.endDate ||
      (filters.direction && filters.direction !== 'all') ||
      (filters.status && filters.status !== 'all') ||
      filters.minDuration ||
      filters.maxDuration ||
      filters.fromNumber ||
      filters.toNumber
    );
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="relative">
          <Filter className="h-4 w-4 mr-2" />
          Advanced Filters
          {hasActiveFilters() && (
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-indigo-600 rounded-full" />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-96" align="end">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold">Filter Options</h4>
            {hasActiveFilters() && (
              <Button variant="ghost" size="sm" onClick={resetFilters}>
                <X className="h-4 w-4 mr-1" />
                Clear All
              </Button>
            )}
          </div>

          {/* Date Range */}
          <div className="space-y-2">
            <Label>Date Range</Label>
            <div className="grid grid-cols-2 gap-2">
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" size="sm" className="justify-start text-left">
                    <CalendarIcon className="h-4 w-4 mr-2" />
                    {filters.startDate ? format(filters.startDate, 'PP') : 'Start date'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={filters.startDate}
                    onSelect={(date) => handleFilterUpdate('startDate', date)}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>

              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" size="sm" className="justify-start text-left">
                    <CalendarIcon className="h-4 w-4 mr-2" />
                    {filters.endDate ? format(filters.endDate, 'PP') : 'End date'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={filters.endDate}
                    onSelect={(date) => handleFilterUpdate('endDate', date)}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          {/* Call Direction */}
          <div className="space-y-2">
            <Label>Call Direction</Label>
            <Select
              value={filters.direction}
              onValueChange={(value) => handleFilterUpdate('direction', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select direction" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Calls</SelectItem>
                <SelectItem value="inbound">Inbound Only</SelectItem>
                <SelectItem value="outbound">Outbound Only</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Call Status */}
          <div className="space-y-2">
            <Label>Call Status</Label>
            <Select
              value={filters.status}
              onValueChange={(value) => handleFilterUpdate('status', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="busy">Busy</SelectItem>
                <SelectItem value="no-answer">No Answer</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Duration Range */}
          <div className="space-y-2">
            <Label>Duration (seconds)</Label>
            <div className="grid grid-cols-2 gap-2">
              <Input
                type="number"
                placeholder="Min"
                value={filters.minDuration || ''}
                onChange={(e) =>
                  handleFilterUpdate('minDuration', e.target.value ? parseInt(e.target.value) : undefined)
                }
              />
              <Input
                type="number"
                placeholder="Max"
                value={filters.maxDuration || ''}
                onChange={(e) =>
                  handleFilterUpdate('maxDuration', e.target.value ? parseInt(e.target.value) : undefined)
                }
              />
            </div>
          </div>

          {/* Phone Numbers */}
          <div className="space-y-2">
            <Label>From Number</Label>
            <Input
              placeholder="+1234567890"
              value={filters.fromNumber || ''}
              onChange={(e) => handleFilterUpdate('fromNumber', e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>To Number</Label>
            <Input
              placeholder="+1234567890"
              value={filters.toNumber || ''}
              onChange={(e) => handleFilterUpdate('toNumber', e.target.value)}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 pt-2">
            <Button variant="outline" size="sm" className="flex-1" onClick={resetFilters}>
              Reset
            </Button>
            <Button size="sm" className="flex-1" onClick={applyFilters}>
              Apply Filters
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
};
