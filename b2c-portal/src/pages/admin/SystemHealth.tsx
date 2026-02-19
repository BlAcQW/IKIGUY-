import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { API_ENDPOINTS, apiRequest } from '@/config/api';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, HardDrive, MemoryStick, Activity, Server, AlertTriangle, CheckCircle, XCircle, RefreshCw, Trash2, Database, Package, Container, GitBranch, Settings, Cpu, Clock, Zap, XOctagon } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';
import ServiceManagement from '@/components/admin/ServiceManagementUpdated';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

interface DiskUsage {
  filesystem: string;
  size: string;
  used: string;
  available: string;
  usePercent: number;
  mountPoint: string;
}

interface LargeFile {
  path: string;
  size: string;
  sizeBytes: number;
  lastModified: string;
}

interface DuplicateFile {
  paths: string[];
  size: string;
  sizeBytes: number;
  hash: string;
}

interface ServiceStatus {
  name: string;
  status: 'running' | 'stopped' | 'failed' | 'unknown';
  memory: string;
  cpu: string;
  uptime: string;
  logs?: string[];
}

interface TopProcess {
  user: string;
  pid: number;
  cpu: number;
  mem: number;
  command: string;
}

interface SystemOverview {
  cpu: {
    count: number;
    loadAverage: string;
  };
  uptime: string;
  memory: {
    total: string;
    used: string;
    free: string;
    percent: number;
  };
  disk: {
    total: string;
    used: string;
    available: string;
    percent: number;
  };
  topCpuProcesses: TopProcess[];
  topMemProcesses: TopProcess[];
  servicesRunning: number;
  dockerContainers: {
    running: number;
    total: number;
  };
  timestamp: string;
}

interface SystemHealthData {
  diskUsage: DiskUsage[];
  largeFiles: LargeFile[];
  duplicateFiles: DuplicateFile[];
  dockerUsage: {
    images: string;
    containers: string;
    volumes: string;
    buildCache: string;
    reclaimable: string;
  };
  pipCache: {
    size: string;
    fileCount: number;
  };
  mongoLogs: {
    size: string;
    path: string;
  };
  services: ServiceStatus[];
  memoryUsage: {
    total: string;
    used: string;
    free: string;
    percent: number;
  };
}

export default function SystemHealth() {
  const [loading, setLoading] = useState(false);
  const [healthData, setHealthData] = useState<SystemHealthData | null>(null);
  const [overviewData, setOverviewData] = useState<SystemOverview | null>(null);
  const [selectedTab, setSelectedTab] = useState('overview');
  const [cleanupLoading, setCleanupLoading] = useState<string | null>(null);
  const [lastRefreshTime, setLastRefreshTime] = useState<string | null>(null);
  const [killProcessDialogOpen, setKillProcessDialogOpen] = useState(false);
  const [processToKill, setProcessToKill] = useState<TopProcess | null>(null);
  const [killingProcess, setKillingProcess] = useState(false);

  const fetchHealthData = async () => {
    setLoading(true);
    try {
      // Fetch both health and overview data in parallel
      const [healthResponse, overviewResponse] = await Promise.all([
        apiRequest(API_ENDPOINTS.systemHealth),
        apiRequest(API_ENDPOINTS.systemOverview)
      ]);

      if (!healthResponse.ok) throw new Error('Failed to fetch system health');
      if (!overviewResponse.ok) throw new Error('Failed to fetch system overview');

      const healthDataResult = await healthResponse.json();
      const overviewDataResult = await overviewResponse.json();

      setHealthData(healthDataResult);
      setOverviewData(overviewDataResult);

      // Persist data to localStorage
      const timestamp = new Date().toISOString();
      localStorage.setItem('systemHealthData', JSON.stringify(healthDataResult));
      localStorage.setItem('systemOverviewData', JSON.stringify(overviewDataResult));
      localStorage.setItem('systemHealthTimestamp', timestamp);
      setLastRefreshTime(timestamp);

      toast({
        title: 'Success',
        description: 'System health data refreshed',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch system health data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const performCleanup = async (cleanupType: string) => {
    setCleanupLoading(cleanupType);
    try {
      const response = await apiRequest(API_ENDPOINTS.systemCleanup, {
        method: 'POST',
        body: JSON.stringify({ type: cleanupType }),
      });

      if (!response.ok) throw new Error('Cleanup failed');

      const result = await response.json();
      toast({
        title: 'Success',
        description: `Cleanup completed: ${result.freedSpace} freed`,
      });

      // Refresh data and persist
      fetchHealthData();
    } catch (error) {
      toast({
        title: 'Error',
        description: `Failed to perform ${cleanupType} cleanup`,
        variant: 'destructive',
      });
    } finally {
      setCleanupLoading(null);
    }
  };

  const handleKillProcessClick = (process: TopProcess) => {
    setProcessToKill(process);
    setKillProcessDialogOpen(true);
  };

  const handleKillProcess = async () => {
    if (!processToKill) return;

    setKillingProcess(true);
    try {
      const response = await apiRequest(API_ENDPOINTS.processKill, {
        method: 'POST',
        body: JSON.stringify({ pid: processToKill.pid, signal: 'TERM' }),
      });

      if (!response.ok) {
        const error = await response.json();
        const errorMessage = error.detail || 'Failed to kill process';

        // Check if it's a "process not found" error
        if (response.status === 404 || errorMessage.toLowerCase().includes('not found')) {
          toast({
            title: 'Process Not Found',
            description: `Process ${processToKill.pid} no longer exists. It may have already terminated. Refreshing process list...`,
            variant: 'default',
          });

          // Close dialog and refresh data
          setKillProcessDialogOpen(false);
          setProcessToKill(null);

          // Refresh immediately to show updated list
          setTimeout(() => {
            fetchHealthData();
          }, 500);

          return;
        }

        throw new Error(errorMessage);
      }

      const result = await response.json();
      toast({
        title: 'Success',
        description: result.message || `Process ${processToKill.pid} terminated`,
      });

      // Close dialog and refresh data
      setKillProcessDialogOpen(false);
      setProcessToKill(null);

      // Wait a moment then refresh to show updated process list
      setTimeout(() => {
        fetchHealthData();
      }, 1000);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to kill process',
        variant: 'destructive',
      });
    } finally {
      setKillingProcess(false);
    }
  };

  useEffect(() => {
    // Load persisted data from localStorage
    const storedData = localStorage.getItem('systemHealthData');
    const storedOverviewData = localStorage.getItem('systemOverviewData');
    const storedTimestamp = localStorage.getItem('systemHealthTimestamp');

    if (storedData) {
      try {
        setHealthData(JSON.parse(storedData));
        setLastRefreshTime(storedTimestamp);
      } catch (error) {
        console.error('Failed to parse stored health data:', error);
      }
    }

    if (storedOverviewData) {
      try {
        setOverviewData(JSON.parse(storedOverviewData));
      } catch (error) {
        console.error('Failed to parse stored overview data:', error);
      }
    }
  }, []);

  const getDiskUsageColor = (percent: number) => {
    if (percent < 60) return 'text-green-500';
    if (percent < 80) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getServiceStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'stopped':
        return <XCircle className="h-4 w-4 text-gray-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">System Health</h1>
          <p className="text-muted-foreground">
            Monitor and optimize your system resources
            {lastRefreshTime && (
              <span className="block text-xs mt-1">
                Last refreshed: {new Date(lastRefreshTime).toLocaleString()}
              </span>
            )}
          </p>
        </div>
        <Button onClick={fetchHealthData} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {loading && !healthData ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : (
        <Tabs value={selectedTab} onValueChange={setSelectedTab}>
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="overview">
              <Activity className="h-4 w-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="disk">
              <HardDrive className="h-4 w-4 mr-2" />
              Disk Usage
            </TabsTrigger>
            <TabsTrigger value="memory">
              <MemoryStick className="h-4 w-4 mr-2" />
              Memory
            </TabsTrigger>
            <TabsTrigger value="services">
              <Settings className="h-4 w-4 mr-2" />
              Services
            </TabsTrigger>
            <TabsTrigger value="monitoring">
              <Zap className="h-4 w-4 mr-2" />
              Monitoring
            </TabsTrigger>
            <TabsTrigger value="applications">
              <Server className="h-4 w-4 mr-2" />
              Applications
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            {!overviewData ? (
              <div className="text-center text-muted-foreground py-8">
                No overview data available. Click Refresh to load data.
              </div>
            ) : (
              <>
                {/* System Stats Cards */}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">CPU Cores</CardTitle>
                      <Cpu className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{overviewData.cpu.count}</div>
                      <p className="text-xs text-muted-foreground mt-1">
                        Load: {overviewData.cpu.loadAverage}
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Memory</CardTitle>
                      <MemoryStick className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{overviewData.memory.percent}%</div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {overviewData.memory.used} / {overviewData.memory.total}
                      </p>
                      <Progress value={overviewData.memory.percent} className="h-1 mt-2" />
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Disk Usage</CardTitle>
                      <HardDrive className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{overviewData.disk.percent}%</div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {overviewData.disk.used} / {overviewData.disk.total}
                      </p>
                      <Progress value={overviewData.disk.percent} className="h-1 mt-2" />
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Uptime</CardTitle>
                      <Clock className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-lg font-bold">{overviewData.uptime}</div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {overviewData.servicesRunning} services running
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {/* Top Processes */}
                <div className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>Top CPU Processes</span>
                        {overviewData.timestamp && (
                          <span className="text-xs text-muted-foreground font-normal">
                            Updated: {new Date(overviewData.timestamp).toLocaleTimeString()}
                          </span>
                        )}
                      </CardTitle>
                      <CardDescription>Processes consuming the most CPU</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ScrollArea className="h-[280px]">
                        <div className="space-y-2 pr-4">
                          {overviewData.topCpuProcesses.map((proc, index) => (
                            <div key={`cpu-${proc.pid}-${index}`} className="flex items-start justify-between p-3 border rounded-lg hover:bg-accent/10 dark:hover:bg-accent/5 transition-colors gap-3">
                              <div className="flex-1 min-w-0">
                                <div className="font-medium text-sm break-words">{proc.command}</div>
                                <div className="text-xs text-muted-foreground mt-1">
                                  PID: {proc.pid} | User: {proc.user}
                                </div>
                              </div>
                              <div className="flex items-center gap-2 flex-shrink-0">
                                <Badge variant={proc.cpu > 80 ? 'destructive' : proc.cpu > 50 ? 'secondary' : 'outline'}>
                                  {proc.cpu.toFixed(1)}%
                                </Badge>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-7 w-7 p-0"
                                  onClick={() => handleKillProcessClick(proc)}
                                  title="Kill process"
                                >
                                  <XOctagon className="h-4 w-4 text-destructive" />
                                </Button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>Top Memory Processes</span>
                        {overviewData.timestamp && (
                          <span className="text-xs text-muted-foreground font-normal">
                            Updated: {new Date(overviewData.timestamp).toLocaleTimeString()}
                          </span>
                        )}
                      </CardTitle>
                      <CardDescription>Processes consuming the most memory</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ScrollArea className="h-[280px]">
                        <div className="space-y-2 pr-4">
                          {overviewData.topMemProcesses.map((proc, index) => (
                            <div key={`mem-${proc.pid}-${index}`} className="flex items-start justify-between p-3 border rounded-lg hover:bg-accent/10 dark:hover:bg-accent/5 transition-colors gap-3">
                              <div className="flex-1 min-w-0">
                                <div className="font-medium text-sm break-words">{proc.command}</div>
                                <div className="text-xs text-muted-foreground mt-1">
                                  PID: {proc.pid} | User: {proc.user}
                                </div>
                              </div>
                              <div className="flex items-center gap-2 flex-shrink-0">
                                <Badge variant={proc.mem > 20 ? 'destructive' : proc.mem > 10 ? 'secondary' : 'outline'}>
                                  {proc.mem.toFixed(1)}%
                                </Badge>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-7 w-7 p-0"
                                  onClick={() => handleKillProcessClick(proc)}
                                  title="Kill process"
                                >
                                  <XOctagon className="h-4 w-4 text-destructive" />
                                </Button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    </CardContent>
                  </Card>
                </div>

                {/* Docker Info */}
                {overviewData.dockerContainers && overviewData.dockerContainers.running > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Docker Containers</CardTitle>
                      <CardDescription>Container status</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center gap-4">
                        <Badge variant="outline">
                          {overviewData.dockerContainers.running} running
                        </Badge>
                        <Badge variant="outline">
                          {overviewData.dockerContainers.total} total
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            )}
          </TabsContent>

          <TabsContent value="disk" className="space-y-4">
            {/* Disk Usage Overview */}
            <Card>
              <CardHeader>
                <CardTitle>Disk Usage Overview</CardTitle>
                <CardDescription>Current disk space utilization</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {healthData?.diskUsage.map((disk) => (
                  <div key={disk.mountPoint} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>{disk.mountPoint}</span>
                      <span className={getDiskUsageColor(disk.usePercent)}>
                        {disk.used} / {disk.size} ({disk.usePercent}%)
                      </span>
                    </div>
                    <Progress value={disk.usePercent} className="h-2" />
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Cleanup Options */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    MongoDB Logs
                  </CardTitle>
                  <CardDescription>
                    Size: {healthData?.mongoLogs.size || 'N/A'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button 
                    onClick={() => performCleanup('mongo_logs')}
                    disabled={cleanupLoading === 'mongo_logs'}
                    className="w-full"
                  >
                    {cleanupLoading === 'mongo_logs' ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <Trash2 className="h-4 w-4 mr-2" />
                    )}
                    Rotate Logs
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Package className="h-5 w-5" />
                    Pip Cache
                  </CardTitle>
                  <CardDescription>
                    Size: {healthData?.pipCache.size || 'N/A'} ({healthData?.pipCache.fileCount || 0} files)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button 
                    onClick={() => performCleanup('pip_cache')}
                    disabled={cleanupLoading === 'pip_cache'}
                    className="w-full"
                  >
                    {cleanupLoading === 'pip_cache' ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <Trash2 className="h-4 w-4 mr-2" />
                    )}
                    Clear Cache
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Container className="h-5 w-5" />
                    Docker
                  </CardTitle>
                  <CardDescription>
                    Reclaimable: {healthData?.dockerUsage.reclaimable || 'N/A'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button 
                    onClick={() => performCleanup('docker')}
                    disabled={cleanupLoading === 'docker'}
                    className="w-full"
                  >
                    {cleanupLoading === 'docker' ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <Trash2 className="h-4 w-4 mr-2" />
                    )}
                    Clean Docker
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Large Files */}
            <Card>
              <CardHeader>
                <CardTitle>Large Files</CardTitle>
                <CardDescription>Files larger than 500MB</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[300px]">
                  <div className="space-y-2">
                    {healthData?.largeFiles.map((file, index) => (
                      <div key={index} className="flex justify-between items-center p-2 hover:bg-accent/10 dark:hover:bg-accent/5 rounded transition-colors">
                        <span className="text-sm truncate flex-1">{file.path}</span>
                        <Badge variant="outline">{file.size}</Badge>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Duplicate Files */}
            {healthData?.duplicateFiles && healthData.duplicateFiles.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Duplicate Files</CardTitle>
                  <CardDescription>Files with identical content</CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[300px]">
                    <div className="space-y-4">
                      {healthData.duplicateFiles.map((dup, index) => (
                        <div key={index} className="border rounded p-3">
                          <div className="flex justify-between mb-2">
                            <Badge>{dup.size}</Badge>
                            <span className="text-xs text-muted-foreground">Hash: {dup.hash.substring(0, 8)}...</span>
                          </div>
                          <div className="space-y-1">
                            {dup.paths.map((path, pathIndex) => (
                              <div key={pathIndex} className="text-xs text-muted-foreground truncate">
                                {path}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="memory" className="space-y-4">
            {/* Memory Overview */}
            <Card>
              <CardHeader>
                <CardTitle>Memory Usage</CardTitle>
                <CardDescription>System memory utilization</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between text-sm">
                    <span>Memory</span>
                    <span className={getDiskUsageColor(healthData?.memoryUsage.percent || 0)}>
                      {healthData?.memoryUsage.used} / {healthData?.memoryUsage.total} ({healthData?.memoryUsage.percent}%)
                    </span>
                  </div>
                  <Progress value={healthData?.memoryUsage.percent || 0} className="h-2" />
                </div>
              </CardContent>
            </Card>

            {/* Top Memory Consuming Services */}
            <Card>
              <CardHeader>
                <CardTitle>Top Memory Consuming Services</CardTitle>
                <CardDescription>Services sorted by memory usage</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  <div className="space-y-2">
                    {healthData?.services
                      ?.filter(service => service.memory && service.memory !== 'N/A')
                      ?.sort((a, b) => {
                        // Parse memory values for sorting
                        const parseMemory = (mem: string) => {
                          const match = mem.match(/(\d+\.?\d*)\s*(MB|GB|KB)/i);
                          if (!match) return 0;
                          const value = parseFloat(match[1]);
                          const unit = match[2].toUpperCase();
                          return unit === 'GB' ? value * 1024 : unit === 'MB' ? value : value / 1024;
                        };
                        return parseMemory(b.memory) - parseMemory(a.memory);
                      })
                      ?.map((service, index) => (
                        <div key={index} className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent/10 dark:hover:bg-accent/5 transition-colors">
                          <div className="flex items-center gap-3">
                            {getServiceStatusIcon(service.status)}
                            <div>
                              <div className="font-medium">{service.name}</div>
                              <div className="text-xs text-muted-foreground">
                                CPU: {service.cpu || 'N/A'} | Uptime: {service.uptime || 'N/A'}
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <Badge variant={
                              service.memory.includes('GB') ? 'destructive' : 
                              parseInt(service.memory) > 500 ? 'secondary' : 'outline'
                            }>
                              {service.memory}
                            </Badge>
                          </div>
                        </div>
                      )) || (
                        <div className="text-center text-muted-foreground py-8">
                          No service memory data available. Click Refresh to load data.
                        </div>
                      )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Service Management</AlertTitle>
              <AlertDescription>
                For detailed service control (start, stop, restart), please switch to the Services tab.
              </AlertDescription>
            </Alert>
          </TabsContent>

          <TabsContent value="services">
            <ServiceManagement />
          </TabsContent>

          <TabsContent value="monitoring" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Grafana</CardTitle>
                  <CardDescription>Metrics visualization</CardDescription>
                </CardHeader>
                <CardContent>
                  <Badge variant="outline" className="mb-2">Coming Soon</Badge>
                  <p className="text-sm text-muted-foreground">
                    Real-time metrics and dashboards
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Prometheus</CardTitle>
                  <CardDescription>Metrics collection</CardDescription>
                </CardHeader>
                <CardContent>
                  <Badge variant="outline" className="mb-2">Coming Soon</Badge>
                  <p className="text-sm text-muted-foreground">
                    Time-series metrics database
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Kibana</CardTitle>
                  <CardDescription>Log analysis</CardDescription>
                </CardHeader>
                <CardContent>
                  <Badge variant="outline" className="mb-2">Coming Soon</Badge>
                  <p className="text-sm text-muted-foreground">
                    Log aggregation and search
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>ElasticSearch</CardTitle>
                  <CardDescription>Search engine</CardDescription>
                </CardHeader>
                <CardContent>
                  <Badge variant="outline" className="mb-2">Coming Soon</Badge>
                  <p className="text-sm text-muted-foreground">
                    Full-text search and analytics
                  </p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="applications" className="space-y-4">
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Application Health</AlertTitle>
              <AlertDescription>
                Application-specific health monitoring will be available in future updates.
              </AlertDescription>
            </Alert>
          </TabsContent>
        </Tabs>
      )}

      {/* Kill Process Confirmation Dialog */}
      <AlertDialog open={killProcessDialogOpen} onOpenChange={setKillProcessDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Kill Process?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to terminate this process? This action cannot be undone.
              {processToKill && (
                <div className="mt-4 p-3 bg-muted rounded-lg space-y-1">
                  <div className="text-sm">
                    <span className="font-medium">PID:</span> {processToKill.pid}
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">User:</span> {processToKill.user}
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">CPU:</span> {processToKill.cpu.toFixed(1)}%
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">Memory:</span> {processToKill.mem.toFixed(1)}%
                  </div>
                  <div className="text-sm break-words">
                    <span className="font-medium">Command:</span> {processToKill.command}
                  </div>
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={killingProcess}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleKillProcess}
              disabled={killingProcess}
              className="bg-destructive hover:bg-destructive/90"
            >
              {killingProcess ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Killing...
                </>
              ) : (
                'Kill Process'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}