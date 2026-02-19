import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { API_ENDPOINTS } from '@/config/api-config';
import {
  Server,
  Activity,
  Radio,
  Users,
  RefreshCw,
  CheckCircle,
  XCircle,
  Plus,
  Trash2,
  Eye
} from 'lucide-react';

interface HealthStatus {
  status: string;
  asterisk_connected: boolean;
  ami_version?: string;
  timestamp: string;
}

interface AsteriskStatus {
  status: string;
  uptime?: string;
  active_channels?: number;
  active_calls?: number;
  sip_peers?: number;
}

interface SIPPeer {
  username: string;
  status: string;
  registered: boolean;
}

export const AsteriskManagementPanel: React.FC = () => {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [asteriskStatus, setAsteriskStatus] = useState<AsteriskStatus | null>(null);
  const [sipPeers, setSipPeers] = useState<string[]>([]);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // Fetch health status
  const fetchHealthStatus = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.asterisk.health);
      if (!response.ok) throw new Error('Failed to fetch health status');
      const data = await response.json();
      setHealthStatus(data);
    } catch (error) {
      console.error('Error fetching health status:', error);
      toast({
        title: 'Health Check Failed',
        description: 'Could not connect to Asterisk monitoring service',
        variant: 'destructive',
      });
    }
  };

  // Fetch Asterisk status
  const fetchAsteriskStatus = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.asterisk.status);
      if (!response.ok) throw new Error('Failed to fetch Asterisk status');
      const data = await response.json();
      setAsteriskStatus(data);
    } catch (error) {
      console.error('Error fetching Asterisk status:', error);
    }
  };

  // Fetch SIP peers
  const fetchSIPPeers = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.asterisk.sip.peers);
      if (!response.ok) throw new Error('Failed to fetch SIP peers');
      const data = await response.json();
      setSipPeers(data.peers || []);
    } catch (error) {
      console.error('Error fetching SIP peers:', error);
    }
  };

  // Reload PJSIP configuration
  const handleReloadPJSIP = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(API_ENDPOINTS.asterisk.reload, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Failed to reload PJSIP');

      const data = await response.json();
      toast({
        title: 'PJSIP Reloaded',
        description: data.message || 'PJSIP configuration reloaded successfully',
      });

      await refreshAllData();
    } catch (error) {
      console.error('Error reloading PJSIP:', error);
      toast({
        title: 'Reload Failed',
        description: 'Could not reload PJSIP configuration',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Delete SIP peer
  const handleDeletePeer = async (username: string) => {
    if (!confirm(`Are you sure you want to delete SIP peer "${username}"?`)) {
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(API_ENDPOINTS.asterisk.sip.peer, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          number: username,
          sip_username: username,
        }),
      });

      if (!response.ok) throw new Error('Failed to delete SIP peer');

      toast({
        title: 'Success',
        description: 'SIP peer deleted successfully',
      });

      await refreshAllData();
    } catch (error) {
      console.error('Error deleting SIP peer:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete SIP peer',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Refresh all data
  const refreshAllData = async () => {
    setIsLoading(true);
    try {
      await Promise.all([
        fetchHealthStatus(),
        fetchAsteriskStatus(),
        fetchSIPPeers(),
      ]);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Initial data load and auto-refresh
  useEffect(() => {
    refreshAllData();

    const interval = setInterval(refreshAllData, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Server className="h-6 w-6 text-indigo-600" />
            Asterisk Management
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Monitor and manage Asterisk PBX system
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">
            Last updated: {lastRefresh.toLocaleTimeString()}
          </span>
          <Button
            onClick={refreshAllData}
            disabled={isLoading}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Health Status */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Activity className="h-4 w-4" />
              System Health
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {healthStatus?.status === 'healthy' ? (
                <>
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <Badge variant="default" className="bg-green-500">Healthy</Badge>
                </>
              ) : (
                <>
                  <XCircle className="h-5 w-5 text-red-500" />
                  <Badge variant="destructive">Unhealthy</Badge>
                </>
              )}
            </div>
            {healthStatus?.ami_version && (
              <p className="text-xs text-muted-foreground mt-2">
                {healthStatus.ami_version}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Active Channels */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Radio className="h-4 w-4" />
              Active Channels
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {asteriskStatus?.active_channels ?? '-'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {asteriskStatus?.active_calls ?? 0} active calls
            </p>
          </CardContent>
        </Card>

        {/* SIP Peers */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Users className="h-4 w-4" />
              SIP Peers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {asteriskStatus?.sip_peers ?? sipPeers.length}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Registered endpoints
            </p>
          </CardContent>
        </Card>

        {/* Uptime */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Server className="h-4 w-4" />
              System Uptime
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">
              {asteriskStatus?.uptime || 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Asterisk PBX
            </p>
          </CardContent>
        </Card>
      </div>

      {/* SIP Peers Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                SIP Peers
              </CardTitle>
              <CardDescription>
                Registered SIP endpoints in Asterisk
              </CardDescription>
            </div>
            <Button
              onClick={handleReloadPJSIP}
              disabled={isLoading}
              variant="outline"
              size="sm"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Reload PJSIP
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {sipPeers.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Users className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p className="text-lg font-medium mb-1">No SIP peers found</p>
              <p className="text-sm">Asterisk PJSIP peers will appear here</p>
            </div>
          ) : (
            <div className="space-y-2">
              {sipPeers.map((peer, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-green-500" />
                    <span className="font-mono text-sm">{peer}</span>
                    <Badge variant="outline">Active</Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeletePeer(peer)}
                      disabled={isLoading}
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Asterisk Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex items-center justify-between p-2 bg-muted rounded">
            <span className="text-muted-foreground">API Endpoint:</span>
            <span className="font-mono text-xs">{API_ENDPOINTS.asterisk.base}</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-muted rounded">
            <span className="text-muted-foreground">Status:</span>
            <span className="font-semibold">{asteriskStatus?.status || 'Unknown'}</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-muted rounded">
            <span className="text-muted-foreground">AMI Connected:</span>
            {healthStatus?.asterisk_connected ? (
              <Badge className="bg-green-500">Connected</Badge>
            ) : (
              <Badge variant="destructive">Disconnected</Badge>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
