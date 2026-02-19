import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import { useOrganization } from '@/contexts/OrganizationContext';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Calendar, CalendarIcon, Search, Filter, Download, Phone, PhoneCall, User, Clock, DollarSign, Loader2 } from 'lucide-react';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar as CalendarComponent } from '@/components/ui/calendar';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


// Types
interface CallLog {
  id: string;
  call_id: string;
  assistant_id: string;
  assistant_name?: string;
  status: string;
  direction: string;
  from_phone?: string;
  to_phone?: string;
  start_time: string;
  end_time?: string;
  duration?: number;
  transcript?: string;
  summary?: string;
  sentiment?: string;
  cost?: number;
  customer_id?: string;
  created_at: string;
  updated_at: string;
}

interface CallLogFilter {
  start_date?: Date;
  end_date?: Date;
  status?: string;
  direction?: string;
  assistant_id?: string;
  automation_id?: string;
  keyword?: string;
}

interface Automation {
  _id: string;
  automation_name: string;
  automationName?: string;
}

const CallLogs: React.FC = () => {
  const { toast } = useToast();
  const { getAccessToken } = useMongoAuth();
  const { currentOrganization } = useOrganization();
  // Using API_BASE_URL from api-config;

  // Get authentication headers
  // Reason: Add X-Organization-ID header for organization-scoped queries
  const getAuthHeaders = (): Record<string, string> => {
    const token = getAccessToken();
    const currentOrgId = localStorage.getItem('kasaai_current_organization_id');

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    if (currentOrgId) {
      headers['X-Organization-ID'] = currentOrgId;
    }

    return headers;
  };

  // State
  const [callLogs, setCallLogs] = useState<CallLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [filters, setFilters] = useState<CallLogFilter>({});
  const [selectedLog, setSelectedLog] = useState<CallLog | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  // Refs for infinite scroll
  const observerTarget = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const hasMoreRef = useRef(hasMore);
  const loadingMoreRef = useRef(loadingMore);

  // Reason: Keep refs in sync with state for observer callback
  useEffect(() => {
    hasMoreRef.current = hasMore;
    loadingMoreRef.current = loadingMore;
  }, [hasMore, loadingMore]);

  // Automation filter
  const [automations, setAutomations] = useState<Automation[]>([]);
  const [selectedAutomation, setSelectedAutomation] = useState<string>('');

  // Date filters
  const [startDate, setStartDate] = useState<Date>();
  const [endDate, setEndDate] = useState<Date>();

  // Fetch automations for the current organization
  const fetchAutomations = async () => {
    try {
      const headers = getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/automation-configs`, {
        method: 'GET',
        headers
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setAutomations(data.configs || []);
    } catch (error) {
      console.error('Error fetching automations:', error);
    }
  };

  // Fetch call logs (with append mode for infinite scroll)
  const fetchCallLogs = async (append = false, pageToFetch = page) => {
    // Reason: Prevent fetching if already loading more, or trying to append when no more data
    if (loadingMore || (append && !hasMore)) {
      console.log('[Infinite Scroll] Fetch blocked', { loadingMore, append, hasMore });
      return;
    }

    console.log('[Infinite Scroll] Starting fetch', { append, pageToFetch, currentPage: page });

    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }

    try {
      const params = new URLSearchParams({
        page: pageToFetch.toString(),
        per_page: '20',
        sort_by: 'created_at', // Changed to match vapi_calls schema
        sort_order: 'desc'
      });

      // Add filters (map to backend field names)
      if (filters.start_date) {
        params.append('start_date', filters.start_date.toISOString());
      }
      if (filters.end_date) {
        params.append('end_date', filters.end_date.toISOString());
      }
      if (filters.status) {
        params.append('status', filters.status); // Backend expects status
      }
      if (filters.assistant_id) {
        params.append('assistant_id', filters.assistant_id);
      }
      if (filters.automation_id) {
        params.append('automation_id', filters.automation_id);
      }
      if (filters.keyword) {
        // Backend doesn't support keyword search yet, but we'll include it for future
        params.append('keyword', filters.keyword);
      }

      const headers = getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/call-logs?${params}`, {
        method: 'GET',
        headers
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Map backend response structure to frontend expectations
      const newLogs = data.logs || [];

      console.log('[Infinite Scroll] Fetch response', {
        append,
        newLogsCount: newLogs.length,
        currentPage: data.pagination?.page,
        totalPages: data.pagination?.pages,
        total: data.pagination?.total
      });

      if (append) {
        // Reason: Append new logs to existing ones for infinite scroll
        setCallLogs(prev => {
          console.log('[Infinite Scroll] Appending logs', { prevCount: prev.length, newCount: newLogs.length });
          return [...prev, ...newLogs];
        });
      } else {
        // Reason: Replace logs when filters change or initial load
        setCallLogs(newLogs);
      }

      setTotalCount(data.pagination?.total || 0);

      // Reason: Check if there are more pages to load
      const currentPage = data.pagination?.page || page;
      const totalPages = data.pagination?.pages || 1;
      const moreAvailable = currentPage < totalPages;
      console.log('[Infinite Scroll] Setting hasMore:', moreAvailable, { currentPage, totalPages });
      setHasMore(moreAvailable);

    } catch (error) {
      console.error('Error fetching call logs:', error);
      toast({
        title: "Failed to load call logs",
        description: "Please check your connection and try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  // Apply filters
  const applyFilters = () => {
    setFilters({
      start_date: startDate,
      end_date: endDate,
      automation_id: selectedAutomation || undefined,
      keyword: searchKeyword
    });
    setPage(1);
    setCallLogs([]); // Reset logs when applying filters
    setHasMore(true); // Reset hasMore flag
  };

  // Clear filters
  const clearFilters = () => {
    setFilters({});
    setSearchKeyword('');
    setStartDate(undefined);
    setEndDate(undefined);
    setSelectedAutomation('');
    setPage(1);
    setCallLogs([]); // Reset logs when clearing filters
    setHasMore(true); // Reset hasMore flag
  };

  // Load more data when user scrolls to bottom
  const loadMore = useCallback(() => {
    console.log('[Infinite Scroll] loadMore called', { loadingMore, hasMore });
    if (!loadingMore && hasMore) {
      setPage(prev => {
        console.log('[Infinite Scroll] Incrementing page from', prev, 'to', prev + 1);
        return prev + 1;
      });
    }
  }, [loadingMore, hasMore]);

  // Format duration
  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Format cost
  const formatCost = (cost?: number) => {
    if (!cost) return 'N/A';
    return `$${cost.toFixed(4)}`;
  };

  // Get status badge variant
  const getStatusVariant = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'default';
      case 'in_progress': return 'secondary';
      case 'failed': return 'destructive';
      case 'cancelled': return 'outline';
      default: return 'secondary';
    }
  };

  // Get direction icon
  const getDirectionIcon = (direction: string) => {
    return direction === 'inbound' ? <PhoneCall className="h-4 w-4" /> : <Phone className="h-4 w-4" />;
  };

  // Effects
  // Reason: Fetch automations when organization changes
  useEffect(() => {
    if (currentOrganization) {
      fetchAutomations();
    }
  }, [currentOrganization]);

  // Reason: Fetch call logs when component mounts, filters change, or organization changes
  // This ensures call logs are refreshed when user switches organizations
  useEffect(() => {
    if (currentOrganization) {
      fetchCallLogs(false); // Initial load
    }
  }, [filters, currentOrganization]);

  // Reason: Fetch more call logs when page changes (for infinite scroll)
  useEffect(() => {
    if (page > 1 && currentOrganization) {
      console.log('[Infinite Scroll] Page changed to:', page);
      fetchCallLogs(true, page); // Append mode with explicit page
    }
  }, [page, currentOrganization]);

  // Reason: Set up Intersection Observer for infinite scroll
  useEffect(() => {
    const currentTarget = observerTarget.current;
    const scrollContainer = scrollContainerRef.current;

    console.log('[Infinite Scroll] Setting up observer', {
      hasObserverTarget: !!currentTarget,
      hasScrollContainer: !!scrollContainer,
      hasMore: hasMoreRef.current,
      loadingMore: loadingMoreRef.current,
      callLogsCount: callLogs.length
    });

    // Reason: Don't set up observer if target isn't ready
    if (!currentTarget) {
      console.warn('[Infinite Scroll] No observer target, skipping observer setup');
      return;
    }

    // Reason: Try with scroll container first, fallback to viewport if container not ready
    const observerRoot = scrollContainer || null;
    console.log('[Infinite Scroll] Using observer root:', observerRoot ? 'scrollContainer' : 'viewport (null)');

    const observer = new IntersectionObserver(
      entries => {
        const intersecting = entries[0].isIntersecting;
        const currentHasMore = hasMoreRef.current;
        const currentLoadingMore = loadingMoreRef.current;

        console.log('[Infinite Scroll] Observer callback fired!', {
          isIntersecting: intersecting,
          hasMore: currentHasMore,
          loadingMore: currentLoadingMore,
          boundingRect: entries[0].boundingClientRect,
          intersectionRatio: entries[0].intersectionRatio
        });

        // Reason: Load more when the observer target becomes visible and conditions are met
        if (intersecting && currentHasMore && !currentLoadingMore) {
          console.log('[Infinite Scroll] ✅ Triggering loadMore');
          loadMore();
        } else {
          console.log('[Infinite Scroll] ❌ Not loading:', { intersecting, currentHasMore, currentLoadingMore });
        }
      },
      {
        root: observerRoot,
        rootMargin: '200px', // Start loading 200px before reaching the target
        threshold: 0.01 // Trigger when even 1% is visible
      }
    );

    console.log('[Infinite Scroll] Starting observation on target');
    observer.observe(currentTarget);

    return () => {
      console.log('[Infinite Scroll] Cleaning up observer');
      observer.unobserve(currentTarget);
      observer.disconnect();
    };
  }, [loadMore, callLogs.length]);

  return (
    <div className="flex h-screen bg-background text-foreground">
      <DashboardSidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-border">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold">Call Logs</h1>
              <p className="text-gray-600">
                View and analyze your VAPI call history ({totalCount} total calls)
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="p-6 border-b border-border bg-muted/50">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-600" />
                <Input
                  placeholder="Search transcripts and summaries..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Automation Filter */}
            <div className="w-[200px]">
              <Select value={selectedAutomation} onValueChange={setSelectedAutomation}>
                <SelectTrigger>
                  <SelectValue placeholder="All Automations" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Automations</SelectItem>
                  {automations.map((automation) => (
                    <SelectItem key={automation._id} value={automation._id}>
                      {automation.automation_name || automation.automationName || 'Unnamed'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Date Range */}
            <div className="flex gap-2">
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-[150px] justify-start text-left font-normal",
                      !startDate && "text-gray-600"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {startDate ? format(startDate, "PPP") : "Start date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <CalendarComponent
                    mode="single"
                    selected={startDate}
                    onSelect={setStartDate}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>

              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-[150px] justify-start text-left font-normal",
                      !endDate && "text-gray-600"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {endDate ? format(endDate, "PPP") : "End date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <CalendarComponent
                    mode="single"
                    selected={endDate}
                    onSelect={setEndDate}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button onClick={applyFilters} size="sm">
                <Filter className="h-4 w-4 mr-2" />
                Apply
              </Button>
              <Button onClick={clearFilters} variant="outline" size="sm">
                Clear
              </Button>
            </div>
          </div>
        </div>

        {/* Call Logs Table */}
        <div ref={scrollContainerRef} className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
                <p className="text-gray-600">Loading call logs...</p>
              </div>
            </div>
          ) : callLogs.length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <Phone className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No call logs found</h3>
                <p className="text-gray-600">
                  {Object.keys(filters).length > 0
                    ? "Try adjusting your filters to see more results."
                    : "Your call logs will appear here once you start making calls."
                  }
                </p>
              </div>
            </div>
          ) : (
            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[100px]">Direction</TableHead>
                        <TableHead>Call Details</TableHead>
                        <TableHead>Assistant</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Duration</TableHead>
                        <TableHead>Cost</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead className="w-[100px]">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {callLogs.map((log) => (
                        <TableRow
                          key={log.id}
                          className="cursor-pointer hover:bg-muted/50"
                          onClick={() => setSelectedLog(log)}
                        >
                          <TableCell>
                            <div className="flex items-center gap-2">
                              {getDirectionIcon(log.direction)}
                              <span className="text-xs capitalize">{log.direction}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="space-y-1">
                              <div className="flex items-center gap-2 text-sm">
                                <span className="font-medium">From:</span>
                                <span>{log.from_phone || 'N/A'}</span>
                              </div>
                              <div className="flex items-center gap-2 text-sm">
                                <span className="font-medium">To:</span>
                                <span>{log.to_phone || 'N/A'}</span>
                              </div>
                              {log.customer_id && (
                                <div className="flex items-center gap-2 text-xs text-gray-600">
                                  <User className="h-3 w-3" />
                                  <span>{log.customer_id}</span>
                                </div>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="space-y-1">
                              <div className="font-medium text-sm">
                                {log.assistant_name || 'Unknown'}
                              </div>
                              <div className="text-xs text-gray-600">
                                {log.assistant_id}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant={getStatusVariant(log.status)} className="capitalize">
                              {log.status.replace('_', ' ')}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Clock className="h-4 w-4 text-gray-600" />
                              <span className="text-sm">{formatDuration(log.duration)}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <DollarSign className="h-4 w-4 text-gray-600" />
                              <span className="text-sm">{formatCost(log.cost)}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="text-sm">
                              {format(new Date(log.start_time || log.created_at), 'MMM dd, yyyy')}
                            </div>
                            <div className="text-xs text-gray-600">
                              {format(new Date(log.start_time || log.created_at), 'HH:mm')}
                            </div>
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedLog(log);
                              }}
                            >
                              View
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Infinite Scroll Loader */}
          {callLogs.length > 0 && (
            <div ref={observerTarget} className="flex flex-col items-center justify-center py-6 min-h-[50px] gap-4">
              {loadingMore ? (
                <div className="flex items-center gap-2 text-gray-600">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span className="text-sm">Loading more calls...</span>
                </div>
              ) : hasMore ? (
                <>
                  <span className="text-sm text-gray-400">Scroll for more...</span>
                  <Button
                    onClick={() => {
                      console.log('[Manual] Load more clicked');
                      loadMore();
                    }}
                    variant="outline"
                    size="sm"
                  >
                    Load More (Manual Test)
                  </Button>
                </>
              ) : (
                <span className="text-sm text-gray-600">
                  All {totalCount} calls loaded
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Call Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-card border border-border rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold">Call Details</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedLog(null)}
              >
                ✕
              </Button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Call Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Call Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <span className="font-medium">Call ID:</span>
                    <span className="font-mono">{selectedLog.call_id}</span>

                    <span className="font-medium">Status:</span>
                    <Badge variant={getStatusVariant(selectedLog.status)} className="w-fit">
                      {selectedLog.status.replace('_', ' ')}
                    </Badge>

                    <span className="font-medium">Direction:</span>
                    <span className="capitalize">{selectedLog.direction}</span>

                    <span className="font-medium">Duration:</span>
                    <span>{formatDuration(selectedLog.duration)}</span>

                    <span className="font-medium">Cost:</span>
                    <span>{formatCost(selectedLog.cost)}</span>

                    <span className="font-medium">From:</span>
                    <span>{selectedLog.from_phone || 'N/A'}</span>

                    <span className="font-medium">To:</span>
                    <span>{selectedLog.to_phone || 'N/A'}</span>
                  </div>
                </CardContent>
              </Card>

              {/* Assistant Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Assistant Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-1 gap-2 text-sm">
                    <div>
                      <span className="font-medium">Name:</span>
                      <span className="ml-2">{selectedLog.assistant_name || 'Unknown'}</span>
                    </div>
                    <div>
                      <span className="font-medium">ID:</span>
                      <span className="ml-2 font-mono">{selectedLog.assistant_id}</span>
                    </div>
                    {selectedLog.sentiment && (
                      <div>
                        <span className="font-medium">Sentiment:</span>
                        <span className="ml-2 capitalize">{selectedLog.sentiment}</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Transcript */}
              {selectedLog.transcript && (
                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle className="text-sm">Transcript</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-muted p-4 rounded-md text-sm max-h-60 overflow-y-auto">
                      {selectedLog.transcript}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Summary */}
              {selectedLog.summary && (
                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle className="text-sm">Summary</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-muted p-4 rounded-md text-sm">
                      {selectedLog.summary}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CallLogs;