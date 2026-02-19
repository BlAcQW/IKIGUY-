import React, { useState, useEffect } from 'react';
import {
  Phone,
  PhoneIncoming,
  PhoneOutgoing,
  Clock,
  DollarSign,
  TrendingUp,
  Users,
  FileAudio,
  RefreshCw,
  Download,
  Calendar,
  AlertCircle,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { API_ENDPOINTS, CORE_API_URL } from '@/config/api-config';
import { useToast } from '@/hooks/use-toast';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface PhoneNumber {
  id: string;
  number: string;
  provider: string;
  status: string;
  assigned_assistant_id?: string;
}

interface DIDStats {
  phone_number: string;
  total_calls: number;
  inbound_calls: number;
  outbound_calls: number;
  total_minutes: number;
  total_cost: number;
  success_rate: number;
  unique_numbers_called: number;
  unique_numbers_received_from: number;
  recordings_count: number;
  avg_call_duration: number;
  recent_calls: CallRecord[];
}

interface CallRecord {
  id: string;
  call_id: string;
  direction: 'inbound' | 'outbound';
  from_number: string;
  to_number: string;
  start_time: string;
  duration: number;
  status: string;
  cost?: number;
  recording_url?: string;
  transcript?: string;
}

interface DIDAnalyticsPanelProps {
  onRefresh?: () => void;
}

export const DIDAnalyticsPanel: React.FC<DIDAnalyticsPanelProps> = ({ onRefresh }) => {
  const { toast } = useToast();
  const [phoneNumbers, setPhoneNumbers] = useState<PhoneNumber[]>([]);
  const [selectedDID, setSelectedDID] = useState<string | null>(null);
  const [didStats, setDidStats] = useState<DIDStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [period, setPeriod] = useState<'7d' | '30d' | '90d' | 'all'>('30d');

  // Fetch phone numbers
  const fetchPhoneNumbers = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(API_ENDPOINTS.phoneNumbers.list);
      if (!response.ok) throw new Error('Failed to fetch phone numbers');
      const data = await response.json();
      const numbers = (data.numbers || []) as PhoneNumber[];
      setPhoneNumbers(numbers);
      if (numbers.length > 0 && !selectedDID) {
        setSelectedDID(numbers[0].number);
      }
    } catch (error: any) {
      console.error('Error fetching phone numbers:', error);
      toast({
        title: 'Error',
        description: 'Failed to load phone numbers',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch DID statistics
  const fetchDIDStats = async (phoneNumber: string) => {
    if (!phoneNumber) return;

    setIsLoadingStats(true);
    try {
      // Calculate date range
      const endDate = new Date();
      const startDate = new Date();
      if (period === '7d') {
        startDate.setDate(endDate.getDate() - 7);
      } else if (period === '30d') {
        startDate.setDate(endDate.getDate() - 30);
      } else if (period === '90d') {
        startDate.setDate(endDate.getDate() - 90);
      } else {
        startDate.setFullYear(2020); // All time
      }

      // Fetch call logs for this DID (both inbound and outbound)
      const coreApiUrl = CORE_API_URL;
      const [inboundResponse, outboundResponse] = await Promise.all([
        fetch(
          `${coreApiUrl}/call-logs?to_phone=${encodeURIComponent(phoneNumber)}&start_date=${startDate.toISOString()}&end_date=${endDate.toISOString()}&per_page=1000`
        ),
        fetch(
          `${coreApiUrl}/call-logs?from_phone=${encodeURIComponent(phoneNumber)}&start_date=${startDate.toISOString()}&end_date=${endDate.toISOString()}&per_page=1000`
        ),
      ]);

      if (!inboundResponse.ok || !outboundResponse.ok) {
        throw new Error('Failed to fetch call logs');
      }

      const inboundData = await inboundResponse.json();
      const outboundData = await outboundResponse.json();

      const inboundCalls = (inboundData.logs || []) as CallRecord[];
      const outboundCalls = (outboundData.logs || []) as CallRecord[];
      const allCalls = [...inboundCalls, ...outboundCalls];

      // Calculate statistics
      const totalCalls = allCalls.length;
      const inboundCount = inboundCalls.length;
      const outboundCount = outboundCalls.length;
      const totalMinutes = allCalls.reduce((sum, call) => sum + (call.duration || 0), 0) / 60;
      const totalCost = allCalls.reduce((sum, call) => sum + (call.cost || 0), 0);
      const successfulCalls = allCalls.filter(
        (call) => call.status === 'completed' || call.status === 'ended'
      ).length;
      const successRate = totalCalls > 0 ? (successfulCalls / totalCalls) * 100 : 0;
      const uniqueNumbersCalled = new Set(
        outboundCalls.map((call) => call.to_number)
      ).size;
      const uniqueNumbersReceivedFrom = new Set(
        inboundCalls.map((call) => call.from_number)
      ).size;
      const recordingsCount = allCalls.filter((call) => call.recording_url).length;
      const avgCallDuration =
        allCalls.length > 0
          ? allCalls.reduce((sum, call) => sum + (call.duration || 0), 0) / allCalls.length / 60
          : 0;

      // Get recent calls (last 10)
      const recentCalls = allCalls
        .sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime())
        .slice(0, 10);

      setDidStats({
        phone_number: phoneNumber,
        total_calls: totalCalls,
        inbound_calls: inboundCount,
        outbound_calls: outboundCount,
        total_minutes: totalMinutes,
        total_cost: totalCost,
        success_rate: successRate,
        unique_numbers_called: uniqueNumbersCalled,
        unique_numbers_received_from: uniqueNumbersReceivedFrom,
        recordings_count: recordingsCount,
        avg_call_duration: avgCallDuration,
        recent_calls: recentCalls,
      });
    } catch (error: any) {
      console.error('Error fetching DID stats:', error);
      toast({
        title: 'Error',
        description: 'Failed to load DID statistics',
        variant: 'destructive',
      });
    } finally {
      setIsLoadingStats(false);
    }
  };

  useEffect(() => {
    fetchPhoneNumbers();
  }, []);

  useEffect(() => {
    if (selectedDID) {
      fetchDIDStats(selectedDID);
    }
  }, [selectedDID, period]);

  const formatDuration = (minutes: number): string => {
    if (minutes < 1) {
      return `${Math.round(minutes * 60)}s`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const exportToCSV = () => {
    if (!didStats) return;

    const headers = [
      'Phone Number',
      'Total Calls',
      'Inbound',
      'Outbound',
      'Total Minutes',
      'Total Cost',
      'Success Rate',
      'Unique Numbers Called',
      'Unique Numbers Received From',
      'Recordings',
      'Avg Call Duration',
    ];

    const row = [
      didStats.phone_number,
      didStats.total_calls,
      didStats.inbound_calls,
      didStats.outbound_calls,
      didStats.total_minutes.toFixed(2),
      didStats.total_cost.toFixed(2),
      `${didStats.success_rate.toFixed(1)}%`,
      didStats.unique_numbers_called,
      didStats.unique_numbers_received_from,
      didStats.recordings_count,
      formatDuration(didStats.avg_call_duration),
    ];

    const csvContent = [headers.join(','), row.join(',')].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `did-analytics-${didStats.phone_number}-${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <p className="mt-2 text-sm text-muted-foreground">Loading phone numbers...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* DID Selector */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Phone className="h-5 w-5" />
                DID Analytics
              </CardTitle>
              <CardDescription>
                Detailed statistics and analytics per phone number (DID)
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={period}
                onChange={(e) => setPeriod(e.target.value as any)}
                className="px-3 py-1.5 text-sm border rounded-md bg-background"
              >
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
                <option value="all">All time</option>
              </select>
              <Button onClick={() => selectedDID && fetchDIDStats(selectedDID)} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {phoneNumbers.map((phone) => (
              <Button
                key={phone.id}
                variant={selectedDID === phone.number ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedDID(phone.number)}
              >
                {phone.number}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Statistics */}
      {isLoadingStats ? (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="mt-2 text-sm text-muted-foreground">Loading statistics...</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : didStats ? (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  Total Calls
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{didStats.total_calls}</div>
                <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
                  <PhoneIncoming className="h-3 w-3" />
                  <span>{didStats.inbound_calls} inbound</span>
                  <PhoneOutgoing className="h-3 w-3 ml-2" />
                  <span>{didStats.outbound_calls} outbound</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Total Minutes
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{formatDuration(didStats.total_minutes)}</div>
                <p className="text-sm text-muted-foreground mt-2">
                  Avg: {formatDuration(didStats.avg_call_duration)} per call
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  Total Cost
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">${didStats.total_cost.toFixed(2)}</div>
                <p className="text-sm text-muted-foreground mt-2">
                  ${(didStats.total_cost / didStats.total_calls || 0).toFixed(2)} per call
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Success Rate
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{didStats.success_rate.toFixed(1)}%</div>
                <p className="text-sm text-muted-foreground mt-2">
                  {didStats.total_calls - Math.round((didStats.total_calls * didStats.success_rate) / 100)} failed
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Additional Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Unique Numbers Called
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{didStats.unique_numbers_called}</div>
                <p className="text-sm text-muted-foreground mt-2">Outbound contacts</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Unique Callers
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{didStats.unique_numbers_received_from}</div>
                <p className="text-sm text-muted-foreground mt-2">Inbound contacts</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <FileAudio className="h-4 w-4" />
                  Recordings
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{didStats.recordings_count}</div>
                <p className="text-sm text-muted-foreground mt-2">
                  {didStats.total_calls > 0
                    ? `${((didStats.recordings_count / didStats.total_calls) * 100).toFixed(1)}% of calls`
                    : 'No recordings'}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Recent Calls */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="h-5 w-5" />
                    Recent Calls
                  </CardTitle>
                  <CardDescription>Last 10 calls for this DID</CardDescription>
                </div>
                <Button onClick={exportToCSV} variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Export CSV
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {didStats.recent_calls.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No calls found for this period</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Direction</TableHead>
                      <TableHead>From</TableHead>
                      <TableHead>To</TableHead>
                      <TableHead>Time</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Cost</TableHead>
                      <TableHead>Recording</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {didStats.recent_calls.map((call) => (
                      <TableRow key={call.id}>
                        <TableCell>
                          {call.direction === 'inbound' ? (
                            <Badge variant="default" className="bg-green-500">
                              <PhoneIncoming className="h-3 w-3 mr-1" />
                              Inbound
                            </Badge>
                          ) : (
                            <Badge variant="default" className="bg-blue-500">
                              <PhoneOutgoing className="h-3 w-3 mr-1" />
                              Outbound
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <span className="font-mono text-sm">{call.from_number}</span>
                        </TableCell>
                        <TableCell>
                          <span className="font-mono text-sm">{call.to_number}</span>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">{formatTimestamp(call.start_time)}</span>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">{formatDuration(call.duration / 60)}</span>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              call.status === 'completed' || call.status === 'ended'
                                ? 'default'
                                : 'destructive'
                            }
                          >
                            {call.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">
                            {call.cost ? `$${call.cost.toFixed(2)}` : '-'}
                          </span>
                        </TableCell>
                        <TableCell>
                          {call.recording_url ? (
                            <a
                              href={call.recording_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary hover:underline"
                            >
                              <FileAudio className="h-4 w-4" />
                            </a>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-muted-foreground">
              <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>Select a phone number to view analytics</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

