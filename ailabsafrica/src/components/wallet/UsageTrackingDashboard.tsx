import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { 
  Phone, 
  MessageSquare, 
  Video, 
  Globe, 
  DollarSign, 
  Clock, 
  TrendingUp, 
  AlertTriangle,
  MapPin,
  Wifi,
  Smartphone
} from 'lucide-react';
import HelpTooltip from '../help/HelpTooltip';

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

interface RegionalPricing {
  region: string;
  currency: string;
  webrtc_cost: number;
  phone_cost: number;
  sms_cost: number;
  video_cost: number;
}

interface UsageAlert {
  id: string;
  alert_type: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

const UsageTrackingDashboard: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [mediumUsage, setMediumUsage] = useState<MediumUsage[]>([]);
  const [regionalPricing, setRegionalPricing] = useState<RegionalPricing[]>([]);
  const [alerts, setAlerts] = useState<UsageAlert[]>([]);
  const [selectedRegion, setSelectedRegion] = useState('GH');
  const [loading, setLoading] = useState(true);
  const [walletBalance, setWalletBalance] = useState(0);

  const regions = [
    { code: 'GH', name: 'Ghana', flag: '🇬🇭' },
    { code: 'NG', name: 'Nigeria', flag: '🇳🇬' },
    { code: 'KE', name: 'Kenya', flag: '🇰🇪' },
    { code: 'ZA', name: 'South Africa', flag: '🇿🇦' },
    { code: 'EG', name: 'Egypt', flag: '🇪🇬' },
    { code: 'US', name: 'United States', flag: '🇺🇸' },
  ];

  const communicationMediums = [
    { key: 'webrtc', name: 'WebRTC', icon: Wifi, color: 'bg-blue-500' },
    { key: 'phone', name: 'Phone', icon: Phone, color: 'bg-green-500' },
    { key: 'sms', name: 'SMS', icon: MessageSquare, color: 'bg-purple-500' },
    { key: 'video', name: 'Video', icon: Video, color: 'bg-red-500' },
  ];

  useEffect(() => {
    if (user) {
      loadUsageData();
      loadAlerts();
    }
  }, [user, selectedRegion]);

  const loadUsageData = async () => {
    if (!user) return;
    
    setLoading(true);
    try {
      // Load wallet balance
      const { data: walletData } = await supabase
        .from('wallets')
        .select('balance')
        .eq('user_id', user.id)
        .single();

      if (walletData) {
        setWalletBalance(walletData.balance);
      }

      // Load usage statistics by communication medium
      const { data: usageData } = await supabase
        .from('usage_tracking')
        .select('communication_medium, duration_minutes, total_cost, cost_per_minute')
        .eq('user_id', user.id)
        .eq('status', 'completed');

      if (usageData) {
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

      // Load regional pricing
      const { data: pricingData } = await supabase
        .from('pricing_config')
        .select('region, currency, communication_medium, final_cost_per_minute')
        .eq('is_active', true);

      if (pricingData) {
        const pricingMap = new Map<string, RegionalPricing>();
        pricingData.forEach(record => {
          const existing = pricingMap.get(record.region) || {
            region: record.region,
            currency: record.currency,
            webrtc_cost: 0,
            phone_cost: 0,
            sms_cost: 0,
            video_cost: 0
          };

          switch (record.communication_medium) {
            case 'webrtc':
              existing.webrtc_cost = record.final_cost_per_minute;
              break;
            case 'phone':
              existing.phone_cost = record.final_cost_per_minute;
              break;
            case 'sms':
              existing.sms_cost = record.final_cost_per_minute;
              break;
            case 'video':
              existing.video_cost = record.final_cost_per_minute;
              break;
          }

          pricingMap.set(record.region, existing);
        });

        setRegionalPricing(Array.from(pricingMap.values()));
      }

    } catch (error: any) {
      console.error('Error loading usage data:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load usage data',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const loadAlerts = async () => {
    if (!user) return;

    try {
      const { data: alertsData } = await supabase
        .from('usage_alerts')
        .select('*')
        .eq('user_id', user.id)
        .eq('is_resolved', false)
        .order('created_at', { ascending: false });

      if (alertsData) {
        setAlerts(alertsData);
      }
    } catch (error) {
      console.error('Error loading alerts:', error);
    }
  };

  const markAlertAsRead = async (alertId: string) => {
    try {
      await supabase
        .from('usage_alerts')
        .update({ is_read: true })
        .eq('id', alertId);

      setAlerts(alerts => alerts.filter(alert => alert.id !== alertId));
    } catch (error) {
      console.error('Error marking alert as read:', error);
    }
  };

  const getCurrentRegionPricing = () => {
    return regionalPricing.find(p => p.region === selectedRegion);
  };

  const getMediumIcon = (medium: string) => {
    const mediumConfig = communicationMediums.find(m => m.key === medium);
    return mediumConfig ? mediumConfig.icon : Globe;
  };

  const getMediumColor = (medium: string) => {
    const mediumConfig = communicationMediums.find(m => m.key === medium);
    return mediumConfig ? mediumConfig.color : 'bg-gray-500';
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading usage data...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Usage Tracking Dashboard</h1>
        <p className="text-muted-foreground">Monitor your assistant usage and costs by communication medium</p>
      </div>

      {/* Region Selector */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5" />
            Regional Pricing
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium">Select Region:</span>
            <Select value={selectedRegion} onValueChange={setSelectedRegion}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {regions.map(region => (
                  <SelectItem key={region.code} value={region.code}>
                    <span className="flex items-center gap-2">
                      <span>{region.flag}</span>
                      <span>{region.name}</span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

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
              {alerts.map(alert => (
                <div key={alert.id} className="flex items-center justify-between p-3 bg-white rounded-lg border">
                  <div className="flex-1">
                    <p className="text-sm font-medium">{alert.message}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(alert.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => markAlertAsRead(alert.id)}
                  >
                    Dismiss
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
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
            <CardTitle className="text-sm font-medium">Wallet Balance</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${walletBalance.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground">
              Available balance
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

      {/* Regional Pricing */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Current Regional Pricing ({selectedRegion})</CardTitle>
        </CardHeader>
        <CardContent>
          {getCurrentRegionPricing() ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {communicationMediums.map(medium => {
                const Icon = medium.icon;
                const pricing = getCurrentRegionPricing();
                const cost = pricing?.[`${medium.key}_cost` as keyof RegionalPricing] || 0;
                
                return (
                  <div key={medium.key} className="text-center p-4 border rounded-lg">
                    <Icon className={`h-8 w-8 mx-auto mb-2 ${medium.color.replace('bg-', 'text-')}`} />
                    <h3 className="font-medium">{medium.name}</h3>
                    <p className="text-2xl font-bold text-primary">
                      ${cost.toFixed(4)}
                    </p>
                    <p className="text-xs text-muted-foreground">per minute</p>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-muted-foreground">No pricing data available for this region.</p>
          )}
        </CardContent>
      </Card>

      {/* Usage by Communication Medium */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Usage by Communication Medium</CardTitle>
        </CardHeader>
        <CardContent>
          {mediumUsage.length > 0 ? (
            <div className="space-y-4">
              {mediumUsage.map(usage => {
                const Icon = getMediumIcon(usage.medium);
                const color = getMediumColor(usage.medium);
                
                return (
                  <div key={usage.medium} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-full ${color}`}>
                        <Icon className="h-4 w-4 text-white" />
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
          ) : (
            <p className="text-muted-foreground">No usage data available.</p>
          )}
        </CardContent>
      </Card>

      {/* Usage Progress */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Usage Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between text-sm">
              <span>Available Balance</span>
              <span>${walletBalance.toFixed(2)}</span>
            </div>
            <Progress 
              value={Math.min((walletBalance / 50) * 100, 100)} 
              className="h-2"
            />
            <p className="text-xs text-muted-foreground">
              Based on current regional pricing
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default UsageTrackingDashboard;
