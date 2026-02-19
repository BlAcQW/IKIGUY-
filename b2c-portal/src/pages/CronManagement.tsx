/**
 * Cron Management Page
 *
 * Admin page for managing scheduled cron jobs.
 * Shows all registered cron jobs with ability to pause, resume, and delete.
 */

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
  Clock,
  Play,
  Pause,
  Trash2,
  AlertTriangle,
  CheckCircle,
  MoreVertical,
  RefreshCw,
  Activity,
  Calendar,
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { cronManagementService, CronJob, CronStats } from '@/services/CronManagementService';
import { format, formatDistanceToNow } from 'date-fns';
import CreateCronJobDialog from '@/components/cron/CreateCronJobDialog';

const CronManagement: React.FC = () => {
  const { toast } = useToast();

  // State
  const [jobs, setJobs] = useState<CronJob[]>([]);
  const [stats, setStats] = useState<CronStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  // Delete confirmation dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [jobToDelete, setJobToDelete] = useState<CronJob | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Create job dialog
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Load demo jobs
  const handleLoadDemoJobs = async () => {
    try {
      setLoading(true);
      await cronManagementService.initializeDemoJobs();
      toast({
        title: 'Demo jobs loaded',
        description: '5 demo cron jobs have been created successfully.',
      });
      await fetchData();
    } catch (error) {
      toast({
        title: 'Failed to load demo jobs',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Fetch jobs and stats
  const fetchData = async () => {
    setLoading(true);
    try {
      const [jobsResponse, statsResponse] = await Promise.all([
        cronManagementService.getCronJobs(
          statusFilter === 'all' ? undefined : statusFilter,
          typeFilter === 'all' ? undefined : typeFilter
        ),
        cronManagementService.getCronStats(),
      ]);

      setJobs(jobsResponse.jobs || []);
      setStats(statsResponse.stats);
    } catch (error) {
      console.error('Error fetching cron data:', error);
      toast({
        title: 'Failed to load cron jobs',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  // Pause job
  const handlePause = async (job: CronJob) => {
    try {
      await cronManagementService.pauseCronJob(job.id);
      toast({
        title: 'Job paused',
        description: `${job.name} has been paused successfully.`,
      });
      fetchData();
    } catch (error) {
      console.error('Error pausing job:', error);
      toast({
        title: 'Failed to pause job',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
    }
  };

  // Resume job
  const handleResume = async (job: CronJob) => {
    try {
      await cronManagementService.resumeCronJob(job.id);
      toast({
        title: 'Job resumed',
        description: `${job.name} has been resumed successfully.`,
      });
      fetchData();
    } catch (error) {
      console.error('Error resuming job:', error);
      toast({
        title: 'Failed to resume job',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
    }
  };

  // Delete job
  const handleDelete = async () => {
    if (!jobToDelete) return;

    setDeleting(true);
    try {
      await cronManagementService.deleteCronJob(jobToDelete.id);
      toast({
        title: 'Job deleted',
        description: `${jobToDelete.name} has been successfully removed.`,
      });
      fetchData();
      setDeleteDialogOpen(false);
      setJobToDelete(null);
    } catch (error) {
      console.error('Error deleting job:', error);
      toast({
        title: 'Failed to delete job',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
    } finally {
      setDeleting(false);
    }
  };

  // Filter jobs
  const filteredJobs = jobs.filter((job) => {
    const matchesSearch =
      searchKeyword === '' ||
      job.name.toLowerCase().includes(searchKeyword.toLowerCase()) ||
      job.description.toLowerCase().includes(searchKeyword.toLowerCase()) ||
      job.func_name.toLowerCase().includes(searchKeyword.toLowerCase());

    return matchesSearch;
  });

  // Get unique job types
  const jobTypes = Array.from(new Set(jobs.map((j) => j.job_type)));

  useEffect(() => {
    fetchData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [statusFilter, typeFilter]);

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-border">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Clock className="h-6 w-6" />
                Cron Management
              </h1>
              <p className="text-gray-600">
                Manage scheduled jobs and monitor execution ({filteredJobs.length} jobs)
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button onClick={() => setCreateDialogOpen(true)} size="sm">
                <Calendar className="h-4 w-4 mr-2" />
                Create Job
              </Button>
              <Button onClick={fetchData} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="p-6 grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Total Jobs</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_jobs}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Active Jobs</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">{stats.active_jobs}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Paused Jobs</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-600">{stats.paused_jobs}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Success Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">{stats.recent_success_rate}%</div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filters */}
        <div className="p-6 border-b border-border bg-muted/50">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-600" />
                <Input
                  placeholder="Search jobs by name, description, or function..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Status Filter */}
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="paused">Paused</SelectItem>
              </SelectContent>
            </Select>

            {/* Type Filter */}
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="All Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {jobTypes.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Jobs Table */}
        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
                <p className="text-gray-600">Loading cron jobs...</p>
              </div>
            </div>
          ) : filteredJobs.length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center max-w-md">
                <Clock className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No cron jobs found</h3>
                <p className="text-gray-600 mb-4">
                  {searchKeyword || statusFilter !== 'all' || typeFilter !== 'all'
                    ? 'Try adjusting your filters to see more results.'
                    : 'No scheduled cron jobs are currently registered.'}
                </p>
                {!searchKeyword && statusFilter === 'all' && typeFilter === 'all' && (
                  <div className="text-sm text-muted-foreground space-y-2">
                    <p>
                      Cron jobs are automatically created when you:
                    </p>
                    <ul className="list-disc list-inside text-left space-y-1">
                      <li>Schedule voice campaigns with recurring patterns</li>
                      <li>Set up automated tasks in your workflows</li>
                      <li>Create custom scheduled jobs using the API</li>
                    </ul>
                    <div className="mt-4 pt-4 border-t">
                      <p className="mb-2">Want to see how it works?</p>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleLoadDemoJobs}
                        disabled={loading}
                      >
                        Load Demo Jobs
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Job Name</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Trigger</TableHead>
                        <TableHead>Next Run</TableHead>
                        <TableHead className="w-[100px]">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredJobs.map((job) => (
                        <TableRow key={job.id}>
                          <TableCell>
                            <div>
                              <div className="flex items-center gap-2">
                                <Clock className="h-4 w-4 text-gray-600" />
                                <span className="font-medium">{job.name}</span>
                              </div>
                              <p className="text-xs text-gray-600 mt-1">{job.description}</p>
                              <p className="text-xs text-gray-600 mt-1">
                                Function: <span className="font-mono">{job.func_name}</span>
                              </p>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="capitalize">
                              {job.job_type}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {job.is_paused ? (
                              <Badge variant="secondary">
                                <Pause className="h-3 w-3 mr-1" />
                                Paused
                              </Badge>
                            ) : (
                              <Badge variant="default" className="bg-green-600">
                                <Play className="h-3 w-3 mr-1" />
                                Active
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <div className="text-sm">
                              <Badge variant="outline">{job.trigger_type}</Badge>
                              {job.trigger_details?.expression && (
                                <p className="text-xs text-gray-600 mt-1 font-mono">
                                  {job.trigger_details.expression}
                                </p>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            {job.next_run_time ? (
                              <div className="text-sm">
                                <div>{format(new Date(job.next_run_time), 'PPp')}</div>
                                <div className="text-xs text-gray-600">
                                  {formatDistanceToNow(new Date(job.next_run_time), { addSuffix: true })}
                                </div>
                              </div>
                            ) : (
                              <span className="text-sm text-gray-600">Not scheduled</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="sm">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                {job.is_paused ? (
                                  <DropdownMenuItem onClick={() => handleResume(job)}>
                                    <Play className="h-4 w-4 mr-2" />
                                    Resume
                                  </DropdownMenuItem>
                                ) : (
                                  <DropdownMenuItem onClick={() => handlePause(job)}>
                                    <Pause className="h-4 w-4 mr-2" />
                                    Pause
                                  </DropdownMenuItem>
                                )}
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  className="text-destructive"
                                  onClick={() => {
                                    setJobToDelete(job);
                                    setDeleteDialogOpen(true);
                                  }}
                                >
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Cron Job</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete <strong>{jobToDelete?.name}</strong>?
              This action cannot be undone and will remove the scheduled job from the system.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setDeleteDialogOpen(false);
                setJobToDelete(null);
              }}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? 'Deleting...' : 'Delete Job'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Job Dialog */}
      <CreateCronJobDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSuccess={fetchData}
      />
    </div>
  );
};

export default CronManagement;
