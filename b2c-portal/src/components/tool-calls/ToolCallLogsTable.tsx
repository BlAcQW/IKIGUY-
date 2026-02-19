/**
 * Tool Call Logs Table Component
 *
 * Displays tool call logs in a paginated table with filtering capabilities.
 * Can be used standalone or embedded in other pages/modals.
 */

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Search,
  Filter,
  Download,
  Clock,
  Target,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Zap,
  Database,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import {
  toolCallLogsService,
  ToolCallLog,
  ToolCallLogsFilter,
  ToolCallStatus,
} from '@/services/ToolCallLogsService';
import { ToolCallLogDetailModal } from './ToolCallLogDetailModal';

interface ToolCallLogsTableProps {
  /** Filter by company/knowledge base name */
  companyName?: string;
  /** Filter by automation ID */
  automationId?: string;
  /** Show filters bar */
  showFilters?: boolean;
  /** Show export button */
  showExport?: boolean;
  /** Initial page size */
  pageSize?: number;
  /** Custom className */
  className?: string;
  /** Compact mode (smaller text, tighter spacing) */
  compact?: boolean;
}

export const ToolCallLogsTable: React.FC<ToolCallLogsTableProps> = ({
  companyName,
  automationId,
  showFilters = true,
  showExport = true,
  pageSize = 50,
  className,
  compact = false,
}) => {
  const { toast } = useToast();

  // State
  const [logs, setLogs] = useState<ToolCallLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState<ToolCallLog | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Filters
  const [searchKeyword, setSearchKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState<ToolCallStatus | 'all'>('all');
  const [daysFilter, setDaysFilter] = useState<number>(7);

  // Fetch logs
  const fetchLogs = async () => {
    setLoading(true);
    try {
      const filters: ToolCallLogsFilter = {
        page,
        page_size: pageSize,
        days: daysFilter,
      };

      if (companyName) filters.company_name = companyName;
      if (automationId) filters.automation_id = automationId;
      if (statusFilter !== 'all') filters.status = statusFilter;
      if (searchKeyword.trim()) filters.search = searchKeyword.trim();

      const response = await toolCallLogsService.getToolCallLogs(filters);

      setLogs(response.logs);
      setTotalCount(response.total);
      setTotalPages(response.total_pages);
    } catch (error) {
      console.error('Error fetching tool call logs:', error);
      toast({
        title: 'Failed to load tool call logs',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Export logs to CSV
  const handleExport = async () => {
    try {
      toast({
        title: 'Exporting logs...',
        description: 'This may take a moment for large datasets.',
      });

      const filters: ToolCallLogsFilter = {
        days: daysFilter,
      };

      if (companyName) filters.company_name = companyName;
      if (automationId) filters.automation_id = automationId;
      if (statusFilter !== 'all') filters.status = statusFilter;
      if (searchKeyword.trim()) filters.search = searchKeyword.trim();

      const csv = await toolCallLogsService.exportToCSV(filters);

      // Download CSV
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tool-call-logs-${format(new Date(), 'yyyy-MM-dd')}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: 'Export successful',
        description: `${totalCount} logs exported to CSV.`,
      });
    } catch (error) {
      console.error('Error exporting logs:', error);
      toast({
        title: 'Export failed',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
    }
  };

  // Apply filters
  const applyFilters = () => {
    setPage(1);
    fetchLogs();
  };

  // Clear filters
  const clearFilters = () => {
    setSearchKeyword('');
    setStatusFilter('all');
    setDaysFilter(7);
    setPage(1);
  };

  // Effects
  useEffect(() => {
    fetchLogs();
  }, [page, companyName, automationId]);

  // Helper functions
  const getStatusBadge = (status: ToolCallStatus) => {
    const variants = {
      success: { variant: 'default' as const, icon: CheckCircle, color: 'text-green-600' },
      failed: { variant: 'destructive' as const, icon: XCircle, color: 'text-red-600' },
      timeout: { variant: 'outline' as const, icon: Clock, color: 'text-orange-600' },
      error: { variant: 'destructive' as const, icon: AlertTriangle, color: 'text-red-600' },
    };

    const config = variants[status] || variants.error;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="capitalize">
        <Icon className="h-3 w-3 mr-1" />
        {status}
      </Badge>
    );
  };

  const formatMs = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Filters */}
      {showFilters && (
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-600" />
              <Input
                placeholder="Search queries and responses..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && applyFilters()}
                className="pl-10"
              />
            </div>
          </div>

          {/* Status Filter */}
          <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as any)}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="success">Success</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="timeout">Timeout</SelectItem>
              <SelectItem value="error">Error</SelectItem>
            </SelectContent>
          </Select>

          {/* Days Filter */}
          <Select value={daysFilter.toString()} onValueChange={(value) => setDaysFilter(parseInt(value))}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Last 7 days" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">Last 24 hours</SelectItem>
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
            </SelectContent>
          </Select>

          {/* Action Buttons */}
          <div className="flex gap-2">
            <Button onClick={applyFilters} size="sm">
              <Filter className="h-4 w-4 mr-2" />
              Apply
            </Button>
            <Button onClick={clearFilters} variant="outline" size="sm">
              Clear
            </Button>
            {showExport && (
              <Button onClick={handleExport} variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
            <p className="text-gray-600">Loading tool call logs...</p>
          </div>
        </div>
      ) : logs.length === 0 ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Database className="h-12 w-12 text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No tool calls found</h3>
            <p className="text-gray-600">
              {searchKeyword || statusFilter !== 'all'
                ? 'Try adjusting your filters to see more results.'
                : 'Tool call logs will appear here as queries are processed.'}
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
                    <TableHead className={compact ? 'text-xs' : ''}>Query</TableHead>
                    <TableHead className={compact ? 'text-xs w-[100px]' : 'w-[120px]'}>Status</TableHead>
                    <TableHead className={compact ? 'text-xs w-[80px]' : 'w-[100px]'}>Confidence</TableHead>
                    <TableHead className={compact ? 'text-xs w-[80px]' : 'w-[100px]'}>Time</TableHead>
                    <TableHead className={compact ? 'text-xs w-[60px]' : 'w-[80px]'}>Sources</TableHead>
                    <TableHead className={compact ? 'text-xs w-[100px]' : 'w-[120px]'}>Date</TableHead>
                    <TableHead className={compact ? 'text-xs w-[80px]' : 'w-[100px]'}>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow
                      key={log.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => setSelectedLog(log)}
                    >
                      <TableCell>
                        <div className="space-y-1 max-w-md">
                          <div className={cn('font-medium', compact ? 'text-xs' : 'text-sm')}>
                            {log.query_original}
                          </div>
                          {log.query_normalized && log.query_normalized !== log.query_original && (
                            <div className="text-xs text-gray-600">
                              Normalized: {log.query_normalized}
                            </div>
                          )}
                          <div className={cn('text-gray-600 line-clamp-1', compact ? 'text-xs' : 'text-sm')}>
                            {log.response}
                          </div>
                          <div className="flex items-center gap-2 flex-wrap">
                            {log.is_cached && (
                              <Badge variant="secondary" className="text-xs">
                                <Zap className="h-3 w-3 mr-1" />
                                Cached
                              </Badge>
                            )}
                            {log.requires_escalation && (
                              <Badge variant="outline" className="text-xs text-orange-600">
                                <AlertTriangle className="h-3 w-3 mr-1" />
                                Escalated
                              </Badge>
                            )}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(log.status)}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Target className={cn('h-4 w-4', getConfidenceColor(log.confidence_score))} />
                          <span className={cn(compact ? 'text-xs' : 'text-sm', getConfidenceColor(log.confidence_score))}>
                            {(log.confidence_score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-gray-600" />
                          <span className={compact ? 'text-xs' : 'text-sm'}>{formatMs(log.processing_time)}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className={compact ? 'text-xs' : ''}>
                          {log.sources_used.length}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className={compact ? 'text-xs' : 'text-sm'}>
                          {format(new Date(log.created_at), 'MMM dd, yyyy')}
                        </div>
                        <div className="text-xs text-gray-600">
                          {format(new Date(log.created_at), 'HH:mm:ss')}
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

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Showing {logs.length} of {totalCount} logs
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
            >
              Previous
            </Button>
            <span className="text-sm text-gray-600">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page + 1)}
              disabled={page === totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {selectedLog && (
        <ToolCallLogDetailModal
          log={selectedLog}
          open={!!selectedLog}
          onClose={() => setSelectedLog(null)}
        />
      )}
    </div>
  );
};

export default ToolCallLogsTable;
