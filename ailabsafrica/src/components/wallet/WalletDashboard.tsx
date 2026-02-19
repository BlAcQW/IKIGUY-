import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { 
  Wallet, 
  CreditCard, 
  Clock, 
  TrendingUp, 
  DollarSign, 
  BarChart3,
  Phone,
  MessageSquare,
  Video,
  Wifi,
  AlertTriangle,
  MapPin
} from 'lucide-react';
import BundlePurchase from './BundlePurchase';
import UsageHistory from './UsageHistory';
import WalletTransactions from './WalletTransactions';
import UsageAnalytics from './UsageAnalytics';
import UsageTrackingDashboard from './UsageTrackingDashboard';
import PricingDashboard from './PricingDashboard';
import HelpTooltip from '../help/HelpTooltip';
import HelpButton from '../help/HelpButton';

interface WalletData {
  id: string;
  balance: number;
  currency: string;
  created_at: string;
  updated_at: string;
}

interface UsageStats {
  total_minutes: number;
  total_cost: number;
  sessions_count: number;
  average_session_length: number;
}

interface MediumUsage {
  medium: string;
  minutes: number;
  cost: number;
  sessions: number;
  cost_per_minute: number;
}

interface UsageAlert {
  id: string;
  alert_type: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

const WalletDashboard = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [mediumUsage, setMediumUsage] = useState<MediumUsage[]>([]);
  const [alerts, setAlerts] = useState<UsageAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [showBundlePurchase, setShowBundlePurchase] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (user) {
      loadWalletData();
    }
  }, [user]);

  const loadWalletData = async () => {
    if (!user) return;
    
    setLoading(true);
    try {
      // Load wallet data
      const { data: walletData, error: walletError } = await supabase
        .from('wallets')
        .select('*')
        .eq('user_id', user.id)
        .single();

      if (walletError && walletError.code !== 'PGRST116') {
        throw walletError;
      }

      if (walletData) {
        setWallet(walletData);
      }

      // Load usage statistics by communication medium
      const { data: usageData, error: usageError } = await supabase
        .from('usage_tracking')
        .select('communication_medium, duration_minutes, total_cost, cost_per_minute')
        .eq('user_id', user.id)
        .eq('status', 'completed');

      if (usageError) {
        console.error('Error loading usage stats:', usageError);
      } else if (usageData) {
        // Calculate overall stats
        const stats: UsageStats = {
          total_minutes: usageData.reduce((sum, record) => sum + (record.duration_minutes || 0), 0),
          total_cost: usageData.reduce((sum, record) => sum + (record.total_cost || 0), 0),
          sessions_count: usageData.length,
          average_session_length: usageData.length > 0 
            ? usageData.reduce((sum, record) => sum + (record.duration_minutes || 0), 0) / usageData.length 
            : 0
        };
        setUsageStats(stats);

        // Calculate usage by medium
        const mediumMap = new Map<string, MediumUsage>();
        usageData.forEach(record => {
          const medium = record.communication_medium || 'webrtc';
          const existing = mediumMap.get(medium) || {
            medium,
            minutes: 0,
            cost: 0,
            sessions: 0,
            cost_per_minute: 0
          };
          
          existing.minutes += record.duration_minutes || 0;
          existing.cost += record.total_cost || 0;
          existing.sessions += 1;
          existing.cost_per_minute = existing.cost / existing.minutes;
          
          mediumMap.set(medium, existing);
        });

        setMediumUsage(Array.from(mediumMap.values()));
      }

      // Load alerts
      const { data: alertsData } = await supabase
        .from('usage_alerts')
        .select('*')
        .eq('user_id', user.id)
        .eq('is_resolved', false)
        .order('created_at', { ascending: false });

      if (alertsData) {
        setAlerts(alertsData);
      }
    } catch (error: any) {
      console.error('Error loading wallet data:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load wallet data',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleBundlePurchase = () => {
    setShowBundlePurchase(true);
  };

  const handleBundlePurchaseComplete = () => {
    setShowBundlePurchase(false);
    loadWalletData(); // Refresh wallet data
    toast({
      title: 'Success',
      description: 'Bundle purchased successfully!'
    });
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading wallet...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Wallet Dashboard</h1>
          <p className="text-muted-foreground">Manage your assistant usage and billing</p>
        </div>
        <HelpButton showText={true} />
      </div>

      {/* Wallet Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              Wallet Balance
              <HelpTooltip 
                content="Your current wallet balance. Add funds to use AI assistants. Usage is deducted in real-time based on communication medium and duration."
                size="sm"
              />
            </CardTitle>
            <Wallet className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${wallet?.balance?.toFixed(2) || '0.00'}
            </div>
            <p className="text-xs text-muted-foreground">
              Available for assistant usage
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Usage</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {usageStats?.total_minutes?.toFixed(1) || '0'} min
            </div>
            <p className="text-xs text-muted-foreground">
              {usageStats?.sessions_count || 0} sessions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Spent</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${usageStats?.total_cost?.toFixed(2) || '0.00'}
            </div>
            <p className="text-xs text-muted-foreground">
              Lifetime spending
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Session</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {usageStats?.average_session_length?.toFixed(1) || '0'} min
            </div>
            <p className="text-xs text-muted-foreground">
              Per conversation
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <Card className="mb-6 border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-800">
              <AlertTriangle className="h-5 w-5" />
              Usage Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {alerts.slice(0, 3).map(alert => (
                <div key={alert.id} className="flex items-center justify-between p-3 bg-white rounded-lg border">
                  <div className="flex-1">
                    <p className="text-sm font-medium">{alert.message}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(alert.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Button onClick={handleBundlePurchase} className="flex items-center gap-2">
              <CreditCard className="h-4 w-4" />
              Buy Usage Bundle
            </Button>
            <Button variant="outline" onClick={() => setActiveTab('usage-tracking')}>
              <BarChart3 className="h-4 w-4" />
              Usage Tracking
            </Button>
            <Button variant="outline" onClick={() => setActiveTab('pricing')}>
              <DollarSign className="h-4 w-4" />
              Pricing Dashboard
            </Button>
            <Button variant="outline" onClick={() => window.location.href = '/voice-agents'}>
              View Assistants
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Usage Progress */}
      {wallet && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Usage Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between text-sm">
                <span>Available Balance</span>
                <span>${wallet.balance.toFixed(2)}</span>
              </div>
              <Progress 
                value={Math.min((wallet.balance / 50) * 100, 100)} 
                className="h-2"
              />
              <p className="text-xs text-muted-foreground">
                Based on $0.50 per minute usage rate
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Usage by Communication Medium */}
      {mediumUsage.length > 0 && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Usage by Communication Medium</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mediumUsage.map(usage => {
                const getMediumIcon = (medium: string) => {
                  switch (medium) {
                    case 'webrtc': return Wifi;
                    case 'phone': return Phone;
                    case 'sms': return MessageSquare;
                    case 'video': return Video;
                    default: return Wifi;
                  }
                };
                const Icon = getMediumIcon(usage.medium);
                
                return (
                  <div key={usage.medium} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-full bg-primary/10">
                        <Icon className="h-4 w-4 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-medium capitalize">{usage.medium}</h3>
                        <p className="text-sm text-muted-foreground">
                          {usage.sessions} sessions
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">{usage.minutes.toFixed(1)} min</p>
                      <p className="text-sm text-muted-foreground">
                        ${usage.cost.toFixed(2)}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs for detailed views */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="usage-tracking">Usage Tracking</TabsTrigger>
          <TabsTrigger value="pricing">Pricing</TabsTrigger>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="usage">Usage History</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-4">
          <div className="space-y-4">
            <WalletTransactions userId={user?.id} />
            <UsageHistory userId={user?.id} />
          </div>
        </TabsContent>

        <TabsContent value="usage-tracking" className="space-y-4">
          <UsageTrackingDashboard />
        </TabsContent>

        <TabsContent value="pricing" className="space-y-4">
          <PricingDashboard />
        </TabsContent>
        
        <TabsContent value="transactions" className="space-y-4">
          <WalletTransactions userId={user?.id} />
        </TabsContent>
        
        <TabsContent value="usage" className="space-y-4">
          <UsageHistory userId={user?.id} />
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <UsageAnalytics userId={user?.id} />
        </TabsContent>
      </Tabs>

      {/* Bundle Purchase Modal */}
      {showBundlePurchase && (
        <BundlePurchase 
          onComplete={handleBundlePurchaseComplete}
          onCancel={() => setShowBundlePurchase(false)}
        />
      )}
    </div>
  );
};

export default WalletDashboard;
