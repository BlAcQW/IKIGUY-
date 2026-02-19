import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, HardDrive, MemoryStick, Activity, Server, AlertTriangle, CheckCircle, XCircle, RefreshCw, Trash2, Database, Package, Container, GitBranch } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

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
  const { user, getTenantId } = useMongoAuth();
  const [isLoading, setLoading] = useState(false);
  const [healthData, setHealthData] = useState<SystemHealthData | null>(null);
  const [selectedTab, setSelectedTab] = useState('disk');
  const [cleanupLoading, setCleanupLoading] = useState<string | null>(null);

  // Check if user is admin
  if (!user || user.role !== 'admin') {
    return <Navigate to="/voice-agent" replace />;
  }

  const fetchHealthData = async () => {
    setLoading(true);
    try {
      const headers: any = {};
      const token = localStorage.getItem('mongo_access_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch('/api/system/health', {
        headers,
      });
      
      if (!response.ok) throw new Error('Failed to fetch system health');
      
      const data = await response.json();
      setHealthData(data);
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
      const headers: any = {
        'Content-Type': 'application/json',
      };
      const token = localStorage.getItem('mongo_access_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch('/api/system/cleanup', {
        method: 'POST',
        headers,
        body: JSON.stringify({ type: cleanupType }),
      });
      
      if (!response.ok) throw new Error('Cleanup failed');
      
      const result = await response.json();
      toast({
        title: 'Success',
        description: `Cleanup completed: ${result.freedSpace} freed`,
      });
      
      // Refresh data
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

  useEffect(() => {
    fetchHealthData();
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
    <div className="flex h-screen bg-background">
      <DashboardSidebar />
      <div className="flex-1 overflow-auto">
        <div className="p-8 pb-12">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-3xl font-bold">System Health</h1>
              <p className="text-gray-600">Monitor and optimize your system resources</p>
            </div>
            <Button onClick={fetchHealthData} disabled={isLoading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>

          {isLoading && !healthData ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : (
            <Tabs value={selectedTab} onValueChange={setSelectedTab}>
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="disk">
                  <HardDrive className="h-4 w-4 mr-2" />
                  Disk Usage
                </TabsTrigger>
                <TabsTrigger value="memory">
                  <MemoryStick className="h-4 w-4 mr-2" />
                  Memory & Services
                </TabsTrigger>
                <TabsTrigger value="monitoring">
                  <Activity className="h-4 w-4 mr-2" />
                  Monitoring
                </TabsTrigger>
                <TabsTrigger value="applications">
                  <Server className="h-4 w-4 mr-2" />
                  Applications
                </TabsTrigger>
              </TabsList>

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
                          <div key={index} className="flex justify-between items-center p-2 hover:bg-muted rounded">
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
                                <span className="text-xs text-gray-600">Hash: {dup.hash.substring(0, 8)}...</span>
                              </div>
                              <div className="space-y-1">
                                {dup.paths.map((path, pathIndex) => (
                                  <div key={pathIndex} className="text-xs text-gray-600 truncate">
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

                {/* Services Status */}
                <Card>
                  <CardHeader>
                    <CardTitle>Services Status</CardTitle>
                    <CardDescription>Health and resource usage of system services</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {healthData?.services.map((service) => (
                        <div key={service.name} className="border rounded p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              {getServiceStatusIcon(service.status)}
                              <span className="font-medium">{service.name}</span>
                              <Badge variant={service.status === 'running' ? 'default' : 'secondary'}>
                                {service.status}
                              </Badge>
                            </div>
                            <div className="flex gap-4 text-sm text-gray-600">
                              <span>CPU: {service.cpu}</span>
                              <span>Memory: {service.memory}</span>
                              <span>Uptime: {service.uptime}</span>
                            </div>
                          </div>
                          {service.logs && service.logs.length > 0 && (
                            <div className="mt-2">
                              <details>
                                <summary className="text-sm text-gray-600 cursor-pointer">
                                  Recent logs
                                </summary>
                                <ScrollArea className="h-32 mt-2 p-2 bg-muted rounded">
                                  <pre className="text-xs">
                                    {service.logs.join('\n')}
                                  </pre>
                                </ScrollArea>
                              </details>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
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
                      <p className="text-sm text-gray-600">
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
                      <p className="text-sm text-gray-600">
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
                      <p className="text-sm text-gray-600">
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
                      <p className="text-sm text-gray-600">
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
        </div>
      </div>
    </div>
  );
}