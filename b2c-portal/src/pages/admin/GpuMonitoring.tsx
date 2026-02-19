import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, Cpu, MemoryStick, Thermometer, Activity, RefreshCw, AlertTriangle } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';
import { API_ENDPOINTS, apiRequest } from '@/config/api';

interface GpuProcess {
  pid: number;
  processName: string;
  usedMemory: string;
  usedMemoryBytes: number;
}

interface GpuDevice {
  index: number;
  name: string;
  driverVersion: string;
  cudaVersion: string;
  totalMemory: string;
  usedMemory: string;
  freeMemory: string;
  memoryPercent: number;
  utilizationGpu: number;
  utilizationMemory: number;
  temperature: number;
  powerDraw: string;
  powerLimit: string;
  processes: GpuProcess[];
}

interface GpuMonitoringData {
  gpus: GpuDevice[];
  timestamp: string;
  available: boolean;
  error?: string;
}

export default function GpuMonitoring() {
  const [isLoading, setLoading] = useState(false);
  const [gpuData, setGpuData] = useState<GpuMonitoringData | null>(null);

  const fetchGpuData = async () => {
    setLoading(true);
    try {
      const response = await apiRequest(API_ENDPOINTS.systemGpu);

      if (!response.ok) throw new Error('Failed to fetch GPU data');

      const data = await response.json();
      setGpuData(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch GPU monitoring data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGpuData();
    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchGpuData, 5000);
    return () => clearInterval(interval);
  }, []);

  const getUtilizationColor = (percent: number) => {
    if (percent < 50) return 'text-green-500';
    if (percent < 80) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getTemperatureColor = (temp: number) => {
    if (temp < 70) return 'text-green-500';
    if (temp < 85) return 'text-yellow-500';
    return 'text-red-500';
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="p-8 pb-12">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">GPU Monitoring</h1>
          <p className="text-muted-foreground">Real-time GPU status and performance metrics</p>
        </div>
        <Button onClick={fetchGpuData} disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {isLoading && !gpuData ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : gpuData && !gpuData.available ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              No GPU Available
            </CardTitle>
            <CardDescription>
              {gpuData.error || 'No NVIDIA GPU detected or NVIDIA drivers not installed'}
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <div className="space-y-6">
          {gpuData?.gpus.map((gpu) => (
            <Card key={gpu.index}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Cpu className="h-5 w-5" />
                      GPU {gpu.index}: {gpu.name}
                    </CardTitle>
                    <CardDescription className="mt-2 space-y-1">
                      <div>Driver Version: {gpu.driverVersion}</div>
                      <div>CUDA Version: {gpu.cudaVersion}</div>
                      <div>Power: {gpu.powerDraw} / {gpu.powerLimit}</div>
                    </CardDescription>
                  </div>
                  <Badge variant={gpu.utilizationGpu > 80 ? 'destructive' : 'default'}>
                    {gpu.utilizationGpu}% Utilization
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* GPU Utilization */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Activity className="h-4 w-4" />
                      <span className="text-sm font-medium">GPU Utilization</span>
                    </div>
                    <span className={`text-sm font-medium ${getUtilizationColor(gpu.utilizationGpu)}`}>
                      {gpu.utilizationGpu}%
                    </span>
                  </div>
                  <Progress value={gpu.utilizationGpu} className="h-2" />
                </div>

                {/* Memory Usage */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <MemoryStick className="h-4 w-4" />
                      <span className="text-sm font-medium">Memory Usage</span>
                    </div>
                    <span className={`text-sm font-medium ${getUtilizationColor(gpu.memoryPercent)}`}>
                      {gpu.usedMemory} / {gpu.totalMemory} ({gpu.memoryPercent}%)
                    </span>
                  </div>
                  <Progress value={gpu.memoryPercent} className="h-2" />
                </div>

                {/* Temperature */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Thermometer className="h-4 w-4" />
                      <span className="text-sm font-medium">Temperature</span>
                    </div>
                    <span className={`text-sm font-medium ${getTemperatureColor(gpu.temperature)}`}>
                      {gpu.temperature}°C
                    </span>
                  </div>
                  <Progress value={(gpu.temperature / 100) * 100} className="h-2" />
                </div>

                {/* Running Processes */}
                {gpu.processes && gpu.processes.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">Running Processes ({gpu.processes.length})</h3>
                    <ScrollArea className="h-[200px]">
                      <div className="space-y-2">
                        {gpu.processes.map((process) => (
                          <div key={process.pid} className="flex justify-between items-center p-2 hover:bg-muted rounded border">
                            <div className="flex-1">
                              <div className="text-sm font-medium">{process.processName}</div>
                              <div className="text-xs text-muted-foreground">PID: {process.pid}</div>
                            </div>
                            <Badge variant="outline">{process.usedMemory}</Badge>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>
                )}

                {gpu.processes && gpu.processes.length === 0 && (
                  <div className="text-sm text-muted-foreground text-center p-4 border rounded">
                    No processes currently using this GPU
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {gpuData && (
        <div className="mt-4 text-xs text-muted-foreground text-right">
          Last updated: {new Date(gpuData.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  );
}
