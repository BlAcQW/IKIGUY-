import React, { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Wallet, Calendar, History, CreditCard, Bot, Shield, BarChart3, TrendingUp, DollarSign, Download, MessageSquare } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/components/ui/use-toast';
import WalletSection from '@/components/dashboard/WalletSection';
import DemoBookings from '@/components/dashboard/DemoBookings';
import TransactionHistory from '@/components/dashboard/TransactionHistory';
import RecentDemos from '@/components/dashboard/RecentDemos';
import PaymentHistory from '@/components/dashboard/PaymentHistory';
import PaymentAnalytics from '@/components/dashboard/PaymentAnalytics';
import VoiceAgents from '@/pages/VoiceAgents';
import VoiceAgentManagement from '@/components/dashboard/VoiceAgentManagement';
import AssistantAnalytics from '@/components/dashboard/AssistantAnalytics';
import DemoAnalytics from '@/components/dashboard/DemoAnalytics';
import AdvancedAnalytics from '@/components/dashboard/AdvancedAnalytics';
import TwoFactorAuth from '@/components/TwoFactorAuth';
import RefundHistory from '@/components/dashboard/RefundHistory';
import CostTracking from '@/components/dashboard/CostTracking';
import SMSTester from '@/components/SMSTester';

const Dashboard = () => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [wallet, setWallet] = useState<any>(null);
  const [profileData, setProfileData] = useState<any>(null);

  useEffect(() => {
    if (!loading && !user) {
      navigate('/auth');
    }
  }, [user, loading, navigate]);

  useEffect(() => {
    if (user) {
      fetchUserData();
    }
  }, [user]);

  const fetchUserData = async () => {
    try {
      // Fetch wallet data
      const { data: walletData, error: walletError } = await supabase
        .from('wallets')
        .select('*')
        .eq('user_id', user?.id)
        .single();

      if (walletError && walletError.code !== 'PGRST116') {
        console.error('Error fetching wallet:', walletError);
      } else {
        setWallet(walletData);
      }

      // Fetch profile data
      const { data: profile, error: profileError } = await supabase
        .from('profiles')
        .select('*')
        .eq('user_id', user?.id)
        .single();

      if (profileError && profileError.code !== 'PGRST116') {
        console.error('Error fetching profile:', profileError);
      } else {
        setProfileData(profile);
      }
    } catch (error) {
      console.error('Error fetching user data:', error);
      toast({
        title: "Error loading data",
        description: "Failed to load your account information.",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted">
      <div className="container mx-auto px-4 py-8">
        <Tabs defaultValue="agents" className="flex w-full gap-6">
          {/* Sidebar */}
          <div className="w-64 flex-shrink-0">
            <TabsList className="flex flex-col h-auto w-full bg-muted/50 p-2 space-y-2">
              <TabsTrigger value="agents" className="flex items-center gap-2 justify-start w-full">
                <Bot className="h-4 w-4" />
                Voice Agents
              </TabsTrigger>
              <TabsTrigger value="wallet" className="flex items-center gap-2 justify-start w-full">
                <Wallet className="h-4 w-4" />
                Wallet
              </TabsTrigger>
              <TabsTrigger value="bookings" className="flex items-center gap-2 justify-start w-full">
                <Calendar className="h-4 w-4" />
                Demo Bookings
              </TabsTrigger>
              <TabsTrigger value="history" className="flex items-center gap-2 justify-start w-full">
                <History className="h-4 w-4" />
                Transactions
              </TabsTrigger>
              <TabsTrigger value="payments" className="flex items-center gap-2 justify-start w-full">
                <CreditCard className="h-4 w-4" />
                Payment History
              </TabsTrigger>
              <TabsTrigger value="analytics" className="flex items-center gap-2 justify-start w-full">
                <BarChart3 className="h-4 w-4" />
                Analytics
              </TabsTrigger>
              <TabsTrigger value="demo-analytics" className="flex items-center gap-2 justify-start w-full">
                <BarChart3 className="h-4 w-4" />
                Demo Analytics
              </TabsTrigger>
              <TabsTrigger value="advanced-analytics" className="flex items-center gap-2 justify-start w-full">
                <TrendingUp className="h-4 w-4" />
                Advanced Analytics
              </TabsTrigger>
              <TabsTrigger value="cost-tracking" className="flex items-center gap-2 justify-start w-full">
                <DollarSign className="h-4 w-4" />
                Cost Tracking
              </TabsTrigger>
              <TabsTrigger value="security" className="flex items-center gap-2 justify-start w-full">
                <Shield className="h-4 w-4" />
                Security
              </TabsTrigger>
              <TabsTrigger value="sms-tester" className="flex items-center gap-2 justify-start w-full">
                <MessageSquare className="h-4 w-4" />
                SMS Tester
              </TabsTrigger>
            </TabsList>
          </div>

          {/* Main Content Area */}
          <div className="flex-1 min-w-0">

          <TabsContent value="wallet" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <WalletSection wallet={wallet} onWalletUpdate={fetchUserData} />
              <RecentDemos />
            </div>
          </TabsContent>

          <TabsContent value="bookings" className="space-y-6">
            <DemoBookings />
          </TabsContent>

          <TabsContent value="history" className="space-y-6">
            <TransactionHistory />
          </TabsContent>

          <TabsContent value="payments" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <PaymentHistory />
              <RefundHistory />
            </div>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6">
            <PaymentAnalytics />
          </TabsContent>

          <TabsContent value="demo-analytics" className="space-y-6">
            <DemoAnalytics />
          </TabsContent>

          <TabsContent value="advanced-analytics" className="space-y-6">
            <AdvancedAnalytics />
          </TabsContent>

          <TabsContent value="agents" className="space-y-6">
            <VoiceAgents />
          </TabsContent>

          <TabsContent value="security" className="space-y-6">
            <div className="flex justify-center">
              <TwoFactorAuth />
            </div>
          </TabsContent>

          <TabsContent value="cost-tracking" className="space-y-6">
            <CostTracking />
          </TabsContent>

          <TabsContent value="sms-tester" className="space-y-6">
            <div className="flex justify-center">
              <SMSTester />
            </div>
          </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
};

export default Dashboard;