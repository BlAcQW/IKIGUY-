import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Phone,
  PhoneIncoming,
  PhoneOutgoing,
  Clock,
  Search,
  ChevronLeft,
  ChevronRight,
  Download,
} from 'lucide-react';
import { AdvancedFilters, FilterOptions } from './AdvancedFilters';

export interface CallRecord {
  id: string;
  call_id: string;
  direction: 'inbound' | 'outbound';
  from_number: string;
  to_number: string;
  start_time: string;
  end_time?: string;
  duration: number; // in seconds
  status: 'completed' | 'failed' | 'busy' | 'no-answer';
  disposition: string;
}

interface CallHistoryTableProps {
  calls: CallRecord[];
  isLoading?: boolean;
  onRefresh?: () => void;
}

export const CallHistoryTable: React.FC<CallHistoryTableProps> = ({
  calls,
  isLoading = false,
  onRefresh,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [activeFilters, setActiveFilters] = useState<FilterOptions>({});
  const itemsPerPage = 10;

  // CSV Export Function
  const exportToCSV = () => {
    // Prepare CSV headers
    const headers = ['Call ID', 'Direction', 'From', 'To', 'Start Time', 'Duration', 'Status'];

    // Prepare CSV rows
    const rows = filteredCalls.map((call) => [
      call.call_id,
      call.direction,
      call.from_number,
      call.to_number,
      call.start_time,
      formatDuration(call.duration),
      call.status,
    ]);

    // Combine headers and rows
    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.join(','))
    ].join('\n');

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `call-history-${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Apply advanced filters
  const applyAdvancedFilters = (call: CallRecord): boolean => {
    // Start date filter
    if (activeFilters.startDate) {
      const callDate = new Date(call.start_time);
      if (callDate < activeFilters.startDate) return false;
    }

    // End date filter
    if (activeFilters.endDate) {
      const callDate = new Date(call.start_time);
      const endOfDay = new Date(activeFilters.endDate);
      endOfDay.setHours(23, 59, 59, 999);
      if (callDate > endOfDay) return false;
    }

    // Direction filter
    if (activeFilters.direction && activeFilters.direction !== 'all') {
      if (call.direction !== activeFilters.direction) return false;
    }

    // Status filter
    if (activeFilters.status && activeFilters.status !== 'all') {
      if (call.status !== activeFilters.status) return false;
    }

    // Duration filters
    if (activeFilters.minDuration && call.duration < activeFilters.minDuration) return false;
    if (activeFilters.maxDuration && call.duration > activeFilters.maxDuration) return false;

    // Phone number filters
    if (activeFilters.fromNumber && !call.from_number.includes(activeFilters.fromNumber)) return false;
    if (activeFilters.toNumber && !call.to_number.includes(activeFilters.toNumber)) return false;

    return true;
  };

  // Filter calls based on search term and advanced filters
  const filteredCalls = calls.filter(
    (call) =>
      (call.from_number.includes(searchTerm) ||
      call.to_number.includes(searchTerm) ||
      call.call_id.includes(searchTerm)) &&
      applyAdvancedFilters(call)
  );

  // Pagination
  const totalPages = Math.ceil(filteredCalls.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentCalls = filteredCalls.slice(startIndex, endIndex);

  // Format duration
  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Get status badge variant
  const getStatusBadge = (status: CallRecord['status']) => {
    switch (status) {
      case 'completed':
        return <Badge variant="default" className="bg-green-500">Completed</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      case 'busy':
        return <Badge variant="secondary">Busy</Badge>;
      case 'no-answer':
        return <Badge variant="outline">No Answer</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by phone number or call ID..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1); // Reset to first page on search
            }}
            className="pl-10"
          />
        </div>
        <AdvancedFilters
          onFilterChange={(filters) => {
            setActiveFilters(filters);
            setCurrentPage(1);
          }}
          onReset={() => {
            setActiveFilters({});
            setCurrentPage(1);
          }}
        />
        <Button
          variant="outline"
          size="sm"
          onClick={exportToCSV}
          disabled={filteredCalls.length === 0}
        >
          <Download className="h-4 w-4 mr-2" />
          Export CSV
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={isLoading}
        >
          Refresh
        </Button>
      </div>

      {/* Table */}
      <div className="border rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[120px]">Direction</TableHead>
              <TableHead>From</TableHead>
              <TableHead>To</TableHead>
              <TableHead>Start Time</TableHead>
              <TableHead className="w-[100px]">Duration</TableHead>
              <TableHead className="w-[120px]">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                    <span className="text-muted-foreground">Loading calls...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : currentCalls.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  <Phone className="h-8 w-8 mx-auto mb-2 text-muted-foreground opacity-50" />
                  <p className="text-muted-foreground">
                    {searchTerm ? 'No calls found matching your search' : 'No call history available'}
                  </p>
                </TableCell>
              </TableRow>
            ) : (
              currentCalls.map((call) => (
                <TableRow key={call.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {call.direction === 'inbound' ? (
                        <>
                          <PhoneIncoming className="h-4 w-4 text-green-500" />
                          <span className="text-sm">Inbound</span>
                        </>
                      ) : (
                        <>
                          <PhoneOutgoing className="h-4 w-4 text-blue-500" />
                          <span className="text-sm">Outbound</span>
                        </>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="font-mono text-sm">{call.from_number}</span>
                  </TableCell>
                  <TableCell>
                    <span className="font-mono text-sm">{call.to_number}</span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-sm">
                      <Clock className="h-3 w-3 text-muted-foreground" />
                      {formatTimestamp(call.start_time)}
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm font-medium">
                      {formatDuration(call.duration)}
                    </span>
                  </TableCell>
                  <TableCell>{getStatusBadge(call.status)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {startIndex + 1} to {Math.min(endIndex, filteredCalls.length)} of{' '}
            {filteredCalls.length} calls
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <span className="text-sm">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
