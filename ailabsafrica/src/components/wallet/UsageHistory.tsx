import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { Clock, DollarSign, Calendar, Activity } from 'lucide-react';

interface UsageRecord {
  id: string;
  assistant_id: string;
  session_id: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  total_cost: number;
  status: string;
  metadata: any;
  created_at: string;
}

interface UsageHistoryProps {
  userId?: string;
}

const UsageHistory = ({ userId }: UsageHistoryProps) => {
  const { toast } = useToast();
  const [usageRecords, setUsageRecords] = useState<UsageRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [assistantNames, setAssistantNames] = useState<Record<string, string>>({});

  useEffect(() => {
    if (userId) {
      loadUsageHistory();
    }
  }, [userId]);

  const loadUsageHistory = async () => {
    if (!userId) return;
    
    setLoading(true);
    try {
      const { data, error } = await supabase
        .from('usage_tracking')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })
        .limit(50);

      if (error) throw error;
      setUsageRecords(data || []);

      // Load assistant names for display
      if (data && data.length > 0) {
        await loadAssistantNames(data);
      }
    } catch (error: any) {
      console.error('Error loading usage history:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load usage history',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const loadAssistantNames = async (records: UsageRecord[]) => {
    try {
      const assistantIds = [...new Set(records.map(r => r.assistant_id))];
      const { data, error } = await supabase
        .from('custom_demos')
        .select('assistant_id, assistant_name')
        .in('assistant_id', assistantIds);

      if (error) throw error;

      const namesMap: Record<string, string> = {};
      data?.forEach(demo => {
        namesMap[demo.assistant_id] = demo.assistant_name;
      });

      setAssistantNames(namesMap);
    } catch (error) {
      console.error('Error loading assistant names:', error);
    }
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="default">Active</Badge>;
      case 'completed':
        return <Badge variant="secondary">Completed</Badge>;
      case 'paused':
        return <Badge variant="outline">Paused</Badge>;
      case 'cancelled':
        return <Badge variant="destructive">Cancelled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Usage History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Usage History
        </CardTitle>
      </CardHeader>
      <CardContent>
        {usageRecords.length === 0 ? (
          <div className="text-center py-8">
            <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No usage history</h3>
            <p className="text-muted-foreground">
              Start using your assistants to see usage history here.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {usageRecords.map((record) => (
              <div
                key={record.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="font-semibold">
                      {assistantNames[record.assistant_id] || 'Unknown Assistant'}
                    </h4>
                    {getStatusBadge(record.status)}
                  </div>
                  
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {formatDate(record.start_time)}
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDuration(record.duration_minutes)}
                    </div>
                    <div className="flex items-center gap-1">
                      <DollarSign className="h-3 w-3" />
                      ${record.total_cost?.toFixed(2) || '0.00'}
                    </div>
                  </div>
                  
                  {record.metadata && Object.keys(record.metadata).length > 0 && (
                    <div className="mt-2 text-xs text-muted-foreground">
                      <details>
                        <summary className="cursor-pointer hover:text-foreground">
                          Session Details
                        </summary>
                        <pre className="mt-1 p-2 bg-muted rounded text-xs overflow-x-auto">
                          {JSON.stringify(record.metadata, null, 2)}
                        </pre>
                      </details>
                    </div>
                  )}
                </div>
                
                <div className="text-right">
                  <div className="text-sm font-medium">
                    Session: {record.session_id.slice(0, 8)}...
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        
        {usageRecords.length > 0 && (
          <div className="mt-6 pt-4 border-t">
            <div className="flex justify-between items-center text-sm">
              <span className="text-muted-foreground">
                Showing {usageRecords.length} most recent sessions
              </span>
              <Button variant="outline" size="sm" onClick={loadUsageHistory}>
                Refresh
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default UsageHistory;
