import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Database as DatabaseIcon,
  RefreshCw,
  Loader2,
  AlertTriangle,
  CheckCircle,
  Download,
  Upload,
  Trash2,
  Clock,
  HardDrive,
  Calendar,
  Shield
} from 'lucide-react';
import { toast } from '@/components/ui/use-toast';
import { API_BASE_URL } from '@/config/api-config';

interface AvailableDatabase {
  name: string;
  type: 'mongodb' | 'postgresql';
}

interface BackupMetadata {
  database_name: string;
  database_type: string;
  backup_type: string;
  organization_id: string;
  timestamp: string;
  file_size: number;
  compressed_size: number;
  backup_path: string;
  status: string;
  error?: string;
}

interface BackupStats {
  total_backups: number;
  total_size_bytes: number;
  total_size_mb: number;
  by_type: Record<string, number>;
  by_database: Record<string, number>;
  latest_backup: BackupMetadata | null;
}

export default function Database() {
  const [loading, setLoading] = useState(false);
  const [backupsLoading, setBackupsLoading] = useState(false);
  const [backupInProgress, setBackupInProgress] = useState(false);
  const [restoreInProgress, setRestoreInProgress] = useState(false);

  const [availableDatabases, setAvailableDatabases] = useState<{
    mongodb: string[];
    postgresql: string[];
  }>({ mongodb: [], postgresql: [] });

  const [backups, setBackups] = useState<BackupMetadata[]>([]);
  const [backupStats, setBackupStats] = useState<BackupStats | null>(null);

  const [selectedDatabase, setSelectedDatabase] = useState<string>('');
  const [selectedDatabaseType, setSelectedDatabaseType] = useState<string>('mongodb');
  const [selectedBackupType, setSelectedBackupType] = useState<string>('manual');
  const [selectedOrganizationId, setSelectedOrganizationId] = useState<string>('default');

  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false);
  const [selectedBackupForRestore, setSelectedBackupForRestore] = useState<BackupMetadata | null>(null);

  const [filterDatabaseType, setFilterDatabaseType] = useState<string>('all');
  const [filterBackupType, setFilterBackupType] = useState<string>('all');

  // Get access token
  const getAccessToken = () => {
    return localStorage.getItem('access_token');
  };

  // Fetch available databases
  const fetchAvailableDatabases = async () => {
    setLoading(true);
    try {
      const token = getAccessToken();
      if (!token) {
        toast({
          title: 'Authentication required',
          description: 'Please log in to access database management',
          variant: 'destructive',
        });
        return;
      }

      const response = await fetch(`${API_BASE_URL}/backups/databases`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch databases: ${response.status}`);
      }

      const data = await response.json();
      setAvailableDatabases(data);

      // Set default selection
      if (data.mongodb.length > 0) {
        setSelectedDatabase(data.mongodb[0]);
        setSelectedDatabaseType('mongodb');
      } else if (data.postgresql.length > 0) {
        setSelectedDatabase(data.postgresql[0]);
        setSelectedDatabaseType('postgresql');
      }

      toast({
        title: 'Databases loaded',
        description: `Found ${data.mongodb.length} MongoDB and ${data.postgresql.length} PostgreSQL databases`,
      });
    } catch (error) {
      console.error('Failed to fetch databases:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to fetch databases',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Fetch backup list
  const fetchBackups = async () => {
    setBackupsLoading(true);
    try {
      const token = getAccessToken();
      if (!token) return;

      const params = new URLSearchParams();
      if (filterDatabaseType !== 'all') {
        params.append('database_type', filterDatabaseType);
      }
      if (filterBackupType !== 'all') {
        params.append('backup_type', filterBackupType);
      }

      const response = await fetch(`${API_BASE_URL}/backups/?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch backups: ${response.status}`);
      }

      const data = await response.json();
      setBackups(data);
    } catch (error) {
      console.error('Failed to fetch backups:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch backup list',
        variant: 'destructive',
      });
    } finally {
      setBackupsLoading(false);
    }
  };

  // Fetch backup stats
  const fetchBackupStats = async () => {
    try {
      const token = getAccessToken();
      if (!token) return;

      const response = await fetch(`${API_BASE_URL}/backups/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch backup stats: ${response.status}`);
      }

      const data = await response.json();
      setBackupStats(data);
    } catch (error) {
      console.error('Failed to fetch backup stats:', error);
    }
  };

  // Create backup
  const handleCreateBackup = async () => {
    if (!selectedDatabase) {
      toast({
        title: 'Selection required',
        description: 'Please select a database to backup',
        variant: 'destructive',
      });
      return;
    }

    setBackupInProgress(true);
    try {
      const token = getAccessToken();
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch(`${API_BASE_URL}/backups/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          database_name: selectedDatabase,
          database_type: selectedDatabaseType,
          organization_id: selectedOrganizationId,
          backup_type: selectedBackupType,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Backup failed: ${response.status}`);
      }

      const data = await response.json();

      toast({
        title: 'Backup created',
        description: `Backup for ${selectedDatabase} created successfully (${(data.compressed_size / (1024 * 1024)).toFixed(2)} MB)`,
      });

      // Refresh backup list and stats
      await fetchBackups();
      await fetchBackupStats();
    } catch (error) {
      console.error('Backup failed:', error);
      toast({
        title: 'Backup failed',
        description: error instanceof Error ? error.message : 'Failed to create backup',
        variant: 'destructive',
      });
    } finally {
      setBackupInProgress(false);
    }
  };

  // Restore backup
  const handleRestoreBackup = async () => {
    if (!selectedBackupForRestore) return;

    setRestoreInProgress(true);
    try {
      const token = getAccessToken();
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch(`${API_BASE_URL}/backups/restore`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          backup_path: selectedBackupForRestore.backup_path,
          target_database_name: null, // Restore to original database
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Restore failed: ${response.status}`);
      }

      const data = await response.json();

      toast({
        title: 'Restore completed',
        description: `Database restored successfully from backup`,
      });

      setRestoreDialogOpen(false);
      setSelectedBackupForRestore(null);
    } catch (error) {
      console.error('Restore failed:', error);
      toast({
        title: 'Restore failed',
        description: error instanceof Error ? error.message : 'Failed to restore backup',
        variant: 'destructive',
      });
    } finally {
      setRestoreInProgress(false);
    }
  };

  // Cleanup old backups
  const handleCleanupBackups = async () => {
    setLoading(true);
    try {
      const token = getAccessToken();
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch(`${API_BASE_URL}/backups/cleanup`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Cleanup failed: ${response.status}`);
      }

      toast({
        title: 'Cleanup completed',
        description: 'Old backups cleaned up successfully',
      });

      // Refresh backup list and stats
      await fetchBackups();
      await fetchBackupStats();
    } catch (error) {
      console.error('Cleanup failed:', error);
      toast({
        title: 'Cleanup failed',
        description: error instanceof Error ? error.message : 'Failed to cleanup backups',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  // Get backup type badge color
  const getBackupTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      daily: 'bg-blue-500',
      weekly: 'bg-green-500',
      monthly: 'bg-purple-500',
      manual: 'bg-gray-500',
    };
    return colors[type] || 'bg-gray-500';
  };

  // Initial load
  useEffect(() => {
    fetchAvailableDatabases();
    fetchBackups();
    fetchBackupStats();
  }, []);

  // Refresh backups when filters change
  useEffect(() => {
    fetchBackups();
  }, [filterDatabaseType, filterBackupType]);

  return (
    <div className="p-8 pb-12">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Database Backup Management</h1>
          <p className="text-muted-foreground">Create and manage database backups</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchBackups} disabled={backupsLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${backupsLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={handleCleanupBackups} variant="outline" disabled={loading}>
            <Trash2 className="h-4 w-4 mr-2" />
            Cleanup Old Backups
          </Button>
        </div>
      </div>

      {/* Backup Stats */}
      {backupStats && (
        <div className="grid gap-4 md:grid-cols-4 mb-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Backups
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{backupStats.total_backups}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Size
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{backupStats.total_size_mb.toFixed(2)} MB</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Daily Backups
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{backupStats.by_type.daily || 0}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Latest Backup
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm">
                {backupStats.latest_backup
                  ? formatTimestamp(backupStats.latest_backup.timestamp)
                  : 'No backups'}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Create Backup */}
      <div className="grid gap-4 md:grid-cols-2 mb-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              Create Backup
            </CardTitle>
            <CardDescription>
              Create a manual backup of a database
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Database Type</label>
              <Select value={selectedDatabaseType} onValueChange={setSelectedDatabaseType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="mongodb">MongoDB</SelectItem>
                  <SelectItem value="postgresql">PostgreSQL</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Database</label>
              <Select value={selectedDatabase} onValueChange={setSelectedDatabase}>
                <SelectTrigger>
                  <SelectValue placeholder="Select database..." />
                </SelectTrigger>
                <SelectContent>
                  {selectedDatabaseType === 'mongodb'
                    ? availableDatabases.mongodb.map((db) => (
                        <SelectItem key={db} value={db}>
                          {db}
                        </SelectItem>
                      ))
                    : availableDatabases.postgresql.map((db) => (
                        <SelectItem key={db} value={db}>
                          {db}
                        </SelectItem>
                      ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Backup Type</label>
              <Select value={selectedBackupType} onValueChange={setSelectedBackupType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="manual">Manual</SelectItem>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              className="w-full"
              onClick={handleCreateBackup}
              disabled={backupInProgress || !selectedDatabase}
            >
              {backupInProgress ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating Backup...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Create Backup
                </>
              )}
            </Button>

            <Alert>
              <Shield className="h-4 w-4" />
              <AlertTitle>Backup Location</AlertTitle>
              <AlertDescription>
                Backups are stored securely in Hetzner Storage Box with encryption.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Retention Policy
            </CardTitle>
            <CardDescription>
              Automatic backup cleanup schedule
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
              <div>
                <div className="font-medium text-sm">Daily Backups</div>
                <div className="text-xs text-muted-foreground">Kept for 7 days</div>
              </div>
              <Badge className="bg-blue-500">{backupStats?.by_type.daily || 0}</Badge>
            </div>

            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div>
                <div className="font-medium text-sm">Weekly Backups</div>
                <div className="text-xs text-muted-foreground">Kept for 4 weeks</div>
              </div>
              <Badge className="bg-green-500">{backupStats?.by_type.weekly || 0}</Badge>
            </div>

            <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
              <div>
                <div className="font-medium text-sm">Monthly Backups</div>
                <div className="text-xs text-muted-foreground">Kept for 12 months</div>
              </div>
              <Badge className="bg-purple-500">{backupStats?.by_type.monthly || 0}</Badge>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <div className="font-medium text-sm">Manual Backups</div>
                <div className="text-xs text-muted-foreground">Kept forever</div>
              </div>
              <Badge className="bg-gray-500">{backupStats?.by_type.manual || 0}</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Backup List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Available Backups</CardTitle>
              <CardDescription>
                List of all available database backups
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Select value={filterDatabaseType} onValueChange={setFilterDatabaseType}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Database type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="mongodb">MongoDB</SelectItem>
                  <SelectItem value="postgresql">PostgreSQL</SelectItem>
                </SelectContent>
              </Select>

              <Select value={filterBackupType} onValueChange={setFilterBackupType}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Backup type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                  <SelectItem value="manual">Manual</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {backupsLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : backups.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No backups found. Create your first backup above.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Database</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Backup Type</TableHead>
                  <TableHead>Timestamp</TableHead>
                  <TableHead className="text-right">Size</TableHead>
                  <TableHead className="text-right">Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {backups.map((backup) => (
                  <TableRow key={backup.backup_path}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <DatabaseIcon className="h-4 w-4 text-muted-foreground" />
                        {backup.database_name}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{backup.database_type}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={getBackupTypeBadge(backup.backup_type)}>
                        {backup.backup_type}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatTimestamp(backup.timestamp)}</TableCell>
                    <TableCell className="text-right">
                      {formatFileSize(backup.compressed_size)}
                    </TableCell>
                    <TableCell className="text-right">
                      {backup.status === 'completed' ? (
                        <CheckCircle className="h-4 w-4 text-green-500 inline" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-red-500 inline" />
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedBackupForRestore(backup);
                          setRestoreDialogOpen(true);
                        }}
                      >
                        <Upload className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Restore Dialog */}
      <Dialog open={restoreDialogOpen} onOpenChange={setRestoreDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Restore Database</DialogTitle>
            <DialogDescription>
              Are you sure you want to restore this backup? This will replace all current data in the database.
            </DialogDescription>
          </DialogHeader>
          {selectedBackupForRestore && (
            <div className="space-y-2 py-4">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Database:</span>
                <span className="font-medium">{selectedBackupForRestore.database_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Type:</span>
                <span className="font-medium">{selectedBackupForRestore.database_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Backup Type:</span>
                <Badge className={getBackupTypeBadge(selectedBackupForRestore.backup_type)}>
                  {selectedBackupForRestore.backup_type}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Timestamp:</span>
                <span className="font-medium">{formatTimestamp(selectedBackupForRestore.timestamp)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Size:</span>
                <span className="font-medium">{formatFileSize(selectedBackupForRestore.compressed_size)}</span>
              </div>
            </div>
          )}
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Warning</AlertTitle>
            <AlertDescription>
              This operation will drop all existing data and replace it with the backup. This cannot be undone.
            </AlertDescription>
          </Alert>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRestoreDialogOpen(false)} disabled={restoreInProgress}>
              Cancel
            </Button>
            <Button onClick={handleRestoreBackup} disabled={restoreInProgress} variant="destructive">
              {restoreInProgress ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Restoring...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Restore Backup
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Warnings */}
      <Alert className="mt-6">
        <Shield className="h-4 w-4" />
        <AlertTitle>Database Backup Management</AlertTitle>
        <AlertDescription>
          All backups are encrypted and stored securely in Hetzner Storage Box. Manual backups are kept forever,
          while automated backups (daily, weekly, monthly) follow the retention policy shown above. Always verify
          backups before deleting any data.
        </AlertDescription>
      </Alert>
    </div>
  );
}
