import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import {
  Server,
  Users,
  CheckCircle,
  XCircle,
  RefreshCw,
  Plus,
  Trash2,
  Eye,
  LogOut,
  Database,
  Zap
} from 'lucide-react';

interface FreeSWITCHHealth {
  api: string;
  mongodb: string;
  redis: string;
  freeswitch: string;
}

interface SIPUser {
  username: string;
  phone_number: string;
  context: string;
  enabled: boolean;
  registration_status: string;
  created_at: string;
  updated_at: string;
}

export const FreeSWITCHManagementPanel: React.FC = () => {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [health, setHealth] = useState<FreeSWITCHHealth | null>(null);
  const [users, setUsers] = useState<SIPUser[]>([]);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const FREESWITCH_API_URL = 'https://freeswitch-api.ailabsafrica.com';

  // Fetch health status
  const fetchHealth = async () => {
    try {
      const response = await fetch(`${FREESWITCH_API_URL}/health`);
      if (!response.ok) throw new Error('Failed to fetch FreeSWITCH health');
      const data = await response.json();
      setHealth(data);
    } catch (error) {
      console.error('Error fetching FreeSWITCH health:', error);
      toast({
        title: 'Health Check Failed',
        description: 'Could not connect to FreeSWITCH API',
        variant: 'destructive',
      });
    }
  };

  // Fetch users
  const fetchUsers = async () => {
    try {
      const response = await fetch(`${FREESWITCH_API_URL}/users`);
      if (!response.ok) throw new Error('Failed to fetch users');
      const data = await response.json();
      setUsers(data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  // Reload FreeSWITCH XML
  const handleReloadXML = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${FREESWITCH_API_URL}/reload`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Failed to reload XML');

      const data = await response.json();
      toast({
        title: 'XML Reloaded',
        description: data.message || 'FreeSWITCH XML reloaded successfully',
      });

      await refreshAllData();
    } catch (error) {
      console.error('Error reloading XML:', error);
      toast({
        title: 'Reload Failed',
        description: 'Could not reload FreeSWITCH XML',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Delete user
  const handleDeleteUser = async (username: string) => {
    if (!confirm(`Are you sure you want to delete user "${username}"?`)) {
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${FREESWITCH_API_URL}/users/${username}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Failed to delete user');

      toast({
        title: 'Success',
        description: 'User deleted successfully',
      });

      await refreshAllData();
    } catch (error) {
      console.error('Error deleting user:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete user',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Logout user (force unregister)
  const handleLogoutUser = async (username: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${FREESWITCH_API_URL}/users/${username}/logout`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Failed to logout user');

      toast({
        title: 'Success',
        description: 'User logged out successfully',
      });

      await refreshAllData();
    } catch (error) {
      console.error('Error logging out user:', error);
      toast({
        title: 'Error',
        description: 'Failed to logout user',
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
        fetchHealth(),
        fetchUsers(),
      ]);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Initial load and auto-refresh
  useEffect(() => {
    refreshAllData();

    const interval = setInterval(refreshAllData, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const getHealthBadge = (status: string) => {
    if (status === 'healthy') {
      return <Badge className="bg-green-500">Healthy</Badge>;
    } else if (status.includes('unhealthy')) {
      return <Badge variant="destructive">Unhealthy</Badge>;
    } else {
      return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const getRegistrationBadge = (status: string) => {
    if (status === 'registered') {
      return <Badge className="bg-green-500">Registered</Badge>;
    } else if (status === 'unregistered') {
      return <Badge variant="outline">Not Registered</Badge>;
    } else {
      return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Server className="h-6 w-6 text-indigo-600" />
            FreeSWITCH Management
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Manage SIP users and monitor FreeSWITCH status
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

      {/* Health Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Server className="h-4 w-4" />
              API Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            {getHealthBadge(health?.api || 'unknown')}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Database className="h-4 w-4" />
              MongoDB
            </CardTitle>
          </CardHeader>
          <CardContent>
            {getHealthBadge(health?.mongodb || 'unknown')}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Redis
            </CardTitle>
          </CardHeader>
          <CardContent>
            {getHealthBadge(health?.redis || 'unknown')}
            {health?.redis?.includes('Authentication') && (
              <p className="text-xs text-amber-600 mt-1">Auth required (non-critical)</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Server className="h-4 w-4" />
              FreeSWITCH
            </CardTitle>
          </CardHeader>
          <CardContent>
            {getHealthBadge(health?.freeswitch || 'unknown')}
          </CardContent>
        </Card>
      </div>

      {/* SIP Users Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                SIP Users
              </CardTitle>
              <CardDescription>
                Manage FreeSWITCH SIP users and their registration status
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={handleReloadXML}
                disabled={isLoading}
                variant="outline"
                size="sm"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Reload XML
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {users.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Users className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p className="text-lg font-medium mb-1">No SIP users found</p>
              <p className="text-sm mb-4">Create a phone number via the Phone Routes tab to automatically provision a FreeSWITCH user</p>
            </div>
          ) : (
            <div className="space-y-3">
              {users.map((user) => (
                <div
                  key={user.username}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent transition-colors"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className={`w-3 h-3 rounded-full ${user.registration_status === 'registered' ? 'bg-green-500' : 'bg-gray-300'}`} />

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-mono text-sm font-medium">{user.username}</span>
                        {!user.enabled && (
                          <Badge variant="outline" className="text-xs">Disabled</Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        <span>📞 {user.phone_number}</span>
                        <span>•</span>
                        <span>Context: {user.context}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {getRegistrationBadge(user.registration_status)}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    {user.registration_status === 'registered' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleLogoutUser(user.username)}
                        disabled={isLoading}
                        title="Force logout"
                      >
                        <LogOut className="h-4 w-4 text-amber-500" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteUser(user.username)}
                      disabled={isLoading}
                      title="Delete user"
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
          <CardTitle className="text-sm">FreeSWITCH Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex items-center justify-between p-2 bg-muted rounded">
            <span className="text-muted-foreground">API Endpoint:</span>
            <span className="font-mono text-xs">{FREESWITCH_API_URL}</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-muted rounded">
            <span className="text-muted-foreground">SIP Port:</span>
            <span className="font-mono">5060 (UDP)</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-muted rounded">
            <span className="text-muted-foreground">Domain:</span>
            <span className="font-mono">asterisk.ailabsafrica.com</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-muted rounded">
            <span className="text-muted-foreground">Total Users:</span>
            <span className="font-semibold">{users.length}</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-muted rounded">
            <span className="text-muted-foreground">Registered:</span>
            <span className="font-semibold text-green-600">
              {users.filter(u => u.registration_status === 'registered').length}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
