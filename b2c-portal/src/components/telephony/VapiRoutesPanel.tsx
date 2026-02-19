import React, { useState, useEffect } from 'react';
import { ArrowRight, Phone, Bot, Activity, Clock, AlertCircle, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { API_ENDPOINTS } from '@/config/api-config';
import { useToast } from '@/hooks/use-toast';

interface PhoneNumber {
  id: string;
  number: string;
  provider: string;
  status: string;
  assigned_assistant_id?: string;
  assigned_at?: string;
  webhook_url?: string;
}

interface VapiCall {
  call_id: string;
  to_number: string;
  assistant_id: string;
  status: string;
  started_at: string;
  metadata?: Record<string, any>;
}

interface VapiRoutesPanelProps {
  onRefresh?: () => void;
}

export const VapiRoutesPanel: React.FC<VapiRoutesPanelProps> = ({ onRefresh }) => {
  const { toast } = useToast();
  const [phoneNumbers, setPhoneNumbers] = useState<PhoneNumber[]>([]);
  const [activeCalls, setActiveCalls] = useState<VapiCall[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch phone numbers and active calls
  const fetchData = async () => {
    try {
      setIsLoading(true);

      // Fetch phone numbers
      const phoneResponse = await fetch(API_ENDPOINTS.phoneNumbers.list);
      if (phoneResponse.ok) {
        const phoneData = await phoneResponse.json();
        setPhoneNumbers(phoneData.numbers || []);
      }

      // Fetch active Vapi calls
      const callsResponse = await fetch(API_ENDPOINTS.vapi.call.active);
      if (callsResponse.ok) {
        const callsData = await callsResponse.json();
        setActiveCalls(callsData.calls || []);
      }
    } catch (error: any) {
      console.error('Error fetching Vapi routes data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load Vapi routing data',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchData();
    if (onRefresh) onRefresh();
  };

  // Calculate routing stats
  const assignedRoutes = phoneNumbers.filter(p => p.assigned_assistant_id);
  const unassignedNumbers = phoneNumbers.filter(p => !p.assigned_assistant_id);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <p className="mt-2 text-sm text-muted-foreground">Loading Vapi routes...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Routes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <ArrowRight className="h-5 w-5 text-green-500" />
              <span className="text-2xl font-bold">{assignedRoutes.length}</span>
              <span className="text-sm text-muted-foreground">/ {phoneNumbers.length}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Calls</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-500 animate-pulse" />
              <span className="text-2xl font-bold">{activeCalls.length}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Unassigned Numbers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-yellow-500" />
              <span className="text-2xl font-bold">{unassignedNumbers.length}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Calls */}
      {activeCalls.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-blue-500 animate-pulse" />
                  Active Vapi Calls
                </CardTitle>
                <CardDescription>Real-time call monitoring</CardDescription>
              </div>
              <Button onClick={handleRefresh} variant="outline" size="sm" disabled={isRefreshing}>
                <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {activeCalls.map((call) => (
                <div
                  key={call.call_id}
                  className="flex items-center justify-between p-3 border rounded-lg bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                    <Phone className="h-4 w-4 text-blue-600" />
                    <span className="font-mono text-sm">{call.to_number}</span>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    <Bot className="h-4 w-4 text-purple-600" />
                    <span className="text-sm text-muted-foreground truncate max-w-[200px]">
                      {call.assistant_id}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="default" className="bg-blue-500">
                      {call.status}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      <Clock className="h-3 w-3 inline mr-1" />
                      {new Date(call.started_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Phone-to-Assistant Routes */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <ArrowRight className="h-5 w-5" />
                Phone Number → Assistant Routes
              </CardTitle>
              <CardDescription>
                Configured webhook routing for inbound calls
              </CardDescription>
            </div>
            <Button onClick={handleRefresh} variant="outline" size="sm" disabled={isRefreshing}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {assignedRoutes.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No phone-to-assistant routes configured</p>
              <p className="text-sm mt-1">Assign phone numbers to assistants in the Phone Numbers page</p>
            </div>
          ) : (
            <div className="space-y-3">
              {assignedRoutes.map((phone) => (
                <div
                  key={phone.id}
                  className="p-4 border rounded-lg hover:bg-accent transition-colors"
                >
                  {/* Route visualization */}
                  <div className="flex items-center gap-4">
                    {/* Phone Number */}
                    <div className="flex items-center gap-2 flex-1">
                      <Phone className="h-5 w-5 text-blue-500" />
                      <div>
                        <div className="font-mono font-semibold">{phone.number}</div>
                        <div className="text-xs text-muted-foreground">
                          {phone.provider.toUpperCase()}
                        </div>
                      </div>
                    </div>

                    {/* Arrow */}
                    <ArrowRight className="h-6 w-6 text-muted-foreground flex-shrink-0" />

                    {/* Assistant */}
                    <div className="flex items-center gap-2 flex-1">
                      <Bot className="h-5 w-5 text-purple-500" />
                      <div>
                        <div className="font-semibold truncate max-w-[200px]">
                          {phone.assigned_assistant_id}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Vapi Assistant
                        </div>
                      </div>
                    </div>

                    {/* Status */}
                    <div className="flex items-center gap-2">
                      <Badge variant="default" className={
                        phone.status === 'active' ? 'bg-green-500' : 'bg-gray-500'
                      }>
                        {phone.status}
                      </Badge>
                    </div>
                  </div>

                  {/* Webhook URL */}
                  {phone.webhook_url && (
                    <div className="mt-3 pt-3 border-t">
                      <div className="text-xs text-muted-foreground">
                        Webhook: <span className="font-mono">{phone.webhook_url}</span>
                      </div>
                    </div>
                  )}

                  {/* Assignment timestamp */}
                  {phone.assigned_at && (
                    <div className="mt-2 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3 inline mr-1" />
                      Assigned {new Date(phone.assigned_at).toLocaleString()}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Unassigned Numbers Warning */}
      {unassignedNumbers.length > 0 && (
        <Card className="border-yellow-200 dark:border-yellow-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-700 dark:text-yellow-500">
              <AlertCircle className="h-5 w-5" />
              Unassigned Numbers
            </CardTitle>
            <CardDescription>
              These numbers won't route calls until assigned to an assistant
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {unassignedNumbers.map((phone) => (
                <div
                  key={phone.id}
                  className="flex items-center justify-between p-3 border rounded-lg bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800"
                >
                  <div className="flex items-center gap-3">
                    <Phone className="h-4 w-4 text-yellow-600" />
                    <span className="font-mono">{phone.number}</span>
                    <Badge variant="outline">{phone.provider.toUpperCase()}</Badge>
                  </div>
                  <Badge variant="outline" className="text-yellow-700 dark:text-yellow-500">
                    No route configured
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
