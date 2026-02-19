import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/components/ui/use-toast';
import { 
  Activity, 
  Globe, 
  Settings, 
  RefreshCw, 
  Trash2, 
  Download,
  Upload,
  Zap
} from 'lucide-react';

interface CDNStats {
  totalAssets: number;
  cachedAssets: number;
  cacheHitRate: number;
  averageResponseTime: number;
  bandwidthUsed: number;
  storageUsed: number;
}

interface CDNHealth {
  status: 'healthy' | 'degraded' | 'unavailable';
  responseTime: number;
  lastCheck: string;
}

const CDNDashboard = () => {
  const { toast } = useToast();
  const [stats, setStats] = useState<CDNStats>({
    totalAssets: 0,
    cachedAssets: 0,
    cacheHitRate: 0,
    averageResponseTime: 0,
    bandwidthUsed: 0,
    storageUsed: 0
  });
  const [health, setHealth] = useState<CDNHealth>({
    status: 'unavailable',
    responseTime: 0,
    lastCheck: new Date().toISOString()
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCDNData();
  }, []);

  const loadCDNData = async () => {
    setLoading(true);
    try {
      // Simulate loading CDN data
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setStats({
        totalAssets: 1247,
        cachedAssets: 1189,
        cacheHitRate: 95.3,
        averageResponseTime: 45,
        bandwidthUsed: 2.4,
        storageUsed: 8.7
      });

      setHealth({
        status: 'healthy',
        responseTime: 45,
        lastCheck: new Date().toISOString()
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load CDN data",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800';
      case 'unavailable':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const clearCache = async () => {
    try {
      // Simulate cache clearing
      await new Promise(resolve => setTimeout(resolve, 2000));
      toast({
        title: "Success",
        description: "CDN cache cleared successfully",
      });
      loadCDNData();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to clear cache",
        variant: "destructive",
      });
    }
  };

  const refreshHealth = async () => {
    try {
      setHealth(prev => ({ ...prev, status: 'degraded' }));
      await new Promise(resolve => setTimeout(resolve, 1000));
      setHealth({
        status: 'healthy',
        responseTime: Math.floor(Math.random() * 50) + 20,
        lastCheck: new Date().toISOString()
      });
      toast({
        title: "Success",
        description: "Health check completed",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Health check failed",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">CDN Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor and manage your Content Delivery Network
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={refreshHealth}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh Health
          </Button>
          <Button variant="outline" onClick={clearCache}>
            <Trash2 className="h-4 w-4 mr-2" />
            Clear Cache
          </Button>
        </div>
      </div>

      {/* Health Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            CDN Health Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Badge className={getHealthColor(health.status)}>
                {health.status.toUpperCase()}
              </Badge>
              <div>
                <p className="text-sm text-muted-foreground">Response Time</p>
                <p className="font-semibold">{health.responseTime}ms</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-muted-foreground">Last Check</p>
              <p className="text-sm">{new Date(health.lastCheck).toLocaleTimeString()}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Assets</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalAssets.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Files served via CDN
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cache Hit Rate</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.cacheHitRate}%</div>
            <Progress value={stats.cacheHitRate} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {stats.cachedAssets} of {stats.totalAssets} assets cached
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.averageResponseTime}ms</div>
            <p className="text-xs text-muted-foreground">
              Average CDN response time
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Bandwidth Used</CardTitle>
            <Download className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.bandwidthUsed} TB</div>
            <p className="text-xs text-muted-foreground">
              This month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Storage Used</CardTitle>
            <Upload className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.storageUsed} GB</div>
            <p className="text-xs text-muted-foreground">
              CDN storage utilization
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CDN Status</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Active</div>
            <p className="text-xs text-muted-foreground">
              All regions operational
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>
            Latest CDN operations and events
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <div>
                  <p className="text-sm font-medium">Cache refreshed</p>
                  <p className="text-xs text-muted-foreground">2 minutes ago</p>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <div>
                  <p className="text-sm font-medium">New asset uploaded</p>
                  <p className="text-xs text-muted-foreground">15 minutes ago</p>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <div>
                  <p className="text-sm font-medium">Health check passed</p>
                  <p className="text-xs text-muted-foreground">1 hour ago</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CDNDashboard;
