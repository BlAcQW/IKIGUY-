import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import apiClient from '@/config/api';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  FileText,
  RefreshCw,
  Download,
  Trash2,
  Search,
  Filter,
  AlertCircle,
  AlertTriangle,
  Info,
  CheckCircle,
  XCircle,
  Activity,
  Calendar,
  User,
  Server,
} from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

type LogLevel = 'all' | 'info' | 'warning' | 'error' | 'debug' | 'critical';
type LogCategory = 'all' | 'auth' | 'api' | 'database' | 'system' | 'user' | 'automation';

interface LogEntry {
  id: string;
  timestamp: string;
  level: Exclude<LogLevel, 'all'>;
  category: Exclude<LogCategory, 'all'>;
  message: string;
  user?: string;
  source: string;
  details?: string;
}

export default function Logs() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLevel, setSelectedLevel] = useState<LogLevel>('all');
  const [selectedCategory, setSelectedCategory] = useState<LogCategory>('all');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [totalLogs, setTotalLogs] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage] = useState(50);

  // Fetch logs on component mount and when filters change
  useEffect(() => {
    fetchLogs();
  }, [currentPage, selectedLevel, selectedCategory, searchQuery]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchLogs();
      }, 5000);
    }
    return () => clearInterval(interval);
  }, [autoRefresh, currentPage, selectedLevel, selectedCategory, searchQuery]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params: any = {
        page: currentPage,
        per_page: perPage,
      };

      if (selectedLevel && selectedLevel !== 'all') {
        params.level = selectedLevel;
      }

      if (selectedCategory && selectedCategory !== 'all') {
        params.category = selectedCategory;
      }

      if (searchQuery) {
        params.search = searchQuery;
      }

      const response = await apiClient.get('/api/admin/logs', { params });

      setLogs(response.data.logs);
      setFilteredLogs(response.data.logs);
      setTotalLogs(response.data.total);
    } catch (error: any) {
      console.error('Error fetching logs:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to fetch logs',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const filterLogs = () => {
    // Filtering is now done server-side, so this is just for local display
    setFilteredLogs(logs);
  };

  const handleRefresh = async () => {
    await fetchLogs();
    toast({
      title: 'Logs refreshed',
      description: 'Activity logs have been updated',
    });
  };

  const handleExport = () => {
    toast({
      title: 'Export started',
      description: 'Exporting logs to CSV...',
    });
  };

  const handleClearLogs = () => {
    toast({
      title: 'Not Implemented',
      description: 'Log clearing must be done through the system administrator',
      variant: 'destructive',
    });
  };

  const getLevelIcon = (level: Exclude<LogLevel, 'all'>) => {
    switch (level) {
      case 'info':
        return <Info className="h-4 w-4 text-blue-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'debug':
        return <Activity className="h-4 w-4 text-gray-500" />;
      case 'critical':
        return <AlertCircle className="h-4 w-4 text-red-700" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const getLevelBadgeVariant = (level: Exclude<LogLevel, 'all'>) => {
    switch (level) {
      case 'info':
        return 'default';
      case 'warning':
        return 'secondary';
      case 'error':
      case 'critical':
        return 'destructive';
      case 'debug':
        return 'outline';
      default:
        return 'default';
    }
  };

  const getCategoryIcon = (category: Exclude<LogCategory, 'all'>) => {
    switch (category) {
      case 'auth':
        return <User className="h-3 w-3" />;
      case 'database':
        return <Server className="h-3 w-3" />;
      case 'system':
        return <Activity className="h-3 w-3" />;
      default:
        return null;
    }
  };

  const getLogStats = () => {
    return {
      total: logs.length,
      info: logs.filter(l => l.level === 'info').length,
      warning: logs.filter(l => l.level === 'warning').length,
      error: logs.filter(l => l.level === 'error').length,
      critical: logs.filter(l => l.level === 'critical').length,
    };
  };

  const stats = getLogStats();

  return (
    <div className="p-8 pb-12">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Activity Logs</h1>
          <p className="text-muted-foreground">Monitor system activity and events</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button onClick={handleRefresh} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid gap-4 md:grid-cols-5 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Logs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">All activity logs</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Info className="h-4 w-4 text-blue-500" />
              Info
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.info}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
              Warnings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.warning}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <XCircle className="h-4 w-4 text-red-500" />
              Errors
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.error}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-700" />
              Critical
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.critical}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <label className="text-sm font-medium">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search logs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Log Level</label>
              <Select value={selectedLevel} onValueChange={(value) => setSelectedLevel(value as LogLevel)}>
                <SelectTrigger>
                  <SelectValue placeholder="All levels" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="info">Info</SelectItem>
                  <SelectItem value="warning">Warning</SelectItem>
                  <SelectItem value="error">Error</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="debug">Debug</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Category</label>
              <Select value={selectedCategory} onValueChange={(value) => setSelectedCategory(value as LogCategory)}>
                <SelectTrigger>
                  <SelectValue placeholder="All categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  <SelectItem value="auth">Authentication</SelectItem>
                  <SelectItem value="api">API</SelectItem>
                  <SelectItem value="database">Database</SelectItem>
                  <SelectItem value="system">System</SelectItem>
                  <SelectItem value="user">User</SelectItem>
                  <SelectItem value="automation">Automation</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Auto-refresh</label>
              <Button
                variant={autoRefresh ? 'default' : 'outline'}
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                {autoRefresh ? 'On' : 'Off'}
              </Button>
              {autoRefresh && <span className="text-xs text-muted-foreground">Every 5s</span>}
            </div>
            <div className="text-sm text-muted-foreground">
              Showing {filteredLogs.length} of {totalLogs} logs
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>System Logs</CardTitle>
              <CardDescription>Recent activity and system events</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={handleClearLogs}>
              <Trash2 className="h-4 w-4 mr-2" />
              Clear Logs
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[180px]">Timestamp</TableHead>
                  <TableHead className="w-[100px]">Level</TableHead>
                  <TableHead className="w-[120px]">Category</TableHead>
                  <TableHead>Message</TableHead>
                  <TableHead className="w-[150px]">Source</TableHead>
                  <TableHead className="w-[180px]">User</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredLogs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                      No logs found matching your filters
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredLogs.map((log) => (
                    <TableRow key={log.id} className="group">
                      <TableCell className="font-mono text-xs">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-3 w-3 text-muted-foreground" />
                          {log.timestamp}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getLevelBadgeVariant(log.level)} className="flex items-center gap-1 w-fit">
                          {getLevelIcon(log.level)}
                          {log.level}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="flex items-center gap-1 w-fit">
                          {getCategoryIcon(log.category)}
                          {log.category}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{log.message}</div>
                          {log.details && (
                            <div className="text-xs text-muted-foreground mt-1">{log.details}</div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">{log.source}</TableCell>
                      <TableCell className="text-sm">
                        {log.user && (
                          <div className="flex items-center gap-2">
                            <User className="h-3 w-3 text-muted-foreground" />
                            {log.user}
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
